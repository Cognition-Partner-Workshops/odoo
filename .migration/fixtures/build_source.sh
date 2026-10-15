#!/usr/bin/env bash
# Build the read-only Odoo source database odoo_src (product, uom, sale, purchase,
# stock, account with demo data; code migration scope stays product + uom)
# and the SELECT-only role odoo_ro on the local PostgreSQL 16 cluster (port 5433).
# Idempotent: a second run leaves the database untouched and prints the same counts.
#
# The odoo_ro password comes from the secret ODOO_PG_RO_DSN, the plugin's JSON
# PostgreSQL secret {"user","password","host","port","database"}, so every VM
# gets the same DSN. On the very first build, export ODOO_RO_PASSWORD instead.
#
# Deterministic (d-source-repro = deterministic-fixture): the build runs the Odoo code of
# SOURCE_COMMIT, the run-branch tip before any model opted into MongoDB storage, so every
# table is written by the PostgreSQL storage; every create_date / write_date stamped during
# the build is then pinned to FIXED_INSTANT and the only random defaults in migrate-bucket
# tables (the attribute value colours) are replaced. Two VMs building this fixture get the
# same rows on every column the recon harness compares; prove it with a second build and a
# data-only pg_dump diff (see source.md).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY=/home/ubuntu/.venvs/odoo/bin/python
PGPORT=5433
DB=odoo_src
ADDONS=product,uom,sale,purchase,stock,account
MARKER=migration.fixture_source
MARKER_VERSION=3   # bump when the fixture changes so an old odoo_src is rebuilt (3: pinned timestamps)
SOURCE_COMMIT=03a3cb561ac42578e920b1f549e9d400177add06   # mongo-run/20261014 before PR #21 (first opt-in)
FIXED_INSTANT='2026-10-14 00:00:00'   # UTC; the run date
export PGPORT PGHOST=/var/run/postgresql

# ODOO_REPO: an Odoo checkout at SOURCE_COMMIT. Default: a git worktree of this repo at
# that commit, created on first use next to the repo (the run-branch tip itself cannot build
# the source: its opted-in models would write through MongoDB).
REPO="${ODOO_REPO:-$(dirname "$(cd "$HERE/../.." && pwd)")/odoo-base}"
if [ ! -e "$REPO/odoo-bin" ]; then
  git -C "$HERE/../.." worktree add "$REPO" "$SOURCE_COMMIT"
fi
head="$(git -C "$REPO" rev-parse HEAD)"
[ "$head" = "$SOURCE_COMMIT" ] || { echo "$REPO is at $head, not SOURCE_COMMIT $SOURCE_COMMIT" >&2; exit 1; }

if [ -z "${ODOO_RO_PASSWORD:-}" ]; then
  [ -n "${ODOO_PG_RO_DSN:-}" ] || { echo "set ODOO_PG_RO_DSN (or ODOO_RO_PASSWORD on first build)" >&2; exit 1; }
  ODOO_RO_PASSWORD="$("$PY" -c 'import sys, json; print(json.loads(sys.argv[1]).get("password", ""))' "$ODOO_PG_RO_DSN")"
  [ -n "$ODOO_RO_PASSWORD" ] || { echo "ODOO_PG_RO_DSN has no password" >&2; exit 1; }
fi

sudo -n pg_ctlcluster 16 main status >/dev/null 2>&1 || sudo -n pg_ctlcluster 16 main start

# A failed query aborts (set -e); only a missing database or an old/unset marker triggers a rebuild.
built=
exists="$(psql -X -v ON_ERROR_STOP=1 -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB'")"
if [ "$exists" = 1 ]; then
  built="$(psql -X -v ON_ERROR_STOP=1 -d "$DB" -tAc "SELECT value FROM ir_config_parameter WHERE key='$MARKER'")"
fi
if [ "$built" != "$MARKER_VERSION" ]; then
  dropdb --if-exists "$DB"
  "$PY" "$REPO/odoo-bin" --addons-path="$REPO/addons,$REPO/odoo/addons" \
    -d "$DB" --db_port="$PGPORT" -i "$ADDONS" --with-demo --stop-after-init --log-level=warn
  "$PY" "$REPO/odoo-bin" shell --addons-path="$REPO/addons,$REPO/odoo/addons" \
    -d "$DB" --db_port="$PGPORT" --log-level=warn < "$HERE/exercise_source.py"
  # Pin every build-time stamp and the randint colour defaults of product.attribute.value (a
  # function of the id) and product.template.attribute.value (its value's colour), then set the
  # marker in the same transaction: an odoo_src that carries MARKER_VERSION is always pinned.
  psql -X -1 -v ON_ERROR_STOP=1 -q -d "$DB" -v fixed="$FIXED_INSTANT" -v marker="$MARKER" -v version="$MARKER_VERSION" <<'SQL'
SET LOCAL fixture.instant = :'fixed';
DO $$
DECLARE r record;
BEGIN
  FOR r IN
    SELECT c.table_name, c.column_name
    FROM information_schema.columns c
    JOIN information_schema.tables t USING (table_schema, table_name)
    WHERE c.table_schema = 'public' AND t.table_type = 'BASE TABLE'
      AND c.column_name IN ('create_date', 'write_date')
      AND c.data_type LIKE 'timestamp%'
  LOOP
    EXECUTE format('UPDATE %I SET %I = %L WHERE %I IS NOT NULL',
                   r.table_name, r.column_name, current_setting('fixture.instant'), r.column_name);
  END LOOP;
END $$;
UPDATE product_attribute_value SET color = (id - 1) % 11 + 1;
UPDATE product_template_attribute_value ptav SET color = pav.color
  FROM product_attribute_value pav WHERE pav.id = ptav.product_attribute_value_id;
INSERT INTO ir_config_parameter (key, value, create_uid, create_date, write_uid, write_date)
VALUES (:'marker', :'version', 1, :'fixed', 1, :'fixed')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, write_date = EXCLUDED.write_date;
SQL
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
SELECT 'sale_order', count(*) FROM sale_order UNION ALL
SELECT 'sale_order_line', count(*) FROM sale_order_line UNION ALL
SELECT 'purchase_order', count(*) FROM purchase_order UNION ALL
SELECT 'purchase_order_line', count(*) FROM purchase_order_line UNION ALL
SELECT 'stock_picking', count(*) FROM stock_picking UNION ALL
SELECT 'stock_move', count(*) FROM stock_move UNION ALL
SELECT 'stock_move_line', count(*) FROM stock_move_line UNION ALL
SELECT 'stock_quant', count(*) FROM stock_quant UNION ALL
SELECT 'account_move', count(*) FROM account_move UNION ALL
SELECT 'account_move_line', count(*) FROM account_move_line UNION ALL
SELECT 'mail_message', count(*) FROM mail_message;
SQL
