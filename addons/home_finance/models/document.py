from odoo import models, fields, api
from ..utils.date_utils import get_month_end_date, get_end_of_previous_month

class Document(models.AbstractModel):
    _name = 'home_finance.document'
    _description = 'Abstract model for documents'

    active = fields.Boolean(string='Active', default=True)
    period = fields.Date(
        string='Period',
        default=lambda self: get_end_of_previous_month(fields.Date.context_today(self)),
        required=True,
    )
    comment = fields.Text(string='Commentary')

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            if 'period' in val and val['period']:
                val['period'] = get_month_end_date(val['period'])
        return super().create(vals)


    def write(self, vals):
        if 'period' in vals and vals['period']:
            vals['period'] = get_month_end_date(vals['period'])
        return super().write(vals)
