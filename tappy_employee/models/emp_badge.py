from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

class GamificationBadgeEmployee(models.Model):
    _name = 'gamification.badge.employee'
    _description = 'Employee Badge'
    _order = 'create_date desc'

    employee_id = fields.Many2one('hr.employee',string='Employee',required=True)
    badge_id = fields.Many2one('gamification.badge', string='Badge Name',required=True)
    sender_id = fields.Many2one('res.users',string='Granted By')
    comment = fields.Text(string='Comment')
    create_date = fields.Date(readonly=True)

class GamificationBadgeEmployeeWizard(models.TransientModel):
    _name = 'gamification.badge.employee.wizard'
    _description = 'Grant Badge to Employee'

    badge_id = fields.Many2one('gamification.badge', string='Badge Name',required=True)
    employee_id = fields.Many2one('hr.employee',required=True)
    comment = fields.Text(string='Comment')

    def action_grant_badge(self):
        self.ensure_one()

        if not self.employee_id:
            raise UserError(_('Please select an employee.'))

        self.env['gamification.badge.employee'].create({
            'employee_id': self.employee_id.id,
            'badge_id': self.badge_id.id,
            'comment': self.comment,
        })

        return {'type': 'ir.actions.act_window_close'}

