from collections import defaultdict

from odoo import models, fields, api

from ..utils.currency_utils import compute_base_amount
from ..utils.date_utils import get_current_period


class WalletBalance(models.Model):
    _name = 'home_finance.wallet.balance'
    _description = 'Wallet balance for home finance management'
    _order = 'wallet_id'

    wallet_id = fields.Many2one(
        'home_finance.wallet',
        string='Wallet',
        required=True,
    )
    period = fields.Date(
        string='Period',
        required=True,
        help='Last period used during balance calculation.',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='wallet_id.currency_id',
        readonly=True,
        store=True,
    )
    amount = fields.Monetary(
        string='Amount',
        required=True,
        currency_field='currency_id',
    )
    base_currency_id = fields.Many2one(
        'res.currency',
        string='Base Currency',
        default=lambda self: self.env.company.currency_id,
        store=True,
        readonly=True,
    )
    base_amount = fields.Monetary(
        string='Base Amount',
        compute='_compute_base_amount',
        currency_field='base_currency_id',
        store=True,
        readonly=True,
    )

    _check_wallet_uniqueness = models.Constraint(
            'unique(wallet_id)',
            'Balance for this wallet already exists.'
        )


    @api.depends('amount', 'currency_id', 'base_currency_id', 'period')
    def _compute_base_amount(self):
        for record in self:
            record.base_amount = compute_base_amount(record, self)

    @api.model
    def action_calculate(self):
        period = get_current_period(self)

        wallets = self.env['home_finance.wallet'].search([
            ('active', '=', True),
        ])
        wallet_ids = wallets.ids

        if not wallet_ids:
            return

        balances_by_wallet = defaultdict(float)

        self._apply_transactions(balances_by_wallet, wallet_ids, period)
        self._apply_incoming_transfers(balances_by_wallet, wallet_ids, period)
        self._apply_outgoing_transfers(balances_by_wallet, wallet_ids, period)

        existing_balances = self.search([
            ('wallet_id', 'in', wallet_ids),
        ])
        existing_map = {record.wallet_id.id: record for record in existing_balances}

        to_create = []
        to_update = []

        for wallet in wallets:
            vals = {
                'wallet_id': wallet.id,
                'period': period,
                'amount': balances_by_wallet[wallet.id],
            }

            existing_record = existing_map.get(wallet.id)
            if existing_record:
                to_update.append((existing_record, vals))
            else:
                to_create.append(vals)

        for record, vals in to_update:
            record.write({
                'period': vals['period'],
                'amount': vals['amount'],
            })

        if to_create:
            self.create(to_create)

    def _apply_transactions(self, balances_by_wallet, wallet_ids, period):
        transactions = self.env['home_finance.transaction'].search([
            ('wallet_id', 'in', wallet_ids),
            ('period', '<=', period),
            ('active', '=', True),
        ])

        for transaction in transactions:
            if transaction.type == 'income':
                balances_by_wallet[transaction.wallet_id.id] += transaction.amount
            elif transaction.type == 'expense':
                balances_by_wallet[transaction.wallet_id.id] -= transaction.amount

    def _apply_incoming_transfers(self, balances_by_wallet, wallet_ids, period):
        transfers = self.env['home_finance.transfer'].search([
            ('destination_wallet_id', 'in', wallet_ids),
            ('period', '<=', period),
            ('active', '=', True),
        ])

        for transfer in transfers:
            balances_by_wallet[transfer.destination_wallet_id.id] += transfer.destination_amount

    def _apply_outgoing_transfers(self, balances_by_wallet, wallet_ids, period):
        transfers = self.env['home_finance.transfer'].search([
            ('source_wallet_id', 'in', wallet_ids),
            ('period', '<=', period),
            ('active', '=', True),
        ])

        for transfer in transfers:
            balances_by_wallet[transfer.source_wallet_id.id] -= transfer.source_amount