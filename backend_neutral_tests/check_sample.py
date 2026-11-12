#!/usr/bin/env python3
"""Validate sample.yaml: every cited file exists, every symbol appears in it (whole word),
and `line` (when given) is the line of the first symbol. Run from the repo root:

    python3 backend_neutral_tests/check_sample.py            # validate
    python3 backend_neutral_tests/check_sample.py --render   # validate and regenerate SAMPLE.md
"""
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = Path(__file__).resolve().parent / "sample.yaml"


def check_ref(ref, errors, label):
    path = ROOT / ref["file"]
    if not path.is_file():
        errors.append(f"{label}: missing file {ref['file']}")
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    for sym in ref.get("symbols", []):
        if not re.search(rf"\b{re.escape(sym)}\b", text):
            errors.append(f"{label}: symbol {sym!r} not found in {ref['file']}")
    line = ref.get("line")
    if line and ref.get("symbols"):
        first = ref["symbols"][0]
        if not (0 < line <= len(lines)) or not re.search(rf"\b{re.escape(first)}\b", lines[line - 1]):
            errors.append(f"{label}: {ref['file']}:{line} does not contain {first!r}")


def check_test_ref(ref, errors, label):
    file, _, sym = ref.partition("::")
    path = ROOT / file
    if not path.is_file():
        errors.append(f"{label}: missing test file {file}")
        return
    if sym and not re.search(rf"\b{re.escape(sym)}\b", path.read_text(encoding="utf-8", errors="replace")):
        errors.append(f"{label}: test symbol {sym!r} not found in {file}")


def render(d):
    L = []
    w = L.append
    w("# Backend-neutral ORM test suite: representative code sample\n")
    w(f"Pinned to `{d['repo']}` branch `{d['branch']}`, commit `{d['commit']}`. Machine-readable twin: [`sample.yaml`](sample.yaml); "
      "validate both with `python3 backend_neutral_tests/check_sample.py` (checks every file path, symbol and line below exists; "
      "`--render` regenerates this file from the YAML).\n")
    w("## Purpose\n")
    w("Odoo's ~2,700 test files assume PostgreSQL. This manifest names the models and code paths a **backend-neutral** suite will cover: "
      "tests that assert only on records, field values, ordering and raised exception classes, never on SQL text, query counts, cursors or savepoints, "
      "so they pass on PostgreSQL today and can run unchanged against another backend. It is a sample, not an inventory: the goal is to hit every "
      "*kind* of backend-sensitive behaviour from more than one addon.\n")
    w("## Addon spread\n")
    w(f"- Core: `{'`, `'.join(d['addons']['core'])}`")
    w(f"- Addons (confirmed from the starting hypothesis): `{'`, `'.join(d['addons']['spread'])}`")
    w(f"- Supporting: `{'`, `'.join(d['addons']['supporting'])}` (dependency of stock/sale/point_of_sale; only `product.category` hierarchy is used)\n")
    w("The hypothesis was kept because the static scan confirms it: `account` is the heaviest raw-SQL and constraint user outside core; `mail` and `website` "
      "hold the most lock/upsert and text-search SQL; `stock`, `project`, `hr_holidays`, `sale`, `point_of_sale` each own a different style of SQL-view report "
      "and heavy `read_group`/`child_of` use. Addons that scored high but were not added (`payment`, `mass_mailing`, `l10n_*_edi`) are listed under *Deliberately left out* with the reason.\n")
    w("## Selection criteria (use these to extend the sample)\n")
    for c in d['selection_criteria']:
        w(f"- **{c['id']}** {c['rule']}")
    w("\nTo add a target: pick a symbol that satisfies C1 and C2, add it to `sample.yaml` with `file`, `symbols`, `line`, `existing_tests` and a one-line `neutral_assertion`, "
      "then run the checker with `--render`. Scan patterns per category are recorded in each category's `scan` key.\n")
    w("## Targets by category\n")
    for cat in d['categories']:
        w(f"### {cat['name']}\n")
        w(f"Scan pattern: `{cat['scan']}`" + (f"; scan counts: `{cat['scan_counts']}`" if 'scan_counts' in cat else "") + "\n")
        if cat.get('note'):
            w(cat['note'] + "\n")
        for t in cat['targets']:
            w(f"#### `{t['id']}` - {t['model']} (`{t['addon']}`)\n")
            refs = [f"`{t['file']}:{t['line']}` - `{'`, `'.join(t['symbols'])}`"]
            for a in t.get('also', []):
                refs.append(f"`{a['file']}" + (f":{a['line']}" if a.get('line') else "") + f"` - `{'`, `'.join(a['symbols'])}`")
            w("- Code: " + "; ".join(refs))
            w(f"- Pattern: {t['pattern']}")
            w(f"- Why: {t['reason']}")
            w("- Existing tests: " + ", ".join(f"`{x}`" for x in t['existing_tests']))
            w(f"- Neutral assertion: {t['neutral_assertion']}\n")
    w("## Deliberately left out\n")
    for e in d['excluded']:
        w(f"- **{e['item']}** - {e['why']}")
    w("\n## Open decisions for the next ticket\n")
    for o in d['open_decisions']:
        w(f"- **{o['id']}. {o['question']}** {o['context']} *Proposal:* {o['proposal']}")
    w("\n## How the sample was built\n")
    w("Static grep over `odoo/` and `addons/` `*.py` (excluding `tests/`, `static/`, `node_modules/`) for the scan patterns above, then manual reading of each candidate to confirm C1-C2 "
      "and to find the closest existing test. Counts are file/call-site counts from that scan and differ slightly from the ticket's figures because of pattern choice; "
      "they are inventory evidence, not coverage data.\n")
    (MANIFEST.parent / "SAMPLE.md").write_text("\n".join(L))
    print("rendered SAMPLE.md")


def main():
    data = yaml.safe_load(MANIFEST.read_text())
    if "--render" in sys.argv:
        render(data)
    errors, n_targets, n_refs = [], 0, 0
    for cat in data["categories"]:
        addons = set()
        for t in cat["targets"]:
            n_targets += 1
            addons.add(t["addon"])
            check_ref(t, errors, t["id"])
            n_refs += 1
            for extra in t.get("also", []):
                check_ref(extra, errors, f"{t['id']} (also)")
                n_refs += 1
                addons.add(extra["file"].split("/")[1] if extra["file"].startswith("addons/") else "core")
            for tr in t.get("existing_tests", []):
                check_test_ref(tr, errors, t["id"])
        if len(addons) < 2:
            errors.append(f"category {cat['id']}: targets from only {sorted(addons)}")
        print(f"{cat['id']:<22} targets={len(cat['targets']):<2} addons={sorted(addons)}")
    print(f"\n{n_targets} targets, {n_refs} file/symbol references checked")
    for e in errors:
        print("ERROR", e)
    print("OK" if not errors else f"{len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
