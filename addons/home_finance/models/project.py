from odoo import models, fields

class Project(models.Model):
    _name = 'home_finance.project'
    _description = 'Transaction Project'
    name = fields.Char(string='Name', required=True)
    active = fields.Boolean(string='Active', default=True)

