{
    'name': 'Tappy Toes Attendance',
    'version': '18.0.1.0',
    'category': '',
    'author': 'Tappy Toes',
    'website': '',
    'depends': ['base', 'mail','hr_attendance', 'web','hr'],
    'data': [
        'security/ir.model.access.csv',
        # 'views/hr_attendance_views.xml',
        'views/full_attendance_wizard_views.xml',
        
        
    ],
    'installable': True,
    'auto_install': False,
}