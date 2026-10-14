#!/usr/bin/env python3
"""Write the recon fixture manifest (.migration/fixtures/odoo_fixture.json) from the live fixture.

Sizing is checked against .migration/data_profile.json: for every fan-out between two
migrate-bucket tables (.migration/table_buckets.json) the fixture's p50/p99/max must reach
the profile's (nearest-rank percentiles, as data_profile.py computes them), and the outlier
template must exceed the profile's max variants per template. Any gap fails the build.
Reads the fixture through the env var named by --dsn-env (odoo_ro, database odoo_fixture).
"""
import argparse
import datetime as dt
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import psycopg

HERE = Path(__file__).resolve().parent
MIGRATION = HERE.parent
OUTLIER_XMLID = ("__migration__", "fixture_outlier_tee")
VARIANT_FANOUT = ("product_template", "product_product", "product_tmpl_id")


def percentile(dist, pct):
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


def fanout_values(rows):
    dist = sorted(((int(r[0]), int(r[1])) for r in rows), key=lambda x: x[0])
    return {"parents": sum(n for _, n in dist),
            "parents_zero": next((n for v, n in dist if v == 0), 0),
            "min": dist[0][0] if dist else None,
            "p50": percentile(dist, 50), "p95": percentile(dist, 95),
            "p99": percentile(dist, 99), "max": dist[-1][0] if dist else None}


