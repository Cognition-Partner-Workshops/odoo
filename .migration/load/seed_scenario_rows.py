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
