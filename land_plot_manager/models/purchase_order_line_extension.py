from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    total_land = fields.Float(string="Total Land")
    plotted_land = fields.Char(string="Plot Land")
    notes = fields.Char(string="Note")
    land_purchase = fields.Boolean(
        string="Land Purchase?",
        help="Check if this purchase order is related to land."
    )

    doc_attachment_ids = fields.Many2many(
        'ir.attachment',
        'purchase_order_ir_attachments_rel',
        'order_id',
        'attachment_id',
        string='Documents'
    )