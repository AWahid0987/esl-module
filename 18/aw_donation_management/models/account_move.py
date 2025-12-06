from odoo import  models, api, fields


class AccountMove(models.Model):
    _inherit = "account.move"
    
    donation_order_id = fields.Many2one("donation.order", string="Donatation Order", readonly=True)
    
    received_by = fields.Char(string="Received By")
        
    
    
    
    @api.depends('amount_residual', 'move_type', 'state', 'company_id')
    def _compute_payment_state(self):
        super(AccountMove, self)._compute_payment_state()  # Call the original method
        for rec in self:
            if rec.donation_order_id:
                rec.donation_order_id.payment_status = rec.payment_state
