import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class Category(models.Model):
    _name = "home_finance.category"
    _inherit = ["home_finance.category", "magento_integrator.id.mixin"]

    def import_categories(self):
        categories = self.env['magento_integrator.api'].get_category_all()
        for item in categories.get('items', []):
            self.create({
                'm2_id': item['id'],
                'name': item['title'],
                'type': 'expense' if item['move'] else 'income',
            })