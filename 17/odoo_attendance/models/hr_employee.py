# -*- coding: utf-8 -*-
from geopy.geocoders import Nominatim
from odoo import exceptions, fields, models, _


class HrEmployee(models.Model):
    """Extend HR Employee for attendance with geo-location"""
    _inherit = 'hr.employee'

    # -------------------------------------------------------------------------
    # MANUAL ATTENDANCE (BUTTON)
    # -------------------------------------------------------------------------
    def attendance_manual(self, next_action, entered_pin=None):
        """Override manual attendance to add latitude and longitude via context"""
        self.ensure_one()

        # Read coordinates from context (set by JS / controller)
        latitude = self.env.context.get('latitude')
        longitude = self.env.context.get('longitude')

        # Inject coords in context so _attendance_action / _attendance_action_change
        # dono ko yeh values mil jayein
        ctx = dict(self.env.context, latitude=latitude, longitude=longitude)
        self = self.with_context(ctx)

        attendance_user_and_no_pin = self.user_has_groups(
            'hr_attendance.group_hr_attendance_user,'
            '!hr_attendance.group_hr_attendance_use_pin'
        )
        can_check_without_pin = attendance_user_and_no_pin or (
            self.user_id == self.env.user and entered_pin is None
        )

        if can_check_without_pin or (entered_pin is not None and entered_pin == self.sudo().pin):
            # IMPORTANT: keep original signature here
            return self._attendance_action(next_action)

        if not self.user_has_groups('hr_attendance.group_hr_attendance_user'):
            return {
                'warning': _(
                    'To activate Kiosk mode without pin code, you must have '
                    'access right as an Officer or above in the Attendance app. '
                    'Please contact your administrator.'
                )
            }

        return {'warning': _('Wrong PIN')}

    # -------------------------------------------------------------------------
    # MAIN ATTENDANCE ACTION (CALLED BY BUTTON / KIOSK)
    # -------------------------------------------------------------------------
    def _attendance_action(self, next_action):
        """Handle attendance changes with geo-location (compatible signature)."""
        self.ensure_one()
        employee = self.sudo()

        action_message = self.env['ir.actions.actions']._for_xml_id(
            'hr_attendance.hr_attendance_action_greeting_message'
        )

        action_message['previous_attendance_change_date'] = (
            employee.last_attendance_id
            and (employee.last_attendance_id.check_out or employee.last_attendance_id.check_in)
            or False
        )
        action_message['employee_name'] = employee.name
        action_message['barcode'] = employee.barcode
        action_message['next_action'] = next_action
        action_message['hours_today'] = employee.hours_today
        action_message['kiosk_delay'] = employee.company_id.attendance_kiosk_delay * 1000

        # Coordinates coming from context (set in attendance_manual or controller)
        latitude = self.env.context.get('latitude')
        longitude = self.env.context.get('longitude')

        # Call our extended method (see below) – it is fully backward compatible
        # We always pass latitude first, then longitude
        modified_attendance = employee._attendance_action_change(latitude, longitude)

        action_message['attendance'] = modified_attendance.read()[0]
        action_message['total_overtime'] = employee.total_overtime

        # Calculate overtime today
        action_message['overtime_today'] = self.env['hr.attendance.overtime'].sudo().search([
            ('employee_id', '=', employee.id),
            ('date', '=', fields.Date.context_today(self)),
            ('adjustment', '=', False),
        ]).duration or 0

        return {'action': action_message}

    # -------------------------------------------------------------------------
    # CORE ATTENDANCE CHANGE (OVERRIDE)
    # -------------------------------------------------------------------------
    def _attendance_action_change(self, *args, **kwargs):
        """
        Perform Check In/Check Out with geo-location.

        COMPATIBLE with standard hr_attendance:
          - our code may call:   _attendance_action_change(latitude, longitude)
          - core may call:       _attendance_action_change()
          - core 17 may call:    _attendance_action_change(geo_ip_response)
        """
        self.ensure_one()
        action_date = fields.Datetime.now()
        location_address = False

        latitude = None
        longitude = None

        # ---------------------------------------------------------------------
        # 1) Our internal call: (latitude, longitude)
        # ---------------------------------------------------------------------
        if len(args) == 2:
            latitude, longitude = args

        # ---------------------------------------------------------------------
        # 2) Possible core call with a geo_ip_response dict
        #    (Odoo might pass geoip_latitude / geoip_longitude)
        # ---------------------------------------------------------------------
        elif len(args) == 1 and args[0]:
            geo_ip_response = args[0] or {}
            latitude = (
                geo_ip_response.get('geoip_latitude')
                or geo_ip_response.get('latitude')
            )
            longitude = (
                geo_ip_response.get('geoip_longitude')
                or geo_ip_response.get('longitude')
            )

        # ---------------------------------------------------------------------
        # 3) Keyword arguments (if any)
        # ---------------------------------------------------------------------
        if 'latitude' in kwargs and latitude is None:
            latitude = kwargs.get('latitude')
        if 'longitude' in kwargs and longitude is None:
            longitude = kwargs.get('longitude')

        # ---------------------------------------------------------------------
        # 4) Fallback: context (set by controller / attendance_manual)
        # ---------------------------------------------------------------------
        if latitude is None:
            latitude = self.env.context.get('latitude')
        if longitude is None:
            longitude = self.env.context.get('longitude')

        # Normalize to float if possible
        def _to_float(v):
            try:
                return float(v)
            except Exception:
                return None

        latitude = _to_float(latitude)
        longitude = _to_float(longitude)

        # Try to get human-readable address from coordinates
        if latitude is not None and longitude is not None:
            try:
                geolocator = Nominatim(user_agent='odoo-attendance-geo', timeout=5)
                # Nominatim expects "lat, lon"
                location = geolocator.reverse(
                    f"{latitude}, {longitude}",
                    language='en'  # ALWAYS RETURN ENGLISH ADDRESS
                )
                if location:
                    location_address = location.address
            except Exception:
                location_address = False

        # ===== Check In =====
        if self.attendance_state != 'checked_in':
            vals = {
                'employee_id': self.id,
                'checkin_address': location_address or False,
                'checkin_latitude': latitude or False,
                'checkin_longitude': longitude or False,
                'checkin_location': (
                    f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"
                    if latitude is not None and longitude is not None else False
                ),
            }
            return self.env['hr.attendance'].create(vals)

        # ===== Check Out =====
        attendance = self.env['hr.attendance'].search(
            [('employee_id', '=', self.id), ('check_out', '=', False)],
            limit=1,
        )
        if attendance:
            attendance.write({
                'checkout_address': location_address or False,
                'checkout_latitude': latitude or False,
                'checkout_longitude': longitude or False,
                'checkout_location': (
                    f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"
                    if latitude is not None and longitude is not None else False
                ),
                'check_out': action_date,
            })
        else:
            raise exceptions.UserError(_(
                'Cannot perform check out on %(empl_name)s, could not find '
                'corresponding check in. Your attendances have probably been '
                'modified manually by HR.'
            ) % {'empl_name': self.sudo().name})

        return attendance
