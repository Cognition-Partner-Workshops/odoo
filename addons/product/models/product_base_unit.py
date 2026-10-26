from odoo import fields, models


class ProductBaseUnit(models.Model):
    _name = 'product.base.unit'
    _description = "Unit of Measure for price per unit on products."
    _storage = 'mongodb'      # UNT14 wave 2 w2-b01: documents in odoo_unt13.productBaseUnit (signed spec map-draft-5)
    _order = 'name'

    name = fields.Char(
        help="Define a custom unit to display in the price per unit of measure field.",
        required=True,
        translate=True,
    )
