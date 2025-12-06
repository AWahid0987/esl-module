from odoo import models, fields

class DonationCollectionCenter(models.Model):
    _name = 'donation.collection.center'
    _description = 'Donation Collection Center'

    name = fields.Char(string='Center Name', required=True)
    address = fields.Text(string='Address')
    region_id = fields.Many2one('donation.region', string='Region')
    capacity = fields.Integer(string='Capacity')