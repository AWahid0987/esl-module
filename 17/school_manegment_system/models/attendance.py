# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class Attendance(models.Model):
    _name = 'school.attendance'
    _description = 'Student Attendance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'
    _sql_constraints = [
        ('unique_student_date', 'unique(student_id, date)', 'Attendance for this student on this date already exists!'),
    ]

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today, tracking=True)
    student_id = fields.Many2one('school.student', string='Student', required=True, tracking=True,
                                domain="[('state', '=', 'admitted')]")
    class_id = fields.Many2one('school.class', string="Class")  # 👈 Add this line
    start_time = fields.Datetime(string="Start Time")
    end_time = fields.Datetime(string="End Time")
    classroom_id = fields.Many2one('school.class', string='Class', related='student_id.class_id', store=True)
    status = fields.Selection([
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late')
    ], string='Status', required=True, default='present', tracking=True)
    remark = fields.Text(string='Remarks', tracking=True)
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed')], string='Stage', default='draft', tracking=True)

    # New: check in / check out timestamps and computed duration
    check_in = fields.Datetime(string='Check In')
    check_out = fields.Datetime(string='Check Out')
    duration_minutes = fields.Float(string='Duration (mins)', compute='_compute_duration', store=True)

    @api.model
    def create(self, vals):
        # Prevent duplicate attendance for the same student and date
        if vals.get('student_id') and vals.get('date'):
            existing = self.search([
                ('student_id', '=', vals['student_id']),
                ('date', '=', vals['date'])
            ], limit=1)
            if existing:
                raise ValidationError(_('Attendance is already set for this student on this date!'))
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('school.attendance') or _('New')
        return super(Attendance, self).create(vals)

    def write(self, vals):
        # Assign sequence if name is still 'New' and not set
        for rec in self:
            if ('name' not in vals or vals.get('name') == _('New')) and rec.name == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('school.attendance') or _('New')
        # Prevent duplicate attendance for the same student and date
        if 'student_id' in vals or 'date' in vals:
            for rec in self:
                student_id = vals.get('student_id', rec.student_id.id)
                date = vals.get('date', rec.date)
                existing = self.search([
                    ('student_id', '=', student_id),
                    ('date', '=', date),
                    ('id', '!=', rec.id)
                ], limit=1)
                if existing:
                    raise ValidationError(_('Attendance is already set for this student on this date!'))
        return super(Attendance, self).write(vals)

    def action_confirm(self):
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_("Only draft attendance can be confirmed."))
            record.state = 'confirmed'
            # When confirming, if no check_in exist and status present, set check_in to now
            if record.status == 'present' and not record.check_in:
                record.check_in = fields.Datetime.now()
    def action_qr_scan(self):
        """
        This button simulates a manual QR scan (entry/exit) from the form view.
        It uses the same logic as record_scan_for_student().
        """
        for record in self:
            student = record.student_id
            if not student:
                raise ValidationError(_("Please select a student before scanning."))

            # Call the helper logic that records QR attendance
            self.record_scan_for_student(student)

            record.message_post(body=_("QR scan processed for student: %s") % student.name)
            _logger.info("Manual QR scan triggered for student %s", student.name)
        return True


    @api.depends('check_in', 'check_out')
    def _compute_duration(self):
        for rec in self:
            if rec.check_in and rec.check_out:
                try:
                    in_dt = fields.Datetime.from_string(rec.check_in)
                    out_dt = fields.Datetime.from_string(rec.check_out)
                    delta = out_dt - in_dt
                    rec.duration_minutes = round(delta.total_seconds() / 60.0, 2)
                except Exception:
                    rec.duration_minutes = 0.0
            else:
                rec.duration_minutes = 0.0

    # Helper used by external QR controller or student.mark_attendance_from_qr
    @api.model
    def record_scan_for_student(self, student):
        """
        Low-level helper that given a student record creates/updates today's attendance.
        Returns the attendance record.
        """
        today = fields.Date.context_today(self)
        now = fields.Datetime.now()
        att = self.search([('student_id', '=', student.id), ('date', '=', today)], limit=1)
        if not att:
            # create with check_in
            att = self.create({
                'student_id': student.id,
                'date': today,
                'status': 'present',
                'check_in': now,
                'name': self.env['ir.sequence'].next_by_code('school.attendance') or _('New'),
                'state': 'confirmed',
            })
            _logger.info("Created attendance (check-in) for %s on %s", student.name, today)
        else:
            # if only check_in present, set check_out
            if att.check_in and not att.check_out:
                att.write({'check_out': now, 'state': 'confirmed'})
                _logger.info("Updated attendance (check-out) for %s on %s", student.name, today)
            else:
                _logger.info("Attendance already complete for %s on %s", student.name, today)
        return att

    # REPORTS / SUMMARY
    @api.model
    def daily_class_report(self, date=None, class_id=None):
        """
        Returns a dict summary for a given date and class (or for all classes if class_id is False).
        Example return:
        {
            'date': '2025-11-04',
            'class_id': 3 or False,
            'total_students': 30,
            'present_count': 25,
            'absent_count': 5,
            'late_count': 0,
            'present_list': [ (student_id, student_name), ... ],
            'absent_list': [ (student_id, student_name), ... ]
        }
        """
        date = date or fields.Date.context_today(self)
        domain = [('date', '=', date)]
        if class_id:
            domain += [('classroom_id', '=', int(class_id))]

        attendances = self.search(domain)
        present = attendances.filtered(lambda a: a.status == 'present')
        absent = attendances.filtered(lambda a: a.status == 'absent')
        late = attendances.filtered(lambda a: a.status == 'late')

        # total students in that class (admitted)
        if class_id:
            total_students = self.env['school.student'].search_count([('class_id', '=', int(class_id)), ('state', '=', 'admitted')])
            # students without an attendance record are considered absent in the report
            attended_student_ids = attendances.mapped('student_id').ids
            all_student_records = self.env['school.student'].search([('class_id', '=', int(class_id)), ('state', '=', 'admitted')])
            absent_students_missing = [s for s in all_student_records if s.id not in attended_student_ids]
            absent_list = [(a.student_id.id, a.student_id.name) for a in absent] + [(s.id, s.name) for s in absent_students_missing]
        else:
            # across all classes:
            total_students = self.env['school.student'].search_count([('state', '=', 'admitted')])
            attended_student_ids = attendances.mapped('student_id').ids
            all_student_records = self.env['school.student'].search([('state', '=', 'admitted')])
            absent_students_missing = [s for s in all_student_records if s.id not in attended_student_ids]
            absent_list = [(a.student_id.id, a.student_id.name) for a in absent] + [(s.id, s.name) for s in absent_students_missing]

        present_list = [(a.student_id.id, a.student_id.name) for a in present]

        return {
            'date': date,
            'class_id': class_id or False,
            'total_students': total_students,
            'present_count': len(present_list),
            'absent_count': len(absent_list),
            'late_count': len(late),
            'present_list': present_list,
            'absent_list': absent_list,
        }
