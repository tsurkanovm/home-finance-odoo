from odoo import models, fields, api, _
from odoo.exceptions import UserError
from ..constant import STATEMENT_TYPE_SELECTION

class StatementImportRuleLine(models.Model):
    _name = 'home_finance.statement.import.rule.line'
    _description = 'Statement Import Rule Line'

    rule_id = fields.Many2one('home_finance.statement.import.rule', string='Import Rule', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10, index=True)
    type = fields.Selection(string='Movement Type', required=True, selection=STATEMENT_TYPE_SELECTION)
    wallet_id = fields.Many2one('home_finance.wallet', string='Wallet')
    category_id = fields.Many2one('home_finance.category', string='Category',
                                  domain="[('type', '=', type)]")
    purpose_key_word = fields.Char(string='Purpose Keyword', index=True)
    commentary_key_word = fields.Char(string='Commentary Keyword')

    # def action_save_and_duplicate(self):
    #     self.ensure_one()
    #
    #     if not self.id or not self.rule_id.id:
    #         raise UserError(_("Please save the import rule first, then duplicate the line."))
    #
    #     duplicated_line = self.copy({
    #         'rule_id': self.rule_id.id,
    #         'sequence': self.sequence + 1,
    #     })
    #
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Duplicated Rule Line',
    #         'res_model': 'home_finance.statement.import.rule.line',
    #         'view_mode': 'form',
    #         'res_id': duplicated_line.id,
    #         'target': 'new',
    #     }

    # def action_save_and_duplicate(self):
    #     self.ensure_one()
    #
    #     if not self.rule_id:
    #         raise UserError(_("Please save the import rule first, then duplicate the line."))
    #
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': _('Duplicate Rule Line'),
    #         'res_model': 'home_finance.statement.import.rule.line',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'context': {
    #             'default_rule_id': self.rule_id.id,
    #             'default_sequence': self.sequence + 1,
    #             'default_type': self.type,
    #             'default_wallet_id': self.wallet_id.id if self.wallet_id else False,
    #             'default_category_id': self.category_id.id if self.category_id else False,
    #             'default_purpose_key_word': self.purpose_key_word,
    #             'default_commentary_key_word': self.commentary_key_word,
    #         },
    #     }

    def action_save_and_duplicate(self):
        self.ensure_one()

        if not self.rule_id:
            raise UserError(_("Please save the import rule first, then duplicate the line."))

        self.copy({
            'rule_id': self.rule_id.id,
            'sequence': self.sequence + 1,
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }