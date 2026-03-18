import base64
import io
import logging
import pandas as pd
from typing import Iterator
from collections import defaultdict

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

    # ACTION METHODS
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

    def action_convert(self):
        self.ensure_one()
        _logger.info("Starting conversion of import lines into documents for import %s", self.id)

        transfer_data = self._prepare_transfer_data()
        transaction_data = self._prepare_transaction_data()

        self._create_transfer_documents(transfer_data)
        self._create_transaction_documents(transaction_data)

        lines_to_convert = self.line_ids.filtered(lambda line: line.status == 'draft' and line.type)
        lines_to_convert.write({'status': 'converted'})

    # CRON ACTION METHODS
    def cron_cleanup_expired_imports(self, delete=True):
        import_ttl = self.env['ir.config_parameter'].sudo().get_param('home_finance.statement_import_ttl', default=2)
        if not import_ttl:
            return
        cutoff_date = fields.Date.add(fields.Date.context_today(self), months=-int(import_ttl))
        expired_imports = self.search([('period', '<', cutoff_date)])
        if delete:
            expired_imports.unlink()
            _logger.info("Deleted %s expired statement imports with period before %s", len(expired_imports), cutoff_date)
        else:
            _logger.info("Found %s expired statement imports with period before %s", len(expired_imports), cutoff_date)

    def _prepare_transfer_data(self) -> dict:
        transfer_lines = self.line_ids.filtered(
            lambda line: line.status == 'draft' and line.type == MOVEMENT_TYPE_TRANSFER
        )

        transfer_data = defaultdict(lambda: {
            'amount': 0.0,
            'destination_amount': 0.0,
        })

        for line in transfer_lines:
            line.action_validate()
            key = (line.wallet_id.id, line.destination_wallet_id.id)
            transfer_data[key]['amount'] += line.amount
            transfer_data[key]['destination_amount'] += line.destination_amount

        return dict(transfer_data)

    def _prepare_transaction_data(self) -> dict:
        transaction_lines = self.line_ids.filtered(
            lambda line: line.status == 'draft' and line.type != MOVEMENT_TYPE_TRANSFER
        )

        transaction_data = defaultdict(lambda: {
            'amount': 0.0,
        })

        for line in transaction_lines:
            line.action_validate()
            key = (
                line.type,
                line.wallet_id.id,
                line.category_id.id,
                line.project_id.id,
            )
            transaction_data[key]['amount'] += line.amount

        return dict(transaction_data)

    def _create_transfer_documents(self, transfer_data: dict):
        transfer_model = self.env['home_finance.transfer']

        for (wallet_id, destination_wallet_id), data in transfer_data.items():
            transfer_model.create({
                'source_wallet_id': wallet_id,
                'destination_wallet_id': destination_wallet_id,
                'source_amount': data['amount'],
                'destination_amount': data['destination_amount'],
                'period': self.period,
            })
            _logger.info(
                "Created transfer: source_wallet_id=%s, destination_wallet_id=%s, amount=%s, destination_amount=%s",
                wallet_id,
                destination_wallet_id,
                data['amount'],
                data['destination_amount'],
            )

    def _create_transaction_documents(self, transaction_data: dict):
        transaction_model = self.env['home_finance.transaction']

        for (movement_type, wallet_id, category_id, project_id), data in transaction_data.items():
            transaction_model.create({
                'type': movement_type,
                'wallet_id': wallet_id,
                'category_id': category_id,
                'project_id': project_id,
                'amount': data['amount'],
                'period': self.period,
            })
            _logger.info(
                "Created transaction: type=%s, wallet_id=%s, category_id=%s, project_id=%s, amount=%s",
                movement_type,
                wallet_id,
                category_id,
                project_id,
                data['amount'],
            )

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

    def _iter_statement_rows(self, df: pd.DataFrame) -> Iterator[dict]:
        for _, row in df.iterrows():
            yield {
                'purpose': row.iloc[0],
                'description': row.iloc[1],
                'amount': row.iloc[2],
            }

    def _get_matched_line(self, row_data: dict) -> models.Model:
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

    def _prepare_base_line_vals(self, row_data: dict) -> dict:
        return {
            'statement_import_id': self.id,
            'wallet_id': self.wallet_id.id,
            'statement_purpose': row_data['purpose'],
            'comment': row_data['description'],
            'amount': row_data['amount'],
        }

    def _create_transfer_line(self, match_line, row_data: dict) -> dict:
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

    def _create_income_line(self, match_line, row_data: dict) -> dict:
        amount = row_data['amount']

        vals = self._prepare_base_line_vals(row_data)
        vals.update({
            'type': MOVEMENT_TYPE_INCOME,
            'amount': amount,
            'category_id': match_line.category_id.id,
            'status': 'error' if amount < 0 else 'draft',
        })

        return vals

    def _create_expense_line(self, match_line, row_data: dict) -> dict:
        amount = row_data['amount']

        vals = self._prepare_base_line_vals(row_data)
        vals.update({
            'type': MOVEMENT_TYPE_EXPENSE,
            'amount': abs(amount),
            'category_id': match_line.category_id.id,
            'status': 'error' if amount > 0 else 'draft',
        })

        return vals

    def _prepare_error_line_vals(self, row_data: dict) -> dict:
        vals = self._prepare_base_line_vals(row_data)
        vals.update({
            'status': 'error',
        })

        return vals