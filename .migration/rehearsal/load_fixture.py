#!/usr/bin/env python3
"""s3.1 local rehearsal: load the recon fixture into a local MongoDB exactly as the
mapping spec says (one document per root row, embeds keyed by parent_key)
and measure what the sign-off pack needs: documents per collection, the largest BSON
document against 16 MB, and the longest array per embed. Read-only on PostgreSQL.
Fixture-only: a load here proves the load path, never parity (AGENTS.md rule 4).

  /home/ubuntu/.venvs/recon/bin/python .migration/rehearsal/load_fixture.py \
      --spec .migration/mapping_spec.json --source-dsn-secret FIXTURE_RO_DSN \
      --target-uri-secret MONGO_LOCAL_URI --target-db odoo_unt15 \
      --out .migration/rehearsal/rehearsal.json \
      --samples-out .migration/rehearsal_samples.json

  export FIXTURE_RO_DSN="$(python3 -c 'import json,os;d=json.loads(os.environ["ODOO_PG_RO_DSN"]);d["database"]="odoo_fixture";print(json.dumps(d))')" MONGO_LOCAL_URI=mongodb://localhost:27017 && \
  PYTHONPATH=/home/ubuntu/plugin-pin/skills/mongo-recon-harness/harness \
  /home/ubuntu/.venvs/recon/bin/python .migration/rehearsal/load_fixture.py \
      --spec .migration/mapping_spec.json --source-dsn-secret FIXTURE_RO_DSN \
      --target-uri-secret MONGO_LOCAL_URI --target-db odoo_unt15 \
      --out .migration/rehearsal/rehearsal.json \
      --samples-out .migration/rehearsal_samples.json
"""
import argparse
import datetime as dt
import decimal
import json
import os
import pathlib
import sys
import time
import uuid
from collections import defaultdict

import bson
import psycopg
from bson import json_util
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
        pairs = [(target, to_bson(row[pos[sources[0]]]))]
    else:
        pairs = [(t, to_bson(row[pos[s]])) for s, t in zip(sources, target)]
    return {name: value for name, value in pairs if value is not None}


def percentile(values, pct):
    if not values:
        return 0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(round(pct / 100 * (len(ordered) - 1))))]


def _reference_fields(coll):
    mapped = {f["source"]: f["target"] for f in coll.get("fields", [])}
    key = coll.get("key") or {}
    targets = key.get("target")
    targets = [targets] if isinstance(targets, str) else list(targets or [])
    mapped.update(zip(key.get("source", []), targets))
    fields = []
    for ref in (coll.get("decision") or {}).get("references", []):
        columns = ref.get("column") or []
        columns = [columns] if isinstance(columns, str) else columns
        fields.append([mapped.get(column, column) for column in columns])
    return fields


def _path_value(doc, path):
    value = doc
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def _set_path(doc, path, value):
    parts = path.split(".")
    for part in parts[:-1]:
        doc = doc.setdefault(part, {})
    doc[parts[-1]] = value


def _sample_score(coll, doc):
    populated_refs = sum(
        all(doc.get(field) is not None for field in fields)
        for fields in _reference_fields(coll))
    arrays = [_path_value(doc, emb["array_path"]) for emb in coll.get("embeds", [])]
    populated_arrays = sum(bool(value) for value in arrays)
    array_elements = sum(len(value) for value in arrays if isinstance(value, (list, dict)))
    return populated_arrays + populated_refs, populated_arrays, populated_refs, array_elements


