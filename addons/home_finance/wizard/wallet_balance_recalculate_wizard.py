from odoo import models, fields, _

class WalletBalanceRecalculateWizard(models.TransientModel):
    _name = 'home_finance.wallet.balance.recalculate.wizard'
    _description = 'Recalculate Wallet Balances'

    note = fields.Text(
        string='Info',
        readonly=True,
        default=lambda self: _('This action recalculates wallet balances from source documents.')
    )

    def action_calculate(self):
        self.ensure_one()

        self.env['home_finance.wallet.balance'].action_calculate()

        return self.env.ref('home_finance.hf_wallet_balance_action').read()[0]