"""Render the s2.3 dependency register (NOTES.md section) from register_db.py, register_probe.py
and register_scan.py output. Dispositions:
  A  storage path handles it: generic framework code (core, base, mixins of non-scope modules)
     whose table is resolved per model at run time, ORM-only crons, foreign keys
  B  unit owns it: scope-module (or bridge) code naming in-scope tables, reports and views over
     in-scope tables; owned by the unit that migrates the first-moved table it names
  C  out of estate: no in-scope table, upgrade scripts that never run on this database
  python .migration/register_notes.py --src ../odoo-unt13-src --db db.json --probe probe.json \
      --scan scan.json > section.md
"""
import argparse
import ast
import collections
import json
import pathlib
import re

IDENT_RE = re.compile(r"[a-z_][a-z0-9_]*")
ON_DEL = {"a": "no action", "r": "restrict", "c": "cascade", "n": "set null", "d": "set default"}
FANOUT = {
    ("addons/account/models/account_account.py", "_action_unmerge"): ("account_account",),
    ("odoo/addons/base/wizard/base_partner_merge.py", "_update_foreign_keys_generic"): (
        "account_account", "res_partner", "res_partner_bank"),
    ("odoo/addons/base/wizard/base_partner_merge.py", "_update_reference_fields_generic"): (
        "account_account", "res_partner", "res_partner_bank"),
}


def is_test(rel):
    parts = rel.split("/")
    return "tests" in parts or parts[-1].startswith("test_")


def model_methods(src, installed, model):
    """{method name: [(file, FunctionDef)]} over every class with _name/_inherit == model."""
    out = collections.defaultdict(list)
    for m in installed:
        for base in (src / "addons" / m, src / "odoo" / "addons" / m):
            for f in sorted(base.rglob("*.py")) if base.is_dir() else ():
                text = f.read_text()
                if "/tests/" in str(f) or repr(model) not in text and '"%s"' % model not in text:
                    continue
                for cls in ast.walk(ast.parse(text)):
                    if isinstance(cls, ast.ClassDef) and model in [
                            n.value for st in cls.body if isinstance(st, ast.Assign)
                            for t in st.targets if isinstance(t, ast.Name)
                            and t.id in ("_name", "_inherit")
                            for n in ast.walk(st.value) if isinstance(n, ast.Constant)]:
                        for fn in cls.body:
                            if isinstance(fn, ast.FunctionDef):
                                out[fn.name].append((f, fn))
    return out


def cron_reach(src, installed, model, method):
    """Models named via env['x'] by `method` and the same-model methods it calls, 2 levels."""
    defs, found, todo, seen = model_methods(src, installed, model), set(), {method}, set()
    for _ in range(3):
        nxt = set()
        for name in todo - seen:
            seen.add(name)
            for _f, fn in defs.get(name, ()):
                for n in ast.walk(fn):
                    if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant) \
                            and isinstance(n.slice.value, str) and "." in n.slice.value:
                        found.add(n.slice.value)
                    elif isinstance(n, ast.Attribute) and n.attr in defs:
                        nxt.add(n.attr)
        todo = nxt
    return found


def class_model_refs(src, installed, model_names):
    """Model names referenced anywhere in the class bodies defining each model."""
    refs = collections.defaultdict(set)
    for module in installed:
        for base in (src / "addons" / module, src / "odoo" / "addons" / module):
            if not base.is_dir():
                continue
            for f in sorted(base.rglob("*.py")):
                rel = f.relative_to(src).as_posix()
                if is_test(rel):
                    continue
                tree = ast.parse(f.read_text(), rel)
                for cls in ast.walk(tree):
                    if not isinstance(cls, ast.ClassDef):
                        continue
                    defined = set()
                    for st in cls.body:
                        if isinstance(st, ast.Assign):
                            targets, value = st.targets, st.value
                        elif isinstance(st, ast.AnnAssign):
                            targets, value = [st.target], st.value
                        else:
                            continue
                        if any(isinstance(t, ast.Name) and t.id in ("_name", "_inherit")
                               for t in targets):
                            defined |= {n.value for n in ast.walk(value)
                                        if isinstance(n, ast.Constant) and
                                        isinstance(n.value, str)}
                    defined &= model_names
                    if not defined:
                        continue
                    referenced = {n.value for n in ast.walk(cls)
                                  if isinstance(n, ast.Constant) and
                                  isinstance(n.value, str) and n.value in model_names}
                    for model in defined:
                        refs[model].update(referenced)
            break
    return refs


