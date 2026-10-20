#!/usr/bin/env python3
"""s3.1 local rehearsal: load the recon fixture into a local MongoDB exactly as the
mapping spec says (one document per root row, embeds as arrays keyed by parent_key)
and measure what the sign-off pack needs: documents per collection, the largest BSON
document against 16 MB, and the longest array per embed. Read-only on PostgreSQL.
Fixture-only: a load here proves the load path, never parity (AGENTS.md rule 4).

  /home/ubuntu/.venvs/recon/bin/python .migration/rehearsal/load_fixture.py \
      --spec .migration/mapping_spec.json --source-dsn-secret ODOO_PG_FIXTURE_DSN \
      --target-uri-secret MONGO_LOCAL_URI --target-db odoo_unt12 \
      --out .migration/rehearsal/rehearsal.json
"""
import argparse
import datetime as dt
import decimal
import json
import os
import sys
import uuid
from collections import defaultdict

import bson
import psycopg
from bson.decimal128 import Decimal128
from pymongo import MongoClient
from pymongo.errors import OperationFailure
from recon.adapters import parse_postgresql_secret

MAX_BSON = 16 * 1024 * 1024


def to_bson(value):
    if isinstance(value, decimal.Decimal):
        return Decimal128(value)
    if isinstance(value, dt.datetime):
        return value
    if isinstance(value, dt.date):
        return dt.datetime(value.year, value.month, value.day)
    if isinstance(value, dt.time):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, memoryview):
        return bytes(value)
    return value


def q(name):
    return '"' + name + '"'


def fetch(cur, table, columns):
    cur.execute(f"SELECT {', '.join(q(c) for c in columns)} FROM {q(table)}")
    return cur.fetchall()


def key_doc(sources, target, row, pos):
    if isinstance(target, str):
        return {target: to_bson(row[pos[sources[0]]])}
    return {t: to_bson(row[pos[s]]) for s, t in zip(sources, target)}


def percentile(values, pct):
    if not values:
        return 0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(round(pct / 100 * (len(ordered) - 1))))]


