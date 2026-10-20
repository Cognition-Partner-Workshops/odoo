"""Second half of build_fixture.sh: runs inside the freshly cloned fixture database.

Adds the synthetic outlier (a product template with OUTLIER_CHILDREN vendor
pricelist lines; product_supplierinfo is a leaf in the in-scope fan-outs, so the
extra rows do not pull any other fan-out's percentiles below the profile),
counts every in-scope table, recomputes every in-scope fan-out with the pinned
profile's query shape and nearest-rank percentiles, fails if the fixture is below
the profile on p50/p99/max or if a mapping_spec embed has no profile fan-out,
tags each fan-out with the spec embeds it backs, lists fan-outs skipped for an
empty parent table and
writes the manifest accepted by preflight.py::validate_fixture_manifest. Database
ACLs are not part of a template copy, so the source's PUBLIC revoke and odoo_ro
CONNECT grant are re-applied here.
Connects with libpq defaults (PGPORT from the caller); never opens the source.
"""
import json
import math
import os
import sys
from datetime import datetime, timezone

import psycopg2

root = os.environ["ROOT"]
fixtureDb, sourceDb = os.environ["FIXTURE_DB"], os.environ["SOURCE_DB"]
outlierChildren = int(os.environ["OUTLIER_CHILDREN"])
readOnlyRole = os.environ["RO_ROLE"]
manifestPath = os.environ["MANIFEST"]
outlierRel = "fanout:product_supplierinfo->product_template(product_tmpl_id)"
PCTS = ("p50", "p99", "max")

profile = json.load(open(f"{root}/.migration/data_profile.json"))
buckets = json.load(open(f"{root}/.migration/table_buckets.json"))["tables"]
inScope = sorted(t for t, v in buckets.items() if v["bucket"] == "in_scope" and v["kind"] == "table")
fanouts = [s for s in profile["stats"] if s["query_id"] == "fanout"
           and s["subject"]["parent"] in inScope and s["subject"]["child"] in inScope]
fanoutIds = {s["id"] for s in profile["stats"] if s["query_id"] == "fanout"}

# every embed in the signed-off spec must have its fan-out in the table
spec = json.load(open(f"{root}/.migration/mapping_spec.json"))
embedsByFanout, failures = {}, []
for coll in spec["collections"]:
    for embed in coll.get("embeds") or []:
        fanoutId = f"fanout:{embed['child_table']}->{coll['root_table']}({','.join(embed['parent_key'])})"
        embedsByFanout.setdefault(fanoutId, []).append(f"{coll['collection']}.{embed['array_path']}")
        if fanoutId not in fanoutIds:
            failures.append(f"{coll['collection']}.{embed['array_path']}: {fanoutId} is not in data_profile.json")
        elif fanoutId not in {s["id"] for s in fanouts}:
            fanouts.append(next(s for s in profile["stats"] if s["id"] == fanoutId))

conn = psycopg2.connect(dbname=fixtureDb)
cur = conn.cursor()


def percentile(dist, pct):
    # nearest-rank over (value, count) pairs, as in the pinned data_profile.py
    total = sum(n for _, n in dist)
    if not total:
        return None
    rank = max(1, math.ceil(total * pct / 100.0))
    seen = 0
    for value, n in dist:
        seen += n
        if seen >= rank:
            return value
    return dist[-1][0]


def columns(table, exclude):
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' "
                "AND table_name=%s ORDER BY ordinal_position", (table,))
    return [c for (c,) in cur.fetchall() if c not in exclude]


def q(name):
    return '"' + name.replace('"', '""') + '"'


def fkParentColumns(child, parent, childCols):
    cur.execute("""
        SELECT ARRAY(SELECT a.attname::text FROM unnest(con.confkey) WITH ORDINALITY k(attnum, ord)
                     JOIN pg_attribute a ON a.attrelid=con.confrelid AND a.attnum=k.attnum ORDER BY ord)
        FROM pg_constraint con
        WHERE con.contype='f' AND con.conrelid=%s::regclass AND con.confrelid=%s::regclass
          AND ARRAY(SELECT a.attname::text FROM unnest(con.conkey) WITH ORDINALITY k(attnum, ord)
                    JOIN pg_attribute a ON a.attrelid=con.conrelid AND a.attnum=k.attnum ORDER BY ord)
              = %s::text[]""", (q(child), q(parent), childCols))
    row = cur.fetchone()
    return row[0] if row else None


