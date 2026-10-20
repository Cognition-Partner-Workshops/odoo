"""Scenario rows for the product-taxonomy unit (wave 1, w1-b02).

`product_tag` and `product_base_unit` are empty in `odoo_src`, so the live recon would leave
them UNVERIFIED. The batch notes require scenario rows: they are created through the ORM on a
clone of the fixture database (never in `odoo_src`), with the PostgreSQL storage of
`build_source.sh`'s SOURCE_COMMIT worktree (the run branch before any model opted into MongoDB):

    createdb -h /var/run/postgresql -p 5433 -T odoo_fixture odoo_w1b02_fix
    cd ../odoo-base && odoo-bin shell -d odoo_w1b02_fix --db_port=5433 --no-http \
        --addons-path=addons,odoo/addons < <repo>/.migration/load/seed_scenario_rows.py

The clone is the source of the committed live recon (`ODOO_SCENARIO_DSN`: the read-only DSN
with `database` set to `odoo_w1b02_fix`); the loader and the recon harness read it read-only.

Deterministic (d-taxonomy-seed-drift = pin-and-reload): the ORM stamps `create_date` /
`write_date` with now(), so two clones seeded on different VMs would differ on exactly those
columns and an independent verifier's re-seeded clone would fail Tier 3. After the ORM writes,
both tables are pinned to FIXED_INSTANT, the instant `build_source.sh` pins every source row to;
every other seeded value is a literal. Prove it with two clones and a data-only pg_dump diff.
"""
FIXED_INSTANT = '2026-10-14 00:00:00'   # UTC; keep equal to build_source.sh FIXED_INSTANT


def unseeded(section, found, expected):
    """`found` are the natural keys of the rows a section's lookup returned, `expected` the keys of the
    rows it seeds. None found: seed; exactly the expected keys: skip. Anything else (a missing row, a
    duplicate, a foreign row) is a clone edited after seeding -- sections commit together, so seeding
    cannot leave one half done -- which this script refuses to repair rather than trip a unique
    constraint or hide a missing scenario row."""
    found, expected = sorted(map(str, found)), sorted(map(str, expected))
    if found and found != expected:
        raise SystemExit(f'refusing: {section} holds {found}, not the scenario rows {expected}; '
                         'reseed from a fresh clone of odoo_src')
    return not found

Tag = env['product.tag']
TAGS = ['Seasonal', 'Clearance', 'Staff pick']
if unseeded('product_tag', Tag.with_context(lang='en_US').search([('name', 'in', TAGS)]).mapped('name'), TAGS):
    seasonal = Tag.create({'name': 'Seasonal', 'sequence': 1, 'color': '#FF7F0E', 'visible_to_customers': True})
    env['res.lang']._activate_lang('fr_FR')  # one translated value exercises the {lang: value} shape
    seasonal.with_context(lang='fr_FR').name = 'Saisonnier'
    Tag.create({'name': 'Clearance', 'sequence': 5, 'color': '#3C3C3C', 'visible_to_customers': False})
    Tag.create({'name': 'Staff pick', 'sequence': 10, 'color': '#2CA02C', 'visible_to_customers': True})
BaseUnit = env['product.base.unit']
BASE_UNITS = ['per 100 g', 'per litre']
if unseeded('product_base_unit', BaseUnit.with_context(lang='en_US').search([('name', 'in', BASE_UNITS)]).mapped('name'), BASE_UNITS):
    BaseUnit.create([{'name': 'per 100 g'}, {'name': 'per litre'}])

