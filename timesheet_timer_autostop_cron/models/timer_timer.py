# -*- coding: utf-8 -*-
from odoo import api, fields, models

DEFAULT_MAX_HOURS = 8.0
ICP_KEY = "timesheet.timer_max_hours"


class TimerTimer(models.Model):
    _inherit = "timer.timer"

    @api.model
    def _get_limit_seconds(self):
        """Return limit in seconds; defaults to 8h."""
        try:
            val = self.env["ir.config_parameter"].sudo().get_param(ICP_KEY, str(DEFAULT_MAX_HOURS))
            hours = float(val or DEFAULT_MAX_HOURS)
        except Exception:
            hours = DEFAULT_MAX_HOURS
        return hours * 3600.0

    @api.model
    def _cron_autostop_timesheet_timers(self):
        """Scheduled Action entry point."""
        limit_seconds = self._get_limit_seconds()
        now = fields.Datetime.now()

        timers = self.sudo().search([
            ("timer_start", "!=", False),
            ("timer_pause", "=", False),  # works when False/NULL treated as False in Odoo
            ("res_model", "=", "account.analytic.line"),
            ("res_id", "!=", 0),
        ])

        AAL = self.env["account.analytic.line"].sudo()

        for t in timers:
            try:
                elapsed = (now - t.timer_start).total_seconds()
            except Exception:
                continue

            if elapsed < limit_seconds:
                continue

            line = AAL.browse(t.res_id).exists()
            if line:
                # Preferred path: stop using the timesheet API you provided.
                try:
                    line.action_timer_stop()
                    continue
                except Exception:
                    pass

            # Fallback: stop and unlink the timer directly
            try:
                t.action_timer_stop()
            except Exception:
                pass
            try:
                t.unlink()
            except Exception:
                pass
