#!/usr/bin/env python3
"""Spec-driven initial load of one unit's collections from PostgreSQL into the migration target.

    /home/ubuntu/.venvs/odoo/bin/python .migration/load/load_unit.py --unit stock-reference \\
        --source-dsn-secret ODOO_SCENARIO_DSN [--target-uri-secret MONGODB_ATLAS_URI] \\
        [--target-db odoo_unt12] [--replace]

The unit's collections come from .migration/units.json and must all be write targets of the unit
in --target-db; rows, field targets and indexes come from .migration/mapping_spec.json; values go
through the ORM's own ``odoo.orm.storage_mongodb.to_bson`` so a loaded document is what
``_storage = 'mongodb'`` would have written (NULL columns are omitted: ``null_missing_equiv``).
Roots are keyed id -> _id; each spec ``embeds[]`` entry (One2many children keyed by ``id``, Many2many
relation tables keyed by the other side's id) becomes one array per parent document, its elements
shaped as ``storage_mongodb.create`` pushes them (the child fields in mapping order, NULLs omitted,
in child key order); a parent without children carries no array. Every run empties the collection first;
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
    return unit['collections'], unit['embedded_tables']


def connect_source(secret_name):
    params = json.loads(os.environ[secret_name])
    conn = psycopg2.connect(dbname=params['database'], **{k: params[k] for k in ('user', 'password', 'host', 'port')})
    conn.set_session(readonly=True, isolation_level='REPEATABLE READ')  # one snapshot for roots and embeds
    return conn, params['database']


def select(cur, table, columns, order):
    cur.execute(f'SELECT {", ".join(chr(34) + c + chr(34) for c in columns)} FROM "{table}" '
                f'ORDER BY {", ".join(chr(34) + c + chr(34) for c in order)}')
    return cur.fetchall()


def convert(fields, values, into):
    for field, value in zip(fields, values):
        value = to_bson(value, field['bson_type'])
        if value is not None:
            into[field['target']] = value
    return into


def relation_documents(cur, coll_spec):
    """A relation table kept as its own collection, keyed by its natural (composite) key: one document per
    pair, shaped as the storage path writes them (``{column1Target: id, column2Target: id}``, _id left to the
    driver)."""
    key = coll_spec['key']
    if coll_spec['fields'] or coll_spec['embeds'] or len(key['source']) != 2 or len(key['target']) != 2:
        raise SystemExit(f'{coll_spec["collection"]}: only two-column relation tables without fields or embeds are supported')
    return [dict(zip(key['target'], map(int, row))) for row in select(cur, coll_spec['root_table'], key['source'], key['source'])]


def documents(cur, coll_spec):
    if isinstance(coll_spec['key']['target'], list):
        return relation_documents(cur, coll_spec)
    if coll_spec['key']['source'] != ['id'] or coll_spec['key']['target'] != '_id':
        raise SystemExit(f'{coll_spec["collection"]}: only roots keyed by id -> _id are supported')
    fields = coll_spec['fields']
    docs = {int(row[0]): convert(fields, row[1:], {'_id': int(row[0])})
            for row in select(cur, coll_spec['root_table'], ['id'] + [f['source'] for f in fields], ['id'])}
    for embed in coll_spec['embeds']:
        embed_elements(cur, coll_spec['collection'], embed, docs)
    return list(docs.values())


def embed_elements(cur, name, embed, docs):
    """Append each child row to its parent's array, in (parent, child key) order."""
    path = f'{name}.{embed["array_path"]}'
    fields = embed['child_fields']
    if (embed['shape'] != 'array' or embed.get('parent_ref') != ['id'] or len(embed['parent_key']) != 1
            or embed.get('overflow') or any(k not in [f['source'] for f in fields] for k in embed['key']['source'])):
        raise SystemExit(f'{path}: only arrays keyed by child columns under a parent keyed by id are supported')
    parent = embed['parent_key'][0]
    order = [parent] + [c for c in embed['child_key'] if c != parent]
    for row in select(cur, embed['child_table'], [parent] + [f['source'] for f in fields], order):
        doc = docs.get(int(row[0]))
        if doc is None:
            raise SystemExit(f'{path}: {embed["child_table"]}.{parent}={row[0]!r} has no parent document; nothing was changed')
        doc.setdefault(embed['array_path'], []).append(convert(fields, row[1:], {}))


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
                raise SystemExit(f'{name}: duplicate value for unique index {key_spec} at {doc.get("_id", doc)}; nothing was changed')
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
    names, embedded_tables = unit_collections(unit_id, target_db)
    spec = {c['collection']: c for c in json.load(MAPPING.open())['collections']}
    missing = [n for n in names if n not in spec]
    if missing:
        raise SystemExit(f'{missing} are not in {MAPPING.relative_to(ROOT)}')
    embedded = sorted((n, e['array_path'], e['child_table']) for n in names for e in spec[n]['embeds'])
    declared = sorted((e['collection'], e['array_path'], e['table']) for e in embedded_tables)
    if embedded != declared:
        raise SystemExit(f'{unit_id} declares embeds {declared} but the spec embeds {embedded}: plan gap, halt')
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
            elements = ', '.join(f'{sum(len(d.get(e["array_path"], ())) for d in loads[name])} {e["array_path"]}'
                                 for e in spec[name]['embeds'])
            print(f'{spec[name]["root_table"]} ({source_db}) -> {target_db}.{name}: {len(loads[name])} documents'
                  f'{" (" + elements + " elements)" if elements else ""}, {len(db[name].index_information())} indexes')
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
