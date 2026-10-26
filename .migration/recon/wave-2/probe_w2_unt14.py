#!/usr/bin/env python3
"""Read-only verifier probes for wave 2 (UNT14-54), past the recon gate.

    probe_w2_unt14.py snapshot <out.json> <coll,coll,...>   # count, raw-BSON sha256, max writeDate per collection
    probe_w2_unt14.py unit <unit> <out.json>                # the unit's collection against odoo_src

Target: odoo_unt13 on MONGODB_ATLAS_URI (reads only). Source: the read-only PostgreSQL role in ODOO_PG_RO_DSN
(JSON, by name only), session read-only. Checks per unit: count; per mapped field missing == source NULLs, no
explicit nulls, BSON type == spec bson_type; no unmapped keys (root and embedded elements); no duplicate keys
(_id, junction pair, natural keys); every root row compared field by field; every embedded array compared
element by element with the child table; declared indexes present with the same key order, unique flag and
partial filter; every declared reference resolved against the real FK parent: a merged wave 1-2 collection
(or embedded child array) in odoo_unt13, otherwise the PostgreSQL-resident table in odoo_src; root junctions
read back from both endpoints. Prints one JSON object; exit 1 on any FAIL.
"""
import datetime as dt
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from decimal import Decimal

import psycopg
from bson import decode
from bson.codec_options import CodecOptions
from bson.decimal128 import Decimal128
from bson.raw_bson import RawBSONDocument
from pymongo import MongoClient

ROOT = os.environ.get("ROOT", ".")
TARGET_DB = "odoo_unt13"
MERGED_WAVES = {1, 2}
spec = json.load(open(f"{ROOT}/.migration/mapping_spec.json"))
units = json.load(open(f"{ROOT}/.migration/units.json"))
cols = {c["collection"]: c for c in spec["collections"]}
coll_meta = {}
for u in units["units"]:
    for cc in u["collections"]:
        coll_meta[cc["collection"]] = {"unit": u["id"], "wave": u["wave"], "batch": u["batch"]}
merged_root = {cols[c]["root_table"]: c for c in coll_meta if coll_meta[c]["wave"] in MERGED_WAVES}
merged_embed = {e["child_table"]: (c, e) for c in coll_meta if coll_meta[c]["wave"] in MERGED_WAVES
                for e in cols[c].get("embeds", [])}
table_wave = {cols[c]["root_table"]: coll_meta[c]["wave"] for c in coll_meta}
table_wave.update({e["child_table"]: coll_meta[c]["wave"] for c in coll_meta for e in cols[c].get("embeds", [])})

client = MongoClient(os.environ["MONGODB_ATLAS_URI"], serverSelectionTimeoutMS=20000)
db = client.get_database(TARGET_DB)
RAW = CodecOptions(document_class=RawBSONDocument)

BSON_PY = {"int": (int,), "string": (str,), "date": (dt.datetime,), "bool": (bool,), "object": (dict,),
           "decimal": (Decimal128,), "double": (float,), "array": (list,), "long": (int,)}


def type_ok(v, bson_type):
    if bson_type not in BSON_PY:
        return True
    if bson_type in ("int", "long") and isinstance(v, bool):
        return False
    return isinstance(v, BSON_PY[bson_type])


