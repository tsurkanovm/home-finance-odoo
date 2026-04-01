from odoo import models, fields, api, _
from odoo.tools import float_compare
from odoo.exceptions import ValidationError

class Transfer(models.Model):
    _name = 'home_finance.transfer'
    _description = 'Transfer between wallets'
    _inherit = ['home_finance.document']

    source_wallet_id = fields.Many2one('home_finance.wallet', string='From Wallet', required=True, ondelete='restrict')
    destination_wallet_id = fields.Many2one('home_finance.wallet', string='To Wallet', required=True, ondelete='restrict')

    source_currency_id = fields.Many2one('res.currency', string='From Currency',
                                         related='source_wallet_id.currency_id', readonly=True)
    source_amount = fields.Monetary(string='From Amount', required=True, currency_field="source_currency_id")

    destination_currency_id = fields.Many2one('res.currency', string='To Currency',
                                              related='destination_wallet_id.currency_id', readonly=True)
    destination_amount = fields.Monetary(string='To Amount', required=True, currency_field="destination_currency_id")


    name = fields.Char(string='Transaction Name', compute='_compute_name')

    _check_amounts = models.Constraint(
        'CHECK(source_amount > 0 AND destination_amount > 0)',
        'The From Amount or To Amount must be positive.',
    )

    _check_wallets_equality = models.Constraint(
        'CHECK(source_wallet_id != destination_wallet_id)',
        'Wallets should be different.',
    )

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------
    @api.depends('source_wallet_id', 'destination_wallet_id')
    def _compute_name(self):
        for transfer in self:
            if transfer.source_wallet_id and transfer.destination_wallet_id:
                transfer.name = _("Transfer from %s to %s") % (transfer.source_wallet_id.name, transfer.destination_wallet_id.name)
            else:
                transfer.name = _("New Transfer")

    # -------------------------------------------------------------------------
    # CONSTRAIN METHODS
    # -------------------------------------------------------------------------
    @api.constrains('source_currency_id', 'destination_currency_id', 'source_amount', 'destination_amount')
    def _check_wallets_and_currencies(self):
        for transfer in self:
            #skip if this checkup, if this transfer goes from Magento (artifact of the old system)
            if transfer.m2_id:
                continue
            if ((transfer.source_currency_id == transfer.destination_currency_id)
                    and (float_compare(transfer.source_amount,transfer.destination_amount, precision_digits=2) != 0)):
                raise ValidationError(_(
                    "When transferring between the same currencies, "
                    "the From Amount and To Amount should be different. Transfer name %s, source amount: %s destination amount: %s"
                ) % (transfer.name, transfer.source_amount, transfer.destination_amount))

    # -------------------------------------------------------------------------
    # ONCHANGE METHODS
    # -------------------------------------------------------------------------
    @api.onchange('source_wallet_id', 'destination_wallet_id', 'source_amount', 'period')
    def _onchange_source_amount_currency(self):
        if self.source_currency_id and self.source_amount:
            self.destination_amount = self.env['res.currency'].browse(self.source_currency_id.id)._convert(
                self.source_amount,
                self.destination_currency_id,
                self.env.company,
                self.period
            )
