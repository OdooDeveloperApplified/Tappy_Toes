/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { DateTimeInput } from "@web/core/datetime/datetime_input";

const { Component, onWillStart, onMounted, useState } = owl;
const { DateTime } = luxon; // Luxon import karyu chhe

export class ProfitLossDashboard extends Component {
    static components = { DateTimeInput };
    static template = "ProfitLossDashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        const savedFilter = localStorage.getItem("pl_dashboard_filter") || "year";
        const savedCompareYear = localStorage.getItem("pl_dashboard_compare_year");
        this.state = useState({
            dashboardData: { companies_data: [] },
            currentFilter: savedFilter,
            referenceDate: DateTime.local(), // Native Date ni jagya ae Luxon Date
            fromDate: null,
            toDate: null,
            customFromDate: null,
            customToDate: null,
            chartTypes: {},
            trendChartTypes: {},
            isLoading: true,
            compareYear: savedCompareYear ? parseInt(savedCompareYear, 10) : null,
            showCompareDropdown: false,
            trendCompareMetric: "revenue",
        });

        onWillStart(async () => {
            await this.calculateDatesAndLoad();
        });

        onMounted(() => {
            this.renderCharts();
            this.renderTrendCharts();
        });
    }

    getSafeId(name) {
        if (!name) return "";
        return "pl_chart_" + name.replace(/\s+/g, "_").replace(/[^a-zA-Z0-9_]/g, "");
    }

    getTrendSafeId(name) {
        if (!name) return "";
        return "pl_trend_chart_" + name.replace(/\s+/g, "_").replace(/[^a-zA-Z0-9_]/g, "");
    }

    // --- Date Calculation Logic (Luxon Base) ---
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

    get displayDateText() {
        if (this.state.currentFilter === 'custom') {
            const from = this.state.customFromDate ? this.state.customFromDate.toISODate() : '';
            const to = this.state.customToDate ? this.state.customToDate.toISODate() : '';
            return from && to ? `${from} to ${to}` : "Select Dates";
        }
        
        const ref = this.state.referenceDate;
        if (!ref) return "Select Period";

        if (this.state.currentFilter === 'year') {
            return ref.toFormat("yyyy"); // e.g., 2026
        } else if (this.state.currentFilter === 'month') {
            return ref.toFormat("MMMM yyyy"); // e.g., April 2026
        } else if (this.state.currentFilter === 'quarter') {
            const startMonth = ref.startOf('quarter').toFormat("MMM");
            const endMonth = ref.endOf('quarter').toFormat("MMM yyyy");
            return `${startMonth} - ${endMonth}`; // e.g., Apr - Jun 2026
        }
        return "Select Period";
    }

    // --- Data Loading & Interactions ---
    async calculateDatesAndLoad() {
        const { fromDate, toDate } = this.getDateRange();

        if (this.state.currentFilter === 'custom' && (!fromDate || !toDate)) {
            return; // Wait until both custom dates are selected
        }

        this.state.fromDate = fromDate;
        this.state.toDate = toDate;
        localStorage.setItem("pl_dashboard_filter", this.state.currentFilter);

        await this.loadDashboardData(this.state.currentFilter, fromDate, toDate);
    }

    async loadDashboardData(filter, fromDate, toDate) {
        this.state.isLoading = true;
        // Python ne dates proper male te mate dictionary (kwargs) tarike pass karyu chhe
        const data = await this.orm.silent.call("account.dashboard", "get_dashboard_data", [], {
            filter: filter,
            from_date: fromDate,
            to_date: toDate,
            compare_year: this.state.compareYear || false,
        });
        this.state.dashboardData = data || { companies_data: [] };
        this.state.isLoading = false;
        setTimeout(() => {
            this.renderCharts();
            this.renderTrendCharts();
        }, 200);
    }

    setFilter(filter) {
        this.state.currentFilter = filter;
        this.state.referenceDate = DateTime.local(); // Reset to today on filter change
        if (filter !== 'custom') {
            this.calculateDatesAndLoad();
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
        this.calculateDatesAndLoad();
    }

    onCustomDateChange(field, luxonDate) {
        this.state[field] = luxonDate;
        this.state.currentFilter = "custom";

        // Auto-apply the filter as soon as both dates are selected
        if (this.state.customFromDate && this.state.customToDate) {
            this.calculateDatesAndLoad();
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
        localStorage.setItem("pl_dashboard_compare_year", year);
        this.calculateDatesAndLoad();
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
        localStorage.removeItem("pl_dashboard_compare_year");
        this.calculateDatesAndLoad();
    }

    setTrendCompareMetric(key) {
        this.state.trendCompareMetric = key;
        this.renderTrendCharts();
    }

    // --- Rendering Helpers ---
    changeChartType(companyName, type) {
        this.state.chartTypes[companyName] = type;
        this.renderCharts();
    }

    formatValue(value, currency = "") {
        const num = Number(value) || 0;
        return `${num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${currency}`;
    }

    getCompanyCards(company) {
        const currency = company.currency || "";
        const hasCompare = !!(this.state.compareYear && company.compare);

        const makeCard = (title, key, icon, bg) => {
            const card = { title, value: this.formatValue(company[key], currency), icon, bg };
            if (hasCompare) {
                card.compareValue = this.formatValue(company.compare[key], currency);
                const pct = company.variance ? company.variance[key] : null;
                card.changePct = pct === undefined ? null : pct;
            }
            return card;
        };

        return [
            makeCard("Revenue", "revenue", "bi-cash-stack", "crm-bg-primary"),
            makeCard("Cost of Revenue", "cost_of_revenue", "bi-arrow-down-circle", "crm-bg-warning"),
            makeCard("Gross Profit", "gross_profit", "bi-graph-up", "crm-bg-success"),
            makeCard("Operating Expenses", "operating_expenses", "bi-bar-chart-line", "crm-bg-secondary"),
            makeCard("Common Expenses", "expense_69", "bi-receipt", "crm-bg-danger"),
            makeCard("Branch Contribution", "branch_contribution", "bi-building", "crm-bg-info"),
            makeCard("Net Profit", "net_profit", "bi-bank", "crm-bg-dark"),
        ];
    }

    get companySections() {
        const companies = this.state.dashboardData?.companies_data || [];
        return companies.map((company) => ({
            name: company.company_name,
            cards: this.getCompanyCards(company),
            currency: company.currency,
            monthly_trend: company.monthly_trend,
            compare_monthly_trend: company.compare_monthly_trend,
        }));
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

    changeTrendChartType(companyName, type) {
        this.state.trendChartTypes[companyName] = type;
        this.renderTrendCharts();
    }

    renderTrendCharts() {
        this.companySections.forEach((company) => {
            const type = this.state.trendChartTypes[company.name] || "line";
            const ctx = document.getElementById(this.getTrendSafeId(company.name));
            if (!ctx) return;

            if (ctx.chartInstance) ctx.chartInstance.destroy();

            const trend = company.monthly_trend;
            if (!trend || !trend.labels || !trend.labels.length) return;

            const actualType = type === "area" ? "line" : type;
            const compareYear = this.state.compareYear;

            let datasets;
            let labels = trend.labels;
            let titleText = `Month-Wise Account Trend - ${company.name}`;

            if (compareYear) {
                const metricKey = this.state.trendCompareMetric || "revenue";
                const metric = this.accountFilterList.find((item) => item.key === metricKey) || this.accountFilterList[0];
                const compareTrend = company.compare_monthly_trend;

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
                titleText = `${metric.label} Trend - ${company.name}: ${this.state.referenceDate.year} vs ${compareYear}`;
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
        });
    }

    renderCharts() {
        this.companySections.forEach((company) => {
            const type = this.state.chartTypes[company.name] || "bar";
            const ctx = document.getElementById(this.getSafeId(company.name));
            if (!ctx) return;

            const chartCards = company.cards;
            const labels = chartCards.map((c) => c.title);
            const values = chartCards.map((c) => {
                const rawValue = c.value || "0";
                const cleanNumber = parseFloat(rawValue.replace(/[^0-9.-]+/g, ""));
                return isNaN(cleanNumber) ? 0 : cleanNumber;
            });

            if (ctx.chartInstance) ctx.chartInstance.destroy();

            const config = {
                type: type === "horizontalBar" ? "bar" : type,
                data: {
                    labels,
                    datasets: [{
                        label: `${company.name} (${company.currency})`,
                        data: values,
                        backgroundColor: ["#2563eb", "#d97706", "#059669", "#7c3aed", "#dc2626", "#475569", "#06b6d4"],
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
                        title: { display: true, text: `Profit & Loss Summary - ${company.name}` },
                        legend: { display: type === "pie" },
                    },
                    scales: type === "pie" ? {} : {
                        y: { beginAtZero: true, grid: { color: "#eee" } },
                        x: { grid: { color: "#fafafa" } },
                    },
                },
            };
            ctx.chartInstance = new Chart(ctx, config);
        });
    }
}

registry.category("actions").add("profit_loss_dashboard", ProfitLossDashboard);