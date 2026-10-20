# Part of Odoo. See LICENSE file for full copyright and licensing details.
import datetime

import psycopg2

from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger, sql


@tagged('post_install', '-at_install', 'mongodb')
class TestMongoStorage(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.store = cls.env.registry.mongo_store
        cls.env['res.lang']._activate_lang('fr_FR')
        cls.partner_a = cls.env['res.partner'].create({'name': 'Alice'})
        cls.partner_b = cls.env['res.partner'].create({'name': 'Bob'})
        cls.tag_x, cls.tag_y = cls.env['test.mongo.tag'].create([{'name': 'x'}, {'name': 'y'}])
        cls.author_a, cls.author_b = cls.env['test.mongo.author'].create([
            {'name': 'Ann', 'rating': 4.5, 'score': 1.25, 'partner_id': cls.partner_b.id,
             'birthday': '1980-01-02', 'title': 'Doctor', 'tag_ids': [(6, 0, [cls.tag_x.id])]},
            {'name': 'Ben', 'rating': 3.0, 'partner_id': cls.partner_a.id, 'state': 'done'},
        ])
        cls.book_a1, cls.book_a2, cls.book_b1 = cls.env['test.mongo.book'].create([
            {'name': 'Zebra', 'author_id': cls.author_a.id, 'price': 10.5, 'pages': 100,
             'published': '2024-03-05 10:00:00', 'tag_ids': [(6, 0, [cls.tag_y.id])],
             'chapter_ids': [(0, 0, {'name': 'One', 'sequence': 2}), (0, 0, {'name': 'Two', 'sequence': 1})]},
            {'name': 'Apple', 'author_id': cls.author_a.id, 'price': 20, 'pages': 50, 'published': '2024-04-05 10:00:00'},
            {'name': 'Mango', 'author_id': cls.author_b.id, 'price': 5, 'pages': 300},
        ])
        cls.env.flush_all()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # the test transaction rolled back, the journal undid the documents; remove the test collections
        for model in ('test.mongo.tag', 'test.mongo.author', 'test.mongo.book', 'test.mongo.variant'):
            cls.store.db.drop_collection(cls.store.model_collection(cls.env[model]).name)
        for collection in ('testMongoBookTagRel', 'testMongoReviewPartnerRel'):
            cls.store.db.drop_collection(cls.store.collection(collection).name)

    def doc(self, record):
        return self.store.model_collection(record).find_one({'_id': record.id})

    def test_collection_naming_and_shadow(self):
        coll = self.store.model_collection(self.author_a)
        self.assertEqual(coll.name, f"{self.env.cr.dbname}__testMongoAuthor")
        self.assertEqual(coll.database.name, 'odoo_unt12')
        doc = self.doc(self.author_a)
        self.assertEqual(doc['name'], 'Ann')
        self.assertEqual(str(doc['rating']), '4.50')          # spec decimal -> Decimal128
        self.assertIsInstance(doc['score'], float)             # spec double
        self.assertEqual(doc['partnerId'], self.partner_b.id)
        self.assertEqual(doc['birthday'], datetime.datetime(1980, 1, 2))
        self.assertEqual(doc['title'], {'en_US': 'Doctor'})
        self.assertEqual(doc['tagRel'], [{'tagId': self.tag_x.id}])
        self.env.cr.execute("SELECT id FROM test_mongo_author ORDER BY id")
        self.assertEqual([r[0] for r in self.env.cr.fetchall()], sorted((self.author_a + self.author_b).ids))
        self.env.cr.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'test_mongo_author'")
        self.assertEqual([r[0] for r in self.env.cr.fetchall()], ['id'])
        self.assertEqual(self.env['test.mongo.author'].browse([self.author_a.id, 99999]).exists(), self.author_a)
        indexes = self.store.model_collection(self.author_a).index_information()
        self.assertIn('partnerId_1', indexes)
        self.assertIn('rating_-1__id_1', indexes)

    def test_read_write(self):
        author = self.author_a
        author.invalidate_recordset()
        self.assertEqual(author.name, 'Ann')
        self.assertEqual(author.rating, 4.5)
        self.assertEqual(author.birthday, datetime.date(1980, 1, 2))
        self.assertEqual(author.partner_id, self.partner_b)
        self.assertEqual(author.tag_ids, self.tag_x)
        self.assertEqual(author.book_ids, self.book_a2 + self.book_a1)
        self.assertEqual(author.book_count, 2)
        author.write({'rating': 2.345, 'birthday': False, 'name': 'Anna'})
        author.flush_recordset()
        doc = self.doc(author)
        self.assertEqual(str(doc['rating']), '2.35')
        self.assertIsNone(doc['birthday'])
        self.assertEqual(doc['name'], 'Anna')
        self.assertEqual(doc['writeUid'], self.env.uid)
        author.invalidate_recordset()
        self.assertEqual(author.rating, 2.35)
        self.assertFalse(author.birthday)

    def test_search_domains(self):
        Author = self.env['test.mongo.author']
        self.assertEqual(Author.search([('name', '=', 'Ann')]), self.author_a)
        self.assertEqual(Author.search([('name', 'ilike', 'an')]), self.author_a)
        self.assertEqual(Author.search([('name', '=like', 'B%')]), self.author_b)
        self.assertEqual(Author.search([('name', 'not ilike', 'ann')]), self.author_b)
        self.assertEqual(Author.search([('rating', '>', 4)]), self.author_a)
        self.assertEqual(Author.search([('rating', '<=', 3)]), self.author_b)
        self.assertEqual(Author.search([('birthday', '=', False)]), self.author_b)
        self.assertEqual(Author.search([('birthday', '!=', False)]), self.author_a)
        self.assertEqual(Author.search([('score', '=', 0)]), self.author_b)     # falsy value matches null
        self.assertEqual(Author.search([('state', 'in', ['done'])]), self.author_b)
        self.assertEqual(Author.search([('state', 'not in', ['done'])]), self.author_a)
        self.assertEqual(Author.search(['|', ('name', '=', 'Ann'), ('name', '=', 'Ben')]), self.author_a + self.author_b)
        self.assertEqual(Author.search(['!', ('name', '=', 'Ann')]), self.author_b)
        self.assertEqual(Author.search([('id', 'in', [self.author_b.id])]), self.author_b)
        self.assertEqual(Author.search_count([]), 2)
        self.assertEqual(Author.search_count([('rating', '>', 0)], limit=1), 1)
        self.author_b.active = False
        self.author_b.flush_recordset()
        self.assertEqual(Author.search([]), self.author_a)
        self.assertEqual(Author.with_context(active_test=False).search([]), self.author_a + self.author_b)
        self.assertEqual(Author.search([('active', '=', False)]), self.author_b)

    def test_order_limit_offset(self):
        Author = self.env['test.mongo.author']
        self.assertEqual(Author.search([]), self.author_a + self.author_b)          # rating desc
        self.assertEqual(Author.search([], order='rating asc'), self.author_b + self.author_a)
        self.assertEqual(Author.search([], order='rating asc', limit=1), self.author_b)
        self.assertEqual(Author.search([], order='rating asc', offset=1), self.author_a)
        # many2one into PostgreSQL ordered by the comodel's own order (partner name: Alice < Bob)
        self.assertEqual(Author.search([], order='partner_id'), self.author_b + self.author_a)
        self.assertEqual(Author.search([], order='partner_id desc'), self.author_a + self.author_b)
        self.assertEqual(Author.search([], order='state'), self.author_a + self.author_b)
        # nulls last on ascending, first on descending (PostgreSQL defaults)
        self.assertEqual(Author.search([], order='birthday asc'), self.author_a + self.author_b)
        self.assertEqual(Author.search([], order='birthday desc'), self.author_b + self.author_a)
        # many2one into MongoDB: books by author (rating desc) then name
        self.assertEqual(self.env['test.mongo.book'].search([]), self.book_a2 + self.book_a1 + self.book_b1)

    def test_cross_store_many2one(self):
        Author = self.env['test.mongo.author']
        Book = self.env['test.mongo.book']
        self.assertEqual(Author.search([('partner_id.name', '=', 'Alice')]), self.author_b)
        self.assertEqual(Author.search([('partner_id', 'in', self.partner_b.ids)]), self.author_a)
        self.assertEqual(Author.search([('partner_id', 'not in', self.partner_b.ids)]), self.author_b)
        self.assertEqual(Book.search([('author_id.partner_id.name', '=', 'Bob')]), self.book_a2 + self.book_a1)
        self.assertEqual(Book.search([('author_id.name', '=', 'Ben')]), self.book_b1)
        # PostgreSQL model filtering and ordering through a MongoDB comodel
        Review = self.env['test.mongo.review']
        reviews = Review.create([
            {'name': 'r1', 'book_id': self.book_b1.id, 'author_id': self.author_b.id},
            {'name': 'r2', 'book_id': self.book_a1.id, 'author_id': self.author_a.id},
        ])
        self.assertEqual(Review.search([('book_id.name', '=', 'Mango')]), reviews[0])
        self.assertEqual(Review.search([('book_id.author_id.partner_id', '=', self.partner_b.id)]), reviews[1])
        self.assertEqual(Review.search([]), reviews[1] + reviews[0])        # book order: Zebra (Ann) before Mango (Ben)
        self.assertEqual(Review.search([], order='book_id desc'), reviews[0] + reviews[1])
        self.assertEqual(reviews.mapped('book_id.name'), ['Mango', 'Zebra'])
        self.assertEqual(self.book_a1.review_ids, reviews[1])
        self.assertEqual(Book.search([('review_ids.name', '=', 'r2')]), self.book_a1)
        self.assertEqual(Book.search([('review_ids', '=', False)]), self.book_a2)
        self.env.cr.execute("SELECT book_id FROM test_mongo_review ORDER BY id")
        self.assertEqual([r[0] for r in self.env.cr.fetchall()], [self.book_b1.id, self.book_a1.id])
        # the PostgreSQL foreign key onto the shadow still cascades
        self.book_b1.unlink()
        self.assertFalse(reviews[0].exists())
        self.assertTrue(reviews[1].exists())

    def test_one2many(self):
        Author = self.env['test.mongo.author']
        self.assertEqual(Author.search([('book_ids.name', '=', 'Mango')]), self.author_b)
        self.assertEqual(Author.search([('book_ids', 'any', [('pages', '>', 60)])]), self.author_a + self.author_b)
        self.assertEqual(Author.search([('book_ids', 'not any', [('pages', '>', 60)])]), Author)
        self.author_a.write({'book_ids': [(0, 0, {'name': 'New', 'pages': 1})]})
        self.assertEqual(self.author_a.book_count, 3)
        self.assertEqual(len(self.author_a.book_ids), 3)

    def test_many2many(self):
        Author = self.env['test.mongo.author']
        self.assertEqual(Author.search([('tag_ids', 'in', self.tag_x.ids)]), self.author_a)
        self.assertEqual(Author.search([('tag_ids.name', '=', 'x')]), self.author_a)
        self.assertEqual(Author.search([('tag_ids', '=', False)]), self.author_b)
        self.assertEqual(self.tag_x.author_ids, self.author_a)
        self.author_b.tag_ids = [(4, self.tag_x.id), (4, self.tag_y.id)]
        self.author_b.flush_recordset()
        self.assertEqual(self.doc(self.author_b)['tagRel'], [{'tagId': self.tag_x.id}, {'tagId': self.tag_y.id}])
        self.tag_x.invalidate_recordset()
        self.assertEqual(self.tag_x.author_ids, self.author_a + self.author_b)
        self.author_b.tag_ids = [(3, self.tag_x.id)]
        self.author_b.flush_recordset()
        self.assertEqual(self.doc(self.author_b)['tagRel'], [{'tagId': self.tag_y.id}])
        self.assertEqual(self.author_b.tag_ids, self.tag_y)
        # relation table as its own collection
        Book = self.env['test.mongo.book']
        rel = self.store.collection('testMongoBookTagRel')
        self.assertEqual(list(rel.find({}, {'_id': 0})), [{'bookId': self.book_a1.id, 'tagId': self.tag_y.id}])
        self.assertEqual(Book.search([('tag_ids', 'in', self.tag_y.ids)]), self.book_a1)
        self.assertEqual(self.book_a1.tag_ids, self.tag_y)
        self.book_a1.tag_ids = [(5,)]
        self.book_a1.flush_recordset()
        self.assertEqual(rel.count_documents({}), 0)
        # PostgreSQL model with a PostgreSQL relation table onto MongoDB tags
        review = self.env['test.mongo.review'].create({'name': 'r', 'tag_ids': [(6, 0, (self.tag_x + self.tag_y).ids)]})
        self.assertEqual(review.tag_ids, self.tag_x + self.tag_y)
        self.assertEqual(self.env['test.mongo.review'].search([('tag_ids.name', '=', 'y')]), review)
        # deleting either endpoint removes the MongoDB-stored links
        self.book_a1.tag_ids = [(4, self.tag_y.id)]
        self.env.flush_all()
        book_id, tag_id = self.book_a1.id, self.tag_x.id
        self.assertEqual(rel.count_documents({'bookId': book_id}), 1)
        self.book_a1.unlink()
        self.assertEqual(rel.count_documents({'bookId': book_id}), 0)
        self.assertEqual([e['tagId'] for e in self.doc(self.author_a)['tagRel']], [tag_id])
        self.tag_x.unlink()
        self.assertEqual(self.doc(self.author_a)['tagRel'], [])
        self.assertFalse(self.author_a.tag_ids)

    def test_embedded_model(self):
        Chapter = self.env['test.mongo.chapter']
        chapters = self.book_a1.chapter_ids
        self.assertEqual(chapters.mapped('name'), ['Two', 'One'])                  # sequence order
        self.assertEqual(Chapter.search([('book_id', '=', self.book_a1.id)]), chapters)
        self.assertEqual(Chapter.search([('name', '=', 'One')]).book_id, self.book_a1)
        self.assertEqual(Chapter.search([('book_id.name', '=', 'Zebra')]), chapters)
        doc = self.doc(self.book_a1)
        self.assertEqual([(c['id'], c['name']) for c in doc['chapter']],
                         [(chapters[1].id, 'One'), (chapters[0].id, 'Two')])
        chapters[1].write({'name': 'Uno', 'sequence': 0})
        chapters.flush_recordset()
        self.assertEqual([(c['name'], c['sequence']) for c in self.doc(self.book_a1)['chapter']], [('Uno', 0), ('Two', 1)])
        self.book_a1.invalidate_recordset(['chapter_ids'])
        self.assertEqual(self.book_a1.chapter_ids.mapped('name'), ['Uno', 'Two'])
        # move a chapter to another book
        chapters[0].book_id = self.book_a2
        chapters.flush_recordset()
        self.assertEqual([c['name'] for c in self.doc(self.book_a1)['chapter']], ['Uno'])
        self.assertEqual([c['name'] for c in self.doc(self.book_a2)['chapter']], ['Two'])
        self.assertEqual(self.book_a2.chapter_ids, chapters[0])
        chapters[0].unlink()
        self.assertEqual(self.doc(self.book_a2)['chapter'], [])
        self.env.cr.execute("SELECT id FROM test_mongo_chapter")
        self.assertEqual([r[0] for r in self.env.cr.fetchall()], [chapters[1].id])
        # deleting the book cascades through the chapters' own unlink (array, shadow rows, attachments)
        attachment = self.env['ir.attachment'].create({'name': 'a', 'res_model': Chapter._name, 'res_id': chapters[1].id})
        self.book_a1.unlink()
        self.assertFalse(chapters[1].exists())
        self.assertEqual(Chapter.search_count([]), 0)
        self.assertFalse(attachment.exists())

    def test_inherits(self):
        Variant = self.env['test.mongo.variant']
        variants = Variant.create([
            {'name': 'Kiwi', 'author_id': self.author_b.id, 'code': 'K1', 'pages': 7},
            {'name': 'Banana', 'author_id': self.author_a.id, 'code': 'B1'},
        ])
        self.assertEqual(variants.mapped('name'), ['Kiwi', 'Banana'])
        self.assertEqual(variants[0].book_id.pages, 7)
        self.assertEqual(Variant.search([('name', '=', 'Kiwi')]), variants[0])
        self.assertEqual(Variant.search([('author_id.name', '=', 'Ann')]), variants[1])
        self.assertEqual(Variant.search([]), variants[1] + variants[0])            # ordered by inherited name
        variants[0].name = 'Apricot'
        self.env.flush_all()
        self.assertEqual(self.doc(variants[0].book_id)['name'], 'Apricot')
        self.assertEqual(Variant.search([], order='name desc'), variants[1] + variants[0])
        variants[1].unlink()
        self.assertFalse(variants[1].exists())

    def test_parent_store(self):
        Author = self.env['test.mongo.author']
        child = Author.create({'name': 'Child', 'parent_id': self.author_a.id})
        grandchild = Author.create({'name': 'Grand', 'parent_id': child.id})
        self.assertEqual(child.parent_path, f'{self.author_a.id}/{child.id}/')
        self.assertEqual(grandchild.parent_path, f'{self.author_a.id}/{child.id}/{grandchild.id}/')
        self.assertEqual(Author.search([('id', 'child_of', self.author_a.id)]), self.author_a + child + grandchild)
        self.assertEqual(Author.search([('id', 'parent_of', grandchild.id)]), self.author_a + child + grandchild)
        child.parent_id = self.author_b
        child.flush_recordset()
        self.assertEqual(grandchild.parent_path, f'{self.author_b.id}/{child.id}/{grandchild.id}/')
        self.assertEqual(self.doc(grandchild)['parentPath'], grandchild.parent_path)
        self.assertEqual(Author.search([('id', 'child_of', self.author_b.id)]), self.author_b + child + grandchild)
        # cascade through the many2one ondelete emulation
        self.author_b.unlink()
        self.assertFalse((child + grandchild).exists())

    def test_read_group(self):
        Author = self.env['test.mongo.author']
        self.assertEqual(
            Author._read_group([], ['state'], ['__count', 'rating:sum']),
            [('draft', 1, 4.5), ('done', 1, 3.0)],
        )
        self.assertEqual(Author._read_group([], [], ['rating:max', 'rating:avg']), [(4.5, 3.75)])
        groups = Author._read_group([], ['partner_id'], ['__count'], order='partner_id')
        self.assertEqual(groups, [(self.partner_a, 1), (self.partner_b, 1)])
        self.assertEqual(Author._read_group([], ['birthday:year'], ['__count']),
                         [(datetime.date(1980, 1, 1), 1), (False, 1)])
        Book = self.env['test.mongo.book']
        self.assertEqual(
            Book._read_group([], ['author_id'], ['pages:sum', 'price:sum'], order='author_id'),
            [(self.author_a, 150, 30.5), (self.author_b, 300, 5.0)],
        )
        self.assertEqual(Book._read_group([], ['published:month'], ['__count'], order='published:month desc'),
                         [(False, 1), (datetime.datetime(2024, 4, 1), 1), (datetime.datetime(2024, 3, 1), 1)])
        self.assertEqual(Book._read_group([], ['author_id'], ['__count'], having=[('__count', '>', 1)]),
                         [(self.author_a, 2)])
        self.assertEqual(Book.read_group([], ['author_id'], ['pages:sum'])[0][1], 150)

    def test_required_and_ondelete(self):
        with self.assertRaises(psycopg2.IntegrityError), mute_logger('odoo.sql_db'):
            with self.env.cr.savepoint():
                self.env['test.mongo.book'].create({'author_id': self.author_a.id})
        # restrict from a PostgreSQL table onto the shadow (real foreign key)
        self.env['test.mongo.review'].create({'name': 'r', 'author_id': self.author_a.id})
        with self.assertRaises(psycopg2.IntegrityError), mute_logger('odoo.sql_db'):
            with self.env.cr.savepoint():
                self.author_a.unlink()
        # set null emulated for a MongoDB document referencing a deleted PostgreSQL row
        self.partner_a.unlink()
        self.assertFalse(self.author_b.partner_id)
        self.assertIsNone(self.doc(self.author_b)['partnerId'])

    def test_init_skipped(self):
        # test.mongo.tag.init() indexes a column the id shadow does not have: Registry.init_models()
        # must not run init() for a MongoDB-stored model (the install would have failed)
        cr = self.env.cr
        self.assertFalse(sql.index_exists(cr, 'test_mongo_tag_name_index'))
        self.assertEqual(sql.table_columns(cr, 'test_mongo_tag').keys(), {'id'})

    def test_check_constraint(self):
        Book = self.env['test.mongo.book']
        # the constraint is not on the shadow; the storage path enforces it like PostgreSQL would
        self.assertIsNone(sql.constraint_definition(self.env.cr, 'test_mongo_book', 'test_mongo_book_check_pages'))
        with self.assertRaises(psycopg2.errors.CheckViolation) as cm, mute_logger('odoo.sql_db'):
            with self.env.cr.savepoint():
                Book.create([{'name': 'Ok', 'author_id': self.author_a.id, 'pages': 1},
                             {'name': 'Neg', 'author_id': self.author_a.id, 'pages': -1}])
        self.assertEqual(cm.exception.diag.constraint_name, 'test_mongo_book_check_pages')
        self.assertEqual(Book._sql_error_to_message(cm.exception), 'Pages must be positive.')
        self.assertFalse(Book.search([('name', 'in', ('Ok', 'Neg'))]))
        self.assertEqual(self.store.model_collection(Book).count_documents({'name': {'$in': ['Ok', 'Neg']}}), 0)
        with self.assertRaises(psycopg2.errors.CheckViolation) as cm, mute_logger('odoo.sql_db'):
            with self.env.cr.savepoint():
                self.book_a1.write({'pages': -5})
                self.env.flush_all()
        self.assertEqual(cm.exception.diag.constraint_name, 'test_mongo_book_check_pages')
        self.env.invalidate_all()
        self.assertEqual(self.book_a1.pages, 100)
        self.book_a1.write({'pages': 7})
        self.env.flush_all()
        self.assertEqual(self.doc(self.book_a1)['pages'], 7)

    def test_duplicate_unique_key(self):
        Tag = self.env['test.mongo.tag']
        coll = self.store.model_collection(Tag)
        with self.assertRaises(psycopg2.errors.UniqueViolation) as cm, mute_logger('odoo.sql_db'):
            with self.env.cr.savepoint():
                Tag.create([{'name': 'z'}, {'name': 'x'}])
        self.assertEqual(cm.exception.diag.constraint_name, 'name_1')
        self.assertEqual(cm.exception.diag.table_name, 'test_mongo_tag')
        self.assertEqual(cm.exception.diag.message_detail, "Key (name)=(x) already exists.")
        self.assertIn('name_1', Tag._sql_error_to_message(cm.exception))
        # the rows inserted before the duplicate are gone, like the whole INSERT on PostgreSQL
        self.assertEqual(coll.count_documents({'name': 'z'}), 0)
        self.assertEqual(Tag.search_count([]), 2)
        with self.assertRaises(psycopg2.errors.UniqueViolation), mute_logger('odoo.sql_db'):
            with self.env.cr.savepoint():
                self.tag_y.write({'name': 'x'})
                self.env.flush_all()
        self.assertEqual(self.doc(self.tag_y)['name'], 'y')

    def test_unopted_relation_stays_in_postgresql(self):
        # test_mongo_review_partner_rel is spec-mapped to a collection, but neither model is opted in
        cr = self.env.cr
        self.assertTrue(sql.table_exists(cr, 'test_mongo_review_partner_rel'))
        review = self.env['test.mongo.review'].create({'name': 'r', 'partner_ids': [(6, 0, self.partner_a.ids)]})
        self.env.flush_all()
        cr.execute("SELECT partner_id FROM test_mongo_review_partner_rel WHERE review_id = %s", [review.id])
        self.assertEqual([r[0] for r in cr.fetchall()], self.partner_a.ids)
        self.assertEqual(review.partner_ids, self.partner_a)
        self.assertEqual(self.env['test.mongo.review'].search([('partner_ids', 'in', self.partner_a.ids)]), review)
        self.assertNotIn(self.store.collection('testMongoReviewPartnerRel').name, self.store.db.list_collection_names())

    def test_rollback_journal(self):
        Author = self.env['test.mongo.author']
        coll = self.store.model_collection(Author)
        before = coll.count_documents({})
        with self.assertRaises(ZeroDivisionError), self.env.cr.savepoint():
            extra = Author.create({'name': 'Gone'})
            self.author_a.write({'name': 'Changed'})
            self.author_b.unlink()
            self.env.flush_all()
            self.assertEqual(coll.count_documents({}), before)
            self.assertEqual(coll.find_one({'_id': extra.id})['name'], 'Gone')
            1 / 0
        self.assertEqual(coll.count_documents({}), before)
        self.assertEqual(coll.find_one({'_id': self.author_a.id})['name'], 'Ann')
        self.assertEqual(coll.find_one({'_id': self.author_b.id})['name'], 'Ben')
        # a value committed by another cursor in between is kept on rollback
        with self.assertRaises(ZeroDivisionError), self.env.cr.savepoint():
            self.author_a.write({'name': 'Mine', 'state': 'done'})
            self.env.flush_all()
            coll.update_one({'_id': self.author_a.id}, {'$set': {'name': 'Theirs'}})
            1 / 0
        self.assertEqual(coll.find_one({'_id': self.author_a.id})['name'], 'Theirs')
        self.assertEqual(coll.find_one({'_id': self.author_a.id})['state'], 'draft')    # the other field is undone
        coll.update_one({'_id': self.author_a.id}, {'$set': {'name': 'Ann'}})
        # the first MongoDB write of a cursor made inside a savepoint rolls back with it
        with self.registry.cursor() as cr:
            env = self.env(cr=cr)
            with self.assertRaises(ZeroDivisionError), cr.savepoint():
                extra = env['test.mongo.author'].create({'name': 'Gone'})
                env.flush_all()
                self.assertEqual(coll.find_one({'_id': extra.id})['name'], 'Gone')
                1 / 0
            self.assertIsNone(coll.find_one({'_id': extra.id}))
            cr.rollback()

    def test_translations(self):
        author = self.author_a
        author.with_context(lang='fr_FR').title = 'Docteur'
        author.flush_recordset()
        self.assertEqual(self.doc(author)['title'], {'en_US': 'Doctor', 'fr_FR': 'Docteur'})
        author.invalidate_recordset()
        self.assertEqual(author.title, 'Doctor')
        self.assertEqual(author.with_context(lang='fr_FR').title, 'Docteur')
        Author = self.env['test.mongo.author']
        self.assertEqual(Author.with_context(lang='fr_FR').search([('title', 'ilike', 'docteur')]), author)
        self.assertEqual(Author.search([('title', '=', 'Doctor')]), author)
        self.assertEqual(Author.with_context(lang='fr_FR').search([('title', '=', 'Doctor')]), Author)
        # untranslated records fall back to en_US
        self.author_b.title = 'Mr'
        self.author_b.flush_recordset()
        self.assertEqual(Author.with_context(lang='fr_FR').search([('title', '=', 'Mr')]), self.author_b)
