/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { AccountReportFilters } from "@account_reports/components/account_report/filters/filters";
import { RecordSelector } from "@web/core/record_selectors/record_selector";

// We patch the 'components' static property of the original component
patch(AccountReportFilters.components, {
    // By adding RecordSelector here, we make it available in the component's template
    RecordSelector,
});

// Patch 2: Add a new method to the component's prototype to generate the correct props.
patch(AccountReportFilters.prototype, {
    /**
     * Prepares the props for the RecordSelector component.
     * @param {string} resModel The model of the record to select.
     * @param {string} optionKey The key in the report options where the ID is stored.
     */
    getRecordSelectorProps(resModel, optionKey, domain = []) {
    return {
        resModel,
        resId: this.controller.options[optionKey]?.[0] || false, // must be a single number or false
        update: (resId) => {
            this.filterClicked({ optionKey: optionKey, optionValue: [resId], reload: true });
        },
        domain,
    };
}
});