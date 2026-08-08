from odoo import api, fields, models, _
from odoo.exceptions import UserError
import calendar
from datetime import date

class HrSaturdayRotaMonth(models.Model):
    _name = 'hr.saturday.rota.month'
    _description = 'Monthly Saturday Rota'
    _order = 'year desc, month desc'

    name = fields.Char(string='Name', compute='_compute_name', store=True)
    month = fields.Selection(
        [(str(m), calendar.month_name[m]) for m in range(1, 13)],
        string="Month", required=True
    )
    year = fields.Selection(
        [(str(y), str(y)) for y in range(2020, 2050)],
        string="Year", required=True, default=lambda self: str(date.today().year)
    )

    date_sat_1 = fields.Date(string="Saturday 1", compute='_compute_saturdays', store=True)
    date_sat_2 = fields.Date(string="Saturday 2", compute='_compute_saturdays', store=True)
    date_sat_3 = fields.Date(string="Saturday 3", compute='_compute_saturdays', store=True)
    date_sat_4 = fields.Date(string="Saturday 4", compute='_compute_saturdays', store=True)
    date_sat_5 = fields.Date(string="Saturday 5", compute='_compute_saturdays', store=True)

    date_sat_1_str = fields.Char(string="Saturday 1 Str", compute='_compute_saturdays', store=True)
    date_sat_2_str = fields.Char(string="Saturday 2 Str", compute='_compute_saturdays', store=True)
    date_sat_3_str = fields.Char(string="Saturday 3 Str", compute='_compute_saturdays', store=True)
    date_sat_4_str = fields.Char(string="Saturday 4 Str", compute='_compute_saturdays', store=True)
    date_sat_5_str = fields.Char(string="Saturday 5 Str", compute='_compute_saturdays', store=True)

    line_ids = fields.One2many('hr.saturday.rota.line', 'rota_id', string='Employees')

    @api.depends('month', 'year')
    def _compute_name(self):
        for rec in self:
            if rec.month and rec.year:
                month_name = calendar.month_name[int(rec.month)]
                rec.name = f"Saturday Rota - {month_name} {rec.year}"
            else:
                rec.name = "New Rota"

    @api.depends('month', 'year')
    def _compute_saturdays(self):
        for rec in self:
            rec.date_sat_1 = False
            rec.date_sat_2 = False
            rec.date_sat_3 = False
            rec.date_sat_4 = False
            rec.date_sat_5 = False
            rec.date_sat_1_str = False
            rec.date_sat_2_str = False
            rec.date_sat_3_str = False
            rec.date_sat_4_str = False
            rec.date_sat_5_str = False
            if rec.month and rec.year:
                m = int(rec.month)
                y = int(rec.year)
                saturdays = []
                for day in range(1, calendar.monthrange(y, m)[1] + 1):
                    d = date(y, m, day)
                    if d.weekday() == 5:
                        saturdays.append(d)
                
                if len(saturdays) > 0:
                    rec.date_sat_1 = saturdays[0]
                    rec.date_sat_1_str = saturdays[0].strftime('%d/%m/%Y')
                if len(saturdays) > 1:
                    rec.date_sat_2 = saturdays[1]
                    rec.date_sat_2_str = saturdays[1].strftime('%d/%m/%Y')
                if len(saturdays) > 2:
                    rec.date_sat_3 = saturdays[2]
                    rec.date_sat_3_str = saturdays[2].strftime('%d/%m/%Y')
                if len(saturdays) > 3:
                    rec.date_sat_4 = saturdays[3]
                    rec.date_sat_4_str = saturdays[3].strftime('%d/%m/%Y')
                if len(saturdays) > 4:
                    rec.date_sat_5 = saturdays[4]
                    rec.date_sat_5_str = saturdays[4].strftime('%d/%m/%Y')

    def action_generate_lines(self):
        self.ensure_one()
        employees = self.env['hr.employee'].search([])
        existing_employees = self.line_ids.mapped('employee_id')
        
        lines_to_create = []
        for emp in employees:
            if emp not in existing_employees:
                lines_to_create.append((0, 0, {
                    'employee_id': emp.id,
                }))
        if lines_to_create:
            self.write({'line_ids': lines_to_create})
        return True


class HrSaturdayRotaLine(models.Model):
    _name = 'hr.saturday.rota.line'
    _description = 'Saturday Rota Line'

    rota_id = fields.Many2one('hr.saturday.rota.month', string='Rota Month', required=True, ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    
    sat_1 = fields.Boolean(string="Sat 1")
    sat_2 = fields.Boolean(string="Sat 2")
    sat_3 = fields.Boolean(string="Sat 3")
    sat_4 = fields.Boolean(string="Sat 4")
    sat_5 = fields.Boolean(string="Sat 5")
