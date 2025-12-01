from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = "res.partner"

    fbr_buyer_type_id = fields.Many2one(
        'fbr.buyer.type',
        string='FBR Buyer Type',
        help='Select the buyer registration type'
    )