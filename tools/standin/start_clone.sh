#!/usr/bin/env bash
# Start the run branch's Odoo on the stand-in production clone with the switch loaded.
# Usage: tools/standin/start_clone.sh [--restore] [http_port]   (default port 8070)
#   --restore  rebuild odoo_unt16_prod from the published odoo_src snapshot first
#              (.migration/fixtures/restore_source.sh odoo_unt16_prod; needs ODOO_PG_RO_DSN)
# Runtime switch config: $STANDIN_SWITCH_CONFIG (default ~/standin-run/switch.json, created
# all-source from tools/standin/switch.json on first start).
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
repo="$(cd "$here/../.." && pwd)"
db=odoo_unt16_prod
if [[ "${1:-}" == "--restore" ]]; then "$repo/.migration/fixtures/restore_source.sh" "$db"; shift; fi
port="${1:-8070}"
export STANDIN_SWITCH_CONFIG="${STANDIN_SWITCH_CONFIG:-$HOME/standin-run/switch.json}"
py=/home/ubuntu/.venvs/odoo/bin/python
[[ -f "$STANDIN_SWITCH_CONFIG" ]] || "$py" "$here/switch.py" init
cd "$repo"
exec "$py" odoo-bin -d "$db" --db-filter "^$db\$" --db_host /var/run/postgresql --db_port 5433 \
    --addons-path "addons,odoo/addons,$here/addons" --load base,web,standin_switch \
    --http-port "$port" --gevent-port "$((port + 2))" --no-database-list --max-cron-threads 0
