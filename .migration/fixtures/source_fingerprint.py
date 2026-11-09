#!/usr/bin/env python3
"""Fingerprint the run's frozen source database over a read-only session.

The fingerprint is sha256 over every public table's name, columns (name, type) and row
count, so a rebuild from build_source.sh can be checked against the recorded value.
Usage (with the Odoo venv python, which has psycopg2): source_fingerprint.py
       [--dsn-secret ODOO_PG_RO_DSN] [--dbname NAME] [--counts]
                             [--expect sha256:...] [--volatile-table NAME ...]

Volatile tables (default: bus_bus, Odoo's transient notification queue) keep their name and
columns in the hash but not their row count, which varies between builds of the same recipe.
"""
import argparse
import hashlib
import json
import os
import sys

import psycopg2
from psycopg2 import sql

TABLES = """
    select c.relname from pg_class c join pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'public' and c.relkind in ('r', 'p') order by c.relname
"""
COLUMNS = """
    select table_name, column_name, data_type from information_schema.columns
    where table_schema = 'public' order by table_name, column_name
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dsn-secret', default='ODOO_PG_RO_DSN')
    parser.add_argument('--dbname', help='override the database named by the secret')
    parser.add_argument('--counts', action='store_true', help='print per-table row counts')
    parser.add_argument('--expect', help='exit 1 unless the fingerprint equals this value')
    parser.add_argument('--volatile-table', action='append', dest='volatile',
                        help='table whose row count is left out of the hash (repeatable; default bus_bus)')
    args = parser.parse_args()
    volatile = set(args.volatile or ['bus_bus'])

    dsn = os.environ.get(args.dsn_secret)
    if not dsn:
        sys.exit(f'{args.dsn_secret} is not set')
    if dsn.lstrip().startswith('{'):
        # the mongo-migration plugin's PostgreSQL JSON shape {user, password, host, port, database}
        params = json.loads(dsn)
        dsn = psycopg2.extensions.make_dsn(
            user=params['user'], password=params['password'], host=params['host'],
            port=params.get('port', 5432), dbname=params['database'])
    conn = psycopg2.connect(dsn, **({'dbname': args.dbname} if args.dbname else {}))
    conn.set_session(readonly=True)
    cur = conn.cursor()
    cur.execute(TABLES)
    tables = [name for (name,) in cur.fetchall()]
    cur.execute(COLUMNS)
    columns = {}
    for table, column, data_type in cur.fetchall():
        columns.setdefault(table, []).append([column, data_type])
    entries = []
    for table in tables:
        cur.execute(sql.SQL('select count(*) from {}').format(sql.Identifier(table)))
        entries.append({'table': table, 'columns': columns.get(table, []), 'rows': cur.fetchone()[0]})
    conn.close()

    hashed = [{k: v for k, v in e.items() if not (k == 'rows' and e['table'] in volatile)}
              for e in entries]
    canonical = json.dumps(hashed, sort_keys=True, separators=(',', ':'))
    fingerprint = 'sha256:' + hashlib.sha256(canonical.encode()).hexdigest()
    if args.counts:
        for entry in entries:
            print(f"{entry['table']}\t{entry['rows']}")
    print(json.dumps({
        'fingerprint': fingerprint,
        'tables': len(entries),
        'non_empty_tables': sum(1 for e in entries if e['rows']),
        'rows': sum(e['rows'] for e in entries),
        'volatile_tables': sorted(volatile),
    }))
    if args.expect and args.expect != fingerprint:
        sys.exit(f'fingerprint mismatch: expected {args.expect}')


if __name__ == '__main__':
    main()
