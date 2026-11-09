#!/usr/bin/env python3
"""Fingerprint the run's frozen source database over a read-only session.

The fingerprint is sha256 over every public table's name, columns (name, type) and row
count, so a rebuild from build_source.sh can be checked against the recorded value.
Usage (with the Odoo venv python, which has psycopg2): source_fingerprint.py
       [--dsn-secret ODOO_PG_RO_DSN] [--dbname NAME] [--counts]
                             [--expect sha256:...]
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
    args = parser.parse_args()

    dsn = os.environ.get(args.dsn_secret)
    if not dsn:
        sys.exit(f'{args.dsn_secret} is not set')
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

    canonical = json.dumps(entries, sort_keys=True, separators=(',', ':'))
    fingerprint = 'sha256:' + hashlib.sha256(canonical.encode()).hexdigest()
    if args.counts:
        for entry in entries:
            print(f"{entry['table']}\t{entry['rows']}")
    print(json.dumps({
        'fingerprint': fingerprint,
        'tables': len(entries),
        'non_empty_tables': sum(1 for e in entries if e['rows']),
        'rows': sum(e['rows'] for e in entries),
    }))
    if args.expect and args.expect != fingerprint:
        sys.exit(f'fingerprint mismatch: expected {args.expect}')


if __name__ == '__main__':
    main()
