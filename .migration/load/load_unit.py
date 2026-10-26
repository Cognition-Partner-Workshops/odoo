#!/usr/bin/env python3
"""Spec-driven load of one unit's collections from PostgreSQL into the migration target.

    /home/ubuntu/.venvs/odoo/bin/python .migration/load/load_unit.py --unit accountLockException \\
        --source-dsn-secret ODOO_PG_RO_DSN [--source-db odoo_fixture] [--target-uri-secret MONGODB_ATLAS_URI] \\
        [--prefix odoo_w1b01_tour__] [--reload] [--report <path.json>]

The run's one shared loader (units.json ``shared_loader``): later batches call it, never a copy.
The unit's collections come from .migration/units.json and must all be write targets of the unit in the
allowed target database (odoo.orm.storage_mongodb.DATABASE, the only entry of .migration/allowed_targets.json);
rows, field targets, embeds and indexes come from the signed .migration/mapping_spec.json, read through
odoo.orm.storage_mongodb so its sha256 is checked. Values go through the storage path's own encoder, so a
loaded document is what ``_storage = 'mongodb'`` writes: ``_id`` = id, NULL columns omitted
(null_missing_equiv), a relation table mapped to its own collection as one document per row holding its key
columns. Each spec ``embeds[]`` entry becomes one array per parent document shaped as the ORM pushes it: a
child table's element is its id (the spec's id target) then its child fields in mapping order, NULLs omitted,
elements in (parent, child id) order; a junction table's element is the other side's id only; a parent
without children carries no array. Indexes are built by storage_mongodb's own index routine, so the ORM's
``ensure_indexes`` finds them as it would have made them. One PostgreSQL connection, one REPEATABLE READ
read-only snapshot for roots and embeds, serial reads: source concurrency 1.

Every run clears the unit's collections first; a collection that already holds documents needs --reload,
since once the model is opted in the collection is the system of record and a reload discards every edit
made through the ORM. A failed run restores the documents and indexes it found. --source-db swaps the
database of the JSON DSN (the fixture clone or a seeded copy; the role and host stay). --prefix writes
scratch copies ``<prefix><collection>`` (a PostgreSQL copy's ``<copy>__`` namespace, as
storage_mongodb.collection_prefix names it) instead of the write targets, for tests and tours; the prefix
must end with ``__`` and the caller clears it afterwards. Secrets are read by name from the environment and
never printed.
"""
import argparse
import json
import os
import sys
from pathlib import Path

import bson
import psycopg2
from pymongo import MongoClient

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT)]
from odoo.orm import storage_mongodb  # noqa: E402

UNITS = ROOT / '.migration' / 'units.json'
ALLOWED = ROOT / '.migration' / 'allowed_targets.json'
TARGET_DB = storage_mongodb.DATABASE


def connect_target(secret_name, unit_id):
    return MongoClient(os.environ[secret_name], appname=f'odoo-load-{unit_id}').get_database(TARGET_DB)


def unit_entry(unit_id):
    unit = next((u for u in json.load(UNITS.open())['units'] if u['id'] == unit_id), None)
    if unit is None:
        raise SystemExit(f'unit {unit_id!r} is not in {UNITS.relative_to(ROOT)}')
    return unit


def unit_specs(unit):
    """The unit's collections from the signed spec, checked against units.json and the unit's write targets."""
    by_name = {spec['collection']: spec for spec in storage_mongodb._spec_tables().values()}
    specs = []
    for entry in unit['collections']:
        name = entry['collection']
        if f'{TARGET_DB}.{name}' not in unit['write_targets']:
            raise SystemExit(f'{TARGET_DB}.{name} is not a write target of {unit["id"]}: plan gap, halt')
        spec = by_name.get(name)
        if spec is None:
            raise SystemExit(f'{name} is not in the signed mapping spec')
        if spec['root_table'] != entry['root_table']:
            raise SystemExit(f'{name}: units.json says table {entry["root_table"]!r}, the spec says {spec["root_table"]!r}')
        declared = sorted(entry['embedded_tables'])
        embedded = sorted(embed['child_table'] for embed in spec['embeds'])
        if declared != embedded:
            raise SystemExit(f'{unit["id"]} declares embeds {declared} for {name} but the spec embeds {embedded}: plan gap, halt')
        specs.append(spec)
    return specs


def connect_source(secret_name, database):
    params = json.loads(os.environ[secret_name])
    database = database or params['database']
    conn = psycopg2.connect(dbname=database, **{k: params[k] for k in ('user', 'password', 'host', 'port')})
    conn.set_session(readonly=True, isolation_level='REPEATABLE READ')   # one snapshot for roots and embeds
    return conn, database


