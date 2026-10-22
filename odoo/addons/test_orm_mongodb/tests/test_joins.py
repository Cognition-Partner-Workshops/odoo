from odoo import Command
from odoo.tests import TransactionCase, tagged


@tagged('at_install', '-post_install')
class TestCrossStoreOrderMongodb(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Attribute = cls.env['test_orm_mongodb.attribute']
        cls.Value = cls.env['test_orm_mongodb.attribute_value']
        cls.Tag = cls.env['test_orm_mongodb.tag']
        cls.Link = cls.env['test_orm_mongodb.pg_link']
        cls.color, cls.size = cls.Attribute.create([
            {'name': 'Color', 'sequence': 2, 'value_ids': [Command.create({'name': 'Red'})]},
            {'name': 'Size', 'sequence': 1, 'value_ids': [Command.create({'name': 'Large'})]},
        ])
        cls.values = cls.color.value_ids + cls.size.value_ids

    def test_mongodb_model_orders_by_many2one(self):
        red, large = self.values
        domain = [('id', 'in', self.values.ids)]
        self.assertEqual(self.Value.search(domain, order='attribute_id, id'), large + red)    # Size's sequence first
        self.assertEqual(self.Value.search(domain, order='attribute_id desc, id'), red + large)
        self.assertEqual(self.Value.search(domain, order='attribute_id.id, id'), red + large)  # raw ids

    def test_postgresql_model_orders_by_mongodb_many2one(self):
        late, early = self.Tag.create([{'name': 'late', 'sequence': 9}, {'name': 'early', 'sequence': 1}])
        a, b, c = self.Link.create([
            {'name': 'a', 'tag_id': late.id}, {'name': 'b', 'tag_id': early.id}, {'name': 'c'},
        ])
        domain = [('id', 'in', (a + b + c).ids)]
        self.assertEqual(self.Link.search(domain, order='tag_id, id'), b + a + c)     # NULL last
        self.assertEqual(self.Link.search(domain, order='tag_id desc, id'), c + a + b)
