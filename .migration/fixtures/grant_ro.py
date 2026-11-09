#!/usr/bin/env python3
"""Grant the read-only role named by the ODOO_PG_RO_DSN secret SELECT on every public table of a source database.

Usage: grant_ro.py <db_name>  (Odoo venv python, which has psycopg2; ubuntu superuser on the 5433 cluster)
"""
import json, os, sys
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import parse_dsn

db = sys.argv[1]
raw = os.environ['ODOO_PG_RO_DSN']
# the probe's PostgreSQL JSON shape {user, password, host, port, database}, or a libpq DSN
ro = json.loads(raw) if raw.lstrip().startswith('{') else parse_dsn(raw)
role = sql.Identifier(ro['user'])
for target in ('postgres', db):
    conn = psycopg2.connect(dbname=target, host='/var/run/postgresql', port=5433)
    conn.autocommit = True
    cur = conn.cursor()
    if target == 'postgres':
        cur.execute("select 1 from pg_roles where rolname = %s", [ro['user']])
        verb = 'ALTER' if cur.fetchone() else 'CREATE'
        cur.execute(sql.SQL(verb + " ROLE {} LOGIN PASSWORD %s").format(role), [ro['password']])
        cur.execute(sql.SQL("ALTER ROLE {} SET default_transaction_read_only = on").format(role))
    else:
        cur.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(sql.Identifier(db), role))
        cur.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(role))
        cur.execute(sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA public TO {}").format(role))
    conn.close()
print('GRANT OK')
