from odoo import models, fields, api
from odoo.exceptions import ValidationError

class CrmLead(models.Model):
    _inherit = "crm.lead"

    qualified_lost_reason_id = fields.Many2one('qualified.lost.reason', string="Qualified Lost Reason")
    lead_offer = fields.Char(string="Lead Offer")
    utm_source = fields.Char(string="UTM Source")
    utm_medium = fields.Char(string="UTM Medium")
    utm_campaign = fields.Char(string="UTM Campaign")
    customer_status_ids = fields.Many2one('customer.status', string='Customer Status')
    
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