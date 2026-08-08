{
    'name': 'Tappy Late Deduction',
    'version': '18.0.1.0',
    'category': 'Human Resources',
    'author': 'Tappy Toes',
    'summary': 'Calculates late attendance deductions based on UAE Labour Law',
    'depends': ['hr_attendance', 'hr_payroll', 'l10n_ae_hr_payroll'],
    'data': [
        'data/hr_payroll_data.xml',
        'views/hr_attendance_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
