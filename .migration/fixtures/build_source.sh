#!/usr/bin/env bash
# Rebuild the read-only legacy source for run unt12: PostgreSQL database odoo_src on the
# local PG16 cluster (port 5433), installed by the run branch's pre-migration Odoo code
# (SOURCE_COMMIT, the 20.0 commit mongo-run/unt12 was cut from) with
#   -i product,uom,sale,purchase,stock,account --with-demo
# plus the SELECT-only role odoo_ro.
#
# Rerunnable: an odoo_src that already carries ir_config_parameter
# migration.fixture_source = MARKER_VERSION is kept and only the role, its privileges and
# the counts are refreshed; anything else is dropped and rebuilt. A rebuild is
# deterministic (gate g-source-deterministic): Odoo installs under libfaketime with its clock
# started at FIXED_INSTANT and PYTHONHASHSEED=0, so every date and every now()-derived
# timestamp lands at FIXED_INSTANT plus a whole number of hours plus the install's run time
# (about a minute). The post-install transaction then rounds those timestamps to the hour,
# pins create_date/write_date and the PostgreSQL-side orm_signaling stamps to FIXED_INSTANT,
# replaces the random defaults (colours, access tokens, channel uuids, database.uuid/secret)
# with id-derived values, and writes the marker. A frozen clock is not an option: Odoo's
# registry load spins forever when time stands still.
#
# The odoo_ro password is read from ODOO_PG_RO_DSN, the plugin's JSON PostgreSQL secret
# ({"user","password","host","port","database"}); bind secret:personal:ODOO_PG_RO_DSN in a
# one-shot exec. The value is never printed.
set -euo pipefail

PY=/home/ubuntu/.venvs/odoo/bin/python
DB=odoo_src
ROLE=odoo_ro
ADDONS=product,uom,sale,purchase,stock,account
MARKER=migration.fixture_source
MARKER_VERSION=2
SOURCE_COMMIT=63446015e3c154f552633f54951843dcbb51e9a9
FIXED_INSTANT='2026-10-20 00:00:00'
FAKETIME_LIB=/usr/lib/x86_64-linux-gnu/faketime/libfaketime.so.1
FRAMEWORK_TABLES='^(ir|res|mail|bus|web|base)_'
export PGPORT=5433 PGHOST=/var/run/postgresql

REPO_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
SRC_TREE="${ODOO_SOURCE_TREE:-$(dirname "$REPO_ROOT")/odoo-unt12-src}"

die() { echo "build_source: $*" >&2; exit 1; }
sql() { psql -X -q -v ON_ERROR_STOP=1 "$@"; }

[ -n "${ODOO_PG_RO_DSN:-}" ] || die "ODOO_PG_RO_DSN is not set"
RO_PASSWORD="$("$PY" -c 'import json, os; print(json.loads(os.environ["ODOO_PG_RO_DSN"])["password"])')"
[ -n "$RO_PASSWORD" ] || die "ODOO_PG_RO_DSN carries no password"

sudo -n pg_ctlcluster 16 main status >/dev/null 2>&1 || sudo -n pg_ctlcluster 16 main start

# Build from a checkout pinned at SOURCE_COMMIT, never from the run-branch tip: once models
# opt into MongoDB storage the tip no longer writes every table through PostgreSQL.
if [ ! -e "$SRC_TREE/odoo-bin" ]; then
  git -C "$REPO_ROOT" worktree add --detach "$SRC_TREE" "$SOURCE_COMMIT"
fi
[ "$(git -C "$SRC_TREE" rev-parse HEAD)" = "$SOURCE_COMMIT" ] || die "$SRC_TREE is not at $SOURCE_COMMIT"
[ -z "$(git -C "$SRC_TREE" status --porcelain)" ] || die "$SRC_TREE has local changes"
[ -e "$FAKETIME_LIB" ] || die "$FAKETIME_LIB is missing (apt install faketime)"
ODOO_BIN=(env "FAKETIME=@$FIXED_INSTANT" "LD_PRELOAD=$FAKETIME_LIB" PYTHONHASHSEED=0
          "$PY" "$SRC_TREE/odoo-bin" --addons-path="$SRC_TREE/addons,$SRC_TREE/odoo/addons" -d "$DB" --db_port="$PGPORT" --log-level=warn)

current=
if [ "$(sql -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '$DB'")" = 1 ] &&
   [ "$(sql -d "$DB" -tAc "SELECT to_regclass('public.ir_config_parameter') IS NOT NULL")" = t ]; then
  current="$(sql -d "$DB" -tAc "SELECT value FROM ir_config_parameter WHERE key = '$MARKER'")"
fi

if [ "$current" = "$MARKER_VERSION" ]; then
  echo "build_source: $DB already carries $MARKER=$MARKER_VERSION; keeping it"
else
  echo "build_source: building $DB from $SOURCE_COMMIT (-i $ADDONS --with-demo)"
  dropdb --if-exists "$DB"
  "${ODOO_BIN[@]}" -i "$ADDONS" --with-demo --stop-after-init
  # One transaction: pin every build-time stamp, round the now()-derived timestamps, replace
  # the random defaults, write the marker. A database carrying the marker is therefore
  # always a pinned one. Framework tables (ir_*, res_*, mail_*, bus_*, web_*, base_*) only
  # get the create_date/write_date pin; their remaining runtime values are out of scope.
  sql -1 -d "$DB" -v instant="$FIXED_INSTANT" -v marker="$MARKER" -v version="$MARKER_VERSION" -v framework="$FRAMEWORK_TABLES" <<'SQL'
