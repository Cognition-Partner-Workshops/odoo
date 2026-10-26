from odoo import models, fields


class StockScrapReasonTag(models.Model):
    _name = 'stock.scrap.reason.tag'
    _description = 'Scrap Reason Tag'
    _storage = 'mongodb'      # UNT14 wave 2 w2-b01: documents in odoo_unt13.stockScrapReasonTag (signed spec map-draft-5)
    _order = 'sequence, id'

    name = fields.Char(string="Name", required=True, translate=True)
    sequence = fields.Integer(default=10)
    color = fields.Integer(string="Color", default=0x3C3C3C)

    _name_uniq = models.Constraint(
        'unique (name)',
        'Tag name already exists!',
    )