def main():
    ap = argparse.ArgumentParser()
    for k in ("src", "db", "probe", "scan"):
        ap.add_argument("--" + k, type=pathlib.Path, required=True)
    ap.add_argument("--buckets", type=pathlib.Path,
                    default=pathlib.Path(__file__).resolve().parent / "table_buckets.json")
    a = ap.parse_args()
    db, probe, scan = (json.loads(p.read_text()) for p in (a.db, a.probe, a.scan))
    tb = json.loads(a.buckets.read_text())
    bucket = {t: v["bucket"] for t, v in tb["tables"].items()}
    in_scope = {t for t, b in bucket.items() if b == "in_scope"}
    scope_mods = set(tb["scope_addons"]) | set(tb["bridges"])
    table_of = {m: v["table"] for m, v in probe["models"].items()}
    model_names = set(probe["models"])
    class_refs = class_model_refs(a.src, db["installed_modules"], model_names)
    fk_fanout = collections.defaultdict(set)
    for fk in db["foreign_keys"]:
        if fk["table"] in in_scope:
            fk_fanout[fk["ref_table"]].add(fk["table"])
    out, counts = [], collections.Counter()
    w = out.append

    def disp_site(s):
        if s["kind"] == "upgrade_script":
            return "C", "upgrade script: runs only on -u from an older module version"
        if not s["in_scope"]:
            return "C", "no in-scope table"
        if s["function"] == "get_kpi_summary" and not s["model"]:
            return "B", "bare cursor without a registry: no ORM hook can reroute it"
        if s["function"] == "_action_unmerge":
            return "B", "dynamic: every table holding an account_account FK column"
        if (s["file"], s["function"]) in {
                ("odoo/addons/base/wizard/base_partner_merge.py",
                 "_update_foreign_keys_generic"),
                ("odoo/addons/base/wizard/base_partner_merge.py",
                 "_update_reference_fields_generic")}:
            return "A", "generic core FK fan-out"
        if s["module"] in scope_mods:
            return "B", ""
        if s["dynamic"] or s["unresolved"] or s["orm_query"]:
            return "A", "generic code; table resolved per model (%d in-scope tables)" % len(
                s["in_scope"])
        return "B", "non-scope module names in-scope tables"

    rows = {"write": [], "read": []}
    other = collections.Counter()
    for s in scan["sites"]:
        fanout_models = FANOUT.get((s["file"], s["function"]), ())
        if fanout_models:
            fanout_tables = set().union(*(fk_fanout[m] for m in fanout_models))
            s["in_scope"] = dict(s["in_scope"])
            s["in_scope"].update({t: "write" for t in fanout_tables})
            s["fanout_note"] = "; ".join(
                "FK fan-out of %s: %d in-scope tables (catalog FKs; Reference/res_id columns "
                "not included)" % (m, len(fk_fanout[m])) for m in fanout_models)
        d, why = disp_site(s)
        kind = s["kind"]
        if d == "C" and kind != "upgrade_script":
            other[kind] += 1
            continue
        op = "write" if any(v == "write" for v in s["in_scope"].values()) else "read"
        rows[op].append((s, d, why))
        counts[(kind, op, d)] += 1

    w("## s2.3 dependency register (other writers and readers)\n")
    w("Built fresh on %s at marker v4 (row_counts_sha256 `%s`, %d tables, %d installed modules)"
      " from AST scans of the source tree at SOURCE_COMMIT plus catalog reads; in scope = the %d"
      " `in_scope` tables of `.migration/table_buckets.json`. Generators: "
      "`.migration/register_db.py` (read-only catalog facts, refuses on a fingerprint mismatch), "
      "`.migration/register_probe.py` (rendered `_table_sql` on a throwaway clone), "
      "`.migration/register_scan.py` (AST), `.migration/register_notes.py` (this section).\n"
      % (db["database"] if "database" in db else "odoo_src", db["row_counts_sha256"],
         db["table_count"], len(db["installed_modules"]), len(in_scope)))
    w("Dispositions: **A** storage path handles it; **B** unit owns it (the unit that migrates"
      " the first-moved table it names; every later unit naming it re-checks it); **C** out of"
      " estate.\n")
    w("### Coverage\n")
    w("Entry points scanned in every non-test .py file of the %d installed modules and the core"
      " (`odoo/` outside `odoo/addons`): cursor `execute`, `execute_values`, `executemany`,"
      " `copy_expert`/`copy_from`/`copy_to`, `mogrify`; `env.execute_query`/"
      "`execute_query_dict`; `psycopg2.extras.execute_values`; every `odoo.tools.sql` helper that"
      " takes a table (`create_index`, `column_exists`, `drop_view_if_exists`, `add_foreign_key`,"
      " `increment_fields_skiplock`, ...); `SQL(...)` fragments built outside a cursor call"
      " (search/order/compute overrides); `_auto = False` models (`_table_sql`/`_table_query`"
      " rendered from the registry, `init()` views from `pg_rewrite`); `ir_cron` and code server"
      " actions; triggers, functions, views and foreign keys from the catalog. Tables come from"
      " literal names in the SQL text, `self._table`/`env[m]._table` resolved through the"
      " class's model (abstract mixins expand to every stored model inheriting them), and for"
      " SQL built from ORM `Query`/`TableSQL` objects the function's `env[...]` models or the"
      " class's model. `SELECT ... FOR UPDATE` is a lock, not a write. Sites that name no"
      " in-scope table are counted, not listed: %s.\n" % (
          len(db["installed_modules"]),
          ", ".join("%d %s" % (n, k) for k, n in sorted(other.items()))))

    def site_table(title, items):
        w("### %s (%d)\n" % (title, len(items)))
        w("| # | disp | kind | site | function | in-scope tables (w = written) | note |")
        w("|---|---|---|---|---|---|---|")
        for i, (s, d, why) in enumerate(sorted(items, key=lambda x: (x[0]["file"],
                                                                      x[0]["line"])), 1):
            tabs = s["in_scope"]
            if len(tabs) > 8:
                ts = "%d tables (%d written)" % (len(tabs), sum(v == "write" for v in
                                                                 tabs.values()))
            else:
                ts = ", ".join(t + (" (w)" if v == "write" else "") for t, v in tabs.items())
            note = why
            if s["view_ddl"]:
                note = (note + "; " if note else "") + "view DDL: reads only"
            if s["dynamic"] and not why:
                note = (note + "; " if note else "") + "dynamic table"
            if s.get("fanout_note"):
                note = (note + "; " if note else "") + s["fanout_note"]
            w("| %d | %s | %s | `%s:%d` | `%s.%s` | %s | %s |" % (
                i, d, s["kind"], s["file"], s["line"], s["model"] or "-",
                s["function"] or "-", ts, note))
        w("")

    site_table("Raw SQL writes into in-scope tables", rows["write"])
    site_table("Raw SQL reads of in-scope tables", rows["read"])

    w("### SQL views and `_table_sql` reports\n")
    w("| # | disp | model | how | in-scope tables read | note |")
    w("|---|---|---|---|---|---|")
    rep_rows = []
    views = {v["name"]: v["reads"] for v in db["views"]}
    for m, v in sorted(probe["table_sql"].items()):
        tables = set(IDENT_RE.findall(v.get("sql", "").lower())) & set(bucket)
        view = table_of.get(m)
        if view in views:
            tables |= set(views[view])
            how = "init() view `%s` + `_table_sql`" % view
        else:
            how = "`%s`" % v["attr"]
        ins = sorted(tables & in_scope)
        d = "B" if ins else "C"
        rep_rows.append((d, m, how, ins, v.get("error", "")))
    for name, reads in views.items():
        if name not in {table_of.get(m) for m in probe["table_sql"]}:
            ins = sorted(set(reads) & in_scope)
            rep_rows.append(("B" if ins else "C", "-", "view `%s`" % name, ins, ""))
    for i, (d, m, how, ins, err) in enumerate(rep_rows, 1):
        counts[("report", "read", d)] += 1
        w("| %d | %s | `%s` | %s | %s | %s |" % (i, d, m, how, ", ".join(ins) or "-",
                                                 err or ("rebuilt from Mongo data by the "
                                                         "owning unit" if d == "B" else "")))
    w("")

    w("### Scheduled jobs (`ir_cron`)\n")
    w("| id | disp | xmlid | model | active | every | direct (method-level) | "
      "class-level 2-hop (count + up to 6 names) | note |")
    w("|---|---|---|---|---|---|---|---|---|")
    sites_by_fn = collections.defaultdict(list)
    for s in scan["sites"]:
        sites_by_fn[(s["model"], s["function"])].append(s)
    for c in db["crons"]:
        meth = re.findall(r"model\.(\w+)\(", c["code"] or "")
        direct_reach = set()
        for mt in meth:
            for x in cron_reach(a.src, db["installed_modules"], c["model"], mt):
                if table_of.get(x) in in_scope:
                    direct_reach.add(table_of[x])
        own = table_of.get(c["model"])
        if own in in_scope:
            direct_reach.add(own)
        class_models = set(class_refs.get(c["model"], ()))
        two_hop_models = class_models | {
            target for model in class_models for target in class_refs.get(model, ())}
        class_reach = {table_of[m] for m in two_hop_models if table_of.get(m) in in_scope}
        if own in in_scope:
            class_reach.add(own)
        raw = [s for mt in meth for s in sites_by_fn.get((c["model"], mt), []) if s["in_scope"]]
        if c["xmlid"] == "base.autovacuum_job":
            d, note = "A", "vacuums every transient/in-scope model with _gc_* hooks; pause it"
        elif raw:
            d, note = "B", "reaches raw SQL"
            if class_reach and not direct_reach:
                note += "; indirect ORM reach, conservative"
        elif direct_reach:
            d, note = "A", "ORM writes; pause during load windows"
        elif class_reach:
            d, note = "A", "indirect ORM reach, conservative"
        else:
            d, note = "C", ""
        reaches_scope = bool(direct_reach or class_reach or raw or
                             c["xmlid"] == "base.autovacuum_job")
        counts[("cron", "write" if reaches_scope else "read", d)] += 1
        class_names = sorted(class_reach)
        class_display = "%d: %s%s" % (
            len(class_names), ", ".join(class_names[:6]),
            ", ..." if len(class_names) > 6 else "")
        w("| %d | %s | `%s` | `%s` | %s | %s %s | %s | %s | %s |" % (
            c["id"], d, c["xmlid"], c["model"], c["active"], c["interval_number"],
            c["interval_type"], ", ".join(sorted(direct_reach)) or "-",
            class_display if class_names else "0: -", note))
    w("")

    fks = db["foreign_keys"]
    into = [k for k in fks if k["ref_table"] in in_scope and k["table"] not in in_scope]
    out_of = [k for k in fks if k["table"] in in_scope and k["ref_table"] not in in_scope]
    inside = [k for k in fks if k["table"] in in_scope and k["ref_table"] in in_scope]
    w("### Database-side writers: foreign keys, triggers, functions\n")
    w("Triggers in the catalog: %d; user functions in `public`: %d; code server actions using"
      " the cursor: %d. Foreign keys: %d inside the in-scope set, %d from in-scope tables to"
      " PostgreSQL tables, %d from PostgreSQL tables into in-scope tables (all **A**: the"
      " storage path drops the constraint with the column move and must enforce `ondelete`"
      " itself; a PostgreSQL-side cascade into a Mongo-backed table no longer fires).\n" % (
          len(db["triggers"]), len(db["functions"]), len(db["server_actions_cursor"]),
          len(inside), len(out_of), len(into)))
    by_del = collections.Counter((k["on_del"]) for k in fks if k in out_of)
    w("In-scope -> PostgreSQL by `ondelete`: %s.\n" % ", ".join(
        "%s %d" % (ON_DEL[k], n) for k, n in sorted(by_del.items())))
    w("| PostgreSQL table (bucket) | column | -> in-scope table | ondelete |")
    w("|---|---|---|---|")
    for k in sorted(into, key=lambda k: (k["table"], k["columns"])):
        w("| %s (%s) | %s | %s | %s |" % (k["table"], bucket.get(k["table"], "?"),
                                          ",".join(k["columns"]), k["ref_table"],
                                          ON_DEL[k["on_del"]]))
    counts[("foreign_key", "write", "A")] += len(into) + len(out_of) + len(inside)
    w("")

    w("### Totals\n")
    w("| kind | op | A | B | C |")
    w("|---|---|---|---|---|")
    keys = sorted({(k, o) for k, o, _ in counts})
    for k, o in keys:
        w("| %s | %s | %d | %d | %d |" % (k, o, counts[(k, o, "A")], counts[(k, o, "B")],
                                         counts[(k, o, "C")]))
    w("")
    reports_b = sum(d == "B" for d, _m, _how, _ins, _err in rep_rows)
    writing_crons = counts[("cron", "write", "A")] + counts[("cron", "write", "B")]
    w("### Writes outside odoo_unt13\n")
    w("None during this ticket: `odoo_src` was only read (role `odoo_ro`, read-only session) and the\n"
      "`_table_sql` render ran on a throwaway clone `odoo_reg_probe`. Later units will need writes to\n"
      "the application's PostgreSQL (never `odoo_src`, never Atlas), each needing a plan decision:\n"
      "- the %d **B** reports/views above: their PostgreSQL view or `_table_sql` stops seeing rows once\n"
      "  its tables move, so the owning unit re-points or rebuilds them;\n"
      "- the %d writing crons (including `base.autovacuum_job`): pausing them during load and parallel-run\n"
      "  windows is an `ir_cron.active` write;\n"
      "- the %d PostgreSQL -> in-scope foreign keys: dropping each constraint when its target table\n"
      "  moves is DDL on the PostgreSQL side.\n"
      % (reports_b, writing_crons, len(into)))
    w("### Plugin findings\n\nNone new from this ticket.\n")
    print("\n".join(out).rstrip())


if __name__ == "__main__":
    main()
