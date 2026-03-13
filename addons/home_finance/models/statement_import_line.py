from odoo import models, fields, api
from ..constant import STATEMENT_TYPE_SELECTION

class StatementImportLine(models.Model):
    _name = 'home_finance.statement.import.line'
    _description = 'Bank Statement Import Line'

    type = fields.Selection(string='Movement Type', required=True, selection=STATEMENT_TYPE_SELECTION)
    wallet_id = fields.Many2one('home_finance.wallet', required=True, string='Wallet')
    category_id = fields.Many2one('home_finance.category', string='Category',
                                  domain="[('type', '=', type)]")
    project_id = fields.Many2one('home_finance.project', string='Project')
    currency_id = fields.Many2one('res.currency', string='Currency', related='wallet_id.currency_id', readonly=True)
    amount = fields.Monetary(string='Amount', required=True, currency_field='currency_id')

    destination_wallet_id = fields.Many2one('home_finance.wallet', string='To Wallet')
    destination_currency_id = fields.Many2one('res.currency', string='To Currency',
                                              related='destination_wallet_id.currency_id', readonly=True)
    destination_amount = fields.Monetary(string='To Amount', currency_field="destination_currency_id")
    comment = fields.Text(string='Commentary')
    status = fields.Selection(string='Status',
                              selection=[('draft', 'Draft'), ('converted', 'Converted'), ('error', 'Error')],
                              default='draft')
    statement_import_id = fields.Many2one('home_finance.statement.import', string='Statement Import', ondelete='cascade')