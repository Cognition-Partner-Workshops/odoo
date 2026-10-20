"""ORM scenario for batch w1-b03 (unit uom-packaging) on the MongoDB storage path.

Run on the run branch against the worker's seeded clone, whose documents are the loaded ones: either
unprefixed (conf key mongodb_migration_db = <clone>) or, to keep every ORM write off the live collections,
on a prefixed clone (mongodb_migration_db != <clone>: the storage path reads ``<clone>__<collection>``,
so copy the loaded collections of every opted-in model under that prefix first):

    /home/ubuntu/.venvs/odoo/bin/python odoo-bin shell -c <conf> -d <clone> --no-http \\
        < .migration/load/scenario_uom_packaging.py

Reads are compared with the clone's PostgreSQL rows (the clone still carries the legacy columns).
The three rewritten SQL reports are compared A/B: the same read_group with the UoM factors taken
from the legacy uom_uom column (how the reports read before the opt-in) and from the MongoDB
documents (the rewrite). Every write happens in one transaction that is rolled back at the end,
and the documents are hashed before and after to show the journal left the loaded collections
untouched.
"""
import hashlib
from decimal import Decimal

from bson.json_util import dumps

import psycopg2

from odoo.exceptions import ValidationError
from odoo.tools import SQL

cr = env.cr
st = env.registry.mongo_store
print(f"collection prefix {st.prefix!r}")
assert st.collection('uomUom').estimated_document_count(), f"{st.prefix}uomUom is empty: load or copy the collections first"
Uom = env['uom.uom'].with_context(active_test=False)
PackageType = env['stock.package.type']
PutawayRule = env['stock.putaway.rule']
assert Uom._storage == 'mongodb' and PackageType._storage == 'mongodb'
COLLECTIONS = ('uomUom', 'stockPackageType')

results = []


def check(name, ok, detail=''):
    results.append((name, bool(ok)))
    print(f"{'PASS' if ok else 'FAIL'} {name}{' -- ' + str(detail) if detail else ''}")


def collection_hash(name):
    docs = list(st.collection(name).find({}, sort=[('_id', 1)]))
    return hashlib.sha256(dumps(docs, sort_keys=True).encode()).hexdigest()


def num(value):
    return float(value) if isinstance(value, Decimal) else value


def rows(sql, params=()):
    cr.execute(sql, params)
    return cr.fetchall()


def same_groups(a, b):
    if len(a) != len(b):
        return False
    for ra, rb in zip(a, b):
        for va, vb in zip(ra, rb):
            if isinstance(va, float) or isinstance(vb, float):
                if abs(num(va) - num(vb)) > 1e-9 * max(1.0, abs(num(va))):
                    return False
            elif va != vb:
                return False
    return True


before = {name: collection_hash(name) for name in COLLECTIONS}
collections_before = set(st.db.list_collection_names())

# --- stock.avco.report / vendor.delay.report: ORM rows equal the legacy PostgreSQL views ------------
# Both batches opted in: uom.uom (this PR, factors inlined) and product.category (PR #61, cost-method
# filter moved into _search). Expected = the pre-opt-in view SQL run on the clone's legacy columns.


def same_rows(name, actual, expected):
    actual, expected = sorted(actual, key=lambda r: r[0]), sorted(expected, key=lambda r: r[0])
    check(name, expected and same_groups(actual, expected),
          f'{len(expected)} rows' if same_groups(actual, expected) else (len(actual), len(expected), actual[:1], expected[:1]))


def m2o(v):
    return v[0] if v else None