def select(cur, table, columns, order):
    def ident(name):
        return '"' + name + '"'
    cur.execute(f'SELECT {", ".join(map(ident, columns))} FROM {ident(table)} ORDER BY {", ".join(map(ident, order))}')
    return cur.fetchall()


def convert(fields, values, into):
    for field, value in zip(fields, values, strict=True):
        value = storage_mongodb._to_bson(field['bson_type'], value)
        if value is not None:       # null_missing_equiv: NULL is a missing key, as the ORM writes it
            into[field['target']] = value
    return into


def is_junction(embed):
    """A many2many relation table embedded as an array of the other side's ids (storage_mongodb._spec_relations)."""
    return not embed['fields'] and len(embed['child_fields']) == 1 and len(embed['parent_key']) == 1


def documents(cur, spec):
    key = spec['key']
    if isinstance(key['target'], list):
        if spec['fields'] or spec['embeds']:
            raise SystemExit(f'{spec["collection"]}: a composite-key collection with fields or embeds is not supported')
        return relation_documents(cur, spec)
    if key['source'] != ['id'] or key['target'] != '_id':
        raise SystemExit(f'{spec["collection"]}: only roots keyed id -> _id are supported')
    fields = spec['fields']
    docs = {row[0]: convert(fields, row[1:], {'_id': row[0]})
            for row in select(cur, spec['root_table'], ['id'] + [f['source'] for f in fields], ['id'])}
    for embed in spec['embeds']:
        embed_elements(cur, spec, embed, docs)
    return list(docs.values())


def relation_documents(cur, spec):
    """A relation table mapped to its own collection: one document per row holding the key columns under
    their target names, as the storage path writes links (``_id`` is left to the server)."""
    key = spec['key']
    types = {f['source']: f['bson_type'] for f in spec['decision'].get('key_fields', [])}
    fields = [{'source': s, 'target': t, 'bson_type': types.get(s, 'int')}
              for s, t in zip(key['source'], key['target'], strict=True)]
    return [convert(fields, row, {}) for row in select(cur, spec['root_table'], key['source'], key['source'])]


def embed_elements(cur, spec, embed, docs):
    """Append each child row to its parent's array, shaped as storage_mongodb pushes elements."""
    path = f'{spec["collection"]}.{embed["array_path"]}'
    if (embed.get('shape', 'array') != 'array' or embed.get('overflow') or embed.get('parent_ref', ['id']) != ['id']
            or len(embed['parent_key']) != 1):
        raise SystemExit(f'{path}: only plain arrays under a parent keyed by id are supported (no overflow, no subdocument)')
    parent = embed['parent_key'][0]
    if is_junction(embed):
        other = embed['child_fields'][0]
        fields, order = [other], [parent, other['source']]
    else:
        by_source = {f['source']: f for f in embed['child_fields']}
        if 'id' not in by_source:
            raise SystemExit(f'{path}: child_fields carry no id, the element key the storage path writes')
        fields = [by_source['id']] + [f for f in embed['child_fields'] if f['source'] not in ('id', parent)]
        order = [parent, 'id']
    for row in select(cur, embed['child_table'], [parent] + [f['source'] for f in fields], order):
        doc = docs.get(row[0])
        if doc is None:
            raise SystemExit(f'{path}: {embed["child_table"]}.{parent}={row[0]!r} has no parent document; nothing was changed')
        doc.setdefault(embed['array_path'], []).append(convert(fields, row[1:], {}))


def validate(spec, docs):
    """Refuse up front what the target would refuse mid-load: unencodable documents and duplicate keys of a
    unique index without a spec filter (over documents holding every key, as the ORM's partial indexes)."""
    for doc in docs:
        bson.encode(doc)
    for index in spec['indexes']:
        if not index.get('unique') or index.get('partialFilterExpression'):
            continue
        paths = [path for path, _ in index['keys']]
        seen = set()
        for doc in docs:
            if any(path not in doc for path in paths):
                continue
            key = bson.encode({path: doc[path] for path in paths})
            if key in seen:
                raise SystemExit(f'{spec["collection"]}: duplicate value for unique index {paths} at _id={doc.get("_id", doc)}; nothing was changed')
            seen.add(key)


def index_definitions(coll):
    """Every index of a live collection except _id, with its full options, so a restore recreates it as it was."""
    return [(list(info['key'].items()), {k: v for k, v in info.items() if k not in ('key', 'v', 'ns')})
            for info in coll.list_indexes() if info['name'] != '_id_']


def write_collection(db, name, docs, spec):
    db.drop_collection(name)
    coll = db.get_collection(name)
    if docs:
        coll.insert_many(docs, ordered=True)
    storage_mongodb._create_indexes(coll, spec['indexes'])
    return coll


