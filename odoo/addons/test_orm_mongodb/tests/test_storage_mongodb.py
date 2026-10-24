import datetime as dt
import os
import unittest
from decimal import Decimal
from unittest.mock import patch

import psycopg2.errors
import pymongo.errors
from bson.decimal128 import Decimal128

from odoo import Command, models
from odoo.exceptions import UserError
from odoo.fields import Domain
from odoo.orm import storage_mongodb
from odoo.tests import TransactionCase, tagged
from odoo.tools import SQL, mute_logger, sql
from odoo.tools.translate import TranslationImporter


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
        self.assertEqual(storage_mongodb.get_collection(lock).name, f'{self.env.cr.dbname}__accountLockException')
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

    def test_partner_merge_repoints_documents(self):
        # the merge wizard rewrites foreign keys with raw SQL: the documents must follow
        Users = self.env['res.users'].with_context(no_reset_password=True)
        src, dst = Users.create([{'name': 'Src', 'login': 'merge_src'}, {'name': 'Dst', 'login': 'merge_dst'}])
        lock = self.Lock.create({'company_id': self.company.id, 'user_id': src.id})
        self.env['base.partner.merge.automatic.wizard']._update_foreign_keys_generic('res.users', src, dst)
        self.assertEqual(self.doc(lock)['userId'], dst.id)
        self.assertEqual(lock.user_id, dst)

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

    def test_in_falsy_value_matches_unset(self):
        category = self.Category.create({'name': 'Shelf'})
        unset = self.Capacity.create({'storage_category_id': category.id})
        zero = self.Capacity.create({'storage_category_id': category.id, 'quantity': 0})
        some = self.Capacity.create({'storage_category_id': category.id, 'quantity': 2.5})
        domain = [('storage_category_id', '=', category.id)]
        # like PostgreSQL, 0 also matches NULL, whose value reads as 0
        self.assertEqual(self.Capacity.search(domain + [('quantity', 'in', [0])], order='id'), unset + zero)
        self.assertEqual(self.Capacity.search(domain + [('quantity', 'not in', [0])], order='id'), some)
        self.assertEqual(self.Capacity.search(domain + [('quantity', 'in', [0, 2.5])], order='id'), unset + zero + some)

    def test_new_field_gets_default(self):
        # a module adding a field to existing documents fills in its default
        incoterm = self.Incoterm.create({'code': 'FCA', 'name': 'Free Carrier'})
        storage_mongodb.update(self.Incoterm, incoterm.ids, [{'active': None}])
        self.assertNotIn('active', self.doc(incoterm))
        self.assertEqual(storage_mongodb._new_fields(self.Incoterm), [])
        self.patch(storage_mongodb, '_new_fields', lambda model: [model._fields['active']])
        storage_mongodb.auto_init(self.Incoterm)
        self.assertIs(self.doc(incoterm)['active'], True)

    def test_shadow_column_of_unloaded_field_is_nullable(self):
        # a later module's required column must not block creates while it is not loaded
        cr = self.env.cr
        cr.execute("ALTER TABLE account_incoterms ADD COLUMN later_policy varchar NOT NULL DEFAULT 'x'")
        cr.execute("ALTER TABLE account_incoterms ALTER COLUMN later_policy DROP DEFAULT")
        storage_mongodb.auto_init(self.Incoterm)
        cr.execute(SQL(
            "SELECT attnotnull FROM pg_attribute WHERE attrelid = %s::regclass AND attname = %s",
            'account_incoterms', 'later_policy',
        ))
        self.assertIs(cr.fetchone()[0], False)
        incoterm = self.Incoterm.create({'code': 'CPT', 'name': 'Carriage Paid To'})
        self.env.flush_all()
        cr.execute("SELECT later_policy FROM account_incoterms WHERE id = %s", [incoterm.id])
        self.assertIsNone(cr.fetchone()[0])

    def test_group_by_decimal(self):
        categories = self.Category.create([
            {'name': 'Crate', 'max_weight': 2.5},
            {'name': 'Bin', 'max_weight': 2.5},
            {'name': 'Rack', 'max_weight': 7.25},
        ])
        groups = self.Category._read_group([('id', 'in', categories.ids)], ['max_weight'], ['__count'])
        self.assertEqual(groups, [(2.5, 2), (7.25, 1)])

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

    def test_layout_follows_model_setup(self):
        # a later module adds fields to the same _fields mapping: the layout must follow
        Category = self.env['test_orm_mongodb.category']
        self.registry._mongodb_layouts[Category._name] = (Category._fields, {'paths': {}})
        self.registry._setup_models__(self.env.cr, [Category._name])
        self.assertIn('name', storage_mongodb._layout(Category)['paths'])

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

    def test_search_flushes_only_fields_it_reads(self):
        Tag = self.env['test_orm_mongodb.tag']
        tag = Tag.create({'name': 'Flushed', 'sequence': 1})
        tag.flush_recordset()
        tag.sequence = 2
        # like PostgreSQL, a dirty field the search does not read stays dirty,
        # even with its cached value invalidated
        Tag._invalidate_cache(['sequence'])
        self.assertEqual(Tag.search([('name', '=', 'Flushed')], order='id'), tag)
        self.assertEqual(Tag.search_count([('id', '=', tag.id)]), 1)
        self.assertEqual(Tag._read_group([('id', '=', tag.id)], [], ['__count']), [(1,)])
        tag.sequence = 2
        self.assertEqual(Tag.search([('sequence', '=', 2)], order='id'), tag)
        tag.sequence = 3
        self.assertEqual(Tag._read_group([('id', '=', tag.id)], ['sequence'], ['__count']), [(3, 1)])

    def test_unlink_set_null_is_flushed(self):
        Template = self.env['test_orm_mongodb.template']
        Variant = self.env['test_orm_mongodb.variant']
        template = Template.create({'name': 'Gone'})
        variant = Variant.create({'product_tmpl_id': template.id, 'default_code': 'V'})
        field = Variant._fields['product_tmpl_id']
        self.patch(field, 'ondelete', 'set null')
        self.patch(field, 'required', False)
        template.unlink()
        self.env.flush_all()
        variant.invalidate_recordset()
        self.assertFalse(variant.product_tmpl_id)
        self.assertEqual(variant.default_code, 'V')

    def test_unlink_set_null_is_a_foreign_key_update(self):
        Template = self.env['test_orm_mongodb.template']
        Variant = self.env['test_orm_mongodb.variant']
        template = Template.create({'name': 'Gone'})
        variant = Variant.create({'product_tmpl_id': template.id, 'default_code': 'V'})
        field = Variant._fields['product_tmpl_id']
        self.patch(field, 'ondelete', 'set null')
        self.patch(field, 'required', False)
        # like PostgreSQL's foreign key, nulling the reference runs no write()
        # override, whose own writes the delete would drop from the cache
        self.patch(type(Variant), 'write', lambda records, vals: self.fail(f"write({vals}) called"))
        template.unlink()
        self.env.flush_all()
        variant.invalidate_recordset()
        self.assertFalse(variant.product_tmpl_id)
        self.assertEqual(variant.default_code, 'V')

    def test_cascade_from_shadow_column_removes_documents(self):
        other = self.env['res.company'].create({'name': 'Doomed'})
        lock = self.Lock.create({'company_id': other.id})
        other.unlink()
        self.assertIsNone(self.doc(lock))
        self.assertFalse(self.Lock.with_context(active_test=False).search([('id', '=', lock.id)]))

    def test_selection_records_are_read_from_documents(self):
        lock = self.Lock.create({'company_id': self.company.id, 'lock_date_field': 'tax_lock_date'})
        selection = self.env['ir.model.fields.selection'].search([
            ('field_id.model', '=', self.Lock._name), ('field_id.name', '=', 'lock_date_field'),
            ('value', '=', 'tax_lock_date'),
        ])
        self.assertEqual(selection._get_records(), lock)

    def test_selection_records_ignore_company_fallback(self):
        Category = self.env['test_orm_mongodb.category']
        explicit = Category.create({'name': 'Explicit', 'property_cost_method': 'average'})
        self.env['ir.default'].set(Category._name, 'property_cost_method', 'average', company_id=self.env.company.id)
        Category.create({'name': 'Fallback'})
        selection = self.env['ir.model.fields.selection'].search([
            ('field_id.model', '=', Category._name), ('field_id.name', '=', 'property_cost_method'),
            ('value', '=', 'average'),
        ])
        self.assertEqual(selection._get_records(), explicit)

    def test_selection_ondelete_bypasses_failing_write(self):
        lock = self.Lock.create({'company_id': self.company.id, 'lock_date_field': 'tax_lock_date'})
        selection = self.env['ir.model.fields.selection'].search([
            ('field_id.model', '=', self.Lock._name), ('field_id.name', '=', 'lock_date_field'),
            ('value', '=', 'tax_lock_date'),
        ])
        field = self.Lock._fields['lock_date_field']
        with patch.object(field, 'ondelete', {'tax_lock_date': 'set null'}), \
                patch.object(type(self.Lock), 'write', side_effect=UserError("write() refused")):
            selection._process_ondelete()
        lock.invalidate_recordset()
        self.assertFalse(lock.lock_date_field)

    def test_selection_ondelete_bypass_keeps_other_companies(self):
        Category = self.env['test_orm_mongodb.category']
        other = self.env['res.company'].create({'name': 'Other company'})
        category = Category.create({'name': 'Both', 'property_cost_method': 'average'})
        category.with_company(other).property_cost_method = 'standard'
        selection = self.env['ir.model.fields.selection'].search([
            ('field_id.model', '=', Category._name), ('field_id.name', '=', 'property_cost_method'),
            ('value', '=', 'average'),
        ])
        field = Category._fields['property_cost_method']
        # also mirrored in PostgreSQL, like a column a report reads
        self.env.cr.execute(f'ALTER TABLE "{Category._table}" ADD COLUMN property_cost_method jsonb')
        with patch.object(field, 'ondelete', {'average': 'set null'}), \
                patch.object(type(Category), '_shadow_columns', ('property_cost_method',)), \
                patch.object(type(Category), 'write', side_effect=UserError("write() refused")):
            selection._process_ondelete()
        category.invalidate_recordset()
        self.assertFalse(category.property_cost_method)
        self.assertEqual(category.with_company(other).property_cost_method, 'standard')
        self.env.cr.execute(f'SELECT property_cost_method FROM "{Category._table}" WHERE id = %s', [category.id])
        self.assertNotIn(str(self.env.company.id), self.env.cr.fetchone()[0] or {})

    def test_cascade_skips_unlink_overrides(self):
        template = self.env['test_orm_mongodb.template'].create({'name': 'Desk'})
        Variant = self.env['test_orm_mongodb.variant']
        variant = Variant.create({'product_tmpl_id': template.id})
        # like a PostgreSQL foreign key, the cascade runs no unlink() override
        with patch.object(type(Variant), 'unlink', side_effect=AssertionError("unlink() called")):
            template.unlink()
        self.assertIsNone(self.doc(variant))
        self.assertFalse(Variant.search([('id', '=', variant.id)]))

    def test_documents_without_shadow_row_are_ignored(self):
        lock = self.Lock.create({'company_id': self.company.id, 'reason': 'orphan'})
        self.env.flush_all()
        self.env.cr.execute("DELETE FROM account_lock_exception WHERE id = %s", [lock.id])
        live = self.Lock.create([{'company_id': self.company.id, 'reason': 'orphan'} for _ in range(2)])
        with mute_logger('odoo.orm.storage_mongodb'):
            self.assertEqual(self.Lock.search([('reason', '=', 'orphan')], order='id', limit=2), live)
            self.assertEqual(self.Lock.search([('reason', '=', 'orphan')], order='id', offset=1), live[1])

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
        self.assertEqual(search([('user_id', 'not in', [False])]), b)
        self.assertEqual(search([('reason', '<', 'Z')]), a | c, "unset Char compares as ''")
        self.assertEqual(search([('reason', '>', '')]), a | b)
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

    def test_custom_sql_domain(self):
        Tag = self.env['test_orm_mongodb.tag']
        tags = Tag.create([{'name': f'Custom {i}'} for i in range(4)])
        even = Domain.custom(to_sql=lambda table: SQL("%s %% 2 = 0", table.id))
        self.assertEqual(Tag.search(Domain('id', 'in', tags.ids) & even), tags.filtered(lambda t: t.id % 2 == 0))
        self.assertEqual(Tag.search(Domain('id', 'in', tags.ids) & ~even), tags.filtered(lambda t: t.id % 2))

    def test_like_on_html_translated_field(self):
        Template = self.env['test_orm_mongodb.template']
        template = Template.create({'name': 'Html', 'description': '<p>Name search</p>'})
        domain = [('id', '=', template.id)]
        self.assertEqual(Template.search(domain + [('description', 'ilike', 'n%a%m%e')]), template)
        self.assertFalse(Template.search(domain + [('description', 'ilike', 'missing')]))
        self.assertEqual(Template.search(domain + [('description', 'not ilike', 'missing')]), template)

    def test_html_translated_field_falls_back_to_english(self):
        self.env['res.lang']._activate_lang('fr_FR')
        Template = self.env['test_orm_mongodb.template']
        template = Template.create({'name': 'Html', 'description': '<p>English only</p>'})
        self.env.flush_all()
        template.invalidate_recordset()
        # like PostgreSQL, a missing translation reads as the English value
        self.assertEqual(
            template.with_context(lang='fr_FR').description,
            '<p>English only</p>',
        )

    def test_translation_import_updates_documents(self):
        self.env['res.lang']._activate_lang('fr_FR')
        Template = self.env['test_orm_mongodb.template']
        template = Template.create({'name': 'Chair', 'description': '<p>Chair</p>'})
        self.env['ir.model.data'].create({
            'module': 'test_orm_mongodb', 'name': 'template_chair',
            'model': Template._name, 'res_id': template.id,
        })
        xmlid = 'test_orm_mongodb.template_chair'
        importer = TranslationImporter(self.env.cr, verbose=False)
        importer.model_translations[Template._name]['name'][xmlid]['fr_FR'] = 'Chaise'
        importer.model_terms_translations[Template._name]['description'][xmlid]['Chair']['fr_FR'] = 'Chaise'
        importer.save()
        self.assertEqual(self.doc(template)['name'], {'en_US': 'Chair', 'fr_FR': 'Chaise'})
        template_fr = template.with_context(lang='fr_FR')
        self.assertEqual(template_fr.name, 'Chaise')
        self.assertEqual(template_fr.description, '<p>Chaise</p>')

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

    def test_unique_violation_like_postgresql(self):
        self.Expression.create({'report_line_id': 1, 'label': 'balance'})
        with self.assertRaises(psycopg2.errors.UniqueViolation) as caught, self.env.cr.savepoint():
            self.Expression.create({'report_line_id': 1, 'label': 'balance'})
        # the same table and constraint in PostgreSQL raise the error to match
        name = 'account_report_expression_report_line_id_label_key'
        self.env.cr.execute(SQL(
            "CREATE TEMPORARY TABLE unique_check (report_line_id int, label varchar, CONSTRAINT %s UNIQUE (report_line_id, label))",
            SQL.identifier(name)))
        with self.assertRaises(psycopg2.errors.UniqueViolation) as expected, self.env.cr.savepoint(), mute_logger('odoo.sql_db'):
            self.env.cr.execute("INSERT INTO unique_check VALUES (1, 'balance'), (1, 'balance')")
        error, pg_error = caught.exception, expected.exception
        self.assertEqual(str(error), str(pg_error))
        self.assertEqual(error.pgcode, pg_error.pgcode)
        for attr in ('sqlstate', 'message_primary', 'message_detail', 'constraint_name', 'column_name'):
            self.assertEqual(getattr(error.diag, attr), getattr(pg_error.diag, attr), attr)
        self.assertEqual(error.diag.table_name, 'account_report_expression')
        self.assertIn('Key (report_line_id, label)=(1, balance) already exists.', self.Expression._sql_error_to_message(error))
        # a unique constraint of the model names the error and orders its key
        constraint = models.Constraint('UNIQUE (label, report_line_id)')
        with patch.object(type(self.Expression), '_table_objects', {'account_report_expression_label_uniq': constraint}), \
                self.assertRaises(psycopg2.errors.UniqueViolation) as caught, self.env.cr.savepoint():
            self.Expression.create({'report_line_id': 1, 'label': 'balance'})
        self.assertEqual(caught.exception.diag.constraint_name, 'account_report_expression_label_uniq')
        self.assertEqual(caught.exception.diag.message_detail, 'Key (label, report_line_id)=(balance, 1) already exists.')

    def test_partial_unique_index(self):
        collection = storage_mongodb.get_collection(self.Expression)
        spec_indexes = storage_mongodb._layout(self.Expression)['indexes']
        partial = [
            dict(index, partialFilterExpression={'formula': 'posted'}) if index.get('unique') else index
            for index in spec_indexes
        ]
        # an index someone else made on the same keys is left alone
        collection.create_index([('reportLineId', 1), ('label', 1)], name='external')
        self.addCleanup(collection.drop_index, 'external')
        storage_mongodb._create_indexes(collection, partial)
        try:
            self.assertIn('external', collection.index_information())
            unique = [info for info in collection.index_information().values() if info.get('unique')]
            self.assertEqual(len(unique), 1, "the index of the previous filter is replaced")
            # the savepoint removes the documents before the spec index is restored
            with self.assertRaises(ZeroDivisionError), self.env.cr.savepoint():
                vals = {'report_line_id': 1, 'label': 'balance'}
                self.Expression.create([vals | {'formula': 'draft'}, vals | {'formula': 'draft'}, vals])
                self.Expression.create(vals | {'formula': 'posted'})
                # a missing key still never collides inside the filter
                self.Expression.create([{'report_line_id': 1, 'formula': 'posted'}] * 2)
                with self.assertRaises(psycopg2.errors.UniqueViolation), self.env.cr.savepoint():
                    self.Expression.create(vals | {'formula': 'posted'})
                # a filter the documents violate fails without dropping the current index
                with self.assertRaises(pymongo.errors.DuplicateKeyError):
                    storage_mongodb._create_indexes(collection, spec_indexes)
                self.assertEqual([info['partialFilterExpression'] for info in collection.index_information().values()
                                  if info.get('unique')], [{'$and': [{'reportLineId': {'$exists': True}, 'label': {'$exists': True}},
                                                                    {'formula': 'posted'}]}])
                1 / 0
        finally:
            storage_mongodb._create_indexes(collection, spec_indexes)
        restored = [info for info in collection.index_information().values() if info.get('unique')]
        self.assertEqual([info['partialFilterExpression'] for info in restored],
                         [{'reportLineId': {'$exists': True}, 'label': {'$exists': True}}])

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

    def test_test_cursor_rollback_undoes_documents(self):
        with self.registry_test_mode(), self.registry.cursor() as cr:
            env = self.env(cr=cr)
            lock = env['test_orm_mongodb.lock_exception'].create({'company_id': self.company.id})
            env.flush_all()
            self.assertIsNotNone(self.doc(lock))
            cr.rollback()
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
            self.env['test_orm_mongodb.tag']._read_group([], ['link_ids.name'], ['__count'])
        with self.assertRaises(NotImplementedError):
            self.Lock.search([], order='display_name')
