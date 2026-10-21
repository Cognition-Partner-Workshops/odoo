"""Seed the scenario rows of batches w1-b01 (unit stock-reference), w1-b02 (unit product-taxonomy),
w1-b04 (unit account-settings) and w1-b06 (unit account-chart) on the worker's own PostgreSQL clone.

Run it through the pre-opt-in source tree (the SOURCE_COMMIT worktree build_source.sh keeps at
../odoo-unt12-src), so every write lands on PostgreSQL and the clone stays a plain source:

    /home/ubuntu/.venvs/odoo/bin/python ../odoo-unt12-src/odoo-bin shell -d <clone> --db_port=5433 \\
        --no-http < .migration/load/seed_scenario_rows.py

1. Deactivates the six cron writers of NOTES.md s2.3 §1 (ids 19-23 and 1) on the clone, as every
   load or recon requires.
2. stock_scrap_reason_tag has 0 fixture rows (units.json recon_unverified): seeds three tags with
   create_date/write_date pinned to FIXED_INSTANT (the build_source.sh instant), so a verifier
   reseeding its own clone gets identical rows and recon grades the collection.
3. w1-b04: account_cash_rounding (+ its three relation tables), account_journal_group, account_lock_exception,
   account_report_line, account_report_expression, account_report_external_value and
   account_report_section_rel have 0 fixture rows: seeds two roundings, two ledger groups, one lock
   exception, one sectioned report and two lines with three expressions and one external value on
   report 1, all pinned to FIXED_INSTANT.
4. w1-b02: product_tag and product_base_unit have 0 fixture rows, and so do the three junction tables
   (product_tag_product_template_rel, product_tag_product_product_rel,
   product_category_stock_picking_type_rel): seeds three tags linked to the two lowest-id templates /
   three lowest-id variants, two base units, and two picking types with wave categories, pinned to
   FIXED_INSTANT.
Idempotent: an already seeded clone only gets the cron step again.
"""
FIXED_INSTANT = '2026-10-20 00:00:00'
CRON_IDS = [1, 19, 20, 21, 22, 23]
TAGS = [
    {'name': 'Damaged in transit', 'sequence': 10, 'color': 1},
    {'name': 'Expired', 'sequence': 20, 'color': 5},
    {'name': 'Quality check failed', 'sequence': 5},  # default color
]

crons = env['ir.cron'].browse(CRON_IDS).exists()
assert set(crons.ids) == set(CRON_IDS), f"cron ids on this clone: {crons.ids}"
crons.write({'active': False})
print(f"crons deactivated: {sorted(crons.ids)}")

Tag = env['stock.scrap.reason.tag']
if Tag.search_count([]):
    print(f"stock.scrap.reason.tag already seeded: {Tag.search_count([])} rows")
else:
    tags = Tag.create(TAGS)
    tags.flush_recordset()
    env.cr.execute(
        "UPDATE stock_scrap_reason_tag SET create_date = %s, write_date = %s WHERE id IN %s",
        (FIXED_INSTANT, FIXED_INSTANT, tuple(tags.ids)),
    )
    print(f"stock.scrap.reason.tag seeded: ids {tags.ids}")
env.cr.commit()
env.cr.execute("SELECT id, name->>'en_US', sequence, color, create_date FROM stock_scrap_reason_tag ORDER BY id")
for row in env.cr.fetchall():
    print(row)

# ---- w1-b04 account-settings -------------------------------------------------------------------
Rounding = env['account.cash.rounding']
if Rounding.search_count([]):
    print(f"w1-b04 account settings already seeded: {Rounding.search_count([])} cash roundings")
