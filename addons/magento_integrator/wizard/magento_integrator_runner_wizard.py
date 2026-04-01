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
        return {
            'type': 'ir.actions.act_window',
            'name': _('Transactions'),
            'res_model': 'home_finance.transaction',
            'view_mode': 'list',
            'target': 'current',
        }

    def _category(self):
        self.env['home_finance.category'].import_categories()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Categories'),
            'res_model': 'home_finance.category',
            'view_mode': 'list',
        }

    def _transaction(self):
        self.env['home_finance.transaction'].import_transactions()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Transactions'),
            'res_model': 'home_finance.transaction',
        }

    def _transfer(self):
        self.env['home_finance.transfer'].import_transfers()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Transfers'),
            'res_model': 'home_finance.transfer',
        }

    def _project(self):
        self.env['home_finance.project'].import_projects()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Projects'),
            'res_model': 'home_finance.project',
            'view_mode': 'list',
        }

    def action_run(self):
        self.ensure_one()

        action_handler = {
            'category':     self._category,
            'project':      self._project,
            'transaction':  self._transaction,
            'transfer':     self._transfer,
            'all':          self._all,
        }

        return action_handler.get(self.data_type, lambda: None)()
