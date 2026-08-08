/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { DateTimeInput } from "@web/core/datetime/datetime_input";

const { Component, onWillStart, onMounted, useState } = owl;

export class ProfitLossConsolidatedDashboard extends Component {
    static template = "ProfitLossConsolidatedDashboard";
    static components = { DateTimeInput };

    setup() {
        this.orm = useService("orm");

        const savedFilter = localStorage.getItem("pl_consolidated_filter") || "year";
        const savedCompareYear = localStorage.getItem("pl_consolidated_compare_year");
        this.state = useState({
            totalData: {},
            companyData: [],
            currentFilter: savedFilter,
            referenceDate: luxon.DateTime.local(),
            customFromDate: null,
            customToDate: null,
            chartTypeCompany: "bar",
            chartTypeTrend: "line",
            isLoading: true,
            compareYear: savedCompareYear ? parseInt(savedCompareYear, 10) : null,
            showCompareDropdown: false,
            trendCompareMetric: "revenue",
        });

        onWillStart(async () => {
            await this.loadDashboardData();
        });

        onMounted(() => {
            this.renderCharts();
        });
    }

    get displayDateText() {
        const ref = this.state.referenceDate;
        if (this.state.currentFilter === 'month') {
            return ref.toFormat("MMMM yyyy"); // e.g., April 2026
        } else if (this.state.currentFilter === 'quarter') {
            // Nava format mate: start month ane end month get karo
            const startMonth = ref.startOf('quarter').toFormat("MMM");
            const endMonth = ref.endOf('quarter').toFormat("MMM yyyy");
            return `${startMonth} - ${endMonth}`; // e.g., Apr - Jun 2026
        } else if (this.state.currentFilter === 'year') {
            return ref.toFormat("yyyy"); // e.g., 2026
        }
        return "";
    }

    getDateRange() {
        const ref = this.state.referenceDate;
        let fromDate, toDate;

        if (this.state.currentFilter === 'month') {
            fromDate = ref.startOf('month').toISODate();
            toDate = ref.endOf('month').toISODate();
        } else if (this.state.currentFilter === 'quarter') {
            fromDate = ref.startOf('quarter').toISODate();
            toDate = ref.endOf('quarter').toISODate();
        } else if (this.state.currentFilter === 'year') {
            fromDate = ref.startOf('year').toISODate();
            toDate = ref.endOf('year').toISODate();
        } else if (this.state.currentFilter === 'custom') {
            fromDate = this.state.customFromDate ? this.state.customFromDate.toISODate() : null;
            toDate = this.state.customToDate ? this.state.customToDate.toISODate() : null;
        }

        return { fromDate, toDate };
    }

    async loadDashboardData() {
        const { fromDate, toDate } = this.getDateRange();

        if (this.state.currentFilter === 'custom' && (!fromDate || !toDate)) {
            return; // Wait until both custom dates are selected
        }

        this.state.isLoading = true;

        const data = await this.orm.silent.call("account.dashboard", "get_consolidated_dashboard_data", [], {
            filter: this.state.currentFilter,
            from_date: fromDate,
            to_date: toDate,
            compare_year: this.state.compareYear || false,
        });

        this.state.totalData = data.total_data || {};
        this.state.companyData = data.company_data || [];
        localStorage.setItem("pl_consolidated_filter", this.state.currentFilter);

        this.state.isLoading = false;

        this.refreshCharts();
    }

    setFilter(filter) {
        this.state.currentFilter = filter;
        this.state.referenceDate = luxon.DateTime.local(); // Reset date on filter change
        if (filter !== 'custom') {
            this.loadDashboardData();
        }
    }

    navigatePeriod(step) {
        if (this.state.currentFilter === 'month') {
            this.state.referenceDate = this.state.referenceDate.plus({ months: step });
        } else if (this.state.currentFilter === 'quarter') {
            this.state.referenceDate = this.state.referenceDate.plus({ quarters: step });
        } else if (this.state.currentFilter === 'year') {
            this.state.referenceDate = this.state.referenceDate.plus({ years: step });
        }
        this.loadDashboardData();
    }

    onCustomDateChange(field, date) {
        this.state[field] = date;
        if (this.state.customFromDate && this.state.customToDate) {
            this.loadDashboardData();
        }
    }

