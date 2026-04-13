from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from ..constant import WALLET_TYPE_SELECTION, WALLET_ACCOUNT_TYPE


class Wallet(models.Model):
    _name = 'home_finance.wallet'
    _description = 'Wallet for home finance management'

    name = fields.Char(string='Wallet Name', required=True)
    type = fields.Selection(string='Type', required=True, selection=WALLET_TYPE_SELECTION, default=WALLET_ACCOUNT_TYPE)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.company.currency_id)
    active = fields.Boolean(string='Active', default=True)
    bank_id = fields.Many2one('home_finance.bank', string='Bank', ondelete='set null')
    user_id = fields.Many2one('res.users', string='User',default=lambda self: self.env.user, ondelete='set null')

    transaction_ids = fields.One2many('home_finance.transaction', 'wallet_id', string='Transactions')
    transfer_source_ids = fields.One2many('home_finance.transfer', 'source_wallet_id', string='Transfers From This Wallet')
    transfer_destination_ids = fields.One2many('home_finance.transfer', 'destination_wallet_id', string='Transfers To This Wallet')

    expense_amount = fields.Monetary(string='Total Expenses', compute='_compute_expense_amount', currency_field='currency_id')
    income_amount = fields.Monetary(string='Total Incomes', compute='_compute_income_amount', currency_field='currency_id')
    transfer_out_amount = fields.Monetary(string='Total Transfers Out', compute='_compute_transfer_out_amount', currency_field='currency_id')
    transfer_in_amount = fields.Monetary(string='Total Transfers In', compute='_compute_transfer_in_amount', currency_field='currency_id')

    _check_name_uniqueness = models.Constraint(
        'unique(name)',
        'The wallet name must be unique!'
    )

    # COMPUTE METHODS
    @api.depends('transaction_ids')
    def _compute_expense_amount(self):
        for wallet in self:
            wallet.expense_amount = sum(
                transaction.amount for transaction in wallet.transaction_ids
                if transaction.type == 'expense' and transaction.is_current_period
            )

    @api.depends('transaction_ids')
    def _compute_income_amount(self):
        for wallet in self:
            wallet.income_amount = sum(
                transaction.amount for transaction in wallet.transaction_ids
                if transaction.type == 'income' and transaction.is_current_period
            )

    @api.depends('transfer_source_ids')
    def _compute_transfer_out_amount(self):
        for wallet in self:
            wallet.transfer_out_amount = sum(
                transfer.source_amount for transfer in wallet.transfer_source_ids
                if transfer.is_current_period
            )

    @api.depends('transfer_destination_ids')
    def _compute_transfer_in_amount(self):
        for wallet in self:
            wallet.transfer_in_amount = sum(
                transfer.destination_amount for transfer in wallet.transfer_destination_ids
                if transfer.is_current_period
            )


    # CRUD METHODS
    def write(self, vals):
        for wallet in self:
            currency_changed = 'currency_id' in vals and vals['currency_id'] != wallet.currency_id.id
            type_changed = 'type' in vals and vals['type'] != wallet.type
            deactivated = 'active' in vals and not vals['active'] and wallet.active

            if currency_changed or type_changed or deactivated:
                self.check_on_existing_transactions(wallet)
                self.check_on_existing_transfer(wallet)

        return super().write(vals)

    def check_on_existing_transactions(self, wallet):
        if self.env['home_finance.transaction'].search([('wallet_id', '=', wallet.id)], limit=1):
            raise ValidationError(_(
                "You cannot change a wallet that has existing transactions."
            ))

    def check_on_existing_transfer(self, wallet):
        existing_transfers = self.env['home_finance.transfer'].search(
            ['|', ('source_wallet_id', '=', wallet.id), ('destination_wallet_id', '=', wallet.id)], limit=1)
        if existing_transfers:
            raise ValidationError(_(
                "You cannot change a wallet that has existing transfers."
            ))