# --- product-catalog (wave 2, w2-b01): product_uom and the four empty relation tables, seeded the
# same way on a clone of odoo_src (createdb -T odoo_src odoo_w2b01_src; the live source, as wave 1)
# product_product_uom_uom_rel (extra_uom_ids), product_template_uom_uom_rel (uom_ids),
# product_tag_product_product_rel (additional_product_tag_ids), product_tag_product_template_rel
# (product_tag_ids). Packagings come from wave 1's uom.uom (Pack of 6 / Dozens, xml ids), tags
# from the rows above; products are the three lowest-id active variants with a barcode.
ProductUom = env['product.uom']
products = env['product.product'].search([('barcode', '!=', False)], order='id', limit=3)
if unseeded('product_uom', ProductUom.search([('barcode', '=like', 'SCN-%')]).mapped('barcode'),
            [f'SCN-{pack}-{product.id:06d}' for product in products for pack in ('PACK6', 'DOZEN')]):
    pack6, dozen = env.ref('uom.product_uom_pack_6'), env.ref('uom.product_uom_dozen')
    tags = env['product.tag'].search([], order='sequence, id')
    for i, product in enumerate(products):
        ProductUom.create([
            {'product_id': product.id, 'uom_id': pack6.id, 'barcode': f'SCN-PACK6-{product.id:06d}'},
            {'product_id': product.id, 'uom_id': dozen.id, 'barcode': f'SCN-DOZEN-{product.id:06d}'},
        ])
        product.extra_uom_ids = [(6, 0, [pack6.id, dozen.id][: i + 1])]
        product.additional_product_tag_ids = [(6, 0, tags[: i + 1].ids)]
        product.product_tmpl_id.uom_ids = [(6, 0, [dozen.id, pack6.id][: i + 1])]
        product.product_tmpl_id.product_tag_ids = [(6, 0, tags[-(i + 1):].ids)]
# --- product-combo (wave 3, w3-b03): the three source combos have company_id NULL, so the company
# rule, _check_company_id, the stored related company_id on items, the translated name and extra_price
# are only observable on a seeded combo (createdb -T odoo_src odoo_w3b03_src). Products: the two
# lowest-id active non-combo variants whose template carries taxes (the account D5 tax writer).
Combo = env['product.combo']
if unseeded('product_combo', Combo.with_context(lang='en_US').search([('name', '=', 'Chicago Desk Set')]).mapped('name'), ['Chicago Desk Set']):
    env['res.lang']._activate_lang('fr_FR')
    taxed = env['product.product'].search([('type', '!=', 'combo'), ('taxes_id', '!=', False)], order='id', limit=2)
    combo = Combo.create({
        'name': 'Chicago Desk Set',
        'sequence': 20,
        'company_id': env['res.company'].search([], order='id desc', limit=1).id,  # My Company (Chicago), id 3
        'combo_item_ids': [
            (0, 0, {'product_id': taxed[0].id, 'extra_price': 7.5}),
            (0, 0, {'product_id': taxed[1].id, 'extra_price': 0.0}),
        ],
    })
    combo.with_context(lang='fr_FR').name = 'Ensemble bureau Chicago'
# --- product-variant-extras (wave 3, w3-b04): product_attribute_custom_value and the transient
# product_label_layout with its four relation tables, all empty in odoo_src; seeded on a clone the
# same way. Custom values hang off the two product_template_attribute_value rows whose attribute
# value is already is_custom (no other source row is flipped): two parentless rows on the same
# value exercise the NULL semantics of sale's unique(custom_ptav, sale_order_line_id), three rows
# belong to sale order lines. Wizard rows cover every print_format, the three product arrays,
# pricelist, packaging and stock's move_ids / move_quantity / print_packaging.
CustomValue = env['product.attribute.custom.value']
ptavs = env['product.template.attribute.value'].search(
    [('product_attribute_value_id.is_custom', '=', True)], order='id')
