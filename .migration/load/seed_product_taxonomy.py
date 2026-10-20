"""Seed the scenario rows of batch w1-b02 (unit product-taxonomy) on the worker's own PostgreSQL clone.

Same pattern and invocation as seed_scenario_rows.py (w1-b01): run through the pre-opt-in source tree
(the SOURCE_COMMIT worktree build_source.sh keeps at ../odoo-unt12-src) so every write lands on
PostgreSQL and the clone stays a plain source:

    /home/ubuntu/.venvs/odoo/bin/python ../odoo-unt12-src/odoo-bin shell -d <clone> --db_port=5433 \\
        --no-http < .migration/load/seed_product_taxonomy.py

1. Deactivates the six cron writers of NOTES.md s2.3 §1 (ids 19-23 and 1) on the clone.
2. units.json recon_unverified for product-taxonomy: product_tag and product_base_unit have 0 fixture
   rows, and so do the three junction tables (product_tag_product_template_rel,
   product_tag_product_product_rel, product_category_stock_picking_type_rel). Seeds three tags linked
   to the two lowest-id templates / three lowest-id variants, two base units, and two picking types
   with wave categories, with create_date/write_date of the new rows pinned to FIXED_INSTANT so a
   verifier reseeding its own clone gets identical rows.
Idempotent: an already seeded clone only gets the cron step again.
"""
FIXED_INSTANT = '2026-10-20 00:00:00'
CRON_IDS = [1, 19, 20, 21, 22, 23]
TAGS = [
    {'name': 'Fragile', 'sequence': 10, 'color': 1, 'visible_to_customers': True},
    {'name': 'Seasonal', 'sequence': 20, 'color': 4, 'visible_to_customers': False},
    {'name': 'Clearance', 'sequence': 5},  # default color, default visibility
]
BASE_UNITS = [{'name': 'Litre'}, {'name': 'Kilogram'}]
WAVE_CATEGORIES = {1: [1, 4], 3: [5]}  # picking type id -> product category ids (fixture ids)

crons = env['ir.cron'].browse(CRON_IDS).exists()
assert set(crons.ids) == set(CRON_IDS), f"cron ids on this clone: {crons.ids}"
crons.write({'active': False})
print(f"crons deactivated: {sorted(crons.ids)}")


def pin(table, ids):
    env.cr.execute(f"UPDATE {table} SET create_date = %s, write_date = %s WHERE id IN %s",
                   (FIXED_INSTANT, FIXED_INSTANT, tuple(ids)))


Tag = env['product.tag']
if Tag.search_count([]):
    print(f"product.tag already seeded: {Tag.search_count([])} rows")
else:
    templates = env['product.template'].search([], order='id', limit=2)
    variants = env['product.product'].search([], order='id', limit=3)
    links = [
        {'product_template_ids': [(6, 0, templates.ids)], 'product_product_ids': [(6, 0, variants.ids)]},
        {'product_template_ids': [(6, 0, templates[:1].ids)]},
        {},  # no links: a tag without arrays
    ]
    tags = Tag.create([dict(tag, **link) for tag, link in zip(TAGS, links)])
    tags.flush_recordset()
    pin('product_tag', tags.ids)
    print(f"product.tag seeded: ids {tags.ids}, templates {templates.ids}, variants {variants.ids}")

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
