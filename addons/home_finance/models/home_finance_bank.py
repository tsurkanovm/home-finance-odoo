from odoo import models, fields

class Bank(models.Model):
    _name = 'home_finance.bank'
    _description = 'Bank'

    name = fields.Char(string='Bank Name', required=True)
    active = fields.Boolean(string='Active', default=True)