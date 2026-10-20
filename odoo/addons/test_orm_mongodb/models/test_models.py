# Part of Odoo. See LICENSE file for full copyright and licensing details.
"""Models exercising the MongoDB storage path.  Their ``_mongodb_spec`` entries
use the mapping-spec shapes of ``.migration/mapping_spec.json``: a root
collection keyed by ``_id`` with camelCase targets and a ``decimal`` field, a
many2many relation embedded as an array of the owning document, a many2many
relation kept as its own collection, and a child model embedded as an array."""

from odoo import api, fields, models
from odoo.tools import SQL


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
         ('state', 'state', 'string'), ('parent_id', 'parentId', 'int'), ('parent_path', 'parentPath', 'string'),
         ('property_note', 'propertyNote', 'object'), ('property_currency_id', 'propertyCurrencyId', 'object'), ('property_country_id', 'propertyCountryId', 'object'),
         ('book_properties_definition', 'bookPropertiesDefinition', 'object')],
        embeds=[_embed('tagRel', 'test_mongo_author_tag_rel', 'author_id', 'tag_id', 'tagId'),
                _embed('coauthorRel', 'test_mongo_coauthor_rel', 'author_id', 'coauthor_id', 'coauthorId'),
                # a PostgreSQL model's relation held by this document (product.template.taxes_id in accountTax)
                _embed('reviewRel', 'test_mongo_author_review_rel', 'author_id', 'review_id', 'reviewId')],
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
    property_note = fields.Char(company_dependent=True)
    # company-dependent many2one (product.category property_account_*_id), searched through dotted paths
    property_currency_id = fields.Many2one('res.currency', company_dependent=True)
    property_country_id = fields.Many2one('res.country', company_dependent=True, ondelete='restrict')
    book_properties_definition = fields.PropertiesDefinition()
    # a self-referential relation table embedded on the owning side's documents, read from both sides
    coauthor_ids = fields.Many2many('test.mongo.author', 'test_mongo_coauthor_rel', 'author_id', 'coauthor_id')
    coauthor_of_ids = fields.Many2many('test.mongo.author', 'test_mongo_coauthor_rel', 'coauthor_id', 'author_id')
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
         ('pages', 'pages', 'int'), ('published', 'published', 'date'), ('archived', 'archived', 'bool'),
         ('book_properties', 'bookProperties', 'object'),
         ('chapter_properties_definition', 'chapterPropertiesDefinition', 'object')],
        embeds=[_embed('chapter', 'test_mongo_chapter', 'book_id', 'id', 'id',
                       [('name', 'name', 'string'), ('sequence', 'sequence', 'int'), ('subtitle', 'subtitle', 'object'),
                        ('meta', 'meta', 'object'), ('chapter_properties', 'chapterProperties', 'object')]),
                # child rows keyed by a natural composite key, with their id as a plain field
                {'array_path': 'edition', 'child_table': 'test_mongo_edition', 'parent_key': ['book_id'], 'parent_ref': ['id'],
                 'key': {'source': ['lang', 'year'], 'target': ['lang', 'year']},
                 'fields': [{'source': 'id', 'target': 'id', 'bson_type': 'int'}, {'source': 'note', 'target': 'note', 'bson_type': 'string'}]}],
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
    archived = fields.Boolean()
    # non-stored, with an SQL form: the domain optimizer keeps its conditions (account.report.active)
    active = fields.Boolean(compute='_compute_active', compute_sql='_compute_sql_active', compute_sudo=False)
    chapter_ids = fields.One2many('test.mongo.chapter', 'book_id')
    tag_ids = fields.Many2many('test.mongo.tag', 'test_mongo_book_tag_rel', 'book_id', 'tag_id')
    review_ids = fields.One2many('test.mongo.review', 'book_id')
    edition_ids = fields.One2many('test.mongo.edition', 'book_id')
    book_properties = fields.Properties(definition='author_id.book_properties_definition')
    chapter_properties_definition = fields.PropertiesDefinition()
    # relation table mapped by the spec but owned by the review's (later) unit: served by PostgreSQL until then
    review_m2m_ids = fields.Many2many('test.mongo.review', 'test_mongo_review_book_rel', 'book_id', 'review_id')

    @api.depends('archived')
    def _compute_active(self):
        for book in self:
            book.active = not book.archived

    def _compute_sql_active(self, table):
        return SQL("NOT COALESCE(%s, FALSE)", table.archived)

    # non-stored with an SQL form, named by an _order (account.account code_path); NULL when unpublished
    shelf = fields.Char(compute='_compute_shelf', compute_sql='_compute_sql_shelf', compute_sudo=True)

    @api.depends('published', 'archived')
    def _compute_shelf(self):
        for book in self:
            book.shelf = str(book.published.year) if book.published else '' if book.archived else False

    def _compute_sql_shelf(self, table):
        return SQL("CASE WHEN %s IS NOT NULL THEN EXTRACT(YEAR FROM %s)::text WHEN %s THEN '' END",
                   table.published, table.published, table.archived)

    half_price = fields.Float(digits=(16, 2), compute='_compute_half_price', compute_sql='_compute_sql_half_price', compute_sudo=True)

    @api.depends('price')
    def _compute_half_price(self):
        for book in self:
            book.half_price = book.price / 2

    def _compute_sql_half_price(self, table):
        return SQL("%s / 2", table.price)


