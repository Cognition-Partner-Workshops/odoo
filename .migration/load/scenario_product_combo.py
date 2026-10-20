"""Tier-4 ORM scenario for unit product-combo (w3-b03): product.combo and product.combo.item are
served from MongoDB, including the §5 R rewrite of product.combo.currency_id (the compute_sql
expression becomes _search_currency_id, a company_id domain) and the cascade of combo_id.

Run from the run branch against a scratch clone of the seeded odoo_src clone whose rows were loaded
into the target by load_unit.py (PostgreSQL rows are the oracle, MongoDB the system under test);
every write is rolled back so the loaded documents are left unchanged::

    odoo-bin shell -d <scratch db> --db_port=5433 --no-http -c <conf> < .migration/load/scenario_product_combo.py

where ``<conf>`` sets ``mongodb_migration_db = <scratch db>``: the scratch clone reads the shared migrated
collections, so every write (including the account D5 tax writer, whose MongoDB side is the catalog document's
``taxesId`` - wave 2's ``productTemplate``, outside this batch's write targets) is asserted after ``flush`` inside a
savepoint and rolled back. The contract §6 post-COMMIT assertion of that writer belongs to a prefixed estate clone
(estate-probe.md recipe) or the product-catalog unit; it is not reachable from a clone that names the shared collections.
"""
from odoo.exceptions import UserError, ValidationError

checks = []


def check(name, ok, detail=''):
    checks.append((name, bool(ok)))
    print(f"{'PASS' if ok else 'FAIL'} {name}{': ' + str(detail) if detail else ''}")


cr = env.cr
Combo, Item, T = env['product.combo'], env['product.combo.item'], env['product.template']
store = env.registry.mongo_store
col = {m._name: store.db[store.collection_name(m)] for m in (Combo, Item)}
check('storage opt-in', Combo._storage == 'mongodb' and Item._storage == 'mongodb')
check('no shadow columns (no D2 / D6 reader on these tables)', not Combo._shadow_columns and not Item._shadow_columns)
before = {n: list(c.find(sort=[('_id', 1)])) for n, c in col.items()}

cr.execute("SELECT id, name->>'en_US', sequence, company_id FROM product_combo ORDER BY sequence, id")
pg = cr.fetchall()
combos = Combo.search([])
check('combo search in default order (sequence, id) = PostgreSQL rows',
      [(c.id, c.name, c.sequence, c.company_id.id or None) for c in combos] == pg, f"{len(combos)} combos")
cr.execute("SELECT id, combo_id, product_id, extra_price, company_id FROM product_combo_item ORDER BY id")
pg = cr.fetchall()
items = Item.search([], order='id')
check('combo item search = PostgreSQL rows',
      [(i.id, i.combo_id.id, i.product_id.id, i.extra_price, i.company_id.id or None) for i in items] == pg, f"{len(items)} items")
cr.execute("SELECT combo_id, COUNT(*) FROM product_combo_item GROUP BY combo_id ORDER BY combo_id")
pg = cr.fetchall()
check('combo_item_count (_read_group on the One2many) = PostgreSQL', [(c.id, c.combo_item_count) for c in combos.sorted('id')] == pg)

seeded = Combo.search([('company_id', '!=', False)])
check('seeded combo carries its company', len(seeded) == 1 and seeded.company_id.name == 'My Company (Chicago)', seeded.mapped('name'))
check('translated name: en_US and fr_FR from the jsonb document field',
      seeded.name == 'Chicago Desk Set' and seeded.with_context(lang='fr_FR').name == 'Ensemble bureau Chicago')
check('name ilike search hits the translation', Combo.with_context(lang='fr_FR').search([('name', 'ilike', 'bureau')]) == seeded
      and Combo.search([('name', 'ilike', 'chicago')]) == seeded)
check('items: stored related company_id = combo company',
      all(i.company_id == seeded.company_id for i in seeded.combo_item_ids) and not (items - seeded.combo_item_ids).company_id)
check('extra_price on the seeded item', seeded.combo_item_ids.filtered(lambda i: i.extra_price > 0).mapped('extra_price') == [7.5])
check('item lst_price / currency_id related through product.product (wave 2)',
      all(i.lst_price == i.product_id.lst_price and i.currency_id == i.combo_id.currency_id for i in items))
check('base_price = min(lst_price) over items (same currency)',
      all(abs(c.base_price - min(c.combo_item_ids.mapped('lst_price'))) < 1e-6 for c in combos))
check('items of the taxed products carry taxes (account D5 relation table)', all(i.product_id.taxes_id for i in seeded.combo_item_ids))

main_company = env['res.company']._get_main_company()
usd, eur = main_company.currency_id, env.ref('base.EUR')
check('currency_id compute: company currency, main company as fallback',
      all(c.currency_id == (c.company_id.sudo().currency_id or main_company.currency_id) for c in combos))
check('_search_currency_id (R rewrite) = main currency returns every combo', Combo.search([('currency_id', '=', usd.id)]) == combos)
check('_search_currency_id = EUR returns none', not Combo.search([('currency_id', '=', eur.id)]))
with cr.savepoint(flush=False):
    seeded.company_id.sudo().currency_id = eur   # res.company stays in PostgreSQL; rolled back below
    env.flush_all()
    env.invalidate_all()
    check('_search_currency_id follows the company currency (EUR -> seeded combo only)',
          Combo.search([('currency_id', '=', eur.id)]) == seeded and Combo.search([('currency_id', '!=', eur.id)]) == combos - seeded)
    check('currency_id compute follows the company currency', seeded.currency_id == eur)
