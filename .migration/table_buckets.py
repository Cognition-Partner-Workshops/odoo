#!/usr/bin/env python3
"""Place every table of the read-only source in exactly one bucket, mechanically,
from the catalog the ORM itself maintains (ir_model, ir_model_data, ir_model_fields).

  orm_framework     table name ir_* or orm_signaling_* (ORM registry/cache signaling)
  in_scope          every module that registers the model or relation field is an
                    in-scope addon (product, uom)
  shared_postgresql any other owner: shared with out-of-scope addons, stays in PostgreSQL

Reads the DSN from the env var named by --source-dsn-secret through the plugin's
`parse_postgresql_secret` (JSON secret shape; run with the recon harness venv); writes .migration/table_buckets.json. Nothing here decides."""
import argparse
import json
import os
import pathlib
import sys

import psycopg
from recon.adapters import parse_postgresql_secret  # plugin harness (mongo-recon-harness)

IN_SCOPE_MODULES = ("product", "uom")
FRAMEWORK_PREFIXES = ("ir_", "orm_signaling_")
FRAMEWORK_CITE = "odoo/orm/registry.py (orm_signaling_* tables); odoo/addons/base/models/ir_*.py"

SQL = """
WITH t AS (
  SELECT c.relname AS table_name, c.relkind::text AS relkind
  FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
  WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p', 'v', 'm')
),
model_tables AS (
  SELECT replace(m.model, '.', '_') AS table_name, m.model, m.transient,
         array_agg(DISTINCT d.module ORDER BY d.module) AS modules,
         (array_agg(d.module || '.' || d.name ORDER BY d.id))[1] AS cite
  FROM ir_model m JOIN ir_model_data d ON d.model = 'ir.model' AND d.res_id = m.id
  GROUP BY m.model, m.transient
),
rel_tables AS (
  SELECT f.relation_table AS table_name,
         array_agg(DISTINCT d.module ORDER BY d.module) AS modules,
         (array_agg(d.module || '.' || d.name ORDER BY d.id))[1] AS cite
  FROM ir_model_fields f
  JOIN ir_model_data d ON d.model = 'ir.model.fields' AND d.res_id = f.id
  WHERE f.relation_table IS NOT NULL
  GROUP BY f.relation_table
)
SELECT t.table_name, t.relkind, mt.model, mt.transient,
       coalesce(mt.modules, rt.modules) AS modules, coalesce(mt.cite, rt.cite) AS cite
FROM t LEFT JOIN model_tables mt USING (table_name) LEFT JOIN rel_tables rt USING (table_name)
ORDER BY 1
"""


def bucket(name: str, modules: list[str] | None) -> str | None:
    if name.startswith(FRAMEWORK_PREFIXES):
        return "orm_framework"
    if not modules:
        return None
    return "in_scope" if set(modules) <= set(IN_SCOPE_MODULES) else "shared_postgresql"


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
    tables, unplaced = [], []
    for name, relkind, model, transient, modules, cite in rows:
        b = bucket(name, modules)
        if b is None:
            unplaced.append(name)
            continue
        tables.append({
            "table": name,
            "kind": {"r": "table", "p": "table", "v": "view", "m": "materialized_view"}[relkind],
            "bucket": b,
            "model": model,
            "transient": transient,
            "modules": modules or [],
            "cite": cite or FRAMEWORK_CITE,
        })
    if unplaced:
        print("unplaced tables (no owning module, not a framework prefix): " + ", ".join(unplaced),
              file=sys.stderr)
        return 1
    counts = {b: sum(1 for t in tables if t["bucket"] == b)
              for b in ("in_scope", "shared_postgresql", "orm_framework")}
    a.out.write_text(json.dumps({
        "buckets_version": 1,
        "source": {"family": "postgresql", "secret": a.source_dsn_secret, "schema": "public"},
        "in_scope_modules": list(IN_SCOPE_MODULES),
        "rules": {
            "orm_framework": "table name starts with " + " or ".join(FRAMEWORK_PREFIXES),
            "in_scope": "every module registering the model (ir_model_data model=ir.model) or the "
                        "relation field (ir_model_data model=ir.model.fields) is an in-scope module",
            "shared_postgresql": "any other registering module",
        },
        "counts": counts,
        "tables": tables,
    }, indent=2, sort_keys=False) + "\n")
    print(f"{a.out}: {len(tables)} objects, " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
