{
    'name': 'Tappy Toes Sandwich Leave',
    'version': '18.0.1.0',
    'category': 'Human Resources',
    'summary': 'Applies sandwich rule deductions on payslips',
    'author': 'Tappy Toes',
    'depends': ['hr_payroll', 'hr_attendance', 'l10n_ae_hr_payroll'],
    'data': [
        'data/hr_payroll_data.xml',
        'views/hr_payslip_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
