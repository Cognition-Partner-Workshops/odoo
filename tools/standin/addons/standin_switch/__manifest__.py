{
    'name': 'Stand-in per-request source | reads | writes switch',
    'summary': 'Server-wide (--load) routing for the stand-in production clone; never installed',
    'version': '0.1',
    'depends': ['account'],
    'installable': False,
    'post_load': 'postLoad',
    'license': 'LGPL-3',
}
