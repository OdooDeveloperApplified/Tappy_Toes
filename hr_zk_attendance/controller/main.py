from odoo import http
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)

class BiometricController(http.Controller):
    # @http.route('/bio/attendance', type='http', auth='none', methods=['POST'], csrf=False, cors='*')
    # def bio_attendance(self, **kw):
    #     _logger.info("Received params: %s", kw)
    #     _logger.info("Raw body: %s", http.request.httprequest.data)
    #     return "OK"

    # @http.route('/bio/attendance/iclock/ping', type='http', auth='none', methods=['GET'], csrf=False, cors='*')
    # def bio_ping(self, **kw):
    #     _logger.info("Ping received with: %s", kw)
    #     return "OK"

    # @http.route('/bio/attendance/iclock/getrequest', type='http', auth='none', methods=['GET'], csrf=False, cors='*')
    # def bio_getrequest(self, **kw):
    #     _logger.info("Get request params: %s", kw)
    #     return "OK"

    @http.route('/bio/attendance/iclock/cdata', type='http', auth='public', methods=['GET', 'POST'], csrf=False, cors='*')
    def bio_cdata(self, **kw):
        # Log the URL query parameters (e.g. SN, table, etc.)
        _logger.info("Received CDATA params: %s", kw)

        # Get the raw body data (bytes)
        raw_data = http.request.httprequest.data

        # Decode to string (device sends plain text)
        body_text = raw_data.decode('utf-8', errors='ignore').strip()
        _logger.info("Raw body text:\n%s", body_text)

        # Optional: parse attendance lines
        hr_attedence = request.env['hr.attendance']
        device = kw.get('SN')
        if kw.get('table') == 'ATTLOG' and body_text:
            lines = body_text.splitlines()
            for line in lines:
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    emp_code = parts[0].strip()
                    punch_time = parts[1].strip()
                    verify_mode = parts[2] if len(parts) > 2 else None
                    status_code = parts[3] if len(parts) > 3 else None
                    work_code = parts[-1] if len(parts) > 4 else None

                    _logger.info(
                        "Employee: %s | Time: %s | Verify: %s | Status: %s | Workcode: %s",
                        emp_code, punch_time, verify_mode, status_code, work_code
                    )
                    hr_attedence.sudo()._get_attedence_from_device(emp_code, punch_time, verify_mode, status_code, work_code, device)

        return "OK"