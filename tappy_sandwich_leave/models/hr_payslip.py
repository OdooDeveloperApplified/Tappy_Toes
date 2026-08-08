from odoo import models, fields, api
from datetime import timedelta

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    sandwich_occurrences = fields.Integer(string="Sandwich Leave Occurrences", compute="_compute_sandwich_deduction", store=True)
    sandwich_deduction_amount = fields.Float(string="Sandwich Deduction Amount", compute="_compute_sandwich_deduction", store=True)

    @api.depends('employee_id', 'date_from', 'date_to', 'contract_id')
    def _compute_sandwich_deduction(self):
        for slip in self:
            slip.sandwich_occurrences = 0
            slip.sandwich_deduction_amount = 0.0

            if not slip.employee_id or not slip.date_from or not slip.date_to or not slip.contract_id:
                continue
            
            occurrences = 0
            
            # Iterate through all days in the payslip period to find Fridays
            current_date = slip.date_from
            while current_date <= slip.date_to:
                if current_date.weekday() == 4:  # 4 is Friday in Python (0=Monday)
                    friday = current_date
                    monday = friday + timedelta(days=3)
                    
                    # Check attendance for Friday
                    friday_attendance = self.env['hr.attendance'].search_count([
                        ('employee_id', '=', slip.employee_id.id),
                        ('check_in', '>=', friday),
                        ('check_in', '<', friday + timedelta(days=1))
                    ])
                    
                    if friday_attendance == 0:
                        # Employee was absent on Friday. Check Monday.
                        monday_attendance = self.env['hr.attendance'].search_count([
                            ('employee_id', '=', slip.employee_id.id),
                            ('check_in', '>=', monday),
                            ('check_in', '<', monday + timedelta(days=1))
                        ])
                        
                        if monday_attendance == 0:
                            # Absent on both Friday and following Monday -> Sandwich!
                            occurrences += 1
                
                current_date += timedelta(days=1)
                
            slip.sandwich_occurrences = occurrences
            
            if occurrences > 0:
                # Deduct 3 days salary per occurrence
                daily_wage = slip.contract_id.wage / 30.0
                slip.sandwich_deduction_amount = occurrences * (daily_wage * 3.0)