    // --- Year-over-year comparison ---
    get availableCompareYears() {
        const currentYear = this.state.referenceDate.year;
        const years = [];
        for (let i = 1; i <= 6; i++) {
            years.push(currentYear - i);
        }
        return years;
    }

    get compareLabel() {
        if (!this.state.compareYear) return "";
        const ref = this.state.referenceDate;
        const y = this.state.compareYear;
        if (this.state.currentFilter === 'month') {
            return ref.set({ year: y }).toFormat("MMM yyyy");
        } else if (this.state.currentFilter === 'quarter') {
            const start = ref.startOf('quarter').set({ year: y }).toFormat("MMM");
            const end = ref.endOf('quarter').set({ year: y }).toFormat("MMM yyyy");
            return `${start} - ${end}`;
        }
        return `${y}`;
    }

    toggleCompareDropdown() {
        this.state.showCompareDropdown = !this.state.showCompareDropdown;
    }

    setCompareYear(year) {
        this.state.compareYear = year;
        this.state.showCompareDropdown = false;
        localStorage.setItem("pl_consolidated_compare_year", year);
        this.loadDashboardData();
    }

    onCustomYearInput(ev) {
        const year = parseInt(ev.target.value, 10);
        if (year) {
            this.setCompareYear(year);
        }
    }

    clearCompareYear() {
        this.state.compareYear = null;
        this.state.showCompareDropdown = false;
        localStorage.removeItem("pl_consolidated_compare_year");
        this.loadDashboardData();
    }

    setTrendCompareMetric(key) {
        this.state.trendCompareMetric = key;
        this.renderTrendChart();
    }

    changeMainChartType(type) {
        this.state.chartTypeMain = type;
        this.refreshCharts();
    }

    changeCompanyChartType(type) {
        this.state.chartTypeCompany = type;
        this.refreshCharts();
    }

    refreshCharts() {
        const main = document.getElementById("pl_consolidated_chart");
        const trend = document.getElementById("pl_trend_chart");
        const comp = document.getElementById("pl_company_comparison_chart");
        if (main?.chartInstance) { main.chartInstance.destroy(); main.chartInstance = null; }
        if (trend?.chartInstance) { trend.chartInstance.destroy(); trend.chartInstance = null; }
        if (comp?.chartInstance) { comp.chartInstance.destroy(); comp.chartInstance = null; }
        setTimeout(() => this.renderCharts(), 200);
    }

    formatValue(value, currency = "") {
        const num = Number(value) || 0;
        return `${num.toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        })} ${currency}`;
    }

    formatNumberOnly(value) {
        const num = Number(value) || 0;
        return num.toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    }

    get tableRows() {
        const total = this.state.totalData || {};
        const companies = this.state.companyData || [];
        const currency = total.currency || "";
        
        const metrics = [
            { name: "Revenue", key: "revenue", icon: "bi-cash-stack", color: "color: #2563eb;", isBold: false },
            { name: "Cost of Revenue", key: "cost_of_revenue", icon: "bi-arrow-down-circle", color: "color: #d97706;", isBold: false },
            { name: "Gross Profit", key: "gross_profit", icon: "bi-graph-up", color: "color: #059669;", isBold: true, highlight: true },
            { name: "Operating Expenses", key: "operating_expenses_excl_common", icon: "bi-bar-chart-line", color: "color: #7c3aed;", isBold: false },
            { name: "Common Expenses", key: "common_expense", icon: "bi-receipt", color: "color: #dc2626;", isBold: false },
            { name: "Branch Contribution", key: "branch_contribution", icon: "bi-building", color: "color: #06b6d4;", isBold: true, highlight: true },
            { name: "Net Profit", key: "net_profit", icon: "bi-bank", color: "color: #475569;", isBold: true, highlight: true },
        ];

        const compareYear = this.state.compareYear;

        return metrics.map((m) => ({
            name: m.name,
            icon: m.icon,
            color: m.color,
            isBold: m.isBold,
            highlight: m.highlight,
            companyValues: companies.map((c) => {
                const val = Number(c[m.key]) || 0;
                const changePct = compareYear && c.variance ? c.variance[m.key] : null;
                return {
                    name: c.company_name,
                    value: this.formatNumberOnly(c[m.key]),
                    isNegative: val < 0,
                    compareValue: compareYear && c.compare ? this.formatNumberOnly(c.compare[m.key]) : null,
                    changePct: changePct === undefined ? null : changePct,
                };
            }),
            totalValue: this.formatValue(total[m.key], currency),
            isTotalNegative: (Number(total[m.key]) || 0) < 0,
            totalCompareValue: compareYear && total.compare ? this.formatNumberOnly(total.compare[m.key]) : null,
            totalChangePct: compareYear && total.variance ? total.variance[m.key] : null,
        }));
    }

