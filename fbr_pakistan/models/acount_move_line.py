# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # FBR Fields related from Product
    fbr_uom_id = fields.Many2one(
        'fbr.uom',
        string='FBR UOM',
        related='product_id.fbr_uom_id',
        store=True,
        readonly=False,
        help="Select the FBR unit of measurement for this product"
    )

    fbr_hs_code = fields.Char(
        string='HS Code',
        related='product_id.fbr_hs_code',
        store=True,
        readonly=False,
        help="Harmonized System Code for FBR reporting"
    )

    fbr_sro_item_serial_id = fields.Many2one(
        'fbr.sro.item.serial',
        string='SRO Item Serial No.',
        related='product_id.fbr_sro_item_serial_id',
        store=True,
        readonly=False,
        help='Select the SRO Item Serial Number'
    )

    fbr_fixed_notified_value = fields.Char(
        string='Fixed/Notified Value or Retail Price',
        related='product_id.fbr_fixed_notified_value',
        store=True,
        readonly=False,
        help='Fixed or notified value or retail price for FBR'
    )

    fbr_sales_tax_withheld = fields.Char(
        string='Sales Tax Withheld at Source',
        related='product_id.fbr_sales_tax_withheld',
        store=True,
        readonly=False,
        help='Sales tax withheld at source amount'
    )

    fbr_sro_id = fields.Many2one(
        'fbr.sro',
        string='FBR SRO',
        related='product_id.fbr_sro_id',
        store=True,
        readonly=False,
        help='Select the applicable SRO (Statutory Regulatory Order)'
    )

    fbr_extra_tax = fields.Char(
        string='Extra Tax',
        related='product_id.fbr_extra_tax',
        store=True,
        readonly=False,
        help='Extra tax amount for FBR'
    )

    fbr_further_tax = fields.Char(
        string='Further Tax',
        related='product_id.fbr_further_tax',
        store=True,
        readonly=False,
        help='Further tax amount for FBR'
    )

    fbr_fed_payable = fields.Char(
        string='FED Payable',
        related='product_id.fbr_fed_payable',
        store=True,
        readonly=False,
        help='Federal Excise Duty payable amount'
    )

    @api.onchange('product_id')
    def _onchange_product_id_fbr_fields(self):
        """Auto-populate FBR fields when product is selected"""
        if self.product_id:
            # These will be automatically populated due to related fields
            # But we can add custom logic here if needed
            pass

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