lines = env['sale.order.line'].search([], order='id', limit=3)
custom_vals = [
    {'custom_product_template_attribute_value_id': ptavs[0].id, 'custom_value': 'Walnut legs, 72 cm'},
    {'custom_product_template_attribute_value_id': ptavs[0].id, 'custom_value': 'Oak legs, 68 cm'},
    {'custom_product_template_attribute_value_id': ptavs[1].id, 'custom_value': False},
] + [
    {'custom_product_template_attribute_value_id': ptavs[i % len(ptavs)].id,
     'custom_value': f'Engraved for order line {line.id}', 'sale_order_line_id': line.id}
    for i, line in enumerate(lines)
]
if unseeded('product_attribute_custom_value',
            [(r.custom_product_template_attribute_value_id.id, r.custom_value, r.sale_order_line_id.id)
             for r in CustomValue.search([('custom_product_template_attribute_value_id', 'in', ptavs.ids)])],
            [(v['custom_product_template_attribute_value_id'], v['custom_value'], v.get('sale_order_line_id', False))
             for v in custom_vals]):
    CustomValue.create(custom_vals)
Layout = env['product.label.layout']
# A transient table: odoo_src holds no wizard rows, so every row on a seeded clone must be one of the
# five below (one per print_format); any other set is a foreign clone.
if unseeded('product_label_layout', Layout.search([]).mapped('print_format'), ['dymo', '2x7', '4x7', '4x12', 'zpl']):
    # Transient rows can be vacuumed; a re-seed into an emptied clone would allocate new wizard ids and no
    # longer match a load keyed on the first run's ids. Seed a fresh clone of odoo_src instead.
    env.cr.execute("SELECT is_called FROM product_label_layout_id_seq")
    if env.cr.fetchone()[0]:
        raise SystemExit('refusing: product_label_layout is empty but its id sequence has advanced; '
                         're-seed a fresh clone of odoo_src rather than this one')
    pack6 = env.ref('uom.product_uom_pack_6')
    products = env['product.product'].search([('barcode', '!=', False)], order='id', limit=3)
    pricelist = env['product.pricelist'].search([], order='id', limit=1)
    moves = env['stock.move'].search([('state', '=', 'done')], order='id', limit=4)
    Layout.create([
        {'print_format': 'dymo', 'product_ids': [(6, 0, products.ids)], 'custom_quantity': 2,
         'pricelist_id': pricelist.id},
        {'print_format': '2x7', 'product_tmpl_ids': [(6, 0, products.product_tmpl_id.ids)],
         'with_price': False, 'extra_html': '<p>Fragile</p>'},
        {'print_format': '4x7', 'product_ids': [(6, 0, products[:1].ids)], 'packaging_id': pack6.id,
         'product_uom_ids': [(6, 0, env['product.uom'].search([('product_id', '=', products[0].id)], order='id').ids)]},
        {'print_format': '4x12', 'barcode_format': 'qr', 'move_ids': [(6, 0, moves.ids)],
         'move_quantity': 'move', 'print_packaging': True},
        {'print_format': 'zpl', 'zpl_template': 'jewelry', 'product_ids': [(6, 0, products[1:].ids)],
         'move_ids': [(6, 0, moves[:2].ids)], 'move_quantity': 'custom', 'custom_quantity': 3},
    ])

# Every section is guarded on the presence of its own named rows (compared in en_US, the language they
# are created in), never on a table's total count: a
# neighbouring section can add rows to a shared table as a side effect (activating a currency makes
# `res.company._activate_or_create_pricelists` add a Default pricelist per company), which turned the
# former `search_count([]) == 1` guard false and skipped the whole section. Each section also looks
# up what it needs itself, so sections can be reordered or run alone; one pin and commit at the end.

