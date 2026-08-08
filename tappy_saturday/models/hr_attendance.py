from odoo import api, fields, models
import calendar
from datetime import date

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    is_sat_present = fields.Boolean(string="Saturday Present", compute="_compute_sat_status", store=False)

    @api.depends('check_in', 'employee_id')
    def _compute_sat_status(self):
        for rec in self:
            rec.is_sat_present = False
            
            if not rec.check_in or not rec.employee_id:
                continue

            check_in_date = rec.check_in.date()
            if check_in_date.weekday() != 5:  # Not a Saturday
                continue

            # It is a Saturday check-in. Check the rota.
            month_str = str(check_in_date.month)
            year_str = str(check_in_date.year)
            
            rota = self.env['hr.saturday.rota.month'].search([
                ('month', '=', month_str),
                ('year', '=', year_str)
            ], limit=1)

            is_scheduled = False
            if rota:
                emp_rota_line = rota.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id)
                if emp_rota_line:
                    # Find which Saturday of the month this is
                    saturdays = []
                    for day in range(1, calendar.monthrange(check_in_date.year, check_in_date.month)[1] + 1):
                        d = date(check_in_date.year, check_in_date.month, day)
                        if d.weekday() == 5:
                            saturdays.append(d)
                    
                    try:
                        sat_idx = saturdays.index(check_in_date)
                        if sat_idx == 0: is_scheduled = emp_rota_line.sat_1
                        elif sat_idx == 1: is_scheduled = emp_rota_line.sat_2
                        elif sat_idx == 2: is_scheduled = emp_rota_line.sat_3
                        elif sat_idx == 3: is_scheduled = emp_rota_line.sat_4
                        elif sat_idx == 4: is_scheduled = emp_rota_line.sat_5
                    except ValueError:
                        pass
            
            if is_scheduled:
                rec.is_sat_present = True
