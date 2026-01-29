from odoo import models, fields

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    location_name = fields.Char(string="Location")
