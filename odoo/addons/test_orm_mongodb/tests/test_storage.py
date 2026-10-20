from datetime import date
from unittest.mock import PropertyMock, patch

from odoo import Command
from odoo.exceptions import UserError, ValidationError
from odoo.orm.query import MongoQuery, Query
from odoo.orm.storage_mongodb import MongoStore
from odoo.tests import TransactionCase, tagged
from odoo.tools import SQL, config


@tagged('post_install', '-at_install', 'mongodb')
class TestMongoStorage(TransactionCase):
    """CRUD, search, read_group and cross-store relations of models with
    ``_storage = 'mongodb'`` against the Atlas database ``odoo_migration``.

    Every test runs inside the test savepoint: the MongoDB undo log replays
    the writes when the savepoint rolls back, so the collections end up
    empty again; they are dropped at the end of the class.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.store = cls.env.registry.mongo_store
        cls.Item = cls.env['test_orm_mongodb.item']
        cls.Line = cls.env['test_orm_mongodb.line']
        cls.Category = cls.env['test_orm_mongodb.category']
        cls.Tag = cls.env['test_orm_mongodb.tag']
        cls.Node = cls.env['test_orm_mongodb.node']
        cls.Variant = cls.env['test_orm_mongodb.variant']
        cls.Card = cls.env['test_orm_mongodb.card']
        cls.mongo_models = [cls.Item, cls.Line, cls.Node, cls.Variant, cls.Card]
        for model in cls.mongo_models:  # recreate what another test class dropped
            cls.store.ensure_collection(model)
        cls.addClassCleanup(cls._drop_collections)

    @classmethod
    def _drop_collections(cls):
        for model in cls.mongo_models:
            cls.store.db.drop_collection(cls.store.collection_name(model))

    def _docs(self, model, filter_=None):
        return self.store.find(model, filter_ or {}, sort=[('_id', 1)])

    def _make(self):
        cat_a, cat_b = self.Category.create([{'name': 'A'}, {'name': 'B'}])
        tag_x, tag_y = self.Tag.create([{'name': 'X'}, {'name': 'Y'}])
        items = self.Item.create([
            {'name': 'Alpha', 'code': 'A1', 'quantity': 5, 'price': 2.5, 'date': '2026-01-15',
             'category_id': cat_a.id, 'tag_ids': [Command.set([tag_x.id, tag_y.id])],
             'line_ids': [Command.create({'label': 'l1', 'amount': 10.0}), Command.create({'label': 'l2', 'amount': 5.0})]},
            {'name': 'Beta', 'code': 'B1', 'quantity': 0, 'price': 7.0, 'date': '2026-02-10',
             'category_id': cat_a.id, 'tag_ids': [Command.set([tag_x.id])], 'state': 'done'},
            {'name': 'Gamma', 'quantity': 12, 'price': 1.0, 'date': '2026-02-20',
             'category_id': cat_b.id, 'active': False},
        ])
        return cat_a, cat_b, tag_x, tag_y, items

    def _column_state(self, table, column):
        self.env.cr.execute(
            "SELECT is_nullable, column_default FROM information_schema.columns "
            "WHERE table_name = %s AND column_name = %s", (table, column))
        return self.env.cr.fetchone()

    def test_create_on_pre_existing_shadow_table(self):
        # an existing database keeps the moved columns until cutover: _auto_init relaxes them
        table = self.Item._table
        self.env.cr.execute(SQL(
            "ALTER TABLE %s ADD COLUMN legacy_name varchar NOT NULL DEFAULT 'moved', "
            "ADD COLUMN quantity int4 NOT NULL DEFAULT 1", SQL.identifier(table)))
        with patch.object(type(self.Item), '_shadow_columns', ('quantity',)):
            self.store.ensure_shadow_table(self.Item)
        self.assertEqual(self._column_state(table, 'legacy_name'), ('YES', None))
        self.assertEqual(self._column_state(table, 'quantity'), ('NO', '1'))
        self.assertEqual(self._column_state(table, 'id')[0], 'NO')
        self.env.cr.execute(SQL("ALTER TABLE %s DROP COLUMN quantity", SQL.identifier(table)))
        item = self.Item.create({'name': 'Shadow'})
        self.env.cr.execute(SQL("SELECT id, legacy_name FROM %s WHERE id = %s", SQL.identifier(table), item.id))
        self.assertEqual(self.env.cr.fetchone(), (item.id, None))
        self.assertEqual(self._docs(self.Item, {'_id': item.id})[0]['name'], 'Shadow')

    def test_shadow_columns_write_through(self):
        # full-shadow columns (contract §4) are created on the shadow table and written
        # through on create/write in the same transaction; unlink drops the row
        table = self.Item._table
        legacy = self.Item.create({'name': 'Legacy', 'code': 'L0', 'price': 1.5})  # id-only shadow row
        with patch.object(type(self.Item), '_shadow_columns', ('code', 'price')):
            self.store.ensure_shadow_table(self.Item)
            self.assertEqual(self._column_state(table, 'price'), ('YES', None))
            # the new columns are backfilled from the documents
            self.assertEqual(self._shadow_rows(table, legacy), [(legacy.id, 'L0', 1.5)])
            item, other = self.Item.create([{'name': 'Shadow', 'code': 'S1', 'price': 2.5}, {'name': 'Plain'}])
            self.env.flush_all()
            self.assertEqual(self._shadow_rows(table, item + other), [(item.id, 'S1', 2.5), (other.id, None, None)])
            item.write({'code': False, 'price': 4.0, 'quantity': 7})
            self.env.flush_all()
            self.assertEqual(self._shadow_rows(table, item), [(item.id, None, 4.0)])
            self.assertEqual(self._docs(self.Item, {'_id': item.id})[0]['price'], 4.0)
            item.unlink()
            self.assertEqual(self._shadow_rows(table, item), [])
            self.assertEqual(self._docs(self.Item, {'_id': item.id}), [])

    def _shadow_rows(self, table, records):
        self.env.cr.execute(SQL(
            "SELECT id, code, price FROM %s WHERE id IN %s ORDER BY id", SQL.identifier(table), tuple(records.ids),
        ))
        return self.env.cr.fetchall()

    def test_sql_join_reads_shadow_table(self):
        # a PostgreSQL model joined to a MongoDB comodel through SQL reads the
        # shadow table: ``id`` and ``_shadow_columns`` only (contract §4); the
        # comodel's record rules resolve to an id list (two-step, contract §3)
        with patch.object(type(self.Item), '_shadow_columns', ('price',)):
            self.store.ensure_shadow_table(self.Item)  # creates the shadow column
            cat_a, cat_b, _tag_x, _tag_y, (alpha, beta, _gamma) = self._make()
            cat_a.default_item_id = alpha
            cat_b.default_item_id = beta

            def select_prices(Category):
                query = Category._search([('id', 'in', (cat_a | cat_b).ids)], order='id')
                return Category.env.execute_query(query.select(query.table.id, query.table.default_item_id.price))

            self.assertEqual(select_prices(self.Category), [(cat_a.id, 2.5), (cat_b.id, 7.0)])
            alpha.price = 3.5  # written through to the shadow column at flush
            self.assertEqual(select_prices(self.Category), [(cat_a.id, 3.5), (cat_b.id, 7.0)])
            query = Query(self.Category)
            with self.assertRaises(NotImplementedError):
                query.table.default_item_id.name
            # a record rule (restriction) on the comodel applies to non-superusers
            as_admin = self.Category.with_user(self.env.ref('base.user_admin'))
            self.assertEqual(select_prices(as_admin), [(cat_a.id, 3.5), (cat_b.id, 7.0)])
            self.env['ir.access'].create({
                'name': 'cheap items only', 'operation': 'crud', 'domain': "[('price', '<', 5)]",
                'model_id': self.env['ir.model']._get_id('test_orm_mongodb.item'),
            })
            self.assertEqual(select_prices(as_admin), [(cat_a.id, 3.5), (cat_b.id, None)])

    def test_sql_join_delegated_field_through_parent_shadow(self):
        # an ``_inherits``-delegated field read through SQL (sale.report's
        # ``product_id.uom_id``: product.product -> product_tmpl_id -> product_template.uom_id)
        # has no column on the variant; it resolves through the parent join when the
        # delegate field and the parent column are shadow columns (contract §4)
        with patch.object(type(self.Variant), '_shadow_columns', ('item_id',)), \
             patch.object(type(self.Item), '_shadow_columns', ('name',)):
            self.store.ensure_shadow_table(self.Item)
            with patch.object(self.env.registry, '_post_init_queue', [], create=True):
                self.store.ensure_shadow_table(self.Variant)  # queues the item_id foreign key
            cat_a, cat_b, _tag_x, _tag_y, (alpha, beta, _gamma) = self._make()
            var_a, var_b = self.Variant.create([
                {'item_id': alpha.id, 'ref': 'VA'}, {'item_id': beta.id, 'ref': 'VB'},
            ])
            cat_a.default_variant_id = var_a
            cat_b.default_variant_id = var_b
            self.env.flush_all()

            def select_names(Category):
                query = Category._search([('id', 'in', (cat_a | cat_b).ids)], order='id')
                return Category.env.execute_query(query.select(query.table.id, query.table.default_variant_id.name))

            self.assertEqual(select_names(self.Category), [(cat_a.id, 'Alpha'), (cat_b.id, 'Beta')])
            var_a.name = 'Alpha prime'  # delegated write, shadowed on the parent at flush
            self.assertEqual(select_names(self.Category), [(cat_a.id, 'Alpha prime'), (cat_b.id, 'Beta')])
            query = Query(self.Category)
            with self.assertRaises(NotImplementedError):
                query.table.default_variant_id.ref  # own column, not shadowed
            with self.assertRaises(NotImplementedError):
                query.table.default_variant_id.code  # delegated, parent column not shadowed
        with patch.object(type(self.Variant), '_shadow_columns', ()):
            with self.assertRaises(NotImplementedError):
                Query(self.Category).table.default_variant_id.name  # delegate field not shadowed

    def test_registry_opt_in(self):
        self.assertEqual(self.Item._storage, 'mongodb')
        self.assertEqual(self.Category._storage, 'postgresql')
        self.assertIn('test_orm_mongodb.item', self.env.registry.mongodb_models)
        self.assertNotIn('test_orm_mongodb.category', self.env.registry.mongodb_models)
        self.assertEqual(self.store.database_name, 'odoo_migration')
        # a test database is not the migration database: its collections carry the
        # per-database prefix, so the migrated collections are never touched
        self.assertEqual(self.store.collection_prefix, f'{self.env.cr.dbname}__')
        self.assertEqual(self.store.collection_name(self.Item), f'{self.env.cr.dbname}__testOrmMongodbItem')
        with patch.dict(config.options, {'mongodb_migration_db': self.env.cr.dbname}):
            self.assertEqual(self.store.collection_prefix, '')
            self.assertEqual(self.store.collection_name(self.Item), 'testOrmMongodbItem')
        # a database with committed ids whose documents sit in the unprefixed
        # collection is the migration database started without the key: fail closed
        name, prefixed = 'testOrmMongodbItem', self.store.collection_name(self.Item)
        fake_db = {n: type('Coll', (), {'estimated_document_count': lambda self, c=c: c})() for n, c in ((name, 1), (prefixed, 0))}
        self.store._namespace_checked.discard(name)
        with self.assertRaisesRegex(RuntimeError, 'set mongodb_migration_db'), \
             patch.object(MongoStore, '_has_committed_rows', return_value=True), \
             patch.object(MongoStore, 'db', new_callable=PropertyMock, return_value=fake_db):
            self.store.collection_name(self.Item)
        self.assertNotIn(name, self.store._namespace_checked)
        self.assertEqual(self.store.collection_name(self.Item), prefixed)
        self.assertNotIn(name, self.store._namespace_checked, "no committed ids yet: nothing to cache")
        fake_db[prefixed] = fake_db[name]
        with patch.object(MongoStore, '_has_committed_rows', return_value=True), \
             patch.object(MongoStore, 'db', new_callable=PropertyMock, return_value=fake_db):
            self.assertEqual(self.store.collection_name(self.Item), prefixed)
        self.assertIn(name, self.store._namespace_checked, "documents in the prefixed namespace: established")
        # the shadow table exists with ids only
        self.env.cr.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'test_orm_mongodb_item'")
        self.assertEqual([row[0] for row in self.env.cr.fetchall()], ['id'])
        indexes = {ix['name']: ix for ix in self.store.db[self.store.collection_name(self.Item)].list_indexes()}
        self.assertIn('tagIds.tagId_1', indexes, "multikey index for the reverse read of the many2many")
        unique = [ix for ix in indexes.values() if ix.get('unique') and 'code' in ix['key']]
        self.assertEqual(unique[0]['partialFilterExpression'], {'code': {'$type': 'string'}})

    def test_crud(self):
        _cat_a, _cat_b, tag_x, tag_y, items = self._make()
        alpha = items[0]
        self.assertIsInstance(alpha.id, int)
        self.env.flush_all()
        docs = self._docs(self.Item, {'_id': alpha.id})
        self.assertEqual(len(docs), 1)
        doc = docs[0]
        self.assertEqual(doc['name'], 'Alpha')
        self.assertEqual(doc['quantity'], 5)
        self.assertEqual(doc['categoryId'], alpha.category_id.id)
        self.assertEqual(doc['tagIds'], [{'tagId': tag_x.id}, {'tagId': tag_y.id}])
        self.assertEqual(doc['total'], 15.0)
        self.env.cr.execute("SELECT id FROM test_orm_mongodb_item ORDER BY id")
        self.assertEqual([row[0] for row in self.env.cr.fetchall()], items.ids)

        # read back through the ORM (cache invalidated)
        self.env.invalidate_all()
        self.assertEqual(alpha.name, 'Alpha')
        self.assertEqual(alpha.date, date(2026, 1, 15))
        self.assertEqual(alpha.price, 2.5)
        self.assertEqual(alpha.state, 'draft')
        self.assertEqual(alpha.line_ids.mapped('amount'), [10.0, 5.0])
        self.assertEqual(alpha.tag_ids, tag_x | tag_y)

        # write: $set / $unset, many2many $pull, computed stored field
        alpha.write({'quantity': 7, 'code': False, 'tag_ids': [Command.unlink(tag_x.id)]})
        alpha.line_ids[0].amount = 1.0
        self.env.flush_all()
        doc = self._docs(self.Item, {'_id': alpha.id})[0]
        self.assertEqual(doc['quantity'], 7)
        self.assertNotIn('code', doc)
        self.assertEqual(doc['tagIds'], [{'tagId': tag_y.id}])
        self.assertEqual(doc['total'], 6.0)
        self.env.invalidate_all()
        self.assertEqual(alpha.total, 6.0)

        # unlink: shadow row first (FK cascade on the lines' shadow rows is
        # not declared, the ORM cascades), then the document
        line_ids = alpha.line_ids.ids
        alpha.unlink()
        self.assertFalse(self._docs(self.Item, {'_id': alpha.id}))
        self.assertFalse(self._docs(self.Line, {'_id': {'$in': line_ids}}))
        self.env.cr.execute("SELECT count(*) FROM test_orm_mongodb_item WHERE id = %s", [alpha.id])
        self.assertEqual(self.env.cr.fetchone()[0], 0)
        self.assertFalse(alpha.exists())
        self.assertTrue(items[1].exists())

    def test_constraints(self):
        with self.assertRaises(ValidationError):
            self.Item.create({'name': 'Neg', 'quantity': -1})
        self.Item.create({'name': 'One', 'code': 'DUP'})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.Item.create({'name': 'Two', 'code': 'DUP'})
        # nullable unique key: several documents without a code are fine
        self.Item.create([{'name': 'N1'}, {'name': 'N2'}])

    def test_search(self):
        cat_a, _cat_b, _tag_x, _tag_y, items = self._make()
        alpha, beta, gamma = items
        self.assertIsInstance(self.Item._search([]), MongoQuery)
        self.assertEqual(self.Item.search([]), alpha | beta)  # active_test
        self.assertEqual(self.Item.with_context(active_test=False).search([], order='id'), items)
        self.assertEqual(self.Item.search([('name', 'ilike', 'alp')]), alpha)
        self.assertEqual(self.Item.search([('name', '=like', 'B%')]), beta)
        self.assertEqual(self.Item.search([('name', 'like', 'Al%')]), alpha)
        self.assertEqual(self.Item.search([('name', 'ilike', 'a_pha')]), alpha)
        self.assertEqual(self.Item.search([('name', 'like', 'lp')]), alpha)
        self.assertEqual(self.Item.search([('name', 'not ilike', 'alp')]), beta)
        self.assertEqual(self.Item.search([('quantity', '>', 0)]), alpha)
        self.assertEqual(self.Item.search([('quantity', '>=', 0), ('state', '=', 'done')]), beta)
        self.assertEqual(self.Item.search([('code', 'in', ['A1', False])]), alpha)
        self.assertEqual(self.Item.search([('code', '!=', False), ('code', 'not in', ['A1'])]), beta)
        self.assertEqual(self.Item.search([('date', '>=', '2026-02-01')]), beta)
        self.assertEqual(self.Item.search(['|', ('name', '=', 'Alpha'), ('name', '=', 'Beta')], order='name desc'), beta | alpha)
        self.assertEqual(self.Item.search([], order='price desc', limit=1), beta)
        self.assertEqual(self.Item.search([], order='price desc', offset=1), alpha)
        self.assertEqual(self.Item.search_count([('price', '<', 5)]), 1)
        self.assertEqual(self.Item.search([('id', 'in', [alpha.id, gamma.id])]), alpha)
        self.assertEqual(self.Item.search([('category_id', '=', cat_a.id)], order='id'), alpha | beta)
        self.assertEqual(self.Item.search([('category_id', '=', False)]), self.Item)
        self.assertEqual(self.Item.search([('line_ids.amount', '>', 6)]), alpha)
        self.assertEqual(self.Item.search([('line_ids', '=', False)]), beta)
        self.assertEqual(self.Item.search([('date.month_number', '=', 2), ('active', 'in', [True, False])]), beta | gamma)
        with self.assertRaises(NotImplementedError):
            self.Item._table_sql  # noqa: B018

    def test_float_digits_stored_as_numbers(self):
        # Float(digits) and Monetary pass their rounded value to the column as a
        # float_repr() string: the document holds the double, like the numeric column
        eur = self.env.ref('base.EUR')
        d1, d2, d3 = items = self.Item.create([
            {'name': 'D1', 'discount': 2, 'currency_id': eur.id, 'cost': 1.005},
            {'name': 'D2', 'discount': 2.345, 'currency_id': eur.id, 'cost': 10},
            {'name': 'D3', 'discount': 10, 'currency_id': eur.id, 'cost': 0},
        ])
        self.env.flush_all()
        docs = {doc['_id']: doc for doc in self._docs(self.Item, {'_id': {'$in': items.ids}})}
        self.assertEqual([docs[item.id]['discount'] for item in items], [2.0, 2.35, 10.0])
        self.assertEqual([type(docs[item.id]['discount']) for item in items], [float, float, float])
        self.assertEqual([docs[item.id]['cost'] for item in items], [1.01, 10.0, 0.0])
        self.assertEqual([type(docs[item.id]['cost']) for item in items], [float, float, float])
        self.assertEqual(self.Item.search([('discount', '<=', 2)]), d1)
        self.assertEqual(self.Item.search([('discount', '>', 2)], order='id'), d2 | d3)
        self.assertEqual(self.Item.search([('discount', '=', 2.345)]), d2)  # rounded like the column
        self.assertEqual(self.Item.search([('discount', '=', 2.35)]), d2)
        self.assertEqual(self.Item.search([('cost', '>=', 10)]), d2)
        self.assertEqual(self.Item.search([('cost', '=', 1.01)]), d1)

        d3.write({'discount': 3.14159, 'cost': 2.5})
        self.env.flush_all()
        doc = self._docs(self.Item, {'_id': d3.id})[0]
        self.assertEqual((doc['discount'], doc['cost']), (3.14, 2.5))
        self.assertEqual(self.Item.search([('discount', '=', 3.14)]), d3)
        self.assertEqual(self.Item.search([('discount', '>', 3), ('cost', '<', 3)]), d3)
        self.env.invalidate_all()
        self.assertEqual((d3.discount, d3.cost), (3.14, 2.5))

    def test_read_group(self):
        cat_a, cat_b, _tag_x, _tag_y, items = self._make()
        groups = self.Item.with_context(active_test=False)._read_group(
            [], ['category_id'], ['quantity:sum', 'price:avg', '__count', 'price:max', 'id:recordset'],
        )
        self.assertEqual(groups, [
            (cat_a, 5, 4.75, 2, 7.0, items[0] | items[1]),
            (cat_b, 12, 1.0, 1, 1.0, items[2]),
        ])
        groups = self.Item.with_context(active_test=False)._read_group(
            [], ['date:month'], ['quantity:sum'], order='date:month desc',
        )
        self.assertEqual(groups, [(date(2026, 2, 1), 12), (date(2026, 1, 1), 5)])
        groups = self.Item.with_context(active_test=False)._read_group(
            [], ['state'], ['__count'], having=[('__count', '>', 1)],
        )
        self.assertEqual(groups, [('draft', 2)])
        self.assertEqual(self.Item._read_group([], [], ['quantity:sum']), [(5,)])
        self.assertEqual(self.Item._read_group([('name', '=', 'nope')], [], ['__count', 'quantity:sum']), [(0, 0)])
        self.assertEqual(self.Item._read_group([('name', '=', 'nope')], [], ['__count'], offset=1), [])
        self.assertEqual(self.Item.read_group([], ['category_id'], ['quantity:sum'])[0][1], 5)
        self.assertEqual(self.Item.search([('category_id.name', '=', 'B')]), self.Item)

    def test_cross_store_relations(self):
        cat_a, cat_b, tag_x, tag_y, items = self._make()
        alpha, beta, gamma = items
        # Many2one MongoDB -> PostgreSQL: two-step domain and browse
        self.assertEqual(alpha.category_id, cat_a)
        self.assertEqual(self.Item.search([('category_id.name', '=', 'A')], order='id'), alpha | beta)
        self.assertEqual(self.Item.search([('category_id', 'not any', [('name', '=', 'A')])]), self.Item)
        # One2many PostgreSQL -> MongoDB: read and search
        self.assertEqual(cat_a.item_ids, alpha | beta)
        self.assertEqual(cat_a.item_count, 2)
        self.assertEqual(self.Category.search([('item_ids.price', '>', 5)]), cat_a)
        self.assertEqual(self.Category.with_context(active_test=False).search([('item_ids', 'any', [('name', '=', 'Gamma')])]), cat_b)
        self.assertEqual(self.Category.search([('item_ids', 'any', [('name', '=', 'Gamma')])]), self.Category)
        self.assertEqual(self.Category.search([('item_ids.name', '=', 'Nope')]), self.Category)
        # Many2many both ways (array on the MongoDB document)
        self.assertEqual(tag_x.item_ids, alpha | beta)
        self.assertEqual(tag_y.item_ids, alpha)
        self.assertEqual(self.Item.search([('tag_ids.name', '=', 'Y')]), alpha)
        self.assertEqual(self.Item.search([('tag_ids', 'not in', tag_y.ids)]), beta)
        self.assertEqual(self.Tag.search([('item_ids.name', '=', 'Beta')]), tag_x)
        tag_y.write({'item_ids': [Command.link(beta.id)]})
        self.assertEqual(beta.tag_ids, tag_x | tag_y)
        self.assertEqual(self._docs(self.Item, {'_id': beta.id})[0]['tagIds'], [{'tagId': tag_x.id}, {'tagId': tag_y.id}])
        self.env.cr.execute("SELECT to_regclass('test_orm_mongodb_item_tag_rel')")
        self.assertIsNone(self.env.cr.fetchone()[0], "no PostgreSQL relation table for an array relation")
        # Many2one PostgreSQL -> MongoDB: FK to the shadow table, ON DELETE SET NULL
        cat_b.default_item_id = gamma
        gamma.unlink()
        cat_b.invalidate_recordset()
        self.assertFalse(cat_b.default_item_id)
        # One2many MongoDB -> MongoDB
        self.assertEqual(self.Line.search([('item_id.name', '=', 'Alpha')]), alpha.line_ids)
        # deleting a PostgreSQL record referenced from MongoDB documents: ondelete 'set null'
        cat_a.unlink()
        self.env.invalidate_all()
        self.assertFalse(alpha.category_id)
        self.assertNotIn('categoryId', self._docs(self.Item, {'_id': alpha.id})[0])

    def test_parent_store(self):
        root = self.Node.create({'name': 'root'})
        a, c = self.Node.create([{'name': 'a', 'parent_id': root.id}, {'name': 'c', 'parent_id': root.id}])
        b = self.Node.create({'name': 'b', 'parent_id': a.id})
        self.env.flush_all()
        self.assertEqual(root.parent_path, f"{root.id}/")
        self.assertEqual(b.parent_path, f"{root.id}/{a.id}/{b.id}/")
        self.assertEqual(self._docs(self.Node, {'_id': b.id})[0]['parentPath'], b.parent_path)
        indexes = {ix['name'] for ix in self.store.db[self.store.collection_name(self.Node)].list_indexes()}
        self.assertIn('parentPath_1', indexes)

        # child_of / parent_of resolve through parent_path
        self.assertEqual(self.Node.search([('id', 'child_of', a.id)]), a | b)
        self.assertEqual(self.Node.search([('id', 'child_of', root.id)]), root | a | c | b)
        self.assertEqual(self.Node.search([('id', 'parent_of', b.id)]), root | a | b)
        self.assertEqual(self.Node.search([('parent_id', 'child_of', root.id)]), root | a | c | b)  # same-model hierarchy field: root included, as in SQL

        # moving a subtree rewrites the prefix of every descendant
        a.parent_id = c
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertEqual(a.parent_path, f"{root.id}/{c.id}/{a.id}/")
        self.assertEqual(b.parent_path, f"{root.id}/{c.id}/{a.id}/{b.id}/")
        self.assertEqual(self._docs(self.Node, {'_id': b.id})[0]['parentPath'], b.parent_path)
        self.assertEqual(self.Node.search([('id', 'child_of', c.id)]), c | a | b)
        # an ancestor and its descendant moved under the same parent in one write
        (a | b).write({'parent_id': root.id})
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertEqual(a.parent_path, f"{root.id}/{a.id}/")
        self.assertEqual(b.parent_path, f"{root.id}/{b.id}/")
        self.assertEqual(self.Node.search([('id', 'child_of', a.id)]), a)
        b.parent_id = a
        a.parent_id = False
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertEqual(b.parent_path, f"{a.id}/{b.id}/")
        self.assertEqual(self.Node.search([('id', 'child_of', root.id)]), root | c)

        # recursion check
        with self.assertRaises(UserError), self.cr.savepoint():
            a.parent_id = b
        self.assertFalse((root | a | b | c)._has_cycle())
        self.assertEqual(b.parent_path, f"{a.id}/{b.id}/")

        # recompute from scratch
        self.store.db[self.store.collection_name(self.Node)].update_many({}, {'$unset': {'parentPath': ''}})
        self.Node._parent_store_compute()
        self.assertEqual(b.parent_path, f"{a.id}/{b.id}/")
        self.assertEqual(c.parent_path, f"{root.id}/{c.id}/")

        # ondelete cascade through the MongoDB referrers
        a.unlink()
        self.assertFalse(b.exists())

    def test_rollback_replays_undo_log(self):
        before = self.store.count(self.Item, {})
        item = self.Item.create({'name': 'Temp', 'code': 'T1'})
        self.env.flush_all()
        self.assertEqual(self.store.count(self.Item, {'_id': item.id}), 1)
        with self.cr.savepoint() as sp:
            item.write({'name': 'Changed'})
            created = self.Item.create({'name': 'Inner'})
            self.env.flush_all()
            self.assertEqual(self._docs(self.Item, {'_id': item.id})[0]['name'], 'Changed')
            sp.rollback()
        self.env.invalidate_all()
        self.assertEqual(self._docs(self.Item, {'_id': item.id})[0]['name'], 'Temp')
        self.assertEqual(self.store.count(self.Item, {'_id': created.id}), 0)
        self.assertEqual(self.store.count(self.Item, {}), before + 1)
        self.assertEqual(self.store.repair(self.Item), {'documents_removed': 0, 'shadow_rows_removed': 0})


@tagged('post_install', '-at_install')
class TestStoragePath(TestMongoStorage):
    """Storage-path rules found by the first opted-in business models (wave 2)."""

    def test_order_through_inherits_mongodb_parent(self):
        *_, items = self._make()
        alpha, beta, _gamma = items
        v_beta, v_alpha = self.Variant.create([{'item_id': beta.id}, {'item_id': alpha.id}])
        term = self.Variant._order_to_sort('name')[0]
        self.assertEqual((term[0], term[1], term[4]), ('itemId', 1, self.store.collection_name(self.Item)))
        self.assertEqual(self.Variant.search([]), v_alpha + v_beta)
        self.assertEqual(self.Variant.search([], order='name desc'), v_beta + v_alpha)
        self.assertTrue(self.Variant.fields_get(['name'])['name']['sortable'])

    def test_order_through_inherits_postgresql_parent(self):
        c_b, c_a = self.Card.create([{'name': 'B'}, {'name': 'A'}])
        term = self.Card._order_to_sort('name')[0]
        self.assertIsInstance(term[0], dict, "a PostgreSQL parent is ranked by its ids, not joined")
        self.assertEqual(self.Card.search([]), c_a + c_b)
        self.assertEqual(self.Card.search([], order='name desc'), c_b + c_a)
        c_b.name = 'AA'
        self.assertEqual(self.Card.search([]), c_b + c_a, "pending parent writes are flushed before the sort")

    def test_order_many2one_follows_comodel_order(self):
        _a, cat_b, _x, _y, items = self._make()
        alpha, beta, gamma = items
        alpha.category_id = cat_b
        self.assertEqual(self.Item.with_context(active_test=False).search([], order='category_id, id'), beta + alpha + gamma)
        self.assertEqual(self.Item.with_context(active_test=False).search([], order='category_id desc, id'), alpha + gamma + beta)
        # only the references of the matching documents are ranked in PostgreSQL
        with patch.object(MongoStore, 'distinct', autospec=True, side_effect=MongoStore.distinct) as distinct:
            self.assertEqual(self.Item.with_context(active_test=False).search([('id', '=', gamma.id)], order='category_id, id'), gamma)
        filter_ = distinct.call_args.args[3]
        self.assertEqual(filter_.get('_id'), {'$in': [gamma.id]}, filter_)
        line_a, line_b = alpha.line_ids
        line_g = self.Line.create({'item_id': gamma.id, 'label': 'g'})
        gamma.sequence = 1
        self.assertEqual(self.Line.search([], order='item_id, id'), line_g + line_a + line_b)

    def test_search_flushes_pending_writes(self):
        *_, items = self._make()
        beta = items[1]
        beta.name = 'Zulu'
        self.assertEqual(self.Item.search([('name', '=', 'Zulu')]), beta)
        beta.sequence = 1
        self.assertEqual(self.Item.search([], order='sequence, id')[0], beta)

    def test_many2one_condition_on_mongodb_comodel(self):
        cat_a, cat_b, _x, _y, items = self._make()
        cat_a.default_item_id = items[0]
        cat_b.default_item_id = items[1]
        self.assertEqual(self.Category.search([('default_item_id.name', '=', 'Beta')]), cat_b)
        self.assertEqual(self.Category.search([('default_item_id.name', '=', 'Nope')]), self.Category)

    def test_description_probes_tolerate_mongodb(self):
        with patch.object(MongoStore, 'distinct', side_effect=AssertionError("a probe queries no store")), \
                patch.object(MongoStore, 'find', side_effect=AssertionError("a probe queries no store")):
            description = self.Item.fields_get()
        self.assertFalse(description['line_ids']['sortable'])
        self.assertTrue(description['total']['sortable'])
        self.assertTrue(description['category_id']['sortable'])

    def test_attachment_access_two_steps_ids(self):
        *_, items = self._make()
        alpha, beta, _gamma = items
        user = self.env['res.users'].create({'name': 'w2', 'login': 'w2', 'group_ids': [Command.link(self.env.ref('base.group_user').id)]})
        Attachment = self.env['ir.attachment']
        att_alpha, att_beta, att_ghost = Attachment.create([
            {'name': 'a', 'res_model': self.Item._name, 'res_id': alpha.id, 'raw': b'a'},
            {'name': 'b', 'res_model': self.Item._name, 'res_id': beta.id, 'raw': b'b'},
            {'name': 'g', 'res_model': self.Item._name, 'res_id': alpha.id + 100000, 'raw': b'g'},
        ])
        domain = [('res_model', '=', self.Item._name), ('res_id', 'in', [alpha.id, beta.id, att_ghost.res_id])]
        found = Attachment.with_user(user).search(domain)
        self.assertEqual(found, att_alpha + att_beta, "the id restriction of the two-step keeps out the dangling res_id")
        found = Attachment.with_user(user).search(domain[:1] + [('res_id', '=', beta.id)])
        self.assertEqual(found, att_beta)

    def test_unique_index_without_message(self):
        *_, items = self._make()
        self.Variant.create({'item_id': items[0].id, 'ref': 'R1'})
        with self.assertRaises(ValidationError) as cm, self.cr.savepoint():
            self.Variant.create({'item_id': items[1].id, 'ref': 'R1'})
        self.assertIn('already exists', str(cm.exception))
        self.assertIn('ref', str(cm.exception))

    def test_many2many_array_ondelete(self):
        _a, _b, tag_x, tag_y, items = self._make()
        alpha = items[0]
        field = self.Item._fields['tag_ids']
        layout = (self.Item._name, 'tagIds', 'tagId')
        original = MongoStore.m2m_layout
        self.env.flush_all()
        coll = self.store.db[self.store.collection_name(self.Item)]
        coll.update_one({'_id': alpha.id}, {'$set': {'tagIds': [{'tagId': tag_x.id}, {'tagId': tag_y.id}]}})
        with patch.object(MongoStore, 'm2m_layout', lambda store, model, f: layout if f is field else original(store, model, f)):
            with patch.object(field, 'ondelete', 'restrict'), self.assertRaises(UserError), self.cr.savepoint():
                tag_x.unlink()
            tag_y.unlink()
            self.env.flush_all()
        self.assertEqual(coll.find_one({'_id': alpha.id})['tagIds'], [{'tagId': tag_x.id}])
