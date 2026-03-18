{
    'name': 'Home Finance',
    'version': '1.0',
    'category': 'Accounting',
    'description': """
        The Home Fiance module. Provides a simple way to manage your home finances, including tracking expenses, incomes, 
        and uploads from your bank statements.
    """,
    'application': True,
    'depends': ['base', 'base_setup'],
    'data': [
        'data/ir.model.access.csv',
        'data/ir.cron_data.xml',
        'views/home_finance_views.xml',
        'views/home_finance_menus.xml',
        'views/res_config_settings_views.xml',
    ],
    "demo": [
    ],
    'author': 'Mykhailo Tsurkanov',
    'license': 'LGPL-3',
}
