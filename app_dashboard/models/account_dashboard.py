from odoo import models, fields, api, _
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import re
import logging
_logger = logging.getLogger(__name__)

class ProfitLossDashboard(models.Model):
    _name = "account.dashboard"
    _description = "Profit and Loss Dashboard"

    def _shift_date_to_year(self, d, target_year):
        try:
            return d.replace(year=target_year)
        except ValueError:
            # Feb 29 has no equivalent in a non-leap target year
            return d.replace(year=target_year, day=28)

    def _compute_variance(self, current, previous):
        variance = {}
        for key, cur_val in current.items():
            prev_val = (previous or {}).get(key)
            if not previous or prev_val in (None, 0):
                variance[key] = None
            else:
                variance[key] = round((cur_val - prev_val) / abs(prev_val) * 100, 1)
        return variance

    def _get_company_pl_metrics(self, financial_report, company, date_from, date_to):
        report_company = financial_report.with_company(company).with_context(
            company_id=company.id,
            allowed_company_ids=[company.id],
        )

        options = report_company.get_options({})
        options['date'].update({
            'date_from': fields.Date.to_string(date_from),
            'date_to': fields.Date.to_string(date_to),
            'mode': 'range',
            'filter': 'custom',
        })
        options['unfold_all'] = True
        options['all_entries'] = False
        options['comparison'] = {'filter': 'no_comparison'}
        options['companies'] = [{'id': company.id, 'name': company.name}]

        report_company._init_currency_table(options)
        report_lines = report_company.sudo()._get_lines(options)

        def get_balance(line_name):
            line = next((l for l in report_lines if (l.get('name') or '').strip().lower() == line_name.lower()), None)
            if line:
                col = line.get('columns', [{}])[0]
                return col.get('no_format') or col.get('balance') or 0.0
            return 0.0

        revenue = get_balance("Revenue")
        cost_of_revenue = abs(get_balance("Less Costs of Revenue"))
        total_operating_expenses = abs(get_balance("Less Operating Expenses"))

        accounts_69 = self.env['account.account'].with_context(
            allowed_company_ids=[company.id]
        ).sudo().search([('code', '=like', '69%')])

        move_lines = self.env['account.move.line'].sudo().search([
            ('account_id', 'in', accounts_69.ids),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('company_id', '=', company.id),
            ('parent_state', '=', 'posted'),
        ])
        common_expense = sum(line.debit - line.credit for line in move_lines)

        gross_profit = revenue - cost_of_revenue
        operating_expenses_excl_common = total_operating_expenses - abs(common_expense)
        net_profit = gross_profit - operating_expenses_excl_common - abs(common_expense)
        branch_contribution = gross_profit - operating_expenses_excl_common

        return {
            "revenue": round(revenue, 2),
            "cost_of_revenue": round(cost_of_revenue, 2),
            "gross_profit": round(gross_profit, 2),
            "operating_expenses_excl_common": round(operating_expenses_excl_common, 2),
            "common_expense": round(common_expense, 2),
            "net_profit": round(net_profit, 2),
            "branch_contribution": round(branch_contribution, 2),
        }

    def _compute_monthly_trend_data(self, financial_report, company, date_from, date_to):
        current_date = fields.Date.from_string(date_from) if isinstance(date_from, str) else date_from
        end_date = fields.Date.from_string(date_to) if isinstance(date_to, str) else date_to

        if not current_date or not end_date or current_date > end_date:
            return {"labels": [], "datasets": {}}

        cur_month_start = current_date.replace(day=1)

        labels = []
        datasets = {
            "revenue": [],
            "cost_of_revenue": [],
            "gross_profit": [],
            "operating_expenses_excl_common": [],
            "common_expense": [],
            "net_profit": [],
            "branch_contribution": [],
        }

        while cur_month_start <= end_date:
            cur_month_end = (cur_month_start + relativedelta(months=1)) - relativedelta(days=1)
            actual_end = min(cur_month_end, end_date)
            actual_start = max(cur_month_start, current_date)

            labels.append(cur_month_start.strftime("%b %Y"))

            metrics = self._get_company_pl_metrics(financial_report, company, actual_start, actual_end)

            for key in datasets:
                datasets[key].append(metrics[key])

            cur_month_start += relativedelta(months=1)

        return {"labels": labels, "datasets": datasets}

    def _empty_totals(self):
        return {
            "revenue": 0.0,
            "cost_of_revenue": 0.0,
            "gross_profit": 0.0,
            "operating_expenses_excl_common": 0.0,
            "common_expense": 0.0,
            "net_profit": 0.0,
            "branch_contribution": 0.0,
            "currency": "",
            "monthly_trend": {
                "labels": [],
                "datasets": {
                    "revenue": [],
                    "cost_of_revenue": [],
                    "gross_profit": [],
                    "operating_expenses_excl_common": [],
                    "common_expense": [],
                    "net_profit": [],
                    "branch_contribution": [],
                },
            },
        }

    def _accumulate_totals(self, totals, metrics):
        for key in ("revenue", "cost_of_revenue", "gross_profit",
                    "operating_expenses_excl_common", "common_expense",
                    "net_profit", "branch_contribution"):
            totals[key] = round(totals[key] + metrics[key], 2)

    def _accumulate_trend(self, tot_trend, monthly_trend):
        if not tot_trend["labels"] and monthly_trend.get("labels"):
            tot_trend["labels"] = list(monthly_trend["labels"])
            for k in tot_trend["datasets"]:
                tot_trend["datasets"][k] = list(monthly_trend["datasets"].get(k, []))
        elif monthly_trend.get("labels"):
            for k, vals in monthly_trend["datasets"].items():
                if k in tot_trend["datasets"]:
                    for idx, val in enumerate(vals):
                        if idx < len(tot_trend["datasets"][k]):
                            tot_trend["datasets"][k][idx] = round(tot_trend["datasets"][k][idx] + val, 2)
                        else:
                            tot_trend["datasets"][k].append(round(val, 2))

    @api.model
    def get_dashboard_data(self, filter='custom', from_date=None, to_date=None, compare_year=None):
        # We now rely exclusively on the exact dates generated by JS
        try:
            if from_date and to_date:
                date_from = fields.Date.from_string(from_date)
                date_to = fields.Date.from_string(to_date)
            else:
                # Fallback to current year if something breaks
                today = fields.Date.today()
                date_from = today.replace(month=1, day=1)
                date_to = today.replace(month=12, day=31)

            # ---------------------------------------------------------
            # Load P&L report
            # ---------------------------------------------------------
            financial_report = self.env.ref("account_reports.profit_and_loss", raise_if_not_found=False)
            if not financial_report:
                raise ValueError("Profit and Loss report definition not found (account_reports.profit_and_loss).")

            compare_date_from = compare_date_to = None
            if compare_year:
                compare_year = int(compare_year)
                compare_date_from = self._shift_date_to_year(date_from, compare_year)
                compare_date_to = self._shift_date_to_year(date_to, compare_year)

            companies = self.env.companies
            all_company_data = []

            for company in companies:
                metrics = self._get_company_pl_metrics(financial_report, company, date_from, date_to)
                monthly_trend = self._compute_monthly_trend_data(financial_report, company, date_from, date_to)

                company_data = {
                    "company_name": company.name,
                    "currency": company.currency_id.symbol or "",
                    "revenue": metrics["revenue"],
                    "cost_of_revenue": metrics["cost_of_revenue"],
                    "gross_profit": metrics["gross_profit"],
                    "operating_expenses": metrics["operating_expenses_excl_common"],
                    "expense_69": metrics["common_expense"],
                    "net_profit": metrics["net_profit"],
                    "branch_contribution": metrics["branch_contribution"],
                    "monthly_trend": monthly_trend,
                }

                if compare_year:
                    compare_metrics = self._get_company_pl_metrics(financial_report, company, compare_date_from, compare_date_to)
                    compare_trend = self._compute_monthly_trend_data(financial_report, company, compare_date_from, compare_date_to)
                    compare_display = {
                        "revenue": compare_metrics["revenue"],
                        "cost_of_revenue": compare_metrics["cost_of_revenue"],
                        "gross_profit": compare_metrics["gross_profit"],
                        "operating_expenses": compare_metrics["operating_expenses_excl_common"],
                        "expense_69": compare_metrics["common_expense"],
                        "net_profit": compare_metrics["net_profit"],
                        "branch_contribution": compare_metrics["branch_contribution"],
                    }
                    current_display = {k: v for k, v in company_data.items() if k in compare_display}
                    company_data["compare_year"] = compare_year
                    company_data["compare"] = compare_display
                    company_data["variance"] = self._compute_variance(current_display, compare_display)
                    company_data["compare_monthly_trend"] = compare_trend

                all_company_data.append(company_data)

            return {"companies_data": all_company_data}

        except Exception as e:
            _logger.exception("Error in get_dashboard_data: %s", e)
            raise

    @api.model
    def get_consolidated_dashboard_data(self, filter='year', from_date=None, to_date=None, compare_year=None):
        # Trust the dates coming from JavaScript! Do NOT use 'today' for filters.
        if from_date and to_date:
            date_from = fields.Date.from_string(from_date)
            date_to = fields.Date.from_string(to_date)
        else:
            # Fallback only
            today = fields.Date.today()
            date_from = today.replace(month=1, day=1)
            date_to = today

        financial_report = self.env.ref("account_reports.profit_and_loss", raise_if_not_found=False)
        if not financial_report:
            raise ValueError("Profit and Loss report not found.")

        compare_date_from = compare_date_to = None
        if compare_year:
            compare_year = int(compare_year)
            compare_date_from = self._shift_date_to_year(date_from, compare_year)
            compare_date_to = self._shift_date_to_year(date_to, compare_year)

        all_companies = self.env['res.company'].sudo().search([])

        total_data = self._empty_totals()
        compare_total_data = self._empty_totals() if compare_year else None

        company_data = []

        for company in all_companies:
            metrics = self._get_company_pl_metrics(financial_report, company, date_from, date_to)
            monthly_trend = self._compute_monthly_trend_data(financial_report, company, date_from, date_to)

            self._accumulate_totals(total_data, metrics)
            self._accumulate_trend(total_data["monthly_trend"], monthly_trend)

            entry = {
                'company_name': company.name,
                'currency': company.currency_id.symbol or "",
                'revenue': metrics['revenue'],
                'cost_of_revenue': metrics['cost_of_revenue'],
                'gross_profit': metrics['gross_profit'],
                'operating_expenses_excl_common': metrics['operating_expenses_excl_common'],
                'common_expense': metrics['common_expense'],
                'net_profit': metrics['net_profit'],
                'branch_contribution': metrics['branch_contribution'],
                'monthly_trend': monthly_trend,
            }

            if compare_year:
                compare_metrics = self._get_company_pl_metrics(financial_report, company, compare_date_from, compare_date_to)
                compare_trend = self._compute_monthly_trend_data(financial_report, company, compare_date_from, compare_date_to)

                self._accumulate_totals(compare_total_data, compare_metrics)
                self._accumulate_trend(compare_total_data["monthly_trend"], compare_trend)

                entry["compare"] = compare_metrics
                entry["variance"] = self._compute_variance(metrics, compare_metrics)
                entry["compare_monthly_trend"] = compare_trend

            company_data.append(entry)

        if all_companies:
            total_data["currency"] = all_companies[0].currency_id.symbol or ""

        result = {
            "total_data": total_data,
            "company_data": company_data,
        }

        if compare_year:
            compare_total_data["currency"] = total_data["currency"]
            total_data["compare"] = compare_total_data
            total_data["variance"] = self._compute_variance(
                {k: total_data[k] for k in compare_total_data if k not in ("currency", "monthly_trend")},
                {k: compare_total_data[k] for k in compare_total_data if k not in ("currency", "monthly_trend")},
            )
            total_data["compare_monthly_trend"] = compare_total_data["monthly_trend"]
            result["compare_year"] = compare_year

        return result
