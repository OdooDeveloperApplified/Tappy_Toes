from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import date, timedelta
import calendar

class AttendanceReportWizard(models.TransientModel):
    _inherit = "attendance.report.wizard"

    def action_generate_report(self):
        # We need to completely override or modify the loop.
        # Since we want to change `total_days` and `absent_days`, we will let super() run or rewrite the logic.
        # It's better to rewrite the core logic for the days calculation.
        
        if self.start_date and self.end_date:
            start_date = self.start_date
            end_date = self.end_date
            month = start_date.month
            year = start_date.year
        elif self.month and self.year:
            month = int(self.month)
            year = int(self.year)
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
        else:
            raise UserError("Please select either Month & Year or Start & End Date.")

        employees = self.env['hr.employee'].search([])

        # Clear previous lines
        self.env['attendance.report.line'].search([('wizard_id', '=', self.id)]).unlink()

        # Fetch the rota for this month
        rota = self.env['hr.saturday.rota.month'].search([('month', '=', str(month)), ('year', '=', str(year))], limit=1)
        
        # Prepare saturday dates
        saturdays = []
        for day in range(1, calendar.monthrange(year, month)[1] + 1):
            d = date(year, month, day)
            if d.weekday() == 5:
                saturdays.append(d)

        for emp in employees:
            # Get all attendance check-ins in range
            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', emp.id),
                ('check_in', '>=', start_date),
                ('check_in', '<=', end_date)
            ])
            checkin_days = {att.check_in.date() for att in attendances}
            
            # Calculate working days and saturdays
            total_working_days = 0
            saturday_present = 0
            saturday_absent = 0
            saturday_na = 0
            
            # Find the employee's rota line
            emp_rota_line = rota.line_ids.filtered(lambda l: l.employee_id.id == emp.id) if rota else False
            
            # Iterate through all dates
            current_date = start_date
            while current_date <= end_date:
                if current_date.weekday() < 5:  # Monday to Friday
                    total_working_days += 1
                elif current_date.weekday() == 5:  # Saturday
                    # Check if employee is scheduled to work this Saturday
                    is_scheduled = False
                    if emp_rota_line:
                        try:
                            sat_idx = saturdays.index(current_date)
                            if sat_idx == 0: is_scheduled = emp_rota_line.sat_1
                            elif sat_idx == 1: is_scheduled = emp_rota_line.sat_2
                            elif sat_idx == 2: is_scheduled = emp_rota_line.sat_3
                            elif sat_idx == 3: is_scheduled = emp_rota_line.sat_4
                            elif sat_idx == 4: is_scheduled = emp_rota_line.sat_5
                        except ValueError:
                            pass
                    
                    if is_scheduled:
                        total_working_days += 1
                        if current_date in checkin_days:
                            saturday_present += 1
                        else:
                            saturday_absent += 1
                    else:
                        saturday_na += 1
                
                current_date += timedelta(days=1)

            present_days = len(checkin_days)
            absent_days = total_working_days - present_days
            # Ensure absent days don't go negative if they checked in on a Sunday/N/A Saturday
            if absent_days < 0:
                absent_days = 0

            total_saturdays = len(saturdays)
            
            self.env['attendance.report.line'].create({
                'wizard_id': self.id,
                'employee_id': emp.id,
                'present_days': present_days,
                'absent_days': absent_days,
                'total_days': total_working_days,
                'saturday_assigned': f"{saturday_present + saturday_absent}/{total_saturdays}",
                'saturday_present_days': f"{saturday_present}/{total_saturdays}",
                'saturday_absent_days': f"{saturday_absent}/{total_saturdays}",
                'saturday_na_days': f"{saturday_na}/{total_saturdays}",
            })

        return {
            "type": "ir.actions.act_window",
            "name": "Attendance Report",
            "res_model": "attendance.report.line",
            "view_mode": "list",
            "domain": [("wizard_id", "=", self.id)],
            "target": "current",
        }

class AttendanceReportLine(models.TransientModel):
    _inherit = "attendance.report.line"

    saturday_assigned = fields.Char(string="Sat Assigned")
    saturday_present_days = fields.Char(string="Sat Present")
    saturday_absent_days = fields.Char(string="Sat Absent")
    saturday_na_days = fields.Char(string="Sat N/A")
