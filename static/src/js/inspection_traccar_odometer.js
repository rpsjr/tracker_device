odoo.define("tracker_device.inspection_traccar_odometer", function (require) {
    "use strict";

    var FormController = require("web.FormController");

    FormController.include({
        _onSave: function () {
            var self = this;
            var res = this._super.apply(this, arguments);
            if (
                this.modelName === "fleet.vehicle.inspection" &&
                res &&
                typeof res.then === "function"
            ) {
                res.then(function () {
                    var state = self.model.get(self.handle, {raw: true});
                    var resId = state && state.res_id;
                    if (!resId) {
                        return;
                    }
                    self._rpc({
                        model: "fleet.vehicle.inspection",
                        method: "action_check_traccar_odometer_on_save",
                        args: [[resId]],
                    }).then(function (action) {
                        if (action && typeof action === "object" && action.type) {
                            self.do_action(action, {
                                on_close: function () {
                                    self.reload();
                                },
                            });
                        }
                    });
                });
            }
            return res;
        },
    });
});

