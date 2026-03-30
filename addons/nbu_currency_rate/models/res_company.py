import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    currency_provider = fields.Selection(
        selection=lambda self: self._get_currency_provider_selection(),
    )

    def _get_currency_provider_selection(self):
        selection = []
        parent = getattr(super(), "_get_currency_provider_selection", None)
        if parent:
            selection = parent()
        return selection + [("nbu", "National Bank of Ukraine (NBU)")]

    def _get_provider_adapter(self):
        self.ensure_one()
        if self.currency_provider == "nbu":
            return self.env["nbu_currency_rate.provider"]
        return None

    def _get_available_currencies_map(self, currency=None):
        """
        Return mapping: {'USD': res.currency(...), 'EUR': res.currency(...), ...}

        currency may be:
        - None -> all currencies
        - res.currency recordset
        - currency id
        """
        self.ensure_one()
        Currency = self.env["res.currency"]

        if not currency:
            currencies = Currency.search([])
        elif isinstance(currency, models.BaseModel):
            currencies = currency
        else:
            currencies = Currency.browse(currency)

        return {curr.name: curr for curr in currencies.exists()}

    def _get_latest_company_rates(self, date=None, currency=None):
        """
        Return provider rates in company-based format:

            {
                'UAH': 41.20,
                'EUR': 0.91,
            }

        Meaning:
            how many units of target currency correspond
            to 1 unit of company currency.

        These are NOT technical res.currency.rate.rate values.
        """
        self.ensure_one()

        adapter = self._get_provider_adapter()
        if adapter is None:
            raise UserError(
                _("No custom currency provider adapter configured for company %s.")
                % self.display_name
            )

        currencies_map = self._get_available_currencies_map(currency)
        return adapter.get_rates(
            company=self,
            currencies_map=currencies_map,
            date=date or fields.Date.context_today(self),
        )

    def _get_latest_rate_record(self, currency, target_date):
        self.ensure_one()
        return self.env["res.currency.rate"].search(
            [
                ("currency_id", "=", currency.id),
                ("company_id", "=", self.id),
                ("name", "<=", target_date),
            ],
            order="name desc, id desc",
            limit=1,
        )

    def _get_company_currency_technical_rate(self, target_date):
        """
        Return technical rate of company currency on target date.

        Fallback to 1.0 if no explicit rate row exists.
        """
        self.ensure_one()

        rate_rec = self._get_latest_rate_record(self.currency_id, target_date)
        return rate_rec.rate or 1.0

    def _upsert_currency_rate(self, currency, target_date, technical_rate):
        self.ensure_one()

        rate_model = self.env["res.currency.rate"]
        existing = rate_model.search(
            [
                ("currency_id", "=", currency.id),
                ("company_id", "=", self.id),
                ("name", "=", target_date),
            ],
            limit=1,
        )

        vals = {
            "currency_id": currency.id,
            "company_id": self.id,
            "name": target_date,
            "rate": technical_rate,
        }

        if existing:
            existing.write({"rate": technical_rate})
        else:
            rate_model.create(vals)

    def _apply_currency_rates(self, company_rates, date=None):
        """
        Convert company-based rates to Odoo technical rates and save them.

        company_rates format:
            {
                'UAH': 41.20,
                'EUR': 0.91,
            }

        Meaning:
            1 company_currency = X target_currency
        """
        self.ensure_one()

        target_date = date or fields.Date.context_today(self)
        currencies_map = self._get_available_currencies_map()
        company_currency = self.currency_id
        company_currency_technical_rate = self._get_company_currency_technical_rate(
            target_date
        )

        for code, company_rate in company_rates.items():
            currency = currencies_map.get(code)
            if not currency:
                _logger.warning(
                    "Skipping unknown currency code %s for company %s",
                    code,
                    self.name,
                )
                continue

            # Never store a separate row for company currency itself.
            if currency == company_currency:
                continue

            if not company_rate:
                _logger.warning(
                    "Skipping empty company rate for currency %s in company %s",
                    code,
                    self.name,
                )
                continue

            technical_rate = company_rate * company_currency_technical_rate
            self._upsert_currency_rate(currency, target_date, technical_rate)

    def _update_nbu_currency_rates(self, date=None, currency=None):
        self.ensure_one()

        company_rates = self._get_latest_company_rates(date=date, currency=currency)
        if company_rates:
            self._apply_currency_rates(company_rates, date=date)

        return True

    def update_currency_rates(self, date=None, currency=None):
        res = True

        companies = (self or self.search([])).filtered(
            lambda c: c.currency_provider == "nbu"
        )
        for company in companies:
            try:
                _logger.info("Updating NBU currency rates for company %s", company.name)
                company._update_nbu_currency_rates(date=date, currency=currency)
            except UserError:
                _logger.exception(
                    "Business error while updating NBU rates for company %s",
                    company.name,
                )
                res = False
            except Exception:
                _logger.exception(
                    "Unexpected error while updating NBU rates for company %s",
                    company.name,
                )
                res = False

        return res