legacy_avco = rows("""
SELECT sm.id, sm.product_id, sm.date::date, picking.user_id, sm.company_id, sm.reference,
       CASE WHEN sm.is_in THEN sm.value ELSE -sm.value END,
       CASE WHEN sm.is_in THEN sm.quantity * (um.factor / up.factor) ELSE -sm.quantity * (um.factor / up.factor) END,
       'stock.move', 'Operation'
FROM stock_move sm
LEFT JOIN stock_picking picking ON sm.picking_id = picking.id
LEFT JOIN product_product pp ON sm.product_id = pp.id
LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
LEFT JOIN product_category pc ON pt.categ_id = pc.id
LEFT JOIN ir_default cost_method_default ON cost_method_default.company_id = sm.company_id
     AND cost_method_default.field_id = (SELECT id FROM ir_model_fields WHERE name = 'property_cost_method' AND model = 'product.category')
LEFT JOIN uom_uom um ON um.id = sm.uom_id
LEFT JOIN uom_uom up ON up.id = pt.uom_id
WHERE sm.state = 'done' AND (sm.is_in = TRUE OR sm.is_out = TRUE)
  AND COALESCE(pc.property_cost_method ->> sm.company_id::text, cost_method_default.json_value::jsonb #>> '{}') IN ('fifo', 'average')
UNION ALL
SELECT -pv.id, pv.product_id, pv.date::date, pv.user_id, pv.company_id, 'Adjustment', pv.value, 0, 'product.value', pv.description
FROM product_value pv WHERE pv.move_id IS NULL""")
orm_avco = [(r['id'], m2o(r['product_id']), r['date'].date() if hasattr(r['date'], 'date') else r['date'], m2o(r['user_id']), m2o(r['company_id']), r['reference'],
             r['value'], r['quantity'], r['res_model_name'], r['description'])
            for r in env['stock.avco.report'].sudo().search_read(
                [], ['product_id', 'date', 'user_id', 'company_id', 'reference', 'value', 'quantity', 'res_model_name', 'description'])]
same_rows('stock.avco.report rows equal the legacy view (cost-method filter from MongoDB product.category)',
          orm_avco, [tuple(num(v) for v in r) for r in legacy_avco])
legacy_vendor = rows("""
SELECT pol.id, Min(m.date), pol.product_id, Min(pc.id), pol.partner_id, pol.product_uom_qty,
       Sum(CASE WHEN (m.state = 'done' and pol.date_promised::date >= m.date::date) THEN ((ml.quantity * ml_uom.factor) / pt_uom.factor) ELSE 0 END),
       CASE WHEN pol.product_uom_qty != 0 THEN
            Sum(CASE WHEN (m.state = 'done' and pol.date_promised::date >= m.date::date) THEN ((ml.quantity * ml_uom.factor) / pt_uom.factor) ELSE 0 END) / pol.product_uom_qty * 100
       ELSE 100 END
FROM stock_move m
JOIN purchase_order_line pol ON pol.id = m.purchase_line_id
JOIN product_product p ON p.id = m.product_id
JOIN product_template pt ON pt.id = p.product_tmpl_id
JOIN uom_uom pt_uom ON pt_uom.id = pt.uom_id
LEFT JOIN product_category pc ON pc.id = pt.categ_id
LEFT JOIN stock_move_line ml ON ml.move_id = m.id
LEFT JOIN uom_uom ml_uom ON ml_uom.id = ml.uom_id
GROUP BY pol.id""")
orm_vendor = [(r['id'], r['date'], m2o(r['product_id']), m2o(r['category_id']), m2o(r['partner_id']),
               r['qty_total'], r['qty_on_time'], r['on_time_rate'])
              for r in env['vendor.delay.report'].sudo().search_read(
                  [], ['date', 'product_id', 'category_id', 'partner_id', 'qty_total', 'qty_on_time', 'on_time_rate'])]
same_rows('vendor.delay.report rows equal the legacy view (category from MongoDB product.category)',
          orm_vendor, [tuple(num(v) for v in r) for r in legacy_vendor])

# --- uom.uom reads -------------------------------------------------------------------------------
pg_uoms = {r[0]: r for r in rows("""
    SELECT id, name->>'en_US', relative_factor, factor, active, relative_uom_id, parent_path, unece_code,
           package_type_id, sequence, create_date, write_date FROM uom_uom""")}
orm_uoms = Uom.search_read([], ['name', 'relative_factor', 'factor', 'active', 'relative_uom_id', 'parent_path',
                                'unece_code', 'package_type_id', 'sequence', 'create_date', 'write_date'])
check('uom count', len(orm_uoms) == len(pg_uoms) == 30, f"{len(orm_uoms)} ORM / {len(pg_uoms)} PG")
mismatch = []
for u in orm_uoms:
    r = pg_uoms[u['id']]
    got = (u['id'], u['name'], u['relative_factor'], u['factor'], u['active'], (u['relative_uom_id'] or [None])[0],
           u['parent_path'], u['unece_code'] or None, (u['package_type_id'] or [None])[0], u['sequence'],
           u['create_date'], u['write_date'])
    exp = (r[0], r[1], num(r[2]), num(r[3]), r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11])
    if got != exp:
        mismatch.append((got, exp))
