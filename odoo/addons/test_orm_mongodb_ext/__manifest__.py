{
    'name': 'Test ORM MongoDB storage: foreign-addon fields',
    'category': 'Hidden/Tests',
    'description': """Declares a Many2many on a model opted into MongoDB from another addon: the field must travel with the document (id array), not a PostgreSQL relation table.""",
    'depends': ['test_orm_mongodb'],
    'author': 'Odoo S.A.',
    'license': 'LGPL-3',
}
