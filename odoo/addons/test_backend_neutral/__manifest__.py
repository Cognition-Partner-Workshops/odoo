{
    'name': 'Test Backend Neutral',
    'category': 'Hidden/Tests',
    'description': """Backend-neutral ORM test suite and its harness.

See backend_neutral_tests/CONTRACT.md at the repository root.""",
    'depends': ['base', 'mail', 'stock', 'website'],
    'data': [
        'security/ir.access.csv',
    ],
    'author': 'Odoo S.A.',
    'license': 'LGPL-3',
}
