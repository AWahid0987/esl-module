from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    donor_type = fields.Selection([
        ('individual', 'Individual'),
        ('organization', 'Organization')
    ], string='Donor Type')
    related_projects = fields.Many2many('project.project', string='Related Projects')
    donation_ids = fields.One2many('ngo.donation', 'donor_id', string='Donations')
    total_donated = fields.Monetary(string='Total Donated', compute='_compute_total_donated', currency_field='company_currency')
    company_currency = fields.Many2one('res.currency', string='Currency', compute='_compute_company_currency')

    @api.depends('donation_ids.amount')
    def _compute_total_donated(self):
        for partner in self:
            partner.total_donated = sum(partner.donation_ids.mapped('amount'))

    @api.depends('company_id')
    def _compute_company_currency(self):
        for rec in self:
            rec.company_currency = rec.env.company.currency_id
