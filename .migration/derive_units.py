#!/usr/bin/env python3
"""s3.3-unit-derivation (board UNT12): derive .migration/units.json from the signed-off
map-draft-2 spec, the fixture manifest, the access scan and the s2.3 dependency register.

    python3 .migration/derive_units.py            # writes .migration/units.json
    python3 .migration/derive_units.py --check    # exit 1 if the committed file differs

Every number and disposition in units.json is read from a committed artifact; the only
hand-authored input is UNITS below (which collections form one coherent code slice) and
the two cited lifecycle exceptions in FORWARD_EXCEPTIONS.
"""
from __future__ import annotations

import argparse
import ast
import collections
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIG = ROOT / ".migration"
OUT = MIG / "units.json"

SCOPE_MODULES = ["uom", "product", "sale", "purchase", "stock", "account"]
BRIDGE_MODULES = ["account_edi_ubl_cii", "account_qr_code_sepa", "purchase_edi_ubl_bis3",
                  "purchase_stock", "sale_edi_ubl", "sale_purchase", "sale_purchase_stock",
                  "sale_stock", "stock_account"]
MODULES = SCOPE_MODULES + BRIDGE_MODULES

# The judgment: one coherent code slice per unit, named by the Odoo models it owns.
UNITS = [
    ("uom-packaging", "Units of measure and package types",
     "addons/uom + the stock extension of uom.uom (package_type_id) + stock.package.type",
     ["uomUom", "stockPackageType"]),
    ("stock-reference", "Stock reference data (storage categories, scrap reason tags, return reasons)",
     "addons/stock reference models with no outbound reference; sale_stock return.reason",
     ["stockStorageCategory", "stockScrapReasonTag", "returnReason"]),
    ("product-taxonomy", "Product taxonomy (categories, removal strategies, tags, documents, base units)",
     "addons/product category/tag/document models + stock product.removal",
     ["productCategory", "productRemoval", "productTag", "productDocument", "productBaseUnit"]),
    ("product-attributes", "Product attributes and their values",
     "addons/product product.attribute (+ embedded product.attribute.value)",
     ["productAttribute"]),
    ("account-settings", "Accounting settings (payment terms, incoterms, cash rounding, journal groups, lock exceptions, report definitions)",
     "addons/account configuration leaves nothing in the chart depends on",
     ["accountPaymentTerm", "accountIncoterms", "accountCashRounding", "accountJournalGroup", "accountLockException",
      "accountReport", "accountReportExpression", "accountReportExternalValue"]),
    ("account-chart", "Chart of accounts, tags, taxes, fiscal positions",
     "addons/account chart models: account, account tag, tax, tax group, tax repartition line, fiscal position",
     ["accountAccount", "accountAccountTag", "accountTax", "accountTaxGroup", "accountTaxRepartitionLine",
      "accountFiscalPosition"]),
    ("account-journal", "Journals, payment methods, reconciliation models",
     "addons/account journal + payment method + reconcile model (incl. the dashboard raw SQL)",
     ["accountJournal", "accountPaymentMethod", "accountReconcileModel", "accountReconcileModelLineAccountTaxRel"]),
    ("product-catalog", "Product catalog (templates, variants, combos, vendor lines, pricelists)",
     "addons/product template/variant/supplierinfo/pricelist + their sale/purchase/stock/account extensions",
     ["productTemplate", "productProduct", "productTemplateAttributeValue",
      "productAttributeValueProductTemplateAttributeLineRel", "productCombo", "productSupplierinfo",
      "productPricelist", "productPricelistItem"]),
    ("stock-config", "Warehouse configuration (warehouses, locations, picking types, routes, rules, putaway, orderpoints)",
     "addons/stock configuration models + purchase_stock buy rules",
     ["stockWarehouse", "stockLocation", "stockPickingType", "stockRoute", "stockRule", "stockPutawayRule",
      "stockStorageCategoryCapacity", "stockWarehouseOrderpoint"]),
    ("sale", "Sales orders and lines",
     "addons/sale + sale_stock + sale_purchase + sale_edi_ubl (+ sale.report)",
     ["saleOrder", "saleOrderLine"]),
    ("purchase", "Purchase orders and lines",
     "addons/purchase + purchase_stock + purchase_edi_ubl_bis3 (+ purchase.report, purchase.bill.union, purchase.bill.line.match)",
     ["purchaseOrder", "purchaseOrderLine"]),
    ("stock-ops", "Stock operations (pickings, moves, move lines, quants, lots, packages, valuation)",
     "addons/stock operational models + stock_account product.value (+ the three PostgreSQL views)",
     ["stockPicking", "stockMove", "stockMoveLine", "stockQuant", "stockLot", "stockPackage",
      "stockPackageHistory", "stockPickingBatch", "stockReference", "productValue"]),
    ("account-ledger", "Ledger: journal entries, lines, reconciliation, payments, bank statements",
     "addons/account move/line/partial+full reconcile/payment/bank statement (+ account.invoice.report)",
     ["accountMove", "accountMoveLine", "accountPartialReconcile", "accountFullReconcile", "accountPayment",
      "accountBankStatement", "accountBankStatementLine"]),
]

