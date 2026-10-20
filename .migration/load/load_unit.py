#!/usr/bin/env python3
"""Spec-driven initial load of one unit's root collections from PostgreSQL into the migration target.

    /home/ubuntu/.venvs/odoo/bin/python .migration/load/load_unit.py --unit stock-reference \\
        --source-dsn-secret ODOO_SCENARIO_DSN [--target-uri-secret MONGODB_ATLAS_URI] \\
        [--target-db odoo_unt12] [--replace]

The unit's collections come from .migration/units.json and must all be write targets of the unit
in --target-db; rows, field targets and indexes come from .migration/mapping_spec.json; values go
through the ORM's own ``odoo.orm.storage_mongodb.to_bson`` so a loaded document is what
``_storage = 'mongodb'`` would have written (NULL columns are omitted: ``null_missing_equiv``).
Root collections keyed by id -> _id, plus junction arrays embedded in them (a many2many relation
table stored as an array of ``{<targetKey>: <other id>}`` elements on the owning document, as the
storage path writes it; a parent with no rows has no array). Every run empties the collection first;
a non-empty collection needs --replace: once the model is opted in the collection is the
system of record and a reload discards every edit made through the ORM. Secrets are read by name
from the environment (the PostgreSQL one is the plugin's JSON shape) and never printed.
"""
import argparse
import json
import os
import sys
from pathlib import Path

import bson
import psycopg2
from pymongo import ASCENDING, MongoClient

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT)]
from odoo.orm.storage_mongodb import to_bson  # noqa: E402

MAPPING = ROOT / '.migration' / 'mapping_spec.json'
UNITS = ROOT / '.migration' / 'units.json'
ALLOWED = ROOT / '.migration' / 'allowed_targets.json'


def unit_collections(unit_id, target_db):
    unit = next((u for u in json.load(UNITS.open())['units'] if u['id'] == unit_id), None)
    if unit is None:
        raise SystemExit(f'unit {unit_id!r} is not in {UNITS.relative_to(ROOT)}')
    outside = [c for c in unit['collections'] if f'{target_db}.{c}' not in unit['write_targets']]
    if outside:
        raise SystemExit(f'{outside} are not write targets of {unit_id} in {target_db}: plan gap, halt')
    unsupported = [e for e in unit['embedded_tables'] if e['shape'] != 'junction']
    if unsupported:
        raise SystemExit(f'{unit_id} embeds {unsupported}: this loader handles flat roots and junction arrays only')
    return unit['collections']


def connect_source(secret_name):
    params = json.loads(os.environ[secret_name])
    conn = psycopg2.connect(dbname=params['database'], **{k: params[k] for k in ('user', 'password', 'host', 'port')})
    conn.set_session(readonly=True, autocommit=True)
    return conn, params['database']


def select(cur, table, columns, order):
    cur.execute(f'SELECT {", ".join(chr(34) + c + chr(34) for c in columns)} FROM "{table}" ORDER BY {order}')
    return cur.fetchall()


def documents(cur, coll_spec):
    if coll_spec['key']['source'] != ['id'] or coll_spec['key']['target'] != '_id':
        raise SystemExit(f'{coll_spec["collection"]}: only roots keyed by id -> _id are supported')
    fields = coll_spec['fields']
    docs = []
    for row in select(cur, coll_spec['root_table'], ['id'] + [f['source'] for f in fields], 'id'):
        doc = {'_id': int(row[0])}
        for field, value in zip(fields, row[1:]):
            value = to_bson(value, field['bson_type'])
            if value is not None:
                doc[field['target']] = value
        docs.append(doc)
    by_id = {doc['_id']: doc for doc in docs}
    for embed in coll_spec['embeds']:
        for parent_id, elements in junction_elements(cur, coll_spec['collection'], embed).items():
            if parent_id not in by_id:
                raise SystemExit(f'{embed["child_table"]}: row for missing {coll_spec["root_table"]}.id={parent_id}; nothing was changed')
            by_id[parent_id][embed['array_path']] = elements
    return docs


def junction_elements(cur, name, embed):
    """Elements of one junction array by parent id: the relation table's rows, the other side's
    column(s) under the embed key target(s), in (parent, key) order."""
    if embed['shape'] != 'array' or embed['fields'] or len(embed['parent_key']) != 1:
        raise SystemExit(f'{name}.{embed["array_path"]}: only junction arrays (one parent column, no fields) are supported')
    key_sources = embed['key']['source']
    key_targets = embed['key']['target'] if isinstance(embed['key']['target'], list) else [embed['key']['target']]
    if len(key_sources) != len(key_targets):
        raise SystemExit(f'{name}.{embed["array_path"]}: key source {key_sources} and target {key_targets} differ in length')
    bson_types = {f['source']: f['bson_type'] for f in embed['child_fields']}
    columns = embed['parent_key'] + key_sources
    by_parent = {}
    for row in select(cur, embed['child_table'], columns, ', '.join(chr(34) + c + chr(34) for c in columns)):
        element = {target: to_bson(value, bson_types.get(source, 'int'))
                   for source, target, value in zip(key_sources, key_targets, row[1:])}
        by_parent.setdefault(int(row[0]), []).append(element)
    return by_parent


