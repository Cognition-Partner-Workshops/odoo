"""Tier-4 ORM scenario for unit product-variant-extras (w3-b04): the storage path serves
`product.attribute.custom.value` and the transient `product.label.layout` from MongoDB, including
sale's nullable unique constraint, stock's `move_ids` routed into the wizard document, the label
report (`_get_report_xml_id` / `_prepare_report_data` / `process`) and the transient vacuum.

Run from the run branch against a scratch clone of the seeded odoo_src clone, after
``-u product,sale,stock`` on it (PostgreSQL rows are the oracle, MongoDB the system under test),
with a conf whose ``mongodb_migration_db`` is NOT the scratch database, so every collection this
script touches is ``<scratch db>__*`` (the transient clean deletes the old wizard documents, which
must never happen to the loaded ones). That namespace must hold a copy of every unprefixed
collection first (a clone has committed shadow ids for every opted-in model, and the storage path
refuses to serve those from an empty namespace); the two unit collections are dropped from it at
the end and the loaded collections are counted unchanged::

    odoo-bin shell -d <scratch db> -c <conf> --no-http < .migration/load/scenario_variant_extras.py
"""
from odoo.tools import config

checks = []


def check(name, ok, detail=''):
    checks.append((name, bool(ok)))
    print(f"{'PASS' if ok else 'FAIL'} {name}{': ' + str(detail) if detail else ''}")


cr = env.cr
CV, Layout = env['product.attribute.custom.value'], env['product.label.layout']
store = env.registry.mongo_store
prefix = store.collection_prefix
check('scratch namespace is prefixed', prefix == f"{cr.dbname}__", prefix)
loaded = {n: store.db[n].count_documents({}) for n in ('productAttributeCustomValue', 'productLabelLayout')}
cv_coll, layout_coll = store.db[store.collection_name(CV)], store.db[store.collection_name(Layout)]
store.ensure_collection(CV)
store.ensure_collection(Layout)
check('scratch namespace holds a copy of the loaded collections',
      (cv_coll.name, layout_coll.name) == (prefix + 'productAttributeCustomValue', prefix + 'productLabelLayout')
      and cv_coll.count_documents({}) == loaded['productAttributeCustomValue'] > 0
      and layout_coll.count_documents({}) == loaded['productLabelLayout'] > 0, loaded)

# -- indexes: sale's unique(custom_ptav, sale_order_line_id) is a partial unique index
unique = [ix for ix in cv_coll.list_indexes() if ix.get('unique')]
sol_unique = next((ix for ix in unique if list(ix['key']) == ['customProductTemplateAttributeValueId', 'saleOrderLineId']), None)
check('sol_custom_value_unique is a partial unique index on (customPTAV, saleOrderLineId)',
      sol_unique is not None and 'saleOrderLineId' in sol_unique.get('partialFilterExpression', {}),
      sol_unique and sol_unique.get('partialFilterExpression'))
check('wizard multikey indexes on the four arrays',
      {tuple(ix['key'])[0] for ix in layout_coll.list_indexes()} >= {'productIds.productProductId',
      'productTmplIds.productTemplateId', 'productUomIds.productUomId', 'moveIds.stockMoveId'})

# -- reads = PostgreSQL rows
cr.execute("SELECT id, custom_product_template_attribute_value_id, custom_value, sale_order_line_id FROM product_attribute_custom_value ORDER BY id")
pg_cv = [(i, p, v or False, s or False) for i, p, v, s in cr.fetchall()]
values = CV.search([], order='id')
check('custom value search = PostgreSQL rows',
      [(v.id, v.custom_product_template_attribute_value_id.id, v.custom_value, v.sale_order_line_id.id) for v in values] == pg_cv,
      f"{len(values)} rows")
check('custom value default _order (ptav, id)',
      CV.search([]).ids == [i for i, *_ in sorted(pg_cv, key=lambda r: (r[1], r[0]))])
check('_compute_name prefixes the attribute value display name',
      all(v.name.startswith(v.custom_product_template_attribute_value_id.display_name) for v in values))
