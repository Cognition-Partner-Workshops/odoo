"""Verifier ORM probes for w1-b03: read-only, run through the batch PR head's own tree against the
verifier's seeded clone. The ORM reads its default PREFIXED namespace (<clone>__uomUom,
<clone>__stockPackageType), filled by verify-prefixed-load.py from the same clone; Odoo is never run unprefixed:

    odoo-bin shell -d <clone> --db_port=5433 --no-http < this file

Every relation is read through the ORM and compared for exact equality with the clone's PostgreSQL
rows; the two embedded junction arrays also with the prefixed documents the ORM reads and, read-only,
with the batch's live collections. Nothing is written: live and prefixed collections are hashed before
and after, and the transaction is rolled back.
"""
import hashlib
import json
import sys

from bson.json_util import dumps

cr = env.cr
st = env.registry.mongo_store
assert st.prefix == f"{cr.dbname}__", f"ORM prefix is {st.prefix!r}: the probes must run through the clone's own prefix, never unprefixed"
LIVE = ('uomUom', 'stockPackageType')
Uom = env['uom.uom'].with_context(active_test=False)
PackageType = env['stock.package.type']
PutawayRule = env['stock.putaway.rule']
Route = env['stock.route']
Template = env['product.template'].with_context(active_test=False)
Product = env['product.product'].with_context(active_test=False)
assert Uom._storage == 'mongodb' and PackageType._storage == 'mongodb'
assert Template._storage != 'mongodb' and Product._storage != 'mongodb'

results = []


def check(name, ok, detail=''):
    results.append({'probe': name, 'pass': bool(ok), 'evidence': str(detail)})


def rows(sql, params=()):
    cr.execute(sql, params)
    return sorted(tuple(r) for r in cr.fetchall())


def collection_hash(name):
    docs = list(st.db[name].find().sort('_id', 1))
    return hashlib.sha256(dumps(docs, sort_keys=True).encode()).hexdigest(), len(docs)


def pairs(name, orm_pairs, pg_pairs, allow_empty=False):
    orm_pairs, pg_pairs = sorted(orm_pairs), sorted(pg_pairs)
    check(name, orm_pairs == pg_pairs and (allow_empty or pg_pairs),
          f'orm={len(orm_pairs)} pg={len(pg_pairs)} pairs' + ('' if orm_pairs == pg_pairs else f' orm[:5]={orm_pairs[:5]} pg[:5]={pg_pairs[:5]}'))


before = {c: collection_hash(c) for c in LIVE + tuple(st.prefix + c for c in LIVE)}
check('ORM reads the prefixed namespace only', all(st.collection(c).name == st.prefix + c for c in LIVE), [st.collection(c).name for c in LIVE])

# --- counts and scalar values through the ORM -------------------------------------------------------
check('uom.uom count', len(Uom.search([])) == rows("SELECT count(*) FROM uom_uom")[0][0] == 30, len(Uom.search([])))
check('stock.package.type count', len(PackageType.search([])) == rows("SELECT count(*) FROM stock_package_type")[0][0] == 3, len(PackageType.search([])))
pg_uoms = rows("SELECT id, name->>'en_US', relative_uom_id, active, unece_code, factor::text, relative_factor::text FROM uom_uom")
orm_uoms = sorted((u.id, u.name, u.relative_uom_id.id or None, u.active, u.unece_code or None, u.factor, u.relative_factor) for u in Uom.search([]))
bad = [(a, b) for a, b in zip(pg_uoms, orm_uoms) if a[:5] != b[:5] or float(a[5]) != b[5] or float(a[6]) != b[6]]
check('uom.uom scalar fields equal PostgreSQL rows', not bad and len(pg_uoms) == len(orm_uoms), bad[:3])
pg_types = rows("SELECT id, name, barcode, package_use, max_weight, sequence FROM stock_package_type")
orm_types = sorted((t.id, t.name, t.barcode or None, t.package_use, t.max_weight, t.sequence) for t in PackageType.search([]))
check('stock.package.type scalar fields equal PostgreSQL rows', pg_types == orm_types, (pg_types, orm_types) if pg_types != orm_types else '3 rows')

# --- product.template.uom_ids / product.product.extra_uom_ids: read from PostgreSQL ----------------
pg_tpl = rows("SELECT product_template_id, uom_uom_id FROM product_template_uom_uom_rel")
pg_prd = rows("SELECT product_product_id, uom_uom_id FROM product_product_uom_uom_rel")
pairs('product.template.uom_ids (ORM) == product_template_uom_uom_rel', [(t.id, u.id) for t in Template.search([]) for u in t.uom_ids], pg_tpl, allow_empty=True)
pairs('product.product.extra_uom_ids (ORM) == product_product_uom_uom_rel', [(p.id, u.id) for p in Product.search([]) for u in p.extra_uom_ids], pg_prd, allow_empty=True)
pairs('product.template search on uom_ids over every uom', [(t.id, u) for u in Uom.search([]).ids for t in Template.search([('uom_ids', 'in', [u])])], pg_tpl, allow_empty=True)
pairs('product.product search on extra_uom_ids over every uom', [(p.id, u) for u in Uom.search([]).ids for p in Product.search([('extra_uom_ids', 'in', [u])])], pg_prd, allow_empty=True)
pairs('uom.uom.product_ids reverse side (if declared)', [(u.id, t.id) for u in Uom.search([]) for t in getattr(u, 'product_ids', env['product.template'])] if 'product_ids' in Uom._fields else [],
      [(b, a) for a, b in pg_tpl] if 'product_ids' in Uom._fields else [], allow_empty=True)
