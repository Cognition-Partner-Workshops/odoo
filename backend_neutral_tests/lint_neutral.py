#!/usr/bin/env python3
"""Lint for backend-neutral tests (rules BN001-BN011, see CONTRACT.md section 6).

    python3 backend_neutral_tests/lint_neutral.py <file-or-dir>...   # exit 1 on any finding
    python3 backend_neutral_tests/lint_neutral.py --self-test         # check the examples in CONTRACT.md

Pure stdlib `ast`; does not import Odoo. Suppress one line with `# neutral: allow BNxxx`.
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONTRACT = HERE / "CONTRACT.md"

FORBIDDEN_MODULES = ("psycopg2", "odoo.sql_db", "odoo.tools.sql")
BACKEND_EXC_ATTRS = {"pgcode", "pgerror", "diag"}
EXECUTE_CALLS = {"execute", "executemany", "execute_values", "execute_query", "execute_query_dict",
                 "fetchone", "fetchall", "fetchmany", "dictfetchall", "dictfetchone", "dictfetchmany"}
TRANSACTION_CALLS = {"savepoint", "cursor", "registry_test_mode", "enter_registry_test_mode"}
CURSOR_ONLY_CALLS = {"commit", "rollback", "flush"}   # forbidden on a cursor, allowed on a harness Transaction
QUERY_ASSERT_CALLS = {"assertQueryCount", "assertQueries", "_patchExecute", "warmup", "profile"}
QUERY_BUILDER_CALLS = {"SQL", "Query", "_as_query", "_where_calc", "_flush_search"}
CURSOR_ATTRS = {"cr", "_cr", "registry"}
SCHEMA_ATTRS = {"_table", "_table_sql", "_table_objects", "_auto", "_sql_constraints"}
# Upper-case keywords (how SQL is written in Odoo) match on shape alone; lower/mixed case must also
# name a table-like identifier so prose such as "Select a product from the list" is not flagged.
SQL_TEXT_UPPER = re.compile(
    r"\bSELECT\b.*\bFROM\s+\S|\bINSERT\s+INTO\b|\bUPDATE\s+\S+\s+SET\b|\bDELETE\s+FROM\b"
    r"|\bFOR\s+(NO\s+KEY\s+)?UPDATE\b|\bSAVEPOINT\b|\bnextval\(|\bON\s+CONFLICT\b|\bWITH\s+RECURSIVE\b",
    re.DOTALL,
)
SQL_TEXT_ANYCASE = re.compile(
    r"\bselect\b.*\bfrom\s+(\"\w+\"|\w+_\w+|\w+\s+\w+\s+(where|join|left|inner|group|order|limit)\b)"
    r"|\binsert\s+into\s+(\"\w+\"|\w+_\w+)|\bupdate\s+(\"\w+\"|\w+_\w+)\s+set\b|\bdelete\s+from\s+(\"\w+\"|\w+_\w+)"
    r"|\bfor\s+(no\s+key\s+)?update\s+(nowait|skip|of)\b|\bsavepoint\s+\w+\s*;|\bnextval\(|\bon\s+conflict\s*\(|\bwith\s+recursive\s+\w+",
    re.IGNORECASE | re.DOTALL,
)
BACKEND_WORDS = re.compile(r"postgres|psycopg|mongo", re.IGNORECASE)
ALLOW = re.compile(r"#\s*neutral:\s*allow\s+(BN\d{3}(?:\s*,?\s*BN\d{3})*)")


def _dotted(node: ast.AST) -> str | None:
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    parts.append(node.id)
    return ".".join(reversed(parts))


def _is_cursor(node: ast.AST) -> bool:
    """`cr`, `self.cr`, `env.cr`, `self.env.cr`, `registry.cursor()`, ... but not `tx` / `t0`."""
    if isinstance(node, ast.Name):
        return node.id in {"cr", "_cr"}
    if isinstance(node, ast.Attribute):
        return node.attr in {"cr", "_cr"}
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        return node.func.attr == "cursor"
    return False


def _is_id_operand(node: ast.AST) -> bool:
    if isinstance(node, ast.Attribute) and node.attr == "id":
        return True
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute) and node.value.attr == "ids":
        return True
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"max", "min"}:
        return any(isinstance(a, ast.Attribute) and a.attr == "ids" for a in node.args)
    return False


class Checker(ast.NodeVisitor):
    def __init__(self, path: str, source: str):
        self.path = path
        self.lines = source.splitlines()
        self.findings: list[tuple[int, str, str]] = []

    def report(self, node: ast.AST, code: str, message: str) -> None:
        line = getattr(node, "lineno", 0)
        src = self.lines[line - 1] if 0 < line <= len(self.lines) else ""
        m = ALLOW.search(src)
        if m and code in m.group(1):
            return
        self.findings.append((line, code, message))

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.name.startswith(FORBIDDEN_MODULES):
                self.report(node, "BN001", f"import of backend module {alias.name!r}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            for alias in node.names:
                if node.module.startswith(FORBIDDEN_MODULES) or f"{node.module}.{alias.name}".startswith(FORBIDDEN_MODULES):
                    self.report(node, "BN001", f"import of backend module {node.module}.{alias.name!s}")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        dotted = _dotted(node)
        if dotted and dotted.startswith(FORBIDDEN_MODULES):
            self.report(node, "BN001", f"backend module reference {dotted}")
        if node.attr in BACKEND_EXC_ATTRS:
            self.report(node, "BN001", f"backend exception attribute .{node.attr}")
        if node.attr in CURSOR_ATTRS:
            self.report(node, "BN006", f"cursor/registry access .{node.attr}")
        if node.attr in SCHEMA_ATTRS:
            self.report(node, "BN008", f"schema internal .{node.attr}")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else func.id if isinstance(func, ast.Name) else None
        if name in EXECUTE_CALLS:
            self.report(node, "BN002", f"raw SQL execution .{name}()")
        if name in TRANSACTION_CALLS:
            self.report(node, "BN003", f"transaction control .{name}()")
        if name in CURSOR_ONLY_CALLS and isinstance(func, ast.Attribute) and _is_cursor(func.value):
            self.report(node, "BN003", f"cursor .{name}(); use the harness Transaction or env.flush_all()")
        if name in QUERY_ASSERT_CALLS:
            self.report(node, "BN004", f"query-count/text assertion {name}()")
        if name in QUERY_BUILDER_CALLS:
            self.report(node, "BN005", f"SQL/Query construction {name}()")
        if name == "mute_logger":
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and arg.value.startswith("odoo.sql_db"):
                    self.report(node, "BN007", "muting the backend logger; use assertIntegrityError()/assertConcurrencyError()")
        if name == "init" and isinstance(func, ast.Attribute) and not node.args and not node.keywords:
            self.report(node, "BN008", "model.init() (SQL view creation)")
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str):
            if SQL_TEXT_UPPER.search(node.value) or SQL_TEXT_ANYCASE.search(node.value):
                self.report(node, "BN009", "SQL text in a string literal")
            if BACKEND_WORDS.search(node.value):
                self.report(node, "BN011", "backend name in a string literal (review: no backend branching)")

    def visit_BinOp(self, node: ast.BinOp) -> None:
        if isinstance(node.op, ast.Add | ast.Sub) and (_is_id_operand(node.left) or _is_id_operand(node.right)):
            self.report(node, "BN010", "arithmetic on record ids")
        self.generic_visit(node)


def lint_source(source: str, path: str = "<string>") -> list[tuple[int, str, str]]:
    checker = Checker(path, source)
    checker.visit(ast.parse(source, filename=path))
    return sorted(checker.findings)


def iter_files(paths: list[str]):
    for p in paths:
        path = Path(p)
        if path.is_dir():
            yield from sorted(path.rglob("*.py"))
        else:
            yield path


def self_test(contract: Path) -> int:
    text = contract.read_text(encoding="utf-8")
    blocks = re.findall(r"```python (compliant|non-compliant)((?: BN\d{3})*)\n(.*?)```", text, re.DOTALL)
    failures = 0
    for i, (kind, codes, code) in enumerate(blocks, 1):
        expected = set(codes.split())
        got = {c for _, c, _ in lint_source(code, f"CONTRACT.md#block{i}")}
        if kind == "compliant" and got:
            failures += 1
            print(f"block {i} ({kind}): expected no findings, got {sorted(got)}")
        elif kind == "non-compliant" and (not got or not expected <= got):
            failures += 1
            print(f"block {i} ({kind}): expected {sorted(expected)}, got {sorted(got)}")
    print(f"{len(blocks)} example blocks checked, {failures} failures")
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="*", help="files or directories to lint")
    parser.add_argument("--self-test", action="store_true", help="lint the examples in CONTRACT.md")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test(CONTRACT)
    if not args.paths:
        parser.error("give at least one path or --self-test")
    total = 0
    for path in iter_files(args.paths):
        for line, code, message in lint_source(path.read_text(encoding="utf-8"), str(path)):
            print(f"{path}:{line}: {code} {message}")
            total += 1
    print(f"{total} finding(s)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