    get cards() {
        const d = this.state.totalData || {};
        const currency = d.currency || "";
        return [
            { title: "Revenue", value: this.formatValue(d.revenue, currency), icon: "bi-cash-stack", bg: "crm-bg-primary" },
            { title: "Cost of Revenue", value: this.formatValue(d.cost_of_revenue, currency), icon: "bi-arrow-down-circle", bg: "crm-bg-warning" },
            { title: "Gross Profit", value: this.formatValue(d.gross_profit, currency), icon: "bi-graph-up", bg: "crm-bg-success" },
            { title: "Operating Expenses", value: this.formatValue(d.operating_expenses_excl_common, currency), icon: "bi-bar-chart-line", bg: "crm-bg-secondary" },
            { title: "Common Expenses", value: this.formatValue(d.common_expense, currency), icon: "bi-receipt", bg: "crm-bg-danger" },
            { title: "Branch Contribution", value: this.formatValue(d.branch_contribution, currency), icon: "bi-building", bg: "crm-bg-info" },
            { title: "Net Profit", value: this.formatValue(d.net_profit, currency), icon: "bi-bank", bg: "crm-bg-dark" },
        ];
    }

    // Metrics available for the Month-Wise Account Trend chart.
    // Keys match the "monthly_trend.datasets" keys returned by the backend,
    // and mirror the same 7 metrics shown in the KPI cards above.
    get accountFilterList() {
        return [
            { key: "revenue", label: "Revenue", color: "#2563eb", icon: "bi-cash-stack" },
            { key: "cost_of_revenue", label: "Cost of Revenue", color: "#d97706", icon: "bi-arrow-down-circle" },
            { key: "gross_profit", label: "Gross Profit", color: "#059669", icon: "bi-graph-up" },
            { key: "operating_expenses_excl_common", label: "Operating Expenses", color: "#7c3aed", icon: "bi-bar-chart-line" },
            { key: "common_expense", label: "Common Expenses", color: "#dc2626", icon: "bi-receipt" },
            { key: "branch_contribution", label: "Branch Contribution", color: "#06b6d4", icon: "bi-building" },
            { key: "net_profit", label: "Net Profit", color: "#475569", icon: "bi-bank" },
        ];
    }

    changeTrendChartType(type) {
        this.state.chartTypeTrend = type;
        this.renderTrendChart();
    }

