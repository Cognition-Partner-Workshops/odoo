"""Verifier's own reseed of one unit into the clone's test-isolation prefix (UNT12-30).

    VERIFY_SRC_DSN=<JSON DSN of the verifier clone> python verify-load-prefixed.py --unit product-attributes

Reuses the committed loader (`.migration/load/load_unit.py`: documents, validate, index_specs,
write_collection) unchanged, but targets ``<clone>__<collection>`` in the allowed database, the
collections the ORM reads for that clone when ``mongodb_migration_db`` is NOT set. It refuses to
touch an unprefixed (live batch) collection.
"""
import argparse, json, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT / '.migration' / 'load'), str(ROOT)]
import load_unit  # noqa: E402

parser = argparse.ArgumentParser()
parser.add_argument('--unit', required=True)
parser.add_argument('--source-dsn-secret', default='VERIFY_SRC_DSN')
parser.add_argument('--target-uri-secret', default='MONGODB_ATLAS_URI')
parser.add_argument('--target-db', default=json.load(load_unit.ALLOWED.open())['databases'][0])
args = parser.parse_args()
names, _ = load_unit.unit_collections(args.unit, args.target_db)
spec = {c['collection']: c for c in json.load(load_unit.MAPPING.open())['collections']}
conn, source_db = load_unit.connect_source(args.source_dsn_secret)
cur = conn.cursor()
loads = {n: load_unit.documents(cur, spec[n]) for n in names}
conn.close()
for n in names:
    load_unit.validate(n, spec[n], loads[n])
db = load_unit.MongoClient(os.environ[args.target_uri_secret], appname=f'odoo-verify-{args.unit}')[args.target_db]
prefix = f'{source_db}__'
for n in names:
    target = prefix + n
    assert target.startswith(prefix) and '__' in target and target != n
    load_unit.write_collection(db[target], loads[n], load_unit.index_specs(spec[n]))
    print(f'{spec[n]["root_table"]} ({source_db}) -> {args.target_db}.{target}: {len(loads[n])} documents, '
          f'{len(db[target].index_information())} indexes')
