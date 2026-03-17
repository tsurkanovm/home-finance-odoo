import base64
import io
import pandas as pd
import logging
from odoo import models, fields, api
from ..constant import MOVEMENT_TYPE_TRANSFER, MOVEMENT_TYPE_INCOME, MOVEMENT_TYPE_EXPENSE

_logger = logging.getLogger(__name__)

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

    @api.constrains('filename')
    def _check_filename(self):
        for record in self:
            accept_file_type = record.import_rule_id.file_type
            if record.filename and not record.filename.endswith('.' + accept_file_type):
                raise ValueError(f'The file must be an Excel file ({accept_file_type}).')

    @api.depends('wallet_id', 'period')
    def _compute_name(self):
        for record in self:
            if record.filename and record.wallet_id and record.period:
                record.name = f"Statement import for {record.wallet_id.name} on {record.period}"
            else:
                record.name = "New Statement Import"


    def action_parse(self):
        _logger.info(f"Starting parsing for statement import {self.name}")
        self.ensure_one()
        match self.import_rule_id.file_type:
            case "xlsx":
                self.parse_xlsx()
            case _:
                raise ValueError("Unsupported file type for now")


    def parse_xlsx(self):
        # Decode the file content
        file_content = base64.b64decode(self.file)

        use_cols = (self.import_rule_id.statement_purpose_column + ','
                   + self.import_rule_id.statement_commentary_column + ','
                   + self.import_rule_id.statement_amount_column)
        # Read the Excel file into a DataFrame
        df = pd.read_excel(
            io.BytesIO(file_content),
            usecols=use_cols
        )
        df = df.iloc[self.import_rule_id.statement_first_row:] # Skip the first rows (header)

        handlers = {
            MOVEMENT_TYPE_TRANSFER: self.create_transfer_line,
            MOVEMENT_TYPE_INCOME: self.create_income_line,
            MOVEMENT_TYPE_EXPENSE: self.create_expense_line,
        }

        for _, row in df.iterrows():
            row_data = {
                'purpose': row.iloc[0],
                'description': row.iloc[1],
                'amount': row.iloc[2],
            }
           # _logger.info("Purpose: %s, Description: %s, Amount: %s", row_data['purpose'], row_data['description'], row_data['amount'])
            #search import rule line by purpose and description
            match_line = self.get_matched_line(row_data)
           # _logger.info("Matched line: %s", match_line.type, match_line.category_id.name, match_line.wallet_id.name)

            if not match_line:
                self.create_error_line(row_data)
                continue

            handler = handlers.get(match_line.type)
            if handler:
                handler(match_line, row_data)
            else:
                self.create_error_line(row_data)


    def get_matched_line(self, row_data):
        purpose, description, _ = row_data.values()
        #_logger.info("Purpose: %s, Description: %s", purpose, description)
        description_condition = '%' + description.replace('"', '') + '%'
        match_line = self.import_rule_id.rule_line_ids.search(
            [
                ('rule_id', '=', self.import_rule_id.id),
                ('purpose_key_word', '=', purpose),
                ('commentary_key_word', 'ilike', description_condition)
            ],
            limit=1, order='sequence asc')
        if not match_line:
            match_line = self.import_rule_id.rule_line_ids.search(
                [('rule_id', '=', self.import_rule_id.id), ('purpose_key_word', '=', purpose)],
                limit=1, order='sequence asc')

        if not match_line:
            match_line = self.import_rule_id.rule_line_ids.search(
                [('rule_id', '=', self.import_rule_id.id), ('commentary_key_word', 'ilike', description_condition)],
                limit=1, order='sequence asc')

        return match_line

    def create_transfer_line(self, match_line, row_data):
        purpose, description, amount = row_data.values()
        self.env['home_finance.statement.import.line'].create({
            'statement_import_id': self.id,
            'wallet_id': self.wallet_id.id if amount < 0 else match_line.wallet_id.id,
            'type': MOVEMENT_TYPE_TRANSFER,
            'statement_purpose': purpose,
            'comment': description,
            'amount': abs(amount),
            'destination_amount': abs(amount),
            'destination_wallet_id': match_line.wallet_id.id,
        })

    def create_income_line(self, match_line, row_data):
        purpose, description, amount = row_data.values()
        self.env['home_finance.statement.import.line'].create({
            'statement_import_id': self.id,
            'wallet_id': self.wallet_id.id,
            'type': MOVEMENT_TYPE_INCOME,
            'statement_purpose': purpose,
            'comment': description,
            'amount': amount,
            'category_id': match_line.category_id.id,
            'status': 'error' if amount < 0 else 'draft',
        })

    def create_expense_line(self, match_line, row_data):
        purpose, description, amount = row_data.values()
        self.env['home_finance.statement.import.line'].create({
            'statement_import_id': self.id,
            'wallet_id': self.wallet_id.id,
            'type': MOVEMENT_TYPE_EXPENSE,
            'statement_purpose': purpose,
            'comment': description,
            'amount': abs(amount),
            'category_id': match_line.category_id.id,
            'status': 'error' if amount > 0 else 'draft',
        })

    def create_error_line(self, row_data):
        purpose, description, amount = row_data.values()
        self.env['home_finance.statement.import.line'].create({
            'statement_import_id': self.id,
            'wallet_id': self.wallet_id.id,
            'statement_purpose': purpose,
            'comment': description,
            'amount': amount,
            'status': 'error',
        })

