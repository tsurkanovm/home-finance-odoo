from odoo import models, fields, api, _
from ..constant import MOVEMENT_TYPE_SELECTION, MOVEMENT_TYPE_EXPENSE


class Transaction(models.Model):
    _name='home_finance.transaction'
    _inherit = 'home_finance.document'
    _description='Home Finance Transaction'


    #registration_date = fields.Datetime(string='Registration Date', default=fields.Datetime.now)

    type = fields.Selection(string='Movement Type', required=True, selection=MOVEMENT_TYPE_SELECTION, default=MOVEMENT_TYPE_EXPENSE)
    wallet_id = fields.Many2one('home_finance.wallet', required=True, string='Wallet')
    category_id = fields.Many2one('home_finance.category', required=True, string='Category', domain="[('type', '=', type)]")
    project_id = fields.Many2one('home_finance.project', string='Project')
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.company.currency_id)
    amount = fields.Monetary(string='Amount', required=True)

    name = fields.Char(string='Transaction Name', compute='_compute_name')

    @api.depends('type', 'category_id', 'currency_id', 'amount')
    def _compute_name(self):
        for transaction in self:
            if transaction.category_id and transaction.amount:
                transaction.name \
                    = f"{transaction.category_id.name} - {transaction.amount} {transaction.currency_id.name}"
            else:
                transaction.name = _("New Transaction")