#!/usr/bin/env python3
"""Fingerprint the run's frozen source database over a read-only session.

The fingerprint is sha256 over every public table's name, columns (name, type) and row
count, so a rebuild from build_source.sh can be checked against the recorded value.
Usage (with the Odoo venv python, which has psycopg2): source_fingerprint.py
       [--dsn-secret ODOO_PG_RO_DSN] [--dbname NAME] [--counts]
                             [--expect sha256:...] [--volatile-table NAME ...]
                             [--content [--table-hashes]]

Volatile tables (default: bus_bus, Odoo's transient notification queue) keep their name and
columns in the hash but not their row count, which varies between builds of the same recipe.
"""
import argparse
import hashlib
import json
import os
import sys
import tempfile

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


def contentSummary(conn, volatile, perTable=False):
    conn.set_session(readonly=True, isolation_level='REPEATABLE READ')
    conn.set_client_encoding('UTF8')
    with conn.cursor() as cur:
        cur.execute("SET LOCAL TimeZone = 'UTC'")
        cur.execute("SET LOCAL DateStyle = 'ISO, YMD'")
        cur.execute("SET LOCAL extra_float_digits = 1")
        cur.execute("SET LOCAL bytea_output = 'hex'")
        cur.execute("SET LOCAL IntervalStyle = 'postgres'")
        cur.execute(TABLES)
        tables = [name for (name,) in cur.fetchall() if name not in volatile]
        cur.execute(COLUMNS)
        allColumns = cur.fetchall()
        tableHashes = {}
        for table in tables:
            columns = [column for name, column, _ in allColumns if name == table]
            cur.execute("""
                select a.attname from pg_index i
                join pg_class c on c.oid = i.indrelid
                join pg_namespace n on n.oid = c.relnamespace
                cross join lateral unnest(i.indkey) with ordinality k(attnum, position)
                join pg_attribute a on a.attrelid = c.oid and a.attnum = k.attnum
                where n.nspname = 'public' and c.relname = %s and i.indisprimary
                order by k.position
            """, [table])
            primaryKey = [name for (name,) in cur.fetchall()]
            orderColumns = [sql.Identifier(name) for name in primaryKey] if primaryKey else [
                sql.SQL('{}::text COLLATE "C"').format(sql.Identifier(name)) for name in columns]
            query = sql.SQL('COPY (SELECT {} FROM {} ORDER BY {}) TO STDOUT').format(
                sql.SQL(', ').join(map(sql.Identifier, columns)),
                sql.Identifier('public', table), sql.SQL(', ').join(orderColumns))
            with tempfile.TemporaryFile() as rowsFile:
                cur.copy_expert(query.as_string(conn), rowsFile)
                rowsFile.seek(0)
                tableHashes[table] = hashlib.file_digest(rowsFile, 'sha256').hexdigest()
    canonical = json.dumps(tableHashes, sort_keys=True, separators=(',', ':'))
    summary = {
        'fingerprint': 'sha256:' + hashlib.sha256(canonical.encode()).hexdigest(),
        'tables': len(tableHashes),
        'excluded_tables': sorted(volatile),
    }
    if perTable:
        summary['table_hashes'] = tableHashes
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dsn-secret', default='ODOO_PG_RO_DSN')
    parser.add_argument('--dbname', help='override the database named by the secret')
    parser.add_argument('--counts', action='store_true', help='print per-table row counts')
    parser.add_argument('--content', action='store_true', help='hash ordered row contents instead of schema/counts')
    parser.add_argument('--table-hashes', action='store_true', help='include per-table hashes in content mode')
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
    if args.content:
        try:
            summary = contentSummary(conn, volatile, args.table_hashes)
        finally:
            conn.close()
        print(json.dumps(summary))
        if args.expect and args.expect != summary['fingerprint']:
            sys.exit(f'fingerprint mismatch: expected {args.expect}')
        return
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