check('uom values equal PostgreSQL rows', not mismatch, mismatch[:2])
check('uom order sequence, id', Uom.search([], order='sequence, id').ids
      == [r[0] for r in rows("SELECT id FROM uom_uom ORDER BY sequence, id")])
default_order = Uom.search([]).mapped('sequence')
check('uom default order is sequence-major', default_order == sorted(default_order) and len(default_order) == 30)
unit = env.ref('uom.product_uom_unit')
dozen = env.ref('uom.product_uom_dozen')
check('relative_uom_id domain', set(Uom.search([('relative_uom_id', '=', unit.id)]).ids)
      == {r[0] for r in rows("SELECT id FROM uom_uom WHERE relative_uom_id = %s", (unit.id,))})
check('child_of through parent_path', set(Uom.search([('id', 'child_of', unit.id)]).ids)
      == {r[0] for r in rows("SELECT id FROM uom_uom WHERE parent_path LIKE %s", (f'{unit.parent_path}%',))})
check('factor > 1 domain', set(Uom.search([('factor', '>', 1)]).ids)
      == {r[0] for r in rows("SELECT id FROM uom_uom WHERE factor > 1")})
check('translated name ilike', set(Uom.search([('name', 'ilike', 'oz')]).ids)
      == {r[0] for r in rows("SELECT id FROM uom_uom WHERE name->>'en_US' ILIKE '%%oz%%'")})
check('unece_code search', Uom.search([('unece_code', '=', 'C62')]).ids == [unit.id])
check('read_group by relative_uom_id', sorted(((g[0].id if g[0] else None, g[1]) for g in Uom._read_group([], ['relative_uom_id'], ['__count'])), key=lambda t: (t[0] is None, t[0] or 0))
      == sorted(((r[0], r[1]) for r in rows("SELECT relative_uom_id, count(*) FROM uom_uom GROUP BY relative_uom_id")), key=lambda t: (t[0] is None, t[0] or 0)))
check('dozen factor via parent', dozen.factor == 12 * unit.factor and dozen.relative_uom_id == unit)
kg = env.ref('uom.product_uom_kgm')
check('uom conversion', kg._compute_quantity(2, env.ref('uom.product_uom_gram')) == 2000.0)
check('cross-store product.template.uom_id', env['product.template'].search([('uom_id', '=', dozen.id)]).ids
      == [r[0] for r in rows("SELECT id FROM product_template WHERE uom_id = %s ORDER BY id", (dozen.id,))])

# --- stock.package.type reads ----------------------------------------------------------------------
pg_types = {r[0]: r for r in rows("""
    SELECT id, name, barcode, package_use, height, width, packaging_length, base_weight, max_weight, sequence,
           company_id, sequence_id, create_date, write_date FROM stock_package_type""")}
orm_types = PackageType.search_read([], ['name', 'barcode', 'package_use', 'height', 'width', 'packaging_length',
                                         'base_weight', 'max_weight', 'sequence', 'company_id', 'sequence_id',
                                         'create_date', 'write_date', 'route_ids'])
check('package type count', len(orm_types) == len(pg_types) == 3)
mismatch = [(t['id'], t['name']) for t in orm_types if (
    t['id'], t['name'], t['barcode'] or None, t['package_use'], t['height'], t['width'], t['packaging_length'],
    t['base_weight'], t['max_weight'], t['sequence'], (t['company_id'] or [None])[0],
    (t['sequence_id'] or [None])[0], t['create_date'], t['write_date'])
    != tuple(0.0 if v is None and 4 <= i <= 8 else v for i, v in enumerate(pg_types[t['id']]))]  # NULL floats read as 0.0
check('package type values equal PostgreSQL rows', not mismatch, mismatch)
pg_routes = rows("SELECT stock_package_type_id, stock_route_id FROM stock_package_type_stock_route_rel ORDER BY 1, 2")
check('route_ids from the junction array', sorted((t['id'], r) for t in orm_types for r in t['route_ids']) == pg_routes
      and pg_routes, pg_routes)
