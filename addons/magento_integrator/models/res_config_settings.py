from datetime import date
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    magento_base_url = fields.Char(
        string="Magento Base URL",
        config_parameter="magento_integrator.base_url",
    )
    magento_api_token = fields.Char(
        string="Magento API Token",
        config_parameter="magento_integrator.api_token",
    )
    magento_timeout = fields.Integer(
        string="Magento API Timeout (seconds)",
        config_parameter="magento_integrator.timeout",
        default=30,
    )
