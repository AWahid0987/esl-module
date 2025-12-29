from odoo import models, fields, api

class ProjectProject(models.Model):
    _inherit = 'project.project'

    donation_ids = fields.One2many('ngo.donation', 'project_id', string='Donations')
    total_donations = fields.Monetary(compute='_compute_total_donations', currency_field='company_currency')
    remaining_balance = fields.Monetary(compute='_compute_remaining_balance', currency_field='company_currency')
    company_currency = fields.Many2one('res.currency', string='Currency', compute='_compute_company_currency')

    @api.depends('donation_ids.amount')
    def _compute_total_donations(self):
        for project in self:
            project.total_donations = sum(project.donation_ids.mapped('amount'))

    @api.depends('total_donations')
    def _compute_remaining_balance(self):
        for project in self:
            # Placeholder: replace with actual utilization logic if needed
            project.remaining_balance = project.total_donations

    @api.depends('company_id')
    def _compute_company_currency(self):
        for rec in self:
            rec.company_currency = rec.env.company.currency_id
