# Test models stored in MongoDB. Each maps onto a table of the signed spec
# (.migration/mapping_spec.json) so the real document layout is exercised.
from odoo import fields, models
from odoo.tools import SQL
from odoo.tools.translate import html_translate


class Test_Orm_MongodbIncoterm(models.Model):
    _name = 'test_orm_mongodb.incoterm'
    _description = 'Incoterm stored in MongoDB'
    _table = 'account_incoterms'
    _storage = 'mongodb'

    code = fields.Char()
    name = fields.Char(translate=True)
    active = fields.Boolean(default=True)
    optional_link_ids = fields.Many2many('test_orm_mongodb.pg_link', 'product_optional_rel', 'src_id', 'dest_id')


class Test_Orm_MongodbLock_Exception(models.Model):
    _name = 'test_orm_mongodb.lock_exception'
    _description = 'Lock exception stored in MongoDB'
    _table = 'account_lock_exception'
    _storage = 'mongodb'
    _shadow_columns = ('company_id',)

    company_id = fields.Many2one('res.company', required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users')
    reason = fields.Char()
    lock_date_field = fields.Selection([('fiscalyear_lock_date', "Global"), ('tax_lock_date', "Tax")])
    lock_date = fields.Date()
    company_lock_date = fields.Date()
    end_datetime = fields.Datetime()
    active = fields.Boolean(default=True)


class Test_Orm_MongodbStorage_Category(models.Model):
    _name = 'test_orm_mongodb.storage_category'
    _description = 'Storage category stored in MongoDB'
    _table = 'stock_storage_category'
    _storage = 'mongodb'

    name = fields.Char()
    company_id = fields.Many2one('res.company')
    allow_new_product = fields.Selection([('empty', "Empty"), ('same', "Same"), ('mixed', "Mixed")])
    max_weight = fields.Float(digits=(16, 4))
    capacity_ids = fields.One2many('test_orm_mongodb.storage_capacity', 'storage_category_id')


class Test_Orm_MongodbStorage_Capacity(models.Model):
    _name = 'test_orm_mongodb.storage_capacity'
    _description = 'Storage capacity stored in MongoDB'
    _table = 'stock_storage_category_capacity'
    _storage = 'mongodb'

    storage_category_id = fields.Many2one('test_orm_mongodb.storage_category', ondelete='cascade')
    quantity = fields.Float()
    company_id = fields.Many2one(related='storage_category_id.company_id')


class Test_Orm_MongodbReport_Expression(models.Model):
    _name = 'test_orm_mongodb.report_expression'
    _description = 'Report expression stored in MongoDB (unique key in the spec)'
    _table = 'account_report_expression'
    _storage = 'mongodb'

    report_line_id = fields.Integer()
    label = fields.Char()
    formula = fields.Char()


class Test_Orm_MongodbPg_Link(models.Model):
    _name = 'test_orm_mongodb.pg_link'
    _description = 'PostgreSQL model referencing MongoDB models'

    name = fields.Char()
    incoterm_id = fields.Many2one('test_orm_mongodb.incoterm', ondelete='cascade')
    lock_exception_id = fields.Many2one('test_orm_mongodb.lock_exception', ondelete='set null')
    tag_id = fields.Many2one('test_orm_mongodb.tag', ondelete='set null')
    restrict_tag_id = fields.Many2one('test_orm_mongodb.tag', ondelete='restrict')
    attribute_value_id = fields.Many2one('test_orm_mongodb.attribute_value', ondelete='set null')
    tag_ids = fields.Many2many('test_orm_mongodb.tag', 'product_tag_product_template_rel',
                               'product_template_id', 'product_tag_id')
    optional_incoterm_ids = fields.Many2many('test_orm_mongodb.incoterm', 'product_optional_rel', 'dest_id', 'src_id')


class Test_Orm_MongodbWarehouse(models.Model):
    _name = 'test_orm_mongodb.warehouse'
    _description = 'Warehouse stored in MongoDB, referencing a PostgreSQL model'
    _table = 'stock_warehouse'
    _storage = 'mongodb'

    name = fields.Char()
    buy_pull_id = fields.Many2one('test_orm_mongodb.pg_link')


class Test_Orm_MongodbTag(models.Model):
    _name = 'test_orm_mongodb.tag'
    _description = 'Product tag stored in MongoDB, with junction arrays'
    _table = 'product_tag'
    _storage = 'mongodb'
    _order = 'sequence, id'
    _shadow_relations = ('incoterm_ids',)

    name = fields.Char()
    sequence = fields.Integer()
    link_ids = fields.Many2many('test_orm_mongodb.pg_link', 'product_tag_product_template_rel',
                                'product_tag_id', 'product_template_id')
    incoterm_ids = fields.Many2many('test_orm_mongodb.incoterm', 'product_tag_product_product_rel',
                                    'product_tag_id', 'product_product_id', ondelete='restrict')
    # relation table outside the signed spec, so it stays in PostgreSQL
    partner_ids = fields.Many2many('res.partner', 'test_orm_mongodb_tag_partner_rel', 'tag_id', 'partner_id')
    is_even = fields.Boolean(compute='_compute_is_even', compute_sql='_compute_sql_is_even')
    double_sequence = fields.Integer(compute='_compute_double_sequence')

    def _compute_is_even(self):
        for tag in self:
            tag.is_even = tag.id % 2 == 0

    def _compute_sql_is_even(self, table):
        return SQL("%s %% 2 = 0", table.id)

    def _compute_double_sequence(self):
        for tag in self:
            tag.double_sequence = 2 * tag.sequence


class Test_Orm_MongodbAttribute(models.Model):
    _name = 'test_orm_mongodb.attribute'
    _description = 'Product attribute stored in MongoDB, with embedded values'
    _table = 'product_attribute'
    _storage = 'mongodb'
    _order = 'sequence, id'

    name = fields.Char(translate=True)
    sequence = fields.Integer()
    value_ids = fields.One2many('test_orm_mongodb.attribute_value', 'attribute_id')


class Test_Orm_MongodbAttributeValue(models.Model):
    _name = 'test_orm_mongodb.attribute_value'
    _description = 'Product attribute value embedded in its attribute document'
    _table = 'product_attribute_value'
    _storage = 'mongodb'
    _order = 'sequence, id'

    attribute_id = fields.Many2one('test_orm_mongodb.attribute', required=True, ondelete='cascade')
    name = fields.Char(translate=True)
    sequence = fields.Integer()
    html_color = fields.Char()
    default_extra_price = fields.Float()
    is_custom = fields.Boolean()


class Test_Orm_MongodbFiscalPosition(models.Model):
    _name = 'test_orm_mongodb.fiscal_position'
    _description = 'Fiscal position stored in MongoDB, with embedded account mappings'
    _table = 'account_fiscal_position'
    _storage = 'mongodb'

    name = fields.Char(translate=True)
    account_ids = fields.One2many('test_orm_mongodb.fiscal_position_account', 'position_id')


class Test_Orm_MongodbFiscalPositionAccount(models.Model):
    _name = 'test_orm_mongodb.fiscal_position_account'
    _description = 'Account mapping embedded in its fiscal position, unique per position'
    _table = 'account_fiscal_position_account'
    _storage = 'mongodb'

    position_id = fields.Many2one('test_orm_mongodb.fiscal_position', required=True, ondelete='cascade')
    account_src_id = fields.Integer()
    account_dest_id = fields.Integer()


class Test_Orm_MongodbCategory(models.Model):
    _name = 'test_orm_mongodb.category'
    _description = 'Category stored in MongoDB, with a parent path and company-dependent fields'
    _table = 'product_category'
    _storage = 'mongodb'
    _parent_store = True

    name = fields.Char(translate=True)
    parent_id = fields.Many2one('test_orm_mongodb.category', index=True, ondelete='cascade')
    parent_path = fields.Char(index=True)
    property_cost_method = fields.Selection([('standard', 'Standard'), ('average', 'Average')], company_dependent=True)
    property_stock_journal = fields.Many2one('res.partner', company_dependent=True, ondelete='set null')
    property_account_income_categ_id = fields.Many2one('res.partner', company_dependent=True, ondelete='restrict')
    parity = fields.Char(compute='_compute_parity', compute_sql='_compute_sql_parity')

    def _compute_parity(self):
        for category in self:
            category.parity = 'even' if category.id % 2 == 0 else False

    def _compute_sql_parity(self, table):
        return SQL("CASE WHEN %s %% 2 = 0 THEN 'even' END", table.id)


class Test_Orm_MongodbTemplate(models.Model):
    _name = 'test_orm_mongodb.template'
    _description = 'Product template stored in MongoDB'
    _table = 'product_template'
    _storage = 'mongodb'
    _order = 'name, id'

    name = fields.Char(translate=True, required=True)
    description = fields.Html(translate=html_translate)


class Test_Orm_MongodbVariant(models.Model):
    _name = 'test_orm_mongodb.variant'
    _description = 'Product variant stored in MongoDB, inheriting its template'
    _table = 'product_product'
    _storage = 'mongodb'
    _inherits = {'test_orm_mongodb.template': 'product_tmpl_id'}

    product_tmpl_id = fields.Many2one('test_orm_mongodb.template', required=True, ondelete='cascade')
    default_code = fields.Char()
