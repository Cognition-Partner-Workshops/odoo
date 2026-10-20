# Part of Odoo. See LICENSE file for full copyright and licensing details.
import datetime

import psycopg2

from odoo.exceptions import UserError
from odoo.orm.storage_mongodb import _check_constraints, relax_registry_shadow_tables
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

    def test_embedded_relation_inverse_side(self):
        # self-referential relation table embedded on the author document: both fields read and write it
        Author = self.env['test.mongo.author']
        a, b = self.author_a, self.author_b
        a.coauthor_ids = [(4, b.id)]
        a.flush_recordset()
        self.assertEqual(self.doc(a)['coauthorRel'], [{'coauthorId': b.id}])
        self.assertNotIn('coauthorRel', self.doc(b))
        (a + b).invalidate_recordset()
        self.assertEqual(a.coauthor_ids, b)
        self.assertEqual(b.coauthor_of_ids, a)
        self.assertFalse(a.coauthor_of_ids)
        self.assertFalse(b.coauthor_ids)
        self.assertEqual(Author.search([('coauthor_ids', 'in', b.ids)]), a)
        self.assertEqual(Author.search([('coauthor_of_ids', 'in', a.ids)]), b)
        self.assertEqual(Author.search([('coauthor_of_ids', '=', False)]), a)
        self.assertEqual(Author.search([('coauthor_of_ids.name', '=', 'Ann')]), b)
        self.assertEqual(Author.search([('coauthor_ids.name', '=', 'Ann')]), Author)
        # writes through the inverse side land on the owning document
        c = Author.create({'name': 'Cid', 'coauthor_of_ids': [(4, b.id)]})
        self.env.flush_all()
        self.assertEqual(self.doc(b)['coauthorRel'], [{'coauthorId': c.id}])
        self.assertNotIn('coauthorRel', self.doc(c))
        (b + c).invalidate_recordset()
        self.assertEqual(b.coauthor_ids, c)
        self.assertEqual(c.coauthor_of_ids, b)
        c.coauthor_of_ids = [(3, b.id)]
        self.env.flush_all()
        self.assertEqual(self.doc(b)['coauthorRel'], [])
        # deleting the inverse endpoint removes the link from the owner's document
        a.coauthor_ids = [(4, c.id)]
        self.env.flush_all()
        self.assertEqual([e['coauthorId'] for e in self.doc(a)['coauthorRel']], [b.id, c.id])
        c.unlink()
        self.assertEqual([e['coauthorId'] for e in self.doc(a)['coauthorRel']], [b.id])
        a.invalidate_recordset()
        self.assertEqual(a.coauthor_ids, b)

    def test_company_dependent_write(self):
        Author = self.env['test.mongo.author']
        company = self.env.company
        other = self.env['res.company'].create({'name': 'Other'})
        author = self.author_a
        author.property_note = 'main'
        author.flush_recordset()
        self.assertEqual(self.doc(author)['propertyNote'], {str(company.id): 'main'})
        author.with_company(other).property_note = 'other'
        author.flush_recordset()
        self.assertEqual(self.doc(author)['propertyNote'], {str(company.id): 'main', str(other.id): 'other'})
        author.invalidate_recordset()
        self.assertEqual(author.property_note, 'main')
        self.assertEqual(author.with_company(other).property_note, 'other')
        created = Author.with_company(other).create({'name': 'Cat', 'property_note': 'new'})
        created.flush_recordset()
        self.assertEqual(self.doc(created)['propertyNote'], {str(other.id): 'new'})
        self.assertFalse(created.with_company(company).property_note)
        self.assertEqual(Author.search([('property_note', '=', 'main')]), author)
        self.assertEqual(Author.with_company(other).search([('property_note', '=', 'main')]), Author)
        self.assertEqual(Author.with_company(other).search([('property_note', 'in', ['other', 'new'])]), author + created)

    def test_compute_sql_domain(self):
        Book = self.env['test.mongo.book']
        self.assertEqual(Book.search([]), self.book_a2 + self.book_a1 + self.book_b1)
        self.book_b1.archived = True
        self.book_b1.flush_recordset()
        self.assertIs(self.doc(self.book_b1)['archived'], True)
        self.assertFalse(self.book_b1.active)
        # active_test adds ('active', '=', True): no document path, the field is computed in Python
        self.assertEqual(Book.search([]), self.book_a2 + self.book_a1)
        self.assertEqual(Book.search_count([]), 2)
        self.assertEqual(Book.with_context(active_test=False).search([]), self.book_a2 + self.book_a1 + self.book_b1)
        self.assertEqual(Book.search([('active', '=', False)]), self.book_b1)
        self.assertEqual(Book.search([('active', '!=', True)]), self.book_b1)
        self.assertEqual(Book.search([('active', '=', True), ('author_id', '=', self.author_b.id)]), Book)
        self.author_b.invalidate_recordset(['book_ids'])
        self.assertEqual(self.author_b.book_ids, Book)
        self.assertEqual(self.author_b.with_context(active_test=False).book_ids, self.book_b1)

    def test_relation_owned_by_later_unit_stays_in_postgresql(self):
        # one side opted in (books), the mapped relation collection owned by the reviews' unit (not opted in)
        Book, Review = self.env['test.mongo.book'], self.env['test.mongo.review']
        before = set(self.store.db.list_collection_names())
        review = Review.create({'name': 'r', 'book_ids': [(6, 0, (self.book_a1 + self.book_b1).ids)]})
        self.env.flush_all()
        self.env.cr.execute("SELECT book_id FROM test_mongo_review_book_rel WHERE review_id = %s ORDER BY book_id", (review.id,))
        self.assertEqual([r[0] for r in self.env.cr.fetchall()], sorted((self.book_a1 + self.book_b1).ids))
        self.assertEqual(review.book_ids, self.book_a1 + self.book_b1)
        self.book_a1.invalidate_recordset()
        self.assertEqual(self.book_a1.review_m2m_ids, review)
        self.assertEqual(Book.search([('review_m2m_ids', 'in', review.ids)]), self.book_a1 + self.book_b1)
        self.assertEqual(Book.search([('review_m2m_ids.name', '=', 'r')]), self.book_a1 + self.book_b1)
        self.assertEqual(Review.search([('book_ids', 'in', self.book_b1.ids)]), review)
        self.assertEqual(Review.search([('book_ids.name', '=', 'Mango')]), review)
        self.book_b1.review_m2m_ids = [(3, review.id)]
        self.env.flush_all()
        self.assertEqual(review.book_ids, self.book_a1)
        # embedded variant: the review-tag relation is an array of the (not yet opted-in) review document
        review.tag_ids = [(6, 0, (self.tag_x + self.tag_y).ids)]
        self.env.flush_all()
        self.env.cr.execute("SELECT tag_id FROM test_mongo_review_tag_rel WHERE review_id = %s ORDER BY tag_id", (review.id,))
        self.assertEqual([r[0] for r in self.env.cr.fetchall()], sorted((self.tag_x + self.tag_y).ids))
        review.invalidate_recordset()
        self.assertEqual(review.tag_ids, self.tag_x + self.tag_y)
        self.assertEqual(Review.search([('tag_ids', 'in', self.tag_y.ids)]), review)
        self.assertEqual(self.env['test.mongo.tag'].search([('id', 'in', review.tag_ids.ids)]), self.tag_x + self.tag_y)
        self.assertEqual(set(self.store.db.list_collection_names()) - before, set())
        # the relation a MongoDB-stored model owns is served from MongoDB (books' own tag relation)
        self.assertEqual(self.store.collection('testMongoBookTagRel').count_documents({'bookId': self.book_a1.id}), 1)

    def test_search_flushes_pending_writes(self):
        Author = self.env['test.mongo.author']
        self.author_a.name = 'Renamed'                      # pending in cache, not flushed
        self.assertEqual(Author.search([('name', '=', 'Renamed')]), self.author_a)
        self.assertEqual(self.doc(self.author_a)['name'], 'Renamed')
        self.author_b.rating = 9
        self.assertEqual(Author.search([], order='rating desc', limit=1), self.author_b)
        created = Author.create({'name': 'Fresh', 'rating': 1})
        created.tag_ids = [(4, self.tag_y.id)]
        self.assertEqual(Author.search([('tag_ids', 'in', self.tag_y.ids)]), created)
        self.assertEqual(Author.search_count([('tag_ids', 'in', self.tag_y.ids)]), 1)

    def test_property_definition(self):
        Book = self.env['test.mongo.book']
        self.author_a.book_properties_definition = [{'name': 'genre', 'type': 'char', 'string': 'Genre'}]
        self.author_a.flush_recordset()
        stored = self.doc(self.author_a)['bookPropertiesDefinition']
        self.assertEqual([(d['name'], d['type']) for d in stored], [('genre', 'char')])    # an array, not JSON text
        definition = Book.get_property_definition('book_properties.genre')
        self.assertEqual((definition['name'], definition['type'], definition['string']), ('genre', 'char', 'Genre'))
        self.assertEqual(Book.get_property_definition('book_properties.missing'), {})
        self.book_a1.book_properties = {'genre': 'Novel'}
        self.book_a1.flush_recordset()
        self.assertEqual(self.doc(self.book_a1)['bookProperties'], {'genre': 'Novel'})
        self.book_a1.invalidate_recordset()
        values = self.book_a1.read(['book_properties'])[0]['book_properties']
        self.assertEqual([(d['name'], d['value']) for d in values], [('genre', 'Novel')])

    def test_many2many_read_with_active_test_context(self):
        # a field context carrying active_test must not clash with the default the read sets;
        # like PostgreSQL, the plain field hides archived comodel records, the context one shows them
        Review = self.env['test.mongo.review']
        review = Review.create({'name': 'ctx', 'book_ids': [(6, 0, (self.book_a1 + self.book_b1).ids)]})
        self.book_b1.archived = True
        self.env.flush_all()
        review.invalidate_recordset()
        self.assertEqual(review.archived_book_ids, self.book_a1 + self.book_b1)
        self.assertEqual(review.book_ids, self.book_a1)

    def test_postgresql_domain_into_mongodb_comodel(self):
        Review = self.env['test.mongo.review']
        review = Review.create({'name': 'dom', 'book_ids': [(6, 0, (self.book_a1 + self.book_b1).ids)]})
        other = Review.create({'name': 'none'})
        self.book_b1.archived = True
        self.env.flush_all()
        # PostgreSQL semantics: an id list matches archived records, a subdomain obeys active_test
        self.assertEqual(Review.search([('book_ids', 'in', self.book_b1.ids)]), review)
        self.assertEqual(Review.search([('book_ids', 'in', self.book_a1.ids)]), review)
        self.assertEqual(Review.search([('book_ids', 'any', [('id', '=', self.book_a1.id)])]), review)
        self.assertFalse(Review.search([('book_ids', 'any', [('id', '=', self.book_b1.id)])]))
        self.assertEqual(Review.with_context(active_test=False).search([('book_ids', 'any', [('id', '=', self.book_b1.id)])]), review)
        not_a1 = Review.search([('book_ids', 'not in', self.book_a1.ids)])
        self.assertIn(other, not_a1)
        self.assertNotIn(review, not_a1)
        groups = Review._read_group([('id', 'in', (review + other).ids)], ['book_ids'], ['__count'])
        self.assertEqual({(book.id, count) for book, count in groups}, {(self.book_a1.id, 1), (False, 1)})
        # the relation embedded in the comodel's documents, served from MongoDB (owner opted in)
        review.author_ids = self.author_a
        self.env.flush_all()
        self.assertEqual(self.doc(self.author_a)['reviewRel'], [{'reviewId': review.id}])
        self.assertEqual(review.author_ids, self.author_a)
        self.assertEqual(Review.search([('author_ids', 'in', self.author_a.ids)]), review)
        self.assertEqual(Review.search([('author_ids', 'any', [('name', '=', self.author_a.name)])]), review)
        self.assertNotIn(review, Review.search([('author_ids', 'not in', self.author_a.ids)]))
        self.assertFalse(self.env.registry.db_name and self.store.db.list_collection_names(filter={'name': {'$regex': 'AuthorReview'}}))

    def test_embedded_composite_key_rows(self):
        Edition = self.env['test.mongo.edition']
        e1, e2 = Edition.create([
            {'book_id': self.book_a1.id, 'lang': 'en', 'year': 2001, 'note': 'first'},
            {'book_id': self.book_a1.id, 'lang': 'fr', 'year': 2002},
        ])
        elements = self.doc(self.book_a1)['edition']
        self.assertEqual([(e['id'], e['lang'], e['year']) for e in elements], [(e1.id, 'en', 2001), (e2.id, 'fr', 2002)])
        self.assertEqual(self.book_a1.edition_ids, e1 + e2)
        self.assertEqual(Edition.search([('book_id', '=', self.book_a1.id), ('lang', '=', 'fr')]), e2)
        # the composite key is unique within its parent, like the SQL constraint on (book_id, lang, year)
        with self.assertRaises(psycopg2.errors.UniqueViolation) as cm, mute_logger('odoo.sql_db'):
            with self.env.cr.savepoint():
                Edition.create({'book_id': self.book_a1.id, 'lang': 'en', 'year': 2001})
        self.assertEqual(cm.exception.diag.constraint_name, 'test_mongo_edition_book_lang_year_uniq')
        self.assertEqual(Edition._sql_error_to_message(cm.exception), 'One edition per language and year.')
        with self.assertRaises(psycopg2.errors.UniqueViolation), mute_logger('odoo.sql_db'):
            with self.env.cr.savepoint():
                Edition.create([{'book_id': self.book_a2.id, 'lang': 'de', 'year': 2003}] * 2)
        with self.assertRaises(psycopg2.errors.UniqueViolation), mute_logger('odoo.sql_db'):
            with self.env.cr.savepoint():
                e2.write({'lang': 'en', 'year': 2001})
                e2.flush_recordset()
        e3 = Edition.create({'book_id': self.book_a2.id, 'lang': 'fr', 'year': 2002})
        with self.assertRaises(psycopg2.errors.UniqueViolation), mute_logger('odoo.sql_db'):
            with self.env.cr.savepoint():
                e2.write({'book_id': self.book_a2.id})
                e2.flush_recordset()
        self.assertEqual([(e['id'], e['lang'], e['year']) for e in self.doc(self.book_a1)['edition']], [(e1.id, 'en', 2001), (e2.id, 'fr', 2002)])
        e3.unlink()
        e1.note = 'revised'
        e1.flush_recordset()
        self.assertEqual(self.doc(self.book_a1)['edition'][0]['note'], 'revised')
        e2.book_id = self.book_a2
        e2.flush_recordset()
        self.assertEqual([e['id'] for e in self.doc(self.book_a2)['edition']], [e2.id])
        self.assertEqual([e['id'] for e in self.doc(self.book_a1)['edition']], [e1.id])
        e1.unlink()
        self.assertFalse(self.doc(self.book_a1).get('edition'))

    def test_missing_field_sorts_as_null(self):
        # the loader omits NULL columns: a missing field orders like NULL in PostgreSQL (last on ASC, first on DESC)
        Book = self.env['test.mongo.book']
        book = Book.create({'name': 'Unpaged', 'author_id': self.author_a.id, 'pages': 5})
        getattr(self.store.model_collection(Book), 'update' + '_one')({'_id': book.id}, {'$unset': {'pages': ''}})
        self.assertEqual(Book.search([], order='pages asc, id')[-1], book)
        self.assertEqual(Book.search([], order='pages desc, id')[0], book)
        self.assertEqual(Book.search([], order='pages asc nulls first, id')[0], book)

    def test_order_by_compute_sql_field(self):
        # account.account's default _order names code_path (compute_sql, no document path): the field is
        # computed in Python over the filtered records; ties fall through to the next term, NULLs place
        # like PostgreSQL's (last on ASC, first on DESC)
        Book = self.env['test.mongo.book']
        self.assertEqual((self.book_a1.shelf, self.book_a2.shelf, self.book_b1.shelf), ('2024', '2024', False))
        self.assertEqual(Book.search([], order='shelf, name'), self.book_a2 + self.book_a1 + self.book_b1)
        self.assertEqual(Book.search([], order='shelf desc, name desc'), self.book_b1 + self.book_a1 + self.book_a2)
        self.assertEqual(Book.search([], order='shelf asc nulls first, name'), self.book_b1 + self.book_a2 + self.book_a1)
        self.assertEqual(Book.search([('pages', '>', 60)], order='shelf desc, name'), self.book_b1 + self.book_a1)
        self.assertEqual(Book.search([], order='shelf, name', limit=1, offset=1), self.book_a1)
        # a computed Float with digits orders numerically (its column format is a string: '10.00' < '2.50')
        self.assertEqual((self.book_a1.half_price, self.book_a2.half_price, self.book_b1.half_price), (5.25, 10.0, 2.5))
        self.assertEqual(Book.search([], order='half_price, id'), self.book_b1 + self.book_a1 + self.book_a2)
        self.assertEqual(Book.search([], order='half_price desc, id'), self.book_a2 + self.book_a1 + self.book_b1)
        self.book_b1.published = '2023-01-01 00:00:00'
        self.book_b1.flush_recordset()
        self.assertEqual(Book.search([], order='shelf, name'), self.book_b1 + self.book_a2 + self.book_a1)
        # an empty value is not NULL (compute and compute_sql agree): '' sorts before every year, the NULLs stay apart
        late = Book.create({'name': 'Zed', 'author_id': self.author_b.id})
        self.book_b1.write({'published': False, 'archived': True})
        self.env.flush_all()
        self.assertEqual((self.book_b1.shelf, late.shelf), ('', False))
        all_books = Book.with_context(active_test=False)
        self.assertEqual(all_books.search([], order='shelf, name'), self.book_b1 + self.book_a2 + self.book_a1 + late)
        self.assertEqual(all_books.search([], order='shelf desc, name'), late + self.book_a2 + self.book_a1 + self.book_b1)
        self.book_b1.write({'published': '2023-01-01 00:00:00', 'archived': False})
        late.unlink()
        self.env.flush_all()
        # the generic list view: search([]) with the model's default _order
        self.patch(type(Book), '_order', 'shelf desc, name, id')
        self.assertEqual(Book.search([]), self.book_a2 + self.book_a1 + self.book_b1)
        self.assertEqual(Book.search([('author_id', '=', self.author_a.id)]), self.book_a2 + self.book_a1)

    def test_postgresql_domain_through_many2many_with_comodel_domain(self):
        # product.template.taxes_id carries domain=[('type_tax_use', '=', 'sale')]: ('taxes_id', 'in', ids) on the
        # PostgreSQL model becomes 'any!' over the comodel's ids as a MongoQuery, and the field's domain
        # has to join its filter instead of being added as SQL
        Review = self.env['test.mongo.review']
        review = Review.create({'name': 'dom', 'book_ids': [(6, 0, (self.book_a1 + self.book_a2).ids)],
                                'author_ids': [(6, 0, (self.author_a + self.author_b).ids)]})
        other = Review.create({'name': 'none'})
        self.env.flush_all()
        self.assertEqual(review.cheap_book_ids, self.book_a1)                       # 10.5 < 15, Apple is 20
        # PostgreSQL relation table
        self.assertEqual(Review.search([('cheap_book_ids', 'in', self.book_a1.ids)]), review)
        self.assertFalse(Review.search([('cheap_book_ids', 'in', self.book_a2.ids)]))
        self.assertEqual(Review.search([('cheap_book_ids', 'in', (self.book_a1 + self.book_a2).ids)]), review)
        self.assertEqual(Review.search([('cheap_book_ids', 'not in', self.book_a2.ids)]), review + other)
        self.assertEqual(Review.search([('cheap_book_ids', 'not in', self.book_a1.ids)]), other)
        self.assertEqual(Review.search([('cheap_book_ids', 'any', [('name', '=', 'Zebra')])]), review)
        self.assertFalse(Review.search([('cheap_book_ids', 'any', [('name', '=', 'Apple')])]))
        # relation embedded in the comodel's documents (product_taxes_rel in accountTax)
        self.assertEqual(review.rated_author_ids, self.author_a)                   # 4.5 > 4, Ben is 3.0
        self.assertEqual(Review.search([('rated_author_ids', 'in', self.author_a.ids)]), review)
        self.assertFalse(Review.search([('rated_author_ids', 'in', self.author_b.ids)]))
        self.assertEqual(Review.search([('rated_author_ids', 'not in', self.author_b.ids)]), review + other)
        self.assertEqual(Review.search([('rated_author_ids', 'in', [False])]), other)

    def test_dotted_search_over_company_dependent_many2one(self):
        # product.category property_account_*_id.active: a document holds the company's value or nothing, and
        # nothing means the ir.default fallback (COALESCE(col->>company, fallback) in SQL). Every search is
        # compared with the same search on the PostgreSQL twin field, in two companies.
        Author, Review = self.env['test.mongo.author'], self.env['test.mongo.review']
        company_a, company_b = self.env.company, self.env['res.company'].create({'name': 'B'})
        eur, usd = self.env.ref('base.EUR'), self.env.ref('base.USD')
        authors = self.author_a + self.author_b + Author.create({'name': 'Cid'})
        reviews = Review.create([{'name': 'ra'}, {'name': 'rb'}, {'name': 'rc'}])
        for model in (Author, Review):
            self.env['ir.default'].set(model._name, 'property_currency_id', eur.id, company_id=company_a.id)
        for recs in (authors, reviews):
            recs[0].with_company(company_a).property_currency_id = usd      # explicit (USD) in A, no value and no fallback in B
            recs[1].with_company(company_b).property_currency_id = eur    # fallback (EUR) in A, explicit (EUR) in B
        self.env.flush_all()
        doc = self.doc(authors[0])
        self.assertEqual(doc['propertyCurrencyId'], {str(company_a.id): usd.id})
        self.assertNotIn('propertyCurrencyId', self.doc(authors[2]))
        domains = [
            [('property_currency_id.name', '=', 'EUR')], [('property_currency_id.name', '=', 'USD')],
            [('property_currency_id.active', '=', True)], [('property_currency_id', '=', False)],
            [('property_currency_id', '!=', False)], [('property_currency_id.name', '!=', 'EUR')],
            [('property_currency_id', 'not any', [('name', '=', 'EUR')])], [('property_currency_id', 'in', [eur.id])],
            [('property_currency_id', 'in', [eur.id, False])], [('property_currency_id.name', 'ilike', 'us')],
        ]
        def positions(recs, domain, company):
            found = recs.with_company(company).search([('id', 'in', recs.ids), *domain])
            return sorted(recs.ids.index(id_) for id_ in found.ids)
        for company in (company_a, company_b):
            for domain in domains:
                with self.subTest(company=company.name, domain=domain):
                    self.assertEqual(positions(authors, domain, company), positions(reviews, domain, company))
        self.assertEqual(positions(authors, domains[0], company_a), [1, 2])     # fallback: EUR for rb, rc
        self.assertEqual(positions(authors, domains[0], company_b), [1])        # no fallback in B
        self.assertEqual(positions(authors, domains[3], company_b), [0, 2])

    def test_unlink_through_company_dependent_many2one(self):
        # BaseModel.unlink cleans the jsonb values of the company-dependent many2ones targeting the deleted
        # records with SQL on the holder's table: a MongoDB-stored holder (product.category property_account_*_id
        # -> account.account) has an id-only shadow table, so the storage path does it on the documents
        Review = self.env['test.mongo.review']
        company_a, company_b = self.env.company, self.env['res.company'].create({'name': 'B'})
        gone = self.env['res.currency'].create({'name': 'GON', 'symbol': 'G'})
        kept = self.env.ref('base.USD')
        review = Review.create({'name': 'r'})
        for record in (self.author_a, review):      # MongoDB holder and its PostgreSQL twin
            record.with_company(company_a).property_currency_id = gone
            record.with_company(company_b).property_currency_id = kept
        self.author_b.with_company(company_b).property_currency_id = gone
        self.env.flush_all()
        self.assertEqual(self.doc(self.author_a)['propertyCurrencyId'], {str(company_a.id): gone.id, str(company_b.id): kept.id})
        # an ir.default fallback protects the record on both stores
        self.env['ir.default'].set('test.mongo.author', 'property_currency_id', gone.id, company_id=company_b.id)
        with self.assertRaisesRegex(UserError, 'default value'):
            gone.unlink()
        self.env['ir.default'].discard_records(gone)
        # set null: the company values pointing at the deleted record become null, the others stay
        gone.unlink()
        for record in (self.author_a, review):
            self.assertFalse(record.with_company(company_a).property_currency_id)
            self.assertEqual(record.with_company(company_b).property_currency_id, kept)
        self.assertFalse(self.author_b.with_company(company_b).property_currency_id)
        self.assertEqual(self.doc(self.author_a)['propertyCurrencyId'], {str(company_a.id): None, str(company_b.id): kept.id})
        self.assertEqual(self.doc(self.author_b)['propertyCurrencyId'], {str(company_b.id): None})
        # restrict: blocked like the SQL probe, in any company
        country = self.env['res.country'].create({'name': 'Nowhere', 'code': 'NW'})
        self.author_a.with_company(company_b).property_country_id = country
        self.env.flush_all()
        with self.assertRaisesRegex(UserError, 'You cannot delete'):
            country.unlink()
        self.assertEqual(self.author_a.with_company(company_b).property_country_id, country)

    def test_company_dependent_write_keeps_fallbacks_out(self):
        # the UPDATE of a company-dependent column keeps a company's value only where it differs from its
        # ir.default fallback (the cache holds the fallback of every company read): the document must hold the
        # same map as the PostgreSQL jsonb, or a later fallback change / unlink leaves stale values behind
        Review = self.env['test.mongo.review']
        company_a = self.env.company
        company_b, company_c = (self.env['res.company'].create({'name': name}) for name in ('B', 'C'))
        companies = company_a + company_b + company_c
        eur = self.env.ref('base.EUR')
        gon = self.env['res.currency'].create({'name': 'GON', 'symbol': 'G'})
        review = Review.create({'name': 'r'})
        author = self.author_a
        for model in ('test.mongo.author', 'test.mongo.review'):
            self.env['ir.default'].set(model, 'property_currency_id', eur.id, company_id=company_a.id)

        def stored():
            self.env.flush_all()
            self.env.cr.execute("SELECT property_currency_id FROM test_mongo_review WHERE id = %s", [review.id])
            return self.doc(author).get('propertyCurrencyId'), self.env.cr.fetchone()[0]

        def compare(label):
            for company in companies:
                with self.subTest(label=label, company=company.name):
                    a, r = author.with_company(company), review.with_company(company)
                    self.assertEqual(a.property_currency_id, r.property_currency_id)
                    for value in (False, eur.id, gon.id):
                        self.assertEqual(bool(a.search([('property_currency_id', '=', value), ('id', '=', author.id)])),
                                         bool(r.search([('property_currency_id', '=', value), ('id', '=', review.id)])))

        # read every company (the cache now holds the fallbacks), then write one company's value
        for record in (author, review):
            for company in companies:
                record.with_company(company).property_currency_id
            record.with_company(company_c).property_currency_id = gon
        mongo, postgresql = stored()
        self.assertEqual(mongo, {str(company_c.id): gon.id})
        self.assertEqual(postgresql, {str(company_c.id): gon.id})
        compare('written in C')
        # writing the fallback itself stores nothing; writing False where the fallback is set stores null
        for record in (author, review):
            record.with_company(company_a).property_currency_id = eur
            record.with_company(company_b).property_currency_id = False
        mongo, postgresql = stored()
        self.assertEqual(mongo, postgresql)
        self.assertEqual(mongo, {str(company_c.id): gon.id})
        for record in (author, review):
            record.with_company(company_a).property_currency_id = False
        mongo, postgresql = stored()
        self.assertEqual(mongo, postgresql)
        self.assertEqual(mongo, {str(company_a.id): None, str(company_c.id): gon.id})
        compare('A cleared')
        # a later fallback change is followed where no value is stored
        for model in ('test.mongo.author', 'test.mongo.review'):
            self.env['ir.default'].set(model, 'property_currency_id', gon.id, company_id=company_b.id)
        self.env.invalidate_all()
        self.assertEqual(author.with_company(company_b).property_currency_id, gon)
        compare('fallback changed')
        # the unlink nulls the stored value, the fallback is discarded with the record
        self.env['ir.default'].discard_records(gon)
        gon.unlink()
        mongo, postgresql = stored()
        self.assertEqual(mongo, postgresql)
        self.assertEqual(mongo, {str(company_a.id): None, str(company_c.id): None})
        compare('after unlink')

    def test_shadow_table_relaxed_at_load(self):
        # a model opted in on an existing database keeps its NOT NULL data columns until the shadow is adapted
        Tag = self.env['test.mongo.tag']
        cr = self.env.cr
        cr.execute("ALTER TABLE test_mongo_tag ADD COLUMN legacy_code varchar NOT NULL DEFAULT 'x', "
                   "ADD COLUMN legacy_seq integer NOT NULL DEFAULT 0")
        cr.execute("ALTER TABLE test_mongo_tag ALTER COLUMN legacy_code DROP DEFAULT, ALTER COLUMN legacy_seq DROP DEFAULT")
        with self.assertRaises(psycopg2.IntegrityError), mute_logger('odoo.sql_db'):
            with cr.savepoint():
                Tag.create({'name': 'z'})
        # what load_modules runs once the registry is loaded, instead of a manual -u
        relax_registry_shadow_tables(self.env.registry, cr)
        tag = Tag.create({'name': 'z'})
        tag.flush_recordset()
        self.assertEqual(self.doc(tag)['name'], 'z')
        cr.execute("SELECT column_name, is_nullable FROM information_schema.columns WHERE table_name = 'test_mongo_tag' ORDER BY column_name")
        self.assertEqual(cr.fetchall(), [('id', 'NO'), ('legacy_code', 'YES'), ('legacy_seq', 'YES')])

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
        # a quoted literal is not a column (and a check with no column evaluates)
        self.assertEqual([cols for cons, _, cols in _check_constraints(Book) if cons.name == 'check_const'], [[]])
        # the check sees the value as stored: a partial translation keeps en_US
        self.author_a.with_context(lang='fr_FR').write({'title': 'Docteur'})
        self.env.flush_all()
        self.assertEqual(self.doc(self.author_a)['title'], {'en_US': 'Doctor', 'fr_FR': 'Docteur'})

    def test_duplicate_unique_key(self):
        Tag = self.env['test.mongo.tag']
        coll = self.store.model_collection(Tag)
        with self.assertRaises(psycopg2.errors.UniqueViolation) as cm, mute_logger('odoo.sql_db'):
            with self.env.cr.savepoint():
                Tag.create([{'name': 'z'}, {'name': 'x'}])
        # the spec index maps back to the model's UNIQUE constraint, so its message is used
        self.assertEqual(cm.exception.diag.constraint_name, 'test_mongo_tag_name_uniq')
        self.assertEqual(cm.exception.diag.table_name, 'test_mongo_tag')
        self.assertEqual(cm.exception.diag.message_detail, "Key (name)=(x) already exists.")
        self.assertEqual(Tag._sql_error_to_message(cm.exception), 'Tag names must be unique.')
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
