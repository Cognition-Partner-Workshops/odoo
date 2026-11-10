#!/usr/bin/env python3
"""STAND-IN relay: tail the local MongoDB slice and apply each change back to the clone.

There is no customer production: odoo_unt16_prod is the stand-in clone and the real reverse
CDC transport is customer-run. This relay exists so the stand-in's writes position has a way
back to PostgreSQL for the rehearsal.

The slice's namespaces come from .migration/slices/<slice>.json -> units.json (collections and
tables) -> mapping_spec.json (root and embedded tables); a mismatch between them is refused.
Each batch of change events is applied to odoo_unt16_prod in one PostgreSQL transaction that
also records every event in standin_relay_ledger and moves standin_relay_checkpoint (resume
token + last applied cluster time). The relay stops on the first error and never skips an
event; on restart it resumes after the committed checkpoint. It connects as the clone's
writer (the OS user over the 5433 socket, as the stand-in Odoo does) and refuses any other
database or the read-only role.

The change stream needs a replica set and changeStreamPreAndPostImages on each collection
(fullDocument=required, so every event carries the exact post-image).

Usage (Odoo venv python):
  relay.py init                       enable post-images on the slice collections, create tables
  relay.py run [--start-now | --start-at T,I] [--batch 50] [--apply-delay S]
  relay.py stop                       SIGTERM the running relay; it commits the open batch, exits
  relay.py status                     checkpoint, ledger count, events pending after it
  relay.py verify                     ledger vs change-stream replay: duplicates, gaps, order
  relay.py recon --plugin-worktree DIR [--out DIR]
                                      recon harness (target_class local) at the checkpoint
MongoDB URI: $STANDIN_MONGO_URI (localhost only, e.g. mongodb://localhost:27018/?directConnection=true).
"""
import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
import psycopg2.extras
from bson import Timestamp, json_util
from psycopg2.extensions import parse_dsn
from pymongo import MongoClient
from pymongo.uri_parser import parse_uri

here = Path(__file__).resolve().parent
repoRoot = here.parents[1]
sys.path.insert(0, str(here / "addons" / "standin_switch"))
import slice_docs  # noqa: E402

cloneName = "odoo_unt16_prod"
databaseName = "odoo_unt16"
roSecret = "ODOO_PG_RO_DSN"
runDir = Path(os.environ.get("STANDIN_RUN_DIR", "~/standin-run")).expanduser()
pidFile = runDir / "relay.pid"


def livePid():
    try:
        pid = int(pidFile.read_text())
        os.kill(pid, 0)
        return pid
    except (FileNotFoundError, ValueError, ProcessLookupError):
        return None
applyOps = ("insert", "replace", "update", "delete")

schemaSql = """
CREATE TABLE IF NOT EXISTS standin_relay_checkpoint (
    relay text PRIMARY KEY,
    resume_token jsonb,
    cluster_time_t bigint, cluster_time_i bigint,
    started_t bigint NOT NULL, started_i bigint NOT NULL,
    events bigint NOT NULL DEFAULT 0, batches bigint NOT NULL DEFAULT 0,
    updated_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS standin_relay_ledger (
    relay text NOT NULL, token text NOT NULL,
    cluster_time_t bigint NOT NULL, cluster_time_i bigint NOT NULL,
    ns text NOT NULL, op text NOT NULL, doc_id bigint NOT NULL, batch bigint NOT NULL,
    applied_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (relay, token));
"""


