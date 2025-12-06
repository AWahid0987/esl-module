from odoo import models, api, fields


class ResPartner(models.Model):
    _inherit = "res.partner"
    
    region_id = fields.Many2one('donation.region', string='Region')
    
    # @api.onchange('city')
    # def _onchange_city(self):
    #     if self.city:
    #         # Update the name field with the region name concatenated
    #         self.name = f"{self.name} {self.city}"
            