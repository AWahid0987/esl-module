from odoo import models, fields, api
from odoo.exceptions import UserError

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    bale_ids = fields.One2many('product.bale', 'manufacturing_order_id', string='Bales Created')
    create_bales = fields.Boolean('Create Bales', default=False, help='Automatically create bales when manufacturing is done')

    def action_confirm(self):
        res = super().action_confirm()
        return res

    def button_mark_done(self):
        res = super().button_mark_done()
        for production in self:
            if production.create_bales and production.state == 'done':
                production._create_bales_from_manufacturing()
        return res

    def _create_bales_from_manufacturing(self):
        """Create bales from finished products in manufacturing order"""
        self.ensure_one()
        if not self.move_finished_ids:
            return

        bale_obj = self.env['product.bale']
        
        # Get default location (usually finished products location)
        location = self.location_dest_id or self.env['stock.location'].search([
            ('usage', '=', 'internal'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)

        bale_count = 0
        for move in self.move_finished_ids:
            if move.product_id:
                product = move.product_id
                # Get quantity from move - use quantity field which represents produced quantity
                # In Odoo 19, when MO is done, move.quantity has the produced quantity
                quantity_done = move.quantity
                
                # If quantity is 0, try to get from move lines
                if quantity_done <= 0 and move.move_line_ids:
                    # Try different possible field names for done quantity
                    if hasattr(move.move_line_ids[0], 'qty_done'):
                        quantity_done = sum(move.move_line_ids.mapped('qty_done'))
                    elif hasattr(move.move_line_ids[0], 'quantity_done'):
                        quantity_done = sum(move.move_line_ids.mapped('quantity_done'))
                    elif hasattr(move.move_line_ids[0], 'quantity'):
                        quantity_done = sum(move.move_line_ids.mapped('quantity'))
                
                if quantity_done <= 0:
                    continue
                
                # Get weight from product (in KG)
                # Product weight is usually in KG, but check UOM conversion if needed
                weight_per_unit = 0
                if hasattr(product, 'weight') and product.weight:
                    weight_per_unit = product.weight
                    # If product UOM is not KG, convert it
                    if product.uom_id and product.uom_id.name.upper() != 'KG':
                        # Try to convert to KG
                        kg_uom = self.env['uom.uom'].search([('name', '=', 'kg')], limit=1)
                        if kg_uom:
                            weight_per_unit = product.uom_id._compute_quantity(product.weight, kg_uom)
                
                # If weight is 0 or not set, use a default (but warn)
                if weight_per_unit <= 0:
                    weight_per_unit = 300  # Default 300 KG
                    self.message_post(body=f"Warning: Product {product.name} has no weight set. Using default 300 KG for bales.")
                
                # Ensure weight doesn't exceed 350 KG
                if weight_per_unit > 350:
                    weight_per_unit = 350
                    self.message_post(body=f"Warning: Product {product.name} weight exceeds 350 KG. Setting bale weight to 350 KG maximum.")
                
                # Create bales - each finished product unit becomes a bale
                for i in range(int(quantity_done)):
                    bale_count += 1
                    # Generate unique bale number
                    bale_number = f"{self.name.replace('/', '-')}-{bale_count:04d}"
                    reference = f"{bale_count:04d}"
                    
                    bale_vals = {
                        'name': bale_number,
                        'reference': reference,
                        'product_id': product.id,
                        'weight_kg': weight_per_unit,
                        'quantity': 1,  # Number of cases/keys - can be updated manually
                        'location_id': location.id if location else False,
                        'manufacturing_order_id': self.id,
                        'state': 'available',
                    }
                    try:
                        bale_obj.create(bale_vals)
                    except Exception as e:
                        self.message_post(body=f"Error creating bale {bale_number}: {str(e)}")

        if bale_count > 0:
            self.message_post(body=f"Successfully created {bale_count} bale(s) from manufacturing order")
