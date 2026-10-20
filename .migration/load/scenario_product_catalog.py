"""ORM scenario for batch w2-b02 (unit product-catalog) on the MongoDB storage path.

Run on the run branch against the worker's seeded clone with a conf whose ``mongodb_migration_db`` differs
from the clone, so the registry reads ``<clone>__<collection>`` and no ORM write can reach the live
collections. Every collection an opted-in model reads is copied fresh under that prefix at the start of each run (aggregate $out):

    /home/ubuntu/.venvs/odoo/bin/python odoo-bin shell -c <conf> -d <clone> --no-http \\
        < .migration/load/scenario_product_catalog.py

Reads are compared with the clone's PostgreSQL rows (the clone still carries the legacy columns). The two
rewritten raw-SQL sites (product.product / product.template ``_search_display_name``, UNION ALL replaced by
one Domain.OR search) are compared with the same match computed in SQL. Every write happens in one
transaction that is rolled back at the end, and the collections are hashed before and after.
"""
import hashlib
from decimal import Decimal

from bson.json_util import dumps

cr = env.cr
st = env.registry.mongo_store
COLLECTIONS = ('productTemplate', 'productProduct', 'productTemplateAttributeValue',
               'productAttributeValueProductTemplateAttributeLineRel', 'productCombo', 'productSupplierinfo',
               'productPricelist', 'productPricelistItem')
print(f"collection prefix {st.prefix!r}")
assert st.prefix, "refusing to run unprefixed: the conf must set mongodb_migration_db to another name"
# every collection an opted-in model reads (this unit's and the merged waves') must exist under the prefix
by_table = {Model._table: Model for Model in env.registry.models.values() if not Model._abstract}
served = {spec.collection for table, spec in st.spec.by_table.items()
          if (table in by_table and by_table[table]._storage == 'mongodb') or (table not in by_table and st.relation_served(spec))}
for name in sorted(served):
    if st.db[name].estimated_document_count():
        st.db[name].aggregate([{'$match': {}}, {'$out': st.prefix + name}])
print(f"{len(served)} collections copied under the prefix (fresh copies of the live documents)")

Template = env['product.template'].with_context(active_test=False)
Product = env['product.product'].with_context(active_test=False)
Ptav = env['product.template.attribute.value'].with_context(active_test=False)
Line = env['product.template.attribute.line'].with_context(active_test=False)
Supplier = env['product.supplierinfo']
Pricelist = env['product.pricelist'].with_context(active_test=False)
Item = env['product.pricelist.item']
Combo = env['product.combo']
for model in (Template, Product, Ptav, Line, Supplier, Pricelist, Item, Combo, env['product.combo.item'],
              env['product.uom'], env['customer.product.reference']):
    assert model._storage == 'mongodb', model._name
results = []


def check(name, ok, detail=''):
    results.append((name, bool(ok)))
    print(f"{'PASS' if ok else 'FAIL'} {name}{' -- ' + str(detail) if detail else ''}")


def collection_hash(name):
    docs = list(st.collection(name).find({}, sort=[('_id', 1)]))
    return hashlib.sha256(dumps(docs, sort_keys=True).encode()).hexdigest()


def rows(sql, params=()):
    cr.execute(sql, params)
    return cr.fetchall()


def num(v):
    return float(v) if isinstance(v, Decimal) else v


def m2o(v):
    return v[0] if v else None


def scalar(v):
    return m2o(v) if isinstance(v, (tuple, list)) else num(v) if v is not None else None


def same_rows(name, model, table, fields, columns=None, where=''):
    """search_read of ``fields`` equals SELECT of ``columns`` (NULL floats read as 0.0, m2o as id)."""
    columns = columns or fields
    pg = {r[0]: tuple(num(v) for v in r[1:]) for r in rows(f"SELECT id, {', '.join(columns)} FROM {table} {where}")}
    orm = model.search_read([], fields)
    mismatch = []
    for rec in orm:
        got = tuple(scalar(rec[f]) if rec[f] is not False else None for f in fields)
        exp = pg.get(rec['id'])
        if exp is None or any(g != e and not (g in (0.0, None) and e in (0.0, None)) and not (g is None and e is False) for g, e in zip(got, exp)):
            mismatch.append((rec['id'], got, exp))
    check(name, len(orm) == len(pg) > 0 and not mismatch, f'{len(pg)} rows' if not mismatch else mismatch[:2])