# Plain Many2one columns that point at rows created *after* the owning row, cited to the code
# that creates the target and writes the column back. They are forward references, not
# dependencies; everything else in decision.references / 1:N child_references is a dependency.
FORWARD_EXCEPTIONS = {
    ("stockMove", "account_move_id"):
        "addons/stock_account/models/stock_move.py:260-285 _create_account_move creates the valuation "
        "account.move from the validated stock.move and writes account_move_id back (:283)",
    ("productValue", "account_move_id"):
        "addons/stock_account/models/product_value.py:46 account_move_id is set from the valuation entry "
        "that stock_account creates after the product.value row exists (stock_move.py:260-285)",
}

# s2.3 §4 rows name a module, not a table: the hook's unit is the unit owning the module's
# main model.
HOOK_MODULE_UNIT = {"sale": "sale", "purchase": "purchase", "account": "account-chart", "stock": "stock-ops",
                    "account_edi_ubl_cii": "account-ledger", "purchase_stock": "purchase", "sale_stock": "sale",
                    "stock_account": "stock-ops"}


def load(name):
    with open(MIG / name) as fh:
        return json.load(fh)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args) -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


# ----------------------------------------------------------------------------- spec / units

def build_units(spec, buckets, fixture):
    colls = {c["collection"]: c for c in spec["collections"]}
    unit_of = {}
    for uid, _, _, cs in UNITS:
        for c in cs:
            if c not in colls:
                raise SystemExit(f"{uid}: {c} is not a collection of the spec")
            if c in unit_of:
                raise SystemExit(f"{c} assigned twice")
            unit_of[c] = uid
    missing = sorted(set(colls) - set(unit_of))
    if missing:
        raise SystemExit(f"collections without a unit: {missing}")

    rows = fixture["row_counts"]
    units = {}
    for uid, name, slice_, cs in UNITS:
        roots = [colls[c]["root_table"] for c in cs]
        embedded = []
        for c in cs:
            for e in colls[c]["embeds"]:
                embedded.append({"collection": c, "array_path": e["array_path"], "table": e["child_table"],
                                 "shape": "junction" if is_junction(e) else "child_rows",
                                 "fixture_rows": rows.get(e["child_table"], 0)})
        zero_roots = [c for c in cs if rows.get(colls[c]["root_table"], 0) == 0]
        units[uid] = {
            "id": uid, "name": name, "slice": slice_,
            "owner_modules": sorted({buckets["tables"][colls[c]["root_table"]]["owner"] for c in cs}),
            "collections": cs,
            "root_tables": roots,
            "embedded_tables": embedded,
            "write_targets": [f"{TARGET_DB}.{c}" for c in cs],
            "fixture_rows": {t: rows.get(t, 0) for t in roots + [e["table"] for e in embedded]},
            "recon_unverified": {
                "collections": zero_roots,
                "reason": "0 fixture rows in .migration/fixtures/odoo_fixture.json: recon grades no row, "
                          "verdict UNVERIFIED without a committed seed scenario on a clone of the fixture",
                "embedded_arrays_zero_rows": [f"{e['collection']}.{e['array_path']}" for e in embedded
                                              if e["fixture_rows"] == 0],
            } if zero_roots or any(e["fixture_rows"] == 0 for e in embedded) else {"collections": [],
                                                                                   "embedded_arrays_zero_rows": []},
        }
    return units, unit_of, colls


