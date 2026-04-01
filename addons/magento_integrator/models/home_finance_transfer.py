from odoo import models, _
from odoo.exceptions import UserError
from odoo.addons.home_finance.utils.date_utils import get_month_end_date


OUT_WALLET_KEY = 'storage'
IN_WALLET_KEY = 'storage_in'
IN_AMOUNT_KEY = 'total_in'
OUT_AMOUNT_KEY = 'total'
IN_CURRENCY_KEY = 'currency_in'
OUT_CURRENCY_KEY = 'currency'
EXCLUDE_IDS = [233]

class Transfer(models.Model):
    _name = "home_finance.transfer"
    _inherit = ["home_finance.transfer", "magento_integrator.id.mixin"]

    def import_transfers(self):
        transfers = self.env['magento_integrator.api'].get_transfer_all()
        existing_ids = set(self.with_context(active_test=False).search([]).mapped('m2_id')) | set(EXCLUDE_IDS)

        resolved_wallets = {}
        for item in transfers.get('items', []):
            if item['id'] in existing_ids:
                continue

            source_wallet_key = f"{item[OUT_WALLET_KEY]}_{item[OUT_CURRENCY_KEY]}"
            if source_wallet_key in resolved_wallets:
                source_wallet = resolved_wallets[source_wallet_key]
            else:
                source_wallet = self.env['home_finance.wallet'].get_wallet_by_id_and_currency(item[OUT_WALLET_KEY], item[OUT_CURRENCY_KEY])
                if not source_wallet:
                    raise UserError(_("Source wallet not found for transfer with ID: %s", item['id']))
                resolved_wallets[source_wallet_key] = source_wallet

            destination_wallet_key = f"{item[IN_WALLET_KEY]}_{item[IN_CURRENCY_KEY]}"
            if destination_wallet_key in resolved_wallets:
                destination_wallet = resolved_wallets[destination_wallet_key]
            else:
                destination_wallet = self.env['home_finance.wallet'].get_wallet_by_id_and_currency(item[IN_WALLET_KEY], item[IN_CURRENCY_KEY])
                if not destination_wallet:
                    raise UserError(_("Destination wallet not found for transfer with ID: %s", item['id']))
                resolved_wallets[destination_wallet_key] = destination_wallet

            period = get_month_end_date(item['registration_time'][:10])
            self.create({
                'm2_id': item['id'],
                'period': period,
                'source_wallet_id': source_wallet.id,
                'destination_wallet_id': destination_wallet.id,
                'source_amount': item[OUT_AMOUNT_KEY],
                'destination_amount': item[IN_AMOUNT_KEY],
                'comment': item['commentary'] if item.get('commentary') else '',
            })