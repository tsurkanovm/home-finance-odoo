from odoo import models, fields, _

class WalletBalanceRecalculateWizard(models.TransientModel):
    _name = 'magento_integrator.runner.wizard'
    _description = 'Magento Integrator Runner Wizard'

    data_type = fields.Selection(
        string='Data Type',
        selection=[('all', 'All'), ('category', 'Category'), ('project', 'Project'), ('transaction', 'Transaction'),
                   ('transfer', 'Transfer')],
        default='all',
    )

    def action_run(self):
        self.ensure_one()

        # self.env['home_finance.wallet.balance'].action_calculate()
        #
        # return {
        #     'type': 'ir.actions.act_window',
        #     'name': _('Wallet Balances'),
        #     'res_model': 'home_finance.wallet.balance',
        #     'view_mode': 'pivot',
        #     'target': 'current',
        # }