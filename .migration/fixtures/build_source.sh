#!/usr/bin/env bash
# Build the read-only source for run unt13: PostgreSQL database odoo_src on the local PG16
# cluster (port 5433) plus the SELECT-only role odoo_ro, from a clean checkout at SOURCE_COMMIT.
#   1. -i product,uom,sale,purchase,stock,account --with-demo
#   2. Odoo's populate module (faker==22.0.0 in the Odoo venv): the product, sale, stock and
#      account demo blueprints at POPULATE_SCALE with POPULATE_SEED and one worker; populate is
#      uninstalled afterwards so the installed module set matches the run's
#   3. simulate_business.py through odoo-bin shell: months of business workflows on the ORM
#   4. empty-table gate against expected_empty.txt, then one normalisation transaction and the
#      marker migration.fixture_source = MARKER_VERSION
# Every Odoo process runs under libfaketime with its clock restarted at FIXED_INSTANT and
# PYTHONHASHSEED=0 (a frozen clock is not an option: the registry load spins forever), so
# now()-derived values drift only by that process's runtime; each process must finish within
# 25 minutes and the normalisation rounds every timestamp to the hour, pins create_date and
# write_date, and replaces random values with id-derived ones. A rebuild is byte-identical.
# An odoo_src that already carries the marker is kept; anything else is dropped and rebuilt.
# The odoo_ro password comes from the plugin's JSON PostgreSQL secret (checked below); bind it
# in a one-shot exec. The value is never printed.
set -euo pipefail

PY=/home/ubuntu/.venvs/odoo/bin/python
FAKER_PIN='faker==22.0.0'
DB=odoo_src
ROLE=odoo_ro
ADDONS=product,uom,sale,purchase,stock,account
MARKER=migration.fixture_source
MARKER_VERSION=4
SOURCE_COMMIT=63446015e3c154f552633f54951843dcbb51e9a9
FIXED_INSTANT='2026-10-20 00:00:00'
FAKETIME_LIB=/usr/lib/x86_64-linux-gnu/faketime/libfaketime.so.1
FRAMEWORK_TABLES='^(ir|res|mail|bus|web|base)_'
POPULATE_SEED=13013
POPULATE_SCALE=0.05
export PGPORT=5433 PGHOST=/var/run/postgresql

REPO_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
SRC_TREE="${ODOO_SOURCE_TREE:-$(dirname "$REPO_ROOT")/odoo-unt13-src}"
ADDONS_PATH="$SRC_TREE/addons,$SRC_TREE/odoo/addons"
EXPECTED_EMPTY="$REPO_ROOT/.migration/fixtures/expected_empty.txt"
TOTAL_START=$(date +%s)

die() { echo "build_source: $*" >&2; exit 1; }
sql() { psql -X -q -v ON_ERROR_STOP=1 "$@"; }

[ -n "${ODOO_PG_RO_DSN:-}" ] || die "ODOO_PG_RO_DSN is not set"
RO_PASSWORD="$("$PY" -c 'import json, os; print(json.loads(os.environ["ODOO_PG_RO_DSN"])["password"])')"
[ -n "$RO_PASSWORD" ] || die "ODOO_PG_RO_DSN carries no password"
FAKER_VERSION="$("$PY" -c 'import faker; print(faker.VERSION)')" || die "$FAKER_PIN is not installed"
[ "$FAKER_VERSION" = 22.0.0 ] || die "expected $FAKER_PIN, found faker==$FAKER_VERSION"
[ -e "$FAKETIME_LIB" ] || die "$FAKETIME_LIB is missing (apt install faketime)"

sudo -n pg_ctlcluster 16 main status >/dev/null 2>&1 || sudo -n pg_ctlcluster 16 main start

if [ ! -e "$SRC_TREE/odoo-bin" ]; then
  git -C "$REPO_ROOT" worktree add --detach "$SRC_TREE" "$SOURCE_COMMIT"
