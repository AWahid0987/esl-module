from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SchoolTimetable(models.Model):
    _name = 'school.timetable'
    _description = 'School Timetable'
    _order = "day_of_week, start_time"

    name = fields.Char(string="Name", required=True)
    class_id = fields.Many2one('school.class', string="Class", required=True)
    teacher_id = fields.Many2one('school.teacher', string="Teacher", required=True)
    subject_id = fields.Many2one('school.subject', string="Subject", required=True)
    day_of_week = fields.Selection([
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
    ], string="Day", required=True)
    start_time = fields.Float(string="Start Time", required=True, help="Use 24h format, e.g. 9:00 = 09:00, 13:50 = 13:30")
    end_time = fields.Float(string="End Time", required=True)

    def name_get(self):
        """Show subject + class + day in list views"""
        result = []
        for rec in self:
            name = f"[{rec.day_of_week.capitalize()} {rec.start_time:0.2f}-{rec.end_time:0.2f}] {rec.subject_id.name} ({rec.class_id.name})"
            result.append((rec.id, name))
        return result

    @api.constrains('start_time', 'end_time')
    def _check_time_validity(self):
        """Ensure valid time ranges"""
        for rec in self:
            if rec.start_time >= rec.end_time:
                raise ValidationError("End time must be greater than Start time.")
            if rec.start_time < 0 or rec.end_time > 24:
                raise ValidationError("Time must be between 0 and 24 (24h format).")

    @api.constrains('teacher_id', 'day_of_week', 'start_time', 'end_time')
    def _check_teacher_double_booking(self):
        """Prevent teacher from handling two classes at same time"""
        for rec in self:
            overlaps = self.env['school.timetable'].search([
                ('id', '!=', rec.id),
                ('teacher_id', '=', rec.teacher_id.id),
                ('day_of_week', '=', rec.day_of_week),
                ('start_time', '<', rec.end_time),
                ('end_time', '>', rec.start_time),
            ], limit=1)
            if overlaps:
                raise ValidationError(
                    f"Teacher {rec.teacher_id.name} already has a class "
                    f"on {rec.day_of_week.capitalize()} between {rec.start_time} and {rec.end_time}."
                )

    @api.constrains('class_id', 'day_of_week', 'start_time', 'end_time')
    def _check_class_double_booking(self):
        """Prevent one class from having two different teachers in same time slot"""
        for rec in self:
            overlaps = self.env['school.timetable'].search([
                ('id', '!=', rec.id),
                ('class_id', '=', rec.class_id.id),
                ('day_of_week', '=', rec.day_of_week),
                ('start_time', '<', rec.end_time),
                ('end_time', '>', rec.start_time),
            ], limit=1)
            if overlaps:
                raise ValidationError(
                    f"Class {rec.class_id.name} already has another subject scheduled "
                    f"on {rec.day_of_week.capitalize()} between {rec.start_time} and {rec.end_time}."
                )
    def action_print_timetable(self):
        """Print the timetable report as PDF"""
        return self.env.ref('school_manegment_system.action_report_class_timetable').report_action(self)
   