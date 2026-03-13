from odoo import models, fields
from ..constant import STATEMENT_TYPE_SELECTION

class StatementImportRuleLine(models.Model):
    _name = 'home_finance.statement.import.rule.line'
    _description = 'Statement Import Rule Line'

    rule_id = fields.Many2one('home_finance.statement.import.rule', string='Import Rule', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    type = fields.Selection(string='Movement Type', required=True, selection=STATEMENT_TYPE_SELECTION)
    wallet_id = fields.Many2one('home_finance.wallet', required=True, string='Wallet')
    category_id = fields.Many2one('home_finance.category', string='Category',
                                  domain="[('type', '=', type)]")
    purpose_key_word = fields.Char(string='Purpose Keyword')
    commentary_key_word = fields.Char(string='Commentary Keyword')