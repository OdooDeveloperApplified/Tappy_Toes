from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class ContactTemplate(models.Model):
    _inherit = "res.partner"
    _description = "Contact Template"

    # Child and Family data related fields
    child_name = fields.Char(string="Child Name")
    child_birthday = fields.Date(string="Child date of Birth")
    child_age_band = fields.Selection([
        ('under_18m', 'Under 18m'), 
        ('18m_2y', '18m-2y'),
        ('2y_3y', '2y-3y'), 
        ('3y_4y', '3y-4y'), 
        ('4y_5y', '4y-5y'), 
        ('5y_6y', '5y-6y'), 
        ('over_6y', 'Over 6y'),
        ('unknown', 'Unknown')
    ], string="Child Age Band")
    number_of_children = fields.Integer(string="Number of Children", default=1)
    sibling_notes = fields.Text(string="Sibling Notes")
    exisiting_student = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string="Existing Student")
    exisiting_family = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string="Existing Family")

    # Contact Preferences related fields
    preferred_contact_method = fields.Selection([
        ('call', 'Call'),
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
        ('unknown', 'Unknown')
    ], string="Preferred Contact Method")
    preferred_language = fields.Selection([
        ('english', 'English'),
        ('arabic', 'Arabic'),
        ('hindi', 'Hindi'),
        ('other', 'Other'),
        ('unknown', 'Unknown')
    ], string="Preferred Language")
    whatsapp_number = fields.Char(string="WhatsApp Number")
    preferred_branch = fields.Selection([
        ('karama', 'Karama'),
        ('sharjah', 'Sharjah'),
        ('dubai_south', 'Dubai South'),
        ('fujairah', 'Fujairah'),
        ('online', 'Online'),
        ('unknown', 'Unknown')
    ], string="Preferred Branch")
    do_not_contact = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string="Do Not Contact", default='no')

    # Legacy import fields
    original_ac_contact_id = fields.Char(string="Original Account Contact ID")
    legacy_source = fields.Char(string="Legacy Source")
    legacy_tags_raw = fields.Text(string="Legacy Tags Raw")
    consent_to_contact = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
        ('unknown', 'Unknown')
    ], string="Consent to Contact", default='unknown')

    ########## Code to auto assign location tags to related leads based on preferred_branch:starts ##########
    def _apply_location_tag_to_leads(self):
        for partner in self:
            if not partner.preferred_branch:
                continue

            # Convert selection value → label
            branch_label = dict(self._fields['preferred_branch'].selection).get(partner.preferred_branch)

            if not branch_label:
                continue

            tag_name = f"Location: {branch_label}"

            # Find or create tag
            tag = self.env['crm.tag'].search([('name', '=', tag_name)], limit=1)
            if not tag:
                tag = self.env['crm.tag'].create({'name': tag_name})

            # Find related leads
            leads = self.env['crm.lead'].search([('partner_id', '=', partner.id)])

            # Apply tag (avoid duplicates automatically handled by m2m)
            for lead in leads:
                lead.tag_ids = [(6, 0, [tag.id])]

    # Trigger on create
    @api.model
    def create(self, vals):
        partner = super().create(vals)
        partner._apply_location_tag_to_leads()
        return partner

    # Trigger on update
    def write(self, vals):
        res = super().write(vals)

        if 'preferred_branch' in vals:
            self._apply_location_tag_to_leads()

        return res