def restore_collection(db, name, docs, indexes):
    """Documents back first, then every index; returns what failed, by stage."""
    failed = {}
    try:
        db.drop_collection(name)
        if docs:
            db.get_collection(name).insert_many(docs, ordered=True)
    except Exception as exc:  # noqa: BLE001
        failed['documents'] = repr(exc)
        return failed
    for keys, options in indexes:
        try:
            db.get_collection(name).create_index(keys, **options)
        except Exception as exc:  # noqa: BLE001
            failed.setdefault('indexes', []).append(f'{options.get("name")}: {exc!r}')
    return failed


def load(unit_id, source_secret, source_db, target_secret, prefix, reload, report_path):
    if TARGET_DB not in json.load(ALLOWED.open())['databases']:
        raise SystemExit(f'{TARGET_DB} is not in {ALLOWED.relative_to(ROOT)}')
    if prefix and not prefix.endswith('__'):
        raise SystemExit('--prefix must end with "__", a PostgreSQL copy\'s namespace (storage_mongodb.collection_prefix)')
    unit = unit_entry(unit_id)
    specs = unit_specs(unit)
    # 1. read and convert the whole unit on one snapshot, then validate it, before any collection is touched
    conn, database = connect_source(source_secret, source_db)
    loads = {spec['collection']: documents(conn.cursor(), spec) for spec in specs}
    conn.close()
    for spec in specs:
        validate(spec, loads[spec['collection']])
    db = connect_target(target_secret, unit_id)
    names = {spec['collection']: prefix + spec['collection'] for spec in specs}
    occupied = [name for name in names.values() if db.get_collection(name).estimated_document_count()]
    if occupied and not reload:
        raise SystemExit(f'{TARGET_DB}.{occupied} already hold documents: pass --reload to load the whole unit again '
                         f'(the ORM writes there once the models are opted in); nothing was changed')
    # 2. keep every collection's current documents and indexes so a failed load is undone
    originals = {name: (list(db.get_collection(name).find()), index_definitions(db.get_collection(name)))
                 for name in names.values()}
    touched, summary = [], {}
    try:
        for spec in specs:
            name, docs = names[spec['collection']], loads[spec['collection']]
            touched.append(name)
            coll = write_collection(db, name, docs, spec)
            elements = {e['array_path']: sum(len(d.get(e['array_path'], ())) for d in docs) for e in spec['embeds']}
            summary[name] = {'root_table': spec['root_table'], 'documents': len(docs), 'elements': elements,
                             'indexes': sorted(coll.index_information())}
            shown = ''.join(f', {count} {path}' for path, count in elements.items())
            print(f'{spec["root_table"]} ({database}) -> {TARGET_DB}.{name}: {len(docs)} documents{shown}, '
                  f'{len(summary[name]["indexes"])} indexes')
    except Exception as exc:
        problems = {name: restore_collection(db, name, *originals[name]) for name in touched}
        restored = [name for name in touched if not problems[name]]
        lost = {name: f['documents'] for name, f in problems.items() if 'documents' in f}
        unindexed = {name: f['indexes'] for name, f in problems.items() if 'indexes' in f}
        report = f'load failed: {exc!r}; restored to the pre-run state: {restored}'
        if lost:
            report += f'; DOCUMENTS NOT RESTORED (collection may be empty or partial): {lost}'
        if unindexed:
            report += f'; documents restored but indexes not rebuilt: {unindexed}'
        print(report, file=sys.stderr)
        if lost or unindexed:
            raise SystemExit(report) from exc
        raise
    if report_path:
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)
        Path(report_path).write_text(json.dumps({
            'unit': unit_id, 'source_db': database, 'target_db': TARGET_DB, 'prefix': prefix,
            'mapping_version': json.loads(storage_mongodb.SPEC_PATH.read_bytes())['version'],
            'source_concurrency': 1, 'collections': summary}, indent=1, default=str) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--unit', required=True)
    parser.add_argument('--source-dsn-secret', required=True,
                        help='ENV VAR NAME of the PostgreSQL JSON secret {user,password,host,port,database}')
    parser.add_argument('--source-db', help="read this database instead of the secret's (fixture clone, seeded copy)")
    parser.add_argument('--target-uri-secret', default='MONGODB_ATLAS_URI', help='ENV VAR NAME of the target URI')
    parser.add_argument('--prefix', default='', help='scratch namespace <prefix><collection> (ends with __) instead of the write targets')
    parser.add_argument('--reload', action='store_true', help='load a unit whose collections already hold documents')
    parser.add_argument('--report', help='write a JSON load summary to this path')
    args = parser.parse_args()
    load(args.unit, args.source_dsn_secret, args.source_db, args.target_uri_secret, args.prefix, args.reload, args.report)
