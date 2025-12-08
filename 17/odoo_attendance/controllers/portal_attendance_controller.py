# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError, MissingError


class PortalAttendanceController(http.Controller):
    """Controller for Portal Attendance check in/out"""

    @http.route('/my/attendance', type='http', auth="user", website=True)
    def portal_attendance(self, **kw):
        """Portal attendance page"""
        employee = request.env.user.employee_ids[:1]
        if not employee:
            return request.render('odoo_attendance.portal_attendance_no_employee', {})
        
        # Get attendance state
        attendance_state = employee.attendance_state
        last_attendance = employee.last_attendance_id
        
        values = {
            'employee': employee,
            'attendance_state': attendance_state,
            'last_attendance': last_attendance,
        }
        return request.render('odoo_attendance.portal_attendance_page', values)

    @http.route('/my/attendance/check_in_out', type='json', auth="user", website=True, methods=['POST'], csrf=False)
    def portal_check_in_out(self, **kwargs):
        """Portal check in/out with geolocation"""
        employee = request.env.user.employee_ids[:1]
        if not employee:
            return {'error': 'No employee linked to current user.'}
        
        # Get geolocation from request params
        latitude = kwargs.get('latitude')
        longitude = kwargs.get('longitude')
        commit = kwargs.get('commit', '')
        
        # Try to get from jsonrpc params if available
        if not latitude or not longitude:
            params = kwargs.get('params', {})
            if params:
                latitude = params.get('latitude')
                longitude = params.get('longitude')
                commit = params.get('commit', '')
        
        if not latitude or not longitude:
            return {'error': 'Location is required. Please allow location access.'}
        
        try:
            # Convert to float and validate (don't round - use exact coordinates for 100% accuracy)
            try:
                latitude = float(latitude)
                longitude = float(longitude)
                # Don't round - use exact coordinates like backend does for 100% accuracy
            except (ValueError, TypeError) as e:
                return {'error': f'Invalid location coordinates: {str(e)}. Please try again.'}
            
            # Validate coordinates are in valid range
            if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
                return {'error': f'Invalid location coordinates (lat: {latitude}, lon: {longitude}). Please allow location access again.'}
            
            # Log coordinates for debugging
            import logging
            _logger = logging.getLogger(__name__)
            _logger.info(f"Portal attendance check in/out - Coordinates: {latitude}, {longitude}")
            
            # Pass coordinates via context
            employee_ctx = employee.with_context(
                latitude=latitude,
                longitude=longitude,
                commit=commit,
            )
            
            # Get current attendance state before check in/out
            current_state = employee.attendance_state
            
            # Perform check in/out - use the same method as backend
            # Pass coordinates directly to ensure they are used
            attendance = employee_ctx._attendance_action_change(
                latitude,
                longitude
            )
            
            # Verify location was saved
            if current_state == 'checked_out':
                if not attendance.checkin_latitude or not attendance.checkin_longitude:
                    _logger.error(f"Location not saved for check in - lat: {attendance.checkin_latitude}, lon: {attendance.checkin_longitude}")
                    return {'error': 'Location was not saved. Please try again.'}
                _logger.info(f"Check in location saved - lat: {attendance.checkin_latitude}, lon: {attendance.checkin_longitude}, address: {attendance.checkin_address}")
            else:
                if not attendance.checkout_latitude or not attendance.checkout_longitude:
                    _logger.error(f"Location not saved for check out - lat: {attendance.checkout_latitude}, lon: {attendance.checkout_longitude}")
                    return {'error': 'Location was not saved. Please try again.'}
                _logger.info(f"Check out location saved - lat: {attendance.checkout_latitude}, lon: {attendance.checkout_longitude}, address: {attendance.checkout_address}")
            
            # Save commit message based on what action was performed
            if commit:
                if current_state == 'checked_out':  # We were checked out, so we just checked in
                    attendance.write({'checkin_commit': commit})
                else:  # We were checked in, so we just checked out
                    attendance.write({'checkout_commit': commit})
            
            # Get updated state
            attendance_state = employee_ctx.attendance_state
            
            # Get location details for response
            if current_state == 'checked_out':  # We just checked in
                location_info = {
                    'address': attendance.checkin_address or '',
                    'latitude': attendance.checkin_latitude or '',
                    'longitude': attendance.checkin_longitude or '',
                    'location_link': attendance.checkin_location or '',
                }
            else:  # We just checked out
                location_info = {
                    'address': attendance.checkout_address or '',
                    'latitude': attendance.checkout_latitude or '',
                    'longitude': attendance.checkout_longitude or '',
                    'location_link': attendance.checkout_location or '',
                }
            
            return {
                'success': True,
                'attendance_state': attendance_state,
                'message': 'Check In successful' if attendance_state == 'checked_in' else 'Check Out successful',
                'check_in': attendance.check_in.strftime('%Y-%m-%d %H:%M:%S') if attendance.check_in else False,
                'check_out': attendance.check_out.strftime('%Y-%m-%d %H:%M:%S') if attendance.check_out else False,
                'checkin_address': attendance.checkin_address or '',
                'checkout_address': attendance.checkout_address or '',
                'location': location_info,
            }
        except Exception as e:
            import traceback
            return {'error': str(e) + ' - ' + traceback.format_exc()}