def norm(v):
    if isinstance(v, Decimal128):
        return v.to_decimal()
    if isinstance(v, dt.datetime):
        return v.replace(tzinfo=None, microsecond=v.microsecond // 1000 * 1000)
    if isinstance(v, dt.date):
        return dt.datetime(v.year, v.month, v.day)
    if isinstance(v, dict):
        return {k: norm(x) for k, x in sorted(v.items())}
    if isinstance(v, list):
        return [norm(x) for x in v]
    return v


def equal(a, b):
    a, b = norm(a), norm(b)
    if a is None or b is None:
        return a is None and b is None
    num = (int, float, Decimal)
    if isinstance(a, num) and isinstance(b, num) and not isinstance(a, bool) and not isinstance(b, bool):
        return abs(Decimal(str(a)) - Decimal(str(b))) <= Decimal("1e-9")
    return a == b


def snake(name):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def raw_snapshot(coll):
    raws = list(db.get_collection(coll, codec_options=RAW).find({}, sort=[("_id", 1)]))
    docs = [decode(r.raw) for r in raws]
    digest = hashlib.sha256(b"".join(r.raw for r in raws)).hexdigest()
    wd = [d["writeDate"] for d in docs if isinstance(d.get("writeDate"), dt.datetime)]
    return docs, {"count": len(docs), "raw_bson_sha256": digest,
                  "max_writeDate": max(wd).isoformat() if wd else None}


if sys.argv[1] == "snapshot":
    out = {"label": os.environ.get("PROBE_LABEL", ""), "taken_at": dt.datetime.now(dt.timezone.utc).isoformat(),
           "database": TARGET_DB, "collections": {}}
    for coll in sys.argv[3].split(","):
        _, s = raw_snapshot(coll)
        out["collections"][coll] = s
    json.dump(out, open(sys.argv[2], "w"), indent=1)
    print(json.dumps(out["collections"], indent=1))
    sys.exit(0)

UNIT, OUT = sys.argv[2], sys.argv[3]
COLL = UNIT
cspec = cols[COLL]
TABLE = cspec["root_table"]
fields = cspec["fields"]
embeds = cspec.get("embeds", [])
key = cspec["key"]
JUNCTION = isinstance(key["target"], list)
decision = cspec.get("decision") or {}

kw = json.loads(os.environ["ODOO_PG_RO_DSN"])
kw["dbname"] = kw.pop("database")
conn = psycopg.connect(**kw)
conn.read_only = True
cur = conn.cursor()


def q(sql, args=None):
    cur.execute(sql, args or ())
    return cur.fetchall()


assert q("SELECT current_database()")[0][0] == "odoo_src"
results = {"unit": UNIT, "collection": f"{TARGET_DB}.{COLL}", "source": f"odoo_src.{TABLE}",
           "taken_at": dt.datetime.now(dt.timezone.utc).isoformat(), "probes": []}


def probe(name, status, **ev):
    results["probes"].append({"probe": name, "status": status, **ev})
    print(f"{status:5} {name} {json.dumps(ev, default=str)[:240]}")


def fk_parent(table, column):
    rows = q("SELECT confrelid::regclass::text FROM pg_constraint c JOIN pg_attribute a "
             "ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey) "
             "WHERE c.contype = 'f' AND c.conrelid = %s::regclass AND a.attname = %s", (table, column))
    return rows[0][0] if rows else None


def table_exists(table):
    return bool(q("SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name=%s", (table,)))


# ---- 1. snapshot + count ----
docs, snap = raw_snapshot(COLL)
results["snapshot"] = snap
src_count = q(f"SELECT COUNT(*) FROM {TABLE}")[0][0]
probe("count", "PASS" if src_count == len(docs) else "FAIL", source=src_count, target=len(docs))

# ---- 2. root fields: missing vs NULL, explicit nulls, types ----
field_stats = {}
for f in fields:
    t = f["target"]
    missing = sum(1 for d in docs if t not in d)
    nulls = sum(1 for d in docs if t in d and d[t] is None)
    bad = sum(1 for d in docs if d.get(t) is not None and not type_ok(d[t], f.get("bson_type")))
    src_null = q(f"SELECT COUNT(*) FROM {TABLE} WHERE {f['source']} IS NULL")[0][0]
    field_stats[t] = {"source_null": src_null, "missing": missing, "explicit_null": nulls, "bad_type": bad}
    ok = nulls == 0 and bad == 0 and missing == src_null
    if not ok:
        probe(f"field:{t}", "FAIL", **field_stats[t], bson_type=f.get("bson_type"))
probe("fields", "PASS" if all(v["explicit_null"] == 0 and v["bad_type"] == 0 and v["missing"] == v["source_null"]
                              for v in field_stats.values()) else "FAIL",
      fields=len(fields), stats=field_stats)

# ---- 3. unmapped keys ----
allowed = {"_id"} | {f["target"] for f in fields} | {e["array_path"] for e in embeds}
if JUNCTION:
    allowed |= set(key["target"])
extra = sorted({k for d in docs for k in d} - allowed)
probe("unmapped_keys", "PASS" if not extra else "FAIL", extra_keys=extra)

# ---- 4. duplicates ----
ids = [d["_id"] for d in docs]
dup = {"_id": len(ids) - len(set(ids))}
if JUNCTION:
    pairs = [tuple(d.get(t) for t in key["target"]) for d in docs]
    dup["+".join(key["target"])] = len(pairs) - len(set(pairs))
by_src = {f["source"]: f["target"] for f in fields}
for nk in decision.get("natural_keys", []):
    targets = [by_src.get(c) for c in nk["columns"]]
    if None in targets:
        continue
    vals = [tuple(json.dumps(norm(d.get(t)), sort_keys=True, default=str) for t in targets) for d in docs]
    dup[nk["name"]] = len(vals) - len(set(vals))
probe("duplicates", "PASS" if not any(dup.values()) else "FAIL", **dup)

# ---- 5. root rows field by field / junction pair set ----
if not JUNCTION:
    srccols = [f["source"] for f in fields]
    rows = q(f"SELECT id{''.join(', ' + c for c in srccols)} FROM {TABLE} ORDER BY id")
    src = {r[0]: dict(zip(srccols, r[1:])) for r in rows}
    by_id = {d["_id"]: d for d in docs}
    keydiff = {"source_only": sorted(set(src) - set(by_id))[:10], "target_only": sorted(set(by_id) - set(src))[:10]}
    mism = []
    for k, row in src.items():
        d = by_id.get(k)
        if d is None:
            continue
        for f in fields:
            if not equal(row[f["source"]], d.get(f["target"])):
                mism.append([k, f["target"], str(norm(row[f["source"]]))[:60], str(norm(d.get(f["target"])))[:60]])
    probe("root_rows", "PASS" if not mism and not keydiff["source_only"] and not keydiff["target_only"] else "FAIL",
          rows_compared=len(src), fields_per_row=len(fields), mismatches=len(mism), first_mismatches=mism[:5], **keydiff)
else:
    a, b = key["source"]
    ta, tb = key["target"]
    src_pairs = set(q(f"SELECT {a}, {b} FROM {TABLE}"))
    tgt_pairs = {(d.get(ta), d.get(tb)) for d in docs}
    probe("junction_pairs", "PASS" if src_pairs == tgt_pairs and len(tgt_pairs) == len(docs) else "FAIL",
          source=len(src_pairs), target=len(tgt_pairs),
          source_only=sorted(src_pairs - tgt_pairs)[:5], target_only=sorted(tgt_pairs - src_pairs)[:5])
    for side, other, ts, to, flip in ((a, b, ta, tb, False), (b, a, tb, ta, True)):
        sg, tg = defaultdict(set), defaultdict(set)
        for x, y in src_pairs:
            if flip:
                sg[y].add(x)
            else:
                sg[x].add(y)
        for d in docs:
            tg[d.get(ts)].add(d.get(to))
        bad = sorted(k for k in set(sg) | set(tg) if sg.get(k) != tg.get(k))
        parent = fk_parent(TABLE, side)
        exists = set()
        if parent in merged_root:
            exists = {d["_id"] for d in db.get_collection(merged_root[parent]).find({"_id": {"$in": list(tg)}}, {"_id": 1})}
            where = f"{TARGET_DB}.{merged_root[parent]}._id (wave {table_wave[parent]})"
        elif parent in merged_embed:
            c2, e2 = merged_embed[parent]
            idt = next(f["target"] for f in e2["child_fields"] if f["source"] == e2["key"]["source"][0])
            exists = {d["v"] for d in db.get_collection(c2).aggregate(
                [{"$unwind": "$" + e2["array_path"]}, {"$project": {"v": f"${e2['array_path']}.{idt}"}}])} & set(tg)
            where = f"{TARGET_DB}.{c2}.{e2['array_path']}.{idt} (wave {table_wave[parent]})"
        else:
            exists = {r[0] for r in q(f"SELECT id FROM {parent} WHERE id = ANY(%s)", (list(tg),))}
            where = f"odoo_src.{parent} (PostgreSQL-resident, wave {table_wave.get(parent, 'framework')})"
        dangling = sorted(set(tg) - exists)
        probe(f"junction_readback:{ts}", "PASS" if not bad and not dangling else "FAIL",
              endpoint_table=parent, resolved_in=where, endpoints=len(tg), links=sum(len(v) for v in tg.values()),
              groups_differing=bad[:5], dangling=dangling[:5])

# ---- 6. embedded arrays element by element ----
for e in embeds:
    path, child, pk = e["array_path"], e["child_table"], e["parent_key"][0]
    cfields = e["child_fields"]
    ccols = [f["source"] for f in cfields]
    rows = q(f"SELECT {pk}{''.join(', ' + c for c in ccols)} FROM {child} ORDER BY {pk}")
    src = defaultdict(list)
    for r in rows:
        src[r[0]].append(dict(zip(ccols, r[1:])))
    allowed_e = {f["target"] for f in cfields} | {f["target"] for f in e.get("fields", [])}
    extra_e, nulls_e, bad_e, mism, empty_arrays = set(), 0, 0, [], 0
    tgt = {}
    for d in docs:
        arr = d.get(path)
        if arr is None:
            continue
        if arr == []:
            empty_arrays += 1
        elems = []
        for el in arr:
            if not isinstance(el, dict):
                el = {e["key"]["target"]: el}
            extra_e |= set(el) - allowed_e
            for f in cfields:
                v = el.get(f["target"])
                if f["target"] in el and v is None:
                    nulls_e += 1
                if v is not None and not type_ok(v, f.get("bson_type")):
                    bad_e += 1
            elems.append(el)
        tgt[d["_id"]] = elems

    def canon_elems(lst, names):
        return sorted(json.dumps([norm(x.get(n)) for n in names], sort_keys=True, default=str) for x in lst)
    for parent in set(src) | set(tgt):
        s_el = canon_elems(src.get(parent, []), ccols)
        t_el = canon_elems([{f["source"]: x.get(f["target"]) for f in cfields} for x in tgt.get(parent, [])], ccols)
        if s_el != t_el:
            mism.append([parent, len(s_el), len(t_el)])
    probe(f"embed:{path}", "PASS" if not mism and not extra_e and not nulls_e and not bad_e else "FAIL",
          child_table=child, parents_with_children_source=len(src), parents_with_array_target=len(tgt),
          children_source=sum(len(v) for v in src.values()), elements_target=sum(len(v) for v in tgt.values()),
          parents_differing=mism[:5], unmapped_element_keys=sorted(extra_e), explicit_nulls=nulls_e,
          bad_types=bad_e, empty_arrays=empty_arrays)

# ---- 7. indexes: keys in order, unique flag, partial filter ----
live = {}
for ix in db.get_collection(COLL).list_indexes():
    live[tuple((k, int(v)) for k, v in ix["key"].items())] = {
        "unique": bool(ix.get("unique", False)), "partialFilterExpression": ix.get("partialFilterExpression")}
want = {}
for ix in cspec.get("indexes", []):
    keys = tuple((k, int(d)) for k, d in ix["keys"])
    pfe = ix.get("partialFilterExpression", ix.get("partial_filter"))
    if ix.get("unique"):
        # storage_mongodb._create_indexes: a unique index skips documents missing a key (NULLs are omitted),
        # so the live filter is {path: {$exists: true}} per key, $and-ed with the spec's own filter if any
        exists = {k: {"$exists": True} for k, _ in keys}
        pfe = {"$and": [exists, pfe]} if pfe else exists
    want[keys] = {"unique": bool(ix.get("unique", False)), "partialFilterExpression": pfe}
missing = [list(k) for k in want if k not in live]
opt_mismatch = [{"keys": list(k), "spec": want[k], "live": live[k]} for k in want if k in live and want[k] != live[k]]
extra_ix = [list(k) for k in live if k not in want and k != (("_id", 1),)]
probe("indexes", "PASS" if not missing and not opt_mismatch else "FAIL", declared=len(want),
      spec_partial_filters=sum(1 for ix in cspec.get("indexes", []) if ix.get("partialFilterExpression") or ix.get("partial_filter")),
      unique_exists_filters_expected=sum(1 for v in want.values() if v["unique"]),
      live_options={json.dumps(list(k)): v for k, v in live.items()},
      missing=missing, option_mismatch=opt_mismatch, extra_live=extra_ix)

# ---- 8. references resolved against the real FK parent ----
key_fields = {f["source"]: f["target"] for f in decision.get("key_fields", [])}
refs = []
for r in decision.get("references", []):
    col = r["column"][0]
    refs.append((TABLE, col, by_src.get(col) or key_fields.get(col), r["to"],
                 [d.get(by_src.get(col) or key_fields.get(col)) for d in docs]))
for e in embeds:
    tmap = {f["source"]: f["target"] for f in e["child_fields"]}
    for r in e.get("child_references", []):
        col = r["column"][0]
        vals = []
        for d in docs:
            for el in d.get(e["array_path"], []) or []:
                vals.append(el.get(tmap[col]) if isinstance(el, dict) else el)
        refs.append((e["child_table"], col, f"{e['array_path']}.{tmap[col]}", r["to"], vals))
for table, col, field, to, vals in refs:
    vals = {v for v in vals if v is not None}
    parent = fk_parent(table, col) or snake(to)
    if parent in merged_root:
        found = {d["_id"] for d in db.get_collection(merged_root[parent]).find({"_id": {"$in": list(vals)}}, {"_id": 1})}
        where = f"{TARGET_DB}.{merged_root[parent]}._id (merged wave {table_wave[parent]}, {coll_meta[merged_root[parent]]['batch']})"
    elif parent in merged_embed:
        c2, e2 = merged_embed[parent]
        idt = next(f["target"] for f in e2["child_fields"] if f["source"] == e2["key"]["source"][0])
        found = {d["v"] for d in db.get_collection(c2).aggregate(
            [{"$unwind": "$" + e2["array_path"]}, {"$project": {"v": f"${e2['array_path']}.{idt}"}}])} & vals
        where = f"{TARGET_DB}.{c2}.{e2['array_path']}.{idt} (merged wave {table_wave[parent]}, {coll_meta[c2]['batch']})"
    elif table_exists(parent):
        found = {r[0] for r in q(f"SELECT id FROM {parent} WHERE id = ANY(%s)", (list(vals),))}
        where = f"odoo_src.{parent} (PostgreSQL-resident, {'wave ' + str(table_wave[parent]) if parent in table_wave else 'framework table'})"
    else:
        probe(f"reference:{field}->{to}", "SKIP", reason=f"no FK parent table for {table}.{col}")
        continue
    dangling = sorted(vals - found)
    probe(f"reference:{field}->{to}", "PASS" if not dangling else "FAIL", fk_parent=parent, resolved_in=where,
          distinct_values=len(vals), dangling=dangling[:10])

# ---- 9. snapshot again: nothing changed while probing ----
_, snap2 = raw_snapshot(COLL)
probe("stable_during_probe", "PASS" if snap2["raw_bson_sha256"] == snap["raw_bson_sha256"] else "FAIL", **snap2)

st = Counter(p["status"] for p in results["probes"])
results["summary"] = dict(st)
results["verdict"] = "PASS" if st.get("FAIL", 0) == 0 else "FAIL"
json.dump(results, open(OUT, "w"), indent=1, default=str)
print("PROBE VERDICT", UNIT, results["verdict"], dict(st))
sys.exit(0 if results["verdict"] == "PASS" else 1)
