# Test models stored in MongoDB. Each maps onto a table of the signed spec
# (.migration/mapping_spec.json) so the real document layout is exercised.
from odoo import fields, models


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
    tag_ids = fields.Many2many('test_orm_mongodb.tag', 'product_tag_product_template_rel',
                               'product_template_id', 'product_tag_id')
    optional_incoterm_ids = fields.Many2many('test_orm_mongodb.incoterm', 'product_optional_rel', 'dest_id', 'src_id')


class Test_Orm_MongodbTag(models.Model):
    _name = 'test_orm_mongodb.tag'
    _description = 'Product tag stored in MongoDB, with junction arrays'
    _table = 'product_tag'
    _storage = 'mongodb'
    _order = 'sequence, id'

    name = fields.Char()
    sequence = fields.Integer()
    link_ids = fields.Many2many('test_orm_mongodb.pg_link', 'product_tag_product_template_rel',
                                'product_tag_id', 'product_template_id')
    incoterm_ids = fields.Many2many('test_orm_mongodb.incoterm', 'product_tag_product_product_rel',
                                    'product_tag_id', 'product_product_id', ondelete='restrict')


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