env.invalidate_all()

# writes through the storage path, all rolled back. The scratch clone keeps the full PostgreSQL
# tables: relax their NOT NULL columns as _auto_init_mongodb's shadow shape does (DDL, rolled back)
with cr.savepoint(flush=False):
    for m in (Combo, Item):
        cr.execute("""SELECT column_name FROM information_schema.columns WHERE table_name = %s
                      AND is_nullable = 'NO' AND column_name != 'id'""", (m._table,))
        for (column,) in cr.fetchall():
            cr.execute(f'ALTER TABLE "{m._table}" ALTER COLUMN "{column}" DROP NOT NULL')
    products = seeded.combo_item_ids.product_id
    new = Combo.create({'name': 'Scenario Combo', 'sequence': 30, 'company_id': seeded.company_id.id,
                        'combo_item_ids': [(0, 0, {'product_id': products[0].id, 'extra_price': 1.25}),
                                           (0, 0, {'product_id': products[1].id})]})
    env.flush_all()
    doc = col['product.combo'].find_one({'_id': new.id})
    item_docs = list(col['product.combo.item'].find({'comboId': new.id}))
    check('combo create: document + 2 item documents with the stored related companyId',
          doc and doc['name'] == {'en_US': 'Scenario Combo'} and doc['companyId'] == seeded.company_id.id
          and len(item_docs) == 2 and all(d['companyId'] == seeded.company_id.id for d in item_docs), doc and doc.get('sequence'))
    check('combo_item_count on the new combo', new.combo_item_count == 2)
    priced = [d for d in item_docs if d['productId'] == products[0].id][0]
    check('digits Float extra_price written as a BSON number and matched by a numeric domain (not float_digits_bson_string)',
          type(priced['extraPrice']).__name__ == 'Decimal128' and new.combo_item_ids.filtered(lambda i: i.extra_price > 0)
          == Item.search([('combo_id', '=', new.id), ('extra_price', '>', 1)]), repr(priced['extraPrice']))
    new.write({'sequence': 5})
    env.flush_all()
    check('combo write: document updated and default order re-sorts', col['product.combo'].find_one({'_id': new.id})['sequence'] == 5
          and Combo.search([])[0] == new)
    try:
        with cr.savepoint(flush=False):
            new.write({'combo_item_ids': [(0, 0, {'product_id': products[0].id})]})
            env.flush_all()
        check('_check_combo_item_ids_no_duplicates raises', False)
    except ValidationError as e:
        check('_check_combo_item_ids_no_duplicates raises', True, type(e).__name__)
    try:
        with cr.savepoint(flush=False):
            other = env['res.company'].search([('id', '!=', seeded.company_id.id)], order='id', limit=1)
            products[0].product_tmpl_id.sudo().write({'company_id': other.id})   # product.template: wave 2 storage path
            env.flush_all()
            new._check_company_id()
            Item.create({'combo_id': new.id, 'product_id': products[0].id})
            env.flush_all()
        check('check_company on items (_check_company_id / check_company=True) raises', False)
    except (UserError, ValidationError) as e:
        check('check_company on items (_check_company_id / check_company=True) raises', True, type(e).__name__)
    env.invalidate_all()
    # account's write() clears taxes_id/supplier_taxes_id when a template becomes a combo product: the
    # taxesId array of the catalog document (wave 2, D5 relation snapshot) empties, the combo documents are untouched
    tmpl = products[0].product_tmpl_id
    tcol = store.db[store.collection_name(T)]
    taxes_before = len(tcol.find_one({'_id': tmpl.id}).get('taxesId') or [])
    snapshot = {n: list(c.find(sort=[('_id', 1)])) for n, c in col.items()}
    try:
        with cr.savepoint(flush=False):
            tmpl.sudo().write({'type': 'combo', 'combo_ids': [(6, 0, (combos - seeded)[0].ids)]})   # a company-less combo: the template has no company
            env.flush_all()
            check('account D5 writer clears taxesId when type becomes combo',
                  taxes_before > 0 and not tmpl.taxes_id and not (tcol.find_one({'_id': tmpl.id}).get('taxesId') or []), f"{taxes_before} -> 0")
            check('account D5 writer leaves the combo documents untouched',
                  snapshot == {n: list(c.find(sort=[('_id', 1)])) for n, c in col.items()})
            raise UserError('rollback')
    except UserError as e:
        if str(e) != 'rollback':
            check('account D5 writer: template write type=combo', False, e)
    env.invalidate_all()
    new_items = new.combo_item_ids.ids
    new.unlink()
    env.flush_all()
    check('unlink combo cascades to its items (ondelete=cascade through the storage path)',
          not col['product.combo'].find_one({'_id': new.id}) and col['product.combo.item'].count_documents({'_id': {'$in': new_items}}) == 0
          and not Item.search([('id', 'in', new_items)]))
env.invalidate_all()
cr.rollback()
after = {n: list(c.find(sort=[('_id', 1)])) for n, c in col.items()}
check('loaded collections unchanged after rollback', before == after, {n: len(v) for n, v in after.items()})
failed = [n for n, ok in checks if not ok]
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed" + (f"; FAILED: {failed}" if failed else ''))
if failed:
    raise SystemExit(1)
