import logging

from odoo import models, _
from odoo.exceptions import UserError
from odoo.addons.home_finance.constant import MOVEMENT_TYPE_INCOME, MOVEMENT_TYPE_EXPENSE

_logger = logging.getLogger(__name__)

CATEGORY_KEY = 'cf_item_id'
PROJECT_KEY = 'project_id'
WALLET_KEY = 'storage_id'
TYPE_KEY = 'type_id'

class Transaction(models.Model):
    _name = "home_finance.transaction"
    _inherit = ["home_finance.transaction", "magento_integrator.id.mixin"]

    def import_transactions(self):
        transactions = self.env['magento_integrator.api'].get_transaction_all()
        resolved_wallets = {}
        for item in transactions.get('items', []):
            #1. search by magento_id if find - skip
            existing_transaction = self.search([('m2_id', '=', item['id'])])
            if existing_transaction:
                continue

            #2. search category and project by magento_id
            category = self.env['home_finance.category'].search([('m2_id', '=', item[CATEGORY_KEY])], limit=1)
            if not category:
                raise UserError(_("Category not found for transaction with ID: %s", item['id']))
            project = self.env['home_finance.project'].search([('m2_id', '=', item[PROJECT_KEY])], limit=1) \
                if item.get(PROJECT_KEY) else None

            #3. search wallet by key
            wallet_key = f"{item[WALLET_KEY]}_{item['currency']}"
            if wallet_key in resolved_wallets:
                wallet = resolved_wallets[wallet_key]
            else:
                wallet = self.env['home_finance.wallet'].get_wallet_by_id_and_currency(item[WALLET_KEY], item['currency'])
                resolved_wallets[wallet_key] = wallet
            if not wallet:
                raise UserError(_("Wallet not found for transaction with ID: %s", item['id']))

            #4. create transaction
            self.create({
                'm2_id': item['id'],
                'period': item['registration_time'],
                'amount': item['total'],
                'category_id': category.id,
                'project_id': project.id if project else None,
                'wallet_id': wallet.id,
                'type': MOVEMENT_TYPE_EXPENSE if item[TYPE_KEY] == 1 else MOVEMENT_TYPE_INCOME,
                'active': item['active'],
                'comment': item['commentary'] if item.get('commentary') else '',
            })

