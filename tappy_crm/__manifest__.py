{
    'name': 'Tappy Toes CRM',
    'version': '18.0.1.0',
    'category': '',
    'author': 'Tappy Toes',
    'website': '',
    'depends': ['base', 'mail','web','crm'],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_template_views.xml',
        'views/crm_dashboard_views.xml',
        'views/customer_status_views.xml',
        'views/qualified_lost_reason_views.xml',
        
    ],
   
    'installable': True,
    'auto_install': False,
}