cur.execute("SELECT value FROM ir_config_parameter WHERE key='migration.fixture_source'")
row = cur.fetchone()
if not row:
    sys.exit(f"build_fixture: {fixtureDb} carries no migration.fixture_source marker")
sourceMarker = row[0]

cur.execute(f"REVOKE ALL ON DATABASE {q(fixtureDb)} FROM PUBLIC")
cur.execute(f"GRANT CONNECT ON DATABASE {q(fixtureDb)} TO {q(readOnlyRole)}")

# synthetic outlier: copy the template with the most vendor pricelist lines (with
# one variant, as the ORM would create, stocked like the sibling variant it is
# copied from so the stock_quant fan-out keeps its median), then clone one of its lines
# OUTLIER_CHILDREN times under the new template. uom_id is spread round-robin over
# the units related to the product's own unit (same parent_path root) so the vendor
# lines stay convertible and do not pile up on a single uom fan-out.
cur.execute("SELECT product_tmpl_id, MIN(id) FROM product_supplierinfo GROUP BY 1 ORDER BY COUNT(*) DESC, 1 LIMIT 1")
baseTmpl, baseLine = cur.fetchone()
cur.execute("SELECT MIN(id) FROM product_product WHERE product_tmpl_id=%s", (baseTmpl,))
baseVariant = cur.fetchone()[0]
cur.execute("SELECT id FROM uom_uom WHERE split_part(parent_path, '/', 1) = ("
            "SELECT split_part(u.parent_path, '/', 1) FROM uom_uom u JOIN product_template pt ON pt.uom_id = u.id "
            "WHERE pt.id = %s) ORDER BY id", (baseTmpl,))
uomIds = [u for (u,) in cur.fetchall()]
cols = ", ".join(map(q, columns("product_template", {"id", "name", "default_code"})))
cur.execute(f"INSERT INTO product_template (name, {cols}) "
            f"SELECT %s::jsonb, {cols} FROM product_template WHERE id=%s RETURNING id",
            (json.dumps({"en_US": f"Fixture outlier template ({outlierChildren} vendor lines)"}), baseTmpl))
outlierTmpl = cur.fetchone()[0]
cols = ", ".join(map(q, columns("product_product",
                                {"id", "product_tmpl_id", "default_code", "barcode", "combination_indices"})))
cur.execute(f"INSERT INTO product_product (product_tmpl_id, default_code, {cols}) "
            f"SELECT %s, 'FIXTURE-OUTLIER', {cols} FROM product_product WHERE id=%s RETURNING id",
            (outlierTmpl, baseVariant))
outlierVariant = cur.fetchone()[0]
# the sibling's quant positions at zero quantity, unreserved, lot-free and unowned:
# a zero position needs no move line, lot or valuation history to be consistent
quantCols = columns("stock_quant", {"id", "product_id", "lot_id", "package_id", "owner_id"})
zeroed = [c for c in ("quantity", "reserved_quantity", "inventory_quantity", "inventory_diff_quantity") if c in quantCols]
cols = ", ".join(map(q, [c for c in quantCols if c not in zeroed]))
zeroes = ", ".join(["0"] * len(zeroed))
cur.execute(f"INSERT INTO stock_quant (product_id, lot_id, package_id, owner_id, {', '.join(map(q, zeroed))}, {cols}) "
            f"SELECT %s, NULL, NULL, NULL, {zeroes}, {cols} FROM stock_quant WHERE product_id=%s AND lot_id IS NULL",
            (outlierVariant, baseVariant))
quants = cur.rowcount
cols = ", ".join(map(q, columns("product_supplierinfo",
                                {"id", "product_tmpl_id", "product_id", "product_code", "sequence", "uom_id"})))
for i in range(1, outlierChildren + 1):
    cur.execute(f"INSERT INTO product_supplierinfo (product_tmpl_id, product_id, product_code, sequence, uom_id, {cols}) "
                f"SELECT %s, NULL, %s, %s, %s, {cols} FROM product_supplierinfo WHERE id=%s",
                (outlierTmpl, f"FIXTURE-OUTLIER-{i:02d}", i, uomIds[(i - 1) % len(uomIds)], baseLine))
cur.execute("INSERT INTO ir_config_parameter (key, value) VALUES ('migration.fixture', %s)",
            (f"{sourceDb}:migration.fixture_source={sourceMarker}",))

rowCounts = {}
for t in inScope:
    cur.execute(f"SELECT COUNT(*) FROM {q(t)}")
    rowCounts[t] = cur.fetchone()[0]

