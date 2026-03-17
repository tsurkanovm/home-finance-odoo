import base64
import io
import logging
import pandas as pd
from typing import Dict, Iterator

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..constant import (
    MOVEMENT_TYPE_EXPENSE,
    MOVEMENT_TYPE_INCOME,
    MOVEMENT_TYPE_TRANSFER,
)

_logger = logging.getLogger(__name__)

class StatementImport(models.Model):
    _name = 'home_finance.statement.import'
    _description = 'Bank Statement Import'

    period = fields.Date(
        string='Period',
        required=True,
        default=fields.Date.context_today,
    )
    wallet_id = fields.Many2one(
        'home_finance.wallet',
        string='Wallet',
        required=True,
    )
    import_rule_id = fields.Many2one(
        'home_finance.statement.import.rule',
        string='Statement Import Rule',
        required=True,
        domain="[('wallet_id', '=', wallet_id)]",
    )
    file = fields.Binary(string='File', required=True)
    filename = fields.Char(string='Filename')
    line_ids = fields.One2many(
        'home_finance.statement.import.line',
        'statement_import_id',
        string='Statement Lines',
    )

    name = fields.Char(string='Name', compute='_compute_name')

    @api.constrains('filename', 'import_rule_id')
    def _check_filename(self):
        for record in self:
            if not record.filename or not record.import_rule_id.file_type:
                continue

            accepted_file_type = record.import_rule_id.file_type
            if not record.filename.endswith(f'.{accepted_file_type}'):
                raise ValidationError(
                    f'The file must be a .{accepted_file_type} file.'
                )

    @api.depends('filename', 'wallet_id', 'period')
    def _compute_name(self):
        for record in self:
            if record.filename and record.wallet_id and record.period:
                record.name = (
                    f"Statement import for {record.wallet_id.name} "
                    f"on {record.period}"
                )
            else:
                record.name = "New Statement Import"

    def action_parse(self):
        self.ensure_one()
        _logger.info("Starting parsing for statement import %s", self.display_name)

        parser_by_type = {
            'xlsx': self._parse_xlsx, #will add more parsers later
        }

        parser = parser_by_type.get(self.import_rule_id.file_type)
        if not parser:
            raise ValidationError("Unsupported file type for now.")

        parser()

    def _parse_xlsx(self):
        df = self._read_xlsx_dataframe()

        line_handler_by_type = {
            MOVEMENT_TYPE_TRANSFER: self._create_transfer_line,
            MOVEMENT_TYPE_INCOME: self._create_income_line,
            MOVEMENT_TYPE_EXPENSE: self._create_expense_line,
        }

        line_model = self.env['home_finance.statement.import.line']

        for row_data in self._iter_statement_rows(df):
            match_line = self._get_matched_line(row_data)

            if not match_line:
                line_model.create(self._prepare_error_line_vals(row_data))
                continue

            handler = line_handler_by_type.get(match_line.type)
            if not handler:
                line_model.create(self._prepare_error_line_vals(row_data))
                continue

            line_model.create(handler(match_line, row_data))

    def _read_xlsx_dataframe(self) -> pd.DataFrame:
        file_content = base64.b64decode(self.file)

        use_cols = ','.join([
            self.import_rule_id.statement_purpose_column,
            self.import_rule_id.statement_commentary_column,
            self.import_rule_id.statement_amount_column,
        ])

        df = pd.read_excel(
            io.BytesIO(file_content),
            usecols=use_cols,
        )

        return df.iloc[self.import_rule_id.statement_first_row:]

    def _iter_statement_rows(self, df: pd.DataFrame) -> Iterator[Dict]:
        for _, row in df.iterrows():
            yield {
                'purpose': row.iloc[0],
                'description': row.iloc[1],
                'amount': row.iloc[2],
            }

    def _get_matched_line(self, row_data: Dict) -> models.Model:
        purpose = row_data['purpose']
        description = row_data['description'] or ''
        description_condition = f'%{description.replace(chr(34), "")}%'

        rule_line_model = self.import_rule_id.rule_line_ids

        search_variants = [
            [
                ('rule_id', '=', self.import_rule_id.id),
                ('purpose_key_word', '=', purpose),
                ('commentary_key_word', 'ilike', description_condition),
            ],
            [
                ('rule_id', '=', self.import_rule_id.id),
                ('purpose_key_word', '=', purpose),
            ],
            [
                ('rule_id', '=', self.import_rule_id.id),
                ('commentary_key_word', 'ilike', description_condition),
            ],
        ]

        for domain in search_variants:
            match_line = rule_line_model.search(domain, limit=1, order='sequence asc')
            if match_line:
                return match_line

        return rule_line_model.browse()

    def _prepare_base_line_vals(self, row_data: Dict) -> Dict:
        return {
            'statement_import_id': self.id,
            'wallet_id': self.wallet_id.id,
            'statement_purpose': row_data['purpose'],
            'comment': row_data['description'],
            'amount': row_data['amount'],
        }

    def _create_transfer_line(self, match_line, row_data: Dict) -> Dict:
        amount = row_data['amount']
        source_wallet_id = self.wallet_id.id if amount < 0 else match_line.wallet_id.id

        vals = self._prepare_base_line_vals(row_data)
        vals.update({
            'wallet_id': source_wallet_id,
            'type': MOVEMENT_TYPE_TRANSFER,
            'amount': abs(amount),
            'destination_amount': abs(amount),
            'destination_wallet_id': match_line.wallet_id.id,
            'status': 'draft',
        })

        return vals

    def _create_income_line(self, match_line, row_data: Dict) -> Dict:
        amount = row_data['amount']

        vals = self._prepare_base_line_vals(row_data)
        vals.update({
            'type': MOVEMENT_TYPE_INCOME,
            'amount': amount,
            'category_id': match_line.category_id.id,
            'status': 'error' if amount < 0 else 'draft',
        })

        return vals

    def _create_expense_line(self, match_line, row_data: Dict) -> Dict:
        amount = row_data['amount']

        vals = self._prepare_base_line_vals(row_data)
        vals.update({
            'type': MOVEMENT_TYPE_EXPENSE,
            'amount': abs(amount),
            'category_id': match_line.category_id.id,
            'status': 'error' if amount > 0 else 'draft',
        })

        return vals

    def _prepare_error_line_vals(self, row_data: Dict) -> Dict:
        vals = self._prepare_base_line_vals(row_data)
        vals.update({
            'status': 'error',
        })

        return vals