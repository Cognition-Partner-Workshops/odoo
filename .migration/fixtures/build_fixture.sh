#!/usr/bin/env bash
# Build the recon fixture `odoo_fixture`: a `createdb -T odoo_src` clone of the
# read-only source plus its filestore, then build_fixture.py adds one synthetic
# outlier parent (a product template with OUTLIER_CHILDREN vendor pricelist lines), checks every
# in-scope fan-out against the profile and writes odoo_fixture.json. odoo_src is
# only ever used as a template; nothing connects to it.
set -euo pipefail

PY=/home/ubuntu/.venvs/odoo/bin/python
SRC=odoo_src
DB=odoo_fixture
FILESTORE=/home/ubuntu/.local/share/Odoo/filestore
OUTLIER_CHILDREN=60
ROOT=$(cd "$(dirname "$0")/../.." && pwd)

export PGPORT=5433

[ -d "$FILESTORE/$SRC" ] || { echo "build_fixture: missing filestore $FILESTORE/$SRC" >&2; exit 1; }

dropdb --if-exists "$DB"
createdb -T "$SRC" "$DB"
rm -rf "$FILESTORE/$DB"
cp -a "$FILESTORE/$SRC" "$FILESTORE/$DB"

ROOT="$ROOT" FIXTURE_DB="$DB" SOURCE_DB="$SRC" OUTLIER_CHILDREN="$OUTLIER_CHILDREN" \
  MANIFEST="$ROOT/.migration/fixtures/odoo_fixture.json" \
  "$PY" "$ROOT/.migration/fixtures/build_fixture.py"
