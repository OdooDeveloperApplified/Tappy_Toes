from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import UserError
import logging
from math import ceil
_logger = logging.getLogger(__name__)

class HelpdeskTemplate(models.Model):
    _inherit = "helpdesk.ticket"

    complaint_tags_ids = fields.Many2many('complaint.tags', string='Complaint Tags', required=True)
    staff_involved = fields.Many2one('hr.employee', string='Staff Involved')
    incident_time = fields.Datetime(string='Incident Time',required=True)
    
    # Complaint Investigation fields
    what_happened = fields.Html(string='What took place?')
    nursery_action = fields.Html(string='Action taken by nursery')
    parent_response = fields.Html(string='Parent response')
    root_cause = fields.Html(string='Root cause')
    prevention_measures = fields.Html(string='Preventive measures')
    training_protocols = fields.Html(string='New protocols/training')
    solved_date = fields.Datetime(string="Solved Date", readonly=True)
    complaint_type = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External'),
    ], string='Complaint Type', required=True)

    ######## SLA tracking fields to create custom pivot view for unresolved tickets dashboard starts ##########
    complaint_priority = fields.Selection([
        ('critical', 'Critical'),
        ('moderate', 'Moderate'),
        ('minor', 'Minor')
    ], string='Priority', compute='_compute_priority_from_tags', store=True)
    
    days_since_created = fields.Integer(string='Days Since Created', compute='_compute_days_since_created', store=True)
    sla_deadline_days = fields.Integer(string='SLA Deadline (Days)', compute='_compute_sla_deadline_days', store=True)
    days_past_sla = fields.Integer(string='Days Past SLA', compute='_compute_days_past_sla', store=True)
    is_sla_overdue = fields.Boolean(string='SLA Overdue', compute='_compute_days_past_sla', store=True)
    
    @api.depends('tag_ids')
    def _compute_priority_from_tags(self):
        """Get priority from tag names containing critical/moderate/minor"""
        for ticket in self:
            priority = 'minor'
            
            if ticket.tag_ids:
                tag_names = [tag.name.lower() for tag in ticket.tag_ids]
                
                if any('critical' in tag for tag in tag_names):
                    priority = 'critical'
                elif any('moderate' in tag for tag in tag_names):
                    priority = 'moderate'
                elif any('minor' in tag for tag in tag_names):
                    priority = 'minor'
            
            ticket.complaint_priority = priority
    
    @api.depends('create_date')
    def _compute_days_since_created(self):
        # for ticket in self:
        #     if ticket.create_date:
        #         create_dt = fields.Datetime.from_string(ticket.create_date)  # Parses string to datetime
        #         now_dt = fields.Datetime.now()  # Current UTC time in correct format
        #         delta = now_dt - create_dt
        #         ticket.days_since_created = ceil(delta.total_seconds() / 86400)
        #     else:
        #         ticket.days_since_created = 0
        for ticket in self:
            if ticket.create_date:
                create_date = fields.Datetime.from_string(ticket.create_date).date()
                today_date = fields.Date.context_today(ticket)  # returns current date in user's timezone
                ticket.days_since_created = (today_date - create_date).days
            else:
                ticket.days_since_created = 0
    
    @api.depends('complaint_priority')
    def _compute_sla_deadline_days(self):
        """Set SLA deadline based on priority"""
        sla_days = {
            'critical': 3,
            'moderate': 5,
            'minor': 7
        }
        
        for ticket in self:
            ticket.sla_deadline_days = sla_days.get(ticket.complaint_priority, 7)
    
    @api.depends('days_since_created', 'sla_deadline_days', 'solved_date')
    def _compute_days_past_sla(self):
        """Calculate days past SLA deadline for unresolved tickets only"""
        for ticket in self:
            # Only calculate for unresolved tickets
            if not ticket.solved_date:
                if ticket.days_since_created > ticket.sla_deadline_days:
                    ticket.days_past_sla = ticket.days_since_created - ticket.sla_deadline_days
                    ticket.is_sla_overdue = True
                else:
                    ticket.days_past_sla = 0
                    ticket.is_sla_overdue = False
            else:
                # Ticket is solved, no SLA breach for current purposes
                ticket.days_past_sla = 0
                ticket.is_sla_overdue = False
    ######## SLA tracking fields to create custom pivot view for unresolved tickets dashboard ends ##########

    ################ Cron logic to auto update the Days since created column and Days past due starts ##################
    @api.model
    def recompute_sla_fields_daily(self):
        _logger.info("Recomputing SLA fields for all helpdesk tickets...")
        tickets = self.search([])
        for ticket in tickets:
            if ticket.create_date:
                create_date = fields.Datetime.from_string(ticket.create_date).date()
                today_date = fields.Date.context_today(ticket)
                days_since_created = (today_date - create_date).days

                # Compute SLA deadline days
                sla_days = {
                    'critical': 3,
                    'moderate': 5,
                    'minor': 7
                }
                complaint_priority = ticket.complaint_priority or 'minor'
                sla_deadline_days = sla_days.get(complaint_priority, 7)

                # Compute days past SLA and overdue flag
                if not ticket.solved_date and days_since_created > sla_deadline_days:
                    days_past_sla = days_since_created - sla_deadline_days
                    is_sla_overdue = True
                else:
                    days_past_sla = 0
                    is_sla_overdue = False

                ticket.write({
                    'days_since_created': days_since_created,
                    'sla_deadline_days': sla_deadline_days,
                    'days_past_sla': days_past_sla,
                    'is_sla_overdue': is_sla_overdue,
                })
    ################ Cron logic to auto update the Days since created column and Days past due ends ##################

    # Code to prevent moving back stages in kanban view
    def _prevent_reverse_stage_move(self, vals):
        if 'stage_id' in vals:
            for ticket in self:
                old_stage = ticket.stage_id
                new_stage = self.env['helpdesk.stage'].browse(vals['stage_id'])
                
                # Prevent reverse move based on sequence
                if new_stage.sequence < old_stage.sequence:
                    raise UserError(_("You cannot move the ticket back to a previous stage."))

    def write(self, vals):
        solved_stage = self.env['helpdesk.stage'].search([('name', '=', 'Solved')], limit=1)
        for ticket in self:
            if 'stage_id' in vals and solved_stage:
                new_stage_id = vals.get('stage_id')
                if new_stage_id == solved_stage.id and not ticket.solved_date:
                    vals['solved_date'] = datetime.now()

        # Enforce stage movement restriction in kanban view
        self._prevent_reverse_stage_move(vals)
        return super(HelpdeskTemplate, self).write(vals)

    def create(self, vals):
        solved_stage = self.env['helpdesk.stage'].search([('name', '=', 'Solved')], limit=1)
        if 'stage_id' in vals and solved_stage:
            if vals['stage_id'] == solved_stage.id:
                vals['solved_date'] = datetime.now()
        return super(HelpdeskTemplate, self).create(vals)
    
    ###################### Custom pivot view code for helpdesk dashboard starts ##############################

    week_of_month = fields.Selection([
        ('1', 'Week 1'),
        ('2', 'Week 2'), 
        ('3', 'Week 3'),
        ('4', 'Week 4'),
    ], string='Week of Month', compute='_compute_week_of_month', store=True)
    
    @api.depends('create_date')
    def _compute_week_of_month(self):
        for record in self:
            if record.create_date:
                day = record.create_date.day
                if 1 <= day <= 7:
                    record.week_of_month = '1'
                elif 8 <= day <= 14:
                    record.week_of_month = '2'
                elif 15 <= day <= 21:
                    record.week_of_month = '3'
                else:
                    record.week_of_month = '4'
            else:
                record.week_of_month = False

    ###################### Custom pivot view code for helpdesk dashboard ends ##############################

class ComplaintTags(models.Model):

    _name = "complaint.tags"
    _description = "Complaint Tags"
    _inherit=['mail.thread']
    _rec_name = "complaint_tags"

    complaint_tags = fields.Char(string="Complaint Tags")
