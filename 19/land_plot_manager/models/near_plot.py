from odoo import models, fields

class LandNearPlot(models.Model):
    _name = "land.near.plot"
    _description = "Near Plot / Place for a Land"

    name = fields.Char(string="Place Name", required=True)
    product_id = fields.Many2one('product.template', string="Land Product", ondelete='cascade')
