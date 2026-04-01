from odoo import models

class Project(models.Model):
    _name = "home_finance.project"
    _inherit = ["home_finance.project", "magento_integrator.id.mixin"]

    def import_projects(self):
        projects = self.env['magento_integrator.api'].get_project_all()
        for item in projects:
            self.create({
                'm2_id': item['id'],
                'name': item['title'],
            })