def same_pairs(name, orm_pairs, sql):
    expected = sorted(tuple(r) for r in rows(sql))
    check(name, expected and sorted(orm_pairs) == expected, f'{len(expected)} pairs' if sorted(orm_pairs) == expected else (sorted(orm_pairs)[:3], expected[:3]))


before = {name: collection_hash(name) for name in COLLECTIONS}
collections_before = set(st.db.list_collection_names())

# --- reads: every root equals its PostgreSQL rows ------------------------------------------------
same_rows('product.template rows', Template, 'product_template',
          ['list_price', 'categ_id', 'uom_id', 'type', 'sale_ok', 'purchase_ok', 'active', 'create_date', 'write_date'])
same_rows('product.product rows', Product, 'product_product',
          ['product_tmpl_id', 'default_code', 'barcode', 'active', 'combination_indices', 'create_date', 'write_date'])
same_rows('product.template.attribute.value rows', Ptav, 'product_template_attribute_value',
          ['product_tmpl_id', 'attribute_line_id', 'product_attribute_value_id', 'price_extra', 'ptav_active'])
same_rows('product.template.attribute.line rows (embedded in productTemplate.attributeLine)', Line,
          'product_template_attribute_line', ['product_tmpl_id', 'attribute_id', 'sequence', 'value_count', 'active'])
same_rows('product.supplierinfo rows', Supplier, 'product_supplierinfo',
          ['partner_id', 'product_tmpl_id', 'product_id', 'sequence', 'min_qty', 'price', 'delay', 'create_date'])
same_rows('product.pricelist rows', Pricelist, 'product_pricelist', ['sequence', 'active', 'currency_id', 'company_id', 'create_date'])
same_rows('product.pricelist.item rows', Item, 'product_pricelist_item',
          ['pricelist_id', 'applied_on', 'compute_price', 'product_tmpl_id', 'min_quantity', 'fixed_price', 'price_discount', 'create_date'])
same_rows('product.combo rows', Combo, 'product_combo', ['sequence', 'company_id', 'create_date'])
same_rows('product.combo.item rows (embedded in productCombo.item)', env['product.combo.item'], 'product_combo_item',
          ['combo_id', 'product_id', 'extra_price', 'company_id'])
same_rows('product.uom rows (embedded in productProduct.productUom)', env['product.uom'], 'product_uom',
          ['product_id', 'uom_id', 'barcode', 'company_id', 'create_date'])
same_rows('customer.product.reference rows (embedded element keyed by partnerId: shared storage path reads partner_id as the record id, reported to the manager)',
          env['customer.product.reference'], 'customer_product_reference', ['product_id', 'partner_id', 'customer_product_reference'])
check('translated template names', all(t.name == n for t, n in zip(Template.search([], order='id'),
      [r[0] for r in rows("SELECT name->>'en_US' FROM product_template ORDER BY id")])))
check('translated pricelist names', sorted(Pricelist.search([]).mapped('name')) == sorted(r[0] for r in rows("SELECT name->>'en_US' FROM product_pricelist")))

# --- every array / relation of the eight collections, read from both sides ---------------------------
same_pairs('template.uom_ids = productTemplate.uomUomRel', [(t.id, u) for t in Template.search([]) for u in t.uom_ids.ids],
           "SELECT product_template_id, uom_uom_id FROM product_template_uom_uom_rel")
same_pairs('template.optional_product_ids = productTemplate.productOptionalRel',
           [(t.id, o) for t in Template.search([]) for o in t.optional_product_ids.ids],
           "SELECT src_id, dest_id FROM product_optional_rel")
same_pairs('template.attribute_line_ids = productTemplate.attributeLine',
           [(t.id, l) for t in Template.search([]) for l in t.attribute_line_ids.ids],
           "SELECT product_tmpl_id, id FROM product_template_attribute_line")
