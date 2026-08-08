from odoo import models, fields, api

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    late_occurrences = fields.Integer(string="Late Occurrences", compute="_compute_late_deduction", store=True)
    total_late_minutes = fields.Float(string="Total Late Minutes", compute="_compute_late_deduction", store=True)
    late_deduction_amount = fields.Float(string="Late Deduction Amount", compute="_compute_late_deduction", store=True)

    @api.depends('employee_id', 'date_from', 'date_to', 'contract_id')
    def _compute_late_deduction(self):
        for slip in self:
            slip.late_occurrences = 0
            slip.total_late_minutes = 0.0
            slip.late_deduction_amount = 0.0

            if not slip.employee_id or not slip.date_from or not slip.date_to or not slip.contract_id:
                continue
            
            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', slip.employee_id.id),
                ('check_in', '>=', slip.date_from),
                ('check_in', '<=', slip.date_to),
                ('is_late', '=', True)
            ], order='check_in asc')

            slip.late_occurrences = len(attendances)
            
            if slip.late_occurrences > 5:
                # Exclude the first 5 late occurrences from the total minutes calculation
                penalized_attendances = attendances[5:]
                total_mins = sum(penalized_attendances.mapped('late_minutes'))
                slip.total_late_minutes = total_mins
                
                daily_wage = slip.contract_id.wage / 30.0
                hourly_wage = daily_wage / 8.0
                deduction = (total_mins / 60.0) * hourly_wage
                
                # Cap at 50% of monthly wage
                max_deduction = slip.contract_id.wage * 0.5
                slip.late_deduction_amount = min(deduction, max_deduction)