def is_junction(embed) -> bool:
    return len(embed["child_key"]) == 2 and len(embed["child_fields"]) == 1


# ----------------------------------------------------------------------------- edges / depth

def build_edges(colls, unit_of):
    """Every inter-collection reference of the spec, tagged by where it comes from."""
    edges = []
    for c in colls.values():
        src = c["collection"]
        for r in (c.get("decision") or {}).get("references", []):
            edges.append({"from": src, "column": ".".join(r["column"]), "to": r["to"], "kind": "reference"})
        for e in c["embeds"]:
            for r in e.get("child_references", []):
                edges.append({"from": src, "array_path": e["array_path"], "child_table": e["child_table"],
                              "column": ".".join(r["column"]), "to": r["to"],
                              "kind": "junction" if is_junction(e) else "child_reference"})
    for ed in edges:
        ed["from_unit"], ed["to_unit"] = unit_of[ed["from"]], unit_of[ed["to"]]
        key = (ed["from"], ed["column"])
        ed["hard"] = ed["kind"] in ("reference", "child_reference") and key not in FORWARD_EXCEPTIONS
        if key in FORWARD_EXCEPTIONS:
            ed["forward_because"] = FORWARD_EXCEPTIONS[key]
    return [e for e in edges if e["from_unit"] != e["to_unit"]]


def depths(units, edges):
    hard = collections.defaultdict(set)
    for e in edges:
        if e["hard"]:
            hard[e["from_unit"]].add(e["to_unit"])
    # cycle check on the hard graph (Tarjan)
    sys.setrecursionlimit(10000)
    index, low, onstack, stack, sccs, counter = {}, {}, set(), [], [], [0]

    def visit(v):
        index[v] = low[v] = counter[0]; counter[0] += 1
        stack.append(v); onstack.add(v)
        for w in hard[v]:
            if w not in index:
                visit(w); low[v] = min(low[v], low[w])
            elif w in onstack:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop(); onstack.discard(w); comp.append(w)
                if w == v:
                    break
            sccs.append(comp)

    for u in units:
        if u not in index:
            visit(u)
    cycles = [sorted(c) for c in sccs if len(c) > 1]
    if cycles:
        raise SystemExit(f"hard dependency cycles remain, regroup UNITS or cite an exception: {cycles}")
    memo = {}

    def depth(u):
        if u not in memo:
            memo[u] = 0 if not hard[u] else 1 + max(depth(w) for w in hard[u])
        return memo[u]

    return {u: depth(u) for u in units}


# ----------------------------------------------------------------------------- s2.3 register

LETTER = re.compile(r"^\**(R|S|B|orm)\b")


def parse_register(notes_text: str):
    s23 = notes_text.split("\n## s3.1", 1)[0]
    sections = re.split(r"\n(?=###+ )", s23)
    rows = []
    for sec in sections:
        head, _, body = sec.partition("\n")
        m = re.match(r"###+ (\S+)\.? ?(.*)", head)
        if not m:
            continue
        sec_id = m.group(1).rstrip(".")
        table = [l for l in body.split("\n") if l.startswith("|") and not l.startswith("|---")]
        if not table:
            continue
        header = [c.strip() for c in table[0].strip().strip("|").split("|")]
        for line in table[1:]:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) == len(header) - 1 and header[3:5] == ["verb", "in-scope tables"]:
                # §3b row 27 writes verb and tables in one cell ("DECLARE CURSOR / FETCH over account_move")
                cells = cells[:3] + [cells[3], cells[3]] + cells[4:]
            if len(cells) != len(header):
                raise SystemExit(f"s2.3 §{sec_id}: row has {len(cells)} cells, header {len(header)}: {line[:80]}")
            row = dict(zip(header, cells))
            disp = row["disp."]
            lm = LETTER.match(disp)
            if lm:
                letter = lm.group(1)
            elif sec_id == "5" and disp.startswith("handled by the model"):
                letter = "model"  # §5 row 3: in-scope → in-scope FK edges, no R/S/B letter in the register
            else:
                raise SystemExit(f"s2.3 §{sec_id}: no disposition letter in {disp!r}")
            if sec_id == "3c":
                row_id = str(len([r for r in rows if r["section"] == "3c"]) + 1)
            elif sec_id == "4":
                row_id = f"{cells[0]} {cells[1].split()[0]}"
            else:
                row_id = cells[0]
            rows.append({"section": sec_id, "row": row_id, "disposition": letter, "disp_text": disp,
                         "cells": row})
    return rows


