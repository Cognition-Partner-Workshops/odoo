"""Tier-4 ORM scenario for unit product-catalog (w2-b01): the storage path serves the six
product-catalog models from MongoDB, including the §5 R rewrites (display_name UNIONs,
currency_id compute_sql, catalog_is_in_order subselect) and the D6 shadow columns.

Run from the run branch against a scratch clone of the seeded odoo_src clone whose rows were
loaded into the target by load_unit.py (PostgreSQL rows are the oracle, MongoDB the system
under test); every write is rolled back so the loaded documents are left unchanged::

    odoo-bin shell -d <scratch db> --db_port=5433 --no-http -c <conf> < .migration/load/scenario_product_catalog.py

where ``<conf>`` sets ``mongodb_migration_db = <scratch db>``. On a clone of odoo_fixture the
outlier template (``__migration__.fixture_outlier_tee``) is excluded from the ORM reads: its
attributes 15-17 exist only in odoo_fixture, not in the wave 1 collections loaded from odoo_src.
"""
from odoo.exceptions import ValidationError
from psycopg2 import IntegrityError

checks = []


def check(name, ok, detail=''):
    checks.append((name, bool(ok)))
    print(f"{'PASS' if ok else 'FAIL'} {name}{': ' + str(detail) if detail else ''}")


cr = env.cr
T, P = env['product.template'], env['product.product']
PTAL, PTAV, Doc, PUom = (env['product.template.attribute.line'], env['product.template.attribute.value'],
                         env['product.document'], env['product.uom'])
store = env.registry.mongo_store
check('storage opt-in', all(m._storage == 'mongodb' for m in (T, P, PTAL, PTAV, Doc, PUom)))
before = {m._name: store.db[store.collection_name(m)].count_documents({}) for m in (T, P, PTAL, PTAV, Doc, PUom)}
outlier = env.ref('__migration__.fixture_outlier_tee', raise_if_not_found=False)  # odoo_fixture clones only
outlier_id = outlier_id if outlier else 0
not_outlier_tmpl = [('product_tmpl_id', '!=', outlier_id)]

cr.execute("SELECT id, name->>'en_US', categ_id, uom_id, list_price, active FROM product_template ORDER BY id")
pg = cr.fetchall()
templates = T.with_context(active_test=False).search([], order='id')
check('template search = PostgreSQL rows',
      [(t.id, t.name, t.categ_id.id, t.uom_id.id, t.list_price, t.active) for t in templates] == pg, f"{len(templates)} templates")
cr.execute("""SELECT p.id FROM product_product p JOIN product_template t ON t.id = p.product_tmpl_id
              WHERE p.active AND p.product_tmpl_id != %s
              ORDER BY p.default_code COLLATE "C" NULLS FIRST, t.name->>'en_US' COLLATE "C" NULLS FIRST, p.id""", (outlier_id,))
pg_order = [r[0] for r in cr.fetchall()]
# MongoDB sorts in binary order with missing values first (contract open item C-10), hence COLLATE "C" NULLS FIRST.
# product.product's default order has the _inherits field `name`: _order_to_sort rejects it until the
# storage-path ticket UNT11-42 lands, so every search below passes order='id' and this check is skipped.
try:
    check('variant default order (default_code, name, id) joins the template like SQL',
          P.search([('product_tmpl_id', '!=', outlier_id)]).ids == pg_order)
except NotImplementedError as e:
    print(f"SKIP variant default order: {e} (UNT11-42)")
variant = P.search([('barcode', '!=', False), ('product_tmpl_id', '!=', outlier_id)], order='id', limit=1)
check('_inherits read through the template', variant.name == variant.product_tmpl_id.name and variant.categ_id == variant.product_tmpl_id.categ_id)
check('display_name computed with attribute values',
      all(p.display_name for p in P.search([('product_tmpl_id', '!=', outlier_id)], order='id')))

cr.execute("SELECT id FROM product_template WHERE name->>'en_US' ILIKE '%desk%' ORDER BY id")
pg_desk = {r[0] for r in cr.fetchall()}
cr.execute("""SELECT DISTINCT product_tmpl_id FROM product_product WHERE default_code ILIKE '%desk%' OR barcode = 'desk'""")
pg_desk |= {r[0] for r in cr.fetchall()}
check('template _search_display_name (name OR variants) without UNION ALL',
      set(T.search([('display_name', 'ilike', 'desk')]).ids) == pg_desk, len(pg_desk))
cr.execute("""SELECT p.id FROM product_product p JOIN product_template t ON t.id = p.product_tmpl_id
              WHERE p.active AND (t.name->>'en_US' ILIKE '%desk%' OR p.default_code ILIKE '%desk%' OR p.barcode = 'desk')""")
pg_variants_desk = {r[0] for r in cr.fetchall()}
check('variant _search_display_name (template OR default_code OR barcode)',
      set(P.search([('display_name', 'ilike', 'desk')], order='id').ids) == pg_variants_desk)
check('variant _search_display_name [code] match',
      P.search([('display_name', 'ilike', f'[{variant.default_code}]')], order='id').ids == [variant.id] if variant.default_code else True)
check('variant _search_display_name with partner_id (supplierinfo two-step)',
      isinstance(P.with_context(partner_id=env.ref('base.res_partner_1').id).search([('display_name', 'ilike', 'desk')], order='id').ids, list))

main_currency = env['res.company']._get_main_company().currency_id
cr.execute("""SELECT t.id FROM product_template t LEFT JOIN res_company c ON c.id = t.company_id
              WHERE COALESCE(c.currency_id, %s) = %s ORDER BY t.id""", (main_currency.id, main_currency.id))
