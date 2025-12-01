from odoo import models, fields, api

class HrEmployee(models.Model):
    _inherit = "hr.employee"

    ebf_code = fields.Char(string="Employee Code", readonly=True)

    @api.model
    def create(self, vals):
        if not vals.get('ebf_code'):
            vals['ebf_code'] = self.env['ir.sequence'].next_by_code('hr.employee.ebf') or '/'
        return super(HrEmployee, self).create(vals)
