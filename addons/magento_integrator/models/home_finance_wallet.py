from odoo import models
from odoo.addons.home_finance.constant import WALLET_ACCOUNT_TYPE, WALLET_INVEST_TYPE, WALLET_CASH_TYPE


def _resolve_wallet_type(type):
    if type == '1':
        return WALLET_ACCOUNT_TYPE
    elif type == '2':
        return WALLET_CASH_TYPE
    elif type == '3':
        return WALLET_INVEST_TYPE
    else:
        return WALLET_ACCOUNT_TYPE


class Wallet(models.Model):
    _name = "home_finance.wallet"
    _inherit = ["home_finance.wallet", "magento_integrator.id.mixin"]

    def get_wallet_by_id_and_currency(self, m2_id, currency):
        key = f"{m2_id}_{currency}"
        existing_wallet = self.search([('m2_id', '=', key)], limit=1)
        if existing_wallet:
            return existing_wallet
        else:
            # get by id from Magento and create
            wallet = self.env['magento_integrator.api'].get_wallet_by_id(str(m2_id))
            return self.create({
                'm2_id': key,
                'name': f"{wallet['title']} {currency}",
                'currency_id': self.env['res.currency'].search([('name', '=', currency)], limit=1).id,
                'type': _resolve_wallet_type(wallet['type']),
                'active': wallet['active'],
            })