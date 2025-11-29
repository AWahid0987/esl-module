# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CustomerReport(models.Model):
    _name = 'customer.report'
    _description = 'Customer Wise Invoice Report'

    name = fields.Char("Report Name", default="Customer Invoice Report")
    partner_id = fields.Many2one('res.partner', string="Customer", required=True)
    phone = fields.Char(related="partner_id.phone", string="Phone", readonly=True)
    email = fields.Char(related="partner_id.email", string="Email", readonly=True)



    # All invoices for this customer
    invoice_ids = fields.One2many(
        comodel_name='account.move',
        compute="_compute_invoices",
        string="Invoices",
        store=False
    )

    @api.depends('partner_id')
    def _compute_invoices(self):
        for rec in self:
            if rec.partner_id:
                rec.invoice_ids = self.env['account.move'].search([
                    ('partner_id', '=', rec.partner_id.id),
                    ('move_type', '=', 'out_invoice'),
                    ('state', 'in', ['draft', 'posted'])
                ])
            else:
                rec.invoice_ids = False


class CustomerReportLine(models.Model):
    _name = 'customer.report.line'
    _description = 'Customer Report Invoice Line'

    report_id = fields.Many2one('customer.report', string="Report")
    invoice_id = fields.Many2one('account.move', string="Invoice")
    product_id = fields.Many2one('product.product', string="Product")
    quantity = fields.Float("Quantity")
    price_unit = fields.Monetary("Unit Price", currency_field="currency_id")
    price_subtotal = fields.Monetary("Subtotal", currency_field="currency_id")
    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        related="invoice_id.currency_id",
        store=True
    )


# Optional model for journey labels if not already present
class JourneyLabel(models.Model):
    _name = 'journey.label'
    _description = 'Journey Label'

    name = fields.Char("Journey Label Name", required=True)
