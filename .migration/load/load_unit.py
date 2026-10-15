#!/usr/bin/env python3
"""Load one migration unit's collections from the read-only PostgreSQL source.

Spec-driven: ``.migration/units.json`` names the unit's collections and write targets,
``.migration/mapping_spec.json`` names each collection's root table, fields, embeds and
indexes. Every collection of the unit is dropped and recreated (idempotent), its spec indexes
created, then the rows copied with ``_id`` = the PostgreSQL ``id`` (d-id-key keep-int-id),
NULL columns omitted (``null_missing_equiv``) and array embeds snapshotted from their relation
table as of the load. Writes only to the unit's write targets inside the allowed database.

Run from the recon venv (psycopg 3 + pymongo), secrets by ENV VAR NAME::

    recon/bin/python .migration/load/load_unit.py --unit product-taxonomy \
        --source-dsn-secret ODOO_PG_RO_DSN --target-uri-secret MONGODB_ATLAS_URI
"""
from __future__ import annotations

import argparse
import datetime as dt
import decimal
import json
import os
import sys
from pathlib import Path

import psycopg
import pymongo
from bson import Decimal128, Int64
from recon.adapters import parse_postgresql_secret

MIGRATION = Path(__file__).resolve().parents[1]


def quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def to_bson(value, bson_type: str):
    """psycopg value -> the spec's BSON type; None stays None (omitted from the document)."""
    if value is None:
        return None
    kind = bson_type.lower()
    if kind == 'int':
        return int(value)
    if kind == 'long':
        return Int64(value)
    if kind == 'double':
        return float(value)
    if kind in ('decimal', 'decimal128'):
        return Decimal128(value if isinstance(value, decimal.Decimal) else decimal.Decimal(str(value)))
    if kind == 'bool':
        return bool(value)
    if kind == 'date':
        if isinstance(value, dt.datetime):
            return value  # naive UTC; pymongo truncates to milliseconds (profile incompatibility)
        return dt.datetime(value.year, value.month, value.day)
    if kind == 'string':
        return str(value)
    if kind in ('object', 'array'):
        return value  # psycopg decodes json/jsonb and arrays
    if kind == 'bindata':
        return bytes(value)
    raise TypeError(f"unsupported bson_type {bson_type!r}")


def field_target(collection: dict, source: str) -> str:
    if source == 'id':
        return '_id'
    return next(f['target'] for f in collection['fields'] if f['source'] == source)


def create_indexes(coll, collection: dict) -> list[str]:
    created, seen = [], set()
    wanted = [([tuple(k) for k in ix['keys']], bool(ix.get('unique'))) for ix in collection.get('indexes', ())]
    wanted += [([(field_target(collection, col), 1) for col in nk['columns']], True)
               for nk in collection['decision'].get('natural_keys', ())]
    for keys, unique in wanted:
        if tuple(keys) in seen:
            continue
        seen.add(tuple(keys))
        created.append(coll.create_index(keys, unique=unique))
    return created


def snapshot_embed(cur, embed: dict) -> dict[int, list[dict]]:
    """Array embed elements grouped by parent id, as of the load (point-in-time snapshot)."""
    if embed.get('shape', 'array') != 'array':
        raise NotImplementedError(f"embed {embed['array_path']}: shape {embed['shape']!r}")
    (parent_col,) = embed['parent_key']
    elements: dict[str, dict] = {}
    for f in [{'source': s, 'target': t} for s, t in zip(embed['key']['source'], [embed['key']['target']]
                                                          if isinstance(embed['key']['target'], str)
                                                          else embed['key']['target'])]:
        elements.setdefault(f['target'], f)
    for f in list(embed.get('fields', ())) + list(embed.get('child_fields', ())):
        elements.setdefault(f['target'], f)
    for f in elements.values():
        f.setdefault('bson_type', next((cf['bson_type'] for cf in embed.get('child_fields', ())
                                        if cf['source'] == f['source']), 'int'))
    fields = list(elements.values())
    cols = [parent_col] + [f['source'] for f in fields]
    order = [parent_col] + list(embed['key']['source'])
    cur.execute(f"SELECT {', '.join(map(quote, cols))} FROM {quote(embed['child_table'])}"
                f" ORDER BY {', '.join(map(quote, order))}")
    by_parent: dict[int, list[dict]] = {}
    for row in cur:
        element = {f['target']: v for f, value in zip(fields, row[1:])
                   if (v := to_bson(value, f['bson_type'])) is not None}
        by_parent.setdefault(row[0], []).append(element)
    return by_parent


