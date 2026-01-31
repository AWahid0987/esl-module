
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ProductBale(models.Model):
    _name = 'product.bale'
    _description = 'Product Bale'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char('Bale No', required=True, tracking=True)
    reference = fields.Char('Reference', size=4, required=True, help='4-digit reference number', tracking=True)
    barcode = fields.Char('Barcode', help='Scan barcode to identify bale', tracking=True)
    product_id = fields.Many2one('product.product', required=True, tracking=True)
    weight_kg = fields.Float('Weight (KG)', required=True, tracking=True)
    quantity = fields.Integer('Number of Cases/Keys', default=1, required=True, help='Number of cases or keys in this bale', tracking=True)
    location_id = fields.Many2one('stock.location', string='Location', domain=[('usage', '=', 'internal')], tracking=True)
    lot_id = fields.Many2one('stock.lot', string='Lot/Serial Number', tracking=True)
    manufacturing_order_id = fields.Many2one('mrp.production', string='Manufacturing Order', readonly=True)
    sale_order_line_id = fields.Many2one('sale.order.line', string='Sale Order Line', readonly=True)
    state = fields.Selection([
        ('available', 'Available'),
        ('sold', 'Sold')
    ], default='available', tracking=True)

    @api.constrains('reference')
    def _check_reference(self):
        for record in self:
            if record.reference:
                if not record.reference.isdigit():
                    raise ValidationError('Reference must contain only numbers')
                if len(record.reference) != 4:
                    raise ValidationError('Reference must be exactly 4 digits')

    @api.onchange('weight_kg')
    def _onchange_weight_kg(self):
        if self.weight_kg and self.weight_kg > 350:
            raise ValidationError('Weight cannot exceed 350 KG. Current weight: %s KG' % self.weight_kg)

    @api.constrains('weight_kg')
    def _check_weight_limit(self):
        for record in self:
            if record.weight_kg and record.weight_kg > 350:
                raise ValidationError('Weight cannot exceed 350 KG. Current weight: %s KG' % record.weight_kg)

    @api.constrains('quantity')
    def _check_quantity(self):
        for record in self:
            if record.quantity and record.quantity < 1:
                raise ValidationError('Quantity must be at least 1')

    def name_get(self):
        result = []
        for record in self:
            name = record.name
            if record.reference:
                name = f"[{record.reference}] {name}"
            if record.product_id:
                name = f"{name} - {record.product_id.name}"
            result.append((record.id, name))
        return result

    def action_mark_sold(self):
        self.write({'state': 'sold'})

    def action_mark_available(self):
        self.write({'state': 'available'})

    def action_view_manufacturing(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Manufacturing Order',
            'res_model': 'mrp.production',
            'res_id': self.manufacturing_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_sale_order(self):
        self.ensure_one()
        if self.sale_order_line_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Sale Order',
                'res_model': 'sale.order',
                'res_id': self.sale_order_line_id.order_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        return False
