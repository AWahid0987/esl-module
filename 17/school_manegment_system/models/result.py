from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


# ========================================================
# Student-wise Result
# ========================================================
class SchoolResult(models.Model):
    _name = 'school.result'
    _description = 'Student Result Record'

    roll_number = fields.Char(string="Roll Number", required=True)
    student_id = fields.Many2one('school.student', string="Student", required=True)
    class_id = fields.Many2one('school.class', string="Class", required=True)
    exam_id = fields.Many2one('school.exam', string="Exam", required=True)
    line_ids = fields.One2many('school.result.line', 'result_id', string="Subjects")

    total_marks = fields.Float(string="Total Marks", compute="_compute_totals", store=True)
    obtained_marks = fields.Float(string="Obtained Marks", compute="_compute_totals", store=True)
    percentage = fields.Float(string="Percentage", compute="_compute_totals", store=True)
    grade = fields.Selection(
        [('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('F', 'F')],
        string="Grade", compute="_compute_totals", store=True
    )

    @api.depends('line_ids.obtained_marks', 'line_ids.max_marks')
    def _compute_totals(self):
        for rec in self:
            total = sum(line.max_marks for line in rec.line_ids)
            obtained = sum(line.obtained_marks for line in rec.line_ids)
            rec.total_marks = total
            rec.obtained_marks = obtained
            rec.percentage = (obtained / total * 100) if total else 0

            if rec.percentage >= 90:
                rec.grade = 'A'
            elif rec.percentage >= 75:
                rec.grade = 'B'
            elif rec.percentage >= 60:
                rec.grade = 'C'
            elif rec.percentage >= 50:
                rec.grade = 'D'
            else:
                rec.grade = 'F'


class SchoolResultLine(models.Model):
    _name = 'school.result.line'
    _description = 'Result Subject Line'

    result_id = fields.Many2one('school.result', string="Result", ondelete="cascade")
    subject_id = fields.Many2one('school.subject', string="Subject", required=True)
    teacher_id = fields.Many2one('school.teacher', string="Teacher")
    obtained_marks = fields.Float(string="Obtained Marks", default=0)
    max_marks = fields.Float(related="subject_id.max_marks", store=True)
    percentage = fields.Float(compute="_compute_percentage", store=True)

    @api.depends('obtained_marks', 'max_marks')
    def _compute_percentage(self):
        for rec in self:
            rec.percentage = (rec.obtained_marks / rec.max_marks * 100) if rec.max_marks else 0


# ========================================================
# Class-wise Result Entry (for Teachers)
# ========================================================
class SchoolResultClass(models.Model):
    _name = "school.result.class"
    _description = "Class Wise Result Entry"
    _inherit = ['mail.thread']

    name = fields.Char(string="Result Name", compute="_compute_name", store=True)
    class_id = fields.Many2one('school.class', string="Class", required=True, tracking=True)
    exam_id = fields.Many2one('school.exam', string="Exam", required=True, tracking=True)
    teacher_id = fields.Many2one('school.teacher', string="Teacher", tracking=True,
                                 default=lambda self: self.env.user.teacher_id)
    line_ids = fields.One2many('school.result.class.line', 'result_id', string="Result Lines")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
    ], string="Status", default='draft', tracking=True)

    @api.depends('class_id', 'exam_id')
    def _compute_name(self):
        for rec in self:
            if rec.class_id and rec.exam_id:
                rec.name = f"{rec.class_id.name} - {rec.exam_id.name}"
            else:
                rec.name = "New Result"

    @api.onchange('class_id', 'exam_id')
    def _onchange_class_exam(self):
        """Auto-fill students and subjects taught by current teacher."""
        if not (self.class_id and self.exam_id):
            self.line_ids = [(5, 0, 0)]
            return

        teacher = self.teacher_id or self.env.user.teacher_id
        if not teacher:
            return

        teacher_subjects = teacher.subject_ids.ids
        if not teacher_subjects:
            self.line_ids = [(5, 0, 0)]
            return

        students = self.env['school.student'].search([('class_id', '=', self.class_id.id)])
        lines = []
        for student in students:
            for subj_id in teacher_subjects:
                lines.append((0, 0, {
                    'student_id': student.id,
                    'subject_id': subj_id,
                    'teacher_id': teacher.id,
                    'obtained_marks': 0,
                }))
        self.line_ids = [(5, 0, 0)] + lines

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_approve(self):
        """Convert class result lines into student-wise results."""
        for rec in self:
            for line in rec.line_ids:
                student_result = self.env['school.result'].search([
                    ('student_id', '=', line.student_id.id),
                    ('exam_id', '=', rec.exam_id.id),
                ], limit=1)

                if not student_result:
                    student_result = self.env['school.result'].create({
                        'roll_number': line.student_id.roll_number,
                        'student_id': line.student_id.id,
                        'class_id': rec.class_id.id,
                        'exam_id': rec.exam_id.id,
                    })

                existing_line = student_result.line_ids.filtered(lambda l: l.subject_id.id == line.subject_id.id)
                if existing_line:
                    existing_line.write({
                        'obtained_marks': line.obtained_marks,
                        'teacher_id': line.teacher_id.id,
                    })
                else:
                    student_result.line_ids = [(0, 0, {
                        'subject_id': line.subject_id.id,
                        'teacher_id': line.teacher_id.id,
                        'obtained_marks': line.obtained_marks,
                    })]
            rec.write({'state': 'approved'})


class SchoolResultClassLine(models.Model):
    _name = 'school.result.class.line'
    _description = 'Class Result Line'

    result_id = fields.Many2one('school.result.class', string="Result", ondelete="cascade")
    student_id = fields.Many2one('school.student', string="Student", required=True)
    subject_id = fields.Many2one('school.subject', string="Subject", required=True)
    teacher_id = fields.Many2one('school.teacher', string="Teacher")
    obtained_marks = fields.Float(string="Obtained Marks", default=0)
