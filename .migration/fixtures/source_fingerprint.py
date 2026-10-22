"""Check odoo_src against the committed .migration/source_fingerprint.json.

Connects through the JSON ODOO_PG_RO_DSN secret (read-only role, read-only session),
counts every public base table and hashes one "<table>\t<count>\n" line per table,
sorted by name, as the source-build ticket recorded it. Prints the hash; exits 1 on any
difference (hash, per-table counts or the migration.fixture_source marker).
"""
import hashlib
import json
import os
import sys

import psycopg2

root = os.environ["ROOT"]
expected = json.load(open(f"{root}/.migration/source_fingerprint.json"))
kwargs = json.loads(os.environ["ODOO_PG_RO_DSN"])
kwargs["dbname"] = kwargs.pop("database")
if kwargs["dbname"] != expected["database"]:
    sys.exit(f"source_fingerprint: ODOO_PG_RO_DSN names {kwargs['dbname']}, expected {expected['database']}")

conn = psycopg2.connect(**kwargs)
conn.set_session(readonly=True)
cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public' AND table_type='BASE TABLE'")
counts = {}
for table in sorted(t for (t,) in cur.fetchall()):
    cur.execute('SELECT COUNT(*) FROM "%s"' % table.replace('"', '""'))
    counts[table] = cur.fetchone()[0]
cur.execute("SELECT value FROM ir_config_parameter WHERE key=%s", (expected["marker"]["key"],))
marker = (cur.fetchone() or [None])[0]
conn.close()

digest = hashlib.sha256("".join(f"{t}\t{n}\n" for t, n in sorted(counts.items())).encode()).hexdigest()
problems = []
if digest != expected["row_counts_sha256"]:
    problems.append(f"row_counts_sha256 {digest} != {expected['row_counts_sha256']}")
diff = sorted(set(counts) ^ set(expected["row_counts"])
              | {t for t in counts if t in expected["row_counts"] and counts[t] != expected["row_counts"][t]})
if diff:
    problems.append(f"{len(diff)} table(s) differ, first: {diff[:5]}")
if marker != expected["marker"]["version"]:
    problems.append(f"marker {expected['marker']['key']}={marker!r}, expected {expected['marker']['version']!r}")
if problems:
    print("source_fingerprint: MISMATCH " + "; ".join(problems), file=sys.stderr)
    sys.exit(1)
print(digest)