def register_totals(rows):
    out = {}
    for sec in ("3a", "3b"):
        rs = [r for r in rows if r["section"] == sec]
        sites = sum(int(r["cells"]["sites"]) for r in rs)
        out[sec] = {"rows": len(rs), "sites": sites,
                    **{k: sum(1 for r in rs if r["disposition"] == k) for k in ("R", "S", "B")}}
    return out


def table_resolver(colls, unit_of):
    root_unit = {c["root_table"]: unit_of[c["collection"]] for c in colls.values()}
    child_unit = {e["child_table"]: unit_of[c["collection"]] for c in colls.values() for e in c["embeds"]}
    known = {**child_unit, **root_unit}
    word = re.compile(r"[a-z][a-z0-9_]+")

    def resolve(text: str):
        for w in word.findall(text):
            if w in known:
                return known[w], w
        return None, None

    def resolve_all(text: str):
        """Every migrated table the text names, in order of first mention, with its unit."""
        seen, out = set(), []
        for w in word.findall(text):
            if w in known and w not in seen:
                seen.add(w)
                out.append((w, known[w]))
        return out
    resolve.all = resolve_all
    return resolve, known


def assign_register(rows, resolve, depth):
    """A row's rewrite must exist by the first wave in which any table it reads is Mongo-backed:
    the owner is the lowest-depth unit among every migrated table the row names; every other
    unit named is listed so its batch re-checks the rewrite when its own tables move."""
    table_cell = {"1": "in-scope tables reached", "2": "source tables", "3a": "in-scope tables",
                  "3b": "in-scope tables", "3c": "in-scope tables"}
    for r in rows:
        sec = r["section"]
        if sec in table_cell:
            named = resolve.all(r["cells"][table_cell[sec]])
            r["tables"] = [t for t, _ in named]
            units = sorted({u for _, u in named}, key=lambda u: (depth[u], u))
            r["unit"] = units[0] if units else None
            r["also_touches"] = units[1:]
        elif sec == "4":
            r["unit"] = HOOK_MODULE_UNIT.get(r["cells"]["module"])
            r["tables"], r["also_touches"] = [], []
        else:
            r["unit"] = None
            r["tables"], r["also_touches"] = [], []
    return rows


def register_entry(r):
    c = r["cells"]
    sec = r["section"]
    if sec == "1":
        where = f"{c['model']} {c['method (file)']}"
        what = c["in-scope tables reached"]
    elif sec == "2":
        where, what = c["model"], c["source tables"]
    elif sec in ("3a", "3b"):
        where = c["model / function (file:line)"]
        what = f"{c['verb']}: {c['in-scope tables']} — {c['when']}"
    elif sec == "3c":
        where, what = f"{c['caller']} → {c['framework code']}", c["in-scope tables"]
    elif sec == "4":
        where, what = f"{c['module']} {c['hook']}", c["body"]
    else:
        where, what = c["kind"], c["count in `odoo_src`"]
    out = {"register": f"s2.3 §{sec} row {r['row']}", "disposition": r["disposition"],
           "disposition_text": r["disp_text"], "where": where, "what": what}
    if r.get("tables"):
        out["migrated_tables"] = r["tables"]
    if r.get("also_touches"):
        out["also_touches"] = r["also_touches"]
    return out


# ----------------------------------------------------------------------------- code: models, routines, tests

