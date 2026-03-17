import base64
import io
import pandas as pd
from odoo import models, fields, api

class StatementImport(models.Model):
    _name = 'home_finance.statement.import'
    _description = 'Bank Statement Import'

    period = fields.Date(string='Period', required=True, default=fields.Date.context_today)
    wallet_id = fields.Many2one('home_finance.wallet', string='Wallet', required=True)
    import_rule_id = fields.Many2one('home_finance.statement.import.rule',
                                     string='Statement Import Rule', required=True,
                                     domain="[('wallet_id', '=', wallet_id)]")
    file = fields.Binary(string='File', required=True)
    filename = fields.Char(string='Filename')
    line_ids = fields.One2many('home_finance.statement.import.line', 'statement_import_id', string='Statement Lines')

    name = fields.Char(string='Name', compute='_compute_name')

    @api.depends('wallet_id', 'period')
    def _compute_name(self):
        for record in self:
            if record.filename and record.wallet_id and record.period:
                record.name = f"Statement import for {record.wallet_id.name} on {record.period}"
            else:
                record.name = "New Statement Import"


    def action_parse(self):
        self.ensure_one()
        self.parse_xlsx()
        #return {'type': 'ir.actions.act_window_close'}

    def parse_xlsx(self):
        # Decode the file content
        file_content = base64.b64decode(self.file)

        # Read the Excel file into a DataFrame
        df = pd.read_excel(
            io.BytesIO(file_content),
            usecols="B,D,E"
        )
        df = df.iloc[1:] # Skip the first row (header)

        for _, row in df.iterrows():
            category = row.iloc[0]
            description = row.iloc[1]
            amount = row.iloc[2]

            print(category, description, amount)