SET LOCAL fixture.instant = :'instant';
SET LOCAL fixture.framework = :'framework';
DO $$
DECLARE t record; residual interval;
BEGIN
  FOR t IN
    SELECT c.table_name, c.column_name,
           c.column_name IN ('create_date', 'write_date') OR c.table_name LIKE 'orm_signaling_%' AS pin
    FROM information_schema.columns c
    JOIN information_schema.tables s USING (table_schema, table_name)
    WHERE c.table_schema = 'public' AND s.table_type = 'BASE TABLE' AND c.data_type LIKE 'timestamp%'
      AND (c.column_name IN ('create_date', 'write_date') OR c.table_name !~ current_setting('fixture.framework'))
  LOOP
    IF t.pin THEN
      EXECUTE format('UPDATE %I SET %I = %L WHERE %I IS NOT NULL',
                     t.table_name, t.column_name, current_setting('fixture.instant'), t.column_name);
    ELSE
      -- now()-derived values sit at a whole-hour offset from FIXED_INSTANT plus the install's
      -- run time; anything further from the hour means the clock assumption broke.
      EXECUTE format($q$SELECT coalesce(max(greatest(%1$I - date_trunc('hour', %1$I + interval '30 min'),
                                                     date_trunc('hour', %1$I + interval '30 min') - %1$I)), '0')
                     FROM %2$I$q$, t.column_name, t.table_name) INTO residual;
      IF residual > interval '15 min' THEN
        RAISE EXCEPTION '%.% is % off the hour; install clock drifted', t.table_name, t.column_name, residual;
      END IF;
      EXECUTE format($q$UPDATE %2$I SET %1$I = date_trunc('hour', %1$I + interval '30 min')
                     WHERE %1$I IS NOT NULL AND %1$I <> date_trunc('hour', %1$I + interval '30 min')$q$,
                     t.column_name, t.table_name);
    END IF;
  END LOOP;
END $$;
UPDATE product_attribute_value SET color = (id - 1) % 11 + 1;
UPDATE product_template_attribute_value v SET color = a.color
  FROM product_attribute_value a WHERE a.id = v.product_attribute_value_id;
UPDATE crm_team SET color = (id - 1) % 11 + 1;
UPDATE account_analytic_plan SET color = (id - 1) % 11 + 1;
UPDATE sale_order SET access_token = md5('sale_order.access_token:' || id)::uuid::text WHERE access_token IS NOT NULL;
UPDATE purchase_order SET access_token = md5('purchase_order.access_token:' || id)::uuid::text WHERE access_token IS NOT NULL;
UPDATE discuss_channel SET uuid = left(md5('discuss_channel.uuid:' || id), 10);
UPDATE ir_config_parameter SET value = md5('odoo_src ' || key)::uuid::text WHERE key IN ('database.uuid', 'database.secret');
UPDATE ir_config_parameter SET value = :'instant' WHERE key = 'database.create_date';
INSERT INTO ir_config_parameter (key, value, create_uid, create_date, write_uid, write_date)
VALUES (:'marker', :'version', 1, :'instant', 1, :'instant');
SQL
fi

# The role refresh runs on every invocation, so a rotated password or a lost privilege
# heals on rerun. Nothing is written to the data after this point.
RO_PASSWORD="$RO_PASSWORD" sql -d "$DB" -v role="$ROLE" <<'SQL'
\getenv pw RO_PASSWORD
SELECT format('CREATE ROLE %I LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION PASSWORD %L', :'role', :'pw')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'role') \gexec
SELECT format('ALTER ROLE %I LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION PASSWORD %L', :'role', :'pw') \gexec
SELECT format('ALTER ROLE %I SET default_transaction_read_only = on', :'role') \gexec
REVOKE ALL ON DATABASE odoo_src FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT CONNECT ON DATABASE odoo_src TO odoo_ro;
GRANT USAGE ON SCHEMA public TO odoo_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO odoo_ro;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO odoo_ro;
SQL

echo "build_source: $DB $MARKER=$(sql -d "$DB" -tAc "SELECT value FROM ir_config_parameter WHERE key = '$MARKER'") installed_modules=$(sql -d "$DB" -tAc "SELECT count(*) FROM ir_module_module WHERE state = 'installed'")"
sql -d "$DB" -tA -F' ' <<'SQL'
SELECT 'product_template', count(*) FROM product_template UNION ALL
SELECT 'product_product', count(*) FROM product_product UNION ALL
SELECT 'uom_uom', count(*) FROM uom_uom UNION ALL
SELECT 'sale_order', count(*) FROM sale_order UNION ALL
SELECT 'purchase_order', count(*) FROM purchase_order UNION ALL
SELECT 'stock_move', count(*) FROM stock_move UNION ALL
SELECT 'account_move', count(*) FROM account_move UNION ALL
SELECT 'account_move_line', count(*) FROM account_move_line;
SQL
