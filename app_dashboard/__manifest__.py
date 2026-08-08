{
    'name': 'Accounting Dashboard',
    'version': '18.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Custom Accounting Dashboard',
    'author' : 'Applified',
    'depends': ['account', 'spreadsheet_dashboard'],
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            "https://cdn.jsdelivr.net/npm/chart.js",
            "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css",
            'app_dashboard/static/src/css/dashboard.css',
            'app_dashboard/static/src/css/style.scss',
            'app_dashboard/static/src/js/dashboard.js',
            'app_dashboard/static/src/xml/dashboard_templates.xml',
            'app_dashboard/static/src/js/consolidated_dashboard.js',
            'app_dashboard/static/src/xml/consolidated_dashboard.xml',
        ],
    },
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}
