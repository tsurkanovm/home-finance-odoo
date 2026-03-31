from odoo import models, fields, _

class RunnerWizard(models.TransientModel):
    _name = 'magento_integrator.runner.wizard'
    _description = 'Magento Integrator Runner Wizard'

    data_type = fields.Selection(
        string='Data Type',
        selection=[('all', 'All'), ('category', 'Category'), ('project', 'Project'), ('transaction', 'Transaction'),
                   ('transfer', 'Transfer')],
        default='all',
    )

    def _all(self):
        self.env['home_finance.category'].import_categories()
        self.env['home_finance.project'].import_projects()
        self.env['home_finance.transaction'].import_transactions()
        self.env['home_finance.transfer'].import_transfers()

    def action_run(self):
        self.ensure_one()

        # action_handler = {
        #     'category': self.env['home_finance.category'].import_categories,
        #     'project': self.env['home_finance.project'].import_projects,
        #     'transaction': self.env['home_finance.transaction'].import_transactions,
        #     'transfer': self.env['home_finance.transfer'].import_transfers,
        #     'all': lambda: self._all,
        # }
        #
        # action_handler.get(self.data_type, lambda: None)()

        self.env['home_finance.category'].import_categories()

        # self.env['home_finance.wallet.balance'].action_calculate()
        #
        # return {
        #     'type': 'ir.actions.act_window',
        #     'name': _('Wallet Balances'),
        #     'res_model': 'home_finance.wallet.balance',
        #     'view_mode': 'pivot',
        #     'target': 'current',
        # }