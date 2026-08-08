from odoo import models, fields, tools

class SharedCompanyProxy(models.Model):
    _name = 'shared.company.proxy'
    _description = 'Shared Company Proxy for Selection'
    _auto = False
    _order = 'name'

    name = fields.Char('Company Name', readonly=True)
    company_id = fields.Many2one('res.company', string='Original Company', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (
                SELECT id, name, id AS company_id
                FROM res_company
            )
        ''' % self._table)