else:
    income = env['account.account'].search([('account_type', '=', 'income_other')], limit=1)
    expense = env['account.account'].search([('account_type', '=', 'expense')], limit=1)
    roundings = Rounding.create([
        {'name': 'Round to 0.05', 'rounding': 0.05, 'strategy': 'add_invoice_line', 'rounding_method': 'HALF-UP',
         'profit_account_id': income.id, 'loss_account_id': expense.id,
         'currency_ids': [(6, 0, env['res.currency'].search([]).ids)],
         'partner_category_ids': [(6, 0, [1, 2])], 'payment_method_line_ids': [(6, 0, [1, 2])]},
        {'name': 'Round to 1.00', 'rounding': 1.0, 'strategy': 'biggest_tax', 'rounding_method': 'UP', 'sequence': 20,
         'partner_category_ids': [(6, 0, [3])], 'payment_method_line_ids': [(6, 0, [3])]},
    ])
    groups = env['account.journal.group'].create([
        {'name': 'Statutory ledger', 'sequence': 1},
        {'name': 'IFRS ledger', 'sequence': 2},
    ])
    exceptions = env['account.lock_exception'].create([{
        'company_id': 1, 'user_id': 2, 'reason': 'Late supplier bill', 'lock_date_field': 'fiscalyear_lock_date',
        'lock_date': '2026-01-31', 'end_datetime': '2026-10-27 00:00:00',
    }])
    Line = env['account.report.line']
    parent = Line.create({
        'name': 'W1B04 Sales', 'report_id': 1, 'code': 'W1B04_SALES', 'sequence': 1000,
        'expression_ids': [
            (0, 0, {'label': 'balance', 'engine': 'domain', 'formula': "[('account_id.account_type', '=', 'income')]",
                    'subformula': '-sum', 'date_scope': 'strict_range'}),
            (0, 0, {'label': 'adjustment', 'engine': 'aggregation', 'formula': 'W1B04_ADJ.balance'}),
        ],
    })
    child = Line.create({
        'name': 'W1B04 Sales adjustment', 'report_id': 1, 'parent_id': parent.id, 'code': 'W1B04_ADJ', 'sequence': 1010,
        'expression_ids': [(0, 0, {'label': 'balance', 'engine': 'external', 'formula': 'sum', 'date_scope': 'strict_range'})],
    })
    external = env['account.report.external.value'].create([{
        'name': 'W1B04 opening adjustment', 'target_report_expression_id': child.expression_ids.id,
        'company_id': 1, 'date': '2026-01-01', 'value': 123.45,
    }])
    sectioned = env['account.report'].create({'name': 'W1B04 Sectioned report', 'use_sections': True,
                                              'section_report_ids': [(6, 0, [2, 3])]})
    env.flush_all()
    for table, ids in [('account_cash_rounding', roundings.ids), ('account_journal_group', groups.ids),
                       ('account_lock_exception', exceptions.ids), ('account_report', sectioned.ids),
                       ('account_report_line', (parent | child).ids),
                       ('account_report_expression', (parent | child).expression_ids.ids),
                       ('account_report_external_value', external.ids)]:
        env.cr.execute(
            f"UPDATE {table} SET create_date = %s, write_date = %s WHERE id IN %s",
            (FIXED_INSTANT, FIXED_INSTANT, tuple(ids)),
        )
        print(f"{table} seeded: ids {ids}")
env.cr.commit()
for table in ('account_cash_rounding', 'account_journal_group', 'account_lock_exception', 'account_report_line',
              'account_report_expression', 'account_report_external_value', 'account_report_section_rel',
              'account_cash_rounding_res_currency_rel', 'account_cash_rounding_res_partner_category_rel',
              'account_cash_rounding_account_payment_method_line_rel'):
    env.cr.execute(f"SELECT count(*) FROM {table}")
    print(table, env.cr.fetchone()[0])

# --- w1-b06 (unit account-chart): the seven embedded arrays with 0 fixture rows (units.json recon_unverified) ---
# One parent row each gets elements through the ORM, on the clone only: accountAccount.taxDefaultRel,
# accountTax.filiationRel (a group tax), accountAccountTag.{accountTaxRepartitionLineRel, productTemplateRel,
# accountMoveLineRel} (two new tags: 'taxes' and 'products' applicability), accountFiscalPosition.{account,
# resCountryStateRel}. New rows and touched parents are pinned to FIXED_INSTANT so a reseed is identical.
env.cr.execute("SELECT count(*) FROM account_account_tax_default_rel")
if env.cr.fetchone()[0]:
    print("account-chart already seeded")
