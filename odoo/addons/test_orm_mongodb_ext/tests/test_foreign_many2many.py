from odoo import Command
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'mongodb')
class TestForeignMany2many(TransactionCase):
    """A Many2many declared by another addon on an opted-in model is an id
    array on the document, whichever addon declares it."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.store = cls.env.registry.mongo_store
        cls.Item = cls.env['test_orm_mongodb.item']
        cls.Tag = cls.env['test_orm_mongodb.tag']
        cls.store.ensure_collection(cls.Item)  # recreate what another test class dropped
        cls.addClassCleanup(cls.store.db.drop_collection, cls.store.collection_name(cls.Item))

    def test_foreign_many2many_is_document_array(self):
        tag_x, tag_y = self.Tag.create([{'name': 'X'}, {'name': 'Y'}])
        item = self.Item.create({'name': 'Alpha', 'extra_tag_ids': [Command.set([tag_x.id])]})
        self.env.flush_all()
        doc = self.store.find(self.Item, {'_id': item.id})[0]
        self.assertEqual(doc['extraTagIds'], [{'tagId': tag_x.id}])
        self.env.cr.execute("SELECT to_regclass('test_orm_mongodb_item_extra_tag_rel')")
        self.assertIsNone(self.env.cr.fetchone()[0], "no PostgreSQL relation table")
        indexes = {ix['name'] for ix in self.store.db[self.store.collection_name(self.Item)].list_indexes()}
        self.assertIn('extraTagIds.tagId_1', indexes)
        # both sides read and search through the array
        self.assertEqual(tag_x.extra_item_ids, item)
        self.assertEqual(tag_y.extra_item_ids, self.Item)
        self.assertEqual(self.Item.search([('extra_tag_ids.name', '=', 'X')]), item)
        self.assertEqual(self.Tag.search([('extra_item_ids', 'in', item.ids)]), tag_x)
        tag_y.write({'extra_item_ids': [Command.link(item.id)]})
        self.env.invalidate_all()
        self.assertEqual(item.extra_tag_ids, tag_x | tag_y)
        self.assertEqual(item.tag_ids, self.Tag, "the addon's own relation is untouched")
