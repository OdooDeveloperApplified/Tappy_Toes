/** @odoo-module **/

import { registry } from "@web/core/registry";
import { ImageField, imageField } from "@web/views/fields/image/image_field";
import { useFileViewer } from "@web/core/file_viewer/file_viewer_hook";

export class ImageFieldViewer extends ImageField {
    static template = "app_account_profit_and_loss.ImageFieldViewer";

    setup() {
        super.setup();
        this.fileViewer = useFileViewer();
    }

    onClickImage() {
        if (!this.props.record.data[this.props.name]) {
            return;
        }
        const fieldName = this.fieldType === "many2one" ? this.props.previewImage : this.props.name;
        const url = this.getUrl(fieldName);
        this.fileViewer.open({
            isViewable: true,
            isImage: true,
            displayName: this.props.record.data.display_name || this.imgAlt,
            downloadUrl: url,
            defaultSource: url,
        });
    }
}

export const imageFieldViewer = {
    ...imageField,
    component: ImageFieldViewer,
};

registry.category("fields").add("app_image_viewer", imageFieldViewer);
