# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class HrAttendanceController(http.Controller):
    """Controller for HR Attendance systray actions"""

    @http.route('/hr_attendance/systray', type='json', auth="user")
    def systray_attendance(self, **kwargs):
        # Get the first employee linked to the current user
        employee = request.env.user.employee_ids[:1]
        if not employee:
            return {'error': 'No employee linked to current user.'}

        # geo_ip_response comes from JS (browser geolocation)
        geo_ip_response = request.params.get('geo_ip_response') or {}

        # Extract latitude and longitude (if provided)
        latitudes = geo_ip_response.get('latitude')
        longitudes = geo_ip_response.get('longitude')

        # Pass coords + geo response via context
        employee_ctx = employee.with_context(
            latitude=latitudes,
            longitude=longitudes,
            geo_ip_response=geo_ip_response,
        )

        # Let the employee method handle check in / check out
        employee_ctx._attendance_action_change()

        # Return current attendance state for the systray
        return {'attendance_state': employee_ctx.attendance_state}
