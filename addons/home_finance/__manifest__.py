{
    'name': 'Home Finance',
    'version': '1.0',
    'category': 'Accounting',
    'description': """
        The Home Fiance module. Provides a simple way to manage your home finances, including tracking expenses, incomes, 
        and uploads from your bank statements.
    """,
    'application': True,
    'depends': ['base'],
    'data': [
        'data/ir.model.access.csv',
        'views/home_finance_views.xml',
        'wizard/home_finance_wizard_views.xml',
        'views/home_finance_menus.xml',
    ],
    "demo": [
    ],
    'author': 'Mykhailo Tsurkanov',
    'license': 'LGPL-3',
}
