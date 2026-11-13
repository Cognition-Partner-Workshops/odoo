#!/usr/bin/env bash
# Run the backend-neutral gate: lint, contract self-test, coverage reconciliation,
# then the whole `backend_neutral` suite on a fresh PostgreSQL 16 database.
#
#   backend_neutral_tests/run_neutral_suite.sh [db_name]
#
# Environment: ODOO_PYTHON (default /home/ubuntu/.venvs/odoo/bin/python),
# PGPORT_NEUTRAL (default 5433), KEEP_DB=1 to keep the database afterwards.
# Exit status is non-zero if any step fails. Run from anywhere; it cds to the repo root.
set -u
cd "$(dirname "$0")/.."

odooPython="${ODOO_PYTHON:-/home/ubuntu/.venvs/odoo/bin/python}"
pgPort="${PGPORT_NEUTRAL:-5433}"
dbName="${1:-bn_neutral_$(date +%s)}"
status=0

step() {
    echo
    echo "### $1"
}

step "lint: python3 backend_neutral_tests/lint_neutral.py odoo/addons/test_backend_neutral/tests"
python3 backend_neutral_tests/lint_neutral.py odoo/addons/test_backend_neutral/tests || status=1

step "contract self-test: python3 backend_neutral_tests/lint_neutral.py --self-test"
python3 backend_neutral_tests/lint_neutral.py --self-test || status=1

step "coverage reconciliation: python3 backend_neutral_tests/check_baseline.py"
python3 backend_neutral_tests/check_baseline.py || status=1

step "suite on fresh database $dbName (port $pgPort)"
dropdb -p "$pgPort" --if-exists "$dbName" && createdb -p "$pgPort" "$dbName" || { echo "cannot create $dbName"; exit 1; }
startTime=$(date +%s)
"$odooPython" odoo-bin -d "$dbName" --db_port="$pgPort" --stop-after-init \
    -i test_backend_neutral --test-enable --test-tags backend_neutral \
    2>&1 | grep -E "odoo.tests.stats|post-tests|odoo.tests.result|ERROR|FAIL|Traceback" --line-buffered
suiteStatus=${PIPESTATUS[0]}
echo "suite exit=$suiteStatus runtime=$(( $(date +%s) - startTime ))s"
[ "$suiteStatus" -eq 0 ] || status=1
[ "${KEEP_DB:-0}" = 1 ] || dropdb -p "$pgPort" --if-exists "$dbName"

echo
[ $status -eq 0 ] && echo "NEUTRAL GATE: PASS" || echo "NEUTRAL GATE: FAIL"
exit $status
