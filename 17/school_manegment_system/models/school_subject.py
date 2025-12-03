from odoo import models, fields

class SchoolSubject(models.Model):
    _name = 'school.subject'
    _description = 'School Subject'

    name = fields.Char(string="Subject Name", required=True)
    class_id = fields.Many2one('school.class', string="Class", required=True)
    max_marks = fields.Float(string="Maximum Marks", default=100)
    description = fields.Text(string="Description")
