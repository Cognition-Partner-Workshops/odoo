"""Verifier-side load of whole units into a TEMPORARY prefixed namespace of odoo_unt12 (<clone>__<collection>),
the namespace the ORM reads by default for the clone, so the ORM probes never run unprefixed. Re-uses the batch
head's own .migration/load/load_unit.py unchanged: only the Database handle is wrapped so every collection name
gets the prefix. The live (unprefixed) collections are never touched.

    VERIFY_PREFIX=<clone>__ VERIFY_SRC_DSN=<json dsn of the clone> \\
        python verify-prefixed-load.py --units uom-packaging,product-taxonomy [--cleanup]
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT / '.migration' / 'load')]
import load_unit  # noqa: E402

PREFIX = os.environ['VERIFY_PREFIX']
assert PREFIX.endswith('__') and len(PREFIX) > 2, PREFIX
UNITS = sys.argv[sys.argv.index('--units') + 1].split(',')
NAMES = {u: load_unit.unit_collections(u, 'odoo_unt12')[0] for u in UNITS}
ALL = [n for names in NAMES.values() for n in names]


class PrefixedDatabase:
    def __init__(self, db):
        self._db = db

    def __getitem__(self, name):
        assert name in ALL, name
        return self._db[PREFIX + name]


class PrefixedClient(load_unit.MongoClient):
    def __getitem__(self, name):
        return PrefixedDatabase(super().__getitem__(name))


RealClient = load_unit.MongoClient
if '--cleanup' in sys.argv:
    db = RealClient(os.environ['MONGODB_ATLAS_URI'])['odoo_unt12']
    for n in ALL:
        db[PREFIX + n].drop()
    print('removed', [PREFIX + n for n in ALL], 'remaining prefixed:', [c for c in db.list_collection_names() if c.startswith(PREFIX)])
    sys.exit(0)

load_unit.MongoClient = PrefixedClient
for unit in UNITS:
    load_unit.load(unit, 'VERIFY_SRC_DSN', 'MONGODB_ATLAS_URI', 'odoo_unt12', replace=True)
db = RealClient(os.environ['MONGODB_ATLAS_URI'])['odoo_unt12']
print('actual namespaces written:', {PREFIX + n: db[PREFIX + n].count_documents({}) for n in ALL})
