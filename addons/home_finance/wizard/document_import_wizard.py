import base64
import io
import pandas as pd
from odoo import models, fields, api

class DocumentImportWizard(models.TransientModel):
    _name = 'home_finance.document.import.wizard'
    _description = 'Document Import Wizard'

    period = fields.Date(string='Period', required=True, default=fields.Date.context_today)
    wallet_id = fields.Many2one('home_finance.wallet', string='Wallet', required=True)
    file = fields.Binary(string='File', required=True)
    filename = fields.Char(string='Filename')

    name = fields.Char(string='Import Name', compute='_compute_name')

    @api.depends('filename', 'wallet_id', 'period')
    def _compute_name(self):
        for record in self:
            if record.filename and record.wallet_id and record.period:
                record.name = f"Import {record.filename} for {record.wallet_id.name} on {record.period}"
            else:
                record.name = "New Document Import"


    def action_import(self):
        self.ensure_one()
        self.import_xlsx()
        return {'type': 'ir.actions.act_window_close'}

    def import_xlsx(self):
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