compared, skipped = [], []
for stat in fanouts:
    subj = stat["subject"]
    parent, child, childCols = subj["parent"], subj["child"], subj["child_columns"]
    entry = {"id": stat["id"], "parent": parent, "child": child,
             "embeds": embedsByFanout.get(stat["id"], []),
             "profile": {k: stat["values"][k] for k in PCTS}}
    if rowCounts[parent] == 0:
        skipped.append({**entry, "reason": "parent table empty"})
        continue
    parentCols = fkParentColumns(child, parent, childCols)
    if not parentCols:
        failures.append(f"{stat['id']}: no matching FK constraint in {fixtureDb}")
        continue
    pcols = ", ".join(f"p.{q(c)}" for c in parentCols)
    join = " AND ".join(f"c.{q(fk)} = p.{q(rc)}" for fk, rc in zip(childCols, parentCols))
    cur.execute(f"SELECT n AS children, COUNT(*) AS parents FROM ("
                f"SELECT {pcols}, COUNT(c.{q(childCols[0])}) AS n FROM {q(parent)} p "
                f"LEFT JOIN {q(child)} c ON {join} GROUP BY {pcols}) x GROUP BY n ORDER BY n")
    dist = [(int(a), int(b)) for a, b in cur.fetchall()]
    entry["fixture"] = {"p50": percentile(dist, 50), "p99": percentile(dist, 99), "max": dist[-1][0]}
    below = [k for k in PCTS if entry["profile"][k] is not None and entry["fixture"][k] < entry["profile"][k]]
    if below:
        failures.append(f"{stat['id']}: fixture below profile on {','.join(below)} "
                        f"fixture={entry['fixture']} profile={entry['profile']}")
    compared.append(entry)

outlier = next((e for e in compared if e["id"] == outlierRel), None)
if outlier is None:
    failures.append(f"{outlierRel}: outlier relationship was not compared")
elif outlier["fixture"]["max"] <= outlier["profile"]["max"]:
    failures.append(f"{outlierRel}: outlier max {outlier['fixture']['max']} "
                    f"does not exceed profile max {outlier['profile']['max']}")

if failures:
    conn.rollback()
    print("build_fixture: FAIL", file=sys.stderr)
    for f in failures:
        print("  " + f, file=sys.stderr)
    sys.exit(1)

manifest = {
    "source": f"{sourceDb} (migration.fixture_source={sourceMarker}, "
              f"profile census_sha256={profile['census_sha256']})",
    "method": "synthetic",
    "masked_columns": [],
    "produced_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "produced_by": ".migration/fixtures/build_fixture.sh",
    "database": fixtureDb,
    "filestore": f"~/.local/share/Odoo/filestore/{fixtureDb}",
    "synthetic_outlier": {
        "relationship": outlierRel,
        "product_template_id": outlierTmpl,
        "product_product_id": outlierVariant,
        "zero_quants_at_sibling_locations": quants,
        "children": outlierChildren,
        "uom_id": f"round-robin over the {len(uomIds)} units related to the product's unit",
        "product_code_prefix": "FIXTURE-OUTLIER-",
    },
    "row_counts": rowCounts,
    "fanout_check": {
        "in_scope_fanouts": len(fanouts),
        "compared": len(compared),
        "skipped_empty_parent": len(skipped),
        "rule": "fixture p50/p99/max >= profile p50/p99/max for every compared fan-out",
    },
    "embed_coverage": {
        "spec_version": spec["version"],
        "spec_embeds": sum(len(v) for v in embedsByFanout.values()),
        "compared": sum(len(e["embeds"]) for e in compared),
        "skipped_empty_parent": sum(len(e["embeds"]) for e in skipped),
    },
    "fanouts": compared,
    "fanouts_skipped": skipped,
}
# serialise before committing, publish after: a failed write never leaves a
# rebuilt database next to a stale manifest (the wrapper removed the old one)
with open(manifestPath + ".tmp", "w") as fh:
    json.dump(manifest, fh, indent=1)
    fh.write("\n")
conn.commit()
os.replace(manifestPath + ".tmp", manifestPath)
print(f"build_fixture: {fixtureDb} outlier product_template id={outlierTmpl} variant id={outlierVariant} supplierinfo_lines={outlierChildren}; "
      f"fan-outs compared={len(compared)} skipped_empty_parent={len(skipped)}; "
      f"spec embeds covered={manifest['embed_coverage']['compared']}+{manifest['embed_coverage']['skipped_empty_parent']}"
      f"/{manifest['embed_coverage']['spec_embeds']}; "
      f"tables={len(rowCounts)} rows={sum(rowCounts.values())}")
