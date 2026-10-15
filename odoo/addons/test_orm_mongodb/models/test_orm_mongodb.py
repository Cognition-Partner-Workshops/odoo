from odoo import api, fields, models


class Category(models.Model):
    """PostgreSQL model referenced by, and referencing, MongoDB models."""
    _name = 'test_orm_mongodb.category'
    _description = 'MongoDB test category (PostgreSQL)'
    _order = 'name, id'

    name = fields.Char(required=True)
    item_ids = fields.One2many('test_orm_mongodb.item', 'category_id')
    default_item_id = fields.Many2one('test_orm_mongodb.item', ondelete='set null')
    item_count = fields.Integer(compute='_compute_item_count')

    @api.depends('item_ids')
    def _compute_item_count(self):
        for category in self:
            category.item_count = len(category.item_ids)


class Tag(models.Model):
    _name = 'test_orm_mongodb.tag'
    _description = 'MongoDB test tag (PostgreSQL)'

    name = fields.Char(required=True)
    item_ids = fields.Many2many(
        'test_orm_mongodb.item', 'test_orm_mongodb_item_tag_rel', 'tag_id', 'item_id',
    )


class Item(models.Model):
    """Model stored in MongoDB: documents in collection ``testOrmMongodbItem``."""
    _name = 'test_orm_mongodb.item'
    _description = 'MongoDB test item'
    _storage = 'mongodb'
    _order = 'sequence, id'

    name = fields.Char(required=True)
    code = fields.Char()
    sequence = fields.Integer(default=10)
    quantity = fields.Integer(default=0)
    price = fields.Float()
    active = fields.Boolean(default=True)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default='draft')
    date = fields.Date()
    note = fields.Text()
    category_id = fields.Many2one('test_orm_mongodb.category')
    tag_ids = fields.Many2many(
        'test_orm_mongodb.tag', 'test_orm_mongodb_item_tag_rel', 'item_id', 'tag_id',
    )
    line_ids = fields.One2many('test_orm_mongodb.line', 'item_id')
    total = fields.Float(compute='_compute_total', store=True)

    _code_uniq = models.Constraint('UNIQUE (code)', 'The code must be unique.')
    _quantity_positive = models.Constraint('CHECK (quantity >= 0)', 'The quantity cannot be negative.')

    @api.depends('line_ids.amount')
    def _compute_total(self):
        for item in self:
            item.total = sum(item.line_ids.mapped('amount'))


class Line(models.Model):
    _name = 'test_orm_mongodb.line'
    _description = 'MongoDB test line'
    _storage = 'mongodb'

    item_id = fields.Many2one('test_orm_mongodb.item', required=True, ondelete='cascade')
    label = fields.Char()
    amount = fields.Float()