class TestMongoChapter(models.Model):
    _name = 'test.mongo.chapter'
    _description = 'MongoDB test chapter (embedded in the book document)'
    _storage = 'mongodb'
    _order = 'sequence, id'
    _mongodb_spec = TestMongoBook._mongodb_spec

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    book_id = fields.Many2one('test.mongo.book', required=True, ondelete='cascade')
    # jsonb columns of embedded records, written through the grouped element update
    # (account.reconcile.model.line.analytic_distribution is a Json field)
    subtitle = fields.Char(translate=True)
    meta = fields.Json()
    chapter_properties = fields.Properties(definition='book_id.chapter_properties_definition')


class TestMongoEdition(models.Model):
    _name = 'test.mongo.edition'
    _description = 'MongoDB test edition (embedded in the book document under a composite key)'
    _storage = 'mongodb'
    _order = 'year, id'
    _mongodb_spec = TestMongoBook._mongodb_spec

    book_id = fields.Many2one('test.mongo.book', required=True, ondelete='cascade')
    lang = fields.Char(required=True)
    year = fields.Integer(required=True)
    note = fields.Char()

    _book_lang_year_uniq = models.Constraint('unique (book_id, lang, year)', 'One edition per language and year.')


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
    # the spec maps this (later-wave) model's collection, with the tag relation embedded in it, and two
    # standalone relation collections it owns: none moves before the model does, whether the other side
    # is PostgreSQL (partners) or already MongoDB-stored (books, tags)
    _mongodb_spec = [
        _spec('test_mongo_review', 'testMongoReview', [('name', 'name', 'string'), ('book_id', 'bookId', 'int')],
              embeds=[_embed('tagRel', 'test_mongo_review_tag_rel', 'review_id', 'tag_id', 'tagId')]),
        _spec('test_mongo_review_partner_rel', 'testMongoReviewPartnerRel',
              [('review_id', 'reviewId', 'int'), ('partner_id', 'partnerId', 'int')],
              key={'source': ['review_id', 'partner_id'], 'target': ['reviewId', 'partnerId']}),
        _spec('test_mongo_review_book_rel', 'testMongoReviewBookRel',
              [('review_id', 'reviewId', 'int'), ('book_id', 'bookId', 'int')],
              key={'source': ['review_id', 'book_id'], 'target': ['reviewId', 'bookId']}),
    ]

    name = fields.Char()
    book_id = fields.Many2one('test.mongo.book', ondelete='cascade')
    author_id = fields.Many2one('test.mongo.author', ondelete='restrict')
    # the PostgreSQL twin of test.mongo.author.property_currency_id, for exact-equality checks of searches
    property_currency_id = fields.Many2one('res.currency', company_dependent=True)
    # the PostgreSQL twins of test.mongo.chapter's jsonb columns
    subtitle = fields.Char(translate=True)
    meta = fields.Json()
    chapter_properties = fields.Properties(definition='book_id.chapter_properties_definition')
    tag_ids = fields.Many2many('test.mongo.tag', 'test_mongo_review_tag_rel', 'review_id', 'tag_id')
    partner_ids = fields.Many2many('res.partner', 'test_mongo_review_partner_rel', 'review_id', 'partner_id')
    book_ids = fields.Many2many('test.mongo.book', 'test_mongo_review_book_rel', 'review_id', 'book_id')
    author_ids = fields.Many2many('test.mongo.author', 'test_mongo_author_review_rel', 'review_id', 'author_id')
    archived_book_ids = fields.Many2many('test.mongo.book', 'test_mongo_review_book_rel', 'review_id', 'book_id',
                                         context={'active_test': False})
    # relations carrying a comodel domain (product.template.taxes_id: domain on type_tax_use), on a PostgreSQL
    # relation table and on one embedded in the comodel's documents
    cheap_book_ids = fields.Many2many('test.mongo.book', 'test_mongo_review_book_rel', 'review_id', 'book_id',
                                      domain=[('price', '<', 15)])
    rated_author_ids = fields.Many2many('test.mongo.author', 'test_mongo_author_review_rel', 'review_id', 'author_id',
                                        domain=[('rating', '>', 4)])
