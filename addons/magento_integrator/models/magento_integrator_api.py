import json
import logging

import requests

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

WALLET_URL = "/rest/V1/cashflow/storage/"
CATEGORY_ALL_URL = "/rest/V1/cashflow/cfitem/all"
TRANSACTION_ALL_URL = "/rest/V1/cashflow/incomes/all"
TRANSFER_ALL_URL = "/rest/V1/cashflow/transfer/all"

class MagentoIntegratorApi(models.AbstractModel):
    _name = "magento.integrator.api"
    _description = "Magento API Service"

    def _get_config(self):
        icp = self.env["ir.config_parameter"].sudo()
        return {
            "base_url": (icp.get_param("magento_integrator.base_url") or "").rstrip("/"),
            "token": icp.get_param("magento.integrator.api_token") or "",
            "timeout": int(icp.get_param("magento.integrator.timeout", default="30")),
        }

    def _request(self, method, endpoint, params=None, payload=None):
        config = self._get_config()

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


