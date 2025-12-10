from odoo import http
from odoo.http import request
import logging
import json

_logger = logging.getLogger(__name__)

class HelpdeskDashboardController(http.Controller):

    @http.route('/helpdesk/dashboard/page', type='http', auth='user', website=True)
    def helpdesk_dashboard_page(self):
        """Render the dashboard web page"""
        return request.render('tappy_helpdesk.helpdesk_dashboard_page')

    @http.route('/helpdesk/dashboard/data', type='json', auth='user')
    def helpdesk_dashboard_data(self, year=None, month=None):
        """API endpoint for dashboard data with optional year/month filters"""
        try:
            _logger.info(f"Dashboard data API called with year={year}, month={month}")
            
            # Get the dashboard model
            dashboard_model = request.env['helpdesk.dashboard'].sudo()
            
            # Get complaint data with filters
            data = dashboard_model.get_complaint_data(year=year, month=month)
            data['company_name'] = request.env.user.company_id.name
            
            _logger.info(f"Dashboard data retrieved for {data.get('month_name')} {data.get('selected_year')}")
            
            return data
            
        except Exception as e:
            _logger.error(f"Error in dashboard controller: {str(e)}")
            return {
                "weeks": ["Week 1", "Week 2", "Week 3", "Week 4"],
                "rows": [],
                "error": str(e)
            }

    @http.route('/helpdesk/dashboard', type='json', auth='user')
    def helpdesk_dashboard_data_legacy(self):
        """Legacy API endpoint for backward compatibility"""
        return self.helpdesk_dashboard_data()