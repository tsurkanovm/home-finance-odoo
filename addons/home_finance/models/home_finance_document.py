from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from ..utils.date_utils import get_month_end_date, get_end_of_previous_month, get_current_period

class Document(models.AbstractModel):
    _name = 'home_finance.document'
    _description = 'Abstract model for documents'
    _order = 'period desc, id desc'

    active = fields.Boolean(string='Active', default=True, index=True)
    period = fields.Date(
        string='Period',
        default=lambda self: get_end_of_previous_month(fields.Date.context_today(self)),
        required=True,
        index=True,
    )
    comment = fields.Text(string='Commentary')

    is_current_period = fields.Boolean(
        string='Is Current Period',
        compute='_compute_is_current_period',
        search='_search_is_current_period',
        store=False,
    )

    @api.depends('period')
    def _compute_is_current_period(self):
        current_period = get_current_period(self)
        for record in self:
            record.is_current_period = bool(
                current_period and record.period == current_period
            )

    @api.constrains('period')
    def _check_period(self):
        current_period = get_current_period(self)
        # @todo allow to edit commentary for old records
        for record in self:
            if record.active and record.period and record.period < current_period:
                raise ValidationError(_(
                    "The period of an active document cannot be before the current period. "
                    "Please update the current period in settings or set the document as inactive."
                ))

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

    @api.model
    def _search_is_current_period(self, operator, value):
        current_period = get_current_period(self)

        if operator not in ('=', '!='):
            raise NotImplementedError(_("Unsupported operator '%s' for is_current_period") % operator)

        # Determine whether we want records matching the current period
        # ('=', True) → match | ('=', False) → no match
        # ('!=', True) → no match | ('!=', False) → match
        want_match = (operator == '=') == bool(value)

        if not current_period:
            return [('id', 'in', [])] if want_match else []

        if want_match:
            return [('period', '=', current_period)]
        return [('period', '!=', current_period)]
