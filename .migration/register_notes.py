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
    ("addons/account/models/account_account.py", "_action_unmerge", 1341):
        (("account_account",), "write"),
    ("odoo/addons/base/wizard/base_partner_merge.py", "_update_foreign_keys_generic", 137):
        (("account_account", "res_partner", "res_partner_bank"), "read"),
    ("odoo/addons/base/wizard/base_partner_merge.py", "_update_foreign_keys_generic", 143):
        (("account_account", "res_partner", "res_partner_bank"), "read"),
    ("odoo/addons/base/wizard/base_partner_merge.py", "_update_foreign_keys_generic", 150):
        (("account_account", "res_partner", "res_partner_bank"), "write"),
    ("odoo/addons/base/wizard/base_partner_merge.py", "_update_foreign_keys_generic", 170):
        (("account_account", "res_partner", "res_partner_bank"), "write"),
    ("odoo/addons/base/wizard/base_partner_merge.py", "_update_foreign_keys_generic", 180):
        (("account_account", "res_partner", "res_partner_bank"), "write"),
    ("odoo/addons/base/wizard/base_partner_merge.py", "_update_foreign_keys_generic", 190):
        (("account_account", "res_partner", "res_partner_bank"), "write"),
}

SITE_TARGETS = {
    ("addons/account/models/account_account.py", "_action_unmerge", 1391): set(),
    ("addons/account/models/account_account.py", "_action_unmerge", 1420): set(),
    ("addons/account/models/account_account.py", "_action_unmerge", 1441): {"account_account"},
    ("addons/account/models/account_account.py", "_action_unmerge", 1472): {"account_account"},
    ("addons/account/models/account_account.py", "_action_unmerge", 1490): set(),
    ("odoo/addons/base/wizard/base_partner_merge.py", "_update_reference_fields_generic", 280):
        set(),
}

SITE_NOTES = {
    ("addons/account/models/account_account.py", "_action_unmerge", 1391):
        "reference columns, resolved at run time",
    ("addons/account/models/account_account.py", "_action_unmerge", 1420):
        "reference columns, resolved at run time",
    ("addons/account/models/account_account.py", "_action_unmerge", 1441):
        "company-dependent JSONB field account.account.code_store (account_account)",
    ("addons/account/models/account_account.py", "_action_unmerge", 1472):
        "company-dependent JSONB field account.account.code_store (account_account)",
    ("addons/account/models/account_account.py", "_action_unmerge", 1490):
        "XMLID remap in ir_model_data; no in-scope table",
    ("odoo/addons/base/wizard/base_partner_merge.py", "_update_reference_fields_generic", 280):
        "ir_default company-dependent fallback; no in-scope table",
}


def is_test(rel):
    parts = rel.split("/")
    return "tests" in parts or parts[-1].startswith("test_")


def model_context(src, installed, model_names):
    """Index model methods, class references, relational fields, and company-dependent fields."""
    refs = collections.defaultdict(set)
    methods = collections.defaultdict(lambda: collections.defaultdict(list))
    field_models = collections.defaultdict(lambda: collections.defaultdict(set))
    company_fields = collections.defaultdict(set)
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
                    for fn in cls.body:
                        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            for model in defined:
                                methods[model][fn.name].append(fn)
                    for st in cls.body:
                        if isinstance(st, ast.Assign):
                            targets, value = st.targets, st.value
                        elif isinstance(st, ast.AnnAssign):
                            targets, value = [st.target], st.value
                        else:
                            continue
                        if not isinstance(value, ast.Call) or not isinstance(
                                value.func, ast.Attribute):
                            continue
                        field_type = value.func.attr
                        keywords = {kw.arg: kw.value for kw in value.keywords if kw.arg}
                        first_arg = value.args[0] if value.args else keywords.get("comodel_name")
                        comodel = first_arg.value if isinstance(first_arg, ast.Constant) \
                            and isinstance(first_arg.value, str) else None
                        if field_type in ("Many2one", "One2many", "Many2many"):
                            for target in targets:
                                if not isinstance(target, ast.Name):
                                    continue
                                for model in defined:
                                    if comodel in model_names:
                                        field_models[model][target.id].add(comodel)
                        company_dependent = keywords.get("company_dependent")
                        if not (isinstance(company_dependent, ast.Constant) and
                                company_dependent.value is True):
                            continue
                        for target in targets:
                            if not isinstance(target, ast.Name):
                                continue
                            for model in defined:
                                company_fields[model].add((target.id, field_type, comodel))
            break
    return refs, methods, field_models, company_fields


