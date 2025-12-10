from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import time, datetime, timedelta, date
import calendar
import math
import pytz
import logging

_logger = logging.getLogger(__name__)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # attendance_start_time = fields.Float(
    #     string="Attendance Start Time",
    #     help="Time (in hours) after which employee is considered late (e.g. 9.5 = 9:30 AM).",
    #     config_parameter="attendance.start_time",
    # )
    # attendance_end_time = fields.Float(
    #     string="Attendance End Time",
    #     help="Time (in hours) before which employee is considered too early or late leave.",
    #     config_parameter="attendance.end_time",
    # )
class HrAttendanceTemplate(models.Model):
    _inherit = "hr.attendance"
    _description = "HR Attendance Template"

    # is_late = fields.Boolean(string="Late Comer", compute="_compute_is_late", store=True)
    # late_minutes = fields.Char(string="Late By (HH:MM:SS)", compute="_compute_is_late", store=True)

    # @api.depends('check_in')
    # def _compute_is_late(self):
    #     Param = self.env['ir.config_parameter'].sudo()
    #     print(Param.get_param("attendance.start_time"))
    #     start_time_float = float(Param.get_param("attendance.start_time", 9.0))

    #     # Convert float (e.g. 9.5) → datetime.time
    #     hours = int(start_time_float)
    #     minutes = int(round((start_time_float % 1) * 60))
    #     work_start = time(hour=hours, minute=minutes)

    #     for rec in self:
    #         rec.is_late = False
    #         rec.late_minutes = 0
    #         if not rec.check_in:
    #             continue

    #         # Get user’s timezone
    #         tz_name = rec.employee_id.user_id.tz or self.env.user.tz or 'UTC'
    #         user_tz = pytz.timezone(tz_name)

    #         # Convert check_in (UTC → local)
    #         check_in_local = rec.check_in.astimezone(user_tz)

    #         check_in_time = check_in_local.time()

    #         if check_in_time > work_start:
    #             rec.is_late = True
    #             delta = (
    #                 datetime.combine(check_in_local.date(), check_in_time)
    #                 - datetime.combine(check_in_local.date(), work_start)
    #             )
    #             # rec.late_minutes = math.floor(delta.total_seconds() / 60)
    #             total_seconds = int(delta.total_seconds())
    #             hh, remainder = divmod(total_seconds, 3600)
    #             mm, ss = divmod(remainder, 60)
    #             rec.late_minutes = f"{hh:02d}:{mm:02d}:{ss:02d}"

    #         _logger.info(
    #             "Attendance[%s] | check_in(UTC)=%s | check_in(local)=%s | work_start=%s | tz=%s | is_late=%s | late_minutes=%s",
    #             rec.id, rec.check_in, check_in_local, work_start, tz_name, rec.is_late, rec.late_minutes
    #         )

class AttendanceReportWizard(models.TransientModel):
    _name = "attendance.report.wizard"
    _description = "Attendance Report Wizard"

    month = fields.Selection(
        [(str(m), calendar.month_name[m]) for m in range(1, 13)],
        string="Month"
    )

    # Year: dynamic range (current year → current year + 50)
    year = fields.Selection(
        [(str(y), str(y)) for y in range(date.today().year, date.today().year + 51)],
        string="Year"
    )
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    line_ids = fields.One2many("attendance.report.line", "wizard_id", string="Report Lines")

    def action_generate_report(self):
        # Pick dates: if start_date/end_date given, use them; else use month/year
        if self.start_date and self.end_date:
            start_date = self.start_date
            end_date = self.end_date
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

        # Clear previous lines for this wizard
        self.env['attendance.report.line'].search([('wizard_id', '=', self.id)]).unlink()

        for emp in employees:
            total_days = (end_date - start_date).days + 1

            # Get all attendance check-ins in range
            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', emp.id),
                ('check_in', '>=', start_date),
                ('check_in', '<=', end_date)
            ])
            checkin_days = {att.check_in.date() for att in attendances}
            present_days = len(checkin_days)
            absent_days = total_days - present_days

            self.env['attendance.report.line'].create({
                'wizard_id': self.id,
                'employee_id': emp.id,
                'present_days': present_days,
                'absent_days': absent_days,
                'total_days': total_days,
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
    _name = "attendance.report.line"
    _description = "Attendance Report Line"

    wizard_id = fields.Many2one("attendance.report.wizard", ondelete="cascade")
    employee_id = fields.Many2one("hr.employee", string="Employee")
    present_days = fields.Integer(string="Present Days")
    absent_days = fields.Integer(string="Absent Days")
    total_days = fields.Integer(string="Total Days")

    is_highest_absent = fields.Boolean(string="Highest Absent", compute="_compute_highest_flags")
    is_highest_present = fields.Boolean(string="Highest Present", compute="_compute_highest_flags")

    @api.depends("present_days", "absent_days", "wizard_id")
    def _compute_highest_flags(self):
        for wizard in self.mapped("wizard_id"):
            lines = wizard.line_ids
            if not lines:
                continue
            max_absent = max(lines.mapped("absent_days"))
            max_present = max(lines.mapped("present_days"))
            for line in lines:
                line.is_highest_absent = line.absent_days == max_absent and max_absent > 0
                line.is_highest_present = line.present_days == max_present and max_present > 0