#!/usr/bin/env bash
# Build the recon fixture database odoo_fixture (s2.4-fixture): a clone of the read-only
# source odoo_src plus one synthetic outlier template (60 variants against a source max of
# 5), then write .migration/fixtures/odoo_fixture.json from the live fixture.
# Idempotent: when the fixture marker is current and the fixture still carries the live
# source's database.uuid (a rebuilt odoo_src gets a new one) nothing is rebuilt and only
# the manifest is rewritten. odoo_src is never written; the fixture is a separate database.
# The Odoo filestore is copied alongside the database, as Odoo's own duplicate does.
#
# Needs the secret ODOO_PG_RO_DSN (plugin JSON shape). The fixture DSN is the same JSON
# with "database" swapped to odoo_fixture, exported as ODOO_PG_FIXTURE_DSN for the
# manifest writer and for `recon run --mode fixture --source-dsn-secret ODOO_PG_FIXTURE_DSN`.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="${ODOO_REPO:-$(cd "$HERE/../.." && pwd)}"
PY=/home/ubuntu/.venvs/odoo/bin/python
RECON_PY=/home/ubuntu/.venvs/recon/bin/python
PGPORT=5433
SRC=odoo_src
DB=odoo_fixture
SRC_MARKER_VERSION=2   # build_source.sh MARKER_VERSION the fixture is cloned from
MARKER=migration.fixture
MARKER_VERSION=1       # bump when the fixture changes so an old odoo_fixture is rebuilt
export PGPORT PGHOST=/var/run/postgresql

[ -n "${ODOO_PG_RO_DSN:-}" ] || { echo "set ODOO_PG_RO_DSN" >&2; exit 1; }
ODOO_PG_FIXTURE_DSN="$("$PY" -c 'import sys, json; d = json.loads(sys.argv[1]); d["database"] = sys.argv[2]; print(json.dumps(d))' "$ODOO_PG_RO_DSN" "$DB")"
export ODOO_PG_FIXTURE_DSN

sudo -n pg_ctlcluster 16 main status >/dev/null 2>&1 || sudo -n pg_ctlcluster 16 main start

param() { psql -X -v ON_ERROR_STOP=1 -d "$1" -tAc "SELECT value FROM ir_config_parameter WHERE key='$2'"; }

src_marker="$(param "$SRC" migration.fixture_source)"
[ "$src_marker" = "$SRC_MARKER_VERSION" ] || { echo "$SRC marker is '$src_marker', expected $SRC_MARKER_VERSION: run $HERE/build_source.sh first" >&2; exit 1; }
src_uuid="$(param "$SRC" database.uuid)"   # new on every odoo_src rebuild; the clone inherits it

FILESTORE="$("$PY" -c 'import sys; sys.path.insert(0, sys.argv[1]); from odoo.tools import config; print(config.filestore(sys.argv[2]))' "$REPO" "$DB")"
SRC_FILESTORE="$(dirname "$FILESTORE")/$SRC"

built= fixture_uuid=
exists="$(psql -X -v ON_ERROR_STOP=1 -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB'")"
if [ "$exists" = 1 ]; then
  built="$(param "$DB" "$MARKER")"
  fixture_uuid="$(param "$DB" database.uuid)"
fi
if [ "$built" != "$MARKER_VERSION" ] || [ "$fixture_uuid" != "$src_uuid" ]; then
  dropdb --if-exists "$DB"
  rm -rf "$FILESTORE"
  createdb -T "$SRC" "$DB"   # clone; schema and table grants (odoo_ro SELECT) come with the template
  [ -d "$SRC_FILESTORE" ] && cp -a "$SRC_FILESTORE" "$FILESTORE"   # attachments live outside the database
  "$PY" "$REPO/odoo-bin" shell --addons-path="$REPO/addons,$REPO/odoo/addons" \
    -d "$DB" --db_port="$PGPORT" --log-level=warn < "$HERE/fixture_outlier.py"
fi

psql -X -v ON_ERROR_STOP=1 -q -d "$DB" <<SQL
REVOKE ALL ON DATABASE $DB FROM PUBLIC;
GRANT CONNECT ON DATABASE $DB TO odoo_ro;
SQL

"$RECON_PY" "$HERE/fixture_manifest.py" --out "$HERE/odoo_fixture.json"
