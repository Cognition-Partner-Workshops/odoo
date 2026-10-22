import psycopg2.errors

from odoo import Command
from odoo.orm import storage_mongodb
from odoo.tests import TransactionCase, tagged


@tagged('at_install', '-post_install')
class TestEmbeddedChildrenMongodb(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Attribute = cls.env['test_orm_mongodb.attribute']
        cls.Value = cls.env['test_orm_mongodb.attribute_value']
        cls.color, cls.size = cls.Attribute.create([
            {'name': 'Color', 'value_ids': [
                Command.create({'name': 'Red', 'sequence': 2, 'html_color': '#f00'}),
                Command.create({'name': 'Blue', 'sequence': 1, 'html_color': '#00f'}),
            ]},
            {'name': 'Size', 'value_ids': [Command.create({'name': 'Large', 'sequence': 1})]},
        ])

    def elements(self, attribute):
        self.env.flush_all()
        doc = storage_mongodb.get_collection(attribute).find_one({'_id': attribute.id})
        return doc.get('value', [])

    def names(self, attribute):
        return [element['name']['en_US'] for element in self.elements(attribute)]

    def test_embedded_documents(self):
        red, blue = self.color.value_ids.sorted('id')
        self.assertEqual(self.names(self.color), ['Red', 'Blue'])
        element = self.elements(self.color)[0]
        self.assertEqual(element['id'], red.id)
        self.assertEqual(element['htmlColor'], '#f00')
        self.assertNotIn('attributeId', element)
        self.assertNotIn('_id', element)
        self.env.cr.execute("SELECT id FROM product_attribute_value WHERE id IN %s", [tuple((red + blue).ids)])
        self.assertEqual(len(self.env.cr.fetchall()), 2)

        self.env.invalidate_all()
        self.assertEqual(self.color.value_ids, blue + red)      # ordered by sequence
        self.assertEqual(red.attribute_id, self.color)
        self.assertEqual((red.name, red.sequence, red.html_color), ('Red', 2, '#f00'))

    def test_embedded_writes(self):
        red, blue = self.color.value_ids.sorted('id')
        large = self.size.value_ids

        red.write({'html_color': '#e00', 'default_extra_price': 1.5})
        self.assertEqual(self.names(self.color), ['Red', 'Blue'])   # updated in place
        self.assertEqual(self.elements(self.color)[0]['htmlColor'], '#e00')
        blue.html_color = False
        self.assertNotIn('htmlColor', self.elements(self.color)[1])

        red.attribute_id = self.size
        self.assertEqual(self.names(self.color), ['Blue'])
        self.assertEqual(self.names(self.size), ['Large', 'Red'])
        self.env.invalidate_all()
        self.assertEqual(self.size.value_ids, large + red)
        self.assertEqual(red.default_extra_price, 1.5)

        blue.unlink()
        self.assertEqual(self.elements(self.color), [])
        self.size.unlink()
        self.assertFalse((red + large).exists())
        self.env.cr.execute("SELECT id FROM product_attribute_value WHERE id IN %s", [tuple((red + large).ids)])
        self.assertFalse(self.env.cr.fetchall())

    def test_embedded_search(self):
        red, blue = self.color.value_ids.sorted('id')
        large = self.size.value_ids
        values = red + blue + large
        self.assertEqual(self.Value.search([('id', 'in', values.ids), ('name', 'ilike', 'r')]), red + large)
        self.assertEqual(self.Value.search([('attribute_id', '=', self.color.id)]), blue + red)
        self.assertEqual(self.Value.search([('id', 'in', values.ids), ('html_color', '=', False)]), large)
        self.assertEqual(self.Value.search([('id', 'in', values.ids)], order='sequence desc, id desc'),
                         red + large + blue)
        self.assertEqual(self.Value.search([('id', 'in', values.ids)], order='id', limit=1, offset=1), blue)
        self.assertEqual(self.Value.search_count([('attribute_id.name', '=', 'Size')]), 1)
        self.assertEqual(self.Attribute.search([('value_ids.html_color', '=', '#00f')]), self.color)
        self.assertEqual(self.Attribute.search([('id', 'in', (self.color + self.size).ids),
                                                ('value_ids', '=', False)]), self.Attribute)

    def test_savepoint_rollback_restores_elements(self):
        red, blue = self.color.value_ids.sorted('id')
        before = (self.elements(self.color), self.elements(self.size))
        with self.assertRaises(ZeroDivisionError), self.env.cr.savepoint():
            red.html_color = '#000'
            blue.attribute_id = self.size
            self.Value.create({'attribute_id': self.color.id, 'name': 'Green'})
            self.size.value_ids.filtered(lambda value: value.name == 'Large').unlink()
            1 / 0
        self.assertEqual((self.elements(self.color), self.elements(self.size)), before)

    def test_parent_is_required(self):
        missing = (self.color + self.size).ids[-1] + 1000
        with self.assertRaises(psycopg2.errors.NotNullViolation):
            self.Value.create({'name': 'Orphan'})
        with self.assertRaises(psycopg2.errors.ForeignKeyViolation):
            self.Value.create({'name': 'Orphan', 'attribute_id': missing})
        with self.assertRaises(psycopg2.errors.NotNullViolation):
            self.color.value_ids[0].attribute_id = False
        self.assertEqual(self.names(self.color), ['Red', 'Blue'])
