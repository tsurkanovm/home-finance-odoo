from odoo import fields, models, api
from ..constant import WALLET_TYPE_SELECTION, WALLET_ACCOUNT_TYPE

class Wallet(models.Model):
    _name = 'home_finance.wallet'
    _description = 'Wallet for home finance management'


    name = fields.Char(string='Wallet Name', required=True)
    type = fields.Selection(string='Type', required=True, selection=WALLET_TYPE_SELECTION, default=WALLET_ACCOUNT_TYPE)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.company.currency_id)
    active = fields.Boolean(string='Active', default=True)
