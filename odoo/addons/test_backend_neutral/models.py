from odoo import fields, models


class TestBackendNeutralItem(models.Model):
    """ Sample model of the harness smoke tests: one declared constraint of
    each kind the neutral ``IntegrityError`` covers. """
    _name = 'test_backend_neutral.item'
    _description = 'Backend Neutral Test Item'
    _order = 'id'

    name = fields.Char(required=True)
    code = fields.Char()
    quantity = fields.Integer()
    parent_id = fields.Many2one('test_backend_neutral.item', ondelete='restrict')
    child_ids = fields.One2many('test_backend_neutral.item', 'parent_id')

    _code_unique = models.Constraint(
        'UNIQUE(code)',
        "The code of an item must be unique!",
    )
    _quantity_positive = models.Constraint(
        'CHECK(quantity >= 0)',
        "The quantity of an item must be positive!",
    )