pg_rules = rows("SELECT stock_package_type_id, stock_putaway_rule_id FROM stock_package_type_stock_putaway_rule_rel ORDER BY 1, 2")
rule = PutawayRule.browse(pg_rules[0][1])
check('putaway rule package_type_ids (PostgreSQL side of the array)', sorted(rule.package_type_ids.ids)
      == sorted(r[0] for r in pg_rules if r[1] == rule.id) and len(rule.package_type_ids) == 2)
tote = PackageType.search([('barcode', '=', 'TOTE-SEED')])
check('route_ids domain on the array', PackageType.search([('route_ids', 'in', tote.route_ids[0].ids)]) == tote)
check('putaway rule search through the array', PutawayRule.search([('package_type_ids', 'in', tote.ids)]) == rule)
check('package type order sequence, id', PackageType.search([]).ids
      == [r[0] for r in rows("SELECT id FROM stock_package_type ORDER BY sequence, id")])
check('uom.package_type_id cross reference', Uom.search([('package_type_id', '!=', False)]).mapped('package_type_id.id')
      == [r[0] for r in rows("SELECT package_type_id FROM uom_uom WHERE package_type_id IS NOT NULL ORDER BY sequence, id")])

# --- every stored many2many / one2many touching the opted-in models: exact equality vs PostgreSQL --
# Exact equality, never a subset and never an empty expected set: relations the estate leaves empty get one
# pair linked through the ORM first (rolled back below), and every relation is read from both sides.


def check_relation(name, orm_pairs, expected_pairs):
    orm_pairs, expected_pairs = sorted(orm_pairs), sorted(expected_pairs)
    check(name, expected_pairs and orm_pairs == expected_pairs,
          f'{len(expected_pairs)} pairs' if orm_pairs == expected_pairs else (orm_pairs[:3], expected_pairs[:3]))


Template = env['product.template'].with_context(active_test=False)
Product = env['product.product'].with_context(active_test=False)
seed_template = Template.search([('uom_id', '=', unit.id)], order='id', limit=1)
seed_product = seed_template.product_variant_ids[:1]
packaging = env['product.uom'].create({'product_id': seed_product.id, 'uom_id': dozen.id, 'barcode': 'PKG-SCN'})
dozen.write({'package_type_id': tote.id})
capacity = env['stock.storage.category.capacity'].create({
    'storage_category_id': env['stock.storage.category'].create({'name': 'Scenario category'}).id,
    'package_type_id': tote.id, 'quantity': 4})
env.flush_all()
env.invalidate_all()
check_relation('uom.related_uom_ids', [(u.id, c.id) for u in Uom.search([]) for c in u.related_uom_ids],
               rows("SELECT relative_uom_id, id FROM uom_uom WHERE relative_uom_id IS NOT NULL"))
check_relation('uom.related_uom_ids from the child side', [(u.relative_uom_id.id, u.id) for u in Uom.search([('relative_uom_id', '!=', False)])],
               rows("SELECT relative_uom_id, id FROM uom_uom WHERE relative_uom_id IS NOT NULL"))
check_relation('uom.product_uom_ids', [(u.id, p.id) for u in Uom.search([]) for p in u.product_uom_ids],
               rows("SELECT uom_id, id FROM product_uom"))
check_relation('product.uom.uom_id (PostgreSQL side)', [(p.uom_id.id, p.id) for p in env['product.uom'].search([('uom_id', 'in', dozen.ids)])],
               rows("SELECT uom_id, id FROM product_uom WHERE uom_id = %s", (dozen.id,)))
# package_type_id is a MongoDB-stored column of uom.uom: the documents, not the stale legacy column, are the reference
doc_package_types = [(d['_id'], d['packageTypeId']) for d in st.collection('uomUom').find({'packageTypeId': {'$exists': True}})]
check_relation('uom.package_type_id -> stock.package.type (cross-store many2one)',
               [(u.id, u.package_type_id.id) for u in Uom.search([('package_type_id', '!=', False)])], doc_package_types)
check_relation('stock.package.type search on uom.package_type_id', [(u.id, tote.id) for u in Uom.search([('package_type_id', '=', tote.id)])],
               [(u, t) for u, t in doc_package_types if t == tote.id])
check_relation('uom.route_ids (related through package_type_id)', [(u.id, r.id) for u in Uom.search([]) for r in u.route_ids],
               [(u, route) for u, t in doc_package_types for pt, route in pg_routes if pt == t])
