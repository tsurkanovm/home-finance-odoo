from odoo import fields, models, api
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

    _check_name_uniqueness = models.Constraint(
        'unique(name)',
        'The wallet name must be unique!'
    )

    # CRUD METHODS
    def write(self, vals):
        if 'currency_id' in vals or 'type' in vals:
            for wallet in self:
                self.check_on_existing_transactions(wallet)
                self.check_on_existing_transfer(wallet)

        return super().write(vals)

    def check_on_existing_transactions(self, wallet):
        if self.env['home_finance.transaction'].search([('wallet_id', '=', wallet.id)], limit=1):
            raise ValidationError(
                "You cannot change the currency or type of a wallet that has existing transactions."
            )

    def check_on_existing_transfer(self, wallet):
        existing_transfers = self.env['home_finance.transfer'].search(
            ['|', ('source_wallet_id', '=', wallet.id), ('destination_wallet_id', '=', wallet.id)], limit=1)
        if existing_transfers:
            raise ValidationError(
                "You cannot change the currency or type of a wallet that has existing transfers.")
