{
    'name': 'Magento Integrator',
    'version': '19.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Provide interface for REST API calls to Magento instances. Specifically for Home Finance models',
    'description': """
TODO
    """,
    'author': 'Mykhailo Tsurkanov',
    'license': 'LGPL-3',
    'depends': ['home_finance'],
    'data': [
        'data/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/magento_integrator_runner_wizard_views.xml',
        'views/magento_integrator_menus.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