parentless = CV.search([('sale_order_line_id', '=', False)], order='id')
check('search sale_order_line_id = False (NULL semantics)', parentless.ids == [r[0] for r in pg_cv if not r[3]], parentless.ids)
cr.execute("SELECT sale_order_line_id, count(*) FROM product_attribute_custom_value WHERE sale_order_line_id IS NOT NULL GROUP BY 1 ORDER BY 1")
check('_read_group by sale_order_line_id',
      [(line.id, count) for line, count in
       CV._read_group([('sale_order_line_id', '!=', False)], ['sale_order_line_id'], ['__count'], order='sale_order_line_id')] == cr.fetchall())
line_values = env['sale.order.line'].browse(pg_cv[3][3]).product_custom_attribute_value_ids \
    if 'product_custom_attribute_value_ids' in env['sale.order.line']._fields else CV.browse()
check('sale.order.line.product_custom_attribute_value_ids one2many reads the document',
      line_values.ids == [r[0] for r in pg_cv if r[3] == pg_cv[3][3]], line_values.ids)

cr.execute("SELECT id, print_format, custom_quantity, with_price, move_quantity, print_packaging, pricelist_id, packaging_id FROM product_label_layout ORDER BY id")
pg_layouts = [(i, f, q, bool(w), m, bool(pp), pl or False, pk or False) for i, f, q, w, m, pp, pl, pk in cr.fetchall()]
layouts = Layout.search([], order='id')
check('label layout search = PostgreSQL rows',
      [(l.id, l.print_format, l.custom_quantity, l.with_price, l.move_quantity, l.print_packaging,
        l.pricelist_id.id, l.packaging_id.id) for l in layouts] == pg_layouts, f"{len(layouts)} wizard rows")
for field, rel, col in (('product_ids', 'product_label_layout_product_product_rel', 'product_product_id'),
                        ('product_tmpl_ids', 'product_label_layout_product_template_rel', 'product_template_id'),
                        ('product_uom_ids', 'product_label_layout_product_uom_rel', 'product_uom_id'),
                        ('move_ids', 'product_label_layout_stock_move_rel', 'stock_move_id')):
    cr.execute(f"SELECT product_label_layout_id, array_agg({col} ORDER BY {col}) FROM {rel} GROUP BY 1 ORDER BY 1")
    pg_rel = dict(cr.fetchall())
    check(f'{field} array = {rel}', {l.id: sorted(l[field].ids) for l in layouts if l[field]} == pg_rel, pg_rel)
check('search by product in the productIds array',
      Layout.search([('product_ids', 'in', layouts[0].product_ids[:1].ids)]).ids
      == [l.id for l in layouts if layouts[0].product_ids[:1] <= l.product_ids])
check('search by stock move in the moveIds array (stock extension field)',
      set(Layout.search([('move_ids', 'in', layouts[3].move_ids[:1].ids)]).ids) == {l.id for l in layouts if layouts[3].move_ids[:1] <= l.move_ids})

# -- label report on the loaded wizard rows
for layout in layouts:
    try:
        xml_id, data = layout._prepare_report_data()
        check(f'label report {layout.print_format}: _prepare_report_data', env.ref(xml_id, raise_if_not_found=False) is not None
              and len(data['labels']) > 0 and data['label_template'], f"{xml_id}, {len(data['labels'])} labels")
    except Exception as e:  # noqa: BLE001
        check(f'label report {layout.print_format}: _prepare_report_data', False, f"{type(e).__name__}: {e}")
try:
    action = layouts[0].process()
    check('process() returns the report action', action.get('type') == 'ir.actions.report'
          and action.get('report_name') == env.ref(layouts[0]._get_report_xml_id()).report_name, action.get('report_name'))
except Exception as e:  # noqa: BLE001
    check('process() returns the report action', False, f"{type(e).__name__}: {e}")

