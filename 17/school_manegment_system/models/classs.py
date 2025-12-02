from odoo import models, fields, api

class SchoolClass(models.Model):
    _name = 'school.class'
    _description = 'School Class'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Class Name', required=True, tracking=True)
    code = fields.Char(string='Class Selection', required=True, tracking=True)
    capacity = fields.Integer(string='Capacity', default=30)
    active = fields.Boolean(default=True)
    student_ids = fields.One2many('school.student', 'class_id', string='Students')
    subject_ids = fields.One2many('school.subject', 'class_id', string='Subjects')
    result_ids = fields.One2many('school.result', 'class_id', string='Results')
    description = fields.Text(string='Description') 
    timetable_ids = fields.One2many("school.timetable", "class_id", string="Timetable")
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        help="Analytic account for this class's fees."
    )

    def action_print_timetable(self):
        """Print the timetable report as PDF"""
        return self.env.ref('school_manegment_system.action_report_class_timetable').report_action(self)
   