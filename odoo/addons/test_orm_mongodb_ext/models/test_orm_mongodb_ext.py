from odoo import fields, models


class Item(models.Model):
    """Field declared by another addon on a MongoDB model (NOTES.md D1:
    foreign-module fields travel with the document)."""
    _inherit = 'test_orm_mongodb.item'

    extra_tag_ids = fields.Many2many(
        'test_orm_mongodb.tag', 'test_orm_mongodb_item_extra_tag_rel', 'item_id', 'tag_id',
        string='Extra tags',
    )


class Tag(models.Model):
    _inherit = 'test_orm_mongodb.tag'

    extra_item_ids = fields.Many2many(
        'test_orm_mongodb.item', 'test_orm_mongodb_item_extra_tag_rel', 'tag_id', 'item_id',
    )
