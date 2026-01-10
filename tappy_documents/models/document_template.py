from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import date
from datetime import timedelta

class CompanyDocument(models.Model):
    _name = "company.document"
    _description = "Company Document"
    _inherit = ["mail.thread", "mail.activity.mixin"]
   

    
    name = fields.Char(string="License Name", required=True, tracking=True)

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        tracking=True
    )

    license_type = fields.Char(string="Type of License", required=True, tracking=True)

    purpose = fields.Text(string="Purpose", tracking=True)

    government_body = fields.Char(string="Government Body", tracking=True)

    issue_date = fields.Date(string="Issue Date", required=True, tracking=True)
    expiry_date = fields.Date(string="Expiry Date", required=True, tracking=True)

    days_to_expiry = fields.Integer(
        string="Days to Expiry",
        compute="_compute_days_to_expiry",
        store=True
    )

    renewal_state = fields.Selection([
        ("valid", "Valid"),
        ("expiring", "Expiring Soon"),
        ("expired", "Expired"),
    ], compute="_compute_renewal_state", store=True)

    attachment_ids = fields.Many2many(
        "ir.attachment",
        "license_attachment_rel",
        "license_id",
        "attachment_id",
        string="Documents"
    )

    active = fields.Boolean(default=True)

    @api.depends("expiry_date")
    def _compute_days_to_expiry(self):
        today = date.today()
        for rec in self:
            if rec.expiry_date:
                rec.days_to_expiry = (rec.expiry_date - today).days
            else:
                rec.days_to_expiry = 0

    @api.depends("expiry_date")
    def _compute_renewal_state(self):
        today = date.today()
        warning_date = today + timedelta(days=30)

        for rec in self:
            if not rec.expiry_date:
                rec.renewal_state = "valid"
            elif rec.expiry_date < today:
                rec.renewal_state = "expired"
            elif rec.expiry_date <= warning_date:
                rec.renewal_state = "expiring"
            else:
                rec.renewal_state = "valid"

    # ----------------------------
    # CRON METHOD
    # ----------------------------

    # def _cron_license_expiry_notification(self):
    #     today = date.today()
    #     expiring_licenses = self.search([
    #         ("expiry_date", ">=", today),
    #         ("expiry_date", "<=", today.replace(day=today.day + 30))
    #     ])

    #     for license in expiring_licenses:
    #         license.message_post(
    #             body=f"⚠️ License <b>{license.name}</b> is expiring on <b>{license.expiry_date}</b>."
    #         )
    