fi
[ "$(git -C "$SRC_TREE" rev-parse HEAD)" = "$SOURCE_COMMIT" ] || die "$SRC_TREE is not at $SOURCE_COMMIT"
[ -z "$(git -C "$SRC_TREE" status --porcelain)" ] || die "$SRC_TREE has local changes"

runOdoo() {
  local stage="$1"
  shift
  local started=$SECONDS elapsed
  echo "stage_start=$stage"
  if ! env "FAKETIME=@$FIXED_INSTANT" "LD_PRELOAD=$FAKETIME_LIB" \
    PYTHONHASHSEED=0 "POPULATE_SEED=$POPULATE_SEED" "POPULATE_SCALE=$POPULATE_SCALE" \
    "$PY" "$SRC_TREE/odoo-bin" "$@"; then
    die "Odoo invocation failed: $stage"
  fi
  elapsed=$((SECONDS - started))
  echo "stage_seconds=$stage $elapsed"
  [ "$elapsed" -lt 1500 ] || die "Odoo invocation exceeded 25 minutes: $stage (${elapsed}s)"
}

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
  runOdoo base-install --addons-path="$ADDONS_PATH" -d "$DB" --db_port="$PGPORT" \
    --log-level=warn --no-http -i "$ADDONS" --with-demo --stop-after-init

  runOdoo enable-pricelists shell --addons-path="$ADDONS_PATH" -d "$DB" --db_port="$PGPORT" \
    --log-level=warn --no-http <<'PY'
settings = env['res.config.settings'].create({'group_product_pricelist': True})
settings.execute()
assert env.user.has_group('product.group_product_pricelist')
env.cr.commit()
PY

  runOdoo install-populate --addons-path="$ADDONS_PATH" -d "$DB" --db_port="$PGPORT" \
    --log-level=warn --no-http -i populate --stop-after-init
  runOdoo update-populate --addons-path="$ADDONS_PATH" -d "$DB" --db_port="$PGPORT" \
    --log-level=warn --no-http -u populate --stop-after-init

  runOdoo verify-blueprints shell --addons-path="$ADDONS_PATH" -d "$DB" --db_port="$PGPORT" \
    --log-level=warn --no-http <<'PY'
blueprints = (
    'product.fake_product_demo',
    'sale.fake_sale_demo',
    'stock.stock_populate_demo',
    'account.account_populate_demo',
)
for xmlid in blueprints:
    assert env.ref(xmlid), f'missing populate blueprint {xmlid}'
print('verified populate blueprints:', ', '.join(blueprints))
PY

  for blueprint in product.fake_product_demo sale.fake_sale_demo stock.stock_populate_demo account.account_populate_demo; do
    runOdoo "populate-$blueprint" populate -d "$DB" --db_port="$PGPORT" \
      --addons-path="$ADDONS_PATH" --log-level=warn --no-http \
      -b "$blueprint" --seed "$POPULATE_SEED" --scale "$POPULATE_SCALE" -j 1
  done

  runOdoo uninstall-populate shell --addons-path="$ADDONS_PATH" -d "$DB" --db_port="$PGPORT" \
    --log-level=warn --no-http <<'PY'
module = env['ir.module.module'].search([('name', '=', 'populate')], limit=1)
if module and module.state == 'installed':
    module.button_immediate_uninstall()
assert not env['ir.module.module'].search([('name', '=', 'populate'), ('state', '=', 'installed')])
env.cr.commit()
print('populate uninstalled')
PY

  runOdoo simulate-business shell --addons-path="$ADDONS_PATH" -d "$DB" --db_port="$PGPORT" \
    --log-level=warn --no-http < "$REPO_ROOT/.migration/fixtures/simulate_business.py"

  echo "empty-table-gate: non-framework empty tables (transient-model tables are excluded from failure)"
  counts="$(sql -d "$DB" -At -F $'\t' <<'SQL'
