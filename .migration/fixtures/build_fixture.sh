#!/usr/bin/env bash
# Build the recon fixture odoo_fixture: a `createdb -T odoo_src` clone of the read-only
# source plus its filestore, then build_fixture.py adds one synthetic outlier parent
# (a product template whose vendor pricelist lines are twice the profile max), checks every
# in-scope fan-out against data_profile.json and writes odoo_fixture.json.
# odoo_src is only read (fingerprint check through the read-only role before and after)
# and used as the clone template; nothing writes to it. Bind the JSON ODOO_PG_RO_DSN in a
# one-shot exec; the value is never printed.
set -euo pipefail

PY=/home/ubuntu/.venvs/odoo/bin/python
SRC=odoo_src
DB=odoo_fixture
FILESTORE=/home/ubuntu/.local/share/Odoo/filestore
RO_ROLE=odoo_ro
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
MANIFEST="$ROOT/.migration/fixtures/odoo_fixture.json"
START=$(date +%s)

export PGPORT=5433 PGHOST=/var/run/postgresql

die() { echo "build_fixture: $*" >&2; exit 1; }
[ -n "${ODOO_PG_RO_DSN:-}" ] || die "ODOO_PG_RO_DSN is not set"
[ -d "$FILESTORE/$SRC" ] || die "missing filestore $FILESTORE/$SRC"

SOURCE_SHA=$(ROOT="$ROOT" "$PY" "$ROOT/.migration/fixtures/source_fingerprint.py") \
  || die "$SRC does not match .migration/source_fingerprint.json; rebuild it with build_source.sh"
echo "build_fixture: $SRC fingerprint before build $SOURCE_SHA (matches)"

rm -f "$MANIFEST" "$MANIFEST.tmp"
dropdb --if-exists "$DB"
createdb -T "$SRC" "$DB"
rm -rf "${FILESTORE:?}/$DB"
cp -a "$FILESTORE/$SRC" "$FILESTORE/$DB"

ROOT="$ROOT" FIXTURE_DB="$DB" SOURCE_DB="$SRC" RO_ROLE="$RO_ROLE" MANIFEST="$MANIFEST" \
  SOURCE_SHA="$SOURCE_SHA" "$PY" "$ROOT/.migration/fixtures/build_fixture.py"

AFTER_SHA=$(ROOT="$ROOT" "$PY" "$ROOT/.migration/fixtures/source_fingerprint.py") \
  || { rm -f "$MANIFEST"; die "$SRC fingerprint changed during the build"; }
echo "build_fixture: $SRC fingerprint after build $AFTER_SHA (unchanged)"
echo "build_fixture: wall_seconds=$(( $(date +%s) - START ))"
