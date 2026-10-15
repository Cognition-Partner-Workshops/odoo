{
    'name': 'Test ORM MongoDB storage',
    'category': 'Hidden/Tests',
    'description': """Models opted into the MongoDB storage path (_storage = 'mongodb') and their PostgreSQL neighbours, to test CRUD, search, read_group and cross-store relations.""",
    'depends': ['base'],
    'data': [
        'security/ir.access.csv',
    ],
    'author': 'Odoo S.A.',
    'license': 'LGPL-3',
}
