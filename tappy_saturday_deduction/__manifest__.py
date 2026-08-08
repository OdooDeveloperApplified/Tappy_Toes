{
    'name': 'Tappy Saturday Deduction',
    'version': '18.0.1.0',
    'category': 'Human Resources',
    'author': 'Tappy Toes',
    'summary': 'Calculates salary deductions for absent Saturdays based on the Rota',
    'depends': ['hr_attendance', 'hr_payroll', 'l10n_ae_hr_payroll', 'tappy_saturday'],
    'data': [
        'data/hr_payroll_data.xml',
    ],
    'installable': True,
    'auto_install': False,
}
