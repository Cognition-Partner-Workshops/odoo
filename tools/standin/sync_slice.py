#!/usr/bin/env python3
"""CDC stand-in: copy one slice collection from the stand-in clone to the local MongoDB.

Reads odoo_unt16_prod (never odoo_src) as the read-only role named by the DSN secret, builds
documents from the mapping_spec entry, and upserts them by _id into the local odoo_unt16.
--since copies only rows whose write_date is at or after the given UTC timestamp. The real
CDC transport is customer-run; this exists so the stand-in's reads position has data.

Usage: sync_slice.py --collection accountAccount [--since 2026-11-10T00:00:00] [--dsn-secret ODOO_PG_RO_DSN]
"""
import argparse
import json
import os
import sys
from pathlib import Path

import psycopg2
import psycopg2.extras
from psycopg2.extensions import parse_dsn
from pymongo import MongoClient, ReplaceOne
from pymongo.uri_parser import parse_uri

sys.path.insert(0, str(Path(__file__).resolve().parent / "addons" / "standin_switch"))
import slice_docs  # noqa: E402

cloneName = "odoo_unt16_prod"
databaseName = "odoo_unt16"


def localUri():
    uri = os.environ.get("MONGO_LOCAL_URI", "mongodb://localhost:27017")
    hosts = parse_uri(uri)["nodelist"]
    if not hosts or any(host not in {"localhost", "127.0.0.1"} for host, _ in hosts):
        raise SystemExit("sync_slice writes only to a localhost MongoDB")
    return uri


def sourceConnection(secretName):
    raw = os.environ[secretName]
    params = json.loads(raw) if raw.lstrip().startswith("{") else parse_dsn(raw)
    params = {k: v for k, v in params.items() if k in {"user", "password", "host", "port"}}
    conn = psycopg2.connect(dbname=cloneName, **params)
    conn.set_session(readonly=True)
    return conn


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--collection", required=True)
    parser.add_argument("--since")
    parser.add_argument("--dsn-secret", default="ODOO_PG_RO_DSN")
    args = parser.parse_args()
    entry = slice_docs.loadEntry(args.collection)
    root, key = entry["root_table"], entry["key"]["source"][0]
    with sourceConnection(args.dsn_secret) as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        where, params = ("WHERE write_date >= %s", [args.since]) if args.since else ("", [])
        cur.execute(f'SELECT * FROM "{root}" {where} ORDER BY "{key}"', params)
        rows = cur.fetchall()
        ids = [r[key] for r in rows]
        children = {}
        for embed in entry.get("embeds", []):
            parentCol = embed["parent_key"][0]
            cur.execute(f'SELECT * FROM "{embed["child_table"]}" WHERE "{parentCol}" = ANY(%s)', [ids])
            for child in cur.fetchall():
                children.setdefault(child[parentCol], {}).setdefault(embed["array_path"], []).append(child)
    docs = [slice_docs.buildDocument(entry, row, children.get(row[key], {})) for row in rows]
    coll = MongoClient(localUri(), tz_aware=True)[databaseName][entry["collection"]]
    if docs:
        coll.bulk_write([ReplaceOne({"_id": d["_id"]}, d, upsert=True) for d in docs])
    print(json.dumps({"collection": entry["collection"], "source": cloneName, "since": args.since,
                      "rows": len(docs), "target_docs": coll.estimated_document_count()}))


if __name__ == "__main__":
    main()
