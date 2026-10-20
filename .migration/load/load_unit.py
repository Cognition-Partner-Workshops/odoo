#!/usr/bin/env python3
"""Spec-driven initial load of one unit's root collections from PostgreSQL into the migration target.

    /home/ubuntu/.venvs/odoo/bin/python .migration/load/load_unit.py --unit stock-reference \\
        --source-dsn-secret ODOO_SCENARIO_DSN [--target-uri-secret MONGODB_ATLAS_URI] \\
        [--target-db odoo_unt12] [--replace]

The unit's collections come from .migration/units.json and must all be write targets of the unit
in --target-db; rows, field targets and indexes come from .migration/mapping_spec.json; values go
through the ORM's own ``odoo.orm.storage_mongodb.to_bson`` so a loaded document is what
``_storage = 'mongodb'`` would have written (NULL columns are omitted: ``null_missing_equiv``).
Flat root collections only (this unit embeds nothing). Every run empties the collection first;
a non-empty collection needs --replace: once the model is opted in the collection is the
system of record and a reload discards every edit made through the ORM. Secrets are read by name
from the environment (the PostgreSQL one is the plugin's JSON shape) and never printed.
"""
import argparse
import json
import os
import sys
from pathlib import Path

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
    if unit['embedded_tables']:
        raise SystemExit(f'{unit_id} embeds {unit["embedded_tables"]}: this loader handles flat roots only')
    return unit['collections']


def connect_source(secret_name):
    params = json.loads(os.environ[secret_name])
    conn = psycopg2.connect(dbname=params['database'], **{k: params[k] for k in ('user', 'password', 'host', 'port')})
    conn.set_session(readonly=True, autocommit=True)
    return conn, params['database']


def documents(cur, coll_spec):
    if coll_spec['embeds'] or coll_spec['key']['source'] != ['id'] or coll_spec['key']['target'] != '_id':
        raise SystemExit(f'{coll_spec["collection"]}: only flat roots keyed by id -> _id are supported')
    fields = coll_spec['fields']
    columns = ['id'] + [f['source'] for f in fields]
    cur.execute(f'SELECT {", ".join(chr(34) + c + chr(34) for c in columns)} FROM "{coll_spec["root_table"]}" ORDER BY id')
    docs = []
    for row in cur.fetchall():
        doc = {'_id': int(row[0])}
        for field, value in zip(fields, row[1:]):
            value = to_bson(value, field['bson_type'])
            if value is not None:
                doc[field['target']] = value
        docs.append(doc)
    return docs


def load(unit_id, source_secret, target_secret, target_db, replace):
    if target_db not in json.load(ALLOWED.open())['databases']:
        raise SystemExit(f'{target_db} is not in {ALLOWED.relative_to(ROOT)}')
    names = unit_collections(unit_id, target_db)
    spec = {c['collection']: c for c in json.load(MAPPING.open())['collections']}
    missing = [n for n in names if n not in spec]
    if missing:
        raise SystemExit(f'{missing} are not in {MAPPING.relative_to(ROOT)}')
    conn, source_db = connect_source(source_secret)
    db = MongoClient(os.environ[target_secret], appname=f'odoo-load-{unit_id}')[target_db]
    cur = conn.cursor()
    for name in names:
        docs = documents(cur, spec[name])
        coll = db[name]
        if coll.estimated_document_count() and not replace:
            raise SystemExit(f'{target_db}.{name} already holds documents: pass --replace to reload it '
                             '(the ORM writes here once the model is opted in)')
        coll.drop()
        if docs:
            coll.insert_many(docs, ordered=True)
        for index in spec[name].get('indexes', []):  # the entries MongoStore.ensure_indexes creates
            keys = index.get('keys')
            if not isinstance(keys, list) or not keys:
                continue
            key_spec = [(k[0], k[1]) if isinstance(k, list) else (k, ASCENDING) for k in keys]
            if key_spec != [('_id', ASCENDING)]:
                coll.create_index(key_spec, unique=bool(index.get('unique')))
        print(f'{spec[name]["root_table"]} ({source_db}) -> {target_db}.{name}: {len(docs)} documents, '
              f'{len(coll.index_information())} indexes')
    conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--unit', required=True)
    parser.add_argument('--source-dsn-secret', required=True, help='ENV VAR NAME of the PostgreSQL JSON secret')
    parser.add_argument('--target-uri-secret', default='MONGODB_ATLAS_URI')
    parser.add_argument('--target-db', default=json.load(ALLOWED.open())['databases'][0])
    parser.add_argument('--replace', action='store_true', help='reload collections that already hold documents')
    args = parser.parse_args()
    load(args.unit, args.source_dsn_secret, args.target_uri_secret, args.target_db, args.replace)