# -- writes (scratch namespace only)
with cr.savepoint():
    dup = CV.create({'custom_product_template_attribute_value_id': values[0].custom_product_template_attribute_value_id.id,
                     'custom_value': 'third parentless value'})
    env.flush_all()
    check('third parentless value on the same attribute value is allowed (NULL != NULL)',
          cv_coll.find_one({'_id': dup.id, 'saleOrderLineId': {'$exists': False}}) is not None)
    dup.custom_value = 'edited'
    env.flush_all()
    check('write updates the document', cv_coll.find_one({'_id': dup.id})['customValue'] == 'edited')
    taken = next(v for v in values if v.sale_order_line_id)
    try:
        with cr.savepoint():
            CV.create({'custom_product_template_attribute_value_id': taken.custom_product_template_attribute_value_id.id,
                       'sale_order_line_id': taken.sale_order_line_id.id, 'custom_value': 'duplicate'})
            env.flush_all()
        check('duplicate (customPTAV, saleOrderLineId) raises', False)
    except Exception as e:  # noqa: BLE001
        check('duplicate (customPTAV, saleOrderLineId) raises', True, type(e).__name__)
    dup.unlink()
    env.flush_all()
    check('unlink removes the document', cv_coll.find_one({'_id': dup.id}) is None)
    moves = env['stock.move'].search([('state', '=', 'done')], order='id', limit=2)
    product = env['product.product'].search([('barcode', '!=', False)], order='id', limit=1)
    wiz = Layout.create({'print_format': 'zpl', 'product_ids': [(6, 0, product.ids)], 'move_ids': [(6, 0, moves.ids)],
                         'move_quantity': 'move', 'print_packaging': True})
    env.flush_all()
    doc = layout_coll.find_one({'_id': wiz.id})
    check('new wizard document carries productIds and stock moveIds',
          doc and [e['productProductId'] for e in doc['productIds']] == product.ids
          and sorted(e['stockMoveId'] for e in doc['moveIds']) == sorted(moves.ids) and doc.get('printPackaging') is True, doc and doc.get('moveIds'))
    cr.execute("SELECT count(*) FROM product_label_layout_stock_move_rel WHERE product_label_layout_id = %s", (wiz.id,))
    check('move_ids of the opted-in wizard are not materialised in PostgreSQL', cr.fetchone()[0] == 0)
    # transient vacuum: the loaded wizard rows are pinned to FIXED_INSTANT (days older than
    # transient_age_limit = 1 h); the row just created is fresh and must survive. The storage
    # path's age-based clean (search on write_date + unlink) is called directly: the
    # _transient_vacuum() gate reads _transient_max_hours, a lazy_classproperty whose cache key is
    # its lambda's __name__ and therefore shared with _transient_max_count (0), so after the
    # create() above the gate sees 0 and skips the clean on PostgreSQL and MongoDB alike
    # (pre-existing upstream behaviour, reported, not a storage-path defect)
    old_ids = layouts.ids
    env.invalidate_all()
    print(f"NOTE _transient_max_hours={Layout._transient_max_hours} _transient_max_count={Layout._transient_max_count}"
          f" with transient_age_limit={config.get('transient_age_limit')}: _transient_vacuum() would skip the clean")
    Layout._transient_clean_rows_older_than(3600)
    env.flush_all()
    remaining = sorted(d['_id'] for d in layout_coll.find({}, {'_id': 1}))
    check('age-based transient clean deletes the old wizard documents and keeps the fresh one',
          remaining == [wiz.id] and not Layout.browse(old_ids).exists(), remaining)
    cr.execute("SELECT count(*) FROM product_label_layout WHERE id = ANY(%s)", (old_ids,))
    check('vacuum also removed the shadow rows', cr.fetchone()[0] == 0)
    cr.execute("SELECT count(*) FROM product_label_layout_product_product_rel")
    check('vacuum cleared the PostgreSQL relation rows of the deleted wizards', cr.fetchone()[0] == 0)
env.invalidate_all()
cr.rollback()
layout_coll.drop()
cv_coll.drop()
after = {n: store.db[n].count_documents({}) for n in ('productAttributeCustomValue', 'productLabelLayout')}
check('loaded collections unchanged', after == loaded, after)
check('scratch unit collections dropped', layout_coll.name not in store.db.list_collection_names())
failed = [n for n, ok in checks if not ok]
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed" + (f"; FAILED: {failed}" if failed else ''))
if failed:
    raise SystemExit(1)