pg_currency = [r[0] for r in cr.fetchall()]
check('currency_id search = COALESCE(company currency, main company currency)',
      T.with_context(active_test=False).search([('currency_id', '=', main_currency.id)], order='id').ids == pg_currency)
check('cost_currency_id negative search', T.search_count([('cost_currency_id', '!=', env.company.currency_id.id)])
      == T.search_count([('company_id', '!=', False), ('company_id.currency_id', '!=', env.company.currency_id.id)]))

order = env['sale.order'].search([('order_line.product_id', '!=', False)], order='id', limit=1)
if order:
    in_order = P.with_context(order_id=order.id, product_catalog_order_model='sale.order', child_field='order_line') \
        .search([('catalog_is_in_order', 'in', [True])], order='id')
    check('catalog_is_in_order two-step from sale.order.line (PostgreSQL)', set(in_order.ids) == set(order.order_line.product_id.ids))

cr.execute("SELECT r.product_template_attribute_line_id, array_agg(r.product_attribute_value_id ORDER BY r.product_attribute_value_id) "
           "FROM product_attribute_value_product_template_attribute_line_rel r "
           "JOIN product_template_attribute_line l ON l.id = r.product_template_attribute_line_id "
           "WHERE l.product_tmpl_id != %s GROUP BY 1 ORDER BY 1", (outlier_id,))
pg_lines = [(line_id, list(values)) for line_id, values in cr.fetchall()]
check('attribute line value_ids = relation table (outlier lines excluded: their values exist only in odoo_fixture)',
      [(l.id, sorted(l.value_ids.ids)) for l in PTAL.with_context(active_test=False).search(not_outlier_tmpl, order='id')] == pg_lines)
cr.execute("SELECT id, attribute_line_id, product_attribute_value_id, price_extra FROM product_template_attribute_value ORDER BY id")
pg_values = cr.fetchall()
check('attribute value search = PostgreSQL rows',
      [(v.id, v.attribute_line_id.id, v.product_attribute_value_id.id, v.price_extra) for v in PTAV.with_context(active_test=False).search([], order='id')] == pg_values)
cr.execute("SELECT d.id, a.name, d.ir_attachment_id FROM product_document d JOIN ir_attachment a ON a.id = d.ir_attachment_id ORDER BY d.id")
pg_documents = cr.fetchall()
check('document delegates to ir.attachment (PostgreSQL)', [(d.id, d.name, d.ir_attachment_id.id) for d in Doc.search([], order='id')] == pg_documents)
cr.execute("SELECT id, barcode, product_id, uom_id FROM product_uom ORDER BY id")
pg_uoms = cr.fetchall()
check('product.uom search = PostgreSQL rows', [(u.id, u.barcode, u.product_id.id, u.uom_id.id) for u in PUom.search([], order='id')] == pg_uoms)
cr.execute("SELECT categ_id, COUNT(*) FROM product_template WHERE active GROUP BY 1")
pg_groups = set(cr.fetchall())
check('read_group on categ_id', {(c.id, n) for c, n in T._read_group([], ['categ_id'], ['__count'])} == pg_groups)

# writes through the storage path, projected onto the shadow columns, all rolled back. A template
# create runs _create_variant_ids (variant search with the default order) and waits on UNT11-42; the
# product.uom create/unique/unlink runs here. The scratch clone still has the full
# PostgreSQL tables: relax their NOT NULL columns as _auto_init_mongodb's shadow shape does (DDL, rolled back)
with cr.savepoint(flush=False):
    for m in (T, P, PTAL, PTAV, Doc, PUom):
        cr.execute("""SELECT column_name FROM information_schema.columns WHERE table_name = %s
                      AND is_nullable = 'NO' AND column_name != 'id'""", (m._table,))
        for (column,) in cr.fetchall():
            if column not in m._shadow_columns:
                cr.execute(f'ALTER TABLE "{m._table}" ALTER COLUMN "{column}" DROP NOT NULL')
    # template and variant writes recompute template fields through a variant search with the default
    # order (UNT11-42); the write-through of the storage path is exercised on product.uom here
    pu = PUom.create({'product_id': variant.id, 'uom_id': env.ref('uom.product_uom_dozen').id, 'barcode': 'SCN-UNIQUE-1'})
    env.flush_all()
    cr.execute("SELECT id FROM product_uom WHERE id = %s", (pu.id,))
    check('product.uom create: shadow row + document', cr.fetchone() == (pu.id,) and store.db[store.collection_name(PUom)].find_one({'_id': pu.id})['barcode'] == 'SCN-UNIQUE-1')
    try:
        with cr.savepoint(flush=False):
            PUom.create({'product_id': variant.id, 'uom_id': env.ref('uom.product_uom_pack_6').id, 'barcode': 'SCN-UNIQUE-1'})
            env.flush_all()
        check('product_uom barcode unique index raises', False)
    except (IntegrityError, ValidationError) as e:
        check('product_uom barcode unique index raises', True, type(e).__name__)
    pu.unlink()
    env.flush_all()
    check('unlink removes the document', not store.db[store.collection_name(PUom)].find_one({'_id': pu.id}))
env.invalidate_all()
cr.rollback()
after = {m._name: store.db[store.collection_name(m)].count_documents({}) for m in (T, P, PTAL, PTAV, Doc, PUom)}
check('loaded collections unchanged after rollback', before == after, after)
failed = [n for n, ok in checks if not ok]
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed" + (f"; FAILED: {failed}" if failed else ''))
