# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.addons.stock import _create_inventory_adjustment, _read_stored_qty_available, _save_current_inventory
from odoo.tests import TransactionCase


class TestInitHooks(TransactionCase):

    def test_stored_qty_available_roundtrip(self):
        """ The uninstall hook saves the on-hand quantity into the stored ``qty_available``
        of product.product and the install hook rebuilds the inventory from it, both
        through the model's storage (table or collection). """
        company = self.env.company
        location = self.env['stock.warehouse'].search([('company_id', '=', company.id)], limit=1).lot_stock_id
        product = self.env['product.product'].create({'name': 'Hooked', 'is_storable': True})
        self.env['stock.quant']._update_available_quantity(product, location, 7)

        _save_current_inventory(self.env)
        self.assertEqual(_read_stored_qty_available(self.env).get(product.id), {str(company.id): 7.0})

        self.env['stock.quant']._update_available_quantity(product, location, -7)
        product.invalidate_recordset(['qty_available'])
        self.assertEqual(product.qty_available, 0)
        _create_inventory_adjustment(self.env)
        product.invalidate_recordset(['qty_available'])
        self.assertEqual(product.qty_available, 7)
