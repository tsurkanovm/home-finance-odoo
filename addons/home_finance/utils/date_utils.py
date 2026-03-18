from dateutil.relativedelta import relativedelta
from datetime import date
import calendar

from odoo import fields


def get_month_end_date(value):
    """
        Return the last day of the given month.

        Examples:
        - 2026-03-18 -> 2026-03-31
        - 2026-02-10 -> 2026-02-28
    """
    if not value:
        return False

    if isinstance(value, str):
        value = fields.Date.from_string(value)

    last_day = calendar.monthrange(value.year, value.month)[1]
    return date(value.year, value.month, last_day)

def get_end_of_previous_month(value=None):
    """
    Return the last day of the previous month.

    Examples:
    - 2026-03-18 -> 2026-02-28
    - 2026-01-10 -> 2025-12-31
    """
    if value is None:
        value = fields.Date.today()

    if isinstance(value, str):
        value = fields.Date.from_string(value)

    first_day_this_month = value.replace(day=1)
    return first_day_this_month - relativedelta(days=1)