def _str_list(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, (ast.List, ast.Tuple)):
        return [e.value for e in node.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
    return []


def scan_models():
    """model -> {table, files: [{file, line, kind}]} over the 15 scope + bridge modules.

    One Odoo class is read as a whole: `_name` alone, or `_name` with an `_inherit` that does not
    name the same model, defines the model (kind `name`); `_inherit` naming the `_name` model, or
    `_inherit` alone (string or list), extends every model it lists (kind `inherit`)."""
    found = collections.defaultdict(lambda: {"files": []})
    for mod in MODULES:
        for sub in ("models", "report", "wizard"):
            d = ROOT / "addons" / mod / sub
            if not d.is_dir():
                continue
            for py in sorted(d.rglob("*.py")):
                tree = ast.parse(py.read_text(errors="replace"))
                for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
                    attrs = {}
                    for st in cls.body:
                        if isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], ast.Name):
                            if st.targets[0].id in ("_name", "_inherit", "_table"):
                                attrs[st.targets[0].id] = st.value
                    name = _str_list(attrs["_name"])[:1] if "_name" in attrs else []
                    inherit = _str_list(attrs["_inherit"]) if "_inherit" in attrs else []
                    table = _str_list(attrs["_table"])[:1] if "_table" in attrs else []
                    rel = str(py.relative_to(ROOT))
                    if name and name[0] not in inherit:
                        found[name[0]]["files"].append({"file": rel, "line": cls.lineno, "kind": "name"})
                        if table:
                            found[name[0]]["table"] = table[0]
                        continue
                    for model in inherit:
                        found[model]["files"].append({"file": rel, "line": cls.lineno, "kind": "inherit"})
    for model, info in found.items():
        info.setdefault("table", model.replace(".", "_"))
    return found


def unit_models(units, known_unit, models):
    table_models = collections.defaultdict(list)
    for model, info in models.items():
        table_models[info["table"]].append(model)
    out = {u: {} for u in units}
    for table, unit in known_unit.items():
        for model in table_models.get(table, []):
            files = models[model]["files"]
            defining = [f for f in files if f["kind"] == "name"]
            extending = [f for f in files if f["kind"] == "inherit"]
            out[unit][model] = {"table": table,
                                "defined_in": [f"{f['file']}:{f['line']}" for f in defining],
                                "extended_in": [f"{f['file']}:{f['line']}" for f in extending]}
    return out


def unit_routines(patterns, resolve):
    groups = collections.defaultdict(lambda: {"ops": collections.Counter(), "freq": collections.Counter(),
                                              "patterns": 0, "lines": [10**9, 0], "tables": set()})
    unassigned = 0
    for p in patterns:
        unit = None
        for t in p["tables"]:
            unit, _ = resolve(t)
            if unit:
                break
        if not unit:
            unassigned += 1
            continue
        src = p["source"]
        routine = p.get("routine") or routine_from_note(p)
        g = groups[(unit, src["file"], routine)]
        g["ops"][p["op"]] += 1
        g["freq"][p.get("frequency") or "unrated"] += 1
        g["patterns"] += 1
        g["lines"] = [min(g["lines"][0], src["lines"][0]), max(g["lines"][1], src["lines"][1])]
        g["tables"].update(t for t in p["tables"] if resolve(t)[0])
    per_unit = collections.defaultdict(list)
    for (unit, file, routine), g in sorted(groups.items()):
        per_unit[unit].append({"routine": routine, "file": file, "lines": g["lines"],
                               "patterns": g["patterns"], "ops": dict(g["ops"]), "frequency": dict(g["freq"]),
                               "tables": sorted(g["tables"])})
    return per_unit, unassigned


def routine_from_note(p):
    # sql patterns carry no routine; the scan's note is "<file>:<lines> <Routine> <verb> ..."
    parts = (p.get("note") or "").split()
    if len(parts) >= 2 and parts[0].startswith(p["source"]["file"]):
        return parts[1]
    return "<module level>"


ENV_RE = re.compile(r"env\[['\"]([a-z._]+)['\"]\]")


def unit_tests(known_unit, models):
    """Each Odoo test file goes to the unit whose tables its env['model'] uses most."""
    model_table = {m: i["table"] for m, i in models.items()}
    per_unit = collections.defaultdict(list)
    for mod in MODULES:
        d = ROOT / "addons" / mod / "tests"
        if not d.is_dir():
            continue
        for py in sorted(d.glob("*.py")):
            if py.name == "__init__.py":
                continue
            counts = collections.Counter()
            for m in ENV_RE.findall(py.read_text(errors="replace")):
                table = model_table.get(m, m.replace(".", "_"))
                unit = known_unit.get(table)
                if unit:
                    counts[unit] += 1
            if counts:
                unit, n = counts.most_common(1)[0]
                per_unit[unit].append({"file": str(py.relative_to(ROOT)), "tag": f"/{mod}", "model_refs": n})
    return per_unit


# ----------------------------------------------------------------------------- waves

