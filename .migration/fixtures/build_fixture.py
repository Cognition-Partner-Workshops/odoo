#!/usr/bin/env python3
"""Build synthetic target documents without connecting to any source database."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
from pathlib import Path
import random
from itertools import product

from bson import Binary, Decimal128, json_util

fixtureDir = Path(__file__).resolve().parent
repoRoot = fixtureDir.parents[1]
pluginPin = "2f3873ab"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bounds(stat, size, outlier=False):
    if not size:
        return [], []
    values = stat["values"]
    p50, p99 = values["p50"], values["p99"]
    low = [0] * (math.ceil(size * .5) - 1)
    low += [p50] * (math.ceil(size * .99) - len(low) - 1)
    low += [p99] * (size - len(low))
    high = [p50] * math.ceil(size * .5)
    high += [p99] * (math.ceil(size * .99) - len(high))
    high += [stat.get("tail_limit", values["max"])] * (size - len(high))
    if outlier:
        low[-1] = high[-1] = values["max"]
    return low, high


def quantile(counts, fraction):
    return sorted(counts)[math.ceil(len(counts) * fraction) - 1]


def setPath(document, path, value):
    parts = path.split(".")
    for part in parts[:-1]:
        document = document.setdefault(part, {})
    document[parts[-1]] = value


def makeValue(kind, index, rng):
    values = {
        "int": index, "long": index, "double": index + .25,
        "decimal": Decimal128(str(index) + ".25"), "string": f"synthetic-{index}",
        "bool": bool(index % 2), "object": {"en_US": f"synthetic-{index}"},
        "array": [f"synthetic-{index}"], "binData": Binary(f"synthetic-{index}".encode()),
        "date": datetime(2024, 1, 1, tzinfo=timezone.utc),
    }
    if kind not in values:
        raise ValueError(f"Unsupported BSON type: {kind}")
    return values[kind]


def makeDocument(row, fields, key, rng, required):
    document = {}
    keyTargets = key["target"] if isinstance(key["target"], list) else [key["target"]]
    for source, target in zip(key["source"], keyTargets):
        setPath(document, target, row.get(source, row["id"]))
    for field in fields:
        source, target = field["source"], field["target"]
        if source in row:
            setPath(document, target, row[source])
        elif "null_missing_equiv" in field.get("rules", []) and target not in required:
            choice = rng.randrange(5)
            if choice == 0:
                continue
            setPath(document, target, None if choice == 1 else makeValue(field["bson_type"], row["id"], rng))
        else:
            setPath(document, target, makeValue(field["bson_type"], row["id"], rng))
    return document


def getPath(document, path):
    for part in path.split("."):
        if not isinstance(document, dict):
            return None
        document = document.get(part)
    return document


def repairUnique(documents, collection, roots, sizes, stats):
    repairs = []
    fields = {f["target"]: f for f in collection["fields"]}
    references = {column: roots[r["to"]] for r in collection["decision"].get("references", [])
                  for column in r["column"]}
    for index in collection.get("indexes", []):
        if not index.get("unique"):
            continue
        paths = [key for key, _ in index["keys"]]
        usage = {path: Counter(getPath(document, path) for document in documents) for path in paths
                 if fields[path]["source"] in references}
        caps = {field["source"]: stat["values"]["max"]
                for field in fields.values() for stat in stats
                if stat["subject"]["child"] == collection["root_table"]
                and stat["subject"]["child_columns"] == [field["source"]]}
        seen = set()
        for sequence, document in enumerate(documents, 1):
            signature = lambda: json_util.dumps([getPath(document, path) for path in paths], sort_keys=True)
            if signature() in seen:
                mutable = [path for path in paths if fields[path]["source"] not in references]
                if mutable:
                    path = mutable[0]
                    setPath(document, path, makeValue(fields[path]["bson_type"], sequence, None))
                else:
                    oldValues = [getPath(document, path) for path in paths]
                    for path, value in zip(paths, oldValues):
                        usage[path][value] -= 1
                    domains = [[None] + list(range(1, sizes[references[fields[path]["source"]]] + 1)) for path in paths]
                    for values in product(*domains):
                        if any(value is not None and usage[path][value] >= caps.get(fields[path]["source"], len(documents))
                               for path, value in zip(paths, values)):
                            continue
                        for path, value in zip(paths, values):
                            setPath(document, path, value)
                        if signature() not in seen:
                            for path, value in zip(paths, values):
                                usage[path][value] += 1
                            break
                if signature() in seen:
                    raise ValueError(f"Cannot make unique tuple: {collection['collection']} {paths}")
                repairs.append({"collection": collection["collection"], "id": document["_id"], "paths": paths})
            seen.add(signature())
    for index in collection.get("indexes", []):
        if index.get("unique"):
            keys = [json_util.dumps([getPath(document, key) for key, _ in index["keys"]], sort_keys=True)
                    for document in documents]
            if len(set(keys)) != len(keys):
                raise ValueError(f"Unique indexes conflict: {collection['collection']}")
    return repairs


def build(args):
    specPath = repoRoot / ".migration/mapping_spec.json"
    profilePath = repoRoot / ".migration/data_profile.json"
    spec = json.loads(specPath.read_text())
    profile = json.loads(profilePath.read_text())
    collections = spec["collections"]
    selected = set(c["collection"] for c in collections)
    if args.collections or args.collections_file:
        selected = set(args.collections.split(",")) if args.collections else set()
        if args.collections_file:
            names = json.loads(Path(args.collections_file).read_text())
            if not isinstance(names, list) or not all(isinstance(n, str) for n in names):
                raise ValueError("--collections-file must contain a JSON list of names")
            selected.update(names)
        unknown = selected - {c["collection"] for c in collections}
        if unknown or not selected:
            raise ValueError(f"Empty selection or unknown collections: {sorted(unknown)}")
    rng = random.Random(args.seed)
    roots = {c["root_table"]: c for c in collections}
    holders = {}
    for collection in collections:
        for embed in collection["embeds"]:
            holders.setdefault(embed["child_table"], []).append((collection["root_table"], embed))
    tables = set(roots) | set(holders)
    stats = [s for s in profile["stats"] if s["query_id"] == "fanout"
             and s["values"].get("max") is not None
             and s["subject"]["parent"] in tables and s["subject"]["child"] in tables]
    outlier = max(stats, key=lambda s: (s["values"]["max"], s["values"]["max"] - s["values"]["p99"], s["id"]))
    ties = sorted(s["id"] for s in stats if s["values"]["max"] == outlier["values"]["max"])
    holderStats = {}
    for table, entries in holders.items():
        parent, embed = entries[0]
        matches = [s for s in stats if s["subject"] == {
            "parent": parent, "child": table, "child_columns": embed["parent_key"]}]
        if not matches:
            fallback = {"id": f"synthetic-unmeasured:{parent}->{table}",
                        "subject": {"parent": parent, "child": table, "child_columns": embed["parent_key"]},
                        "values": {"p50": 0, "p99": 0, "max": 1}, "unmeasured": True}
            stats.append(fallback)
            matches = [fallback]
        holderStats[table] = matches[0]
        if embed["shape"] == "subdocument":
            matches[0]["tail_limit"] = 1
    emptyTables = {s["subject"]["table"] for s in profile["stats"]
                   if s["query_id"] == "row_bytes" and s["values"].get("rows_seen") == 0}
    sizes = {table: args.parents if table in roots and table not in emptyTables else 0 for table in sorted(tables)}
    sizes[outlier["subject"]["parent"]] = max(101, args.parents)
    for iteration in range(100):
        previous = dict(sizes)
        for stat in stats:
            subject = stat["subject"]
            count = sizes[subject["parent"]]
            if count:
                low, _ = bounds(stat, count, stat is outlier)
                if subject["child"] not in emptyTables:
                    sizes[subject["child"]] = max(sizes[subject["child"]], sum(low))
        for table, stat in holderStats.items():
            parent = stat["subject"]["parent"]
            while True:
                _, high = bounds(stat, sizes[parent], stat is outlier)
                if sum(high) >= sizes[table]:
                    break
                if not stat["values"]["max"] or parent in emptyTables:
                    break
                sizes[parent] += 1
                if sizes[parent] > 100000:
                    raise ValueError("Fixture exceeds modest-size limit")
        if sizes == previous:
            break
    else:
        raise ValueError("Fanout sizing did not converge")
    rows = {table: [{"id": i + 1} for i in range(count)] for table, count in sizes.items()}
    fanouts = []
    for stat in stats:
        subject = stat["subject"]
        parent, child = subject["parent"], subject["child"]
        if not sizes[parent]:
            continue
        counts, high = bounds(stat, sizes[parent], stat is outlier)
        if holderStats.get(child) is stat:
            remaining = sizes[child] - sum(counts)
            for i in reversed(range(len(counts))):
                extra = min(remaining, high[i] - counts[i])
                counts[i] += extra
                remaining -= extra
            # Rows without a binding parent are not representable in the target embed.
        rng.shuffle(counts)
        allocation = [i + 1 for i, count in enumerate(counts) for _ in range(count)]
        if len(allocation) > sizes[child]:
            allocation = allocation[:sizes[child]]
        allocation += [None] * (sizes[child] - len(allocation))
        rng.shuffle(allocation)
        for row, parentId in zip(rows[child], allocation):
            for column in subject["child_columns"]:
                row[column] = parentId
        achieved = {"p50": quantile(counts, .5), "p99": quantile(counts, .99), "max": max(counts)}
        fanouts.append({"relation": stat["id"], "subject": subject,
                        "targets": None if stat.get("unmeasured") else stat["values"],
                        "achieved": {"parents": len(counts), "parents_zero": counts.count(0), **achieved}})
        if stat is outlier:
            outlierRecord = {"relation": stat["id"], "parent_id": counts.index(stat["values"]["max"]) + 1,
                             "child_count": stat["values"]["max"]}
    # Unmeasured references still point to existing synthetic parents.
    byName = {c["collection"]: c["root_table"] for c in collections}
    for collection in collections:
        shapes = [(collection["root_table"], collection["decision"].get("references", []))]
        shapes += [(e["child_table"], e.get("child_references", [])) for e in collection["embeds"]]
        for table, references in shapes:
            for reference in references:
                parent = byName[reference["to"]]
                for row in rows[table]:
                    for column in reference["column"]:
                        if column not in row:
                            row[column] = rng.randrange(1, sizes[parent] + 1) if sizes[parent] else None
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rowCounts, files, uniqueRepairs, targetRows = {}, {}, [], {}
    for collection in collections:
        name = collection["collection"]
        required = {key for index in collection.get("indexes", []) if index.get("unique") for key, _ in index["keys"]}
        documents = [makeDocument(row, collection["fields"], collection["key"], rng, required)
                     for row in rows[collection["root_table"]]]
        uniqueRepairs.extend(repairUnique(documents, collection, byName, sizes, stats))
        targetRows[collection["root_table"]] = [
            {"id": document["_id"], **{field["source"]: getPath(document, field["target"])
                                       for field in collection["fields"]}}
            for document in documents]
        for embed in collection["embeds"]:
            grouped = {}
            targetRows.setdefault(embed["child_table"], [])
            for row in rows[embed["child_table"]]:
                parentId = row.get(embed["parent_key"][0])
                if parentId is not None and parentId <= sizes[collection["root_table"]]:
                    targetRows[embed["child_table"]].append(row)
                    fields = list({f["target"]: f for f in embed.get("child_fields", []) + embed["fields"]}.values())
                    grouped.setdefault(parentId, []).append(makeDocument(row, fields, embed["key"], rng, set()))
            for row, document in zip(rows[collection["root_table"]], documents):
                elements = grouped.get(row["id"], [])
                if embed["shape"] == "subdocument":
                    if len(elements) > 1:
                        raise ValueError(f"Subdocument has multiple rows: {name}.{embed['array_path']}")
                    if elements:
                        setPath(document, embed["array_path"], elements[0])
                else:
                    setPath(document, embed["array_path"], elements)
        if name not in selected:
            continue
        path = args.out_dir / f"{name}.jsonl.gz"
        with path.open("wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as stream:
                for document in documents:
                    stream.write((json_util.dumps(document, json_options=json_util.RELAXED_JSON_OPTIONS,
                                                   separators=(",", ":")) + "\n").encode())
        rowCounts[name] = len(documents)
        files[name] = {"path": str(path.resolve().relative_to(args.manifest.resolve().parent)),
                       "sha256": digest(path)}
    for entry in fanouts:
        subject = entry["subject"]
        counts = {row["id"]: 0 for row in targetRows.get(subject["parent"], [])}
        for row in targetRows.get(subject["child"], []):
            parentId = row.get(subject["child_columns"][0])
            if parentId in counts:
                counts[parentId] += 1
        values = list(counts.values())
        entry["achieved"] = {"parents": len(values), "parents_zero": values.count(0),
                             "p50": quantile(values, .5) if values else None,
                             "p99": quantile(values, .99) if values else None,
                             "max": max(values, default=0)}
        if entry["targets"] and entry["achieved"]["max"] > entry["targets"]["max"]:
            raise ValueError(f"Actual fanout exceeds profile max: {entry['relation']}")
        entry["quantiles_match"] = entry["targets"] is not None and all(
            entry["achieved"][key] == entry["targets"][key] for key in ("p50", "p99"))
    manifest = {"source": "synthetic; no source database access or copied records", "method": "synthetic",
                "masked_columns": [], "produced_at": datetime.now(timezone.utc).isoformat(),
                "produced_by": f".migration/fixtures/build_fixture.py; plugin {pluginPin}",
                "row_counts": rowCounts, "spec_version": spec["version"],
                "spec_sha256": digest(specPath), "profile_sha256": digest(profilePath),
                "seed": args.seed, "base_parents": args.parents, "outlier_parent": outlierRecord,
                "outlier_tie": {"relations": ties, "rule": "largest max, then largest max-minus-p99, then lexicographically largest relation id"},
                "empty_in_profile": sorted(c["collection"] for c in collections if c["collection"] in selected and c["root_table"] in emptyTables),
                "unique_key_repairs": uniqueRepairs,
                "recon_input": "none — target-shaped synthetic docs; recon --mode fixture needs a source copy",
                "fanout_quantile_method": "nearest-rank", "fanout": fanouts, "files": files,
                "fanout_scope": "all mapped tables, after unique repairs and target embed projection; filtered files retain these global IDs",
                "fanout_mismatches": [entry["relation"] for entry in fanouts if entry["targets"] and not entry["quantiles_match"]],
                "unmeasured_relations": [s["id"] for s in profile["stats"] if s["query_id"] == "fanout"
                                         and s["values"].get("max") is None]}
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Built {len(rowCounts)} collections, {sum(rowCounts.values())} documents")
    print("Outlier:", json.dumps(outlierRecord))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collections")
    parser.add_argument("--collections-file")
    parser.add_argument("--seed", type=int, default=16)
    parser.add_argument("--parents", type=int, default=20)
    parser.add_argument("--out-dir", type=Path, default=fixtureDir / "data")
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    if args.manifest is None:
        args.manifest = args.out_dir.parent / "fixture_manifest.json"
    if args.parents < 2:
        parser.error("--parents must be at least 2")
    try:
        build(args)
    except ValueError as error:
        parser.exit(1, f"fixture refused: {error}\n")


if __name__ == "__main__":
    main()
