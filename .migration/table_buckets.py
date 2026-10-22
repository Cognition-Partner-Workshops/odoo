"""Bucket every public base table of odoo_src for gate g-census-complete (plan step s2.1).

Buckets (decision d-scope):
  in_scope           owner module is a scope addon or an in-closure bridge -> MongoDB
  orm_framework      name matches FRAMEWORK_RE; stays on PostgreSQL whatever its owner
  shared_postgresql  any other table (owner outside the scope); stays on PostgreSQL

Registering modules of a table: the modules holding an ir_model_data row for the ir.model whose
default table name it is, plus the modules holding an ir_model_data row for an ir.model.fields
row whose relation_table it is. Owner: the registering module every other registering module
depends on transitively (ir_module_module_dependency). With no such unique module, the owner is
the alphabetically first registering module that depends on no other registering module, and
the row is marked ambiguous. Scope modules: SCOPE_ADDONS plus every installed module outside
the closure C = SCOPE_ADDONS + their transitive dependencies that depends on a scope module and
whose direct dependencies all lie in C or among such bridges (fixpoint).

Run (read-only, JSON secret bound to ODOO_PG_RO_DSN):
  PYTHONPATH=<plugin>/skills/mongo-recon-harness/harness python .migration/table_buckets.py
Writes .migration/table_buckets.json; --exclude-file PATH also writes the non-in_scope table
names, one per line, for pipeline.py --exclude-table.
"""
import argparse
import json
import os
import pathlib
import re
import sys

import psycopg
from recon.adapters import parse_postgresql_secret

SCOPE_ADDONS = ("product", "uom", "sale", "purchase", "stock", "account")
FRAMEWORK_RE = re.compile(r"^(ir|res|mail|bus|web|base|orm_signaling)_")
OUT = pathlib.Path(__file__).resolve().parent / "table_buckets.json"


def closure(start, deps):
    seen, todo = set(), list(start)
    while todo:
        m = todo.pop()
        if m not in seen:
            seen.add(m)
            todo.extend(deps.get(m, ()))
    return seen


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--exclude-file", type=pathlib.Path)
    args = ap.parse_args(argv)
    with psycopg.connect(**parse_postgresql_secret(os.environ["ODOO_PG_RO_DSN"])) as conn:
        conn.read_only = True
        q = lambda sql: conn.execute(sql).fetchall()
        tables = sorted(r[0] for r in q(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"))
        installed = {r[0]: r[1] for r in q(
            "SELECT name, auto_install FROM ir_module_module WHERE state = 'installed'")}
        deps = {}
        for mod, dep in q("SELECT m.name, d.name FROM ir_module_module_dependency d "
                          "JOIN ir_module_module m ON m.id = d.module_id "
                          "WHERE m.state = 'installed'"):
            deps.setdefault(mod, set()).add(dep)
        model_regs = q("SELECT m.model, d.module, d.name FROM ir_model m "
                       "JOIN ir_model_data d ON d.model = 'ir.model' AND d.res_id = m.id")
        rel_regs = q("SELECT f.relation_table, d.module, d.name FROM ir_model_fields f "
                     "JOIN ir_model_data d ON d.model = 'ir.model.fields' AND d.res_id = f.id "
                     "WHERE f.relation_table IS NOT NULL")

    tableset = set(tables)
    regs = {}
    for model, module, xmlid in model_regs:
        t = model.replace(".", "_")
        if t in tableset:
            regs.setdefault(t, {}).setdefault(module, set()).add(f"{module}.{xmlid}")
    for t, module, xmlid in rel_regs:
        if t in tableset:
            regs.setdefault(t, {}).setdefault(module, set()).add(f"{module}.{xmlid}")

    tdeps = {m: closure(deps.get(m, ()), deps) for m in installed}
    base_closure = closure(SCOPE_ADDONS, deps)
    scope = set(SCOPE_ADDONS)
    bridges = set()
    while True:
        allowed = base_closure | bridges
        new = {m for m in installed if m not in allowed
               and tdeps[m] & scope and deps.get(m, set()) <= allowed}
        if not new:
            break
        bridges |= new
        scope |= new

    rows, counts, framework_scope_owned, ambiguous = {}, {}, [], []
    for t in tables:
        by_mod = regs.get(t, {})
        mods = sorted(by_mod)
        owner, amb = None, False
        if mods:
            roots = [m for m in mods if all(m == o or m in tdeps.get(o, ()) for o in mods)]
            if len(roots) == 1:
                owner = roots[0]
            else:
                amb = True
                owner = sorted(m for m in mods if not (tdeps.get(m, set()) & (set(mods) - {m})))[0]
        if FRAMEWORK_RE.match(t):
            bucket, rule = "orm_framework", f"name matches {FRAMEWORK_RE.pattern}"
            if owner in scope:
                framework_scope_owned.append(t)
        elif owner in scope:
            bucket, rule = "in_scope", f"owner {owner} is a scope module"
        else:
            bucket = "shared_postgresql"
            rule = f"owner {owner} is outside the scope" if owner else "no registering module"
        if amb:
            ambiguous.append(t)
        counts[bucket] = counts.get(bucket, 0) + 1
        rows[t] = {
            "bucket": bucket,
            "owner": owner,
            "registered_by": mods,
            "rule": rule,
            "cite": sorted(x for xs in by_mod.values() for x in xs) if owner else
                    ["information_schema.tables (no ir.model / relation_table registration)"],
            **({"ambiguous_owner": True} if amb else {}),
        }

    doc = {
        "kind": "table-buckets",
        "decision": "d-scope",
        "database": "odoo_src",
        "table_count": len(tables),
        "counts": dict(sorted(counts.items())),
        "scope_addons": list(SCOPE_ADDONS),
        "bridges": sorted(bridges),
        "framework_regex": FRAMEWORK_RE.pattern,
        "framework_tables_owned_by_scope": framework_scope_owned,
        "ambiguous_owner_tables": ambiguous,
        "tables": rows,
    }
    OUT.write_text(json.dumps(doc, indent=1, sort_keys=False) + "\n")
    if args.exclude_file:
        args.exclude_file.write_text(
            "".join(f"{t}\n" for t, r in rows.items() if r["bucket"] != "in_scope"))
    assert sum(counts.values()) == len(tables)
    print(json.dumps({"tables": len(tables), **doc["counts"], "bridges": doc["bridges"],
                      "framework_owned_by_scope": framework_scope_owned,
                      "ambiguous": ambiguous}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
