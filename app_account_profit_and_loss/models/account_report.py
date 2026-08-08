from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)

class AccountReport(models.Model):
    _inherit = 'account.report'
    
    filter_pl_account = fields.Boolean(
        string="Income / Expense Accounts",
        compute=lambda self: self._compute_report_option_filter('filter_pl_account'),
        readonly=False, store=True,
        depends=['root_report_id', 'section_main_report_ids'],
    )

    def _init_options_income_expense_account(self, options, previous_options=None):
        _logger.info("this is income account called options %s",options)
        if not self.filter_pl_account:
            return
        _logger.info("pl_account is %s", self.filter_pl_account)
        options['pl_account'] = True
        options['income_account_id'] = previous_options.get('income_account_id', []) if previous_options else []
        options['expense_account_id'] = previous_options.get('expense_account_id', []) if previous_options else []
    
    # def _get_options_domain(self, options, date_scope):
    #     domain = super()._get_options_domain(options, date_scope)
    #     # Apply custom income/expense filter
    #     if options.get('pl_account'):
    #         _logger.info("this is income %s",  options.get('income_account_id', []))
    #         _logger.info("this is expense %s",  options.get('expense_account_id', []))
    #         income_ids = options.get('income_account_id', [])
    #         expense_ids = options.get('expense_account_id', [])
    #         if income_ids or expense_ids:
    #             domain += [('account_id', '=', income_ids + expense_ids)]

    #     return domain

    def _get_options_domain(self, options, date_scope):
        domain = super()._get_options_domain(options, date_scope)

        # Only apply the filter if user has actually selected any account
        income_ids = options.get('income_account_id') or []
        expense_ids = options.get('expense_account_id') or []

        # Normalize to list of ints
        if isinstance(income_ids, int):
            income_ids = [income_ids]
        elif not isinstance(income_ids, list):
            income_ids = list(income_ids or [])

        if isinstance(expense_ids, int):
            expense_ids = [expense_ids]
        elif not isinstance(expense_ids, list):
            expense_ids = list(expense_ids or [])

        if income_ids or expense_ids:
            ids = income_ids + expense_ids
            _logger.info("this is ids %s", ids)

            # ✅ Only add filter if there are any selected IDs
            if ids:
                domain += [('account_id', 'in', ids)]

        return domain
