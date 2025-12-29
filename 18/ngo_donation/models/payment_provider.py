# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    # Bank Transfer Details
    bank_name = fields.Char(string='Bank Name', help='Name of the bank')
    bank_iban = fields.Char(string='IBAN', help='International Bank Account Number')
    bank_bic = fields.Char(string='BIC/SWIFT', help='Bank Identifier Code or SWIFT code')
    bank_street = fields.Char(string='Street')
    bank_zip = fields.Char(string='Zip')
    bank_city = fields.Char(string='City')
    bank_country_id = fields.Many2one('res.country', string='Country')
    show_bank_details = fields.Boolean(string='Show Bank Details', default=False, help='Show bank details on payment page for bank transfer method')

