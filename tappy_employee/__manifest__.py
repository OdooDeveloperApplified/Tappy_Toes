{
    'name': 'Tappy Toes Employee Management',
    'version': '18.0.1.0',
    'category': '',
    'author': 'Tappy Toes Employee',
    'website': '',
    'depends': ['base', 'mail', 'web','hr' ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_views.xml',
        'views/visa_renewal_views.xml',
        'views/visa_type_views.xml',
    ],
   
    'installable': True,
    'auto_install': False,
}