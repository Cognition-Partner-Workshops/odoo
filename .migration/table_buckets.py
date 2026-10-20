#!/usr/bin/env python3
"""Bucket every table of the read-only source odoo_src for run unt12 (ticket s2.1-pipeline).

Scope rule (an assumption the manager picked): a table is in scope when its owning module
is one of SCOPE_MODULES or one of their bridges, where a bridge is an installed
auto_install module whose dependencies all lie in the scope closure. Framework tables
(ir_*, res_*, mail_*, bus_*, web_*, base_* and the model-less orm_signaling_*/ir_act*
tables) stay on PostgreSQL as orm_framework; every other out-of-scope table is
shared_postgresql.

The owner of a model table is derived from the ir_model_data rows that register its
model (model = 'ir.model'); the owner of a relation table from the rows that register
the many2many fields using it (model = 'ir.model.fields'). The owner is the registering
module every other registering module depends on transitively ("dependency root"),
which does not depend on ir_model_data row order; when no unique root exists the
alphabetically first registering module is taken and the table is listed under
owner_ambiguous. The lowest-id owner is computed too and every table where the two differ
is listed under owner_flips.

Reads only. The source is reached through the JSON secret named by --source-dsn-secret
(bound in a one-shot exec); the value is never printed.
Usage: table_buckets.py --out .migration/table_buckets.json [--print-excludes]
"""
import argparse
import json
import os
import re
import sys

import psycopg

SCOPE_MODULES = ("product", "uom", "sale", "purchase", "stock", "account")
FRAMEWORK_TABLES = re.compile(r"^(ir|res|mail|bus|web|base|orm_signaling)_")


def connect(secret_name):
    value = os.environ.get(secret_name)
    if not value:
        sys.exit(f"table_buckets: {secret_name} is not set")
    kw = json.loads(value)
    kw["dbname"] = kw.pop("database")
    conn = psycopg.connect(**kw, autocommit=True)
    conn.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY")
    return conn


def closure(deps, roots):
    """Modules reachable from roots through the dependency graph (roots included)."""
    seen, stack = set(), list(roots)
    while stack:
        m = stack.pop()
        if m not in seen:
            seen.add(m)
            stack.extend(deps.get(m, ()))
    return seen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-dsn-secret", default="ODOO_PG_RO_DSN")
    ap.add_argument("--out", required=True)
    ap.add_argument("--print-excludes", action="store_true")
    a = ap.parse_args()
    conn = connect(a.source_dsn_secret)

    deps = {}
    auto = set()
    for name, auto_install, dep in conn.execute(
            "SELECT m.name, m.auto_install, d.name FROM ir_module_module m "
            "LEFT JOIN ir_module_module_dependency d ON d.module_id = m.id "
            "WHERE m.state = 'installed'"):
        deps.setdefault(name, set())
        if dep:
            deps[name].add(dep)
        if auto_install:
            auto.add(name)
    depends_on = {m: closure(deps, deps[m]) for m in deps}
    scope = set(SCOPE_MODULES)
    while True:
        bridges = {m for m in auto - scope if deps[m] and deps[m] <= scope}
        if not bridges:
            break
        scope |= bridges
    bridge_modules = sorted(scope - set(SCOPE_MODULES))

    # Registering rows per table: model tables through ir_model, relation tables through
    # the many2many fields that name them.
    registrations = {}
    for table, module, xmlid, row_id in conn.execute(
            "SELECT replace(m.model, '.', '_'), d.module, d.module || '.' || d.name, d.id "
            "FROM ir_model_data d JOIN ir_model m ON m.id = d.res_id "
            "WHERE d.model = 'ir.model' "
            "UNION ALL "
            "SELECT f.relation_table, d.module, d.module || '.' || d.name, d.id "
            "FROM ir_model_data d JOIN ir_model_fields f ON f.id = d.res_id "
            "WHERE d.model = 'ir.model.fields' AND f.relation_table IS NOT NULL"):
        registrations.setdefault(table, []).append((row_id, module, xmlid))

    tables = {}
    counts = {}
    flips, ambiguous, conflicts = [], [], []
    for name, kind in conn.execute(
            "SELECT c.relname, CASE c.relkind WHEN 'v' THEN 'view' ELSE 'table' END "
            "FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p', 'v', 'm') "
            "ORDER BY c.relname"):
        rows = sorted(registrations.get(name, []))
        owner = lowest = cite = None
        if rows:
            lowest = rows[0][1]
            modules = {module for _, module, _ in rows}
            roots = sorted(m for m in modules if all(m == o or m in depends_on[o] for o in modules))
            # No unique root: fall back to the alphabetically first module, which also does
            # not depend on registration order; the table is listed for the manager.
            owner = roots[0] if roots else min(modules)
            if len(roots) != 1:
                ambiguous.append({"table": name, "modules": sorted(modules), "roots": roots})
            row_id, _, xmlid = next(r for r in rows if r[1] == owner)
            cite = f"ir_model_data id={row_id} {xmlid}"
            if owner != lowest:
                flips.append({"table": name, "dependency_root": owner, "lowest_id": lowest})
        if FRAMEWORK_TABLES.match(name):
            bucket = "orm_framework"
            if owner in scope:
                conflicts.append({"table": name, "owner": owner})
            cite = cite or "no ir_model_data registration; framework table by name"
        elif owner is None:
            sys.exit(f"table_buckets: {name} has no ir_model_data registration and no framework name")
        elif owner in scope:
            bucket = "in_scope"
        else:
            bucket = "shared_postgresql"
        tables[name] = {"kind": kind, "bucket": bucket, "owner": owner,
                        "owner_lowest_id": lowest, "cite": cite}
        if kind == "table":
            counts[bucket] = counts.get(bucket, 0) + 1

    marker, uuid = (dict(conn.execute(
        "SELECT key, value FROM ir_config_parameter "
        "WHERE key IN ('migration.fixture_source', 'database.uuid')").fetchall()).get(k)
        for k in ("migration.fixture_source", "database.uuid"))
    excludes = sorted(t for t, v in tables.items()
                      if v["kind"] == "table" and v["bucket"] != "in_scope")
    out = {
        "source": {"database": "odoo_src", "fixture_source_marker": marker, "database_uuid": uuid},
        "owner_rule": "dependency root of the registering modules (order-independent); "
                      "lowest-id owner kept for comparison",
        "scope_modules": list(SCOPE_MODULES), "bridge_modules": bridge_modules,
        "bucket_counts_tables": counts, "views": sorted(t for t, v in tables.items() if v["kind"] == "view"),
        "exclude_tables": excludes, "owner_flips": flips, "owner_ambiguous": ambiguous,
        "framework_named_in_scope_owner": conflicts, "tables": tables,
    }
    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=False)
        fh.write("\n")
    print(f"table_buckets: {sum(counts.values())} tables {counts}, {len(out['views'])} views, "
          f"bridges={bridge_modules}, owner_flips={len(flips)}, ambiguous={len(ambiguous)}, "
          f"framework-named with in-scope owner={len(conflicts)} -> {a.out}")
    if a.print_excludes:
        print(" ".join(f"--exclude-table {t}" for t in excludes))


if __name__ == "__main__":
    main()
