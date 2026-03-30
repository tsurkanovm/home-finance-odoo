from dateutil.relativedelta import relativedelta

from odoo import models, fields, _
from odoo.exceptions import UserError


class NbuCurrencyRateUpdater(models.TransientModel):
    _name = 'nbu_currency_rate.updater'
    _description = 'NBU Currency Rate Updater'

    currency_id = fields.Many2one('res.currency', string='Currency', required=False)
    date_from = fields.Date(string='From Date', required=False, default=fields.Date.today)
    date_to = fields.Date(string='To Date', required=False, default=fields.Date.today)
    interval = fields.Selection(string='Interval',
                                selection=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')],
                                default='weekly')

    def _get_dates(self, date_from, date_to, interval) -> list:
        deltas = {
            'daily': relativedelta(days=1),
            'weekly': relativedelta(weeks=1),
            'monthly': relativedelta(months=1),
        }
        delta = deltas[interval]
        dates, current = [], date_from
        while current <= date_to:
            dates.append(current)
            current += delta

        return dates

    def _update_rates(self) -> bool:
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')

        if active_model == 'res.company' and active_id:
            company = self.env['res.company'].browse(active_id)
        else:
            company = self.env.company

        if not self.date_from or not self.date_to:
            raise UserError(_("Please set both From Date and To Date."))
        if self.date_from > self.date_to:
            raise UserError(_("From Date must be before or equal to To Date."))

        dates = self._get_dates(self.date_from, self.date_to, self.interval)
        for date in dates:
            company.update_currency_rates(date=date, currency=self.currency_id.id)

        return True

    def action_update_rates(self):
        self._update_rates()
        # redirect to currency rate form view
        return self.env.ref('base.action_currency_form').read()[0]
