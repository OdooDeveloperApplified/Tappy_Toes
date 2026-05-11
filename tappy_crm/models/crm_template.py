from odoo import models, fields, api
from odoo.exceptions import ValidationError

class CrmLead(models.Model):
    _inherit = "crm.lead"

    location_name = fields.Many2one('res.company',string="Location")
    qualified_lost_reason_id = fields.Many2one('qualified.lost.reason', string="Qualified Lost Reason")
    lead_offer = fields.Char(string="Lead Offer")
    utm_source = fields.Char(string="UTM Source")
    utm_medium = fields.Char(string="UTM Medium")
    utm_campaign = fields.Char(string="UTM Campaign")
    utm_content = fields.Char (string="Utm Content")
    utm_term = fields.Char (string="Utm Term")
    landing_page_url = fields.Char (string="Landing Page Url")
    gclid = fields.Char (string='gclid (Google Ads)')
    fbclid = fields.Char (string='fbclid (Meta)')
    ttclid = fields.Char (string="ttclid (TikTok)")
    lead_source = fields.Selection(
        [
            ('website', 'Website'),
            ('meta', 'Meta'),
            ('google', 'Google'),
            ('tiktok', 'TikTok'),
        ],
        string='Lead Source'
    )
    customer_status_ids = fields.Many2one('customer.status', string='Customer Status')
    lead_owner = fields.Char(string="Lead Owner")

    # Qualification fields
    preferred_offer = fields.Selection([
        ('online_learning', 'Online Learning'),
        ('learning_pods', 'Learning Pods'),
        ('at_home_service', 'At Home Service'),
        ('unknown', 'Unknown'),
    ], string="Preferred Offer")
    qualification_status = fields.Selection([
        ('unreviewed', 'Unreviewed'),
        ('needs_qualification', 'Needs Qualification'),
        ('qualified', 'Qualified'),
        ('not_fit', 'Not Fit'),
    ], string="Qualification Status", default='unreviewed')
    start_timeline = fields.Selection([
        ('immediate', 'Immediate'),
        ('this_week', 'This Week'),
        ('this_month', 'This Month'),
        ('next_term', 'Next Term'),
        ('unknown', 'Unknown'),
    ], string="Start Timeline")
    parent_main_concern = fields.Many2many('parent.concern', string="Parent's Main Concern")
    decision_maker = fields.Selection([
        ('parent', 'Parent Decides Alone'),
        ('family', 'Needs Family discussion'),
        ('unknown', 'Unknown'),
    ], string="Decision Maker")

    # Sales workflow fields
    last_contact_summary = fields.Text(string="Last Contact Summary", required=True)
    next_followup_date = fields.Date(string="Next Follow-up Date")
    contact_attempt_count = fields.Integer(string="Contact Attempt Count", default=0)
    coverage_fit = fields.Selection([
        ('in_area', 'In Area'),
        ('out_of_area', 'Out of Area'),
        ('online_only', 'Online Only'),
        ('unknown', 'Unknown'),
    ], string="Coverage Fit")
    escalation_needed = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string="Escalation Needed", default='no')
    escalation_type = fields.Selection([
        ('pricing', 'Pricing'),
        ('capacity', 'Capacity'),       
        ('service_area', 'Service Area'),
        ('compliance', 'Compliance'),
        ('complaint', 'Complaint'),
        ('duplicate', 'Duplicate'),
        ('other', 'Other'),
    ], string="Escalation Type")
    close_reason = fields.Selection([
        ('no_response', 'No Response'),
        ('no_longer_needed', 'No Longer Needed'),
        ('chose_another_provider', 'Chose Another Provider'),                  
        ('out_of_area', 'Out of Area'),
        ('wrong_offer', 'Wrong Offer'),
        ('child_too_old', 'Child Too Old'),
        ('wrong_number', 'Wrong Number'),
        ('duplicate', 'Duplicate'),
        ('spam', 'Spam'),
        ('price_objection', 'Price Objection'),
        ('future_interest', 'Future Interest'),
    ], string="Close Reason")

    # Stage milestone dates fields
    appointment_date = fields.Datetime(string="Appointment Date/Time")
    fees_sent_date = fields.Date(string="Fees Sent Date")
    trial_start_date = fields.Date(string="Trial Start Date")
    won_date = fields.Date(string="Won Date")
    currency_id = fields.Many2one('res.currency',related='company_id.currency_id',store=True,readonly=True)
    enrollment_value = fields.Monetary(string="Enrollment Value",currency_field='currency_id')

    # Reactivation fields
    legacy_ac_deal_id = fields.Char(string="Legacy AC Deal ID")
    legacy_ac_status = fields.Selection([
        ('open', 'Open'),
        ('lost', 'Lost'),  
        ('won', 'Won'),         
        ('unknown', 'Unknown'),
    ], string="Legacy AC Status")
    legacy_ac_stage = fields.Selection([
        ('fees_sent', 'Fees Sent'),
        ('appointment_booked', 'Appointment Booked'),         
        ('appointment_attended', 'Appointment Attended'),
        ('appointment_not_attended', 'Appointment Not Attended'),
        ('attended', 'Attended'),
        ('new_lead', 'New Lead'),
        ('no_history', 'No History'),
    ], string="Legacy AC Stage")
    legacy_lost_reason = fields.Char(string="Legacy Lost Reason")
    reactivation_segment = fields.Selection([
        ('priority_open', 'Priority Open'),
        ('priority_lost', 'Priority Lost'),
        ('contacts_only', 'Contacts Only'),
        ('nurture', 'Nurture'),
        ('archive_review', 'Archive Review'),
        ('past_customer', 'Past Customer'),
    ], string="Reactivation Segment")
    reactivation_priority = fields.Selection([
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ], string="Reactivation Priority")
    recommended_first_action = fields.Selection([
        ('call_first', 'Call First'),
        ('whatsapp_first', 'WhatsApp First'),
        ('first_review', 'First Review'),
    ], string="Recommended First Action")


    ################## Code to add lost leads into the pivot view starts ###################
    stage_display = fields.Char(
        string="Stage (Pivot)",
        compute="_compute_stage_display",
        store=True,
        index=True,
    )

    @api.depends("stage_id", "active")
    def _compute_stage_display(self):
        for lead in self:
            if not lead.active:
                lead.stage_display = "Lost"
            elif lead.stage_id and lead.stage_id.name == "Qualified Lost":
                lead.stage_display = "Qualified Lost"
            elif lead.stage_id:
                # Use the stage name itself for pivot grouping
                lead.stage_display = lead.stage_id.name
            else:
                lead.stage_display = "No Stage"
    ################## Code to add lost leads into the pivot view ends ###################

    # Code to open Qualified Lost Reason wizard
    def action_qualified_lost(self):
        return {
            'name': 'Qualified Lost Reason',
            'type': 'ir.actions.act_window',
            'res_model': 'qualified.lost.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lead_id': self.id,
            }
        }

    # Code to manage Lost stage transition (the lead can move to Lost stage only from Qualified Lost stage)
    def action_set_lost(self, **kwargs):
        # lost_stage = self.env['crm.stage'].search([('name', '=', 'Lost')], limit=1)
        # if not lost_stage:
        #     raise ValidationError("Please configure a stage named 'Lost' first.")

        # for lead in self:
        #     if lead.stage_id.name == "Qualified Lost":
                
        #         lead.stage_id = lost_stage.id
        
        # Step 2: Then call super() to let default Odoo logic execute
        return super(CrmLead, self).action_set_lost(**kwargs)
    
    # Code to add requirement contraints based on stage
    @api.constrains('stage_id', 'appointment_date', 'fees_sent_date', 'won_date')
    def _check_stage_requirements(self):
        for lead in self:
            stage = lead.stage_id.name

            if stage in ['Walk-Ins', 'Visit to Nursery'] and not lead.appointment_date:
                raise ValidationError("Please enter Appointment Date to proceed.")

            if stage == 'Fees Sent' and not lead.fees_sent_date:
                raise ValidationError("Please enter Fees Sent Date to proceed.")

            if stage == 'Won' and not lead.won_date:
                raise ValidationError("Please enter Won Date to proceed.")
            
            if stage == 'Qualified Lost' and not lead.close_reason:
                raise ValidationError("Please provide Close Reason to proceed.")
    
