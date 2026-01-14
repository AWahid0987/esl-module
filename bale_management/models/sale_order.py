
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    bale_id = fields.Many2one('product.bale', string='Bale')

    @api.onchange('bale_id')
    def _onchange_bale_id(self):
        if self.bale_id:
            if self.bale_id.weight_kg > 350:
                raise ValidationError('Bale weight cannot exceed 350 KG')
            self.product_id = self.bale_id.product_id
            self.product_uom_qty = self.bale_id.weight_kg

    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty(self):
        if self.product_uom_qty and self.product_uom_qty > 350:
            raise ValidationError('Quantity cannot exceed 350 KG')

    @api.constrains('product_uom_qty')
    def _check_quantity_limit(self):
        for record in self:
            if record.product_uom_qty and record.product_uom_qty > 350:
                raise ValidationError('Quantity cannot exceed 350 KG. Current quantity: %s' % record.product_uom_qty)

    def _action_confirm(self):
        """Mark bale as sold when sale order is confirmed"""
        res = super()._action_confirm()
        for line in self.order_line:
            if line.bale_id and line.bale_id.state == 'available':
                line.bale_id.write({
                    'state': 'sold',
                    'sale_order_line_id': line.id
                })
        return res