def load_collection(cur, db, coll, report):
    root = coll["root_table"]
    key_src = coll["key"]["source"]
    fields = coll["fields"]
    columns = list(dict.fromkeys([*key_src, *(f["source"] for f in fields)]))
    rows = fetch(cur, root, columns)
    pos = {c: i for i, c in enumerate(columns)}
    docs = {}
    for row in rows:
        doc = key_doc(key_src, coll["key"]["target"], row, pos)
        for f in fields:
            doc[f["target"]] = to_bson(row[pos[f["source"]]])
        docs[tuple(row[pos[c]] for c in key_src)] = doc
    embed_stats = []
    for emb in coll.get("embeds", []):
        parent_ref, parent_key = emb["parent_ref"], emb["parent_key"]
        elem_key_src = emb["key"]["source"]
        efields = emb["fields"]
        ecols = list(dict.fromkeys([*parent_key, *elem_key_src, *(f["source"] for f in efields)]))
        erows = fetch(cur, emb["child_table"], ecols)
        epos = {c: i for i, c in enumerate(ecols)}
        if parent_ref != key_src:
            ref_pos = [pos[c] for c in parent_ref]
            by_parent = {tuple(row[i] for i in ref_pos): key for key, row in zip(docs, rows)}
        else:
            by_parent = None
        grouped = defaultdict(list)
        skipped = 0
        for erow in erows:
            parent = tuple(erow[epos[c]] for c in parent_key)
            if any(v is None for v in parent):
                skipped += 1
                continue
            doc_key = by_parent.get(parent) if by_parent is not None else parent
            if doc_key not in docs:
                skipped += 1
                continue
            element = key_doc(elem_key_src, emb["key"]["target"], erow, epos)
            for f in efields:
                element[f["target"]] = to_bson(erow[epos[f["source"]]])
            grouped[doc_key].append(element)
        lengths = [len(v) for v in grouped.values()] + [0] * (len(docs) - len(grouped))
        for doc_key, doc in docs.items():
            doc[emb["array_path"]] = grouped.get(doc_key, [])
        embed_stats.append({
            "array_path": emb["array_path"], "child_table": emb["child_table"],
            "child_rows": len(erows), "embedded": sum(len(v) for v in grouped.values()),
            "skipped_no_parent": skipped, "p50": percentile(lengths, 50),
            "p99": percentile(lengths, 99), "max": max(lengths, default=0)})
    db.drop_collection(coll["collection"])
    target = db[coll["collection"]]
    sizes = [len(bson.encode(d)) for d in docs.values()]
    if docs:
        target.insert_many(list(docs.values()), ordered=True)
    created, failed = 0, []
    for ix in coll.get("indexes", []):
        keys = ix.get("keys")
        if isinstance(keys, list) and keys:
            spec = [(k[0], k[1]) if isinstance(k, list) else (k, 1) for k in keys]
            if spec == [("_id", 1)]:
                continue
            try:
                target.create_index(spec, unique=bool(ix.get("unique")))
                created += 1
            except OperationFailure as exc:  # e.g. code 67: more than 64 indexes
                failed.append({"keys": spec, "code": exc.code,
                               "error": str((exc.details or {}).get("errmsg", exc))})
    report.append({
        "collection": coll["collection"], "root_table": root, "documents": len(docs),
        "max_doc_bytes": max(sizes, default=0), "p50_doc_bytes": percentile(sizes, 50),
        "indexes_in_spec": len(coll.get("indexes", [])), "indexes_created": created,
        "indexes_failed": failed, "embeds": embed_stats})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spec", required=True)
    ap.add_argument("--source-dsn-secret", required=True, help="ENV VAR NAME of the fixture DSN (JSON)")
    ap.add_argument("--target-uri-secret", required=True, help="ENV VAR NAME of the local MongoDB URI")
    ap.add_argument("--target-db", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    spec = json.load(open(a.spec))
    uri = os.environ[a.target_uri_secret]
    if not (uri.startswith("mongodb://127.0.0.1") or uri.startswith("mongodb://localhost")):
        sys.exit("rehearsal target must be the local container (mongodb://127.0.0.1 or localhost)")
    params = parse_postgresql_secret(os.environ[a.source_dsn_secret])
    client = MongoClient(uri)
    db = client[a.target_db]
    report = []
    with psycopg.connect(**params) as conn:
        conn.read_only = True
        with conn.cursor() as cur:
            for coll in spec["collections"]:
                load_collection(cur, db, coll, report)
    largest = max(report, key=lambda r: r["max_doc_bytes"], default=None)
    longest = max((dict(e, collection=r["collection"]) for r in report for e in r["embeds"]),
                  key=lambda e: e["max"], default=None)
    result = {
        "spec_version": spec["version"], "spec_file": a.spec, "target_db": a.target_db,
        "target_class": "local", "source_database": params["dbname"],
        "collections": len(report), "documents": sum(r["documents"] for r in report),
        "indexes_in_spec": sum(r["indexes_in_spec"] for r in report),
        "indexes_created": sum(r["indexes_created"] for r in report),
        "indexes_failed": sum(len(r["indexes_failed"]) for r in report),
        "largest_document": {"collection": largest["collection"], "bytes": largest["max_doc_bytes"],
                             "limit_bytes": MAX_BSON,
                             "pct_of_limit": round(100 * largest["max_doc_bytes"] / MAX_BSON, 4)} if largest else None,
        "longest_array": {k: longest[k] for k in ("collection", "array_path", "child_table", "max")} if longest else None,
        "per_collection": report,
    }
    with open(a.out, "w") as fh:
        json.dump(result, fh, indent=1)
        fh.write("\n")
    print(f"rehearsal {spec['version']}: {len(report)} collections, {result['documents']} documents, "
          f"indexes {result['indexes_created']}/{result['indexes_in_spec']} created "
          f"({result['indexes_failed']} refused), largest {result['largest_document']}, "
          f"longest array {result['longest_array']}")


if __name__ == "__main__":
    main()
