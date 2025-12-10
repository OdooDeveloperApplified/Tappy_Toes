{
    'name': 'Tappy Toes Payroll',
    'version': '18.0.1.0',
    'category': '',
    'author': 'Tappy Toes',
    'website': '',
    'depends': ['base', 'mail','hr_payroll', 'web','hr','l10n_ae_hr_payroll'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_contract_template_views.xml',
        
        
    ],
    'installable': True,
    'auto_install': False,
}