"""Read-only verifier probes for w1-b01 (UNT14-39): accountLockException in odoo_unt13.

Reads the target collection (count, sha256 over raw BSON sorted by _id, max writeDate,
index keys, per-field null/missing/type rates, key sets) and the source table through the
read-only PostgreSQL role (row-by-row value spot check, reference resolution against
res_company / res_users, which stay in PostgreSQL). Prints one JSON object; exit 1 on problems.
"""
import datetime as dt
import hashlib
import json
import os
import sys
from decimal import Decimal

import psycopg
from bson import decode
from bson.codec_options import CodecOptions
from bson.raw_bson import RawBSONDocument
from pymongo import MongoClient

ROOT = os.environ.get("ROOT", ".")
COLL = "accountLockException"
spec = json.load(open(f"{ROOT}/.migration/mapping_spec.json"))
cspec = next(c for c in spec["collections"] if c["collection"] == COLL)
fields = cspec["fields"]
BSON_PY = {"int": (int,), "string": (str,), "date": (dt.datetime,), "bool": (bool,)}

client = MongoClient(os.environ["MONGODB_ATLAS_URI"], serverSelectionTimeoutMS=20000)
db = client.get_database("odoo_unt13")
raw_coll = db.get_collection(COLL, codec_options=CodecOptions(document_class=RawBSONDocument))
raws = list(raw_coll.find({}, sort=[("_id", 1)]))
docs = [decode(r.raw) for r in raws]
digest = hashlib.sha256(b"".join(r.raw for r in raws)).hexdigest()
max_wd = max((d.get("writeDate") for d in docs if d.get("writeDate")), default=None)
indexes = [[list(k) for k in ix["key"].items()] for ix in db.get_collection(COLL).list_indexes()]
problems = []

allowed_keys = {"_id"} | {f["target"] for f in fields}
field_stats = {}
for f in fields:
    t = f["target"]
    missing = sum(1 for d in docs if t not in d)
    nulls = sum(1 for d in docs if t in d and d[t] is None)
    bad_type = sum(1 for d in docs if d.get(t) is not None
                   and not (isinstance(d[t], BSON_PY[f["bson_type"]])
                            and not (f["bson_type"] == "int" and isinstance(d[t], bool))))
    field_stats[t] = {"missing": missing, "null": nulls, "bad_type": bad_type}
    if bad_type:
        problems.append(f"{t}: {bad_type} values not {f['bson_type']}")
    if nulls:
        problems.append(f"{t}: {nulls} explicit nulls (loader omits empty values)")
extra_keys = sorted({k for d in docs for k in d} - allowed_keys)
if extra_keys:
    problems.append(f"unmapped keys in documents: {extra_keys}")
ids = [d["_id"] for d in docs]
if len(ids) != len(set(ids)):
    problems.append("duplicate _id")

spec_ix = [ix["keys"] for ix in cspec["indexes"]]
live_ix = [ix for ix in indexes if ix != [["_id", 1]]]
missing_ix = [k for k in spec_ix if k not in live_ix]
extra_ix = [k for k in live_ix if k not in spec_ix]
if missing_ix or extra_ix:
    problems.append(f"index mismatch: missing {missing_ix} extra {extra_ix}")

kw = json.loads(os.environ["ODOO_PG_RO_DSN"])
kw["dbname"] = kw.pop("database")
with psycopg.connect(**kw) as conn:
    conn.read_only = True
    cur = conn.cursor()
    cols = [f["source"] for f in fields]
    cur.execute("SELECT id, " + ", ".join(cols) + " FROM account_lock_exception ORDER BY id")
    src = {r[0]: dict(zip(cols, r[1:])) for r in cur.fetchall()}
    cur.execute("SELECT id FROM res_company")
    companies = {r[0] for r in cur.fetchall()}
    cur.execute("SELECT id FROM res_users")
    users = {r[0] for r in cur.fetchall()}

def norm(v):
    if isinstance(v, dt.datetime):
        return v.replace(tzinfo=None, microsecond=v.microsecond // 1000 * 1000)
    if isinstance(v, dt.date):
        return dt.datetime(v.year, v.month, v.day)
    if isinstance(v, Decimal):
        return v
    if isinstance(v, str):
        return v.rstrip(" ")
    return v

value_mismatches = []
if set(src) != set(ids):
    problems.append(f"key sets differ: source-only {sorted(set(src) - set(ids))[:5]} target-only {sorted(set(ids) - set(src))[:5]}")
by_id = {d["_id"]: d for d in docs}
for k, row in src.items():
    d = by_id.get(k)
    if d is None:
        continue
    for f in fields:
        sv, tv = norm(row[f["source"]]), norm(d.get(f["target"]))
        if sv != tv:
            value_mismatches.append([k, f["target"]])
if value_mismatches:
    problems.append(f"{len(value_mismatches)} value mismatches, first {value_mismatches[:5]}")

refs = {}
for ref in cspec["decision"]["references"]:
    col = ref["column"][0]
    target = next(f["target"] for f in fields if f["source"] == col)
    pool = companies if ref["to"] == "resCompany" else users
    vals = [d[target] for d in docs if d.get(target) is not None]
    dangling = sorted({v for v in vals if v not in pool})
    refs[f"{target}->{ref['to']}"] = {"checked": len(vals), "dangling": dangling, "resolved_in": "PostgreSQL odoo_src"}
    if dangling:
        problems.append(f"{target}: dangling {dangling[:5]}")

out = {
    "label": os.environ.get("PROBE_LABEL", ""),
    "taken_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    "collection": f"odoo_unt13.{COLL}",
    "count": len(docs), "source_rows": len(src),
    "raw_bson_sha256": digest,
    "max_writeDate": max_wd.isoformat() if max_wd else None,
    "indexes": indexes, "spec_indexes_missing": missing_ix, "extra_indexes": extra_ix,
    "fields": field_stats, "extra_keys": extra_keys,
    "value_mismatches": len(value_mismatches),
    "references": refs, "problems": problems,
}
print(json.dumps(out, indent=1, default=str))
sys.exit(1 if problems else 0)
