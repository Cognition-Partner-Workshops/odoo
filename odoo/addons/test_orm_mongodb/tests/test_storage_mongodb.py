import datetime as dt
import os
import unittest
from decimal import Decimal
from unittest.mock import patch

import psycopg2.errors
from bson.decimal128 import Decimal128

from odoo import Command
from odoo.orm import storage_mongodb
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger, sql


def setUpModule():
    host = storage_mongodb.get_database().client.address[0]
    if host not in ('localhost', '127.0.0.1'):
        raise unittest.SkipTest(f"MongoDB storage tests run against a local server only, not {host}")


@tagged('at_install', '-post_install')
class TestStorageMongodb(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Incoterm = cls.env['test_orm_mongodb.incoterm']
        cls.Lock = cls.env['test_orm_mongodb.lock_exception']
        cls.Category = cls.env['test_orm_mongodb.storage_category']
        cls.Capacity = cls.env['test_orm_mongodb.storage_capacity']
        cls.Expression = cls.env['test_orm_mongodb.report_expression']
        cls.company = cls.env.company

    def doc(self, record):
        return storage_mongodb.get_collection(record).find_one({'_id': record.id})

    # -- documents and shadow table ------------------------------------------

    def test_create_writes_spec_layout(self):
        lock = self.Lock.create({
            'company_id': self.company.id,
            'reason': 'audit',
            'lock_date': '2026-01-31',
            'end_datetime': dt.datetime(2026, 2, 1, 12, 30, 15, 123456),
        })
        doc = self.doc(lock)
        self.assertEqual(storage_mongodb.get_collection(lock).name,
                         os.environ.get('ODOO_MONGODB_COLLECTION_PREFIX', '') + 'accountLockException')
        self.assertEqual(doc['companyId'], self.company.id)
        self.assertEqual(doc['reason'], 'audit')
        self.assertEqual(doc['lockDate'], dt.datetime(2026, 1, 31))
        self.assertEqual(doc['endDatetime'], dt.datetime(2026, 2, 1, 12, 30, 15, 123000))
        self.assertIs(doc['active'], True)
        self.assertEqual(doc['createUid'], self.env.uid)
        self.assertNotIn('userId', doc, "NULL is stored as a missing key")
        self.assertNotIn('companyLockDate', doc)

        lock.invalidate_recordset()
        self.assertEqual(lock.lock_date, dt.date(2026, 1, 31))
        self.assertEqual(lock.reason, 'audit')
        self.assertFalse(lock.user_id)

    def test_decimal_and_double(self):
        category = self.Category.create({'name': 'Pallet', 'max_weight': 1250.125})
        capacity = self.Capacity.create({'storage_category_id': category.id, 'quantity': 2.5})
        self.assertIsInstance(self.doc(category)['maxWeight'], Decimal128)
        self.assertEqual(self.doc(category)['maxWeight'].to_decimal(), Decimal('1250.125'))
        self.assertEqual(self.doc(capacity)['quantity'], 2.5)
        self.env.invalidate_all()
        self.assertEqual(category.max_weight, 1250.125)
        self.assertEqual(capacity.quantity, 2.5)
        self.assertEqual(category.capacity_ids, capacity)

    def test_shadow_table(self):
        cr = self.env.cr
        self.assertEqual(set(sql.table_columns(cr, 'account_lock_exception')), {'id', 'company_id'})
        self.assertEqual(set(sql.table_columns(cr, 'account_incoterms')), {'id'})
        lock = self.Lock.create({'company_id': self.company.id})
        cr.execute("SELECT company_id FROM account_lock_exception WHERE id = %s", [lock.id])
        self.assertEqual(cr.fetchone()[0], self.company.id)

        other = self.env['res.company'].create({'name': 'Other'})
        lock.company_id = other
        lock.reason = 'moved'
        self.env.flush_all()
        cr.execute("SELECT company_id FROM account_lock_exception WHERE id = %s", [lock.id])
        self.assertEqual(cr.fetchone()[0], other.id)
        self.assertEqual(self.doc(lock)['companyId'], other.id)

    def test_write_and_unset(self):
        lock = self.Lock.create({'company_id': self.company.id, 'reason': 'a', 'user_id': self.env.uid})
        lock.write({'reason': 'b', 'user_id': False})
        self.env.flush_all()
        doc = self.doc(lock)
        self.assertEqual(doc['reason'], 'b')
        self.assertNotIn('userId', doc)
        self.assertEqual(doc['writeUid'], self.env.uid)

    def test_translations(self):
        self.env['res.lang']._activate_lang('fr_FR')
        incoterm = self.Incoterm.create({'code': 'EXW', 'name': 'Ex Works'})
        incoterm.with_context(lang='fr_FR').name = 'A l\'usine'
        self.env.flush_all()
        self.assertEqual(self.doc(incoterm)['name'], {'en_US': 'Ex Works', 'fr_FR': "A l'usine"})
        incoterm.invalidate_recordset()
        self.assertEqual(incoterm.name, 'Ex Works')
        self.assertEqual(incoterm.with_context(lang='fr_FR').name, "A l'usine")
        Incoterm_fr = self.Incoterm.with_context(lang='fr_FR')
        self.assertEqual(Incoterm_fr.search([('name', 'ilike', 'usine')]), incoterm)
        self.assertFalse(self.Incoterm.search([('name', 'ilike', 'usine')]))

    def test_unlink(self):
        category = self.Category.create({'name': 'Gone', 'capacity_ids': [Command.create({'quantity': 1})]})
        capacity = category.capacity_ids
        category.unlink()
        self.assertIsNone(self.doc(category))
        self.assertFalse(category.exists())
        self.assertFalse(capacity.exists(), "ondelete=cascade of a many2one stored in MongoDB")
        self.assertIsNone(self.doc(capacity))

    # -- domains and order ----------------------------------------------------

    def test_search_domains(self):
        other = self.env['res.company'].create({'name': 'Other Co'})
        a = self.Lock.create({'company_id': self.company.id, 'reason': 'Year end', 'lock_date': '2026-01-31'})
        b = self.Lock.create({'company_id': other.id, 'reason': 'tax 100%', 'lock_date': '2026-03-31',
                              'user_id': self.env.uid})
        c = self.Lock.create({'company_id': other.id, 'active': False})
        Lock = self.Lock.with_context(active_test=False)
        locks = a | b | c
        dom = [('id', 'in', locks.ids)]

        def search(domain, **kw):
            return Lock.search(dom + domain, **kw)

        self.assertEqual(self.Lock.search(dom), a | b, "active_test applies")
        self.assertEqual(search([('user_id', '=', False)]), a | c)
        self.assertEqual(search([('user_id', '!=', False)]), b)
        self.assertEqual(search([('reason', 'not in', ['tax 100%'])]), a | c, "NULL is not in any set")
        self.assertEqual(search([('active', '=', False)]), c)
        self.assertEqual(search([('lock_date', '>', '2026-02-01')]), b)
        self.assertEqual(search([('lock_date', '<=', '2026-03-31')]), a | b)
        self.assertEqual(search([('reason', 'ilike', 'YEAR')]), a)
        self.assertEqual(search([('reason', 'like', 'YEAR')]), Lock)
        self.assertEqual(search([('reason', 'not ilike', 'year')]), b | c, "not ilike matches NULL")
        self.assertEqual(search([('reason', '=like', 'tax 1_0%')]), b)
        self.assertEqual(search([('reason', '=ilike', 'tax 1_0')]), Lock, "_ matches one character")
        self.assertEqual(search([('company_id.name', '=', 'Other Co')]), b | c)
        self.assertEqual(search(['|', ('reason', '=', 'Year end'), ('active', '=', False)]), a | c)
        self.assertEqual(search(['!', ('company_id', '=', other.id)]), a)
        self.assertEqual(Lock.search_count(dom + [('company_id', '=', other.id)]), 2)

    def test_search_relations_between_mongodb_models(self):
        big = self.Category.create({'name': 'Big', 'capacity_ids': [Command.create({'quantity': 10})]})
        small = self.Category.create({'name': 'Small', 'capacity_ids': [Command.create({'quantity': 1})]})
        self.Category.create({'name': 'Empty'})
        cats = self.Category.search([('name', 'in', ['Big', 'Small', 'Empty'])])
        self.assertEqual(cats.filtered_domain([('capacity_ids.quantity', '>', 5)]), big)
        self.assertEqual(self.Category.search([('id', 'in', cats.ids), ('capacity_ids.quantity', '>', 5)]), big)
        self.assertEqual(self.Category.search([('id', 'in', cats.ids), ('capacity_ids', '=', False)]).name, 'Empty')
        self.assertEqual(self.Capacity.search([('storage_category_id.name', '=', 'Small')]), small.capacity_ids)

    def test_order_limit_offset(self):
        a = self.Lock.create({'company_id': self.company.id, 'reason': 'b', 'lock_date': '2026-01-01'})
        b = self.Lock.create({'company_id': self.company.id, 'reason': 'a'})
        c = self.Lock.create({'company_id': self.company.id, 'reason': 'c', 'lock_date': '2026-02-01'})
        dom = [('id', 'in', (a | b | c).ids)]
        self.assertEqual(self.Lock.search(dom, order='reason').ids, [b.id, a.id, c.id])
        self.assertEqual(self.Lock.search(dom, order='reason desc').ids, [c.id, a.id, b.id])
        # PostgreSQL puts NULLs last ascending and first descending
        self.assertEqual(self.Lock.search(dom, order='lock_date').ids, [a.id, c.id, b.id])
        self.assertEqual(self.Lock.search(dom, order='lock_date desc').ids, [b.id, c.id, a.id])
        self.assertEqual(self.Lock.search(dom, order='lock_date asc nulls first').ids, [b.id, a.id, c.id])
        self.assertEqual(self.Lock.search(dom, order='reason', limit=1, offset=1).ids, [a.id])

    def test_record_rules(self):
        self.Incoterm.create([{'code': 'FOB'}, {'code': 'HID'}])
        user = self.env['res.users'].create({'name': 'U', 'login': 'mongo_rule_user',
                                             'group_ids': [Command.link(self.env.ref('base.group_user').id)]})
        self.env.ref('test_orm_mongodb.access_test_orm_mongodb_incoterm').domain = "[('code', '!=', 'HID')]"
        codes = self.Incoterm.with_user(user).search([('code', 'in', ['FOB', 'HID'])]).mapped('code')
        self.assertEqual(codes, ['FOB'])

    # -- PostgreSQL models joining MongoDB models -----------------------------

    def test_postgresql_model_joins_through_shadow_table(self):
        incoterm = self.Incoterm.create({'code': 'CIF'})
        link = self.env['test_orm_mongodb.pg_link'].create({'name': 'l', 'incoterm_id': incoterm.id})
        Link = self.env['test_orm_mongodb.pg_link']
        self.assertEqual(Link.search([('incoterm_id.code', '=', 'CIF')]), link)
        self.assertEqual(link.incoterm_id.code, 'CIF')
        incoterm.unlink()
        self.assertFalse(link.exists(), "ondelete=cascade runs through the shadow table")

    # -- indexes ----------------------------------------------------------------

    def test_indexes_from_spec(self):
        info = storage_mongodb.get_collection(self.Expression).index_information()
        keys = {tuple(map(tuple, index['key'])): index for index in info.values()}
        unique = keys[('reportLineId', 1), ('label', 1)]
        self.assertTrue(unique['unique'])
        self.assertIn((('engine', 1), ('formula', 1), ('_id', 1)), keys)
        self.assertIn((('code', 1),), {tuple(map(tuple, i['key'])) for i in
                                        storage_mongodb.get_collection(self.Incoterm).index_information().values()})

    def test_unique_index(self):
        self.Expression.create({'report_line_id': 1, 'label': 'balance'})
        # missing keys do not collide, like NULLs in a PostgreSQL unique constraint
        self.Expression.create([{'report_line_id': 1}, {'report_line_id': 1}])
        with self.assertRaises(psycopg2.errors.UniqueViolation), self.env.cr.savepoint():
            self.Expression.create({'report_line_id': 1, 'label': 'balance'})

    # -- transactions -------------------------------------------------------------

    def test_savepoint_rollback_undoes_documents(self):
        lock = self.Lock.create({'company_id': self.company.id, 'reason': 'kept'})
        self.env.flush_all()
        with self.assertRaises(ZeroDivisionError), self.env.cr.savepoint():
            created = self.Lock.create({'company_id': self.company.id, 'reason': 'undone'})
            lock.reason = 'changed'
            self.env.flush_all()
            self.assertEqual(self.doc(lock)['reason'], 'changed')
            1 / 0
        self.assertIsNone(self.doc(created))
        self.assertEqual(self.doc(lock)['reason'], 'kept')

        with self.assertRaises(ZeroDivisionError), self.env.cr.savepoint():
            lock.unlink()
            self.assertIsNone(self.doc(lock))
            1 / 0
        self.assertEqual(self.doc(lock)['reason'], 'kept')

    def test_test_cursor_commit_keeps_undo_on_real_cursor(self):
        mark = self.env.cr._undo_mark()
        with self.registry_test_mode(), self.registry.cursor() as cr:
            env = self.env(cr=cr)
            lock = env['test_orm_mongodb.lock_exception'].create({'company_id': self.company.id})
        self.assertIsNotNone(self.doc(lock))
        self.assertGreater(self.env.cr._undo_mark(), mark, "committing a test cursor only releases its savepoint")
        self.env.cr._undo_to(mark)
        self.assertIsNone(self.doc(lock))

    # -- fail closed ------------------------------------------------------------

    def test_other_database_fails_closed(self):
        with patch.dict(os.environ, {'ODOO_MONGODB_DATABASE': 'odoo_prod'}):
            with self.assertRaises(storage_mongodb.StorageError):
                storage_mongodb.get_database()
            with self.assertRaises(storage_mongodb.StorageError), self.env.cr.savepoint():
                self.Lock.create({'company_id': self.company.id})

    def test_spec_is_pinned(self):
        storage_mongodb._spec_tables.cache_clear()
        self.addCleanup(storage_mongodb._spec_tables.cache_clear)
        with patch.object(storage_mongodb, 'SPEC_SHA256', '0' * 64), self.assertRaises(storage_mongodb.StorageError):
            storage_mongodb._spec_tables()

    def test_unmapped_column_fails_closed(self):
        layouts = self.registry.__dict__['_mongodb_layouts']
        self.addCleanup(layouts.update, dict(layouts))
        layouts.pop(self.Incoterm._name)
        with patch.object(type(self.Incoterm), '_table', 'account_lock_exception'):
            with self.assertRaisesRegex(storage_mongodb.StorageError, "'code' is not in the signed mapping"):
                storage_mongodb._layout(self.Incoterm)

    @mute_logger('odoo.sql_db')
    def test_unsupported_operations_fail_closed(self):
        with self.assertRaises(NotImplementedError):
            self.Lock._read_group([], ['company_id'], ['__count'])
        with self.assertRaises(NotImplementedError):
            self.Lock.search([], order='display_name')
