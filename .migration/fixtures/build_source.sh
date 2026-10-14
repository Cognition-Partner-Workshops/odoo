#!/usr/bin/env bash
# Build the read-only Odoo source database odoo_src (product + uom, demo data)
# and the SELECT-only role odoo_ro on the local PostgreSQL 16 cluster (port 5433).
# Idempotent: a second run leaves the database untouched and prints the same counts.
#
# The odoo_ro password comes from the secret ODOO_PG_RO_DSN
# (postgresql://odoo_ro:<password>@localhost:5433/odoo_src), so every VM gets
# the same DSN. On the very first build, export ODOO_RO_PASSWORD instead.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="${ODOO_REPO:-$(cd "$HERE/../.." && pwd)}"
PY=/home/ubuntu/.venvs/odoo/bin/python
PGPORT=5433
DB=odoo_src
ADDONS=product,uom
MARKER=migration.fixture_source
export PGPORT PGHOST=/var/run/postgresql

if [ -z "${ODOO_RO_PASSWORD:-}" ]; then
  [ -n "${ODOO_PG_RO_DSN:-}" ] || { echo "set ODOO_PG_RO_DSN (or ODOO_RO_PASSWORD on first build)" >&2; exit 1; }
  ODOO_RO_PASSWORD="$("$PY" -c 'import sys, urllib.parse as u; print(u.unquote(u.urlsplit(sys.argv[1]).password or ""))' "$ODOO_PG_RO_DSN")"
  [ -n "$ODOO_RO_PASSWORD" ] || { echo "ODOO_PG_RO_DSN has no password" >&2; exit 1; }
fi

sudo -n pg_ctlcluster 16 main status >/dev/null 2>&1 || sudo -n pg_ctlcluster 16 main start

# A failed query aborts (set -e); only a missing database or an unset marker triggers a rebuild.
built=
if [ "$(psql -X -v ON_ERROR_STOP=1 -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB'")" = 1 ]; then
  built="$(psql -X -v ON_ERROR_STOP=1 -d "$DB" -tAc "SELECT value FROM ir_config_parameter WHERE key='$MARKER'")"
fi
if [ "$built" != "1" ]; then
  dropdb --if-exists "$DB"
  "$PY" "$REPO/odoo-bin" --addons-path="$REPO/addons,$REPO/odoo/addons" \
    -d "$DB" --db_port="$PGPORT" -i "$ADDONS" --with-demo --stop-after-init --log-level=warn
  "$PY" "$REPO/odoo-bin" shell --addons-path="$REPO/addons,$REPO/odoo/addons" \
    -d "$DB" --db_port="$PGPORT" --log-level=warn < "$HERE/exercise_source.py"
fi

psql -v ON_ERROR_STOP=1 -q -d "$DB" -v pw="$ODOO_RO_PASSWORD" <<'SQL'
SELECT format('CREATE ROLE odoo_ro LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD %L', :'pw')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'odoo_ro') \gexec
SELECT format('ALTER ROLE odoo_ro LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD %L', :'pw') \gexec
ALTER ROLE odoo_ro SET default_transaction_read_only = on;
REVOKE ALL ON DATABASE odoo_src FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT CONNECT ON DATABASE odoo_src TO odoo_ro;
GRANT USAGE ON SCHEMA public TO odoo_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO odoo_ro;
SQL

psql -d "$DB" -tA -F' ' <<'SQL'
SELECT 'product_template', count(*) FROM product_template UNION ALL
SELECT 'product_product', count(*) FROM product_product UNION ALL
SELECT 'product_category', count(*) FROM product_category UNION ALL
SELECT 'uom_uom', count(*) FROM uom_uom UNION ALL
SELECT 'mail_message', count(*) FROM mail_message;
SQL
