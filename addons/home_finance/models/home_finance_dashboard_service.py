from odoo import api, models

class HomeFinanceDashboard(models.AbstractModel):
    _name = 'home.finance.dashboard.service'
    _description = 'Home Finance Dashboard Service'

    @api.model
    def get_config(self):
        icp = self.env['ir.config_parameter'].sudo()

        return {
            'current_period': icp.get_param('home_finance.current_period') or False,
        }