from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import pytz
from pytz import timezone, UTC

import logging
_logger = logging.getLogger(__name__)

try:
    from zk import ZK, const
except ImportError:
    _logger.error("Please Install pyzk library.")

class BioDevice(models.Model):
    _name = "bio.device"

    name = fields.Char(string="Name")
    device_sn = fields.Char(string="Device Serial Number")
    related_company = fields.Many2one("res.company", string="Related Company")

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    employee_device_id = fields.Integer(string="Employee Device ID")

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    check_in_dubai = fields.Char(
    compute="_compute_check_in_dubai_time",
    string="Check In (Dubai)"
    )

    def _compute_check_in_dubai_time(self):
        dubai_tz = timezone("Asia/Dubai")
        for rec in self:
            if rec.check_in:
                dubai_dt = UTC.localize(rec.check_in).astimezone(dubai_tz)
                rec.check_in_dubai = dubai_dt.strftime('%d/%m/%Y %H:%M:%S')
            else:
                rec.check_in_dubai = False

    check_out_dubai = fields.Char(
    compute="_compute_dubai_check_out_time",
    string="Check Out (Dubai)"
    )

    def _compute_dubai_check_out_time(self):
        dubai_tz = timezone("Asia/Dubai")
        for rec in self:
            if rec.check_out:
                dubai_dt = UTC.localize(rec.check_out).astimezone(dubai_tz)
                rec.check_out_dubai = dubai_dt.strftime('%d/%m/%Y %H:%M:%S')
            else:
                rec.check_out_dubai = False

    def _get_attedence_from_device(self, emp_code, punch_time, verify_mode, status_code, work_code, device):
        admin_env = self.env(user=SUPERUSER_ID)

        attedence = self.env['hr.attendance'].sudo()
        related_company = self.env['bio.device'].sudo().search([('device_sn', '=', device)]).related_company
        _logger.info("this is related_company %s", related_company)
        # Search for employee using device ID
        employee = self.env['hr.employee'].sudo().search([('employee_device_id', '=', emp_code),('company_id', '=', related_company.id)], limit=1)
        _logger.info("employee %s", employee)
        
        if not employee:
            _logger.info("⚠️ No employee found for device code: %s", emp_code)
            return 

        try:
            # 1️⃣ Device sends IST time
            device_naive = datetime.strptime(punch_time, "%Y-%m-%d %H:%M:%S")

            ist_tz = pytz.timezone('Asia/Dubai')
            ist_dt = ist_tz.localize(device_naive)

            # 2️⃣ Convert IST → UTC (THIS is what Odoo wants)
            utc_dt = ist_dt.astimezone(pytz.UTC).replace(tzinfo=None)

            _logger.info(
                "Device IST %s → Stored UTC %s",
                ist_dt, utc_dt
            )

        except Exception as e:
            _logger.error("Time conversion failed: %s", e)
            return
        
        if verify_mode == "0":
            _logger.info("Clock In Record")
            # Check In
            last_open_att = attedence.search([
                ('employee_id', '=', employee.id),
                ('check_out', '=', False)
            ], limit=1)
            
            if last_open_att:
                _logger.warning("⚠️ Previous attendance was still open. Auto-closing it.")
                safe_checkout = utc_dt - timedelta(seconds=10)
                last_open_att.write({'check_out': safe_checkout})

            clock_in = attedence.create({'employee_id':employee.id,'check_in': utc_dt})
            _logger.info("clock in is %s", clock_in)
        elif verify_mode == "1":
            _logger.info("Clock Out Record")
            clock_out = attedence.search([('employee_id', '=', employee.id), ('check_out', '=', False)])
            if clock_out:
                clock_out.write({
                    'check_out': utc_dt
                })
                _logger.info("clock out is %s", clock_out)
            else:
                _logger.info("check in not found for this employee %s", employee)   
        else:
            _logger.info("verify_mode not match")
        _logger.info("Attedence Is Completed")