else:
    company = env.company
    Account, Tax, Tag = env['account.account'], env['account.tax'], env['account.account.tag']
    accounts = Account.search([('account_type', '=', 'income'), ('company_ids', 'in', company.id)], order='id', limit=2)
    taxes = Tax.search([('type_tax_use', '=', 'sale'), ('amount_type', '=', 'percent'), ('company_id', '=', company.id)], order='id', limit=2)
    position = env['account.fiscal.position'].search([('company_id', '=', company.id)], order='id', limit=1)
    states = env['res.country.state'].search([('country_id', '=', company.country_id.id)], order='id', limit=2)
    product = env['product.template'].search([], order='id', limit=1)
    line = env['account.move.line'].search([('move_id.state', '=', 'draft'), ('display_type', '=', 'product')], order='id', limit=1)
    assert len(accounts) == 2 and len(taxes) == 2 and position and len(states) == 2 and product and line, \
        f"seed inputs on this clone: {accounts.ids} {taxes.ids} {position.ids} {states.ids} {product.ids} {line.ids}"
    grid, product_tag = Tag.create([
        {'name': 'Scenario tax grid', 'applicability': 'taxes', 'country_id': company.country_id.id},
        {'name': 'Scenario product tag', 'applicability': 'products'},
    ])
    accounts[0].write({'tax_ids': [(4, taxes[0].id)]})
    group = Tax.create({'name': 'Scenario group tax', 'amount_type': 'group', 'type_tax_use': 'sale',
                        'company_id': company.id, 'children_tax_ids': [(6, 0, taxes.ids)]})
    repartition = taxes[0].invoice_repartition_line_ids.filtered(lambda r: r.repartition_type == 'tax')[:1]
    repartition.write({'tag_ids': [(4, grid.id)]})
    product.write({'account_tag_ids': [(4, product_tag.id)]})
    line.write({'tax_tag_ids': [(4, grid.id)]})
    mapping = env['account.fiscal.position.account'].create({
        'position_id': position.id, 'account_src_id': accounts[0].id, 'account_dest_id': accounts[1].id})
    position.write({'state_ids': [(6, 0, states.ids)]})
    env.flush_all()
    created = {'account_account_tag': (grid + product_tag).ids, 'account_tax': group.ids,
               'account_tax_repartition_line': group.repartition_line_ids.ids, 'account_fiscal_position_account': mapping.ids}
    touched = {'account_account': accounts[0].ids, 'account_tax_repartition_line': repartition.ids, 'product_template': product.ids,
               'account_move_line': line.ids, 'account_move': line.move_id.ids, 'account_fiscal_position': position.ids}
    for table, ids in created.items():
        env.cr.execute(f"UPDATE {table} SET create_date = %s, write_date = %s WHERE id IN %s", (FIXED_INSTANT, FIXED_INSTANT, tuple(ids)))
    for table, ids in touched.items():
        env.cr.execute(f"UPDATE {table} SET write_date = %s WHERE id IN %s", (FIXED_INSTANT, tuple(ids)))
    print(f"account-chart seeded: created {created}, touched {touched}")
env.cr.commit()
for table in ('account_account_tax_default_rel', 'account_tax_filiation_rel', 'account_account_tag_account_tax_repartition_line_rel',
              'account_account_tag_product_template_rel', 'account_account_tag_account_move_line_rel',
              'account_fiscal_position_account', 'account_fiscal_position_res_country_state_rel'):
    env.cr.execute(f"SELECT count(*) FROM {table}")
    print(table, env.cr.fetchone()[0])

# --- w1-b02 (unit product-taxonomy): the two roots and three junction arrays with 0 fixture rows (units.json recon_unverified) ---
PRODUCT_TAGS = [
    {'name': 'Fragile', 'sequence': 10, 'color': 1, 'visible_to_customers': True},
    {'name': 'Seasonal', 'sequence': 20, 'color': 4, 'visible_to_customers': False},
    {'name': 'Clearance', 'sequence': 5},  # default color, default visibility
]
BASE_UNITS = [{'name': 'Litre'}, {'name': 'Kilogram'}]
WAVE_CATEGORIES = {1: [1, 4], 3: [5]}  # picking type id -> product category ids (fixture ids)


def pin(table, ids):
    env.cr.execute(f"UPDATE {table} SET create_date = %s, write_date = %s WHERE id IN %s",
                   (FIXED_INSTANT, FIXED_INSTANT, tuple(ids)))


ProductTag = env['product.tag']
if ProductTag.search_count([]):
    print(f"product.tag already seeded: {ProductTag.search_count([])} rows")
