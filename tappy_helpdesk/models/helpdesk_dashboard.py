from odoo import models, fields, api
from datetime import datetime, timedelta
from collections import defaultdict
import calendar

class HelpdeskDashboard(models.TransientModel):
    _name = "helpdesk.dashboard"
    _description = "Helpdesk Dashboard"

    @api.model
    def get_complaint_data(self, year=None, month=None):
        """Get complaint data organized by weeks and built-in tags"""
        Ticket = self.env["helpdesk.ticket"]
        
        # Use provided year/month or default to current
        if not year:
            year = datetime.today().year
        if not month:
            month = datetime.today().month
            
        year = int(year)
        month = int(month)
        
        # Get the first and last day of the selected month
        first_day = datetime(year, month, 1).date()
        last_day = datetime(year, month, calendar.monthrange(year, month)[1]).date()
        
        # Calculate week ranges starting from the first day of the month
        week_ranges = []
        current_start = first_day
        
        for week_num in range(4):
            # Week end is either 6 days later or month end, whichever comes first
            week_end = min(current_start + timedelta(days=6), last_day)
            
            week_ranges.append({
                'start': current_start,
                'end': week_end,
                'week_number': week_num + 1,
                'label': f'Week {week_num + 1}'
            })
            
            # Next week starts the day after current week ends
            current_start = week_end + timedelta(days=1)
            
            # Stop if we've reached the end of the month
            if current_start > last_day:
                break
        
        # Get all tickets from the selected month
        tickets = Ticket.search([
            ("create_date", ">=", first_day.strftime('%Y-%m-%d 00:00:00')),
            ("create_date", "<=", last_day.strftime('%Y-%m-%d 23:59:59')),
            ("company_id", "=", self.env.company.id)
        ])
        
        # Initialize data structure based on actual number of weeks
        max_weeks = len(week_ranges)
        data = defaultdict(lambda: [0] * max_weeks)
        tags = set()
        
        # Process each ticket
        for ticket in tickets:
            ticket_date = ticket.create_date.date()
            
            # Find which week this ticket belongs to
            week_index = None
            for i, week_range in enumerate(week_ranges):
                if week_range['start'] <= ticket_date <= week_range['end']:
                    week_index = i
                    break
            
            if week_index is not None:
                # Use built-in tag_ids field
                if ticket.tag_ids:
                    for tag in ticket.tag_ids:
                        if tag.name:  # tag.name is the display name
                            tags.add(tag.name)
                            data[tag.name][week_index] += 1
                else:
                    # Handle tickets without tags
                    tags.add("No Tag")
                    data["No Tag"][week_index] += 1
        
        # Build response
        rows = []
        for tag in sorted(tags):
            week_counts = data[tag]
            # Pad with zeros if less than 4 weeks
            while len(week_counts) < 4:
                week_counts.append(0)
                
            row = {
                "tag": tag,
                "week_counts": week_counts[:4],  # Ensure exactly 4 weeks
                "total": sum(week_counts[:4])
            }
            rows.append(row)
        
        # Only show rows with data
        rows = [row for row in rows if row['total'] > 0]
        
        # Debug info
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info(f"=== DASHBOARD for {calendar.month_name[month]} {year} ===")
        _logger.info(f"Date range: {first_day} to {last_day}")
        for i, week_range in enumerate(week_ranges):
            _logger.info(f"Week {i+1}: {week_range['start']} to {week_range['end']}")
        _logger.info(f"Found {len(tickets)} tickets total")
        if tickets:
            _logger.info(f"First ticket: {tickets[0].create_date}")
            _logger.info(f"Last ticket: {tickets[-1].create_date}")
        _logger.info(f"Tags found: {list(tags)}")
        _logger.info("=== END DEBUG ===")
        
        return {
            "weeks": ["Week 1", "Week 2", "Week 3", "Week 4"],
            "rows": rows,
            "selected_year": year,
            "selected_month": month,
            "month_name": calendar.month_name[month],
            "total_tickets": len(tickets)
        }