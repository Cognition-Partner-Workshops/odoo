"""AST scan for the s2.3 dependency register (no database access).

Inputs: the source tree at SOURCE_COMMIT, .migration/table_buckets.json and the JSON written by
register_db.py (installed modules, crons, views, triggers, foreign keys). Walks every non-test
.py file of the installed modules and of the core (odoo/ outside odoo/addons) and records:
  sql      cursor calls (execute, execute_values, executemany, copy_*, mogrify),
           env.execute_query / execute_query_dict, psycopg2.extras.execute_values
  helper   odoo.tools.sql helpers that touch a table (create_index, column_exists, ...)
  fragment SQL(...) objects built outside a cursor call (search/order/compute overrides)
  report   _auto = False models: _table_query / _table_sql / init() views
Each site gets its table set: literal table names in its SQL text, plus self._table / env[m]._table
resolved through the class's model (an abstract model resolves to every installed model that
inherits it). Writes register.json (one entry per site) for the NOTES.md tables.
  python .migration/register_scan.py --src ../odoo-unt13-src --db db.json --out register.json
"""
import argparse
import ast
import json
import pathlib
import re

CURSOR_CALLS = {"execute", "execute_values", "executemany", "copy_expert", "copy_from",
                "copy_to", "mogrify"}
ENV_CALLS = {"execute_query", "execute_query_dict"}
TABLE_HELPERS = {"table_exists", "table_kind", "create_model_table", "table_columns",
                 "column_exists", "create_column", "rename_column", "convert_column",
                 "convert_column_translatable", "_convert_column", "drop_depending_views",
                 "get_depending_views", "set_not_null", "drop_not_null",
                 "constraint_definition", "add_constraint", "drop_constraint",
                 "add_foreign_key", "get_foreign_keys", "fix_foreign_key", "index_exists",
                 "check_index_exist", "index_definition", "create_index", "add_index",
                 "drop_index", "drop_view_if_exists", "increment_fields_skiplock",
                 "existing_tables"}
WRITE_HELPERS = {"create_model_table", "create_column", "rename_column", "convert_column",
                 "convert_column_translatable", "_convert_column", "drop_depending_views",
                 "set_not_null", "drop_not_null", "add_constraint", "drop_constraint",
                 "add_foreign_key", "fix_foreign_key", "create_index", "add_index",
                 "drop_index", "drop_view_if_exists", "increment_fields_skiplock"}
CURSOR_RE = re.compile(r"(^|\.)(_?cr\w*|cursor|_cursor)$")
WRITE_TARGET_RE = re.compile(
    r"\b(?:insert\s+into|update(?:\s+only)?|delete\s+from|truncate(?:\s+table)?|"
    r"alter\s+table(?:\s+only)?(?:\s+if\s+exists)?|copy|index\s+(?:if\s+not\s+exists\s+)?"
    r"\w*\s*on(?:\s+only)?)\s+\"?([a-z_][a-z0-9_]*)\"?")
WRITE_VERB_RE = re.compile(r"\b(insert|update|delete|truncate|alter|create|drop|copy)\b")
LOCK_RE = re.compile(r"\bfor\s+(no\s+key\s+)?update\b|\bon\s+conflict\b.*?\bdo\s+update\b",
                     re.S)
VIEW_DDL_RE = re.compile(r"\bcreate\s+(or\s+replace\s+)?(materialized\s+)?view\b")
IDENT_RE = re.compile(r"[a-z_][a-z0-9_]*")


def strings(node):
    out = []
    for n in ast.walk(node):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            out.append(n.value)
    return out


def literal(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, (ast.List, ast.Tuple)):
        return [e.value for e in node.elts if isinstance(e, ast.Constant)]
    return []


