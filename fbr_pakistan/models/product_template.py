# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re

class ProductTemplate(models.Model):
    _inherit = "product.template"

    fbr_image = fields.Image(
        string='FBR Product Image',
        help="Product image for FBR reporting and documentation"
    )
    
    fbr_uom_id = fields.Many2one(
        'fbr.uom',
        string='FBR UOM',
        help="Select the FBR unit of measurement for this product"
    )
    fbr_hs_code = fields.Char(
        string='HS Code',
        help="Harmonized System Code for FBR reporting"
    )

    fbr_sro_item_serial_id = fields.Many2one(
        'fbr.sro.item.serial',
        string='SRO Item Serial No.',
        help='Select the SRO Item Serial Number'
    )

    fbr_fixed_notified_value = fields.Char(
        string='Fixed/Notified Value or Retail Price',
        default='0',
        help='Fixed or notified value or retail price for FBR'
    )

    fbr_sales_tax_withheld = fields.Char(
        string='Sales Tax Withheld at Source',
        default='0',
        help='Sales tax withheld at source amount'
    )

    fbr_sro_id = fields.Many2one(
        'fbr.sro',
        string='FBR SRO',
        help='Select the applicable SRO (Statutory Regulatory Order)'
    )

    fbr_extra_tax = fields.Char(
        string='Extra Tax',
        default='0.00',
        help='Extra tax amount for FBR'
    )

    fbr_further_tax = fields.Char(
        string='Further Tax',
        default='0',
        help='Further tax amount for FBR'
    )

    fbr_fed_payable = fields.Char(
        string='FED Payable',
        default='0',
        help='Federal Excise Duty payable amount'
    )





    @api.constrains('fbr_hs_code')
    def _check_fbr_hs_code(self):
        """Validate HS Code format"""
        for record in self:
            if record.fbr_hs_code:
                # Remove any spaces
                hs_code = record.fbr_hs_code.replace(' ', '')

                # Check if it matches the pattern XXXX.XXXX (8 digits with dot in middle)
                if not re.match(r'^\d{4}\.\d{4}$', hs_code):
                    raise ValidationError(
                        "HS Code must be in format XXXX.XXXX (e.g., 0101.2100). "
                        "It should contain exactly 8 digits with a dot after the first 4 digits."
                    )

    @api.onchange('fbr_hs_code')
    def _onchange_fbr_hs_code(self):
        """Auto-format HS Code on change"""
        if self.fbr_hs_code:
            # Remove any non-digit characters except dots
            cleaned = re.sub(r'[^\d.]', '', self.fbr_hs_code)

            # If it's just digits, auto-format with dot
            if cleaned.isdigit() and len(cleaned) == 8:
                self.fbr_hs_code = f"{cleaned[:4]}.{cleaned[4:]}"
            elif cleaned.isdigit() and len(cleaned) > 8:
                # Truncate to 8 digits and format
                self.fbr_hs_code = f"{cleaned[:4]}.{cleaned[4:8]}"
            elif '.' in cleaned:
                # Validate existing format
                parts = cleaned.split('.')
                if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                    if len(parts[0]) <= 4 and len(parts[1]) <= 4:
                        self.fbr_hs_code = f"{parts[0].zfill(4)}.{parts[1].zfill(4)}"