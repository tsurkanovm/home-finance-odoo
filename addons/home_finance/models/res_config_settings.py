from datetime import date
import calendar

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    home_finance_statement_import_ttl = fields.Integer(
        string="Statement Import TTL (months)",
        config_parameter='home_finance.statement_import_ttl',
        default=2,
    )

    # field shown in Settings form
    home_finance_current_period = fields.Date(
        string="Current Period",
        default=fields.Date.context_today,
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        icp = self.env['ir.config_parameter'].sudo()
        raw_value = icp.get_param('home_finance.current_period')

        res.update({
            'home_finance_current_period': raw_value or False,
        })
        return res

    def set_values(self):
        super().set_values()
        icp = self.env['ir.config_parameter'].sudo()

        normalized_value = False
        if self.home_finance_current_period:
            normalized_value = self._get_month_end_date(self.home_finance_current_period)

        icp.set_param(
            'home_finance.current_period',
            normalized_value or ''
        )

    @api.model
    def _get_month_end_date(self, value):
        """
        Convert any selected date to the last day of its month.
        Example:
            2026-02-05 -> 2026-02-28
            2026-02-28 -> 2026-02-28
        """
        if isinstance(value, str):
            value = fields.Date.from_string(value)

        last_day = calendar.monthrange(value.year, value.month)[1]
        return date(value.year, value.month, last_day)