def build_waves(units, depth, spec, tol, contracts):
    by_depth = collections.defaultdict(list)
    for u in units.values():
        by_depth[depth[u["id"]]].append(u)
    waves = []
    for d in sorted(by_depth):
        wave = d + 1
        # one unit per batch, smallest first (the manager may merge small depth-0 batches at preflight)
        batches = []
        for u in sorted(by_depth[d], key=lambda u: (sum(u["fixture_rows"].values()), u["id"])):
            batches.append({"units": [u["id"]], "write_targets": list(u["write_targets"]),
                            "fixture_rows": sum(u["fixture_rows"].values())})
        for i, b in enumerate(batches, 1):
            b["id"] = f"w{wave}-b{i:02d}"
            b.update({"fixture_manifest": FIXTURE_MANIFEST, "recon_tolerances_version": tol["version"],
                      "mapping_version": spec["version"], **contracts})
            for uid in b["units"]:
                units[uid]["batch"] = b["id"]
        batches = [{"id": b["id"], "units": b["units"], "write_targets": b["write_targets"],
                    "fixture_manifest": b["fixture_manifest"],
                    "recon_tolerances_version": b["recon_tolerances_version"],
                    "mapping_version": b["mapping_version"], "mapping_sha256": b["mapping_sha256"],
                    "tolerance_sha256": b["tolerance_sha256"], "fixture_rows": b["fixture_rows"]}
                   for b in batches]
        waves.append({"wave": wave, "depth": d, "batches": batches,
                      "order": "batches listed smallest fixture_rows first; the first is the wave's canary"})
    return waves


# ----------------------------------------------------------------------------- main

TARGET_DB = None
FIXTURE_MANIFEST = ".migration/fixtures/odoo_fixture.json"