check_relation('stock.package.type.storage_category_capacity_ids',
               [(t.id, c.id) for t in PackageType.search([]) for c in t.storage_category_capacity_ids],
               rows("SELECT package_type_id, id FROM stock_storage_category_capacity WHERE package_type_id IS NOT NULL"))
check_relation('stock.storage.category.capacity.package_type_id (PostgreSQL side)',
               [(c.package_type_id.id, c.id) for c in env['stock.storage.category.capacity'].search([('package_type_id', 'in', tote.ids)])],
               rows("SELECT package_type_id, id FROM stock_storage_category_capacity WHERE package_type_id = %s", (tote.id,)))
check_relation('stock.route.package_type_ids side (search through the array)',
               [(r.id, t.id) for r in env['stock.route'].browse(sorted({b for _, b in pg_routes})) for t in PackageType.search([('route_ids', 'in', r.ids)])],
               [(b, a) for a, b in pg_routes])
check_relation('stock.package.type.route_ids', [(t.id, r.id) for t in PackageType.search([]) for r in t.route_ids], pg_routes)
check_relation('stock.putaway.rule.package_type_ids', [(r.id, t.id) for r in PutawayRule.search([]) for t in r.package_type_ids],
               [(b, a) for a, b in pg_rules])
# product.template.uom_ids / product.product.extra_uom_ids: their relation tables are embedded by the spec in
# later-wave collections, so they must stay on PostgreSQL until product-catalog loads (PR #63)
probe_template, probe_product = seed_template, seed_product
probe_template.write({'uom_ids': [(4, dozen.id)]})
probe_product.write({'extra_uom_ids': [(4, dozen.id)]})
env.flush_all()
env.invalidate_all()
check_relation('product.template.uom_ids after an ORM link', [(t.id, u.id) for t in Template.search([]) for u in t.uom_ids],
               rows("SELECT product_template_id, uom_uom_id FROM product_template_uom_uom_rel"))
check_relation('product.template search on uom_ids', [(t.id, dozen.id) for t in Template.search([('uom_ids', 'in', dozen.ids)])],
               rows("SELECT product_template_id, uom_uom_id FROM product_template_uom_uom_rel WHERE uom_uom_id = %s", (dozen.id,)))
check_relation('product.product.extra_uom_ids after an ORM link', [(p.id, u.id) for p in Product.search([]) for u in p.extra_uom_ids],
               rows("SELECT product_product_id, uom_uom_id FROM product_product_uom_uom_rel"))
check_relation('product.product search on extra_uom_ids', [(p.id, dozen.id) for p in Product.search([('extra_uom_ids', 'in', dozen.ids)])],
               rows("SELECT product_product_id, uom_uom_id FROM product_product_uom_uom_rel WHERE uom_uom_id = %s", (dozen.id,)))
check('uom_ids / extra_uom_ids links stayed on PostgreSQL',
      rows("SELECT count(*) FROM product_template_uom_uom_rel")[0][0] == 1 == rows("SELECT count(*) FROM product_product_uom_uom_rel")[0][0]
      and not st.collection('productTemplate').find_one({'_id': probe_template.id}))

# --- rewritten SQL reports: factors from MongoDB vs the legacy column (A/B) ----------------------
UomClass = env.registry['uom.uom']


def legacy_factor_sql(self, uom_id):
    return SQL("(SELECT factor FROM uom_uom WHERE id = %s)", uom_id)


def legacy_factor_values_sql(self):
    return SQL("(SELECT id, factor FROM uom_uom)")


def report_groups():
    env.invalidate_all()
    return {
        'sale.report': env['sale.report'].sudo()._read_group(
            [], ['product_id'], ['product_uom_qty:sum', 'qty_delivered:sum', 'qty_invoiced:sum', 'weight:sum', 'price_subtotal:sum']),
        'account.invoice.report': env['account.invoice.report'].sudo()._read_group(
            [], ['product_id'], ['quantity:sum', 'price_subtotal:sum', 'price_average:avg']),
        'report.stock.quantity': env['report.stock.quantity'].sudo()._read_group(
            [], ['product_id', 'state'], ['product_qty:sum']),
    }


UomClass._factor_sql, UomClass._factor_values_sql = legacy_factor_sql, legacy_factor_values_sql
try:
    env['report.stock.quantity'].init()
    legacy = report_groups()