else:
    templates = env['product.template'].search([], order='id', limit=2)
    variants = env['product.product'].search([], order='id', limit=3)
    links = [
        {'product_template_ids': [(6, 0, templates.ids)], 'product_product_ids': [(6, 0, variants.ids)]},
        {'product_template_ids': [(6, 0, templates[:1].ids)]},
        {},  # no links: a tag without arrays
    ]
    product_tags = ProductTag.create([dict(tag, **link) for tag, link in zip(PRODUCT_TAGS, links)])
    product_tags.flush_recordset()
    pin('product_tag', product_tags.ids)
    print(f"product.tag seeded: ids {product_tags.ids}, templates {templates.ids}, variants {variants.ids}")

BaseUnit = env['product.base.unit']
if BaseUnit.search_count([]):
    print(f"product.base.unit already seeded: {BaseUnit.search_count([])} rows")
else:
    units = BaseUnit.create(BASE_UNITS)
    units.flush_recordset()
    pin('product_base_unit', units.ids)
    print(f"product.base.unit seeded: ids {units.ids}")

env.cr.execute("SELECT count(*) FROM product_category_stock_picking_type_rel")
if env.cr.fetchone()[0]:
    print("stock.picking.type.wave_category_ids already seeded")
else:
    for picking_type_id, categ_ids in WAVE_CATEGORIES.items():
        env['stock.picking.type'].browse(picking_type_id).write({'wave_category_ids': [(6, 0, categ_ids)]})
    env.flush_all()
    print(f"stock.picking.type.wave_category_ids seeded: {WAVE_CATEGORIES}")
env.cr.commit()
for table, cols in (('product_tag', "name->>'en_US', sequence, color, visible_to_customers"),
                    ('product_base_unit', "name->>'en_US'"),
                    ('product_tag_product_template_rel', 'product_template_id'),
                    ('product_tag_product_product_rel', 'product_product_id'),
                    ('product_category_stock_picking_type_rel', 'stock_picking_type_id')):
    env.cr.execute(f"SELECT * FROM (SELECT {cols} FROM {table}) t ORDER BY 1")
    print(table, env.cr.fetchall())

# --- w2-b02 (unit product-catalog): the two roots and seven junction/child arrays with 0 fixture rows (units.json recon_unverified) ---
# productPricelist / productPricelistItem, productTemplate.uomUomRel, productProduct.{customerProductReference, uomUomRel,
# productUom}, productTemplateAttributeValue.{purchaseOrderLineRel, saleOrderLineRel, templateAttributeValueStockMoveRel}.
# Anchored on the fixture's 'Customizable Desk' (template 9: two attribute lines, five variants) and Acme Corporation.
CATALOG_TEMPLATE_ID = 9
CATALOG_PARTNER_ID = 10
SEEDED_BARCODE = 'SEED-DOZEN-0096'

Pricelist = env['product.pricelist']
if Pricelist.search_count([]):
    print(f"product.pricelist already seeded: {Pricelist.search_count([])} rows")
