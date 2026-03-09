
from odoo import models, fields, api
from ..constant import MOVEMENT_TYPE_SELECTION, MOVEMENT_TYPE_EXPENSE

class Category(models.Model):
    _name = 'home_finance.category'
    _description = 'Transaction Category'

    name = fields.Char(string='Category Name', required=True)
    active = fields.Boolean(string='Active', default=True)
    type = fields.Selection(string='Type', selection=MOVEMENT_TYPE_SELECTION, default=MOVEMENT_TYPE_EXPENSE)

    _check_name_type_uniqueness = models.Constraint(
        'unique(name, type)',
        'The name and type must be unique!'
    )