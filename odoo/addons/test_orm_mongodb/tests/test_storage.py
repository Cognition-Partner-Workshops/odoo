from datetime import date
from unittest.mock import patch

from odoo import Command
from odoo.exceptions import UserError, ValidationError
from odoo.orm.query import MongoQuery
from odoo.tests import TransactionCase, tagged
from odoo.tools import SQL


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
        cls.mongo_models = [cls.Item, cls.Line, cls.Node]
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

    def test_registry_opt_in(self):
        self.assertEqual(self.Item._storage, 'mongodb')
        self.assertEqual(self.Category._storage, 'postgresql')
        self.assertIn('test_orm_mongodb.item', self.env.registry.mongodb_models)
        self.assertNotIn('test_orm_mongodb.category', self.env.registry.mongodb_models)
        self.assertEqual(self.store.database_name, 'odoo_migration')
        self.assertEqual(self.store.collection_name(self.Item), 'testOrmMongodbItem')
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
