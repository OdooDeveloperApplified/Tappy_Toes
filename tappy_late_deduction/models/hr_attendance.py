from odoo import fields, models, api
from datetime import datetime, time, date
import pytz
import math

class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    is_late = fields.Boolean(string="Late", compute="_compute_is_late", store=True)
    late_minutes = fields.Float(string="Late Minutes", compute="_compute_is_late", store=True)

    @api.depends('check_in', 'employee_id')
    def _compute_is_late(self):
        for rec in self:
            rec.is_late = False
            rec.late_minutes = 0.0
            
            if not rec.check_in or not rec.employee_id:
                continue

            # Determine timezone
            tz_name = rec.employee_id.tz or self.env.user.tz or 'UTC'
            user_tz = pytz.timezone(tz_name)

            # Convert check_in UTC -> Local time
            check_in_utc = pytz.utc.localize(rec.check_in)
            check_in_local = check_in_utc.astimezone(user_tz)
            check_in_time = check_in_local.time()
            check_in_dayofweek = str(check_in_local.weekday())

            # Determine scheduled start time
            work_start = time(hour=9, minute=0) # Default
            
            # Check resource calendar for the scheduled start time for this day
            calendar = rec.employee_id.resource_calendar_id
            if calendar:
                # Find attendance for this day
                day_attendances = calendar.attendance_ids.filtered(lambda a: a.dayofweek == check_in_dayofweek)
                if day_attendances:
                    # Usually there are morning and afternoon shifts. Take the minimum start time.
                    start_float = min(day_attendances.mapped('hour_from'))
                    hours = int(start_float)
                    minutes = int(round((start_float % 1) * 60))
                    work_start = time(hour=hours, minute=minutes)

            # Check if late
            if check_in_time > work_start:
                # Calculate time difference in minutes
                delta = (
                    datetime.combine(check_in_local.date(), check_in_time) -
                    datetime.combine(check_in_local.date(), work_start)
                )
                total_minutes = delta.total_seconds() / 60.0
                
                # Apply 10 minute grace period (triggers strictly on 11+ minutes)
                if total_minutes >= 11:
                    rec.is_late = True
                    rec.late_minutes = total_minutes
