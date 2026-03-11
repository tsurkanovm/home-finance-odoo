
from odoo import models, fields, api
from odoo.exceptions import ValidationError
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

    # CRUD METHODS
    def write(self, vals):
        if 'type' in vals:
            for category in self:
                self.check_on_existing_transactions(category)

        return super().write(vals)

    def check_on_existing_transactions(self, category):
        if self.env['home_finance.transaction'].search([('category_id', '=', category.id)], limit=1):
            raise ValidationError(
                "You cannot change the type of a category that has existing transactions."
            )