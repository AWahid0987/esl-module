# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import base64
import qrcode
from io import BytesIO
import logging

_logger = logging.getLogger(__name__)


class Student(models.Model):
    _name = 'school.student'
    _description = 'Student'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # BASIC INFORMATION
    name = fields.Char(string='Name', required=True, tracking=True)
    roll_number = fields.Char(string="Roll Number", tracking=True, copy=False)
    admission_number = fields.Char(string="Admission Number", tracking=True, readonly=True, copy=False)
    date_of_birth = fields.Date(string='Date of Birth', required=True, tracking=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
                              string='Gender', required=True, tracking=True)
    blood_group = fields.Selection([
        ('a+', 'A+'), ('a-', 'A-'), ('b+', 'B+'), ('b-', 'B-'),
        ('ab+', 'AB+'), ('ab-', 'AB-'), ('o+', 'O+'), ('o-', 'O-')
    ], string='Blood Group', tracking=True)
    address = fields.Text(string='Address', tracking=True)
    phone = fields.Char(string='Phone', tracking=True)
    email = fields.Char(string='Email', tracking=True)
    parent_name = fields.Char(string='Parent/Guardian Name', required=True, tracking=True)
    parent_phone = fields.Char(string='Parent/Guardian Phone', tracking=True)
    parent_email = fields.Char(string='Parent/Guardian Email', tracking=True)
    class_id = fields.Many2one('school.class', string='Class', tracking=True)
    subject_ids = fields.Many2many('school.subject', string="Subjects", help="Auto assigned based on class")

    # STATE
    state = fields.Selection([('draft', 'Draft'), ('admitted', 'Admitted'), ('left', 'Left')],
                             string='Status', default='draft', tracking=True)
    admission_date = fields.Date(string='Admission Date', tracking=True)
    leaving_date = fields.Date(string='Leaving Date', tracking=True)

    # RELATED
    attendance_ids = fields.One2many('school.attendance', 'student_id', string='Attendance History')
    fee_ids = fields.One2many('school.fee', 'student_id', string='Fee History')

    # STATS
    attendance_count = fields.Integer(compute='_compute_attendance_count', string='Attendance Count')
    fee_count = fields.Integer(compute='_compute_fee_count', string='Fee Count')

    # IMAGE + QR
    image_1920 = fields.Image("Photo", max_width=1920, max_height=1920, tracking=True)
    qr_code = fields.Binary("QR Code", attachment=True)

    # EXTRA CONTACTS
    admin_phone = fields.Char(string="Admin Phone")
    teacher_phone = fields.Char(string="Class Teacher Phone")

    partner_id = fields.Many2one('res.partner', string='Student Partner', ondelete='restrict')

    # CREATE / WRITE
    @api.model_create_multi
    def create(self, vals_list):
        IrSequence = self.env['ir.sequence'].sudo()
        records = super().create(vals_list)
        for rec in records:
            # Generate admission & roll numbers if missing
            if not rec.admission_number:
                rec.admission_number = IrSequence.next_by_code('school.student') or rec.admission_number
            if not rec.roll_number:
                rec.roll_number = IrSequence.next_by_code('school.student.roll') or rec.roll_number

            # Auto-create partner if missing
            if not rec.partner_id:
                partner = self.env['res.partner'].create({'name': rec.name})
                rec.partner_id = partner.id

            # Generate QR code (includes name, class, roll)
            rec._generate_qr_code()
        return records

    def write(self, vals):
        res = super().write(vals)
        trigger_fields = {'name', 'roll_number', 'class_id', 'admission_number'}
        if any(field in vals for field in trigger_fields):
            for rec in self:
                rec._generate_qr_code()
        return res

    # COMPUTES
    @api.depends('attendance_ids')
    def _compute_attendance_count(self):
        for record in self:
            record.attendance_count = len(record.attendance_ids or [])

    @api.depends('fee_ids')
    def _compute_fee_count(self):
        for record in self:
            record.fee_count = len(record.fee_ids or [])

    # QR CODE GENERATOR
    def _generate_qr_code(self):
        """Generate QR code with student's key info (Name, Class, Roll Number)"""
        for record in self.sudo():
            if not record.name or not record.roll_number:
                _logger.warning("Skipping QR generation: missing name or roll for student id %s", record.id)
                continue
            try:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=8,
                    border=4,
                )
                qr_data = (
                    f"Name:{record.name}\n"
                    f"Class:{record.class_id.name or ''}\n"
                    f"Roll:{record.roll_number}"
                )
                qr.add_data(qr_data)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                buf = BytesIO()
                img.save(buf, format="PNG")
                record.qr_code = base64.b64encode(buf.getvalue())
                _logger.info("QR code generated for student %s", record.name)
            except Exception as e:
                _logger.error("QR generation failed for %s: %s", record.name, e)

    # ACTIONS
    def action_admit(self):
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_("Only draft students can be admitted."))
            if not record.roll_number:
                record.roll_number = self.env['ir.sequence'].sudo().next_by_code('school.student.roll')
            record.state = 'admitted'
            record.admission_date = fields.Date.today()
            # Ensure QR regeneration after state change
            record._generate_qr_code()

    def action_leave(self):
        for record in self:
            if record.state != 'admitted':
                raise ValidationError(_("Only admitted students can leave."))
            record.state = 'left'
            record.leaving_date = fields.Date.today()

    # QR SCAN ATTENDANCE (called when QR scanned)
    def mark_attendance_from_qr(self):
        """
        Called when a student's QR is scanned.
        Behavior:
        - If no attendance for today: create attendance with check_in = now, status 'present', state 'draft' (or auto confirm).
        - If attendance exists and check_in exists but check_out is empty: set check_out = now.
        - If both exist: return current record (or optionally create a second record if you want).
        - SMS is sent to parent on each scan (check-in and check-out).
        """
        Attendance = self.env['school.attendance']
        now = fields.Datetime.now()
        today = fields.Date.context_today(self)
        results = []
        for student in self:
            if student.state != 'admitted':
                _logger.warning("QR scan for student %s ignored because not admitted.", student.id)
                results.append(False)
                continue

            # Search for today's attendance record
            att = Attendance.search([
                ('student_id', '=', student.id),
                ('date', '=', today)
            ], limit=1)

            try:
                if not att:
                    # create new attendance with check_in
                    att = Attendance.create({
                        'student_id': student.id,
                        'date': today,
                        'status': 'present',
                        'check_in': now,
                        'name': self.env['ir.sequence'].next_by_code('school.attendance') or _('New'),
                        'state': 'confirmed',  # auto-confirm on scan (change if you prefer draft)
                    })
                    # Send SMS for check-in
                    if student.parent_phone:
                        try:
                            self.env['sms.sms'].create({
                                'body': _("Dear %s, %s checked IN at %s on %s.") % (
                                    student.parent_name or _('Parent'),
                                    student.name,
                                    fields.Datetime.to_string(fields.Datetime.context_timestamp(self.sudo(), fields.Datetime.from_string(now))),
                                    today
                                ),
                                'number': student.parent_phone,
                                'partner_id': student.partner_id.id or False
                            })
                        except Exception as sms_e:
                            _logger.error("Failed to send check-in SMS for %s: %s", student.name, sms_e)
                    _logger.info("Attendance (check-in) created for %s on %s", student.name, today)
                else:
                    # If check_in exists and check_out empty -> set check_out
                    if att.check_in and not att.check_out:
                        att.check_out = now
                        att.state = 'confirmed'
                        # Optionally compute duration - handled by computed field
                        if student.parent_phone:
                            try:
                                self.env['sms.sms'].create({
                                    'body': _("Dear %s, %s checked OUT at %s on %s.") % (
                                        student.parent_name or _('Parent'),
                                        student.name,
                                        fields.Datetime.to_string(fields.Datetime.context_timestamp(self.sudo(), fields.Datetime.from_string(now))),
                                        today
                                    ),
                                    'number': student.parent_phone,
                                    'partner_id': student.partner_id.id or False
                                })
                            except Exception as sms_e:
                                _logger.error("Failed to send check-out SMS for %s: %s", student.name, sms_e)
                        _logger.info("Attendance (check-out) recorded for %s on %s", student.name, today)
                    else:
                        # Already has both check_in and check_out: do nothing (or could log)
                        _logger.info("QR scan: attendance already has check-in & check-out for %s on %s", student.name, today)
                results.append(att)
            except Exception as e:
                _logger.error("Error during QR attendance for %s: %s", student.name, e)
                results.append(False)
        return results

    # ONCHANGE
    @api.onchange('class_id')
    def _onchange_class_id(self):
        self.subject_ids = self.class_id.subject_ids if self.class_id else [(5, 0, 0)]
