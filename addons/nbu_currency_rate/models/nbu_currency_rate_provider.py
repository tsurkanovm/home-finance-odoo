import datetime
import logging

import requests

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

NBU_API_URL = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange"
UAH = "UAH"


class NbuCurrencyRateProvider(models.AbstractModel):
    _name = "nbu_currency_rate.provider"
    _description = "NBU Currency Rate Provider"

    def get_rates(self, company, currencies_map, date=None):
        """
        Return company-based rates, NOT technical Odoo rates.

        Result format:
            {
                'UAH': 41.20,
                'EUR': 0.91,
            }

        Meaning:
            how many units of target currency correspond to
            1 unit of company currency.

        Examples:
            company currency = USD
            - UAH: 41.20   means 1 USD = 41.20 UAH
            - EUR: 0.91    means 1 USD = 0.91 EUR

        Notes:
            - NBU always gives UAH per 1 foreign currency.
            - UAH is derived, because NBU does not return a UAH self-rate row.
            - Company currency itself is excluded from the result.
        """
        company.ensure_one()

        company_code = company.currency_id.name
        requested_codes = set(currencies_map.keys())
        codes_to_process = requested_codes - {company_code}

        if not codes_to_process:
            return {}

        codes_to_fetch = {code for code in codes_to_process if code != UAH}
        if company_code != UAH:
            codes_to_fetch.add(company_code)

        uah_rates = self._fetch_uah_rates(codes_to_fetch, date) if codes_to_fetch else {}

        if company_code == UAH:
            uah_per_company = 1.0
        else:
            uah_per_company = uah_rates.get(company_code)
            if not uah_per_company:
                raise UserError(
                    _("Could not fetch rate for company currency %s from NBU.")
                    % company_code
                )

        result = {}

        for code in codes_to_process:
            if code == UAH:
                # 1 company_currency = uah_per_company UAH
                result[UAH] = uah_per_company
                continue

            uah_per_foreign = uah_rates.get(code)
            if not uah_per_foreign:
                _logger.warning(
                    "NBU returned no usable rate for currency %s on %s",
                    code,
                    date,
                )
                continue

            # Convert via UAH cross-rate:
            # 1 company_currency = (UAH/company) / (UAH/foreign) foreign_currency
            result[code] = uah_per_company / uah_per_foreign

        if not result:
            raise UserError(_("NBU returned no usable currency rates."))

        return result

    def _fetch_uah_rates(self, currency_codes, date):
        """
        Fetch rates from NBU in format:
            {
                'USD': 41.20,
                'EUR': 44.90,
            }

        Meaning:
            UAH per 1 unit of foreign currency
        """
        result = {}
        common_params = {"json": ""}

        if date:
            if isinstance(date, str):
                query_date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
            else:
                query_date = date
            common_params["date"] = query_date.strftime("%Y%m%d")

        for code in currency_codes:
            try:
                response = requests.get(
                    NBU_API_URL,
                    params={**common_params, "valcode": code},
                    timeout=30,
                )
                response.raise_for_status()
                payload = response.json()
            except (requests.RequestException, ValueError) as exc:
                raise UserError(
                    _("Failed to fetch currency rates from NBU: %s") % exc
                ) from exc

            if isinstance(payload, list) and payload:
                rate = payload[0].get("rate")
                if rate:
                    result[code] = float(rate)

        return result