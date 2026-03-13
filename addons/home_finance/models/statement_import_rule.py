from odoo import models, fields

class StatementImportRule(models.Model):
    _name = 'home_finance.statement.import.rule'
    _description = 'Rule for importing bank statements'

    name = fields.Char(string='Rule Name', required=True)
    active = fields.Boolean(string='Active', default=True)
    wallet_id = fields.Many2one('home_finance.wallet', string='Wallet', required=True)
    file_type = fields.Selection(string='File Type',
                                 selection=[('csv', 'CSV'), ('xlsx', 'Excel')], required=True, default='xlsx')
    statement_purpose_column = fields.Selection(
        [('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('E', 'E'), ('F', 'F'), ('G', 'G'), ('H', 'H'), ('I', 'I'), ('J', 'J')],
        string='Statement Purpose Column', required=True, default='B')
    statement_commentary_column = fields.Selection(
        [('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('E', 'E'), ('F', 'F'), ('G', 'G'), ('H', 'H'), ('I', 'I'), ('J', 'J')],
        string='Statement Commentary Column', required=True, default='D')
    statement_amount_column = fields.Selection(
        [('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('E', 'E'), ('F', 'F'), ('G', 'G'), ('H', 'H'), ('I', 'I'), ('J', 'J')],
        string='Statement Amount Column', required=True, default='E'
    )
    statement_first_row = fields.Integer(string='Statement First Row', required=True, default=1)

    rule_line_ids = fields.One2many('home_finance.statement.import.rule.line', 'rule_id', string='Rule Mapping Lines')