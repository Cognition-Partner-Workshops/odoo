# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.fields import Command
from odoo.tests import HttpCase, tagged

from odoo.addons.product.tests.common import ProductVariantsCommon
from odoo.addons.sale.tests.common import SaleCommon


@tagged("post_install", "-at_install")
class TestSaleOrderUI(HttpCase, ProductVariantsCommon):
    _test_user_groups = (
        'product.group_product_manager',
        'sales_team.group_sale_manager',  # FIXME: use sales_team.group_sale_salesman
    )

    _test_user_name = 'Test Sales & Product Manager'

    def test_sale_order_keep_uom_on_variant_wizard_quantity_change(self):
        so = self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "order_line": [
                Command.create({
                    "product_id": self.product_template_sofa.product_variant_ids[0].id,
                    "product_uom_id": self.uom_dozen.id,
                    "product_uom_qty": 1,
                })
            ],
        })

        self.start_tour(
            f"/odoo/sales/{so.id}",
            "sale_order_keep_uom_on_variant_wizard_quantity_change",
            login=self.env.user.login,
        )

        sol = so.order_line[0]
        self.assertEqual(sol.product_uom_id, self.uom_dozen)


@tagged("post_install", "-at_install")
class TestSaleOrderFlowUI(HttpCase, SaleCommon):
    _test_user_groups = (*SaleCommon._test_user_groups, 'base.group_partner_manager')

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        tax = cls.env["account.tax"].create({
            "name": "Tour 15%",
            "amount": 15.0,
            "amount_type": "percent",
            "type_tax_use": "sale",
        })
        cls.env["product.product"].create([
            {"name": "Tour Desk", "list_price": 147.0, "taxes_id": [Command.set(tax.ids)]},
            {"name": "Tour Cabinet", "list_price": 320.0, "taxes_id": [Command.set(tax.ids)]},
        ])

    def test_quotation_to_order_flow(self):
        self.start_tour(
            "/odoo/action-base.action_partner_form",
            "sale_quotation_to_order_flow",
            login=self.env.user.login,
        )

        partner = self.env["res.partner"].search([("name", "=", "Tour Flow Company")])
        self.assertRecordValues(partner, [{"email": "tour.flow@example.com", "phone": "+1 415 555 0127"}])

        order = self.env["sale.order"].search([("partner_id", "=", partner.id)])
        self.assertRecordValues(order, [{
            "state": "sale",
            "user_id": self.env.user.id,
            "amount_untaxed": 614.0,
            "amount_tax": 92.1,
            "amount_total": 706.1,
        }])
        self.assertEqual(order.order_line.mapped("product_uom_qty"), [2.0, 1.0])
