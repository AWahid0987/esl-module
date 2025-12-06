from odoo import models, fields, api
import datetime
class DonationProductLine(models.Model):
    _name = 'donation.product.line'
    _description = 'Donation Product Line'

    name = fields.Char(string='Name', required=True)
    product_id = fields.Many2one('product.product', string='Product')
    account_id = fields.Many2one('account.account', string="Account")
    
    donation_order_id = fields.Many2one('donation.order', string='Donation Order')
    currency_id = fields.Many2one(
            'res.currency', 
            string='Currency', 
            default=lambda self: self.env.company.currency_id.id
        )
    amount = fields.Monetary(
        currency_field='currency_id',
        readonly=False,
        string="Amount"
    )
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.name
            
    # @api.model
    # def create_default_products(self):
    #     product_names = [
    #         'صدقه', 'ھدیہ', 'شفاء', 'ملاقات', 'زکوٰہ', 
    #         'نعت خوانی', 'ملتان شریف فنڈ', 'لاھور فنڈ', 'قربانی والا معاملہ', 
    #         'لنکر م ش', 'ھدیہ امام حسین', 'کنسٹرکشن', 'جمادی الاوّل-21', 
    #         'قطرانہ', 'سپیشل فنڈ لاھور'
    #     ]
    #     product_obj = self.env['product.product']
    #     for name in product_names:
    #         product = product_obj.search([('name', '=', name)], limit=1)
    #         if not product:
    #             product_obj.create({'name': name})