def main(argv=None) -> int:
    global TARGET_DB
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)

    spec = load("mapping_spec.json")
    buckets = load("table_buckets.json")
    fixture = load("fixtures/odoo_fixture.json")
    access = load("access_patterns.json")
    tol = load("recon_tolerances.json")
    conn = load("connectivity.json")
    allowed = load("allowed_targets.json")
    notes = (MIG / "NOTES.md").read_text()
    TARGET_DB = allowed["databases"][0]
    contracts = {"mapping_sha256": sha256(MIG / "mapping_spec.json"),
                 "tolerance_sha256": sha256(MIG / "recon_tolerances.json")}

    units, unit_of, colls = build_units(spec, buckets, fixture)
    edges = build_edges(colls, unit_of)
    depth = depths(units, edges)
    resolve, known_unit = table_resolver(colls, unit_of)

    for u in units.values():
        u["depth"] = depth[u["id"]]
        dep, fwd = collections.defaultdict(list), collections.defaultdict(list)
        for e in edges:
            if e["from_unit"] != u["id"]:
                continue
            desc = f"{e['from']}.{e.get('array_path', '')}{'.' if e.get('array_path') else ''}{e['column']} → {e['to']} ({e['kind']})"
            if depth[e["to_unit"]] < u["depth"]:
                dep[e["to_unit"]].append(desc)
            else:
                fwd[e["to_unit"]].append(desc + (f"; forward: {e['forward_because']}" if e.get("forward_because") else ""))
        u["depends_on"] = sorted(dep)
        u["depends_on_edges"] = {k: sorted(v) for k, v in sorted(dep.items())}
        u["forward_refs"] = {k: sorted(v) for k, v in sorted(fwd.items())}

    # same-depth cross-unit references would be a reference to a sibling batch's collection
    same = [(e["from_unit"], e["to_unit"], e["column"]) for e in edges
            if depth[e["from_unit"]] == depth[e["to_unit"]]]
    if same:
        raise SystemExit(f"references between units of the same depth (sibling batches): {same}")

    rows = assign_register(parse_register(notes), resolve, depth)
    totals = register_totals(rows)
    expect = {"3a": {"rows": 32, "sites": 58, "R": 24, "S": 4, "B": 4},
              "3b": {"rows": 42, "sites": 45, "R": 40, "S": 2, "B": 0}}
    if totals != expect:
        raise SystemExit(f"s2.3 register totals changed: {totals} != NOTES.md totals {expect}")
    for u in units.values():
        u["raw_sql"] = [register_entry(r) for r in rows if r["unit"] == u["id"] and r["section"] in ("3a", "3b", "3c")]
        u["crons"] = [register_entry(r) for r in rows if r["unit"] == u["id"] and r["section"] == "1"]
        u["reports_and_views"] = [register_entry(r) for r in rows if r["unit"] == u["id"] and r["section"] == "2"]
        u["hooks"] = [register_entry(r) for r in rows if r["unit"] == u["id"] and r["section"] == "4"]
        u["blocked"] = [x["register"] for x in u["raw_sql"] + u["hooks"] if x["disposition"] == "B"]
        u["register_rows_touching_later"] = [
            {**register_entry(r), "owner": r["unit"]} for r in rows
            if u["id"] in r.get("also_touches", []) and r["section"] in ("1", "2", "3a", "3b", "3c")]

    models = scan_models()
    for uid, ms in unit_models(units, known_unit, models).items():
        units[uid]["models"] = ms
    routines, unassigned_patterns = unit_routines(access["patterns"], resolve)
    tests = unit_tests(known_unit, models)
    for u in units.values():
        u["routines"] = routines.get(u["id"], [])
        u["scenarios"] = scenarios(u, tests.get(u["id"], []))

    waves = build_waves(units, depth, spec, tol, contracts)

    in_scope = sorted(t for t, v in buckets["tables"].items() if v["bucket"] == "in_scope" and v["kind"] == "table")
    transient = sorted(set(in_scope) - set(known_unit))
    estate_rows = [register_entry(r) for r in rows if r["unit"] is None]

    doc = {
        "kind": "migration-units",
        "board": "UNT12",
        "run_branch": "mongo-run/unt12",
        "derived_from": {
            "mapping_spec": {"file": ".migration/mapping_spec.json", "version": spec["version"],
                             "mapping_sha256": contracts["mapping_sha256"]},
            "recon_tolerances": {"file": ".migration/recon_tolerances.json", "version": tol["version"],
                                 "tolerance_sha256": contracts["tolerance_sha256"]},
            "fixture_manifest": FIXTURE_MANIFEST,
            "dependency_register": ".migration/NOTES.md §s2.3",
            "access_patterns": {"file": ".migration/access_patterns.json", "patterns": len(access["patterns"]),
                                "assigned": len(access["patterns"]) - unassigned_patterns,
                                "unassigned_no_in_scope_table": unassigned_patterns},
            "table_buckets": ".migration/table_buckets.json",
            "plugin_sha": (MIG / "plugin_sha").read_text().strip(),
            "generator": ".migration/derive_units.py",
        },
        "source_access": conn["source_access"],
        "target_access": conn["target_access"],
        "target_database": TARGET_DB,
        "rules": [
            "A unit is one coherent code slice (Odoo models of one functional area across the 15 scope + bridge modules) plus the collections it owns; every collection belongs to exactly one unit.",
            "The batch owning a parent collection loads every embedded child table of that collection (embedded_tables); embedded tables are never separate write targets.",
            "depends_on = every other unit reached by a decision.references row or an embed child_references row whose target unit sits at a lower depth; depends_on_edges lists the columns.",
            "Depth is the longest hard-dependency path. Hard edges are decision.references columns and the FK columns of 1:N embedded child rows (child_key id). Junction-array child_references (two-column key, one field) are not hard: the element holds only the referenced row's integer id, which is the same value on PostgreSQL (id shadow, s2.3 disposition S) and on MongoDB (_id), so the array loads and the ORM resolves it before or after the referenced collection migrates; NOTES.md s3.3 lists, from ir_model_fields in odoo_src, which model's Many2many field writes each forward junction. The two plain FK columns in forward_exceptions are cited to the code that creates the target row after the owning row.",
            "forward_refs = references to units at the same or a later depth; they resolve through the id shadow (s2.3 disposition S) until that unit migrates. No two units of the same depth reference each other (checked), so no batch references a sibling batch's collection.",
            "Waves are the depths (wave = depth + 1), one unit per batch. Batches within a wave are listed smallest fixture_rows first, the first being the wave's canary; the manager may merge small depth-0 batches at preflight (1-5 units per batch). Shared and reference collections (uom, product category, package types, chart of accounts, ...) sit at depth 0 and 1, waves 1 and 2.",
            "Raw-SQL, cron, view and hook rows are copied from the s2.3 register with their disposition letter unchanged. A row is owned by the lowest-depth (earliest-wave) unit among every migrated table it names, because the statement breaks as soon as the first of those tables loses its PostgreSQL columns; the other units it names are listed in also_touches and carry the row under register_rows_touching_later, so their batch re-checks the rewrite when their own tables move. Hooks go to the unit owning the module's main model; rows naming no migrated table are listed under estate.register_rows_without_unit.",
            "fixture_rows come from the committed fixture manifest (odoo_fixture = odoo_src clone + one outlier); a unit whose collection has 0 fixture rows is flagged recon_unverified and needs a seed scenario before its recon can grade PASS.",
            "Scenarios are the Odoo test files whose env[...] references land mostly on the unit's tables (run with --test-tags on the module), the register's report/view read_group checks, the cron bodies, and a seed for every 0-row collection.",
        ],
        "forward_exceptions": [{"collection": k[0], "column": k[1], "why": v} for k, v in FORWARD_EXCEPTIONS.items()],
        "coverage": {
            "in_scope_tables": len(in_scope),
            "root_tables": len(colls),
            "embedded_tables": sum(len(c["embeds"]) for c in colls.values()),
            "transient_wizard_tables_not_migrated": len(transient),
            "arithmetic": f"{len(in_scope)} = {len(colls)} roots + {sum(len(c['embeds']) for c in colls.values())} embedded + {len(transient)} transient (s3.1 answers.txt `close transient_tables`: scratch state, stays on PostgreSQL)",
            "transient_tables": transient,
            "collections_with_zero_fixture_rows": sorted(c for u in units.values() for c in u["recon_unverified"]["collections"]),
        },
        "register_totals": totals,
        "prerequisites_before_wave_1": [
            {"register": "s2.3 §6", "item": "storage path skips or rewrites the view init() DDL (§2), sequence.mixin.init (§3a row 1, §3b row 1) and analytic.mixin.init (§3c) index DDL for Mongo-backed models"},
            {"register": "s2.3 §1", "item": "deactivate cron jobs 19, 20, 21, 22, 23 and 1 (autovacuum) on every migration target database before a load or recon; re-enable per unit"},
            {"register": "s2.3 §3a row 28 / s3.1 design_decisions note", "item": "stock is installed before product_product opts in, on every database that can install stock (B, manager decision recorded as an ordering rule)"},
            {"register": "s2.3 §3a row 23", "item": "kpi_provider.get_kpi_summary runs without a registry (B): manager decision before the account-ledger / account-journal wave"},
        ],
        "estate": {
            "postgresql_side": [register_entry(r) for r in rows if r["section"] == "5"],
            "register_rows_without_unit": [e for e in estate_rows if not e["register"].startswith("s2.3 §5")],
        },
        "units": [units[uid] for uid, *_ in UNITS],
        "waves": waves,
    }
    text = json.dumps(doc, indent=1, ensure_ascii=False) + "\n"
    if args.check:
        if OUT.read_text() != text:
            print("units.json differs from the derivation", file=sys.stderr)
            return 1
        print("units.json matches")
        return 0
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(ROOT)}: {len(units)} units, {len(waves)} waves, "
          f"{sum(len(w['batches']) for w in waves)} batches")
    for w in waves:
        print(f"  wave {w['wave']} (depth {w['depth']}): " + ", ".join(f"{b['id']}={b['units']} rows={b['fixture_rows']}" for b in w["batches"]))
    return 0


def scenarios(u, tests):
    out = []
    for t in tests:
        out.append({"kind": "odoo_test", "file": t["file"], "module_tag": t["tag"], "model_refs": t["model_refs"]})
    for r in u["reports_and_views"]:
        out.append({"kind": "report_read_group", "register": r["register"], "model": r["where"],
                    "check": "read_group / search_read of the report equals the PostgreSQL result on the fixture"})
    for c in u["crons"]:
        out.append({"kind": "cron", "register": c["register"], "job": c["where"]})
    for c in u["recon_unverified"]["collections"]:
        out.append({"kind": "seed", "collection": c,
                    "check": "ORM seed on a clone of the fixture with pinned create_date/write_date so recon grades rows, never on odoo_src"})
    return out


if __name__ == "__main__":
    sys.exit(main())
