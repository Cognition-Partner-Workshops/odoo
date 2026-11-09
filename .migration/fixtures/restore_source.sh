#!/usr/bin/env bash
# Restore the run's frozen source database from the published snapshot (source_snapshot.json).
# Usage: .migration/fixtures/restore_source.sh [--dump PATH] [db_name]
# Downloads the dump from the draft release by asset id with gh (or uses --dump), checks its
# sha256, replaces db_name (default odoo_src)
# on the 5433 cluster under the same name, grants the read-only role named by ODOO_PG_RO_DSN
# with the recipe's grant step, then checks the schema and content fingerprints.
set -euo pipefail

dump=""
if [[ "${1:-}" == "--dump" ]]; then dump="$2"; shift 2; fi
db="${1:-odoo_src}"
here="$(cd "$(dirname "$0")" && pwd)"
py=/home/ubuntu/.venvs/odoo/bin/python
pgbin=/usr/lib/postgresql/16/bin
export PGHOST=/var/run/postgresql PGPORT=5433
: "${ODOO_PG_RO_DSN:?ODOO_PG_RO_DSN secret is not set}"

field() { python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]])' "$here/source_snapshot.json" "$1"; }
sha="$(field sha256)"
if [[ -z "$dump" ]]; then
    dump="${XDG_CACHE_HOME:-$HOME/.cache}/odoo-snapshots/$(field asset_name)"
    mkdir -p "$(dirname "$dump")"
    if [[ ! -f "$dump" ]]; then
        # draft release (repo writers only): fetch the asset by id, not by tag
        gh api -H 'Accept: application/octet-stream' \
            "repos/$(field repo)/releases/assets/$(field asset_id)" > "$dump.part"
        mv "$dump.part" "$dump"
    fi
fi
echo "== check sha256 $dump"
echo "$sha  $dump" | sha256sum -c -

sudo pg_ctlcluster 16 main start 2>/dev/null || true
echo "== replace $db"
"$pgbin/dropdb" --if-exists "$db"
"$pgbin/createdb" "$db"
"$pgbin/pg_restore" --no-owner --no-acl --exit-on-error -d "$db" "$dump"

echo "== grant the read-only role"
"$py" "$here/grant_ro.py" "$db"

echo "== check fingerprints"
"$py" "$here/source_fingerprint.py" --dbname "$db" --expect "$(field schema_fingerprint)"
"$py" "$here/source_fingerprint.py" --dbname "$db" --content --expect "$(field content_fingerprint)"
echo "== DONE $db"
