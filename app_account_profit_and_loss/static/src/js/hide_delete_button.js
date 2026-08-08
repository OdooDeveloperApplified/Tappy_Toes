/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { ListController } from "@web/views/list/list_controller";
import { user } from "@web/core/user";
import { onWillStart } from "@odoo/owl";

const getHideDeletePatch = () => ({
    setup() {
        super.setup(...arguments);
        this.hideAccountMoveDelete = false;
        if (this.props.resModel === 'account.move') {
            onWillStart(async () => {
                this.hideAccountMoveDelete = await user.hasGroup('app_account_profit_and_loss.group_hide_delete_account_move');
            });
        }
    },
    getStaticActionMenuItems() {
        const menuItems = super.getStaticActionMenuItems(...arguments);
        if (menuItems.delete && this.props.resModel === 'account.move' && this.hideAccountMoveDelete) {
            delete menuItems.delete;
        }
        return menuItems;
    }
});

patch(FormController.prototype, getHideDeletePatch());
patch(ListController.prototype, getHideDeletePatch());
