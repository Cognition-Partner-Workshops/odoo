"""Spec-driven bulk load of one mapping collection from PostgreSQL into the migration target.

Reads the root table named by ``.migration/mapping_spec.json``, converts each column to the
mapped BSON type, replaces the collection and creates the spec/natural-key/parent_path indexes
the ORM storage expects.  Secrets are read by name from the environment, never printed.

    python .migration/load/load_collection.py --collection uomUom \
        --source-dsn-secret ODOO_PG_RO_DSN --target-uri-secret MONGODB_ATLAS_URI
"""
import argparse
import datetime
import decimal
import json
import os
import sys
from pathlib import Path

import psycopg
import pymongo
from bson.decimal128 import Decimal128
from recon.adapters import parse_postgresql_secret

ROOT = Path(__file__).resolve().parents[2]
MAPPING = ROOT / '.migration' / 'mapping_spec.json'
ALLOWED = ROOT / '.migration' / 'allowed_targets.json'


def to_bson(value, bson_type):
    if value is None:
        return None
    if bson_type == 'decimal':
        return Decimal128(decimal.Decimal(str(value)))
    if bson_type == 'date':
        if isinstance(value, datetime.datetime) and value.tzinfo is None:
            value = value.replace(tzinfo=datetime.timezone.utc)
        return value
    if bson_type == 'int':
        return int(value)
    if bson_type == 'bool':
        return bool(value)
    if bson_type == 'string':
        return str(value)
    if bson_type == 'object':
        return value if isinstance(value, dict) else json.loads(value)
    return value


def load(collection_name, source_secret, target_secret, target_db):
    spec = json.load(MAPPING.open())
    coll_spec = next(c for c in spec['collections'] if c['collection'] == collection_name)
    if target_db not in json.load(ALLOWED.open())['databases']:
        raise SystemExit(f'{target_db} is not in {ALLOWED.relative_to(ROOT)}')
    if coll_spec.get('embeds') or len(coll_spec['key']['source']) != 1:
        raise SystemExit('only flat collections with a single-column key are supported')

    key_col = coll_spec['key']['source'][0]
    fields = [(f['source'], f['target'], f['bson_type']) for f in coll_spec['fields']]
    columns = [key_col] + [src for src, _, _ in fields]
    table = coll_spec['root_table']
    where = coll_spec.get('root_where') or 'TRUE'
    sql = f'SELECT {", ".join(columns)} FROM {table} WHERE {where} ORDER BY {key_col}'

    pg_params = parse_postgresql_secret(os.environ[source_secret])
    pg_params.pop('schema', None)
    with psycopg.connect(**pg_params) as conn, conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()

    docs = []
    for row in rows:
        doc = {'_id': int(row[0])}
        for (src, target, bson_type), value in zip(fields, row[1:]):
            value = to_bson(value, bson_type)
            if value is not None:
                doc[target] = value
        docs.append(doc)

    client = pymongo.MongoClient(os.environ[target_secret], appname=f'odoo-load-{collection_name}')
    coll = client[target_db][collection_name]
    coll.drop()
    if docs:
        coll.insert_many(docs, ordered=True)
    for index in coll_spec.get('indexes', []):
        coll.create_index([(k, int(d)) for k, d in index['keys']])
    for nk in coll_spec.get('decision', {}).get('natural_keys', []):
        targets = [(t, b) for s, t, b in fields if s in nk['columns']]
        coll.create_index(
            [(t, 1) for t, _ in targets], name=nk['name'], unique=True,
            partialFilterExpression={t: {'$type': b} for t, b in targets})
    print(f'{table} -> {target_db}.{collection_name}: {len(docs)} documents, '
          f'{len(coll.index_information())} indexes (source db {pg_params["dbname"]})')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--collection', required=True)
    parser.add_argument('--source-dsn-secret', required=True)
    parser.add_argument('--target-uri-secret', default='MONGODB_ATLAS_URI')
    parser.add_argument('--target-db', default='odoo_migration')
    args = parser.parse_args()
    sys.exit(load(args.collection, args.source_dsn_secret, args.target_uri_secret, args.target_db))
