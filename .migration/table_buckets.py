#!/usr/bin/env python3
"""Place every table of the read-only source in exactly one bucket, mechanically,
from the catalog the ORM itself maintains (ir_model, ir_model_data, ir_model_fields,
ir_module_module_dependency).

  orm_framework     table name ir_* or orm_signaling_* (ORM registry/cache signaling)
  migrate           owning module is product or uom: modeled and migrated this run
  model_only        owning module is sale, purchase, stock or account: modeled, not migrated
  shared_postgresql any other owner (base, mail, ...): stays in PostgreSQL

The owning module of a table is the first module that registered its model (or its
many2many relation field) in ir_model_data, i.e. the module that defines it; every
later registering module only extends it. That is checked, not assumed: the script
fails if any registering module does not depend (transitively, via
ir_module_module_dependency) on the owner it was assigned.

`exclude_tables` lists the shared_postgresql + orm_framework tables (not views) to pass
to pipeline.py as --exclude-table, so the proposal covers migrate + model_only together.

Reads the DSN from the env var named by --source-dsn-secret through the plugin's
`parse_postgresql_secret` (JSON secret shape; run with the recon harness venv); writes
.migration/table_buckets.json. Nothing here decides."""
import argparse
import json
import os
import pathlib
import sys

import psycopg
from recon.adapters import parse_postgresql_secret  # plugin harness (mongo-recon-harness)

MIGRATE_MODULES = ("product", "uom")
MODEL_ONLY_MODULES = ("sale", "purchase", "stock", "account")
FRAMEWORK_PREFIXES = ("ir_", "orm_signaling_")
FRAMEWORK_CITE = "odoo/orm/registry.py (orm_signaling_* tables); odoo/addons/base/models/ir_*.py"

REGISTRATIONS = """
registrations AS (
  SELECT replace(m.model, '.', '_') AS table_name, m.model, m.transient, d.module, d.id, d.name
  FROM ir_model m JOIN ir_model_data d ON d.model = 'ir.model' AND d.res_id = m.id
  UNION ALL
  SELECT f.relation_table, NULL, NULL, d.module, d.id, d.name
  FROM ir_model_fields f JOIN ir_model_data d ON d.model = 'ir.model.fields' AND d.res_id = f.id
  WHERE f.relation_table IS NOT NULL
),
owned AS (
  SELECT table_name, min(model) AS model, bool_or(transient) AS transient,
         array_agg(DISTINCT module ORDER BY module) AS modules,
         (array_agg(module ORDER BY id))[1] AS owner,
         (array_agg(module || '.' || name ORDER BY id))[1] AS cite
  FROM registrations GROUP BY table_name
)"""

SQL = "WITH " + REGISTRATIONS + """
SELECT c.relname AS table_name, c.relkind::text AS relkind,
       o.model, o.transient, o.modules, o.owner, o.cite
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN owned o ON o.table_name = c.relname
WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p', 'v', 'm')
ORDER BY 1
"""

OWNER_CHECK_SQL = "WITH RECURSIVE " + REGISTRATIONS + """,
dep(module, depends_on) AS (
  SELECT mm.name, dd.name FROM ir_module_module mm
  JOIN ir_module_module_dependency dd ON dd.module_id = mm.id
  UNION
  SELECT dep.module, dd.name FROM dep
  JOIN ir_module_module mm ON mm.name = dep.depends_on
  JOIN ir_module_module_dependency dd ON dd.module_id = mm.id
)
SELECT r.table_name, o.owner, r.module
FROM registrations r JOIN owned o USING (table_name)
WHERE r.module <> o.owner
  AND NOT EXISTS (SELECT 1 FROM dep WHERE dep.module = r.module AND dep.depends_on = o.owner)
ORDER BY 1, 3
"""


def bucket(name: str, owner: str | None) -> str | None:
    if name.startswith(FRAMEWORK_PREFIXES):
        return "orm_framework"
    if owner is None:
        return None
    if owner in MIGRATE_MODULES:
        return "migrate"
    if owner in MODEL_ONLY_MODULES:
        return "model_only"
    return "shared_postgresql"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-dsn-secret", default="ODOO_PG_RO_DSN")
    ap.add_argument("--out", type=pathlib.Path, default=pathlib.Path(".migration/table_buckets.json"))
    a = ap.parse_args()
    raw = os.environ.get(a.source_dsn_secret)
    if not raw:
        print(f"{a.source_dsn_secret} is not set", file=sys.stderr)
        return 2
    params = parse_postgresql_secret(raw)
    params.pop("schema", None)
    with psycopg.connect(**params, autocommit=True) as conn:
        conn.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY")
        rows = conn.execute(SQL).fetchall()
        owner_violations = conn.execute(OWNER_CHECK_SQL).fetchall()
    if owner_violations:
        print("owner check failed (registering module does not depend on the first registering module): "
              + ", ".join(f"{t}: {m} !-> {o}" for t, o, m in owner_violations), file=sys.stderr)
        return 1
    tables, unplaced = [], []
    for name, relkind, model, transient, modules, owner, cite in rows:
        b = bucket(name, owner)
        if b is None:
            unplaced.append(name)
            continue
        tables.append({
            "table": name,
            "kind": {"r": "table", "p": "table", "v": "view", "m": "materialized_view"}[relkind],
            "bucket": b,
            "model": model,
            "transient": transient,
            "owner": owner,
            "modules": modules or [],
            "cite": cite or FRAMEWORK_CITE,
        })
    if unplaced:
        print("unplaced tables (no owning module, not a framework prefix): " + ", ".join(unplaced),
              file=sys.stderr)
        return 1
    buckets = ("migrate", "model_only", "shared_postgresql", "orm_framework")
    counts = {b: sum(1 for t in tables if t["bucket"] == b) for b in buckets}
    exclude = [t["table"] for t in tables
               if t["bucket"] in ("shared_postgresql", "orm_framework") and t["kind"] == "table"]
    a.out.write_text(json.dumps({
        "buckets_version": 2,
        "source": {"family": "postgresql", "secret": a.source_dsn_secret, "schema": "public"},
        "migrate_modules": list(MIGRATE_MODULES),
        "model_only_modules": list(MODEL_ONLY_MODULES),
        "rules": {
            "owner": "module of the first ir_model_data row (lowest id) registering the model "
                     "(model=ir.model) or the relation field (model=ir.model.fields); every other "
                     "registering module must depend on it transitively (ir_module_module_dependency)",
            "orm_framework": "table name starts with " + " or ".join(FRAMEWORK_PREFIXES),
            "migrate": "owner in migrate_modules",
            "model_only": "owner in model_only_modules",
            "shared_postgresql": "any other owner",
            "exclude_tables": "shared_postgresql + orm_framework objects of kind table, "
                              "passed to pipeline.py as --exclude-table",
        },
        "counts": counts,
        "exclude_tables": exclude,
        "tables": tables,
    }, indent=2, sort_keys=False) + "\n")
    print(f"{a.out}: {len(tables)} objects, " + ", ".join(f"{k}={v}" for k, v in counts.items())
          + f", exclude_tables={len(exclude)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