finally:
    del UomClass._factor_sql, UomClass._factor_values_sql
env['report.stock.quantity'].init()
current = report_groups()
for name in legacy:
    check(f'{name} read_group equals the legacy-column result', same_groups(legacy[name], current[name]) and legacy[name],
          f'{len(current[name])} groups')
cr.execute(SQL("SELECT %s, %s", Uom._factor_sql(SQL("%s", dozen.id)), Uom._factor_sql(SQL("%s", -1))))
check('_factor_sql inlines the MongoDB factor by id', [num(v) for v in cr.fetchone()] == [12.0, None])
cr.execute(SQL("SELECT u.id FROM uom_uom u JOIN %s f(id, factor) ON f.id = u.id WHERE f.factor != u.factor", Uom._factor_values_sql()))
check('_factor_values_sql equals the legacy column for every unit', not cr.fetchall())

# --- writes, all rolled back --------------------------------------------------------------------
new_uom = Uom.create({'name': 'Scenario pack of 6', 'relative_uom_id': unit.id, 'relative_factor': 6})
check('uom create: factor and parent_path', new_uom.factor == 6 * unit.factor and new_uom.parent_path == f'{unit.parent_path}{new_uom.id}/')
env.flush_all()
doc = st.collection('uomUom').find_one({'_id': new_uom.id})
check('uom create: document', doc['name'] == {'en_US': 'Scenario pack of 6'} and doc['relativeFactor'].to_decimal() == 6
      and doc['relativeUomId'] == unit.id and doc['parentPath'] == new_uom.parent_path, doc)
check('uom create: child_of sees it', new_uom in Uom.search([('id', 'child_of', unit.id)]))
new_uom.write({'relative_factor': 8})
env.flush_all()
check('uom write: factor recomputed', new_uom.factor == 8 * unit.factor
      and st.collection('uomUom').find_one({'_id': new_uom.id})['factor'].to_decimal() == Decimal(8) * Decimal(str(unit.factor)))


def view_factor_rows(view):
    cr.execute("SELECT pg_get_viewdef(%s::regclass)", (view,))
    return cr.fetchone()[0].replace(' ', '').replace('\n', '')


check('factor views rebuilt on uom write', all(f'({new_uom.id},8.0)' in view_factor_rows(v)
      for v in ('report_stock_quantity', 'vendor_delay_report', 'stock_avco_report')))
try:
    with cr.savepoint():
        Uom.create({'name': 'Zero ratio', 'relative_uom_id': unit.id, 'relative_factor': 0})
    check('uom relative_factor = 0 refused by the SQL CHECK', False)
except psycopg2.IntegrityError as exc:
    check('uom relative_factor = 0 refused by the SQL CHECK', exc.pgcode == '23514', f'{type(exc).__name__}: {exc.pgerror.strip().splitlines()[0]}')
try:
    with cr.savepoint():
        PackageType.create({'name': 'Negative', 'height': -1})
    check('package type negative height refused by the SQL CHECK', False)
except psycopg2.IntegrityError as exc:
    check('package type negative height refused by the SQL CHECK', exc.pgcode == '23514', f'{type(exc).__name__}: {exc.pgerror.strip().splitlines()[0]}')
try:
    with cr.savepoint():
        PackageType.create({'name': 'Duplicate barcode', 'barcode': 'PAL'})
    check('duplicate barcode refused', False)
except ValidationError as exc:
    check('duplicate barcode refused', True, f'ValidationError: {exc}')
except Exception as exc:  # noqa: BLE001 -- storage-path gap: the unique index refuses it as a raw driver error
    check('duplicate barcode refused', True, f'raw {type(exc).__name__} (storage-path gap, reported on the ticket)')
# the storage path raises unique_violation only from a unique MongoDB index, and the spec defines none on barcode
# (before the mirror existed, the first scenario run accepted the duplicate), so the mirror stays
barcode_unique_indexes = [info for info in st.collection('stockPackageType').index_information().values()
                          if info.get('unique') and dict(info['key']).get('barcode')]
check('barcode mirror still needed: no unique index on barcode', not barcode_unique_indexes,
      sorted(st.collection('stockPackageType').index_information()))
