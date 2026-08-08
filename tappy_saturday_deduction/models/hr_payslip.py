from odoo import models, fields, api
import calendar
from datetime import date, timedelta

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    saturday_absent_count = fields.Integer(string="Saturday Absent Count", compute="_compute_saturday_deduction", store=True)
    saturday_deduction_amount = fields.Float(string="Saturday Deduction Amount", compute="_compute_saturday_deduction", store=True)

    @api.depends('employee_id', 'date_from', 'date_to', 'contract_id')
    def _compute_saturday_deduction(self):
        for slip in self:
            slip.saturday_absent_count = 0
            slip.saturday_deduction_amount = 0.0

            if not slip.employee_id or not slip.date_from or not slip.date_to or not slip.contract_id:
                continue

            # Identify the target month based on date_from
            start_date = slip.date_from
            end_date = slip.date_to
            target_month = str(start_date.month)
            target_year = str(start_date.year)

            # Find the rota for this month
            rota = self.env['hr.saturday.rota.month'].search([
                ('month', '=', target_month), 
                ('year', '=', target_year)
            ], limit=1)
            
            if not rota:
                continue

            # Find employee's specific line on the rota
            emp_rota_line = rota.line_ids.filtered(lambda l: l.employee_id.id == slip.employee_id.id)
            if not emp_rota_line:
                continue
                
            emp_rota_line = emp_rota_line[0] # taking the first matching record

            # Gather all Saturdays in that calendar month
            saturdays = []
            for day in range(1, calendar.monthrange(start_date.year, start_date.month)[1] + 1):
                d = date(start_date.year, start_date.month, day)
                if d.weekday() == 5:
                    saturdays.append(d)

            # Fetch all attendances for the payslip period
            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', slip.employee_id.id),
                ('check_in', '>=', start_date),
                ('check_in', '<=', end_date)
            ])
            checkin_days = {att.check_in.date() for att in attendances}

            # Loop through dates in the payslip period
            absent_count = 0
            current_date = start_date
            while current_date <= end_date:
                if current_date.weekday() == 5:
                    # Determine if employee was scheduled
                    is_scheduled = False
                    try:
                        sat_idx = saturdays.index(current_date)
                        if sat_idx == 0: is_scheduled = emp_rota_line.sat_1
                        elif sat_idx == 1: is_scheduled = emp_rota_line.sat_2
                        elif sat_idx == 2: is_scheduled = emp_rota_line.sat_3
                        elif sat_idx == 3: is_scheduled = emp_rota_line.sat_4
                        elif sat_idx == 4: is_scheduled = emp_rota_line.sat_5
                    except ValueError:
                        pass
                    
                    # If scheduled but no attendance record exists, they are absent
                    if is_scheduled and current_date not in checkin_days:
                        absent_count += 1
                
                current_date += timedelta(days=1)

            slip.saturday_absent_count = absent_count
            
            if absent_count > 0:
                # 1 Day deduction for each absent saturday, based on Basic Wage
                daily_wage = slip.contract_id.wage / 30.0
                slip.saturday_deduction_amount = daily_wage * absent_count
