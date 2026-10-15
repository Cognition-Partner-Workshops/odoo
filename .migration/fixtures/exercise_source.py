# Standard ORM flows run once after install so mail/audit tables carry real rows.
# Executed by build_source.sh through `odoo-bin shell`; deterministic on purpose.
category = env['product.category'].create({'name': 'Migration Fixture', 'parent_id': env.ref('product.product_category_goods').id})
template = env['product.template'].create({
    'name': 'Fixture Desk Lamp',
    'categ_id': category.id,
    'list_price': 40.0,
    'uom_id': env.ref('uom.product_uom_unit').id,
    'is_storable': True,
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

# Wider modeling fixture: a received purchase, a confirmed sale and its posted invoice,
# so order, picking, move, quant and journal tables carry rows beyond the demo data.
product = template.product_variant_id
purchase = env['purchase.order'].create({
    'partner_id': env.ref('base.res_partner_12').id,
    'order_line': [(0, 0, {'product_id': product.id, 'product_qty': 20.0, 'price_unit': 25.0})],
})
purchase.button_confirm()
receipt = purchase.picking_ids
receipt.move_ids.write({'quantity': 20.0, 'picked': True})
receipt.button_validate()
assert receipt.state == 'done', receipt.state
sale = env['sale.order'].create({
    'partner_id': env.ref('base.res_partner_2').id,
    'order_line': [(0, 0, {'product_id': product.id, 'product_uom_qty': 5.0})],
})
sale.action_confirm()
assert sale.state == 'sale' and sale.picking_ids, sale.state
invoice = sale._create_invoices()
invoice.action_post()
assert invoice.state == 'posted', invoice.state
env.cr.commit()   # build_source.sh pins the timestamps and sets the marker next
