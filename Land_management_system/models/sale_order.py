# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools import date_utils
from datetime import datetime, date
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_statement_date(self):
        """Get statement date in DD-MM-YYYY format"""
        return fields.Date.today().strftime('%d-%m-%Y')

    def _get_numbered_order_lines(self):
        """Get order lines with serial numbers for reports"""
        numbered_lines = []
        for index, line in enumerate(self.order_line, start=1):
            numbered_lines.append({
                'sr_no': index,
                'line': line
            })
        return numbered_lines

    def _get_amount_in_words(self, amount, currency_name='AED'):
        """Convert amount to words"""
        try:
            from num2words import num2words
            amount_words = num2words(int(amount), lang='en').title()
            return f"{amount_words} {currency_name} Only"
        except ImportError:
            return f"{amount:,.2f} {currency_name} Only"

    def _get_latest_invoice_number(self):
        """Get the latest invoice number related to this sale order"""
        invoices = self.env['account.move'].search([
            ('sale_id', '=', self.id),
            ('move_type', 'in', ['out_invoice', 'out_refund'])
        ], order='create_date desc', limit=1)
        return invoices.name if invoices else ''

    def _get_latest_invoice_date(self):
        """Get the latest invoice date related to this sale order"""
        invoices = self.env['account.move'].search([
            ('sale_id', '=', self.id),
            ('move_type', 'in', ['out_invoice', 'out_refund'])
        ], order='create_date desc', limit=1)
        return invoices.invoice_date.strftime('%d-%m-%Y') if invoices and invoices.invoice_date else ''

    def _get_latest_invoice_due_date(self):
        """Get the latest invoice due date related to this sale order"""
        invoices = self.env['account.move'].search([
            ('sale_id', '=', self.id),
            ('move_type', 'in', ['out_invoice', 'out_refund'])
        ], order='create_date desc', limit=1)
        return invoices.invoice_date_due.strftime('%d-%m-%Y') if invoices and invoices.invoice_date_due else ''

    def _get_total_due_amount(self):
        """Calculate total due amount till date"""
        invoices = self.env['account.move'].search([
            ('sale_id', '=', self.id),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '!=', 'cancel')
        ])
        total_due = sum(invoices.mapped('amount_total'))
        return f"{total_due:,.2f} {self.currency_id.name}"

    def _get_total_paid_amount(self):
        """Calculate total paid amount"""
        invoices = self.env['account.move'].search([
            ('sale_id', '=', self.id),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '!=', 'cancel')
        ])
        total_paid = sum(invoices.mapped('amount_total')) - sum(invoices.mapped('amount_residual'))
        return f"{total_paid:,.2f} {self.currency_id.name}"

    def _get_balance_to_be_paid(self):
        """Calculate balance to be paid"""
        invoices = self.env['account.move'].search([
            ('sale_id', '=', self.id),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '!=', 'cancel')
        ])
        balance = sum(invoices.mapped('amount_residual'))
        return f"{balance:,.2f} {self.currency_id.name}"

    def _get_total_overdue_amount(self):
        """Calculate total overdue amount"""
        today = date.today()
        invoices = self.env['account.move'].search([
            ('sale_id', '=', self.id),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '!=', 'cancel'),
            ('invoice_date_due', '<', today)
        ])
        overdue = sum(invoices.mapped('amount_residual'))
        return f"{overdue:,.2f} {self.currency_id.name}"

    def _get_payment_plan_data(self):
        """Get payment plan data for Statement of Account"""
        payment_plan = []
        
        # Get payment plan stages from account.move
        invoices = self.env['account.move'].search([
            ('sale_id', '=', self.id),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '!=', 'cancel'),
            ('payment_plan_stage', '!=', False)
        ], order='payment_plan_stage')
        
        # Payment plan stages mapping
        stage_labels = {
            'booking_fee': 'Booking Fees',
            'construction_y1': '1st Installment',
            'construction_y2': '2nd Installment',
            'handover': 'At Completion',
            'post_1': 'Post Handover - 1st Installment',
            'post_2': 'Post Handover - 2nd Installment',
            'post_3': 'Post Handover - 3rd Installment',
            'post_4': 'Post Handover - 4th Installment',
            'post_5': 'Post Handover - 5th Installment',
            'post_6': 'Post Handover - 6th Installment',
            'post_7': 'Post Handover - 7th Installment',
            'final': 'Final Installment',
        }
        
        for invoice in invoices:
            percentage = invoice.payment_plan_percentage or 0.0
            vat_amount = invoice.amount_tax
            amount_excl_vat = invoice.amount_untaxed
            amount_incl_vat = invoice.amount_total
            paid_amount = amount_incl_vat - invoice.amount_residual
            outstanding = invoice.amount_residual
            
            payment_plan.append({
                'description': stage_labels.get(invoice.payment_plan_stage, ''),
                'percentage': f"{percentage:.2f}%",
                'due_date': invoice.invoice_date_due.strftime('%d-%m-%Y') if invoice.invoice_date_due else '',
                'installment_amount': f"{amount_incl_vat:,.2f}",
                'vat_amount': f"{vat_amount:,.2f}",
                'installment_amount_sl_vat': f"{amount_excl_vat:,.2f}",
                'payment_date': invoice.invoice_date.strftime('%d-%m-%Y') if invoice.invoice_date else '',
                'paid_amount': f"{paid_amount:,.2f}",
                'outstanding_amount': f"{outstanding:,.2f}",
                'balance_sale_price_sl_vat': f"{amount_excl_vat:,.2f}",
            })
        
        # Add totals row
        if payment_plan:
            total_percentage = sum([float(p['percentage'].replace('%', '')) for p in payment_plan])
            total_installment = sum([float(p['installment_amount'].replace(',', '')) for p in payment_plan])
            total_vat = sum([float(p['vat_amount'].replace(',', '')) for p in payment_plan])
            total_sl_vat = sum([float(p['installment_amount_sl_vat'].replace(',', '')) for p in payment_plan])
            total_paid = sum([float(p['paid_amount'].replace(',', '')) for p in payment_plan])
            total_outstanding = sum([float(p['outstanding_amount'].replace(',', '')) for p in payment_plan])
            
            payment_plan.append({
                'description': 'Total',
                'percentage': f"{total_percentage:.2f}%",
                'due_date': '',
                'installment_amount': f"{total_installment:,.2f}",
                'vat_amount': f"{total_vat:,.2f}",
                'installment_amount_sl_vat': f"{total_sl_vat:,.2f}",
                'payment_date': '',
                'paid_amount': f"{total_paid:,.2f}",
                'outstanding_amount': f"{total_outstanding:,.2f}",
                'balance_sale_price_sl_vat': f"{total_sl_vat:,.2f}",
            })
        
        return payment_plan

    def _get_additional_charges(self):
        """Get additional charges for Statement of Account"""
        charges = []
        
        # DLD Fee 4%
        dld_fee = self.amount_total * 0.04
        charges.append({
            'description': 'DLD Fee 4%',
            'due_date': '',
            'fees_amount': f"{dld_fee:,.2f}",
            'payment_date': '',
            'paid_amount': '0.00',
            'outstanding_amount': f"{dld_fee:,.2f}",
        })
        
        # Other Govt. Charges
        charges.append({
            'description': 'Other Govt. Charges',
            'due_date': '',
            'fees_amount': '0.00',
            'payment_date': '',
            'paid_amount': '0.00',
            'outstanding_amount': '0.00',
        })
        
        # Seller's Admin Charges
        charges.append({
            'description': "Seller's Admin Charges",
            'due_date': '',
            'fees_amount': '0.00',
            'payment_date': '',
            'paid_amount': '0.00',
            'outstanding_amount': '0.00',
        })
        
        # Total row
        total_fees = sum([float(c['fees_amount'].replace(',', '')) for c in charges])
        total_paid = sum([float(c['paid_amount'].replace(',', '')) for c in charges])
        total_outstanding = sum([float(c['outstanding_amount'].replace(',', '')) for c in charges])
        
        charges.append({
            'description': 'Total',
            'due_date': '',
            'fees_amount': f"{total_fees:,.2f}",
            'payment_date': '',
            'paid_amount': f"{total_paid:,.2f}",
            'outstanding_amount': f"{total_outstanding:,.2f}",
        })
        
        return charges

    def _get_receipts(self):
        """Get receipts/payments for Statement of Account"""
        receipts = []
        
        invoices = self.env['account.move'].search([
            ('sale_id', '=', self.id),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '!=', 'cancel')
        ])
        
        for invoice in invoices:
            if invoice.amount_total > invoice.amount_residual:  # Has payments
                # Get reconciled payments
                reconciled_lines = invoice.line_ids.filtered(lambda l: l.account_id.account_type == 'asset_receivable')
                for line in reconciled_lines:
                    for payment in line.matched_debit_ids.debit_move_id.move_id:
                        if payment.payment_id:
                            receipts.append({
                                'receipt_no': invoice.name,
                                'receipt_date': payment.date.strftime('%d-%m-%Y') if payment.date else invoice.invoice_date.strftime('%d-%m-%Y') if invoice.invoice_date else '',
                                'payment_type': payment.payment_id.journal_id.name or '',
                                'cheque_ref_no': payment.payment_id.ref or '',
                                'cheque_date': payment.payment_id.date.strftime('%d-%m-%Y') if payment.payment_id.date else '',
                                'status': 'Paid',
                                'amount': f"{abs(line.balance):,.2f}",
                            })
        
        # If no receipts found, add empty row
        if not receipts:
            receipts.append({
                'receipt_no': '',
                'receipt_date': '',
                'payment_type': '',
                'cheque_ref_no': '',
                'cheque_date': '',
                'status': '',
                'amount': '0.00',
            })
        
        # Total row
        if receipts:
            total_amount = sum([float(r['amount'].replace(',', '')) for r in receipts if r['receipt_no'] != 'Total'])
            receipts.append({
                'receipt_no': 'Total',
                'receipt_date': '',
                'payment_type': '',
                'cheque_ref_no': '',
                'cheque_date': '',
                'status': '',
                'amount': f"{total_amount:,.2f}",
            })
        
        return receipts

