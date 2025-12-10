from odoo import fields, models, api, _
from datetime import date

class HrContractTemplate(models.Model):
    _inherit = "hr.contract"
    _description = "HR Contract Template"

    telecommunication_allowance = fields.Monetary(string="Telecommunication Allowance", currency_field='currency_id')
    
    state = fields.Selection(
        selection_add=[('expiring', 'Expiring Soon')],

    )

    def _check_and_update_expiring_state(self):
        """
        Custom helper to update state to Expiring Soon
        if contract end date is within threshold.
        """
        today = date.today()
        threshold_days = 30

        for contract in self:
            if contract.date_end and contract.state not in ['close', 'cancel']:
                days_left = (contract.date_end - today).days
                if 0 < days_left <= threshold_days:
                    contract.state = 'expiring'
                elif days_left > threshold_days and contract.state == 'expiring':
                    # revert to running if end date was extended
                    contract.state = 'open'

    @api.onchange('date_end')
    def _onchange_date_end(self):
        self._check_and_update_expiring_state()

    def write(self, vals):
        res = super().write(vals)
        if 'date_end' in vals:
            self._check_and_update_expiring_state()
        return res