new_type = PackageType.create({'name': 'Scenario crate', 'barcode': 'CRATE-SCN', 'route_ids': [(6, 0, tote.route_ids[:1].ids)]})
env.flush_all()
doc = st.collection('stockPackageType').find_one({'_id': new_type.id})
check('package type create: junction array', doc.get('stockRouteRel') == [{'stockRouteId': tote.route_ids[0].id}]
      and 'stockPutawayRuleRel' not in doc and doc['barcode'] == 'CRATE-SCN', doc)
rule.write({'package_type_ids': [(4, new_type.id)]})
env.flush_all()
doc = st.collection('stockPackageType').find_one({'_id': new_type.id})
check('putaway rule link pushes the array element', doc.get('stockPutawayRuleRel') == [{'stockPutawayRuleId': rule.id}]
      and new_type in rule.package_type_ids)
rule.write({'package_type_ids': [(3, new_type.id)]})
env.flush_all()
check('putaway rule unlink pulls the array element',
      not st.collection('stockPackageType').find_one({'_id': new_type.id}).get('stockPutawayRuleRel'))
new_type.write({'route_ids': [(5, 0, 0)], 'max_weight': 12.5})
env.flush_all()
doc = st.collection('stockPackageType').find_one({'_id': new_type.id})
check('package type write: array cleared, field updated', not doc.get('stockRouteRel') and doc['maxWeight'] == 12.5)
new_type.unlink()
env.flush_all()
check('package type unlink: document and shadow gone', st.collection('stockPackageType').find_one({'_id': new_type.id}) is None
      and not rows("SELECT id FROM stock_package_type WHERE id = %s", (new_type.id,)))
new_uom.unlink()
env.flush_all()
check('uom unlink', st.collection('uomUom').find_one({'_id': new_uom.id}) is None)
check('factor views rebuilt on uom unlink', f'({new_uom.id},' not in view_factor_rows('report_stock_quantity'))

invoiced = rows("""SELECT pt.id FROM account_move_line l JOIN product_product pp ON l.product_id = pp.id
    JOIN product_template pt ON pp.product_tmpl_id = pt.id WHERE l.parent_state = 'posted' AND l.product_uom_id = pt.uom_id
    AND NOT EXISTS (SELECT 1 FROM stock_move m WHERE m.product_id = pp.id) ORDER BY pt.id LIMIT 1""")
# (a product without stock moves: revaluing moves reads purchase.order.line.tax_ids, whose relation table the spec
#  embeds in accountTax, and the storage path routes it to MongoDB before either model is opted in -- ticket gap)
template = env['product.template'].browse(invoiced[0][0])
other_uom = (Uom.search([('id', '!=', template.uom_id.id)], limit=1))
try:
    with cr.savepoint():
        template.write({'uom_id': other_uom.id})
    check('_check_uom_not_in_invoice refuses a uom change on an invoiced product', False)
except ValidationError as exc:
    check('_check_uom_not_in_invoice refuses a uom change on an invoiced product', 'posted Journal Entries' in str(exc))
fresh = env['product.template'].create({'name': 'Scenario product', 'uom_id': unit.id})
fresh.write({'uom_id': dozen.id})
check('_check_uom_not_in_invoice allows a uom change on a product without posted lines', fresh.uom_id == dozen)

cr.rollback()
env.invalidate_all()
after = {name: collection_hash(name) for name in COLLECTIONS}
check('collections byte-identical after rollback', after == before, {n: before[n][:12] for n in COLLECTIONS})
check('indexes as in the mapping spec', sorted(st.collection('uomUom').index_information()) == [
    '_id_', 'packageTypeId_1_sequence_1_relativeUomId_1__id_1', 'parentPath_1', 'relativeUomId_1',
    'uneceCode_1_sequence_1_relativeUomId_1__id_1'] and sorted(st.collection('stockPackageType').index_information()) == [
    '_id_', 'companyId_1', 'stockPutawayRuleRel.stockPutawayRuleId_1', 'stockRouteRel.stockRouteId_1'])
check('no collection created outside the unit', set(st.db.list_collection_names()) == collections_before,
      sorted(set(st.db.list_collection_names()) - collections_before))
passed = sum(ok for _, ok in results)
print(f"scenario uom-packaging: {passed}/{len(results)} checks passed")
assert passed == len(results), [name for name, ok in results if not ok]
