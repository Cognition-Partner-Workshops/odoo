{
    'name': 'Test Backend Neutral',
    'category': 'Hidden/Tests',
    'description': """Backend-neutral ORM test suite and its harness.

See backend_neutral_tests/CONTRACT.md at the repository root.""",
    'depends': [
        'base',
        'account',
        'hr_holidays',
        'mail',
        'point_of_sale',
        'project',
        'sale',
        'stock',
        'test_base',
        'web',
        'website',
    ],
    'data': [
        'security/ir.access.csv',
    ],
    'author': 'Odoo S.A.',
    'license': 'LGPL-3',
}