def cron_reach(model, methods, field_models, model_names, method):
    """Follow same-model and environment/relational method calls to four edges."""
    def environment_model(expr):
        if isinstance(expr, ast.Attribute):
            return expr.attr == "env"
        return isinstance(expr, ast.Name) and expr.id == "env"

    def assigned_names(node):
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, (ast.AnnAssign, ast.NamedExpr, ast.For, ast.AsyncFor)):
            targets = [node.target]

        def names(target):
            if isinstance(target, ast.Name):
                return [target.id]
            if isinstance(target, (ast.Tuple, ast.List)):
                return [name for element in target.elts for name in names(element)]
            return []

        return [name for target in targets for name in names(target)]

    def expression_models(expr, current_model, aliases):
        if isinstance(expr, ast.Subscript):
            if isinstance(expr.slice, ast.Constant) and \
                    isinstance(expr.slice.value, str) and \
                    environment_model(expr.value) and expr.slice.value in model_names:
                return {expr.slice.value}
            return expression_models(expr.value, current_model, aliases)
        if isinstance(expr, ast.Name):
            if expr.id in ("self", "cls"):
                return {current_model}
            return aliases.get(expr.id, set())
        if isinstance(expr, ast.Attribute):
            targets = field_models.get(current_model, {}).get(expr.attr)
            if targets:
                return set(targets)
            return expression_models(expr.value, current_model, aliases)
        if isinstance(expr, ast.Call):
            if isinstance(expr.func, ast.Attribute):
                return expression_models(expr.func.value, current_model, aliases)
            return expression_models(expr.func, current_model, aliases)
        if isinstance(expr, ast.BinOp):
            return (expression_models(expr.left, current_model, aliases) |
                    expression_models(expr.right, current_model, aliases))
        if isinstance(expr, ast.IfExp):
            return (expression_models(expr.body, current_model, aliases) |
                    expression_models(expr.orelse, current_model, aliases))
        return set()

    def same_model_expression(expr, current_model):
        if isinstance(expr, ast.Name):
            return expr.id in ("self", "cls")
        if isinstance(expr, ast.Attribute):
            if expr.attr in field_models.get(current_model, {}):
                return False
            return same_model_expression(expr.value, current_model)
        if isinstance(expr, ast.Call):
            if isinstance(expr.func, ast.Name) and expr.func.id == "super":
                return True
            if isinstance(expr.func, ast.Attribute):
                return same_model_expression(expr.func.value, current_model)
        return False

    def call_aliases(target, called, call, current_model, aliases):
        definitions = methods.get(target, {}).get(called, ())
        if not definitions:
            return {}
        parameters = definitions[0].args.posonlyargs + definitions[0].args.args
        if parameters and parameters[0].arg in ("self", "cls"):
            parameters = parameters[1:]
        result = collections.defaultdict(set)
        for parameter, argument in zip(parameters, call.args):
            result[parameter.arg].update(
                expression_models(argument, current_model, aliases))
        parameters_by_name = {parameter.arg for parameter in parameters}
        for keyword in call.keywords:
            if keyword.arg in parameters_by_name:
                result[keyword.arg].update(
                    expression_models(keyword.value, current_model, aliases))
        return dict(result)

    reached_models = {model}
    reached_methods = set()
    todo = collections.deque([(model, method, 0, {})])
    seen = set()
    while todo:
        current_model, name, depth, initial_aliases = todo.popleft()
        pair = (current_model, name)
        alias_key = tuple(sorted(
            (key, tuple(sorted(value))) for key, value in initial_aliases.items()))
        context = pair + (alias_key,)
        if context in seen or depth > 4:
            continue
        seen.add(context)
        reached_methods.add(pair)
        definitions = methods.get(current_model, {}).get(name, ())
        for fn in definitions:
            aliases = collections.defaultdict(set)
            for alias, targets in initial_aliases.items():
                aliases[alias].update(targets)
            for _ in range(4):
                for node in ast.walk(fn):
                    names = assigned_names(node)
                    if not names:
                        continue
                    value = node.iter if isinstance(node, (ast.For, ast.AsyncFor)) else node.value
                    targets = expression_models(value, current_model, aliases)
                    for assigned_name in names:
                        aliases[assigned_name].update(targets)
            for node in ast.walk(fn):
                if isinstance(node, ast.Subscript):
                    reached_models.update(expression_models(node, current_model, aliases))
                if not isinstance(node, ast.Call) or \
                        not isinstance(node.func, ast.Attribute):
                    continue
                called = node.func.attr
                receiver = node.func.value
                targets = expression_models(receiver, current_model, aliases)
                if called in methods.get(current_model, {}) and \
                        same_model_expression(receiver, current_model):
                    targets.add(current_model)
                for target in targets:
                    reached_models.add(target)
                    if called in methods.get(target, {}) and depth < 4:
                        todo.append((
                            target, called, depth + 1,
                            call_aliases(target, called, node, current_model, aliases)))
    return reached_models, reached_methods


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
    class_refs, methods, field_models, company_fields = model_context(
        a.src, db["installed_modules"], model_names)
    merge_models = {"account.account", "res.partner", "res.partner.bank"}

    def fields_for_comodels(comodels):
        return sorted(
            (model, name, field_type, comodel)
            for model, fields in company_fields.items()
            for name, field_type, comodel in fields
            if field_type == "Many2one" and comodel in comodels)

    def fields_for_models(models):
        return sorted(
            (model, name, field_type, comodel)
            for model in models
            for name, field_type, comodel in company_fields.get(model, ()))

    def tables_for_fields(fields):
        return {table_of[model] for model, _name, _type, _comodel in fields
                if table_of.get(model) in in_scope}

    def describe_fields(fields):
        grouped = collections.defaultdict(set)
        for model, name, _field_type, _comodel in fields:
            grouped[model].add(name)
        parts = []
        for model, names in sorted(grouped.items()):
            table = table_of.get(model, "no table")
            outside = ", out of scope" if table not in in_scope else ""
            parts.append("%s (%s%s): %s" % (
                model, table, outside, ", ".join(sorted(names))))
        return "; ".join(parts) or "no statically declared company-dependent fields"

    account_company_fields = fields_for_comodels({"account.account"})
    merge_company_fields = fields_for_comodels(merge_models)
    merged_record_fields = fields_for_models(merge_models)
    site_targets = dict(SITE_TARGETS)
    site_targets[("addons/account/models/account_account.py", "_action_unmerge", 1362)] = \
        tables_for_fields(account_company_fields)
    site_targets[("odoo/addons/base/wizard/base_partner_merge.py",
                  "_update_reference_fields_generic", 258)] = \
        tables_for_fields(merge_company_fields)
    site_targets[("odoo/addons/base/wizard/base_partner_merge.py",
                  "_update_reference_fields_generic", 307)] = \
        tables_for_fields(merged_record_fields)
    site_notes = dict(SITE_NOTES)
    site_notes[("addons/account/models/account_account.py", "_action_unmerge", 1362)] = (
        "company-dependent Many2one JSONB values to account.account: %s; no catalog FKs"
        % describe_fields(account_company_fields))
    site_notes[("odoo/addons/base/wizard/base_partner_merge.py",
                "_update_reference_fields_generic", 258)] = (
        "company-dependent Many2one JSONB values to merged models: %s; no catalog FKs"
        % describe_fields(merge_company_fields))
    site_notes[("odoo/addons/base/wizard/base_partner_merge.py",
                "_update_reference_fields_generic", 307)] = (
        "company-dependent fields on merged records: %s"
        % describe_fields(merged_record_fields))
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
        if (s["file"], s["function"]) == (
                "odoo/addons/base/wizard/base_partner_merge.py",
                "_update_foreign_keys_generic"):
            return "A", "generic core FK fan-out"
        if (s["file"], s["function"]) == (
                "odoo/addons/base/wizard/base_partner_merge.py",
                "_update_reference_fields_generic"):
            return "A", "generic core merge update"
        if (s["file"], s["function"]) == (
                "addons/analytic/models/analytic_mixin.py", "_read_group_groupby"):
            return "B", ("generic code; table resolved per model (%d in-scope tables); B since "
                         "UNT14-36: unit-owned (storage worker reclassification)" % len(s["in_scope"]))
        if s["module"] in scope_mods:
            return "B", ""
        if s["dynamic"] or s["unresolved"] or s["orm_query"]:
            return "A", "generic code; table resolved per model (%d in-scope tables)" % len(
                s["in_scope"])
        return "B", "non-scope module names in-scope tables"

    rows = {"write": [], "read": []}
    other = collections.Counter()
    unlisted_notes = []
    for s in scan["sites"]:
        site_key = (s["file"], s["function"], s["line"])
        fanout = FANOUT.get(site_key)
        if fanout:
            fanout_models, fanout_op = fanout
            fanout_tables = set().union(*(fk_fanout[m] for m in fanout_models))
            s["in_scope"] = {t: fanout_op for t in sorted(fanout_tables)}
            s["fanout_note"] = "; ".join(
                "FK fan-out of %s: %d in-scope tables (catalog FKs; Reference/res_id columns "
                "not included)" % (m, len(fk_fanout[m])) for m in fanout_models)
        if site_key in site_targets:
            s["in_scope"] = {
                t: "write" for t in sorted(site_targets[site_key] & in_scope)
            }
            s["site_note"] = site_notes[site_key]
        d, why = disp_site(s)
        kind = s["kind"]
        if d == "C" and kind != "upgrade_script":
            other[kind] += 1
            if s.get("site_note"):
                unlisted_notes.append("`%s:%d`: %s" % (
                    s["file"], s["line"], s["site_note"]))
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
      " in-scope table are counted, not listed: %s%s.\n" % (
          len(db["installed_modules"]),
          ", ".join("%d %s" % (n, k) for k, n in sorted(other.items())),
          ("; " + "; ".join(unlisted_notes)) if unlisted_notes else ""))

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
            if s.get("site_note"):
                note = (note + "; " if note else "") + s["site_note"]
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
      "class-level-only possible (2-hop; count + up to 6 names) | note |")
    w("|---|---|---|---|---|---|---|---|---|")
    sites_by_fn = collections.defaultdict(list)
    for s in scan["sites"]:
        sites_by_fn[(s["model"], s["function"])].append(s)
    reaching_crons = set()
    for c in db["crons"]:
        meth = re.findall(r"model\.(\w+)\(", c["code"] or "")
        direct_reach = set()
        reached_methods = set()
        for mt in meth:
            reached_models, call_methods = cron_reach(
                c["model"], methods, field_models, model_names, mt)
            reached_methods.update(call_methods)
            direct_reach.update(
                table_of[model] for model in reached_models
                if table_of.get(model) in in_scope)
        class_models = set(class_refs.get(c["model"], ()))
        two_hop_models = class_models | {
            target for model in class_models for target in class_refs.get(model, ())}
        class_reach = {table_of[m] for m in two_hop_models if table_of.get(m) in in_scope}
        class_only = class_reach - direct_reach
        raw = [s for model, method in reached_methods
               for s in sites_by_fn.get((model, method), []) if s["in_scope"]]
        raw_write = any(s["write"] for s in raw)
        if c["xmlid"] == "base.autovacuum_job":
            d, note = "A", "vacuums every transient/in-scope model with _gc_* hooks; pause it"
            op = "write"
            reaching_crons.add(c["xmlid"])
        elif raw:
            d, note = "B", "reaches raw SQL"
            op = "write" if raw_write else "read"
            reaching_crons.add(c["xmlid"])
        elif direct_reach:
            d, note = "A", "ORM writes; pause during load windows"
            op = "write"
            reaching_crons.add(c["xmlid"])
        elif class_only:
            d, note = "A", "possible indirect reach (class-level, unproven): review before load"
            op = "possible"
        else:
            d, note = "C", ""
            op = "read"
        counts[("cron", op, d)] += 1
        class_names = sorted(class_only)
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
    possible_crons = sum(counts[("cron", "possible", d)] for d in ("A", "B", "C"))
    w("### Writes outside odoo_unt13\n")
    w("None during this ticket: `odoo_src` was only read (role `odoo_ro`, read-only session) and the\n"
      "`_table_sql` render ran on a throwaway clone `odoo_reg_probe`. Later units will need writes to\n"
      "the application's PostgreSQL (never `odoo_src`, never Atlas), each needing a plan decision:\n"
      "- the %d **B** reports/views above: their PostgreSQL view or `_table_sql` stops seeing rows once\n"
      "  its tables move, so the owning unit re-points or rebuilds them;\n"
      "- the %d crons that reach in-scope tables (including `base.autovacuum_job`): pausing direct\n"
      "  writers during load and parallel-run windows is an `ir_cron.active` write;\n"
      "- plus %d with only possible indirect reach, to review before load;\n"
      "- the %d PostgreSQL -> in-scope foreign keys: dropping each constraint when its target table\n"
      "  moves is DDL on the PostgreSQL side.\n"
      % (reports_b, len(reaching_crons), possible_crons, len(into)))
    w("### Plugin findings\n\nNone new from this ticket.\n")
    print("\n".join(out).rstrip())


if __name__ == "__main__":
    main()
