from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)

class AccountReport(models.Model):
    _inherit = 'account.move'

    file_upload = fields.Image(string="File Upload", max_width=1600, max_height=1600)
    is_restricted_manager = fields.Boolean(string="Is Restricted Manager", compute="_compute_is_restricted_manager")

    @api.depends('company_id')
    def _compute_is_restricted_manager(self):
        for move in self:
            move.is_restricted_manager = self.env.user.has_group('app_account_profit_and_loss.group_hide_delete_account_move')
            _logger.info("Evaluating Restricted Manager for Bill %s: %s", move.id, move.is_restricted_manager)