same_pairs('line.value_ids = relation collection (served from MongoDB)',
           [(l.id, v) for l in Line.search([]) for v in l.value_ids.ids],
           "SELECT product_template_attribute_line_id, product_attribute_value_id FROM product_attribute_value_product_template_attribute_line_rel")
same_pairs('value.pav_attribute_line_ids = relation collection (other side, PostgreSQL model w1-b05)',
           [(v.id, l) for v in env['product.attribute.value'].with_context(active_test=False).search([]) for l in v.pav_attribute_line_ids.ids],
           "SELECT product_attribute_value_id, product_template_attribute_line_id FROM product_attribute_value_product_template_attribute_line_rel")
check('relation table is served from MongoDB', st.relation_served(st.spec.for_table('product_attribute_value_product_template_attribute_line_rel')))
same_pairs('variant.product_template_attribute_value_ids = productProduct.productVariantCombination',
           [(p.id, v) for p in Product.search([]) for v in p.product_template_attribute_value_ids.ids],
           "SELECT product_product_id, product_template_attribute_value_id FROM product_variant_combination")
same_pairs('ptav.ptav_product_variant_ids (other side of the array)',
           [(v.id, p) for v in Ptav.search([]) for p in v.ptav_product_variant_ids.ids],
           "SELECT product_template_attribute_value_id, product_product_id FROM product_variant_combination")
same_pairs('variant.extra_uom_ids = productProduct.uomUomRel', [(p.id, u) for p in Product.search([]) for u in p.extra_uom_ids.ids],
           "SELECT product_product_id, uom_uom_id FROM product_product_uom_uom_rel")
same_pairs('variant.product_uom_ids = productProduct.productUom', [(p.id, u) for p in Product.search([]) for u in p.product_uom_ids.ids],
           "SELECT product_id, id FROM product_uom")
same_pairs('ptav.excluded_value_ids = productTemplateAttributeValue.productTemplateAttributeExcludedValueIdsRel',
           [(v.id, e) for v in Ptav.search([]) for e in v.excluded_value_ids.ids],
           "SELECT product_template_attribute_value_id, excluded_product_template_attribute_value_id FROM product_template_attribute_excluded_value_ids_rel")
same_pairs('sale.order.line.product_no_variant_attribute_value_ids (PostgreSQL side of productTemplateAttributeValue.saleOrderLineRel)',
           [(l.id, v) for l in env['sale.order.line'].search([('product_no_variant_attribute_value_ids', '!=', False)]) for v in l.product_no_variant_attribute_value_ids.ids],
           "SELECT sale_order_line_id, product_template_attribute_value_id FROM product_template_attribute_value_sale_order_line_rel")
same_pairs('purchase.order.line.product_no_variant_attribute_value_ids (PostgreSQL side of purchaseOrderLineRel)',
           [(l.id, v) for l in env['purchase.order.line'].search([('product_no_variant_attribute_value_ids', '!=', False)]) for v in l.product_no_variant_attribute_value_ids.ids],
           "SELECT purchase_order_line_id, product_template_attribute_value_id FROM product_template_attribute_value_purchase_order_line_rel")
same_pairs('stock.move.never_product_template_attribute_value_ids (PostgreSQL side of templateAttributeValueStockMoveRel)',
           [(m.id, v) for m in env['stock.move'].search([('never_product_template_attribute_value_ids', '!=', False)]) for v in m.never_product_template_attribute_value_ids.ids],
           "SELECT move_id, template_attribute_value_id FROM template_attribute_value_stock_move_rel")
same_pairs('combo.combo_item_ids = productCombo.item', [(c.id, i) for c in Combo.search([]) for i in c.combo_item_ids.ids],
           "SELECT combo_id, id FROM product_combo_item")
same_pairs('template.combo_ids = productCombo.productTemplateRel', [(t.id, c) for t in Template.search([]) for c in t.combo_ids.ids],
           "SELECT product_template_id, product_combo_id FROM product_combo_product_template_rel")
same_pairs('pricelist.item_ids = productPricelistItem.pricelistId', [(p.id, i) for p in Pricelist.search([]) for i in p.item_ids.ids],
           "SELECT pricelist_id, id FROM product_pricelist_item")
same_pairs('template.seller_ids = productSupplierinfo.productTmplId', [(t.id, s) for t in Template.search([]) for s in t.seller_ids.ids],
           "SELECT product_tmpl_id, id FROM product_supplierinfo WHERE product_tmpl_id IS NOT NULL")

# --- the two rewritten raw-SQL sites ------------------------------------------------------------------
pg_code = {r[0] for r in rows("SELECT id FROM product_product WHERE default_code ILIKE '%%FURN_00%%'")}
pg_name = {r[0] for r in rows("SELECT p.id FROM product_product p JOIN product_template t ON t.id = p.product_tmpl_id WHERE t.name->>'en_US' ILIKE '%%desk%%'")}
check('product.product name_search by default_code (rewritten _search_display_name)', {r[0] for r in Product.name_search('FURN_00', limit=None)} == pg_code and pg_code, len(pg_code))
check('product.product name_search by template name', {r[0] for r in Product.name_search('desk', limit=None)} >= pg_name and pg_name, len(pg_name))
acme = env['res.partner'].browse(10)
seller = Supplier.search([('partner_id', '=', acme.id)], limit=1)
seller_products = set(Product.search([('product_tmpl_id', '=', seller.product_tmpl_id.id)]).ids)
check('product.product name_search with partner_id context (supplierinfo branch, ids instead of a sub-select)',
      seller and seller_products <= {r[0] for r in Product.with_context(partner_id=acme.id).name_search(seller.product_code or seller.product_name or seller.product_tmpl_id.name, limit=None)},
      (seller.id, seller.product_code, seller.product_name))
check('product.template name_search reaches variants by default_code (rewritten UNION)', Template.name_search('FURN_0096', limit=None) and
      {r[0] for r in Template.name_search('FURN_0096', limit=None)} == {r[0] for r in rows("SELECT DISTINCT product_tmpl_id FROM product_product WHERE default_code ILIKE '%%FURN_0096%%'")})
check('product.template negative name_search', not Template.name_search('FURN_0096', operator='not ilike', limit=None) or
      all(r[0] != 9 for r in Template.name_search('FURN_0096', operator='not ilike', limit=None)))

# --- behaviour on the loaded rows -------------------------------------------------------------------
desk = Template.browse(9)
variant = Product.browse(13)
wholesale = Pricelist.search([('name', '=', 'Seeded wholesale')])
check('pricelist fixed rule at min_quantity', wholesale and wholesale._get_product_price(variant, 2.0) == 950.0, wholesale._get_product_price(variant, 2.0) if wholesale else None)
check('pricelist global discount below min_quantity', wholesale and abs(wholesale._get_product_price(variant, 1.0) - variant.lst_price * 0.9) < 1e-6)
# _select_seller keeps the vendor of the first line in the model order (sequence, min_qty DESC, price, id),
# then takes that vendor's cheapest discounted line
pg_seller = rows("""WITH candidates AS (SELECT * FROM product_supplierinfo WHERE product_tmpl_id = %s AND min_qty <= 1 AND product_id IS NULL)
                    SELECT id FROM candidates
                    WHERE partner_id = (SELECT partner_id FROM candidates ORDER BY sequence, min_qty DESC, price, id LIMIT 1)
                    ORDER BY price * (1 - COALESCE(discount, 0) / 100.0), sequence, id LIMIT 1""", (seller.product_tmpl_id.id,))
seller_info = Product.search([('product_tmpl_id', '=', seller.product_tmpl_id.id)], limit=1)._select_seller(quantity=1.0)
check('_select_seller picks the PostgreSQL-ordered vendor line', seller_info and seller_info['supplierinfo'].id == pg_seller[0][0],
      (seller_info.get('supplierinfo') and seller_info['supplierinfo'].id, pg_seller))
check('variant count per template', {t.id: t.product_variant_count for t in Template.search([])} ==
      {r[0]: r[1] for r in rows("SELECT product_tmpl_id, count(*) FROM product_product WHERE active GROUP BY product_tmpl_id")} | {t.id: 0 for t in Template.search([('product_variant_ids', '=', False)])})