else:
    template = env['product.template'].browse(CATALOG_TEMPLATE_ID)
    variant = template.product_variant_ids.sorted('id')[0]
    partner = env['res.partner'].browse(CATALOG_PARTNER_ID)
    dozen = env.ref('uom.product_uom_dozen')
    pack6 = env.ref('uom.product_uom_pack_6')
    ptavs = template.attribute_line_ids.sorted('id').mapped(lambda line: line.product_template_value_ids.sorted('id')[0])
    assert template and variant and partner and len(ptavs) == 2, f"seed inputs on this clone: {template.ids} {variant.ids} {partner.ids} {ptavs.ids}"
    # the live w2-b02 documents were loaded from a clone whose sequences had moved past a fresh `createdb -T odoo_src`
    # (earlier seed attempts), so pin them: a fresh clone then reproduces the live ids on a verifier's reseed
    LIVE_SEQUENCES = {'product_pricelist_id_seq': 6, 'product_pricelist_item_id_seq': 2, 'product_uom_id_seq': 1,
                      'customer_product_reference_id_seq': 1, 'sale_order_id_seq': 25, 'sale_order_line_id_seq': 51,
                      'purchase_order_id_seq': 17, 'purchase_order_line_id_seq': 32}
    for seq, last in LIVE_SEQUENCES.items():
        env.cr.execute(f"SELECT last_value, is_called FROM {seq}")
        value, is_called = env.cr.fetchone()
        if (value if is_called else value - 1) <= last:
            env.cr.execute("SELECT setval(%s, %s, true)", (seq, last))
        else:
            print(f"{seq} is already past {last} ({value}): ids on this clone will differ from the live load")
    pricelists = Pricelist.create([
        {'name': 'Seeded wholesale', 'sequence': 5, 'item_ids': [
            (0, 0, {'applied_on': '1_product', 'product_tmpl_id': template.id, 'compute_price': 'fixed', 'fixed_price': 950.0, 'min_quantity': 2}),
            (0, 0, {'applied_on': '3_global', 'compute_price': 'discount', 'price_discount': 10.0}),
        ]},
        {'name': 'Seeded retail (inactive)', 'active': False},  # a root without an array
    ])
    template.write({'uom_ids': [(6, 0, (dozen | pack6).ids)]})
    variant.write({'extra_uom_ids': [(6, 0, dozen.ids)]})
    product_uom = env['product.uom'].create({'product_id': variant.id, 'uom_id': dozen.id, 'barcode': SEEDED_BARCODE})
    reference = env['customer.product.reference'].create({
        'product_id': variant.id, 'partner_id': partner.id, 'customer_product_reference': 'ACME-DESK-0096'})
    sale = env['sale.order'].create({'partner_id': partner.id, 'order_line': [
        (0, 0, {'product_id': variant.id, 'product_no_variant_attribute_value_ids': [(6, 0, ptavs[0].ids)]})]})
    sale.order_line.write({'product_no_variant_attribute_value_ids': [(6, 0, ptavs[0].ids)]})
    purchase = env['purchase.order'].create({'partner_id': partner.id, 'order_line': [
        (0, 0, {'product_id': variant.id, 'product_no_variant_attribute_value_ids': [(6, 0, ptavs.ids)]})]})
    warehouse = env.ref('stock.warehouse0')
    move = env['stock.move'].create({
        'product_id': variant.id, 'product_uom_qty': 1.0,
        'location_id': warehouse.lot_stock_id.id, 'location_dest_id': env.ref('stock.stock_location_customers').id,
        'never_product_template_attribute_value_ids': [(6, 0, ptavs[1].ids)]})
    env.flush_all()
    pin('product_pricelist', pricelists.ids)
    pin('product_pricelist_item', pricelists.item_ids.ids)
    pin('product_uom', product_uom.ids)
    pin('customer_product_reference', reference.ids)
    pin('product_template', template.ids)
    pin('product_product', variant.ids)
    print(f"product.pricelist seeded: ids {pricelists.ids}, items {pricelists.item_ids.ids}; template {template.id} uom_ids {(dozen | pack6).ids}; "
          f"variant {variant.id} extra_uom_ids {dozen.ids}, product.uom {product_uom.id}, customer.product.reference {reference.id}; "
          f"sale {sale.id} line {sale.order_line.ids} -> ptav {ptavs[0].id}; purchase {purchase.id} line {purchase.order_line.ids} -> ptavs {ptavs.ids}; "
          f"stock.move {move.id} -> ptav {ptavs[1].id}")
# every row of the unit's tables carries the fixture instant again: the shared sections above and the orders
# created here bump write_date on templates/variants they touch, and recon grades those columns on a verifier's reseed
for table in ('product_template', 'product_product', 'product_template_attribute_line', 'product_template_attribute_value',
              'product_combo', 'product_combo_item', 'product_supplierinfo', 'product_pricelist', 'product_pricelist_item',
              'product_uom', 'customer_product_reference'):
    env.cr.execute(f"UPDATE {table} SET create_date = %s, write_date = %s WHERE create_date <> %s OR write_date <> %s",
                   (FIXED_INSTANT, FIXED_INSTANT, FIXED_INSTANT, FIXED_INSTANT))
    if env.cr.rowcount:
        print(f"{table}: {env.cr.rowcount} rows re-pinned to {FIXED_INSTANT}")
