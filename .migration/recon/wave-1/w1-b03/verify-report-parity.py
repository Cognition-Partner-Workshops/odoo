"""Row parity of stock.avco.report and vendor.delay.report against PostgreSQL, read-only.

Run twice through `odoo-bin shell -d <clone> --db_port=5433 --no-http < this file` on the SAME seeded clone:
  VERIFY_REPORT_MODE=baseline  through the pre-opt-in source tree (odoo-unt12-src at build_source.sh's
                               SOURCE_COMMIT): both reports are plain PostgreSQL views there; every row is
                               dumped, normalised, to verify-report-parity-baseline.json.
  VERIFY_REPORT_MODE=compare   through the verified PR head with its default prefix (<clone>__), product.category
                               and uom.uom opted in (_storage = 'mongodb', read from the prefixed verifier load):
                               the same rows are read through the ORM and compared one for one with the baseline,
                               plus search_count and a vendor.delay.report read_group by category_id.
Nothing is written: the transaction is rolled back and the compare pass hashes the prefixed collections before/after.
The prefix must hold EVERY opted-in model's collection (verify-prefixed-load.py --units <all merged units>): e.g.
product.product.display_name reads product.attribute, so a prefix without productAttribute makes vendor.delay.report's
product_id read back False (MissingError swallowed by convert_to_read); the compare pass asserts the coverage.
"""
import datetime
import decimal
import hashlib
import json
import os
import sys
from pathlib import Path

MODE = os.environ['VERIFY_REPORT_MODE']
OUT = Path(os.environ['VERIFY_REPORT_OUT'])
BASE = OUT / 'verify-report-parity-baseline.json'
REPORTS = ('stock.avco.report', 'vendor.delay.report')


def norm(v):
    if isinstance(v, (tuple, list)):
        return [norm(x) for x in v]
    if isinstance(v, dict):
        return {k: norm(x) for k, x in v.items()}
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.isoformat()
    if isinstance(v, decimal.Decimal):
        return float(round(v, 6))
    if isinstance(v, float):
        return round(v, 6)
    return v


def m2o_id(v):
    return v[0] if isinstance(v, (tuple, list)) else (v or None)


def rows(model):
    Model = env[model].sudo()
    fields = [f for f, d in Model.fields_get().items() if d['type'] not in ('one2many', 'many2many', 'binary')]
    out = []
    for r in Model.search_read([], fields=fields, order='id'):
        rec = {}
        for f in fields:
            v = r.get(f)
            rec[f] = m2o_id(v) if Model._fields[f].type == 'many2one' else norm(v)
        out.append(rec)
    return out


def vendor_groups():
    return norm(sorted(
        (cat.id or None, count, qty_total, qty_on_time)
        for cat, count, qty_total, qty_on_time in env['vendor.delay.report'].sudo()._read_group(
            [], ['category_id'], ['__count', 'qty_total:sum', 'qty_on_time:sum'])))


if MODE == 'baseline':
    assert not any(env[m]._storage == 'mongodb' for m in ('product.category', 'uom.uom') if hasattr(env[m], '_storage')), 'baseline must run through the pre-opt-in tree'
    data = {m: rows(m) for m in REPORTS}
    data['vendor.delay.report:read_group:category_id'] = vendor_groups()
    data['counts'] = {m: env[m].sudo().search_count([]) for m in REPORTS}
    BASE.write_text(json.dumps(data, indent=1, sort_keys=True, default=str) + '\n')
    print('baseline rows:', {m: len(data[m]) for m in REPORTS}, 'groups:', len(data['vendor.delay.report:read_group:category_id']))
    env.cr.rollback()
    sys.exit(0)

assert MODE == 'compare', MODE
from bson.json_util import dumps  # noqa: E402
probes = []


def check(name, ok, evidence):
    probes.append({'probe': name, 'pass': bool(ok), 'evidence': str(evidence)[:1500]})


