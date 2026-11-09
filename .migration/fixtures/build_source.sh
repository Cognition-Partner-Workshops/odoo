#!/usr/bin/env bash
# Build the frozen PostgreSQL 16 source database for a mongo-run (default name odoo_src).
# Usage: .migration/fixtures/build_source.sh [--rebuild] [db_name]
# Installs this checkout with storage off (no model opts into MongoDB on the run base),
# loads demo data plus deterministic scenario rows, then grants the read-only role named
# by the ODOO_PG_RO_DSN secret SELECT on every table. Run once; afterwards nothing writes
# to the database except a rebuild from this same recipe under the same name.
set -euo pipefail

rebuild=0
if [[ "${1:-}" == "--rebuild" ]]; then rebuild=1; shift; fi
db="${1:-odoo_src}"
repo="$(cd "$(dirname "$0")/../.." && pwd)"
py=/home/ubuntu/.venvs/odoo/bin/python
export PGHOST=/var/run/postgresql PGPORT=5433
apps=crm,sale_management,purchase,stock,project,hr_timesheet,hr_holidays,hr_expense,fleet,maintenance,lunch,event,survey
odoo_bin=("$py" "$repo/odoo-bin")
odoo_opts=(-d "$db" --db_port=5433 --no-http --max-cron-threads=0)

: "${ODOO_PG_RO_DSN:?ODOO_PG_RO_DSN secret is not set}"
if grep -rlq --include='*.py' "_storage = 'mongodb'" "$repo/odoo" "$repo/addons"; then
    echo "refusing: a model opts into MongoDB storage on this checkout" >&2; exit 2
fi
sudo pg_ctlcluster 16 main start 2>/dev/null || true
if psql -d postgres -Atc "select 1 from pg_database where datname = '$db'" | grep -q 1; then
    if [[ $rebuild -ne 1 ]]; then echo "refusing: $db exists (pass --rebuild)" >&2; exit 2; fi
    dropdb "$db"
fi
createdb "$db"

echo "== install $apps (demo data)"
"${odoo_bin[@]}" "${odoo_opts[@]}" -i "$apps" --with-demo --stop-after-init

echo "== seed scenario rows"
"${odoo_bin[@]}" shell "${odoo_opts[@]}" <<'SEED'
from datetime import date, datetime, time, timedelta

base_day = date(2026, 1, 5)
def ids(model, domain=()):
    return env[model].search(list(domain), order='id')

users = ids('res.users', [('share', '=', False)])
partners = ids('res.partner', [('is_company', '=', True)])
employees = ids('hr.employee')

lunch_products = ids('lunch.product')
env['lunch.order'].create([{
    'product_id': lunch_products[i % len(lunch_products)].id,
    'user_id': users[i % len(users)].id,
    'date': base_day + timedelta(days=i % 10),
    'quantity': 1 + i % 3,
} for i in range(40)])

vehicles = ids('fleet.vehicle')
service_types = ids('fleet.service.type')
env['fleet.vehicle.log.services'].create([{
    'vehicle_id': vehicles[i % len(vehicles)].id,
    'service_type_id': service_types[i % len(service_types)].id,
    'amount': 50.0 + 10 * i,
    'date_from': base_day + timedelta(days=i),
} for i in range(30)])
env['fleet.vehicle.odometer'].create([{
    'vehicle_id': vehicles[i % len(vehicles)].id,
    'value': 10000.0 + 250 * i,
    'date': base_day + timedelta(days=i),
} for i in range(30)])

equipment = ids('maintenance.equipment')
env['maintenance.request'].create([{
    'name': f'Scenario request {i:02d}',
    'equipment_id': equipment[i % len(equipment)].id,
    'maintenance_type': ('corrective', 'preventive')[i % 2],
    'schedule_date': datetime.combine(base_day + timedelta(days=i), time(9)),
} for i in range(25)])

events = ids('event.event', [('seats_limited', '=', False)])
# import_file defers the on-subscribe mail schedulers (their PDF tickets need wkhtmltopdf)
env['event.registration'].with_context(import_file=True).create([{
    'event_id': events[i % len(events)].id,
    'partner_id': partners[i % len(partners)].id,
    'name': f'Scenario attendee {i:02d}',
    'email': f'attendee{i:02d}@example.com',
} for i in range(40)])

surveys = ids('survey.survey')
env['survey.user_input'].create([{
    'survey_id': surveys[i % len(surveys)].id,
    'partner_id': partners[i % len(partners)].id,
} for i in range(20)])

env['crm.lead'].create([{
    'name': f'Scenario opportunity {i:02d}',
    'type': 'opportunity',
    'partner_id': partners[i % len(partners)].id,
    'expected_revenue': 1000.0 * (i + 1),
} for i in range(30)])

projects = ids('project.project', [('allow_timesheets', '=', True), ('account_id', '!=', False)])
tasks = env['project.task'].create([{
    'name': f'Scenario task {i:02d}',
    'project_id': projects[i % len(projects)].id,
} for i in range(30)])
env['account.analytic.line'].create([{
    'name': f'Scenario timesheet {i:02d}',
    'project_id': tasks[i % len(tasks)].project_id.id,
    'task_id': tasks[i % len(tasks)].id,
    'employee_id': employees[i % len(employees)].id,
    'unit_amount': 1.0 + i % 4,
    'date': base_day + timedelta(days=i % 20),
} for i in range(60)])

expense_products = ids('product.product', [('can_be_expensed', '=', True)])
env['hr.expense'].create([{
    'name': f'Scenario expense {i:02d}',
    'employee_id': employees[i % len(employees)].id,
    'product_id': expense_products[i % len(expense_products)].id,
    'total_amount_currency': 20.0 + 5 * i,
    'date': base_day + timedelta(days=i),
} for i in range(20)])

sale_products = ids('product.product', [('sale_ok', '=', True), ('type', '=', 'consu')])
orders = env['sale.order'].create([{
    'partner_id': partners[i % len(partners)].id,
    'order_line': [(0, 0, {'product_id': sale_products[(i + k) % len(sale_products)].id,
                           'product_uom_qty': 1 + k}) for k in range(3)],
} for i in range(20)])
orders.filtered(lambda o: o.id % 2 == 0).action_confirm()

purchase_products = ids('product.product', [('purchase_ok', '=', True), ('type', '=', 'consu')])
porders = env['purchase.order'].create([{
    'partner_id': partners[i % len(partners)].id,
    'order_line': [(0, 0, {'product_id': purchase_products[(i + k) % len(purchase_products)].id,
                           'product_qty': 2 + k}) for k in range(2)],
} for i in range(15)])
porders.filtered(lambda o: o.id % 2 == 0).button_confirm()

env.cr.commit()
print('SEED OK')
SEED

echo "== grant the read-only role"
"$py" - "$db" <<'GRANT'
import os, sys
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import parse_dsn

db = sys.argv[1]
ro = parse_dsn(os.environ['ODOO_PG_RO_DSN'])
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
GRANT

echo "== DONE $db"
