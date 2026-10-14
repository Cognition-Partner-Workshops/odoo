# Standard ORM flows run once after install so mail/audit tables carry real rows.
# Executed by build_source.sh through `odoo-bin shell`; deterministic on purpose.
category = env['product.category'].create({'name': 'Migration Fixture', 'parent_id': env.ref('product.product_category_goods').id})
template = env['product.template'].create({
    'name': 'Fixture Desk Lamp',
    'categ_id': category.id,
    'list_price': 40.0,
    'uom_id': env.ref('uom.product_uom_unit').id,
})
template.write({'list_price': 45.0})
template.message_post(body='Price reviewed for the migration fixture.')
desk = env.ref('product.product_product_3').product_tmpl_id
desk.write({'list_price': desk.list_price + 10.0})
env.ref('product.product_product_9').product_tmpl_id.action_archive()
pricelist = env['product.pricelist'].create({'name': 'Fixture Pricelist'})
env['product.pricelist.item'].create({
    'pricelist_id': pricelist.id,
    'applied_on': '1_product',
    'product_tmpl_id': template.id,
    'compute_price': 'fixed',
    'fixed_price': 39.0,
})
env['ir.config_parameter'].set_str('migration.fixture_source', '1')
env.cr.commit()
