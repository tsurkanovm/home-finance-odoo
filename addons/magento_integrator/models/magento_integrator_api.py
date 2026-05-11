import logging
from typing import Any

import requests

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

WALLET_URL = "/rest/V1/cashflow/storage/"
CATEGORY_ALL_URL = "/rest/V1/cashflow/cfitem/all"
TRANSACTION_ALL_URL = "/rest/V1/cashflow/incomes/all"
TRANSFER_ALL_URL = "/rest/V1/cashflow/transfer/all"

class MagentoIntegratorApi(models.AbstractModel):
    _name = "magento_integrator.api"
    _description = "Magento API Service"

    def _get_config(self):
        icp = self.env["ir.config_parameter"].sudo()
        return {
            "base_url": (icp.get_param("magento_integrator.base_url") or "").rstrip("/"),
            "token": icp.get_param("magento_integrator.api_token") or "",
            "timeout": int(icp.get_param("magento_integrator.timeout", default="30")),
        }

    def _request(self, method, endpoint, params=None, payload=None):
        if self.env.user.has_group("base.user_admin"):
            config = self._get_config()
        else:
            raise UserError(_("You do not have permissions to access Magento API."))

        if not config["base_url"]:
            raise UserError(_("Magento Base URL is missing."))
        if not config["token"]:
            raise UserError(_("Magento API token is missing."))

        url = f"{config['base_url']}{endpoint}"
        headers = {
            "Authorization": f"Bearer {config['token']}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=payload,
                timeout=config["timeout"],
            )
            response.raise_for_status()
        except requests.exceptions.Timeout as exc:
            raise UserError(_("Magento API timeout.")) from exc
        except requests.exceptions.HTTPError as exc:
            msg = response.text
            try:
                err = response.json()
                msg = err.get("message", msg)
            except Exception:
                pass
            raise UserError(_("Magento API HTTP error: %s") % msg) from exc
        except requests.exceptions.RequestException as exc:
            raise UserError(_("Magento API request failed: %s") % str(exc)) from exc

        try:
            return response.json()
        except ValueError as exc:
            raise UserError(_("Magento API returned invalid JSON.")) from exc

    def get_wallet_by_id(self, wallet_id:str):
        return self._request("GET", WALLET_URL + wallet_id)

    def get_category_all(self):
        return self._request("GET", CATEGORY_ALL_URL)

    def get_transaction_all(self):
        return self._request("GET", TRANSACTION_ALL_URL)

    def get_transfer_all(self):
        return self._request("GET", TRANSFER_ALL_URL)

    def get_project_all(self):
        self._check_access()
        # hardcoded project data, cause M2 does not have endpoint and we have just few projects
        return [
            {"id": 1, "title": "Invest to Forex"},
            {"id": 2, "title": "Stolichnyi"},
            {"id": 3, "title": "Margo"},
            {"id": 4, "title": "Blog samoinvestor"},
            {"id": 6, "title": "Vacation"},
            {"id": 7, "title": "Tasya"},
            {"id": 8, "title": "х/ш 166"},
            {"id": 9, "title": "Starlink"},
            {"id": 10, "title": "OVDP"},
            {"id": 11, "title": "IBK"},
            {"id": 12, "title": "YouTube"},
        ]

    def _check_access(self) -> None:
        if not self.env.user.has_group("base.user_admin"):
            raise UserError(_("You do not have permissions to access Magento API."))
