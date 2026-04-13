from odoo import models, fields, api,_
from odoo.exceptions import ValidationError
from ..constant import STATEMENT_TYPE_SELECTION

class StatementImportLine(models.Model):
    _name = 'home_finance.statement.import.line'
    _description = 'Bank Statement Import Line'

    type = fields.Selection(string='Movement Type', selection=STATEMENT_TYPE_SELECTION)
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
    statement_purpose = fields.Char(string='Statement Purpose')
    status = fields.Selection(string='Status',
                              required=True,
                              selection=[('draft', 'Draft'), ('converted', 'Converted'), ('error', 'Error')],
                              default='draft',
                              index=True)
    statement_import_id = fields.Many2one('home_finance.statement.import', string='Statement Import', ondelete='cascade')

    display_line_no = fields.Integer(
        string='Line No.',
        compute='_compute_display_line_no',
    )

    @api.depends('statement_import_id', 'statement_import_id.line_ids')
    def _compute_display_line_no(self):
        for line in self:
            line.display_line_no = 0
            if not line.statement_import_id:
                continue

            ordered_lines = line.statement_import_id.line_ids.sorted(
                key=lambda l: l.id
            )
            for index, ordered_line in enumerate(ordered_lines, start=1):
                ordered_line.display_line_no = index

    def action_set_draft(self):
        self.ensure_one()
        self.action_validate()
        self.status = 'draft'
        self.amount = abs(self.amount)

    def _line_label(self):
        return _("line #%(no)s") % {'no': self.display_line_no or self.id}

    def action_validate(self):
        self.ensure_one()
        if self.type == 'transfer' and not (self.wallet_id and self.destination_wallet_id and self.amount and self.destination_amount):
            raise ValidationError(_(
                "Validation error in %(line)s: Wallet, To Wallet, Amount and To Amount must be set."
            ) % {'line': self._line_label()})
        if self.type in ['income', 'expense'] and not (self.wallet_id and self.category_id and self.amount):
            raise ValidationError(_(
                "Validation error in %(line)s: Wallet, Category and Amount must be set."
            ) % {'line': self._line_label()})

        return True