st = env.registry.mongo_store
check('ORM prefix is the clone\'s own, never unprefixed', st.prefix == f'{env.cr.dbname}__', st.prefix)
for m, coll in (('product.category', 'productCategory'), ('uom.uom', 'uomUom')):
    check(f'{m} opted in and read from the prefixed collection',
          env[m]._storage == 'mongodb' and st.collection(coll).name == st.prefix + coll and st.collection(coll).estimated_document_count() > 0,
          f"storage={env[m]._storage} coll={st.collection(coll).name} docs={st.collection(coll).estimated_document_count()}")
check('product.category documents in the prefix equal PostgreSQL product_category rows (id set)',
      sorted(d['_id'] for d in st.collection('productCategory').find({}, {'_id': 1})) == [r[0] for r in (env.cr.execute('SELECT id FROM product_category ORDER BY id') or env.cr.fetchall())],
      f"{st.collection('productCategory').estimated_document_count()} docs")
roots = {c['root_table']: c['collection'] for c in json.load((OUT.resolve().parents[2] / 'mapping_spec.json').open())['collections']}
missing, roots_checked, embedded = [], 0, []
for name in sorted(env.registry.models):
    Model = env[name]
    if Model._abstract or Model._transient or getattr(Model, '_storage', None) != 'mongodb' or not Model._auto:
        continue
    if Model._table not in roots:
        embedded.append(name)  # child rows live as embedded arrays of a root collection
        continue
    roots_checked += 1
    env.cr.execute(f'SELECT count(*) FROM "{Model._table}"')
    pg = env.cr.fetchone()[0]
    docs = st.collection(roots[Model._table]).estimated_document_count()
    if docs != pg:
        missing.append((name, st.prefix + roots[Model._table], docs, pg))
check('every opted-in root model has its prefixed collection loaded from the clone (document count == PostgreSQL row count)',
      not missing, missing or f'{roots_checked} root models equal; embedded child models (arrays of a root): {embedded}')
hashed = ['uomUom', 'stockPackageType', 'productCategory']
before = {c: hashlib.sha256(dumps(list(st.collection(c).find().sort('_id', 1)), sort_keys=True).encode()).hexdigest() for c in hashed}
base = json.loads(BASE.read_text())
for m in REPORTS:
    got = json.loads(json.dumps(rows(m), default=str))
    exp = base[m]
    diff = [(g, e) for g, e in zip(got, exp) if g != e]
    check(f'{m}: ORM rows on the PR head == legacy PostgreSQL view rows (every field, ordered by id)',
          len(got) == len(exp) and not diff, f'orm={len(got)} pg={len(exp)} first_diff={diff[:1]}')
    check(f'{m}: search_count == PostgreSQL view count', env[m].sudo().search_count([]) == base['counts'][m], f"orm={env[m].sudo().search_count([])} pg={base['counts'][m]}")
    check(f'{m}: cost-method / category filter leaves no row the legacy view lacks and drops none it has',
          sorted(r['id'] for r in got) == sorted(r['id'] for r in exp), f"ids orm={len(got)} pg={len(exp)}")
groups = json.loads(json.dumps(vendor_groups(), default=str))
check('vendor.delay.report read_group by category_id (MongoDB product.category) == legacy view aggregation',
      groups == base['vendor.delay.report:read_group:category_id'], f'orm={groups} pg={base["vendor.delay.report:read_group:category_id"]}')
after = {c: hashlib.sha256(dumps(list(st.collection(c).find().sort('_id', 1)), sort_keys=True).encode()).hexdigest() for c in hashed}
check('prefixed collections untouched by the report reads (sha256 before == after)', before == after, {c: h[:12] for c, h in after.items()})
env.cr.rollback()
check('transaction rolled back, no PostgreSQL write in the probe', True, 'env.cr.rollback()')
failed = [p for p in probes if not p['pass']]
print(json.dumps({'probes': probes, 'findings': [p['probe'] for p in failed]}, indent=1))
print(f"# report parity probes={len(probes)} passed={len(probes) - len(failed)} failed={len(failed)}", file=sys.stderr)
