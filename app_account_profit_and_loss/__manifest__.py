{
    'name': 'Account Category P&L',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Custom P&L per Income-Expense category',
    'description': 'Shows category-wise Income, Expense, and Gross Profit side by side.',
    'depends': ['account','account_reports'],
    'data': [
        'security/security.xml',
        'data/profit_and_loss.xml',
        'views/profit_and_loss_view.xml',
        'views/account_move_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'app_account_profit_and_loss/static/src/xml/filter_extra_options_custom.xml',
            'app_account_profit_and_loss/static/src/xml/filter.xml',
            'app_account_profit_and_loss/static/src/js/account_report_extend.js',
            'app_account_profit_and_loss/static/src/scss/image_zoom.scss',
            'app_account_profit_and_loss/static/src/js/image_field_viewer.js',
            'app_account_profit_and_loss/static/src/xml/image_field_viewer.xml',
            'app_account_profit_and_loss/static/src/js/hide_delete_button.js',
        ],
    },
    'installable': True,
    'application': False,
}
