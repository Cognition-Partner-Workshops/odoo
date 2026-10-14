# One outlier parent for the recon fixture: a template whose variant fan-out (6 x 5 x 2 = 60)
# is far past the source profile's max of 5 variants per template, 2 attribute lines and
# 5 template attribute values. Executed by build_fixture.sh through
# `odoo-bin shell -d odoo_fixture`; deterministic on purpose. Never run against odoo_src.
assert env.cr.dbname == 'odoo_fixture', env.cr.dbname


def attribute(name, values):
    return env['product.attribute'].create({
        'name': name,
        'create_variant': 'always',
        'value_ids': [(0, 0, {'name': value, 'sequence': i}) for i, value in enumerate(values)],
    })


size = attribute('Fixture Size', ['XS', 'S', 'M', 'L', 'XL', 'XXL'])
color = attribute('Fixture Color', ['Black', 'White', 'Navy', 'Olive', 'Red'])
fit = attribute('Fixture Fit', ['Regular', 'Slim'])
template = env['product.template'].create({
    'name': 'Fixture Outlier Tee',
    'categ_id': env.ref('product.product_category_goods').id,
    'list_price': 20.0,
    'uom_id': env.ref('uom.product_uom_unit').id,
    'attribute_line_ids': [
        (0, 0, {'attribute_id': attr.id, 'value_ids': [(6, 0, attr.value_ids.ids)]})
        for attr in (size, color, fit)
    ],
})
assert len(template.product_variant_ids) == 60, len(template.product_variant_ids)
env['ir.model.data'].create({
    'module': '__migration__', 'name': 'fixture_outlier_tee',
    'model': 'product.template', 'res_id': template.id, 'noupdate': True,
})
env['ir.config_parameter'].set_str('migration.fixture', '1')
env.cr.commit()
