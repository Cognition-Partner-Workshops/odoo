import json
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
        cls.Attribute = cls.env['test_orm_mongodb.report']
        cls.Value = cls.env['test_orm_mongodb.report_column']
        cls.color, cls.size = cls.Attribute.create([
            {'name': 'Color', 'column_ids': [
                Command.create({'name': 'Red', 'sequence': 2, 'expression_label': '#f00'}),
                Command.create({'name': 'Blue', 'sequence': 1, 'expression_label': '#00f'}),
            ]},
            {'name': 'Size', 'column_ids': [Command.create({'name': 'Large', 'sequence': 1})]},
        ])

    def elements(self, attribute):
        self.env.flush_all()
        doc = storage_mongodb.get_collection(attribute).find_one({'_id': attribute.id})
        return doc.get('column', [])

    def names(self, attribute):
        return [element['name']['en_US'] for element in self.elements(attribute)]

    def test_embedded_documents(self):
        red, blue = self.color.column_ids.sorted('id')
        self.assertEqual(self.names(self.color), ['Red', 'Blue'])
        element = self.elements(self.color)[0]
        self.assertEqual(element['id'], red.id)
        self.assertEqual(element['expressionLabel'], '#f00')
        self.assertNotIn('reportId', element)
        self.assertNotIn('_id', element)
        self.env.cr.execute("SELECT id FROM account_report_column WHERE id IN %s", [tuple((red + blue).ids)])
        self.assertEqual(len(self.env.cr.fetchall()), 2)

        self.env.invalidate_all()
        self.assertEqual(self.color.column_ids, blue + red)      # ordered by sequence
        self.assertEqual(red.report_id, self.color)
        self.assertEqual((red.name, red.sequence, red.expression_label), ('Red', 2, '#f00'))

    def test_embedded_writes(self):
        red, blue = self.color.column_ids.sorted('id')
        large = self.size.column_ids

        red.write({'expression_label': '#e00', 'figure_type': 'percentage'})
        self.assertEqual(self.names(self.color), ['Red', 'Blue'])   # updated in place
        self.assertEqual(self.elements(self.color)[0]['expressionLabel'], '#e00')
        blue.expression_label = False
        self.assertNotIn('expressionLabel', self.elements(self.color)[1])

        red.report_id = self.size
        self.assertEqual(self.names(self.color), ['Blue'])
        self.assertEqual(self.names(self.size), ['Large', 'Red'])
        self.env.invalidate_all()
        self.assertEqual(self.size.column_ids, large + red)
        self.assertEqual(red.figure_type, 'percentage')

        blue.unlink()
        self.assertEqual(self.elements(self.color), [])
        self.size.unlink()
        self.assertFalse((red + large).exists())
        self.env.cr.execute("SELECT id FROM account_report_column WHERE id IN %s", [tuple((red + large).ids)])
        self.assertFalse(self.env.cr.fetchall())

    def test_embedded_search(self):
        red, blue = self.color.column_ids.sorted('id')
        large = self.size.column_ids
        values = red + blue + large
        self.assertEqual(self.Value.search([('id', 'in', values.ids), ('name', 'ilike', 'r')]), red + large)
        self.assertEqual(self.Value.search([('report_id', '=', self.color.id)]), blue + red)
        self.assertEqual(self.Value.search([('id', 'in', values.ids), ('expression_label', '=', False)]), large)
        self.assertEqual(self.Value.search([('id', 'in', values.ids)], order='sequence desc, id desc'),
                         red + large + blue)
        self.assertEqual(self.Value.search([('id', 'in', values.ids)], order='id', limit=1, offset=1), blue)
        self.assertEqual(self.Value.search_count([('report_id.name', '=', 'Size')]), 1)
        self.assertEqual(self.Attribute.search([('column_ids.expression_label', '=', '#00f')]), self.color)
        self.assertEqual(self.Attribute.search([('id', 'in', (self.color + self.size).ids),
                                                ('column_ids', '=', False)]), self.Attribute)

    def test_savepoint_rollback_restores_elements(self):
        red, blue = self.color.column_ids.sorted('id')
        before = (self.elements(self.color), self.elements(self.size))
        with self.assertRaises(ZeroDivisionError), self.env.cr.savepoint():
            red.expression_label = '#000'
            blue.report_id = self.size
            self.Value.create({'report_id': self.color.id, 'name': 'Green'})
            self.size.column_ids.filtered(lambda value: value.name == 'Large').unlink()
            1 / 0
        self.assertEqual((self.elements(self.color), self.elements(self.size)), before)

    def test_parent_is_required(self):
        missing = (self.color + self.size).ids[-1] + 1000
        with self.assertRaises(psycopg2.errors.NotNullViolation):
            self.Value.create({'name': 'Orphan'})
        with self.assertRaises(psycopg2.errors.ForeignKeyViolation):
            self.Value.create({'name': 'Orphan', 'report_id': missing})
        with self.assertRaises(psycopg2.errors.NotNullViolation):
            self.color.column_ids[0].report_id = False
        self.assertEqual(self.names(self.color), ['Red', 'Blue'])

    def test_unique_constraint_across_parents(self):
        """ A model's own unique(...) constraint spans the parents, like the
        PostgreSQL constraint on the table, and reads like its violation. """
        red = self.color.column_ids.sorted('id')[0]
        red.custom_audit_action_id = 1
        self.Value.create([{'report_id': self.size.id, 'name': 'Small'}] * 2)    # NULLs never collide
        self.env.flush_all()
        before = self.elements(self.size)
        with self.assertRaises(psycopg2.errors.UniqueViolation) as caught, self.env.cr.savepoint():
            self.Value.create({'report_id': self.size.id, 'name': 'Scarlet', 'custom_audit_action_id': 1})
        self.assertEqual(caught.exception.diag.constraint_name, 'account_report_column_audit_uniq')
        self.assertIn('Key (custom_audit_action_id)=(1) already exists.', str(caught.exception))
        self.assertTrue(traceback.format_exception_only(caught.exception)[0].startswith('psycopg2.errors.UniqueViolation: '))
        self.assertEqual(self.elements(self.size), before)                      # the push was undone
        with self.assertRaises(psycopg2.errors.UniqueViolation), self.env.cr.savepoint():
            self.Value.create([
                {'report_id': self.size.id, 'name': 'Scarlet', 'custom_audit_action_id': 2},
                {'report_id': self.size.id, 'name': 'Crimson', 'custom_audit_action_id': 2},
            ])
        with self.assertRaises(psycopg2.errors.UniqueViolation), self.env.cr.savepoint():
            self.size.column_ids[0].custom_audit_action_id = 1
        self.assertEqual(self.elements(self.size), before)
        self.size.column_ids[0].custom_audit_action_id = 2                                        # free: no violation
        self.assertEqual(self.elements(self.size)[0]['customAuditActionId'], 2)

    def test_unique_constraint_locks_across_parents(self):
        """ Writers of one unique key under different parents share no parent
        row: the key is locked until the transaction ends, so a concurrent
        writer waits for the commit or rollback instead of racing the check. """
        lock = f'account_report_column.account_report_column_audit_uniq:{json.dumps({"customAuditActionId": 7})}'
        with self.registry.cursor() as other:
            def other_can_lock():
                other.execute("SELECT pg_try_advisory_xact_lock(hashtext(%s))", [lock])
                taken, = other.fetchone()
                other.rollback()                            # a transaction lock ends with its transaction
                return taken

            self.assertTrue(other_can_lock())
            with self.env.cr.savepoint():
                self.Value.create({'report_id': self.size.id, 'name': 'Seven', 'custom_audit_action_id': 7})
                self.env.flush_all()
                self.assertFalse(other_can_lock())          # held by this transaction
            self.assertFalse(other_can_lock())              # until it ends, not the savepoint

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


