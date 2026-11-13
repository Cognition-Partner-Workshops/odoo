#!/usr/bin/env python3
"""Reconcile the coverage table of BASELINE.md with sample.yaml.

Checks that the table under "## Coverage" of BASELINE.md has exactly one row per
target id of sample.yaml (no missing, unknown or duplicated id), that each row's
status is one of the allowed values, that every test class a row names exists in
odoo/addons/test_backend_neutral/tests/, and that a covered row names at least one
class while a not-covered one names none. Also lists the test classes no row
refers to. Run from the repo root with the system python3 (PyYAML):

    python3 backend_neutral_tests/check_baseline.py
"""
import ast
import re
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MANIFEST = HERE / "sample.yaml"
BASELINE = HERE / "BASELINE.md"
TESTS_DIR = ROOT / "odoo/addons/test_backend_neutral/tests"

STATUSES_WITH_CLASSES = {"covered", "partly covered"}
STATUSES_WITHOUT_CLASSES = {"not covered", "not expressible neutrally"}
ALLOWED_STATUSES = STATUSES_WITH_CLASSES | STATUSES_WITHOUT_CLASSES


def manifest_target_ids():
    data = yaml.safe_load(MANIFEST.read_text())
    return [t["id"] for cat in data["categories"] for t in cat["targets"]]


def test_classes():
    classes = {}
    for path in sorted(TESTS_DIR.glob("test_*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                classes[node.name] = path.relative_to(ROOT).as_posix()
    return classes


def coverage_rows():
    """Yield (target_id, status, [class names], reason) for each row of the coverage table."""
    text = BASELINE.read_text()
    match = re.search(r"^## Coverage.*?$(.*?)(?=^## )", text, re.M | re.S)
    if not match:
        sys.exit("BASELINE.md has no '## Coverage' section")
    rows = []
    for line in match.group(1).splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 4 or cells[0] in ("Target id", "") or set(cells[0]) <= {"-", ":"}:
            continue
        target = cells[0].strip("`")
        classes = re.findall(r"`(Test\w+)`", cells[2])
        rows.append((target, cells[1], classes, cells[3]))
    return rows


def main():
    errors = []
    targets = manifest_target_ids()
    classes = test_classes()
    rows = coverage_rows()
    seen = {}
    for target, status, named, reason in rows:
        if target in seen:
            errors.append(f"{target}: listed twice")
        seen[target] = status
        if target not in targets:
            errors.append(f"{target}: not a sample.yaml target id")
        if status not in ALLOWED_STATUSES:
            errors.append(f"{target}: status {status!r} not in {sorted(ALLOWED_STATUSES)}")
        if status in STATUSES_WITH_CLASSES and not named:
            errors.append(f"{target}: {status} but names no test class")
        if status in STATUSES_WITHOUT_CLASSES and named:
            errors.append(f"{target}: {status} but names test classes {named}")
        if not reason:
            errors.append(f"{target}: empty reason")
        for name in named:
            if name not in classes:
                errors.append(f"{target}: test class {name!r} not found under {TESTS_DIR.relative_to(ROOT)}")
    for target in targets:
        if target not in seen:
            errors.append(f"{target}: missing from the coverage table")

    referenced = {name for _, _, named, _ in rows for name in named}
    print(f"sample.yaml targets: {len(targets)}")
    print(f"BASELINE.md coverage rows: {len(rows)}")
    for status in sorted(ALLOWED_STATUSES):
        print(f"  {status:<27} {sum(1 for s in seen.values() if s == status)}")
    print(f"test classes under tests/: {len(classes)}, referenced by a row: {len(referenced & set(classes))}")
    unreferenced = sorted(set(classes) - referenced)
    if unreferenced:
        print("classes not attached to a target (harness smoke/lint or extra behaviour): " + ", ".join(unreferenced))
    for e in errors:
        print("ERROR", e)
    print("OK: coverage table reconciles with sample.yaml" if not errors else f"{len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
