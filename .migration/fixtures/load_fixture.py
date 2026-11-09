#!/usr/bin/env python3
"""Load the shared synthetic fixture into the allowlisted local database only."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path

from bson import json_util
from pymongo import MongoClient
from pymongo.uri_parser import parse_uri

fixtureDir = Path(__file__).resolve().parent
repoRoot = fixtureDir.parents[1]
databaseName = "odoo_unt16"


def localUri():
    uri = os.environ.get("MONGO_LOCAL_URI", "mongodb://localhost:27017")
    if not uri.startswith("mongodb://"):
        raise ValueError("Only mongodb:// loopback URIs are allowed")
    parsed = parse_uri(uri)
    if not parsed["nodelist"] or any(host not in {"localhost", "127.0.0.1"}
                                       for host, _ in parsed["nodelist"]):
        raise ValueError("Only localhost/127.0.0.1 MongoDB hosts are allowed")
    if parsed["database"] not in {None, databaseName}:
        raise ValueError("URI database must be odoo_unt16")
    return uri


def load(args):
    uri = localUri()
    allowed = json.loads((repoRoot / ".migration/allowed_targets.json").read_text())
    if databaseName not in allowed["databases"]:
        raise ValueError("odoo_unt16 is not allowlisted")
    specPath = repoRoot / ".migration/mapping_spec.json"
    spec = json.loads(specPath.read_text())
    manifest = json.loads(args.manifest.read_text())
    if manifest["spec_version"] != spec["version"] or manifest["spec_sha256"] != hashlib.sha256(specPath.read_bytes()).hexdigest():
        raise ValueError("Fixture is stale: rebuild against the current spec")
    selected = set(args.collections.split(",")) if args.collections else set(manifest["row_counts"])
    if not selected or selected - set(manifest["row_counts"]):
        raise ValueError("Empty selection or collections absent from manifest")
    collectionSpecs = {c["collection"]: c for c in spec["collections"]}
    prepared = {}
    for name in sorted(selected):
        entry = manifest["files"][name]
        path = (args.manifest.parent / entry["path"]).resolve()
        if not path.is_relative_to(args.manifest.parent.resolve()):
            raise ValueError("Fixture file escapes manifest directory")
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError(f"Fixture checksum mismatch: {name}")
        with gzip.open(path, "rt") as stream:
            documents = [json_util.loads(line) for line in stream if line.strip()]
        if len(documents) != manifest["row_counts"][name]:
            raise ValueError(f"Fixture count mismatch before load: {name}")
        prepared[name] = documents
    # Direct connection prevents a local seed from discovering remote replica members.
    with MongoClient(uri, directConnection=True, serverSelectionTimeoutMS=5000) as client:
        database = client[databaseName]
        for name, documents in prepared.items():
            database.drop_collection(name)
            collection = database.create_collection(name)
            if documents:
                collection.insert_many(documents)
            for index in collectionSpecs[name]["indexes"]:
                options = {key: index[key] for key in ("unique", "sparse", "partialFilterExpression", "name", "expireAfterSeconds") if key in index}
                collection.create_index([tuple(key) for key in index["keys"]], **options)
            actual = collection.count_documents({})
            expected = manifest["row_counts"][name]
            if actual != expected:
                raise ValueError(f"Loaded count mismatch: {name}: {actual} != {expected}")
            print(f"{name}: actual={actual} expected={expected} MATCH")
    print(f"ALL MATCH: {len(prepared)} collections, {sum(len(d) for d in prepared.values())} documents")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=fixtureDir / "fixture_manifest.json")
    parser.add_argument("--collections")
    args = parser.parse_args()
    try:
        load(args)
    except ValueError as error:
        parser.exit(1, f"fixture load refused: {error}\n")


if __name__ == "__main__":
    main()
