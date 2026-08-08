from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)

class AccountReport(models.Model):
    _inherit = 'account.move'

    file_upload = fields.Image(string="File Upload", max_width=1600, max_height=1600)