# --- product-pricing (wave 3, w3-b01): odoo_src holds one pricelist and one item, seeded the same
# way on a clone (createdb -T odoo_src odoo_w3b01_src). Adds the second currency (base.EUR is
# inactive in the source; a Many2one to it is valid), a country group (base.europe), a company
# pricelist, an archived pricelist, a translated name, and one item per applied_on with the
# markup / discount-with-rounding-and-margins (base=pricelist -> another pricelist) / plain discount
# compute modes (Odoo 20 has discount, markup, fixed), a date window,
# min_quantity > 0 and a uom_id. mail.thread rows are suppressed so only the unit's tables change.
Pricelist = env['product.pricelist'].with_context(tracking_disable=True, mail_create_nolog=True)
Item = env['product.pricelist.item']
PRICELISTS = ['Europe Wholesale', 'US Company Retail', 'Legacy 2024']
if unseeded('product_pricelist', Pricelist.with_context(active_test=False, lang='en_US').search(
        [('name', 'in', PRICELISTS)]).mapped('name'), PRICELISTS):
    env['res.lang']._activate_lang('fr_FR')
    furniture = env['product.category'].search([('name', '=', 'Furniture')], limit=1)
    chair = env['product.template'].search([('categ_id', 'child_of', furniture.id)], order='id', limit=1)
    europe = Pricelist.create({
        'name': 'Europe Wholesale', 'sequence': 5, 'currency_id': env.ref('base.EUR').id,
        'company_id': False,
        'country_group_ids': [(6, 0, [env.ref('base.europe').id])],
    })
    europe.with_context(lang='fr_FR').name = 'Europe grossistes'
    us_company = Pricelist.create({
        'name': 'US Company Retail', 'sequence': 10,
        'company_id': env['res.company'].search([('id', '!=', env.company.id)], order='id', limit=1).id,
    })
    Pricelist.create({'name': 'Legacy 2024', 'sequence': 20, 'active': False})
    Item.create([
        {'pricelist_id': europe.id, 'applied_on': '3_global', 'compute_price': 'markup',
         'price_markup': 10.0},
        {'pricelist_id': europe.id, 'applied_on': '2_product_category', 'categ_id': furniture.id,
         'compute_price': 'discount', 'price_discount': 15.0},
        {'pricelist_id': europe.id, 'applied_on': '1_product', 'product_tmpl_id': chair.id,
         'compute_price': 'fixed', 'fixed_price': 99.9,
         'date_start': '2026-01-01 00:00:00', 'date_end': '2026-12-31 23:59:59'},
        {'pricelist_id': europe.id, 'applied_on': '0_product_variant',
         'product_id': chair.product_variant_id.id, 'min_quantity': 5, 'uom_id': chair.uom_id.id,
         'compute_price': 'fixed', 'fixed_price': 89.0},
        {'pricelist_id': us_company.id, 'applied_on': '3_global', 'compute_price': 'markup',
         'price_markup': 15.0},
        # base=pricelist must not cross companies (_check_company_auto): the company-less Europe
        # pricelist is the only valid base for a company pricelist's item.
        {'pricelist_id': us_company.id, 'applied_on': '2_product_category', 'categ_id': furniture.id,
         'min_quantity': 2, 'compute_price': 'discount', 'base': 'pricelist',
         'base_pricelist_id': europe.id, 'price_discount': 5.0, 'price_surcharge': 1.5,
         'price_round': 0.05, 'price_min_margin': 1.0, 'price_max_margin': 20.0},
    ])
env.flush_all()   # the pending translation writes would re-stamp write_date after the pin
for table in ('product_tag', 'product_base_unit', 'product_uom', 'product_product', 'product_template',
              'product_combo', 'product_combo_item', 'product_attribute_custom_value', 'product_label_layout',
              'product_pricelist', 'product_pricelist_item'):
    env.cr.execute(f"UPDATE {table} SET create_date = %(t)s, write_date = %(t)s", {'t': FIXED_INSTANT})
env.invalidate_all()
env.cr.commit()
print('scenario rows:', Tag.search_count([]), 'tags,', BaseUnit.search_count([]), 'base units,',
      ProductUom.search_count([]), 'product uoms,', Combo.search_count([]), 'combos,',
      CustomValue.search_count([]), 'custom values,', Layout.search_count([]), 'label layouts,',
      Pricelist.with_context(active_test=False).search_count([]), 'pricelists,',
      Item.search_count([]), 'pricelist items')