@tagged('at_install', '-post_install')
class TestSubdocumentMongodb(TransactionCase):
    """ A ``subdocument`` embed (map-draft-2: properties_base_definition in
    irModelFields) stores its one child as an object, not an array. The
    report columns stand in for it, their embed reshaped to a subdocument. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Report = cls.env['test_orm_mongodb.report']
        cls.Column = cls.env['test_orm_mongodb.report_column']

    def setUp(self):
        super().setUp()
        children = dict(storage_mongodb._spec_children())
        coll, embed = children['account_report_column']
        children['account_report_column'] = (coll, dict(embed, shape='subdocument'))
        self.patch(storage_mongodb, '_spec_children', lambda: children)
        layouts = self.registry.__dict__.setdefault('_mongodb_layouts', {})
        layouts.pop(self.Column._name, None)
        self.addCleanup(layouts.pop, self.Column._name, None)
        self.assertTrue(storage_mongodb._layout(self.Column)['embed']['subdocument'])
        self.first, self.second = self.Report.create([{'name': 'First'}, {'name': 'Second'}])

    def subdoc(self, report):
        self.env.flush_all()
        return storage_mongodb.get_collection(report).find_one({'_id': report.id}).get('column')

    def test_subdocument_round_trip(self):
        column = self.Column.create({'report_id': self.first.id, 'name': 'Balance', 'expression_label': 'balance'})
        doc = self.subdoc(self.first)
        self.assertIsInstance(doc, dict)
        self.assertEqual((doc['id'], doc['expressionLabel']), (column.id, 'balance'))
        self.assertNotIn('reportId', doc)
        self.env.invalidate_all()
        self.assertEqual(self.first.column_ids, column)
        self.assertEqual((column.name, column.expression_label, column.report_id), ('Balance', 'balance', self.first))
        self.assertEqual(self.Column.search([('expression_label', '=', 'balance')]), column)
        self.assertEqual(self.Report.search([('column_ids.expression_label', '=', 'balance')]), self.first)

        column.expression_label = 'debit'
        self.assertEqual(self.subdoc(self.first)['expressionLabel'], 'debit')
        column.expression_label = False
        self.assertNotIn('expressionLabel', self.subdoc(self.first), "NULL is stored as a missing key")
        column.report_id = self.second
        self.assertIsNone(self.subdoc(self.first))
        self.assertEqual(self.subdoc(self.second)['id'], column.id)
        column.unlink()
        self.assertIsNone(self.subdoc(self.second))

    def test_subdocument_takes_one_child(self):
        column = self.Column.create({'report_id': self.first.id, 'name': 'Balance'})
        before = self.subdoc(self.first)
        with self.assertRaises(psycopg2.errors.UniqueViolation), self.env.cr.savepoint():
            self.Column.create({'report_id': self.first.id, 'name': 'Second one'})
        with self.assertRaises(psycopg2.errors.UniqueViolation), self.env.cr.savepoint():
            self.Column.create([{'report_id': self.second.id, 'name': 'A'}, {'report_id': self.second.id, 'name': 'B'}])
        other = self.Column.create({'report_id': self.second.id, 'name': 'Other'})
        with self.assertRaises(psycopg2.errors.UniqueViolation), self.env.cr.savepoint():
            other.report_id = self.first
            self.env.flush_all()
        self.assertEqual(self.subdoc(self.first), before)
        self.assertEqual(self.subdoc(self.second)['id'], other.id)
        self.env.invalidate_all()
        self.assertEqual(self.first.column_ids, column)

    def test_subdocument_savepoint_rollback(self):
        column = self.Column.create({'report_id': self.first.id, 'name': 'Balance', 'expression_label': 'balance'})
        before = (self.subdoc(self.first), self.subdoc(self.second))
        with self.assertRaises(ZeroDivisionError), self.env.cr.savepoint():
            column.expression_label = 'debit'
            column.report_id = self.second
            self.env.flush_all()    # the first report is vacant once the move is written
            self.Column.create({'report_id': self.first.id, 'name': 'New'})
            self.env.flush_all()
            1 / 0
        self.assertEqual((self.subdoc(self.first), self.subdoc(self.second)), before)
        with self.assertRaises(ZeroDivisionError), self.env.cr.savepoint():
            column.unlink()
            1 / 0
        self.assertEqual(self.subdoc(self.first), before[0])
