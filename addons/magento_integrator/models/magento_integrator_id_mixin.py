from odoo import fields, models


class MagentoIntegratorIdMixin(models.AbstractModel):
    _name = "magento.integrator.id.mixin"
    _description = "Magento Id Binding Mixin"

    m2_id = fields.Char(string="Magento ID", index=True, copy=False)