from dateutil.relativedelta import relativedelta
from odoo import models, fields, api

class Document(models.AbstractModel):
    _name = 'home_finance.document'
    _description = 'Abstract model for documents'

    active = fields.Boolean(string='Active', default=True)

    @api.model
    def _end_of_previous_month(self):
        today = fields.Date.context_today(self)
        first_day_this_month = today.replace(day=1)
        return first_day_this_month - relativedelta(days=1)

    period = fields.Date(
        string='Period',
        default=_end_of_previous_month,
        required=True,
    )
    comment = fields.Text(string='Commentary')
