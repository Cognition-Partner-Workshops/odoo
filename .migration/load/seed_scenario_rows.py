"""Scenario rows for the product-taxonomy unit (wave 1, w1-b02).

`product_tag` and `product_base_unit` are empty in `odoo_src`, so the live recon would leave
them UNVERIFIED. The batch notes require scenario rows: they are created through the ORM on a
clone of the fixture database (never in `odoo_src`), with the PostgreSQL storage of the run
branch tip, i.e. before this batch opts the models into MongoDB:

    createdb -h /var/run/postgresql -p 5433 -T odoo_fixture odoo_w1b02_fix
    git worktree add /tmp/odoo-base mongo-run/20261014
    cd /tmp/odoo-base && odoo-bin shell -d odoo_w1b02_fix --db_port=5433 --no-http \
        --addons-path=addons,odoo/addons < <repo>/.migration/load/seed_scenario_rows.py

The clone is the source of the committed live recon (`ODOO_SCENARIO_DSN`: the read-only DSN
with `database` set to `odoo_w1b02_fix`); the loader and the recon harness read it read-only.
"""
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
env.cr.commit()
print('scenario rows:', Tag.search_count([]), 'tags,', BaseUnit.search_count([]), 'base units')
