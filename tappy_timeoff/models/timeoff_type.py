from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class TimeOffType(models.Model):
    _inherit = "hr.leave.type"
    _description = "HR Leave Type Template"

    
