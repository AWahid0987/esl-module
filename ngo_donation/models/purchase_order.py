from odoo import models, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    donation_project_id = fields.Many2one(
        "donation.projects",
        string="Donation Project",
        help="This purchase is linked to a donation project",
    )