def q(name):
    return '"' + name.replace('"', '""') + '"'


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(HERE / "odoo_fixture.json"))
    ap.add_argument("--dsn-env", default="ODOO_PG_FIXTURE_DSN")
    args = ap.parse_args()

    secret = json.loads(os.environ[args.dsn_env])
    params = {"user": secret["user"], "password": secret["password"], "host": secret["host"],
              "port": int(secret.get("port", 5432)), "dbname": secret["database"]}

    profile_path = MIGRATION / "data_profile.json"
    profile = json.loads(profile_path.read_text())
    buckets = json.loads((MIGRATION / "table_buckets.json").read_text())
    migrate = sorted(t["table"] for t in buckets["tables"]
                     if t["bucket"] == "migrate" and t["kind"] == "table")

    with psycopg.connect(**params, autocommit=True) as conn:
        conn.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY")
        dbname = conn.execute("SELECT current_database()").fetchone()[0]
        markers = dict(conn.execute(
            "SELECT key, value FROM ir_config_parameter WHERE key IN "
            "('migration.fixture', 'migration.fixture_source', 'database.uuid')").fetchall())
        if markers.get("migration.fixture") is None:
            sys.exit(f"{dbname} carries no migration.fixture marker; run build_fixture.sh")

        row_counts = {t: conn.execute(f"SELECT count(*) FROM {q(t)}").fetchone()[0]
                      for t in migrate}

        relationships, uncovered, empty_parent = [], [], []
        for stat in profile["stats"]:
            if stat["query_id"] != "fanout" or stat["status"] != "ok":
                continue
            parent, child = stat["subject"]["parent"], stat["subject"]["child"]
            cols = stat["subject"]["child_columns"]
            if parent not in migrate or child not in migrate or len(cols) != 1:
                continue
            expected = stat["values"]
            if not expected["parents"]:
                empty_parent.append(stat["id"])   # parent table empty in the source: nothing to size
                continue
            rows = conn.execute(
                f"SELECT n, count(*) FROM (SELECT count(c.{q(cols[0])}) AS n FROM {q(parent)} p "
                f"LEFT JOIN {q(child)} c ON c.{q(cols[0])} = p.id GROUP BY p.id) d GROUP BY n"
            ).fetchall()
            measured = fanout_values(rows)
            covered = all(measured[k] is not None and measured[k] >= expected[k]
                          for k in ("p50", "p99", "max") if expected[k] is not None)
            rel = {"id": stat["id"], "parent": parent, "child": child, "column": cols[0],
                   "profile": {k: expected[k] for k in ("parents", "p50", "p99", "max")},
                   "fixture": {k: measured[k] for k in ("parents", "p50", "p99", "max")},
                   "covered": covered}
            relationships.append(rel)
            if not covered:
                uncovered.append(stat["id"])
        relationships.sort(key=lambda r: (-(r["fixture"]["max"] or 0), r["id"]))

        outlier_id = conn.execute(
            "SELECT res_id FROM ir_model_data WHERE module = %s AND name = %s", OUTLIER_XMLID
        ).fetchone()
        if not outlier_id:
            sys.exit(f"outlier {'.'.join(OUTLIER_XMLID)} not found in {dbname}")
        outlier_id = outlier_id[0]
        count = lambda sql: conn.execute(sql, (outlier_id,)).fetchone()[0]  # noqa: E731
        outlier = {
            "table": "product_template", "id": outlier_id, "xmlid": ".".join(OUTLIER_XMLID),
            "name": conn.execute("SELECT name->>'en_US' FROM product_template WHERE id = %s",
                                 (outlier_id,)).fetchone()[0],
            "variants": count("SELECT count(*) FROM product_product WHERE product_tmpl_id = %s"),
            "attribute_lines": count(
                "SELECT count(*) FROM product_template_attribute_line WHERE product_tmpl_id = %s"),
            "template_attribute_values": count(
                "SELECT count(*) FROM product_template_attribute_value WHERE product_tmpl_id = %s"),
            "variant_combinations": count(
                "SELECT count(*) FROM product_variant_combination r JOIN product_product v "
                "ON v.id = r.product_product_id WHERE v.product_tmpl_id = %s"),
        }

    variant_profile = next((r["profile"] for r in relationships
                            if (r["parent"], r["child"], r["column"]) == VARIANT_FANOUT), None)
    outlier["profile_max_variants"] = variant_profile["max"] if variant_profile else None
    if variant_profile and outlier["variants"] <= variant_profile["max"]:
        uncovered.append("outlier:variants<=profile max")

    manifest = {
        "manifest_version": 1,
        "source": ("odoo_src (Odoo 20.0 demo data, migration.fixture_source marker "
                   f"{markers.get('migration.fixture_source')}) cloned with CREATE DATABASE "
                   f"{dbname} TEMPLATE odoo_src, plus one synthetic outlier template"),
        "method": "synthetic",
        "masked_columns": [],
        "masking": "none: Odoo demo data is synthetic, the fixture holds no customer rows",
        "produced_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "produced_by": "s2.4-fixture (.migration/fixtures/build_fixture.sh)",
        "fixture": {
            "family": "postgresql", "database": dbname, "host": params["host"],
            "port": params["port"], "schema": "public", "role": params["user"],
            "marker": {"key": "migration.fixture", "value": markers["migration.fixture"]},
            "source_database_uuid": markers.get("database.uuid"),
            "dsn_env": args.dsn_env,
            "dsn_derivation": "ODOO_PG_RO_DSN JSON with \"database\" replaced by "
                              f"{dbname} (same read-only role); exported per shell, never stored",
            "recon": f"recon run --mode fixture --family postgresql --source-dsn-secret {args.dsn_env}",
            "build": ".migration/fixtures/build_fixture.sh (after build_source.sh)",
        },
        "scope": {"from": ".migration/table_buckets.json bucket migrate", "tables": migrate},
        "row_counts": row_counts,
        "sizing": {
            "profile": {"path": ".migration/data_profile.json", "sha256": sha256(profile_path),
                        "as_of": profile["as_of"], "census_sha256": profile["census_sha256"]},
            "rule": ("every fan-out whose parent and child are both migrate-bucket tables keeps "
                     "parents at the profile's p50, p99 and max (the demo slice is smaller than "
                     "any subset that would still hold all three, so no row is dropped); the "
                     "outlier template exceeds the profile's max variants per template"),
            "relationships": relationships,
            "empty_parent": sorted(empty_parent),
            "uncovered": sorted(uncovered),
        },
        "outlier": outlier,
    }
    Path(args.out).write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    print(f"{args.out}: {len(migrate)} tables, {sum(row_counts.values())} rows, "
          f"{len(relationships)} fan-outs checked ({len(empty_parent)} empty-parent skipped), outlier {outlier['variants']} variants "
          f"(profile max {outlier['profile_max_variants']}), uncovered={len(uncovered)}")
    if uncovered:
        sys.exit(1)


if __name__ == "__main__":
    main()
