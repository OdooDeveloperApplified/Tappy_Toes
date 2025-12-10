{
    'name': 'Tappy Toes Accounts',
    'version': '18.0.1.0',
    'category': '',
    'author': 'Tappy Toes',
    'website': '',
    'depends': ['base', 'mail','account'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move_template_views.xml',
        'reports/invoice_report_inherit.xml',
        
        
    ],
    'installable': True,
    'auto_install': False,
}