def log(event, **fields):
    print(json.dumps({"ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                      "event": event, **fields}, default=str), flush=True)


# ---- slice
def loadSlice(sliceName):
    sliceSpec = json.loads((repoRoot / ".migration" / "slices" / f"{sliceName}.json").read_text())
    units = {u["id"]: u for u in json.loads((repoRoot / ".migration" / "units.json").read_text())["units"]}
    entries, unitTables = [], set()
    for unitId in sliceSpec["units"]:
        unit = units[unitId]
        unitTables |= set(unit["tables"])
        for target in unit["write_targets"]:
            db, _, coll = target.partition(".")
            if db != databaseName or coll not in unit["collections"]:
                raise SystemExit(f"unit {unitId}: write target {target} is outside {databaseName}")
        entries += [slice_docs.loadEntry(c) for c in unit["collections"]]
    specTables = {e["root_table"] for e in entries} | {m["child_table"] for e in entries for m in e.get("embeds", [])}
    if not set(sliceSpec["tables"]) == unitTables == specTables:
        raise SystemExit(f"slice {sliceName}: tables disagree: slice {sorted(sliceSpec['tables'])}, "
                         f"units {sorted(unitTables)}, mapping {sorted(specTables)}")
    return {e["collection"]: e for e in entries}


# ---- connections
def mongoClient():
    uri = os.environ.get("STANDIN_MONGO_URI")
    if not uri:
        raise SystemExit("set STANDIN_MONGO_URI to the local replica set (a change stream needs one)")
    hosts = parse_uri(uri)["nodelist"]
    if not hosts or any(host not in {"localhost", "127.0.0.1"} for host, _ in hosts):
        raise SystemExit("relay reads only a localhost MongoDB")
    return MongoClient(uri, tz_aware=True)


def roUser():
    raw = os.environ.get(roSecret)
    if not raw:
        return None
    return (json.loads(raw) if raw.lstrip().startswith("{") else parse_dsn(raw)).get("user")


def cloneConnection():
    conn = psycopg2.connect(dbname=cloneName, host="/var/run/postgresql", port=5433)
    with conn.cursor() as cur:
        cur.execute("SELECT current_database(), current_user, current_setting('transaction_read_only')")
        dbName, user, readOnly = cur.fetchone()
    if dbName != cloneName or user == roUser() or readOnly == "on":
        raise SystemExit(f"relay must run as the clone's writer on {cloneName}, got {user}@{dbName}")
    conn.rollback()
    return conn


# ---- document -> rows
def fromBson(value, bsonType, where):
    if value is None:
        return None
    if bsonType == "object":
        return psycopg2.extras.Json(value)
    if bsonType == "date":
        if not isinstance(value, datetime):
            raise TypeError(f"{where}: expected a date, got {type(value).__name__}")
        return value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value
    expected = {"int": int, "bool": bool, "string": str}.get(bsonType)
    if expected is None:
        raise TypeError(f"{where}: unsupported bson_type {bsonType}")
    if not isinstance(value, expected) or (expected is int and isinstance(value, bool)):
        raise TypeError(f"{where}: expected {bsonType}, got {type(value).__name__}")
    return value


def applyDocument(cur, entry, doc):
    root, keyColumn = entry["root_table"], entry["key"]["source"][0]
    known = {"_id"} | {f["target"] for f in entry["fields"]} | {m["array_path"] for m in entry.get("embeds", [])}
    unknown = sorted(set(doc) - known)
    if unknown:
        raise ValueError(f"{entry['collection']} {doc.get('_id')}: fields not in the mapping: {unknown}")
    docId = fromBson(doc["_id"], "int", "_id")
    columns = [keyColumn] + [f["source"] for f in entry["fields"]]
    values = [docId] + [fromBson(doc.get(f["target"]), f["bson_type"], f["target"]) for f in entry["fields"]]
    updates = ", ".join(f'"{c}" = EXCLUDED."{c}"' for c in columns[1:])
    cur.execute(f'INSERT INTO "{root}" ({", ".join(chr(34) + c + chr(34) for c in columns)}) '
                f'VALUES ({", ".join(["%s"] * len(columns))}) ON CONFLICT ("{keyColumn}") DO UPDATE SET {updates}',
                values)
    for embed in entry.get("embeds", []):
        parentColumn, childFields = embed["parent_key"][0], embed["child_fields"]
        cur.execute(f'DELETE FROM "{embed["child_table"]}" WHERE "{parentColumn}" = %s', [docId])
        elements = doc.get(embed["array_path"]) or []
        rows = []
        for elem in elements:
            if set(elem) != {f["target"] for f in childFields}:
                raise ValueError(f"{entry['collection']} {docId}.{embed['array_path']}: element keys {sorted(elem)}")
            rows.append([docId] + [fromBson(elem[f["target"]], f["bson_type"], embed["array_path"]) for f in childFields])
        if rows:
            cols = ", ".join(f'"{c}"' for c in [parentColumn] + [f["source"] for f in childFields])
            psycopg2.extras.execute_values(cur, f'INSERT INTO "{embed["child_table"]}" ({cols}) VALUES %s', rows)
    return docId


def removeDocument(cur, entry, docId):
    docId = fromBson(docId, "int", "_id")
    for embed in entry.get("embeds", []):
        cur.execute(f'DELETE FROM "{embed["child_table"]}" WHERE "{embed["parent_key"][0]}" = %s', [docId])
    cur.execute(f'DELETE FROM "{entry["root_table"]}" WHERE "{entry["key"]["source"][0]}" = %s', [docId])
    if cur.rowcount != 1:
        raise ValueError(f"{entry['collection']} delete {docId}: {cur.rowcount} rows in {entry['root_table']}")
    return docId


def bumpSequences(cur, entries):
    for entry in entries.values():
        root, key = entry["root_table"], entry["key"]["source"][0]
        cur.execute("SELECT pg_get_serial_sequence(%s, %s)", [root, key])
        seq = cur.fetchone()[0]
        if seq:
            cur.execute(f'SELECT setval(%s, GREATEST((SELECT COALESCE(max("{key}"), 1) FROM "{root}"), '
                        f'(SELECT last_value FROM {seq})))', [seq])


# ---- checkpoint
def readCheckpoint(cur, relayName):
    cur.execute("SELECT resume_token, cluster_time_t, cluster_time_i, started_t, started_i, events, batches "
                "FROM standin_relay_checkpoint WHERE relay = %s", [relayName])
    row = cur.fetchone()
    if not row:
        return None
    token, ctT, ctI, stT, stI, events, batches = row
    return {"resume_token": json_util.loads(json.dumps(token)) if token else None,
            "cluster_time": Timestamp(ctT, ctI) if ctT is not None else None,
            "started": Timestamp(stT, stI), "events": events, "batches": batches}


def watchArgs(checkpoint):
    if checkpoint["resume_token"]:
        return {"resume_after": checkpoint["resume_token"]}
    return {"start_at_operation_time": checkpoint["started"]}


def openStream(client, entries, maxAwaitMs=500, **kwargs):
    pipeline = [{"$match": {"ns.db": databaseName, "ns.coll": {"$in": sorted(entries)}}}]
    return client[databaseName].watch(pipeline, full_document="required", max_await_time_ms=maxAwaitMs, **kwargs)


def ts(value):
    return f"{value.time},{value.inc}" if value else None


# ---- commands
def cmdInit(args, entries):
    client = mongoClient()
    db = client[databaseName]
    existing = set(db.list_collection_names())
    for name in sorted(entries):
        if name not in existing:
            raise SystemExit(f"{databaseName}.{name} does not exist; load the slice first (sync_slice.py)")
        db.command("collMod", name, changeStreamPreAndPostImages={"enabled": True})
        for index in entries[name].get("indexes", []):
            db[name].create_index([tuple(k) for k in index["keys"]], unique=bool(index.get("unique")))
    conn = cloneConnection()
    with conn, conn.cursor() as cur:
        cur.execute(schemaSql)
    log("init", collections=sorted(entries), clone=cloneName,
        indexes={n: len(entries[n].get("indexes", [])) for n in sorted(entries)})


def cmdRun(args, entries):
    stopping = {"flag": False}
    signal.signal(signal.SIGTERM, lambda *_: stopping.update(flag=True))
    runDir.mkdir(parents=True, exist_ok=True)
    if livePid():
        raise SystemExit(f"relay already running as pid {livePid()}")
    pidFile.write_text(str(os.getpid()))
    client, conn = mongoClient(), cloneConnection()
    with conn, conn.cursor() as cur:
        cur.execute(schemaSql)
        checkpoint = readCheckpoint(cur, args.relay)
        if checkpoint is None:
            if args.start_at:
                t, i = (int(x) for x in args.start_at.split(","))
                started = Timestamp(t, i)
            elif args.start_now:
                started = client[databaseName].command("ping")["operationTime"]
            else:
                raise SystemExit("no committed checkpoint: pass --start-now or --start-at T,I for the first run")
            cur.execute("INSERT INTO standin_relay_checkpoint (relay, started_t, started_i) VALUES (%s, %s, %s)",
                        [args.relay, started.time, started.inc])
            checkpoint = {"resume_token": None, "cluster_time": None, "started": started, "events": 0, "batches": 0}
    log("resume" if checkpoint["resume_token"] else "start", relay=args.relay, pid=os.getpid(),
        checkpoint_cluster_time=ts(checkpoint["cluster_time"]), started=ts(checkpoint["started"]),
        events=checkpoint["events"], batches=checkpoint["batches"])
    batchNo = checkpoint["batches"]
    with openStream(client, entries, **watchArgs(checkpoint)) as stream:
        while not stopping["flag"]:
            batch = []
            while len(batch) < args.batch:
                change = stream.try_next()
                if change is None:
                    break
                batch.append(change)
            if not batch:
                continue
            batchNo += 1
            try:
                with conn, conn.cursor() as cur:
                    for change in batch:
                        op, coll = change["operationType"], change.get("ns", {}).get("coll")
                        if op not in applyOps or coll not in entries:
                            raise ValueError(f"unsupported change {op} on {coll}")
                        if op == "delete":
                            docId = removeDocument(cur, entries[coll], change["documentKey"]["_id"])
                        else:
                            docId = applyDocument(cur, entries[coll], change["fullDocument"])
                        ct = change["clusterTime"]
                        cur.execute("INSERT INTO standin_relay_ledger (relay, token, cluster_time_t, cluster_time_i, "
                                    "ns, op, doc_id, batch) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                                    [args.relay, change["_id"]["_data"], ct.time, ct.inc,
                                     f"{databaseName}.{coll}", op, docId, batchNo])
                        if args.apply_delay:
                            time.sleep(args.apply_delay)
                    bumpSequences(cur, entries)
                    last = batch[-1]
                    cur.execute("UPDATE standin_relay_checkpoint SET resume_token = %s, cluster_time_t = %s, "
                                "cluster_time_i = %s, events = events + %s, batches = %s, updated_at = now() "
                                "WHERE relay = %s",
                                [psycopg2.extras.Json(json.loads(json_util.dumps(last["_id"]))), last["clusterTime"].time,
                                 last["clusterTime"].inc, len(batch), batchNo, args.relay])
            except Exception as exc:
                log("halt", batch=batchNo, error=f"{type(exc).__name__}: {exc}",
                    first_token=batch[0]["_id"]["_data"], note="batch rolled back; checkpoint unchanged")
                pidFile.unlink(missing_ok=True)
                return 1
            log("commit", batch=batchNo, events=len(batch), last_cluster_time=ts(batch[-1]["clusterTime"]),
                ops=[f"{c['operationType']}:{(c.get('documentKey') or {}).get('_id')}" for c in batch])
    pidFile.unlink(missing_ok=True)
    log("stopped", relay=args.relay, batches=batchNo)
    return 0


def cmdStop(args, entries):
    if not livePid():
        raise SystemExit("relay is not running")
    os.kill(int(pidFile.read_text()), signal.SIGTERM)
    log("stop-sent", pid=int(pidFile.read_text()))


def pendingAfter(client, entries, checkpoint, waitMs=1500):
    with openStream(client, entries, maxAwaitMs=waitMs, **watchArgs(checkpoint)) as stream:
        pending = []
        for _ in range(2):
            change = stream.try_next()
            while change is not None:
                pending.append(change["_id"]["_data"])
                change = stream.try_next()
        return pending


def cmdStatus(args, entries):
    client, conn = mongoClient(), cloneConnection()
    with conn, conn.cursor() as cur:
        checkpoint = readCheckpoint(cur, args.relay)
        cur.execute("SELECT count(*) FROM standin_relay_ledger WHERE relay = %s", [args.relay])
        ledger = cur.fetchone()[0]
    if checkpoint is None:
        raise SystemExit("no checkpoint")
    print(json.dumps({"relay": args.relay, "checkpoint_cluster_time": ts(checkpoint["cluster_time"]),
                      "events": checkpoint["events"], "batches": checkpoint["batches"], "ledger_rows": ledger,
                      "pending_after_checkpoint": len(pendingAfter(client, entries, checkpoint)),
                      "running": bool(livePid())}))


def cmdVerify(args, entries):
    client, conn = mongoClient(), cloneConnection()
    with conn, conn.cursor() as cur:
        checkpoint = readCheckpoint(cur, args.relay)
        cur.execute("SELECT token FROM standin_relay_ledger WHERE relay = %s ORDER BY cluster_time_t, cluster_time_i, token",
                    [args.relay])
        ledger = [r[0] for r in cur.fetchall()]
    if not checkpoint["resume_token"]:
        raise SystemExit("no committed checkpoint yet: nothing to verify")
    endToken = checkpoint["resume_token"]["_data"]
    stream = []
    with openStream(client, entries, maxAwaitMs=1000, start_at_operation_time=checkpoint["started"]) as cs:
        while not stream or stream[-1] != endToken:
            change = cs.try_next()
            if change is None:
                raise SystemExit(f"stream replay ended before the checkpoint token ({len(stream)} events)")
            stream.append(change["_id"]["_data"])
    result = {"relay": args.relay, "started": ts(checkpoint["started"]),
              "checkpoint_cluster_time": ts(checkpoint["cluster_time"]),
              "stream_events_to_checkpoint": len(stream), "ledger_rows": len(ledger),
              "duplicates": len(ledger) - len(set(ledger)),
              "missing_from_ledger": [t for t in stream if t not in set(ledger)],
              "not_in_stream": [t for t in ledger if t not in set(stream)],
              "same_order": ledger == stream}
    result["verdict"] = "PASS" if (result["same_order"] and not result["duplicates"]) else "FAIL"
    print(json.dumps(result, indent=2))
    return 0 if result["verdict"] == "PASS" else 1


def cmdRecon(args, entries):
    if livePid():
        raise SystemExit("stop the relay first (relay.py stop) so the checkpoint is fixed during recon")
    worktree = Path(args.plugin_worktree).expanduser().resolve()
    pin = (repoRoot / ".migration" / "plugin_sha").read_text().strip()
    head = subprocess.run(["git", "-C", str(worktree), "rev-parse", "HEAD"], check=True,
                          capture_output=True, text=True).stdout.strip()
    if head != pin:
        raise SystemExit(f"plugin worktree is at {head[:8]}, the pin is {pin[:8]}")
    client, conn = mongoClient(), cloneConnection()
    with conn, conn.cursor() as cur:
        checkpoint = readCheckpoint(cur, args.relay)
        cur.execute("SELECT current_user")
        writer = cur.fetchone()[0]
    if pendingAfter(client, entries, checkpoint):
        raise SystemExit("MongoDB has changes after the checkpoint; run the relay to catch up first")
    env = dict(os.environ, PYTHONPATH=str(worktree / "skills" / "mongo-recon-harness" / "harness"),
               STANDIN_RECON_PG_DSN=json.dumps({"user": writer, "password": "unused-peer-auth", "host": "/var/run/postgresql",
                                               "port": 5433, "database": cloneName}))
    out = Path(args.out or runDir / "recon" / f"ct-{checkpoint['cluster_time'].time}-{checkpoint['cluster_time'].inc}")
    cmd = [args.recon_python, "-m", "recon", "run", "--unit", ",".join(sorted(entries)), "--family", "postgresql",
           "--mapping", ".migration/mapping_spec.json", "--collections", ",".join(sorted(entries)),
           "--tolerances", ".migration/recon_tolerances.json",
           "--canonicalization", str(worktree / "skills" / "mongo-migration" / "profiles" / "postgresql.md"),
           "--mode", "live", "--target-class", "local",
           "--source-dsn-secret", "STANDIN_RECON_PG_DSN", "--target-uri-secret", "STANDIN_MONGO_URI",
           "--target-db", databaseName, "--allowed-targets-file", ".migration/allowed_targets.json",
           "--out", str(out)]
    log("recon", checkpoint_cluster_time=ts(checkpoint["cluster_time"]), plugin=pin[:8], out=str(out))
    code = subprocess.run(cmd, cwd=repoRoot, env=env).returncode
    after = pendingAfter(client, entries, checkpoint)
    log("recon-done", exit=code, checkpoint_cluster_time=ts(checkpoint["cluster_time"]),
        pending_after_checkpoint=len(after))
    return code if not after else 1


def main():
    parser = argparse.ArgumentParser(description="STAND-IN MongoDB -> odoo_unt16_prod relay")
    parser.add_argument("--slice", default="account_account")
    parser.add_argument("--relay", default="account_account")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    run = sub.add_parser("run")
    run.add_argument("--start-now", action="store_true")
    run.add_argument("--start-at", help="first run only: cluster time T,I to start from")
    run.add_argument("--batch", type=int, default=50)
    run.add_argument("--apply-delay", type=float, default=0, help="seconds per event inside the open transaction")
    sub.add_parser("stop")
    sub.add_parser("status")
    sub.add_parser("verify")
    recon = sub.add_parser("recon")
    recon.add_argument("--plugin-worktree", required=True)
    recon.add_argument("--recon-python", default="/home/ubuntu/.venvs/recon/bin/python")
    recon.add_argument("--out")
    args = parser.parse_args()
    entries = loadSlice(args.slice)
    commands = {"init": cmdInit, "run": cmdRun, "stop": cmdStop, "status": cmdStatus,
                "verify": cmdVerify, "recon": cmdRecon}
    sys.exit(commands[args.cmd](args, entries) or 0)


if __name__ == "__main__":
    main()