def load_collection(cur, db, collection: dict) -> dict:
    name, table = collection['collection'], collection['root_table']
    if collection['key'] != {'source': ['id'], 'target': '_id'}:
        raise NotImplementedError(f"{name}: key {collection['key']} is not the integer id")
    db.drop_collection(name)
    db.create_collection(name)
    coll = db[name]
    indexes = create_indexes(coll, collection)
    fields = collection['fields']
    cols = ['id'] + [f['source'] for f in fields]
    cur.execute(f"SELECT {', '.join(map(quote, cols))} FROM {quote(table)} ORDER BY {quote('id')}")
    docs = []
    for row in cur:
        doc = {'_id': row[0]}
        for f, value in zip(fields, row[1:]):
            if (v := to_bson(value, f['bson_type'])) is not None:
                doc[f['target']] = v
        docs.append(doc)
    embeds = {e['array_path']: snapshot_embed(cur, e) for e in collection.get('embeds', ())}
    for doc in docs:
        for path, by_parent in embeds.items():
            if elements := by_parent.get(doc['_id']):
                doc[path] = elements
    if docs:
        coll.insert_many(docs, ordered=True)
    return {'root_table': table, 'rows': len(docs), 'indexes': indexes,
            'embeds': {path: {'child_table': e['child_table'],
                              'elements': sum(len(v) for v in embeds[path].values())}
                       for e in collection.get('embeds', ()) for path in [e['array_path']]}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--unit', required=True, help="unit id in .migration/units.json")
    parser.add_argument('--source-dsn-secret', required=True,
                        help="ENV VAR NAME holding the PostgreSQL JSON secret (read-only role)")
    parser.add_argument('--target-uri-secret', default='MONGODB_ATLAS_URI',
                        help="ENV VAR NAME holding the target URI")
    parser.add_argument('--target-db', default=None,
                        help="defaults to the single database of .migration/allowed_targets.json")
    args = parser.parse_args()

    allowed = json.loads((MIGRATION / 'allowed_targets.json').read_text())['databases']
    target_db = args.target_db or allowed[0]
    if target_db not in allowed:
        sys.exit(f"refused: {target_db!r} is not in .migration/allowed_targets.json")
    units = json.loads((MIGRATION / 'units.json').read_text())
    unit = next((u for u in units['units'] if u['id'] == args.unit), None)
    if unit is None:
        sys.exit(f"refused: unit {args.unit!r} is not in .migration/units.json")
    for name in unit['collections']:
        if f"{target_db}.{name}" not in unit['write_targets']:
            sys.exit(f"refused: {target_db}.{name} is not a write target of {args.unit}")
    spec = json.loads((MIGRATION / 'mapping_spec.json').read_text())
    by_name = {c['collection']: c for c in spec['collections']}

    for secret in (args.source_dsn_secret, args.target_uri_secret):
        if not os.environ.get(secret):
            sys.exit(f"refused: environment variable {secret} is not set")
    params = parse_postgresql_secret(os.environ[args.source_dsn_secret])
    params.pop('schema', None)
    db = pymongo.MongoClient(os.environ[args.target_uri_secret], uuidRepresentation='standard')[target_db]
    with psycopg.connect(**params, autocommit=True) as conn:
        cur = conn.cursor()
        cur.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY")
        cur.execute("SET TIME ZONE 'UTC'")
        loaded = {name: load_collection(cur, db, by_name[name]) for name in unit['collections']}
    print(json.dumps({'unit': args.unit, 'source_database': params.get('dbname') or params.get('database'),
                      'target_db': target_db, 'mapping_version': spec['version'], 'loaded': loaded}, indent=2))


if __name__ == '__main__':
    main()
