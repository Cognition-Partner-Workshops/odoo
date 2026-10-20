# Part of Odoo. See LICENSE file for full copyright and licensing details.
"""Models exercising the MongoDB storage path.  Their ``_mongodb_spec`` entries
use the mapping-spec shapes of ``.migration/mapping_spec.json``: a root
collection keyed by ``_id`` with camelCase targets and a ``decimal`` field, a
many2many relation embedded as an array of the owning document, a many2many
relation kept as its own collection, and a child model embedded as an array."""

from odoo import api, fields, models


def _spec(table, collection, fields_, embeds=(), key=None, indexes=()):
    return {
        'collection': collection, 'root_table': table,
        'key': key or {'source': ['id'], 'target': '_id'},
        'fields': [{'source': s, 'target': t, 'bson_type': b} for s, t, b in fields_],
        'embeds': list(embeds), 'indexes': list(indexes),
    }


def _embed(array_path, child_table, parent_key, key_source, key_target, fields_=()):
    return {
        'array_path': array_path, 'child_table': child_table, 'parent_key': [parent_key], 'parent_ref': ['id'],
        'key': {'source': [key_source], 'target': key_target},
        'fields': [{'source': s, 'target': t, 'bson_type': b} for s, t, b in fields_],
    }


class TestMongoTag(models.Model):
    _name = 'test.mongo.tag'
    _description = 'MongoDB test tag'
    _storage = 'mongodb'
    _order = 'name, id'
    _mongodb_spec = _spec('test_mongo_tag', 'testMongoTag', [('name', 'name', 'string')],
                          indexes=[{'keys': [['name', 1]], 'unique': True}])

    name = fields.Char(required=True)
    _name_uniq = models.Constraint('UNIQUE (name)', 'Tag names must be unique.')
    author_ids = fields.Many2many('test.mongo.author', 'test_mongo_author_tag_rel', 'tag_id', 'author_id')

    def init(self):
        # DDL on a data column, like the sequence/analytic mixins do; the id shadow has none
        self.env.cr.execute("CREATE INDEX IF NOT EXISTS test_mongo_tag_name_index ON test_mongo_tag (name)")


class TestMongoAuthor(models.Model):
    _name = 'test.mongo.author'
    _description = 'MongoDB test author'
    _storage = 'mongodb'
    _order = 'rating desc, id'
    _parent_store = True
    _mongodb_spec = _spec(
        'test_mongo_author', 'testMongoAuthor',
        [('name', 'name', 'string'), ('rating', 'rating', 'decimal'), ('score', 'score', 'double'),
         ('partner_id', 'partnerId', 'int'), ('birthday', 'birthday', 'date'), ('title', 'title', 'object'),
         ('state', 'state', 'string'), ('parent_id', 'parentId', 'int'), ('parent_path', 'parentPath', 'string')],
        embeds=[_embed('tagRel', 'test_mongo_author_tag_rel', 'author_id', 'tag_id', 'tagId')],
        indexes=[{'keys': [['partnerId', 1]]}, {'keys': [['rating', -1], ['_id', 1]]}],
    )

    name = fields.Char(required=True)
    title = fields.Char(translate=True)
    # evaluated on the translations as stored, not on a partial update
    _check_title = models.Constraint("CHECK (title IS NULL OR title ? 'en_US')", 'A title needs an English value.')
    rating = fields.Float(digits=(16, 2))
    score = fields.Float()
    active = fields.Boolean(default=True)
    birthday = fields.Date()
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default='draft')
    partner_id = fields.Many2one('res.partner', ondelete='set null')
    parent_id = fields.Many2one('test.mongo.author', ondelete='cascade')
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many('test.mongo.author', 'parent_id')
    tag_ids = fields.Many2many('test.mongo.tag', 'test_mongo_author_tag_rel', 'author_id', 'tag_id')
    book_ids = fields.One2many('test.mongo.book', 'author_id')
    book_count = fields.Integer(compute='_compute_book_count', store=True)

    @api.depends('book_ids')
    def _compute_book_count(self):
        for author in self:
            author.book_count = len(author.book_ids)


