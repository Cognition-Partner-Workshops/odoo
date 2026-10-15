# Scenario rows for the fixture_zero_rows table update_product_attribute_value (batch w1-b03):
# run the update.product.attribute.value wizard once per mode on the fixture, as the source
# application would, so the TransientModel's collection is graded on real rows.
# Executed by `odoo-bin shell -d odoo_fixture` from the pre-migration (PostgreSQL) code.
Wizard = env['update.product.attribute.value']
if not Wizard.search_count([]):
    ptal = env['product.template.attribute.line'].search([('value_ids', '!=', False)], order='id', limit=1)
    unlinked = (ptal.attribute_id.value_ids - ptal.value_ids)[:1]
    Wizard.create({'attribute_value_id': unlinked.id, 'mode': 'add'}).action_confirm()
    Wizard.create({'attribute_value_id': ptal.value_ids[:1].id, 'mode': 'update_extra_price'}).action_confirm()
    env.cr.commit()
print('update_product_attribute_value rows:', Wizard.search_count([]))
