{
    'name': 'Tappy Toes CRM',
    'version': '18.0.1.0',
    'category': '',
    'author': 'Tappy Toes',
    'website': '',
    'depends': ['base', 'mail','web','crm'],
    'data': [
        'security/ir.model.access.csv',
        # 'views/visa_renewal_views.xml',
        'views/crm_template_views.xml',
        'views/crm_dashboard_views.xml',
        'views/customer_status_views.xml',
        'views/parent_concern_views.xml',
        'views/qualified_lost_reason_views.xml',
        
    ],
    # 'assets': {
    #     'web.assets_backend': [
    #         'tappy_toes/static/src/js/helpdesk_dashboard.js',
    #     ],
    #     'web.assets_qweb': [
    #         'tappy_toes/static/src/xml/helpdesk_dashboard_template.xml',
    #     ],
    # },
    'installable': True,
    'auto_install': False,
}