env.cr.commit()
for table, cols in (('product_pricelist', "name->>'en_US', active"),
                    ('product_pricelist_item', 'pricelist_id, applied_on, compute_price'),
                    ('product_template_uom_uom_rel', 'product_template_id, uom_uom_id'),
                    ('product_product_uom_uom_rel', 'product_product_id, uom_uom_id'),
                    ('product_uom', 'product_id, uom_id, barcode'),
                    ('customer_product_reference', 'product_id, partner_id, customer_product_reference'),
                    ('product_template_attribute_value_sale_order_line_rel', 'product_template_attribute_value_id, sale_order_line_id'),
                    ('product_template_attribute_value_purchase_order_line_rel', 'product_template_attribute_value_id, purchase_order_line_id'),
                    ('template_attribute_value_stock_move_rel', 'template_attribute_value_id, move_id')):
    env.cr.execute(f"SELECT * FROM (SELECT {cols} FROM {table}) t ORDER BY 1, 2")
    print(table, env.cr.fetchall())

# --- w3-b01 (unit stock-config): the two roots and six arrays with 0 fixture rows (units.json recon_unverified) ---
# stockPutawayRule, stockStorageCategoryCapacity, stockWarehouse.stockWhResupplyTable (an archived third warehouse resupplied from WH),
# stockLocation.stockPickingTypeRel (wave locations of WH receipts), stockPickingType.pickingTypeFavoriteUserRel (admin),
# stockRoute.{categ, product, move} (the MTO route on the Office Chair's category, its template and one stock.move).
# Anchored on fixture warehouse WH, storage categories 1-2, package types Pallet/Box and product 5 (Office Chair).
Warehouse = env['stock.warehouse']
if Warehouse.with_context(active_test=False).search_count([('code', '=', 'SEED')]):
    print(f"stock-config already seeded: warehouse {Warehouse.with_context(active_test=False).search([('code', '=', 'SEED')]).ids}")
else:
    # forward-only pins to the ids the live w3-b01 load used, so a fresh `createdb -T odoo_src` clone reproduces them
    LIVE_SEQUENCES = {'stock_warehouse_id_seq': 2, 'stock_location_id_seq': 32, 'stock_picking_type_id_seq': 16,
                      'stock_route_id_seq': 6, 'stock_rule_id_seq': 8, 'stock_putaway_rule_id_seq': 0,
                      'stock_storage_category_capacity_id_seq': 0, 'ir_sequence_id_seq': 32, 'stock_move_id_seq': 136}
    for seq, last in LIVE_SEQUENCES.items():
        env.cr.execute(f"SELECT last_value, is_called FROM {seq}")
        value, is_called = env.cr.fetchone()
        if (value if is_called else value - 1) <= last:
            env.cr.execute("SELECT setval(%s, %s, %s)", (seq, max(last, 1), last > 0))
        else:
            print(f"{seq} is already past {last} ({value}): ids on this clone will differ from the live load")
    wh = env.ref('stock.warehouse0')
    chair = env['product.product'].browse(5)
    furniture = chair.categ_id
    mto = env.ref('stock.route_warehouse0_mto')
    shelf1 = env['stock.location'].search([('complete_name', '=', 'WH/Stock/Shelf 1')])
    shelf2 = env['stock.location'].search([('complete_name', '=', 'WH/Stock/Shelf 2')])
    small, big = env['stock.storage.category'].browse([1, 2])
    pallet, box = env['stock.package.type'].browse([1, 2])
    assert chair.name == 'Office Chair' and chair.is_storable and shelf1 and shelf2 and small.name and big.name and pallet.name and box.name, \
        f"seed inputs on this clone: {chair.name!r} {shelf1.ids} {shelf2.ids} {small.name!r} {big.name!r} {pallet.name!r} {box.name!r}"
    # the depot exists only to carry the resupply array: it is archived at once (its routes, rules, picking types and
    # locations with it) and the multi-warehouse/multi-location groups its creation switched on for every user are
    # switched off again, so the committed scenarios still run against a single active warehouse per company
    group_user = env.ref('base.group_user')
    implied_before = group_user.implied_ids
    depot = Warehouse.create({'name': 'Seeded Depot', 'code': 'SEED', 'company_id': wh.company_id.id, 'resupply_wh_ids': [(6, 0, wh.ids)]})
    depot.write({'active': False})
    for group in group_user.implied_ids - implied_before:
        group_user.write({'implied_ids': [(3, group.id)]})
        group.write({'user_ids': [(3, user.id) for user in group_user.all_user_ids]})
    assert depot.resupply_wh_ids == wh and not depot.active and group_user.implied_ids == implied_before
    wh.in_type_id.write({'favorite_user_ids': [(4, env.ref('base.user_admin').id)],
                         'wave_location_ids': [(6, 0, (wh.lot_stock_id | shelf1).ids)]})
    furniture.write({'route_ids': [(4, mto.id)]})
    chair.product_tmpl_id.write({'route_ids': [(4, mto.id)]})
    routed_move = env['stock.move'].create({
        'product_id': chair.id, 'product_uom_qty': 2.0, 'route_ids': [(6, 0, mto.ids)],
        'location_id': wh.lot_stock_id.id, 'location_dest_id': env.ref('stock.stock_location_customers').id})
    putaway_rules = env['stock.putaway.rule'].create([
        {'product_id': chair.id, 'location_in_id': wh.lot_stock_id.id, 'location_out_id': shelf1.id, 'sequence': 10},
        {'category_id': furniture.id, 'location_in_id': wh.lot_stock_id.id, 'location_out_id': shelf2.id,
         'storage_category_id': small.id, 'package_type_ids': [(6, 0, (pallet | box).ids)], 'sequence': 20},
    ])
    capacities = env['stock.storage.category.capacity'].create([
        {'storage_category_id': small.id, 'product_id': chair.id, 'quantity': 10.0},
        {'storage_category_id': big.id, 'package_type_id': pallet.id, 'quantity': 4.0},
    ])
    env.flush_all()
    print(f"stock-config seeded: archived warehouse {depot.id} (locations {depot.view_location_id.ids + depot.view_location_id.child_ids.ids}, "
          f"picking types {env['stock.picking.type'].with_context(active_test=False).search([('warehouse_id', '=', depot.id)]).ids}, "
          f"routes {env['stock.route'].with_context(active_test=False).search([('warehouse_ids', 'in', depot.ids)]).ids}, rules {env['stock.rule'].with_context(active_test=False).search([('warehouse_id', '=', depot.id)]).ids}) "
          f"resupplied from {wh.id}; receipts {wh.in_type_id.id} favorite of admin, wave locations {(wh.lot_stock_id | shelf1).ids}; "
          f"MTO route {mto.id} on category {furniture.id}, template {chair.product_tmpl_id.id}, move {routed_move.id}; "
          f"putaway rules {putaway_rules.ids}; capacities {capacities.ids}")