class ModelIndex:
    """_name/_inherit/_table/_auto of every class in the installed modules."""

    def __init__(self):
        self.classes = []          # (module, file, ClassDef, names, inherits, table, auto)
        self.children = {}         # model -> models inheriting it

    def add(self, module, rel, cls):
        attrs = {}
        for st in cls.body:
            if isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(
                    st.targets[0], ast.Name):
                attrs[st.targets[0].id] = st.value
        name = literal(attrs["_name"]) if "_name" in attrs else []
        inherit = literal(attrs["_inherit"]) if "_inherit" in attrs else []
        if not name and not inherit:
            return None
        model = name[0] if name else inherit[0]
        table = literal(attrs["_table"])[0] if "_table" in attrs and literal(
            attrs["_table"]) else model.replace(".", "_")
        auto = attrs.get("_auto")
        auto = not (isinstance(auto, ast.Constant) and auto.value is False)
        abstract = any(isinstance(b, ast.Attribute) and b.attr == "AbstractModel"
                       for b in cls.bases)
        transient = any(isinstance(b, ast.Attribute) and b.attr == "TransientModel"
                        for b in cls.bases)
        rec = dict(module=module, file=rel, model=model, table=table, auto=auto,
                   abstract=abstract, transient=transient, inherit=inherit, cls=cls)
        self.classes.append(rec)
        for parent in inherit:
            if parent != model:
                self.children.setdefault(parent, set()).add(model)
        return rec

    def finish(self):
        self.table_of, self.abstract = {}, set()
        for r in self.classes:
            if r["model"] not in self.table_of or r["file"].endswith(
                    "/" + r["model"].replace(".", "_") + ".py"):
                self.table_of.setdefault(r["model"], r["table"])
            if r["abstract"] and r["inherit"] in ([], [r["model"]]):
                self.abstract.add(r["model"])
        for r in self.classes:     # _table declared on any class of the model wins
            if r["table"] != r["model"].replace(".", "_"):
                self.table_of[r["model"]] = r["table"]

    def concrete_tables(self, model, seen=None):
        """Tables of `model`, or of every stored model inheriting it if it is abstract."""
        seen = seen if seen is not None else set()
        if model in seen:
            return set()
        seen.add(model)
        if model not in self.abstract:
            return {self.table_of.get(model, model.replace(".", "_"))}
        out = set()
        for child in self.children.get(model, ()):
            out |= self.concrete_tables(child, seen)
        return out


def module_files(src, installed):
    for m in installed:
        for base in (src / "addons" / m, src / "odoo" / "addons" / m):
            if base.is_dir():
                for f in sorted(base.rglob("*.py")):
                    yield m, f
                break
    core = src / "odoo"
    for f in sorted(core.rglob("*.py")):
        rel = f.relative_to(core).parts
        if rel[0] != "addons":
            yield "(core)", f


def is_test(rel):
    parts = rel.split("/")
    return "tests" in parts or parts[-1].startswith("test_")


