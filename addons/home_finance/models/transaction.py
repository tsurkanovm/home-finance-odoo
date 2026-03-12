from odoo import models, fields, api, _
from ..constant import MOVEMENT_TYPE_SELECTION, MOVEMENT_TYPE_EXPENSE


class Transaction(models.Model):
    _name='home_finance.transaction'
    _inherit = 'home_finance.document'
    _description='Home Finance Transaction'

    # @todo - replace by related field to category type, and two form views (one for expense, one for income)
    type = fields.Selection(string='Movement Type', required=True, selection=MOVEMENT_TYPE_SELECTION,
                            default=MOVEMENT_TYPE_EXPENSE)
    wallet_id = fields.Many2one('home_finance.wallet', required=True, string='Wallet', ondelete='restrict')
    category_id = fields.Many2one('home_finance.category', required=True, string='Category',
                                  domain="[('type', '=', type)]", ondelete='restrict')
    project_id = fields.Many2one('home_finance.project', string='Project', ondelete='restrict')
    currency_id = fields.Many2one('res.currency', string='Currency', related='wallet_id.currency_id', store=True,
                                  readonly=True)
    amount = fields.Monetary(string='Amount', required=True, currency_field='currency_id')
    base_currency_id = fields.Many2one('res.currency', string='Base Currency',
                                       default=lambda self: self.env.company.currency_id, store=True,
                                       readonly=True)
    base_amount = fields.Monetary(string='Base Amount', compute='_compute_base_amount',
                                  currency_field='base_currency_id', store=True, readonly=True)

    name = fields.Char(string='Transaction Name', compute='_compute_name')


    # COMPUTE METHODS
    @api.depends('type', 'category_id', 'amount')
    def _compute_name(self):
        for transaction in self:
            if transaction.category_id and transaction.amount and transaction.wallet_id:
                transaction.name \
                    = f"{transaction.category_id.name} - {transaction.amount} {transaction.currency_id.name}"
            else:
                transaction.name = _("New Transaction")

    @api.depends('amount', 'currency_id', 'base_currency_id', 'period')
    def _compute_base_amount(self):
        for transaction in self:
            if transaction.amount and transaction.currency_id and transaction.base_currency_id:
                transaction.base_amount = self.env['res.currency'].browse(transaction.currency_id.id)._convert(
                    transaction.amount,
                    transaction.base_currency_id,
                    self.env.company,
                    transaction.period
                )
            else:
                transaction.base_amount = 0.0