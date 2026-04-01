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
        items = transactions.get('items', [])
        if not items:
            return

        # Pre-fetch all existing m2_ids in one query
        existing_m2_ids = set(
            self.with_context(active_test=False)
                .search([('m2_id', 'in', [i['id'] for i in items])])
                .mapped('m2_id')
        )

        # Pre-fetch all referenced categories and projects in one query each
        categories_by_m2 = {
            c.m2_id: c for c in self.env['home_finance.category'].search(
                [('m2_id', 'in', [i[CATEGORY_KEY] for i in items])]
            )
        }
        project_m2_ids = [i[PROJECT_KEY] for i in items if i.get(PROJECT_KEY)]
        projects_by_m2 = {
            p.m2_id: p for p in self.env['home_finance.project'].search(
                [('m2_id', 'in', project_m2_ids)]
            )
        } if project_m2_ids else {}

        resolved_wallets = {}
        errors = []
        vals_list = []

        for item in items:
            if item['id'] in existing_m2_ids:
                continue

            category = categories_by_m2.get(item[CATEGORY_KEY])
            if not category:
                errors.append(_("Category not found for transaction with ID: %s") % item['id'])
                continue

            wallet_key = f"{item[WALLET_KEY]}_{item['currency']}"
            if wallet_key not in resolved_wallets:
                resolved_wallets[wallet_key] = self.env['home_finance.wallet'].get_wallet_by_id_and_currency(
                    item[WALLET_KEY], item['currency']
                )
            wallet = resolved_wallets[wallet_key]
            if not wallet:
                errors.append(_("Wallet not found for transaction with ID: %s") % item['id'])
                continue

            project = projects_by_m2.get(item[PROJECT_KEY]) if item.get(PROJECT_KEY) else False
            vals_list.append({
                'm2_id': item['id'],
                'period': item['registration_time'],
                'amount': item['total'],
                'category_id': category.id,
                'project_id': project.id if project else False,
                'wallet_id': wallet.id,
                'type': MOVEMENT_TYPE_EXPENSE if item[TYPE_KEY] == 1 else MOVEMENT_TYPE_INCOME,
                'active': item['active'],
                'comment': item.get('commentary', ''),
            })

        if errors:
            raise UserError('\n'.join(errors))

        if vals_list:
            self.create(vals_list)