class TestMongoBook(models.Model):
    _name = 'test.mongo.book'
    _description = 'MongoDB test book'
    _storage = 'mongodb'
    _order = 'author_id, name, id'
    _mongodb_spec = [_spec(
        'test_mongo_book', 'testMongoBook',
        [('name', 'name', 'string'), ('author_id', 'authorId', 'int'), ('price', 'price', 'decimal'),
         ('pages', 'pages', 'int'), ('published', 'published', 'date')],
        embeds=[_embed('chapter', 'test_mongo_chapter', 'book_id', 'id', 'id',
                       [('name', 'name', 'string'), ('sequence', 'sequence', 'int')])],
    ), _spec(
        # the relation table as its own collection, like the spec's composite-key relations
        'test_mongo_book_tag_rel', 'testMongoBookTagRel',
        [('book_id', 'bookId', 'int'), ('tag_id', 'tagId', 'int')],
        key={'source': ['book_id', 'tag_id'], 'target': ['bookId', 'tagId']},
    )]

    name = fields.Char(required=True)
    author_id = fields.Many2one('test.mongo.author', required=True, ondelete='cascade')
    price = fields.Float(digits=(16, 2))
    pages = fields.Integer()
    _check_pages = models.Constraint('CHECK (pages >= 0)', 'Pages must be positive.')
    # no column, and a literal spelling a column name
    _check_const = models.Constraint("CHECK ('pages' <> '')", 'Always true.')
    published = fields.Datetime()
    chapter_ids = fields.One2many('test.mongo.chapter', 'book_id')
    tag_ids = fields.Many2many('test.mongo.tag', 'test_mongo_book_tag_rel', 'book_id', 'tag_id')
    review_ids = fields.One2many('test.mongo.review', 'book_id')


class TestMongoChapter(models.Model):
    _name = 'test.mongo.chapter'
    _description = 'MongoDB test chapter (embedded in the book document)'
    _storage = 'mongodb'
    _order = 'sequence, id'
    _mongodb_spec = TestMongoBook._mongodb_spec

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    book_id = fields.Many2one('test.mongo.book', required=True, ondelete='cascade')


class TestMongoVariant(models.Model):
    _name = 'test.mongo.variant'
    _description = 'MongoDB test variant (_inherits a MongoDB book)'
    _storage = 'mongodb'
    _inherits = {'test.mongo.book': 'book_id'}
    _order = 'name, code'
    _mongodb_spec = _spec('test_mongo_variant', 'testMongoVariant',
                          [('book_id', 'bookId', 'int'), ('code', 'code', 'string')])

    book_id = fields.Many2one('test.mongo.book', required=True, ondelete='cascade')
    code = fields.Char()


class TestMongoReview(models.Model):
    """ Stays on PostgreSQL; its many2one fields point into MongoDB-stored models. """
    _name = 'test.mongo.review'
    _description = 'PostgreSQL test review of a MongoDB book'
    _order = 'book_id, id'
    # the spec maps a relation table whose both sides stay on PostgreSQL (a later wave): it must not move
    _mongodb_spec = _spec('test_mongo_review_partner_rel', 'testMongoReviewPartnerRel',
                          [('review_id', 'reviewId', 'int'), ('partner_id', 'partnerId', 'int')],
                          key={'source': ['review_id', 'partner_id'], 'target': ['reviewId', 'partnerId']})

    name = fields.Char()
    book_id = fields.Many2one('test.mongo.book', ondelete='cascade')
    author_id = fields.Many2one('test.mongo.author', ondelete='restrict')
    tag_ids = fields.Many2many('test.mongo.tag', 'test_mongo_review_tag_rel', 'review_id', 'tag_id')
    partner_ids = fields.Many2many('res.partner', 'test_mongo_review_partner_rel', 'review_id', 'partner_id')