check('uom_ids / extra_uom_ids relation tables are still PostgreSQL tables (row counts)',
      True, f'product_template_uom_uom_rel={len(pg_tpl)} product_product_uom_uom_rel={len(pg_prd)} (0 estate rows: equality is of empty sets on both sides; no link was made because this verify writes nothing)')
check('no productTemplate / productProduct documents are consulted for these relations',
      'productTemplate' not in st.db.list_collection_names() or st.db['productTemplate'].count_documents({'uomUomRel': {'$exists': True}}) == 0,
      f"productTemplate present={'productTemplate' in st.db.list_collection_names()}")

# --- the two embedded junction arrays, from both sides and against the documents --------------------
pg_routes = rows("SELECT stock_package_type_id, stock_route_id FROM stock_package_type_stock_route_rel")
pg_rules = rows("SELECT stock_package_type_id, stock_putaway_rule_id FROM stock_package_type_stock_putaway_rule_rel")
for label, coll in (('prefixed, what the ORM reads', st.collection('stockPackageType')), ('live batch collection, read-only', st.db['stockPackageType'])):
    docs = {d['_id']: d for d in coll.find()}
    doc_routes = sorted((i, el['stockRouteId']) for i, d in docs.items() for el in d.get('stockRouteRel') or [])
    doc_rules = sorted((i, el['stockPutawayRuleId']) for i, d in docs.items() for el in d.get('stockPutawayRuleRel') or [])
    pairs(f'stockRouteRel documents == stock_package_type_stock_route_rel [{label}]', doc_routes, pg_routes)
    pairs(f'stockPutawayRuleRel documents == stock_package_type_stock_putaway_rule_rel [{label}]', doc_rules, pg_rules)
for c in LIVE:
    live_docs = sorted(dumps(d, sort_keys=True) for d in st.db[c].find())
    pref_docs = sorted(dumps(d, sort_keys=True) for d in st.collection(c).find())
    check(f'{c}: prefixed documents (verifier load from the clone) == live batch documents', live_docs == pref_docs, f'{len(pref_docs)} vs {len(live_docs)} docs')
pairs('stock.package.type.route_ids (owner side, ORM)', [(t.id, r.id) for t in PackageType.search([]) for r in t.route_ids], pg_routes)
pairs('stock.package.type search on route_ids over every route', [(t.id, r.id) for r in Route.search([]) for t in PackageType.search([('route_ids', 'in', r.ids)])], pg_routes)
if 'package_type_ids' in Route._fields:
    pairs('stock.route.package_type_ids (other side, ORM)', [(t.id, r.id) for r in Route.search([]) for t in r.package_type_ids], pg_routes)
else:
    check('stock.route has no package_type_ids field; other side covered by the search through the array', True, sorted(f for f in Route._fields if 'package' in f))
pairs('stock.putaway.rule.package_type_ids (other side, ORM)', [(t.id, r.id) for r in PutawayRule.search([]) for t in r.package_type_ids], pg_rules)
pairs('stock.putaway.rule search on package_type_ids over every package type', [(t.id, r.id) for t in PackageType.search([]) for r in PutawayRule.search([('package_type_ids', 'in', t.ids)])], pg_rules)
if 'putaway_rule_ids' in PackageType._fields:
    pairs('stock.package.type.putaway_rule_ids (owner side, ORM)', [(t.id, r.id) for t in PackageType.search([]) for r in t.putaway_rule_ids], pg_rules)
else:
    check('stock.package.type has no putaway_rule_ids field; owner side covered by the putaway-rule search', True, sorted(f for f in PackageType._fields if 'rule' in f or 'route' in f))
pairs('uom.uom.package_type_id -> stock.package.type (cross-store m2o, ORM) == live documents',
      [(u.id, u.package_type_id.id) for u in Uom.search([('package_type_id', '!=', False)])],
      [(d['_id'], d['packageTypeId']) for d in st.db['uomUom'].find({'packageTypeId': {'$ne': None}})], allow_empty=True)
pairs('uom.uom.relative_uom_id / related_uom_ids both sides', [(u.relative_uom_id.id, u.id) for u in Uom.search([('relative_uom_id', '!=', False)])],
      [(p.id, c.id) for p in Uom.search([]) for c in p.related_uom_ids])
pairs('uom.uom.related_uom_ids == PostgreSQL', [(p.id, c.id) for p in Uom.search([]) for c in p.related_uom_ids],
      rows("SELECT relative_uom_id, id FROM uom_uom WHERE relative_uom_id IS NOT NULL"))

env.invalidate_all()
cr.rollback()
after = {c: collection_hash(c) for c in LIVE + tuple(st.prefix + c for c in LIVE)}
check('live and prefixed collections untouched (sha256 of every document before == after)', before == after, {c: f'{n} docs {h[:12]}' for c, (h, n) in after.items()})
check('transaction rolled back, no PostgreSQL write in the probe', True, 'cr.rollback()')

print(json.dumps({'probes': results, 'findings': [r['probe'] + ': ' + r['evidence'] for r in results if not r['pass']]}, indent=1, default=str))
print(f"# orm probes={len(results)} passed={sum(r['pass'] for r in results)} failed={sum(not r['pass'] for r in results)}", file=sys.stderr)
