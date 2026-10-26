import traceback
from unittest.mock import patch

import psycopg2.errors

from odoo import Command, models
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

    def test_unique_constraint_across_parents(self):
        """ A model's own unique(...) constraint spans the parents, like the
        PostgreSQL constraint on the table, and reads like its violation. """
        red = self.color.value_ids.sorted('id')[0]
        red.color = 1
        self.Value.create([{'attribute_id': self.size.id, 'name': 'Small'}] * 2)    # NULLs never collide
        self.env.flush_all()
        before = self.elements(self.size)
        with self.assertRaises(psycopg2.errors.UniqueViolation) as caught, self.env.cr.savepoint():
            self.Value.create({'attribute_id': self.size.id, 'name': 'Scarlet', 'color': 1})
        self.assertEqual(caught.exception.diag.constraint_name, 'product_attribute_value_color_uniq')
        self.assertIn('Key (color)=(1) already exists.', str(caught.exception))
        self.assertTrue(traceback.format_exception_only(caught.exception)[0].startswith('psycopg2.errors.UniqueViolation: '))
        self.assertEqual(self.elements(self.size), before)                      # the push was undone
        with self.assertRaises(psycopg2.errors.UniqueViolation), self.env.cr.savepoint():
            self.Value.create([
                {'attribute_id': self.size.id, 'name': 'Scarlet', 'color': 2},
                {'attribute_id': self.size.id, 'name': 'Crimson', 'color': 2},
            ])
        with self.assertRaises(psycopg2.errors.UniqueViolation), self.env.cr.savepoint():
            self.size.value_ids[0].color = 1
        self.assertEqual(self.elements(self.size), before)
        self.size.value_ids[0].color = 2                                        # free: no violation
        self.assertEqual(self.elements(self.size)[0]['color'], 2)

    def test_unique_key_within_parent(self):
        Position = self.env['test_orm_mongodb.fiscal_position']
        Mapping = self.env['test_orm_mongodb.fiscal_position_account']
        domestic, export = Position.create([
            {'name': 'Domestic', 'account_ids': [Command.create({'account_src_id': 1, 'account_dest_id': 2})]},
            {'name': 'Export', 'account_ids': [Command.create({'account_src_id': 1, 'account_dest_id': 2})]},
        ])
        Mapping.create([{'position_id': domestic.id, 'account_src_id': 1}] * 2)  # NULLs never collide
        self.env.flush_all()
        collection = storage_mongodb.get_collection(domestic)
        before = [collection.find_one({'_id': position.id})['account'] for position in (domestic, export)]
        with self.assertRaises(psycopg2.errors.UniqueViolation) as caught, self.env.cr.savepoint():
            Mapping.create({'position_id': domestic.id, 'account_src_id': 1, 'account_dest_id': 2})
        self.assertEqual(caught.exception.diag.message_detail,
                         f'Key (position_id, account_src_id, account_dest_id)=({domestic.id}, 1, 2) already exists.')
        self.assertEqual(caught.exception.diag.table_name, 'account_fiscal_position_account')
        # the model's constraint on the parent and the key names the error, with its message
        constraint = models.Constraint('unique (position_id,account_src_id,account_dest_id)', 'Defined only once per position.')
        with patch.object(type(Mapping), '_table_objects', {'account_fiscal_position_account_account_src_dest_uniq': constraint}):
            with self.assertRaises(psycopg2.errors.UniqueViolation) as caught, self.env.cr.savepoint():
                Mapping.create({'position_id': domestic.id, 'account_src_id': 1, 'account_dest_id': 2})
            self.assertEqual(caught.exception.diag.constraint_name, 'account_fiscal_position_account_account_src_dest_uniq')
            self.assertEqual(Mapping._sql_error_to_message(caught.exception), 'Defined only once per position.')
        with self.assertRaises(psycopg2.errors.UniqueViolation), self.env.cr.savepoint():
            export.account_ids.position_id = domestic
            self.env.flush_all()
        self.assertEqual([collection.find_one({'_id': position.id})['account'] for position in (domestic, export)], before)

    def test_merge_deletes_children_a_unique_key_keeps(self):
        # like the merge wizard's SQL: a child whose key exists on the target is deleted
        Position = self.env['test_orm_mongodb.fiscal_position']
        src, dst = Position.create([
            {'name': 'Src', 'account_ids': [Command.create({'account_src_id': 1, 'account_dest_id': 2})]},
            {'name': 'Dst', 'account_ids': [Command.create({'account_src_id': 1, 'account_dest_id': 2})]},
        ])
        kept = dst.account_ids
        self.env['base.partner.merge.automatic.wizard']._update_foreign_keys_generic(
            'test_orm_mongodb.fiscal_position', src, dst)
        self.assertFalse(src.account_ids)
        self.assertEqual(dst.account_ids, kept)
        self.assertEqual(len(storage_mongodb.get_collection(dst).find_one({'_id': dst.id})['account']), 1)