def _relaxed_json_value(value):
    return json.loads(json_util.dumps(value, json_options=json_util.RELAXED_JSON_OPTIONS))


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
            value = to_bson(row[pos[f["source"]]])
            if value is not None:
                doc[f["target"]] = value
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
                value = to_bson(erow[epos[f["source"]]])
                if value is not None:
                    element[f["target"]] = value
            grouped[doc_key].append(element)
        lengths = [len(v) for v in grouped.values()] + [0] * (len(docs) - len(grouped))
        for doc_key, doc in docs.items():
            elements = grouped.get(doc_key, [])
            if emb.get("shape") == "subdocument":
                if len(elements) > 1:
                    raise ValueError(
                        f"{coll['collection']}.{emb['array_path']} is a subdocument "
                        f"but parent {doc_key!r} has {len(elements)} children")
                if elements:
                    _set_path(doc, emb["array_path"], elements[0])
            else:
                _set_path(doc, emb["array_path"], elements)
        embed_stats.append({
            "array_path": emb["array_path"], "child_table": emb["child_table"],
            "child_rows": len(erows), "embedded": sum(len(v) for v in grouped.values()),
            "skipped_no_parent": skipped, "p50": percentile(lengths, 50),
            "p99": percentile(lengths, 99), "max": max(lengths, default=0)})
    db.drop_collection(coll["collection"])
    target = db[coll["collection"]]
    for doc in docs.values():
        doc.setdefault("_id", bson.ObjectId())
    doc_sizes = [(doc, len(bson.encode(doc))) for doc in docs.values()]
    sizes = [size for _, size in doc_sizes]
    largest_doc, largest_doc_bytes = max(doc_sizes, key=lambda item: item[1], default=(None, 0))
    if docs:
        target.insert_many(list(docs.values()), ordered=True)
    loaded_documents = target.count_documents({})
    created, failed = 0, []
    for ix in coll.get("indexes", []):
        keys = ix.get("keys")
        if isinstance(keys, list) and keys:
            spec = [(k[0], k[1]) if isinstance(k, list) else (k, 1) for k in keys]
            if spec == [("_id", 1)]:
                continue
            try:
                options = {"unique": bool(ix.get("unique"))}
                if ix.get("unique"):
                    exists = {path: {"$exists": True} for path, _ in spec}
                    spec_filter = ix.get("partialFilterExpression")
                    options["partialFilterExpression"] = (
                        {"$and": [exists, spec_filter]} if spec_filter else exists)
                elif "partialFilterExpression" in ix:
                    options["partialFilterExpression"] = ix["partialFilterExpression"]
                target.create_index(spec, **options)
                created += 1
            except OperationFailure as exc:  # e.g. code 67: more than 64 indexes
                failed.append({"keys": spec, "code": exc.code,
                               "error": str((exc.details or {}).get("errmsg", exc))})
    report.append({
        "collection": coll["collection"], "root_table": root,
        "source_root_rows": len(rows), "documents": loaded_documents,
        "root_row_count_match": len(rows) == loaded_documents,
        "max_doc_bytes": max(sizes, default=0), "limit_bytes": MAX_BSON,
        "max_doc_pct_of_limit": round(100 * max(sizes, default=0) / MAX_BSON, 4),
        "max_doc_within_16mb": max(sizes, default=0) <= MAX_BSON,
        "largest_document_id": _relaxed_json_value(largest_doc.get("_id")) if largest_doc else None,
        "p50_doc_bytes": percentile(sizes, 50),
        "indexes_in_spec": len(coll.get("indexes", [])), "indexes_created": created,
        "indexes_failed": failed, "embeds": embed_stats})
    return max(docs.values(), key=lambda doc: _sample_score(coll, doc), default=None)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spec", required=True)
    ap.add_argument("--source-dsn-secret", required=True, help="ENV VAR NAME of the fixture DSN (JSON)")
    ap.add_argument("--target-uri-secret", required=True, help="ENV VAR NAME of the local MongoDB URI")
    ap.add_argument("--target-db", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--samples-out", required=True)
    a = ap.parse_args()
    started_at = time.perf_counter()
    spec = json.load(open(a.spec))
    uri = os.environ[a.target_uri_secret]
    if not (uri.startswith("mongodb://127.0.0.1") or uri.startswith("mongodb://localhost")):
        sys.exit("rehearsal target must be the local container (mongodb://127.0.0.1 or localhost)")
    params = parse_postgresql_secret(os.environ[a.source_dsn_secret])
    client = MongoClient(uri)
    db = client[a.target_db]
    report = []
    samples = {}
    with psycopg.connect(**params) as conn:
        conn.read_only = True
        with conn.cursor() as cur:
            for coll in spec["collections"]:
                sample = load_collection(cur, db, coll, report)
                if sample is not None:
                    samples[coll["collection"]] = sample
    largest = max(report, key=lambda r: r["max_doc_bytes"], default=None)
    arrays = [{"collection": r["collection"], "array_path": e["array_path"],
               "child_table": e["child_table"], "length": e["max"]}
              for r in report for e in r["embeds"]]
    longest = max(arrays, key=lambda e: e["length"], default=None)
    top_arrays = sorted(arrays, key=lambda e: e["length"], reverse=True)[:10]
    result = {
        "spec_version": spec["version"], "spec_file": a.spec, "target_db": a.target_db,
        "target_class": "local", "source_database": params["dbname"],
        "samples_file": a.samples_out,
        "wall_time_seconds": round(time.perf_counter() - started_at, 3),
        "collections": len(report), "documents": sum(r["documents"] for r in report),
        "root_row_count_matches": sum(r["root_row_count_match"] for r in report),
        "root_row_count_mismatches": [r["collection"] for r in report if not r["root_row_count_match"]],
        "indexes_in_spec": sum(r["indexes_in_spec"] for r in report),
        "indexes_created": sum(r["indexes_created"] for r in report),
        "indexes_failed": sum(len(r["indexes_failed"]) for r in report),
        "largest_document": {"collection": largest["collection"],
                             "_id": largest["largest_document_id"],
                             "bytes": largest["max_doc_bytes"],
                             "limit_bytes": MAX_BSON,
                             "pct_of_limit": round(100 * largest["max_doc_bytes"] / MAX_BSON, 4)} if largest else None,
        "longest_array": longest,
        "top_10_longest_arrays": top_arrays,
        "per_collection": report,
    }
    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.samples_out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w") as fh:
        json.dump(result, fh, indent=1)
        fh.write("\n")
    pathlib.Path(a.samples_out).write_text(json_util.dumps(
        samples, json_options=json_util.RELAXED_JSON_OPTIONS, indent=2) + "\n")
    print(f"rehearsal {spec['version']}: {len(report)} collections, {result['documents']} documents, "
          f"indexes {result['indexes_created']}/{result['indexes_in_spec']} created "
          f"({result['indexes_failed']} refused), largest {result['largest_document']}, "
          f"longest array {result['longest_array']}, wall time {result['wall_time_seconds']}s")


if __name__ == "__main__":
    main()
