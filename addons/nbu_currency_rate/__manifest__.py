{
    'name': 'Currency Rate Update — NBU (Ukraine)',
    'version': '19.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Import currency rates from the National Bank of Ukraine (NBU) — free API, no key required',
    'description': """
Currency Rate Update — National Bank of Ukraine (NBU)
=====================================================

Features
--------
* Uses the **free, public NBU REST API** — no API key, no registration.
* Endpoint:  ``https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json``
* Supports **all 60+ currencies** published by NBU (USD, EUR, PLN, GBP …).
* Base currency is **UAH** (hryvnia) — rates are expressed as "how many UAH per 1 unit of foreign currency".
* Works with Odoo's built-in scheduler: daily / weekly / monthly automatic updates.
* Compatible with Odoo 19.0.
    """,
    'author': 'Mykhailo Tsurkanov',
    'license': 'LGPL-3',
    'depends': ['home_finance'],
    'data': [
        'data/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/res_company_views.xml',
        'views/nbu_currency_rate_updater_wizard_views.xml',
        'views/nbu_currency_rate_menus.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