def site_kind_of(rel):
    parts = rel.split("/")
    if "migrations" in parts or "upgrades" in parts:
        return "upgrade_script"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=pathlib.Path, required=True)
    ap.add_argument("--db", type=pathlib.Path, required=True)
    ap.add_argument("--buckets", type=pathlib.Path,
                    default=pathlib.Path(__file__).resolve().parent / "table_buckets.json")
    ap.add_argument("--out", type=pathlib.Path, required=True)
    a = ap.parse_args()
    db = json.loads(a.db.read_text())
    buckets = json.loads(a.buckets.read_text())["tables"]
    in_scope = {t for t, v in buckets.items() if v["bucket"] == "in_scope"}
    known = set(buckets) | {v["name"] for v in db["views"]}
    installed = db["installed_modules"]

    parsed, index = [], ModelIndex()
    for module, f in module_files(a.src, installed):
        rel = str(f.relative_to(a.src))
        if is_test(rel):
            continue
        tree = ast.parse(f.read_text(), rel)
        imported = {al.asname or al.name for n in ast.walk(tree)
                    if isinstance(n, ast.ImportFrom) and n.module and (
                        n.module.endswith("tools.sql") or n.module.endswith("tools")
                        or n.module == "psycopg2.extras") for al in n.names}
        class_recs = {}
        for n in ast.walk(tree):
            if isinstance(n, ast.ClassDef):
                rec = index.add(module, rel, n)
                if rec:
                    class_recs[id(n)] = rec
        parsed.append((module, rel, tree, imported, class_recs))
    index.finish()

    sites = []
    for module, rel, tree, imported, class_recs in parsed:
        def visit(node, cls, func, in_call):
            for child in ast.iter_child_nodes(node):
                c_cls, c_func, c_in = cls, func, in_call
                if isinstance(child, ast.ClassDef):
                    c_cls = class_recs.get(id(child))
                elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    c_func = child
                elif isinstance(child, ast.Call):
                    kind = classify(child, imported)
                    if kind:
                        record(kind, child, cls, func)
                        c_in = True
                    elif not in_call and is_sql_ctor(child):
                        record("fragment", child, cls, func)
                        c_in = True
                visit(child, c_cls, c_func, c_in)

        def record(kind, call, cls, func):
            text = " ".join(strings(call))
            # names passed to the call: pull in their assignments in the same function
            if func is not None:
                names = {n.id for n in ast.walk(call) if isinstance(n, ast.Name)}
                for st in ast.walk(func):
                    if isinstance(st, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
                        tgts = st.targets if isinstance(st, ast.Assign) else [st.target]
                        if any(isinstance(t, ast.Name) and t.id in names for t in tgts):
                            text += " " + " ".join(strings(st.value))
            low = LOCK_RE.sub(" ", text.lower())
            literal_tables = {t for t in IDENT_RE.findall(low) if t in known}
            dyn, via_env = set(), set()
            for n in ast.walk(call):
                if isinstance(n, ast.Attribute) and n.attr in ("_table", "_name"):
                    owner = n.value
                    if isinstance(owner, ast.Subscript) and isinstance(
                            owner.slice, ast.Constant):     # env['x.y']._table
                        dyn |= index.concrete_tables(owner.slice.value)
                    elif cls is not None:
                        dyn |= index.concrete_tables(cls["model"])
                    else:
                        dyn.add("*")
            fname = call.func.attr if isinstance(call.func, ast.Attribute) else getattr(
                call.func, "id", "")
            if kind == "helper":
                write = fname in WRITE_HELPERS
                if not literal_tables and not dyn:
                    dyn.add("*")
            else:
                write = bool(WRITE_VERB_RE.search(low))
            for n in ast.walk(func if func is not None else call):
                if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant) and \
                        isinstance(n.slice.value, str) and ast.unparse(n.value).endswith(
                            "env") and n.slice.value in index.table_of:
                    via_env.add(n.slice.value)
            orm_query = False
            if not literal_tables and not dyn:
                # SQL built from ORM Query/TableSQL objects (_search, _as_query, _field_to_sql):
                # the tables are the function's env[...] models, else the class's model
                models = via_env or ({cls["model"]} if cls else set())
                for m in models:
                    dyn |= index.concrete_tables(m)
                orm_query = bool(dyn)
            targets = set(WRITE_TARGET_RE.findall(low)) & known
            if VIEW_DDL_RE.search(low):
                write, targets = False, set()
            tables = literal_tables | (dyn - {"*"})
            ops = {}
            for t in tables:
                ops[t] = "write" if write and (t in targets or t in dyn or not targets) \
                    else "read"
            sites.append(dict(
                kind=site_kind_of(rel) or kind, call=fname, module=module, file=rel,
                line=call.lineno, end_line=call.end_lineno,
                model=cls["model"] if cls else None,
                function=func.name if func is not None else None,
                write=write, dynamic="*" in dyn or bool(dyn - literal_tables),
                unresolved="*" in dyn, orm_query=orm_query,
                view_ddl=bool(VIEW_DDL_RE.search(low)),
                tables={t: ops[t] for t in sorted(tables)},
                in_scope={t: ops[t] for t in sorted(tables & in_scope)},
                sql=re.sub(r"\s+", " ", text)[:300]))

        def classify(call, imported):
            f = call.func
            if isinstance(f, ast.Attribute):
                recv = ast.unparse(f.value)
                if f.attr in CURSOR_CALLS and CURSOR_RE.search(recv):
                    return "sql"
                if f.attr in ENV_CALLS:
                    return "sql"
                if f.attr in TABLE_HELPERS and recv.split(".")[-1] in ("sql", "tools"):
                    return "helper"
                if f.attr == "execute_values" and recv.endswith("extras"):
                    return "sql"
            elif isinstance(f, ast.Name) and f.id in imported:
                if f.id in TABLE_HELPERS:
                    return "helper"
                if f.id == "execute_values":
                    return "sql"
            return None

        def is_sql_ctor(call):
            f = call.func
            return (isinstance(f, ast.Name) and f.id == "SQL" and call.args and isinstance(
                call.args[0], (ast.Constant, ast.JoinedStr)))

        visit(tree, None, None, False)

    reports = []
    for r in index.classes:
        if r["auto"]:
            continue
        cls = r["cls"]
        names = {st.name for st in cls.body if isinstance(st, (ast.FunctionDef,
                                                                ast.AsyncFunctionDef))}
        names |= {st.targets[0].id for st in cls.body if isinstance(st, ast.Assign)
                  and isinstance(st.targets[0], ast.Name)}
        if "_table_query" in names or "_table_sql" in names:
            how = "_table_query" if "_table_query" in names else "_table_sql"
        elif "init" in names:
            how = "init_view"
        else:
            continue
        low = " ".join(strings(cls)).lower()
        tables = {t for t in IDENT_RE.findall(low) if t in known}
        for n in ast.walk(cls):
            if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant) and \
                    isinstance(n.slice.value, str) and "." in n.slice.value and \
                    ast.unparse(n.value).endswith("env"):
                tables |= index.concrete_tables(n.slice.value) & set(buckets)
        tables.discard(r["table"])
        reports.append(dict(model=r["model"], view=r["table"], module=r["module"],
                            file=r["file"], line=cls.lineno, how=how,
                            reads=sorted(tables), in_scope=sorted(tables & in_scope)))

    models = {}
    for r in index.classes:
        models.setdefault(r["model"], {"table": index.table_of[r["model"]],
                                       "abstract": r["model"] in index.abstract,
                                       "modules": set()})["modules"].add(r["module"])
    for v in models.values():
        v["modules"] = sorted(v["modules"])
    a.out.write_text(json.dumps(dict(sites=sites, reports=reports, models=models),
                                indent=1, sort_keys=True))
    print(len(sites), "sites,", len(reports), "reports,", len(models), "models")


if __name__ == "__main__":
    main()
