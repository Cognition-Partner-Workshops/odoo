#!/usr/bin/env python3
"""Load the product-attributes unit (batch w1-b03) from PostgreSQL into MongoDB.

Spec-driven: documents follow `.migration/mapping_spec.json` (field targets, bson types,
the `productTmplIds` id-array embed) and `_id` is the PostgreSQL integer id. Each run drops
and recreates the unit's collections and creates every spec index, so it is idempotent.
Writes only the unit's collections in the single `allowed_targets.json` database.

    python3 .migration/load/product_attributes.py --source-dsn-secret ODOO_PG_RO_DSN

The DSN secret is the JSON form the recon harness takes (psycopg2 keyword arguments).
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path

import psycopg2
import psycopg2.extras
import pymongo

MIGRATION_DIR = Path(__file__).resolve().parents[1]
UNIT = 'product-attributes'


def coerce(value, bson_type):
    if value is None:
        return None
    if bson_type == 'int':
        return int(value)
    if bson_type == 'double':
        return float(value)
    if bson_type == 'bool':
        return bool(value)
    if bson_type == 'string':
        return str(value)
    if bson_type == 'date':
        if isinstance(value, dt.date) and not isinstance(value, dt.datetime):
            return dt.datetime(value.year, value.month, value.day)
        return value
    return value


def document(row, fields):
    doc = {'_id': row['id']}
    for f in fields:
        value = coerce(row[f['source']], f['bson_type'])
        if value is None and 'null_missing_equiv' in f['rules']:
            continue
        doc[f['target']] = value
    return doc


def quoted(names):
    return ', '.join(f'"{n}"' for n in names)


def load_collection(cr, db, spec):
    fields = spec['fields']
    cr.execute(f'SELECT "id", {quoted(f["source"] for f in fields)} FROM "{spec["root_table"]}" ORDER BY "id"')
    docs = {row['id']: document(row, fields) for row in cr.fetchall()}
    for embed in spec.get('embeds', ()):
        parent_col = embed['parent_key'][0]
        child_fields = embed['child_fields']
        cr.execute(f'SELECT "{parent_col}", {quoted(f["source"] for f in child_fields)} '
                   f'FROM "{embed["child_table"]}" ORDER BY {quoted(embed["child_key"])}')
        for row in cr.fetchall():
            element = {f['target']: coerce(row[f['source']], f['bson_type']) for f in child_fields}
            docs[row[parent_col]].setdefault(embed['array_path'], []).append(element)
    name = spec['collection']
    db.drop_collection(name)
    coll = db.create_collection(name)
    if docs:
        coll.insert_many(list(docs.values()), ordered=True)
    for ix in spec.get('indexes', ()):
        coll.create_index([(k, pymongo.ASCENDING if d == 1 else pymongo.DESCENDING) for k, d in ix['keys']],
                          unique=bool(ix.get('unique')))
    return len(docs)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--source-dsn-secret', required=True, help='ENV VAR NAME holding the JSON PostgreSQL DSN')
    parser.add_argument('--target-uri-secret', default='MONGODB_ATLAS_URI', help='ENV VAR NAME holding the cluster URI')
    args = parser.parse_args()

    spec = json.loads((MIGRATION_DIR / 'mapping_spec.json').read_text())
    units = json.loads((MIGRATION_DIR / 'units.json').read_text())
    unit = next(u for u in units['units'] if u['id'] == UNIT)
    database = json.loads((MIGRATION_DIR / 'allowed_targets.json').read_text())['databases'][0]
    by_name = {c['collection']: c for c in spec['collections']}

    dsn = json.loads(os.environ[args.source_dsn_secret])
    pg = psycopg2.connect(**dsn)
    pg.set_session(readonly=True, autocommit=True)
    client = pymongo.MongoClient(os.environ[args.target_uri_secret], appname=f'odoo-load-{UNIT}')
    db = client[database]
    with pg.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cr:
        for name in unit['collections']:
            count = load_collection(cr, db, by_name[name])
            print(f'{database}.{name}: {count} documents')


if __name__ == '__main__':
    main()