SELECT format('SELECT %L, count(*) FROM %I', table_name, table_name)
FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
ORDER BY table_name
\gexec
SQL
)"
transient_tables="$(sql -d "$DB" -At -F $'\t' <<'SQL'
SELECT 'model', replace(model, '.', '_')
FROM ir_model
WHERE transient
UNION
SELECT 'many2many', relation_table
FROM ir_model_fields f
JOIN ir_model m ON m.model = f.model
WHERE m.transient AND f.ttype = 'many2many' AND relation_table IS NOT NULL
ORDER BY 1, 2
SQL
)"
declare -A table_counts transient_models transient_relations expected
while IFS=$'\t' read -r table count; do
  [ -n "$table" ] || continue
  table_counts["$table"]="$count"
done <<< "$counts"
while IFS=$'\t' read -r kind table; do
  [ -n "$table" ] || continue
  if [ "$kind" = model ]; then
    transient_models["$table"]=1
  else
    transient_relations["$table"]=1
  fi
done <<< "$transient_tables"
while read -r table reason; do
  [[ -z "${table:-}" || "$table" == \#* ]] && continue
  [ -n "${reason:-}" ] || die "expected_empty.txt entry has no reason: $table"
  expected["$table"]="$reason"
done < "$EXPECTED_EMPTY"

empty_nonframework=()
empty_transient_models=()
empty_transient_relations=()
all_table_names=()
transient_model_total=0
transient_relation_total=0
while IFS=$'\t' read -r table _count; do
  [ -n "$table" ] && all_table_names+=("$table")
done <<< "$counts"
for table in "${all_table_names[@]}"; do
  [ -n "${table_counts[$table]:-}" ] || continue
  [[ "$table" =~ $FRAMEWORK_TABLES ]] && continue
  if [ -n "${transient_models[$table]:-}" ]; then
    transient_model_total=$((transient_model_total + 1))
    if [ "${table_counts[$table]}" = 0 ]; then
      empty_transient_models+=("$table")
    fi
  fi
  if [ -n "${transient_relations[$table]:-}" ]; then
    transient_relation_total=$((transient_relation_total + 1))
    if [ "${table_counts[$table]}" = 0 ]; then
      empty_transient_relations+=("$table")
    fi
  fi
  if [ "${table_counts[$table]}" = 0 ] &&
     [ -z "${transient_models[$table]:-}" ] &&
     [ -z "${transient_relations[$table]:-}" ]; then
    empty_nonframework+=("$table")
  fi
done
printf 'transient-model tables excluded: %s total; %s empty\n' \
  "$transient_model_total" "${#empty_transient_models[@]}"
printf 'transient-model many2many relation tables excluded: %s total; %s empty\n' \
  "$transient_relation_total" "${#empty_transient_relations[@]}"
printf 'table\tclassification\treason\n'
for table in "${empty_nonframework[@]}"; do
  printf '%s\texpected\t%s\n' "$table" "${expected[$table]:-UNLISTED}"
done
for table in "${empty_transient_models[@]}"; do
  printf '%s\ttransient-model-excluded\t-\n' "$table"
done
for table in "${empty_transient_relations[@]}"; do
  printf '%s\ttransient-many2many-excluded\t-\n' "$table"
done

gate_failed=0
for table in "${empty_nonframework[@]}"; do
  [ -n "${expected[$table]:-}" ] || gate_failed=1
done
for table in "${!expected[@]}"; do
  [ -n "${table_counts[$table]:-}" ] && [ "${table_counts[$table]}" = 0 ] || {
    echo "empty-table-gate: stale expected_empty entry: $table" >&2
    gate_failed=1
  }
done
[ "$gate_failed" -eq 0 ] || die "empty-table gate failed; update only genuinely non-seedable entries after seeding what is feasible"

  echo "normalization: pin create/write timestamps; round all other timestamp columns to nearest hour"
  local_start=$SECONDS
  sql -1 -d "$DB" -v instant="$FIXED_INSTANT" -v marker="$MARKER" \
    -v version="$MARKER_VERSION" <<'SQL'
SET LOCAL TIME ZONE 'UTC';
SET LOCAL app.fixed_instant = :'instant';
DO $$
DECLARE t record; fixed_instant timestamp := current_setting('app.fixed_instant')::timestamp;
BEGIN
  FOR t IN
    SELECT c.table_name, c.column_name,
           c.column_name IN ('create_date', 'write_date') OR c.table_name LIKE 'orm_signaling_%' AS pin
    FROM information_schema.columns c
    JOIN information_schema.tables s USING (table_schema, table_name)
    WHERE c.table_schema = 'public' AND s.table_type = 'BASE TABLE'
      AND c.data_type IN ('timestamp without time zone', 'timestamp with time zone')
  LOOP
    IF t.pin THEN
      EXECUTE format('UPDATE %I SET %I = $1 WHERE %I IS NOT NULL',
                     t.table_name, t.column_name, t.column_name) USING fixed_instant;
    ELSE
      EXECUTE format('UPDATE %I SET %I = date_trunc(''hour'', %I + interval ''30 minutes'') WHERE %I IS NOT NULL',
                     t.table_name, t.column_name, t.column_name, t.column_name);
    END IF;
  END LOOP;
END $$;
UPDATE product_attribute_value SET color = (id - 1) % 11 + 1;
UPDATE product_template_attribute_value v SET color = a.color
  FROM product_attribute_value a WHERE a.id = v.product_attribute_value_id;
UPDATE crm_team SET color = (id - 1) % 11 + 1;
UPDATE account_analytic_plan SET color = (id - 1) % 11 + 1;
UPDATE sale_order SET access_token = NULL;
UPDATE purchase_order SET access_token = NULL;
UPDATE discuss_channel SET uuid = left(md5('discuss_channel.uuid:' || id), 10);
UPDATE account_move SET access_token = NULL;
UPDATE resource_resource SET color = (id - 1) % 11 + 1;
UPDATE utm_tag SET color = (id - 1) % 11 + 1;
UPDATE mail_guest SET access_token = md5('mail_guest.access_token:' || id);
UPDATE mail_mail mm SET "references" = r.refs
  FROM (SELECT m.id,
               string_agg('<' || coalesce(
                   md5('mail_message.message_id:' || (SELECT min(g.id) FROM mail_message g WHERE g.message_id = t.ref)),
                   md5('mail_mail.references:' || m.id || ':' || t.ord)) || '@odoo_src>', ' ' ORDER BY t.ord) AS refs
          FROM mail_mail m
          CROSS JOIN LATERAL regexp_split_to_table(trim(m."references"), '\s+') WITH ORDINALITY AS t(ref, ord)
         WHERE trim(coalesce(m."references", '')) <> ''
         GROUP BY m.id) r
 WHERE r.id = mm.id;
UPDATE mail_message SET message_id = '<' || md5('mail_message.message_id:' || id) || '@odoo_src>'
 WHERE message_id IS NOT NULL;
DELETE FROM bus_bus;
UPDATE ir_config_parameter SET value = md5('odoo_src ' || key)::uuid::text
  WHERE key IN ('database.uuid', 'database.secret');
UPDATE ir_config_parameter SET value = :'instant' WHERE key = 'database.create_date';
UPDATE res_users SET password = NULL;
INSERT INTO ir_config_parameter (key, value, create_uid, create_date, write_uid, write_date)
VALUES (:'marker', :'version', 1, :'instant', 1, :'instant');
SQL
  echo "stage_seconds=normalize-and-marker $((SECONDS - local_start))"
fi

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
echo "build_source: total_wall_seconds=$(($(date +%s) - TOTAL_START)) populate_seed=$POPULATE_SEED populate_scale=$POPULATE_SCALE"
