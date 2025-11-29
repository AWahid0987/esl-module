from odoo import models, fields

class LandNotebook(models.Model):
    _name = "land.notebook"
    _description = "Detailed Notebook for Land Plotting"

    purchase_order_id = fields.Many2one('purchase.order', string="Purchase Order")
    total_land = fields.Float(string="Total Land (ایکڑ)")
    plotted_land = fields.Float(string="Plotted Portion (ایکڑ)")
    remaining_land = fields.Float(string="Remaining Land (ایکڑ)")
    notes = fields.Text(string="Notes")