def validate(name, coll_spec, docs):
    """Refuse up front what the target would refuse mid-load: unencodable documents, duplicate unique keys."""
    for doc in docs:
        bson.encode(doc)
    for key_spec, options in index_specs(coll_spec):
        if not options['unique']:
            continue
        seen = set()
        for doc in docs:
            key = bson.encode({field: doc.get(field) for field, _ in key_spec})
            if key in seen:
                raise SystemExit(f'{name}: duplicate value for unique index {key_spec} at _id={doc["_id"]}; nothing was changed')
            seen.add(key)


def index_specs(coll_spec):
    """The entries MongoStore.ensure_indexes creates, as (keys, create_index options)."""
    specs = []
    for index in coll_spec.get('indexes', []):
        keys = index.get('keys')
        if not isinstance(keys, list) or not keys:
            continue
        key_spec = [(k[0], k[1]) if isinstance(k, list) else (k, ASCENDING) for k in keys]
        if key_spec != [('_id', ASCENDING)]:
            specs.append((key_spec, {'unique': bool(index.get('unique'))}))
    return specs


def index_definitions(coll):
    """Every index of a live collection except _id, with its full options (name, unique,
    partialFilterExpression, sparse, collation, ...), so a restore recreates it as it was."""
    return [(list(info['key'].items()), {k: v for k, v in info.items() if k not in ('key', 'v', 'ns')})
            for info in coll.list_indexes() if info['name'] != '_id_']


def write_collection(coll, docs, indexes):
    coll.drop()
    if docs:
        coll.insert_many(docs, ordered=True)
    for keys, options in indexes:
        coll.create_index(keys, **options)


def restore_collection(coll, docs, indexes):
    """Documents back first, then every index; returns what failed, by stage."""
    failed = {}
    try:
        coll.drop()
        if docs:
            coll.insert_many(docs, ordered=True)
    except Exception as exc:  # noqa: BLE001
        failed['documents'] = repr(exc)
        return failed
    for keys, options in indexes:
        try:
            coll.create_index(keys, **options)
        except Exception as exc:  # noqa: BLE001
            failed.setdefault('indexes', []).append(f'{options.get("name")}: {exc!r}')
    return failed


def load(unit_id, source_secret, target_secret, target_db, replace):
    if target_db not in json.load(ALLOWED.open())['databases']:
        raise SystemExit(f'{target_db} is not in {ALLOWED.relative_to(ROOT)}')
    names = unit_collections(unit_id, target_db)
    spec = {c['collection']: c for c in json.load(MAPPING.open())['collections']}
    missing = [n for n in names if n not in spec]
    if missing:
        raise SystemExit(f'{missing} are not in {MAPPING.relative_to(ROOT)}')
    # 1. read and convert the whole unit, then validate it, before any collection is touched
    conn, source_db = connect_source(source_secret)
    cur = conn.cursor()
    loads = {name: documents(cur, spec[name]) for name in names}
    conn.close()
    for name in names:
        validate(name, spec[name], loads[name])
    db = MongoClient(os.environ[target_secret], appname=f'odoo-load-{unit_id}')[target_db]
    occupied = [n for n in names if db[n].estimated_document_count()]
    if occupied and not replace:
        raise SystemExit(f'{target_db}.{occupied} already hold documents: pass --replace to reload the whole unit '
                         f'(the ORM writes there once the models are opted in); nothing was changed')
    # 2. keep every collection's current documents and indexes so a failed reload is undone
    originals = {name: (list(db[name].find()), index_definitions(db[name])) for name in names}
    touched = []
    try:
        for name in names:
            touched.append(name)
            write_collection(db[name], loads[name], index_specs(spec[name]))
            arrays = ', '.join(f'{e["array_path"]}: {sum(len(d.get(e["array_path"], ())) for d in loads[name])} elements'
                               for e in spec[name]['embeds'])
            print(f'{spec[name]["root_table"]} ({source_db}) -> {target_db}.{name}: {len(loads[name])} documents, '
                  f'{len(db[name].index_information())} indexes' + (f' ({arrays})' if arrays else ''))
    except Exception as exc:
        problems = {name: restore_collection(db[name], *originals[name]) for name in touched}
        restored = [name for name in touched if not problems[name]]
        lost = {name: f['documents'] for name, f in problems.items() if 'documents' in f}
        unindexed = {name: f['indexes'] for name, f in problems.items() if 'indexes' in f}
        report = f'reload failed: {exc!r}; restored to pre-run state: {restored}'
        if lost:
            report += f'; DOCUMENTS NOT RESTORED (collection may be empty or partial): {lost}'
        if unindexed:
            report += f'; documents restored but indexes not rebuilt: {unindexed}'
        print(report, file=sys.stderr)
        if lost or unindexed:
            raise SystemExit(report) from exc
        raise

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--unit', required=True)
    parser.add_argument('--source-dsn-secret', required=True, help='ENV VAR NAME of the PostgreSQL JSON secret')
    parser.add_argument('--target-uri-secret', default='MONGODB_ATLAS_URI')
    parser.add_argument('--target-db', default=json.load(ALLOWED.open())['databases'][0])
    parser.add_argument('--replace', action='store_true', help='reload a unit whose collections already hold documents')
    args = parser.parse_args()
    load(args.unit, args.source_dsn_secret, args.target_uri_secret, args.target_db, args.replace)
