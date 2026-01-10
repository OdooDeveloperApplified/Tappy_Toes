from odoo import fields, models, api, _
from datetime import date

class EmployeeTemplate(models.Model):
    _inherit = "hr.employee"

    mother_name = fields.Char(string="Mother's Name")
    joining_date = fields.Date(string='Joining Date')
    eid_expiry_date = fields.Date(string='EID Expiry Date')
    sponsor_name = fields.Char(string="Sponsor's Name (if applicable)")
    visa_type_ids = fields.Many2one('visa.type',string="Visa Type")
    visa_issue_date = fields.Date(string='Visa Issue Date')
    passport_expiry_date = fields.Date(string='Passport Expiry Date')
    total_salary = fields.Float(string='Total Salary')
    labour_card_no = fields.Char(string='Labour Card Number')
    bank_info = fields.Char(string="Bank Info")
    insurance_number = fields.Char(string='Insurance Number')
    insurance_expiry = fields.Date(string='Insurance Expiration')
    insurance_issue = fields.Date(string='Insurance Issue Date')
    first_aid = fields.Char(string='First Aid')
    first_aid_expiry = fields.Date(string='First Aid Expiry')
    first_aid_issue = fields.Date(string='First Aid Issue Date')
    ohc = fields.Char(string="OHC")
    ohc_expiry_date = fields.Date(string='OHC Expiry')
    ohc_issue_date = fields.Date(string='OHC Issue Date')
    emergency_relation = fields.Char(string='Relation')
    emergency_address = fields.Text(string='Complete Address')
    fire_safety = fields.Char(string="Fire Safety")
    fire_expiry_date = fields.Date(string='Fire Safety Expiry')
    fire_issue_date = fields.Date(string='Fire Safety Issue Date')
    warning_count = fields.Integer(string="Warning/s (written)")
    documents = fields.Many2many('ir.attachment', 'hr_employee_doc_attach_rel',
        'doc_id', 'attach_id', string="Warning Documents", copy=False,
        help='You can attach the copy of your document')
    warning_verbal = fields.Integer(string="Warning/s (verbal)")

    ################ Visa Renewal Status Computation starts ################
    visa_renewal_status = fields.Selection([
        ('active', 'Active'),
        ('expiring_soon', 'Expiring Soon'),
        ('expired', 'Expired')
    ], string='Visa Renewal Status', compute='_compute_visa_renewal_status', store=True)

    @api.depends('visa_expire')
    def _compute_visa_renewal_status(self):
        today = date.today()
        for emp in self:
            if not emp.visa_expire:
                emp.visa_renewal_status = False
                continue

            days_to_expiry = (emp.visa_expire - today).days
            if days_to_expiry < 0:
                emp.visa_renewal_status = 'expired'
            elif days_to_expiry <= 30:
                emp.visa_renewal_status = 'expiring_soon'
            else:
                emp.visa_renewal_status = 'active'
    ################ Visa Renewal Status Computation ends ################

    ################ Work Permit Status Computation starts ################
    work_permit_status = fields.Selection([
        ('active', 'Active'),
        ('expiring_soon', 'Expiring Soon'),
        ('expired', 'Expired')
    ], string='Work Permit Status', compute='_compute_work_permit_status', store=True)

    @api.depends('work_permit_expiration_date')
    def _compute_work_permit_status(self):
        today = date.today()
        for emp in self:
            if not emp.work_permit_expiration_date:
                emp.work_permit_status = False
                continue

            days_to_expiry = (emp.work_permit_expiration_date - today).days
            if days_to_expiry < 0:
                emp.work_permit_status = 'expired'
            elif days_to_expiry <= 30:
                emp.work_permit_status = 'expiring_soon'
            else:
                emp.work_permit_status = 'active'
    ################ Work Permit Status Computation ends ################
    
    ################# Passport Renewal Status Computation starts ################
    passport_renewal_status = fields.Selection([
        ('active', 'Active'),
        ('expiring_soon', 'Expiring Soon'),
        ('expired', 'Expired')
    ], string='Passport Renewal Status', compute='_compute_passport_renewal_status', store=True)

    @api.depends('passport_expiry_date')
    def _compute_passport_renewal_status(self):
        today = date.today()
        for emp in self:
            if not emp.passport_expiry_date:
                emp.passport_renewal_status = False
                continue

            days_to_expiry = (emp.passport_expiry_date - today).days
            if days_to_expiry < 0:
                emp.passport_renewal_status = 'expired'
            elif days_to_expiry <= 30:
                emp.passport_renewal_status = 'expiring_soon'
            else:
                emp.passport_renewal_status = 'active'
    ################# Passport Renewal Status Computation ends ################

    ################ Emirates ID Renewal Status Computation starts ################
    eid_renewal_status = fields.Selection([
        ('active', 'Active'),
        ('expiring_soon', 'Expiring Soon'),
        ('expired', 'Expired')
    ], string='Emirates ID Renewal Status', compute='_compute_eid_renewal_status', store=True)

    @api.depends('eid_expiry_date')
    def _compute_eid_renewal_status(self):
        today = date.today()
        for emp in self:
            if not emp.eid_expiry_date:
                emp.eid_renewal_status = False
                continue

            days_to_expiry = (emp.eid_expiry_date - today).days
            if days_to_expiry < 0:
                emp.eid_renewal_status = 'expired'
            elif days_to_expiry <= 30:
                emp.eid_renewal_status = 'expiring_soon'
            else:
                emp.eid_renewal_status = 'active'
    ################ Emirates ID Renewal Status Computation ends ################

    ################ Insurance Renewal Status Computation starts ################
    insurance_renewal_status = fields.Selection([
        ('active', 'Active'),
        ('expiring_soon', 'Expiring Soon'),
        ('expired', 'Expired')
    ], string='Insurance Renewal Status', compute='_compute_insurance_renewal_status', store=True)

    @api.depends('insurance_expiry')
    def _compute_insurance_renewal_status(self):
        today = date.today()
        for emp in self:
            if not emp.insurance_expiry:
                emp.insurance_renewal_status = False
                continue

            days_to_expiry = (emp.insurance_expiry - today).days
            if days_to_expiry < 0:
                emp.insurance_renewal_status = 'expired'
            elif days_to_expiry <= 30:
                emp.insurance_renewal_status = 'expiring_soon'
            else:
                emp.insurance_renewal_status = 'active'
    ################ Insurance Renewal Status Computation ends ################
    
    ################# Helpdesk Ticket Count per employee starts ################
    helpdesk_ticket_count = fields.Integer(
        string="Helpdesk Tickets",
        compute="_compute_helpdesk_ticket_count"
    )

    def _compute_helpdesk_ticket_count(self):
        Helpdesk = self.env['helpdesk.ticket']
        for emp in self:
            if emp.id:
                emp.helpdesk_ticket_count = Helpdesk.search_count([
                    ('staff_involved', '=', emp.id)
                ])
            else:
                emp.helpdesk_ticket_count = 0

    def action_view_helpdesk_tickets(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Helpdesk Tickets',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'list,form',
            'domain': [('staff_involved', '=', self.id)],
            'context': {'default_staff_involved': self.id},
        }
    ################# Helpdesk Ticket Count per employee ends ################

class VisaType(models.Model):
    _name = 'visa.type'
    _description = 'Visa Type' 
    _inherit = ['mail.thread']
    
    name = fields.Char(string='Visa Type')



