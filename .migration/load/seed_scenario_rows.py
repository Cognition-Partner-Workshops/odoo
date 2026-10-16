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

Tag = env['product.tag']
if not Tag.search_count([]):
    seasonal = Tag.create({'name': 'Seasonal', 'sequence': 1, 'color': '#FF7F0E', 'visible_to_customers': True})
    env['res.lang']._activate_lang('fr_FR')  # one translated value exercises the {lang: value} shape
    seasonal.with_context(lang='fr_FR').name = 'Saisonnier'
    Tag.create({'name': 'Clearance', 'sequence': 5, 'color': '#3C3C3C', 'visible_to_customers': False})
    Tag.create({'name': 'Staff pick', 'sequence': 10, 'color': '#2CA02C', 'visible_to_customers': True})
BaseUnit = env['product.base.unit']
if not BaseUnit.search_count([]):
    BaseUnit.create([{'name': 'per 100 g'}, {'name': 'per litre'}])
env.flush_all()   # the pending translation write would re-stamp write_date after the pin
for table in ('product_tag', 'product_base_unit'):
    env.cr.execute(f"UPDATE {table} SET create_date = %(t)s, write_date = %(t)s", {'t': FIXED_INSTANT})
env.invalidate_all()
env.cr.commit()
print('scenario rows:', Tag.search_count([]), 'tags,', BaseUnit.search_count([]), 'base units')
