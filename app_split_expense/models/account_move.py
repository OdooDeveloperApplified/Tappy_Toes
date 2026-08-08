from odoo import fields, models, api, _
from odoo.exceptions import UserError
from markupsafe import Markup

import logging
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    is_shared_expense = fields.Boolean(string="Is Shared Expense")
    requested_shared_company_ids = fields.Many2many(
        'shared.company.proxy',
        'account_move_req_proxy_rel',
        'move_id',
        'proxy_id',
        string="Requested Companies"
    )
    shared_company_ids = fields.Many2many(
        'res.company',
        'account_move_shared_company_rel',
        'move_id',
        'company_id',
        string="Approved Companies"
    )
    is_already_split = fields.Boolean(string="Is Already Split", default=False, copy=False)
    split_origin_id = fields.Many2one('account.move', string="Original Split Bill", readonly=True, copy=False, help="Reference to the original bill from which this expense was split.")

    @api.onchange('is_shared_expense', 'company_id')
    def _onchange_is_shared_expense(self):
        if self.is_shared_expense and self.company_id:
            proxy_record = self.env['shared.company.proxy'].browse(self.company_id.id)
            if proxy_record.id not in self.requested_shared_company_ids.ids:
                self.requested_shared_company_ids += proxy_record

    def action_split_expense(self):
        self.ensure_one()
        if not self.is_shared_expense:
            return

        if self.move_type != 'in_invoice':
            raise UserError("You can only split expense on Vendor Bills.")

        if self.state != 'draft':
            raise UserError("You can only split expense on draft bills.")

        requested_ids = set(self.requested_shared_company_ids.ids)
        approved_ids = set(self.shared_company_ids.ids)

        if requested_ids != approved_ids:
            raise UserError("You cannot split the expense! The Approved Companies must exactly match the Requested Companies.")

        total_companies = len(self.shared_company_ids)
        if total_companies <= 1:
            raise UserError("You must select at least one other company in the Approved Companies to split the expense with.")

        if self.company_id.id not in self.shared_company_ids.ids:
            raise UserError("The current company must be included in the Approved Companies list.")

        target_companies = self.shared_company_ids.filtered(lambda c: c.id != self.company_id.id)
        created_bills_info = []

        for company in target_companies:
            journal = self.env['account.journal'].sudo().with_company(company).search([
                ('type', '=', 'purchase'),
                ('company_id', '=', company.id)
            ], limit=1)

            if not journal:
                raise UserError(_("Could not find a Purchase Journal in company %s.") % company.name)

            new_lines_vals = []
            for line in self.invoice_line_ids:
                if line.display_type in ('line_section', 'line_note'):
                    new_lines_vals.append((0, 0, {
                        'display_type': line.display_type,
                        'name': line.name
                    }))
                else:
                    line_vals = {
                        'product_id': line.product_id.id,
                        'name': line.name,
                        'quantity': line.quantity,
                        'price_unit': line.price_unit / total_companies,
                    }

                    if line.account_id:
                        target_account = self.env['account.account'].sudo().with_company(company).search([
                            ('code', '=', line.account_id.code),
                            ('company_ids', 'in', company.id)
                        ], limit=1)
                        if target_account:
                            line_vals['account_id'] = target_account.id

                    if line.tax_ids:
                        target_taxes = self.env['account.tax'].sudo().with_company(company).search([
                            ('name', 'in', line.tax_ids.mapped('name')),
                            ('type_tax_use', '=', 'purchase'),
                            ('company_id', '=', company.id)
                        ])
                        if target_taxes:
                            line_vals['tax_ids'] = [(6, 0, target_taxes.ids)]

                    new_lines_vals.append((0, 0, line_vals))

            try:
                create_vals = {
                    'move_type': self.move_type,
                    'partner_id': self.partner_id.id,
                    'invoice_date': self.invoice_date,
                    'date': self.date,
                    'ref': self.ref,
                    'is_already_split': True,
                    'split_origin_id': self.id,
                    'journal_id': journal.id,
                    'invoice_line_ids': new_lines_vals,
                }
                if hasattr(self, 'file_upload'):
                    create_vals['file_upload'] = self.file_upload

                new_move = self.env['account.move'].sudo().with_company(company).create(create_vals)
                new_move.message_post(body=_("This bill was automatically generated from a split shared expense initiated in %s (Original Bill ID: %s).") % (self.company_id.name, self.id))
                created_bills_info.append(Markup("<li>%s (Bill ID: %s)</li>") % (company.name, new_move.id))
                _logger.info("Successfully created split Vendor Bill (ID: %s) for company: %s", new_move.id, company.name)
            except Exception as e:
                _logger.error("Error creating split Vendor Bill for company %s: %s", company.name, str(e))
                raise UserError(_("Could not create split bill in company %s.\nError: %s") % (company.name, str(e)))

        for line in self.invoice_line_ids:
            if line.display_type not in ('line_section','line_note'):
                line.price_unit = line.price_unit / total_companies

        self.is_already_split = True
        
        if created_bills_info:
            body = Markup(_("This expense was successfully split. The following draft bills were automatically generated:<ul>%s</ul>")) % Markup("").join(created_bills_info)
            self.message_post(body=body)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Success"),
                'message': _("Expense successfully split across %s companies.") % total_companies,
                'type': 'success',
                'sticky': True,
                'next': {'type': 'ir.actions.client', 'tag': 'reload'},
            }
        }