class QualifiedLostWizard(models.TransientModel):
    _name = 'qualified.lost.wizard'
    _description = 'Wizard to Qualify a Lead as Lost with Reason'

    qualified_lost_reason_id = fields.Many2one('qualified.lost.reason',string="Qualified Lost Reason", required=True)
    lead_id = fields.Many2one('crm.lead', string="Lead")
    qualified_lost_feedback = fields.Html(
        'Closing Note', sanitize=True
    )

    # Function to move the lead to qualified lost stage and set the reason
    def action_confirm(self):
        qualified_lost_stage = self.env['crm.stage'].search([('name', '=', 'Qualified Lost')], limit=1)
        if not qualified_lost_stage:
            raise ValidationError("Please configure a stage named 'Qualified Lost' first.")

        self.lead_id.write({
            'stage_id': qualified_lost_stage.id,
            'active': True,  # Archive the lead
            'qualified_lost_reason_id': self.qualified_lost_reason_id,
        })
        return {'type': 'ir.actions.act_window_close'}

class QualifiedLostReason(models.Model):
    _name = "qualified.lost.reason"
    _description = 'Qualified Lost Reason'

    name = fields.Char('Description', required=True, translate=True)
    active = fields.Boolean('Active', default=True)
    leads_count = fields.Integer('Leads Count', compute='_compute_leads_count')

    def _compute_leads_count(self):
        lead_data = self.env['crm.lead'].with_context(active_test=False)._read_group(
            [('qualified_lost_reason', '!=', False)],
            ['qualified_lost_reason'],
            ['__count'],
        )
        mapped_data = {lost_reason: count for lost_reason, count in lead_data}
        for reason in self:
            reason.leads_count = mapped_data.get(reason.name, 0)

    def action_lost_leads(self):
        return {
            'name': ('Leads'),
            'view_mode': 'list,form',
            'domain': [('qualified_lost_reason', '!=', False)],
            'res_model': 'crm.lead',
            'type': 'ir.actions.act_window',
            'context': {'create': False, 'active_test': False},
        }

class CustomerStatus(models.Model):
    _name = "customer.status"
    _description = "Customer Status"
    _inherit=['mail.thread']
    _rec_name = "customer_status"

    customer_status = fields.Char(string="Customer Status")

class ParentConcern(models.Model):
    _name = 'parent.concern'
    _description = 'Parent Concern' 
    _inherit = ['mail.thread']
    
    name = fields.Char(string='Parent Concern')