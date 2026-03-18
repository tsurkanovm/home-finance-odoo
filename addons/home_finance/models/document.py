from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ..utils.date_utils import get_month_end_date, get_end_of_previous_month, get_current_period

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

    @api.constrains('period')
    def _check_period(self):
        current_period = get_current_period(self)
        # @todo allow to edit commentary for old records
        for record in self:
            if record.active and record.period and record.period < current_period:
                raise ValidationError(
                    "The period of an active document cannot be before the current period. "
                    "Please update the current period in settings or set the document as inactive."
                )

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
