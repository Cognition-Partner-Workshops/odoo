"""Verifier-only: load the seeded verifier clone into a private, prefixed namespace of the allowed target database
(odoo_unt12.odoo_v_w1b06__<collection>) so the ORM scenario can run without touching the batch collections.
Reuses the worker's load_unit.py functions unchanged. Dropped again after the scenario runs."""
import json, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / '.migration' / 'load'))
import load_unit as lu  # noqa: E402

UNIT, TARGET_DB, PREFIX = 'account-chart', 'odoo_unt12', 'odoo_v_w1b06__'
BATCH = {'accountAccount', 'accountAccountTag', 'accountTax', 'accountTaxGroup', 'accountTaxRepartitionLine', 'accountFiscalPosition'}
names = lu.unit_collections(UNIT, TARGET_DB)
if isinstance(names, tuple):  # the unified loader (PR #68) also returns the unit's embedded_tables
    names = names[0]
assert set(names) == BATCH, names
spec = {c['collection']: c for c in json.load(lu.MAPPING.open())['collections']}
conn, source_db = lu.connect_source('VERIFY_SRC_DSN')
cur = conn.cursor()
loads = {n: lu.documents(cur, spec[n]) for n in names}
conn.close()
for n in names:
    lu.validate(n, spec[n], loads[n])
db = lu.MongoClient(os.environ['MONGODB_ATLAS_URI'], appname='odoo-verify-w1-b06')[TARGET_DB]
if sys.argv[1:] == ['--drop']:
    for n in names:
        db[PREFIX + n].drop()
    print('dropped', [PREFIX + n for n in names]); sys.exit(0)
for n in names:
    coll = db[PREFIX + n]
    assert coll.name.startswith(PREFIX) and coll.name not in BATCH
    if coll.estimated_document_count():
        raise SystemExit(f'{coll.name} already holds documents')
    lu.write_collection(coll, loads[n], lu.index_specs(spec[n]))
    arrays = {e['array_path']: sum(len(d.get(e['array_path'], ())) for d in loads[n]) for e in spec[n]['embeds']}
    print(f'{spec[n]["root_table"]} ({source_db}) -> {TARGET_DB}.{coll.name}: {len(loads[n])} documents, {len(coll.index_information())} indexes, arrays {arrays}')
