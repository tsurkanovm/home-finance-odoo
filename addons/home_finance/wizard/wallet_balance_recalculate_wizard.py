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

        return {
            'type': 'ir.actions.act_window',
            'name': _('Wallet Balances'),
            'res_model': 'home_finance.wallet.balance',
            'view_mode': 'pivot',
            'target': 'current',
        }