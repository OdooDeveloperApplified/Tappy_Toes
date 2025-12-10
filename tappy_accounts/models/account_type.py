from odoo import models, fields, api


class AccountTemplate(models.Model):
    _inherit = 'account.move'
   
    show_bank_details = fields.Boolean(string="Show Bank Details")