    renderTrendChart() {
        const trend = this.state.totalData?.monthly_trend;
        const type = this.state.chartTypeTrend || "line";
        const ctx = document.getElementById("pl_trend_chart");
        if (!ctx) return;

        if (ctx.chartInstance) ctx.chartInstance.destroy();
        if (!trend || !trend.labels || !trend.labels.length) return;

        const actualType = type === "area" ? "line" : type;
        const compareYear = this.state.compareYear;

        let datasets;
        let labels = trend.labels;
        let titleText = `Month-Wise Account Trend (${this.state.totalData.currency || ""})`;

        if (compareYear) {
            const metricKey = this.state.trendCompareMetric || "revenue";
            const metric = this.accountFilterList.find((item) => item.key === metricKey) || this.accountFilterList[0];
            const compareTrend = this.state.totalData?.compare_monthly_trend;

            labels = trend.labels.map((l) => l.split(" ")[0]);

            datasets = [
                {
                    label: `${metric.label} (${this.state.referenceDate.year})`,
                    data: trend.datasets[metric.key] || [],
                    borderColor: metric.color,
                    backgroundColor: type === "area" ? metric.color + "33" : metric.color,
                    borderWidth: 2,
                    fill: type === "area",
                    tension: 0.3,
                },
                {
                    label: `${metric.label} (${compareYear})`,
                    data: (compareTrend && compareTrend.datasets[metric.key]) || [],
                    borderColor: metric.color,
                    backgroundColor: "transparent",
                    borderDash: [6, 4],
                    borderWidth: 2,
                    fill: false,
                    tension: 0.3,
                },
            ];
            titleText = `${metric.label} Trend: ${this.state.referenceDate.year} vs ${compareYear}`;
        } else {
            datasets = this.accountFilterList.map((item) => ({
                label: item.label,
                data: trend.datasets[item.key] || [],
                borderColor: item.color,
                backgroundColor: type === "area" ? item.color + "33" : item.color,
                borderWidth: 2,
                fill: type === "area",
                tension: 0.3,
            }));
        }

        ctx.chartInstance = new Chart(ctx, {
            type: actualType,
            data: { labels, datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: { display: true, text: titleText },
                    legend: { display: true, position: "bottom" },
                },
                scales: {
                    y: { beginAtZero: true, grid: { color: "rgba(128,128,128,0.15)" } },
                    x: { grid: { color: "rgba(128,128,128,0.1)" } },
                },
            },
        });
    }

    renderCharts() {
        this.renderMainChart();
        this.renderTrendChart();
        this.renderCompanyComparisonChart();
    }

    renderMainChart() {
        const d = this.state.totalData;
        const type = this.state.chartTypeMain || "bar";
        const ctx = document.getElementById("pl_consolidated_chart");
        if (!ctx || !d || d.revenue === undefined) return;

        if (ctx.chartInstance) ctx.chartInstance.destroy();

        const labels = ["Revenue", "Cost of Revenue", "Gross Profit", "Operating Expenses", "Common Expenses", "Branch Contribution", "Net Profit"];
        const values = [d.revenue, d.cost_of_revenue, d.gross_profit, d.operating_expenses_excl_common, d.common_expense, d.branch_contribution, d.net_profit];
        const colors = ["#2563eb", "#d97706", "#059669", "#7c3aed", "#dc2626", "#06b6d4", "#475569"];

        ctx.chartInstance = new Chart(ctx, {
            type: type === "horizontalBar" ? "bar" : type,
            data: {
                labels,
                datasets: [{
                    label: `Consolidated (${d.currency})`,
                    data: values,
                    backgroundColor: colors,
                    borderColor: "#fff",
                    borderWidth: 2,
                    fill: type === "line",
                    tension: 0.4,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: type === "horizontalBar" ? "y" : "x",
                plugins: {
                    title: { display: true, text: "Consolidated Profit & Loss Overview" },
                    legend: { display: type === "pie" },
                },
                scales: type === "pie" ? {} : {
                    y: { beginAtZero: true, grid: { color: "#eee" } },
                    x: { grid: { color: "#fafafa" } },
                },
            },
        });
    }

    renderCompanyComparisonChart() {
        const companies = this.state.companyData;
        if (!companies.length) return;

        const type = this.state.chartTypeCompany || "bar";
        const ctx = document.getElementById("pl_company_comparison_chart");
        if (!ctx) return;

        if (ctx.chartInstance) ctx.chartInstance.destroy();

        const labels = companies.map((c) => c.company_name);

        let datasets;

        if (type === "pie") {
            datasets = [{
                label: "Net Profit",
                data: companies.map((c) => c.net_profit),
                backgroundColor: ["#2563eb", "#059669", "#d97706", "#dc2626", "#7c3aed", "#06b6d4", "#475569"],
                borderColor: "#fff",
                borderWidth: 2,
            }];
        } else {
            datasets = [
                { label: "Revenue", data: companies.map((c) => c.revenue), backgroundColor: "#2563eb" },
                { label: "Gross Profit", data: companies.map((c) => c.gross_profit), backgroundColor: "#059669" },
                { label: "Common Expense", data: companies.map((c) => c.common_expense), backgroundColor: "#dc2626" },
                { label: "Branch Contribution", data: companies.map((c) => c.branch_contribution), backgroundColor: "#06b6d4" },
                { label: "Net Profit", data: companies.map((c) => c.net_profit), backgroundColor: "#475569" },
            ];
        }

        ctx.chartInstance = new Chart(ctx, {
            type: type === "horizontalBar" ? "bar" : type,
            data: { labels, datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: type === "horizontalBar" ? "y" : "x",
                plugins: {
                    title: { display: true, text: "Company-wise Profit & Loss Comparison" },
                    legend: { display: true, position: "top" },
                },
                scales: type === "pie" ? {} : {
                    y: { beginAtZero: true, grid: { color: "#eee" } },
                    x: { grid: { color: "#fafafa" } },
                },
            },
        });
    }
}

registry.category("actions").add("profit_loss_consolidated_dashboard", ProfitLossConsolidatedDashboard);