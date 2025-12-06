from odoo import models, fields

class DonationRegion(models.Model):
    _name = 'donation.region'
    _description = 'Donation Region'

    name = fields.Char(string='Region Name', required=True)
    code = fields.Char(string='Region Code')