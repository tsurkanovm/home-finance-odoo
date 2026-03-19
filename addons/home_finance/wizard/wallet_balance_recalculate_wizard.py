from odoo import models, fields

class WalletBalanceRecalculateWizard(models.TransientModel):
    _name = 'home_finance.wallet.balance.recalculate.wizard'
    _description = 'Recalculate Wallet Balances'

    note = fields.Text(
        string='Info',
        readonly=True,
        default='This action recalculates wallet balances from source documents.'
    )

    def action_calculate(self):
        self.ensure_one()

        self.env['home_finance.wallet.balance'].action_calculate()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Wallet Balances',
            'res_model': 'home_finance.wallet.balance',
            'view_mode': 'pivot',
            'target': 'current',
        }