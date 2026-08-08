{
    'name': 'App Split Expense',
    'version': '18.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Split Vendor Bills accross multiple companies automatically',
    'description': """
        This module allows users to split a Vendor Bill equally across multiple selected companies.
        It creates automated draft Vendor Bills in the target companies.
    """,
    'author': 'Applified',
    'website': 'https://applified.co.in',
    'depends': ['base','account'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/account_move_views.xml'
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3'
}