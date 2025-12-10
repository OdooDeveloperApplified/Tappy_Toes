{
    'name': 'Tappy Toes Helpdesk',
    'version': '18.0.1.0',
    'category': '',
    'author': 'Tappy Toes helpdesk',
    'website': '',
    'depends': ['base', 'mail','helpdesk','helpdesk_timesheet', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/helpdesk_template_views.xml',
        'views/complaint_tags_views.xml',
        'views/helpdesk_dashboard_views.xml',
        'views/helpdesk_pivot_views.xml',
        
    ],
    
    'installable': True,
    'auto_install': False,
}