# every row of the unit's tables (and of the wave-1/2 tables the arrays above hang off) carries the fixture instant
# again, so a verifier's reseed reproduces the documents byte for byte
for table in ('stock_warehouse', 'stock_location', 'stock_picking_type', 'stock_route', 'stock_rule', 'stock_putaway_rule',
              'stock_storage_category_capacity', 'stock_warehouse_orderpoint', 'stock_move', 'product_template', 'product_category', 'ir_sequence'):
    env.cr.execute(f"UPDATE {table} SET create_date = %s, write_date = %s WHERE create_date <> %s OR write_date <> %s",
                   (FIXED_INSTANT, FIXED_INSTANT, FIXED_INSTANT, FIXED_INSTANT))
    if env.cr.rowcount:
        print(f"{table}: {env.cr.rowcount} rows re-pinned to {FIXED_INSTANT}")
env.cr.commit()
for table, cols in (('stock_putaway_rule', 'product_id, category_id, location_in_id, location_out_id, storage_category_id, sequence'),
                    ('stock_storage_category_capacity', 'storage_category_id, product_id, package_type_id, quantity'),
                    ('stock_wh_resupply_table', 'supplied_wh_id, supplier_wh_id'),
                    ('stock_location_stock_picking_type_rel', 'stock_picking_type_id, stock_location_id'),
                    ('picking_type_favorite_user_rel', 'picking_type_id, user_id'),
                    ('stock_route_categ', 'route_id, categ_id'), ('stock_route_product', 'route_id, product_id'), ('stock_route_move', 'route_id, move_id'),
                    ('stock_package_type_stock_putaway_rule_rel', 'stock_putaway_rule_id, stock_package_type_id')):
    env.cr.execute(f"SELECT * FROM (SELECT {cols} FROM {table}) t ORDER BY 1, 2")
    print(table, env.cr.fetchall())
