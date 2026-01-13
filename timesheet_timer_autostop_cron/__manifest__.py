# -*- coding: utf-8 -*-
{
    "name": "Timesheet Timer Auto-Stop (Scheduled Action)",
    "version": "19.0.1.0.0",
    "category": "Services/Timesheets",
    "summary": "Stops running timesheet timers after a configured limit using a scheduled action.",
    "description": """
This module creates a Scheduled Action (cron) that:
- Searches running timer.timer records linked to account.analytic.line
- If (now - timer_start) >= configured limit, it stops the timer by calling
  account.analytic.line.action_timer_stop() (and unlinks timer per Odoo behavior)

Configuration:
- System Parameter key: timesheet.timer_max_hours (default 8)
""",
    "author": "EBITDA Solutions",
    "license": "LGPL-3",
    "depends": [
        "timer",
        "hr_timesheet",
    ],
    "data": [
        "data/ir_cron.xml",
    ],
    "installable": True,
    "application": False,
}
