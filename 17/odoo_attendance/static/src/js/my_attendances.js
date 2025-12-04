/** @odoo-module **/

/**
 * This module extends HR Attendance to capture and store geolocation
 * information when employees check in/out.
 *
 * NOTE: The import paths below may need to be adjusted based on the actual
 * structure of the hr_attendance module in your Odoo 17 installation.
 * If you encounter import errors, check the actual paths in:
 * addons/hr_attendance/static/src/js/ or similar location.
 */

import { patch } from "@web/core/utils/patch";
import { MyAttendances } from "@hr_attendance/components/my_attendances/my_attendances";
import { KioskConfirm } from "@hr_attendance/components/kiosk_confirm/kiosk_confirm";
import { session } from "@web/session";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";

patch(MyAttendances.prototype, {
    /**
     * Override update_attendance to capture geolocation
     */
    async update_attendance() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                async (position) => {
                    const ctx = {
                        ...session.user_context,
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                    };

                    try {
                        const result = await this.orm.call(
                            "hr.employee",
                            "attendance_manual",
                            [[this.employee.id], "hr_attendance.hr_attendance_action_my_attendances"],
                            { context: ctx }
                        );

                        if (result.action) {
                            this.actionService.doAction(result.action);
                        } else if (result.warning) {
                            this.displayNotification(result.warning, {
                                type: "danger",
                            });
                        }
                    } catch (error) {
                        this.displayNotification(error.message || _t("Error occurred"), {
                            type: "danger",
                        });
                    }
                },
                (error) => {
                    // Handle geolocation errors
                    const errorMessage = error.message || _t("Unable to get location");
                    const dialogService = this.env.services.dialog || this.dialogService;
                    dialogService.add(Dialog, {
                        title: error.name || _t("Geolocation Error"),
                        body: `${errorMessage}. ${_t("Also check your site connection is secured!")}`,
                        confirm: () => {},
                    });
                }
            );
        } else {
            // Fallback when geolocation is not supported
            try {
                const result = await this.orm.call(
                    "hr.employee",
                    "attendance_manual",
                    [[this.employee.id], "hr_attendance.hr_attendance_action_my_attendances"],
                    { context: session.user_context }
                );

                if (result.action) {
                    this.actionService.doAction(result.action);
                } else if (result.warning) {
                    this.displayNotification(result.warning, {
                        type: "danger",
                    });
                }
            } catch (error) {
                this.displayNotification(error.message || _t("Error occurred"), {
                    type: "danger",
                });
            }
        }
    },
});

patch(KioskConfirm.prototype, {
    /**
     * Override sign in/out to capture geolocation
     */
    async _onClickSignInOut() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                async (position) => {
                    const ctx = {
                        ...session.user_context,
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                    };

                    try {
                        const result = await this.orm.call(
                            "hr.employee",
                            "attendance_manual",
                            [[this.employee_id], this.next_action],
                            { context: ctx }
                        );

                        if (result.action) {
                            this.actionService.doAction(result.action);
                        } else if (result.warning) {
                            this.displayNotification(result.warning, {
                                type: "danger",
                            });
                        }
                    } catch (error) {
                        this.displayNotification(error.message || _t("Error occurred"), {
                            type: "danger",
                        });
                    }
                },
                (error) => {
                    // Handle geolocation errors
                    const errorMessage = error.message || _t("Unable to get location");
                    const dialogService = this.env.services.dialog || this.dialogService;
                    dialogService.add(Dialog, {
                        title: error.name || _t("Geolocation Error"),
                        body: `${errorMessage}. ${_t("Also check your site connection is secured!")}`,
                        confirm: () => {},
                    });
                }
            );
        } else {
            // Fallback when geolocation is not supported - call original method
            super._onClickSignInOut();
        }
    },

    /**
     * Override pin pad OK to capture geolocation
     */
    async _onClickPinPadOk() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                async (position) => {
                    const ctx = {
                        ...session.user_context,
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                    };

                    const pinBox = this.el?.querySelector(".o_hr_attendance_PINbox");
                    const pinValue = pinBox?.value || "";

                    try {
                        const result = await this.orm.call(
                            "hr.employee",
                            "attendance_manual",
                            [[this.employee_id], this.next_action, pinValue],
                            { context: ctx }
                        );

                        if (result.action) {
                            this.actionService.doAction(result.action);
                        } else if (result.warning) {
                            this.displayNotification(result.warning, {
                                type: "danger",
                            });
                            if (pinBox) {
                                pinBox.value = "";
                            }
                            const okButton = this.el?.querySelector(".o_hr_attendance_pin_pad_button_ok");
                            if (okButton) {
                                okButton.disabled = false;
                            }
                        }
                    } catch (error) {
                        this.displayNotification(error.message || _t("Error occurred"), {
                            type: "danger",
                        });
                    }
                },
                (error) => {
                    // Handle geolocation errors
                    const errorMessage = error.message || _t("Unable to get location");
                    const dialogService = this.env.services.dialog || this.dialogService;
                    dialogService.add(Dialog, {
                        title: error.name || _t("Geolocation Error"),
                        body: `${errorMessage}. ${_t("Also check your site connection is secured!")}`,
                        confirm: () => {},
                    });
                }
            );
        } else {
            // Fallback when geolocation is not supported - call original method
            super._onClickPinPadOk();
        }
    },
});
