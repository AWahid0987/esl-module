from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    @api.model
    def _get_translated_name(self, product):
        """Get translated product name using website translation method"""
        try:
            from odoo.http import request
            if hasattr(request, 'website') and request.website:
                return request.website.translate_product(product)['name']
        except:
            pass
        return product.name if product else ''
    
    @api.model
    def _get_translated_description(self, product):
        """Get translated product description using website translation method"""
        try:
            from odoo.http import request
            if hasattr(request, 'website') and request.website:
                return request.website.translate_product(product)['description']
        except:
            pass
        return product.description_ecommerce or product.description_sale or product.description if product else ''
    
    @api.depends('name')
    def _compute_translated_name(self):
        """Compute translated product name"""
        for product in self:
            product.translated_name = self._get_translated_name(product)
    
    @api.depends('description_ecommerce', 'description_sale', 'description')
    def _compute_translated_description(self):
        """Compute translated product description"""
        for product in self:
            product.translated_description = self._get_translated_description(product)
    
    translated_name = fields.Char(
        string='Translated Name',
        compute='_compute_translated_name',
        store=False,
        help='Product name translated to current language'
    )
    
    translated_description = fields.Text(
        string='Translated Description',
        compute='_compute_translated_description',
        store=False,
        help='Product description translated to current language'
    )