check('order by sequence on pricelists', Pricelist.search([]).ids == [r[0] for r in rows("SELECT id FROM product_pricelist ORDER BY sequence, id, name->>'en_US'")])
check('domain through many2one into a sibling MongoDB model', set(Product.search([('product_tmpl_id.categ_id', '=', desk.categ_id.id)]).ids) ==
      {r[0] for r in rows("SELECT p.id FROM product_product p JOIN product_template t ON t.id = p.product_tmpl_id WHERE t.categ_id = %s", (desk.categ_id.id,))})
check('read_group on productSupplierinfo by partner', sorted((g[0].id, g[1]) for g in Supplier._read_group([], ['partner_id'], ['__count'])) ==
      sorted(tuple(r) for r in rows("SELECT partner_id, count(*) FROM product_supplierinfo GROUP BY partner_id")))

# --- register re-checks: reports joining product tables still read (owners re-grade values) ---------
for report in ('sale.report', 'purchase.report', 'account.invoice.report'):
    groups = env[report]._read_group([], ['product_id'], ['__count'])
    check(f'{report} _read_group by product_id runs', sum(g[1] for g in groups) == env[report].search_count([]) > 0, sum(g[1] for g in groups))
for report, view in (('report.stock.quantity', 'report_stock_quantity'), ('stock.avco.report', 'stock_avco_report'), ('vendor.delay.report', 'vendor_delay_report')):
    check(f'{report} reads (PostgreSQL view joining the legacy product columns: finding for the owner)', env[report].search_count([]) == rows(f"SELECT count(*) FROM {view}")[0][0] > 0)

# --- writes through the storage path, then rolled back ----------------------------------------------
attribute = Ptav.browse(1).attribute_id
values = attribute.value_ids.sorted('id')[:2]
new = Template.create({'name': 'Scenario desk', 'list_price': 10.0,
                       'attribute_line_ids': [(0, 0, {'attribute_id': attribute.id, 'value_ids': [(6, 0, values.ids)]})]})
env.flush_all()
rel = st.collection('productAttributeValueProductTemplateAttributeLineRel')
check('template create writes the document', st.collection('productTemplate').find_one({'_id': new.id}) is not None)
check('attribute line creates variants', len(new.product_variant_ids) == 2 and
      st.collection('productProduct').count_documents({'productTmplId': new.id}) == 2)
check('line values land in the relation collection', rel.count_documents({'productTemplateAttributeLineId': new.attribute_line_ids.id}) == 2)
check('template attribute values created', Ptav.search_count([('product_tmpl_id', '=', new.id)]) == 2)
new.write({'uom_ids': [(4, env.ref('uom.product_uom_dozen').id)], 'list_price': 12.5})
env.flush_all()
doc = st.collection('productTemplate').find_one({'_id': new.id})
check('template write updates scalar and junction array', float(doc['listPrice'].to_decimal()) == 12.5 and [e['uomUomId'] for e in doc.get('uomUomRel', [])] == [env.ref('uom.product_uom_dozen').id])
sup = Supplier.create({'partner_id': acme.id, 'product_tmpl_id': new.id, 'price': 4.0, 'min_qty': 3})
item = Item.create({'pricelist_id': wholesale.id, 'applied_on': '1_product', 'product_tmpl_id': new.id, 'compute_price': 'fixed', 'fixed_price': 9.0})
env.flush_all()
check('supplierinfo and pricelist item documents', st.collection('productSupplierinfo').find_one({'_id': sup.id}) is not None and
      st.collection('productPricelistItem').find_one({'_id': item.id}) is not None)
check('new pricelist rule applies', wholesale._get_product_price(new.product_variant_ids[0], 1.0) == 9.0)
new.attribute_line_ids.write({'value_ids': [(3, values[0].id)]})
env.flush_all()
check('removing a line value pulls the relation document', rel.count_documents({'productTemplateAttributeLineId': new.attribute_line_ids.id}) == 1)
cr.rollback()
env.invalidate_all()
after = {name: collection_hash(name) for name in COLLECTIONS}
check('rollback restores every collection', after == before, [n for n in COLLECTIONS if after[n] != before[n]])
check('no collection created outside the prefix', set(st.db.list_collection_names()) == collections_before,
      set(st.db.list_collection_names()) ^ collections_before)
cr.rollback()
failed = [n for n, ok in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed; failed: {failed}")
