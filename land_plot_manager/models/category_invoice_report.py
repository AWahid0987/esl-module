# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from collections import defaultdict


class CategoryInvoiceReport(models.TransientModel):
    _name = 'category.invoice.report'
    _description = 'Category Wise Invoice Report'

    @api.model
    def _get_category_data(self, invoices):
        """
        Group invoices by product category and calculate totals.
        Returns a dictionary with category as key and totals as values.
        """
        category_data = defaultdict(lambda: {
            'count': 0,
            'total_amount': 0.0,
            'paid_amount': 0.0,
            'remaining_amount': 0.0,
            'invoices': []
        })

        for invoice in invoices:
            # Get category from invoice lines
            category = None
            for line in invoice.invoice_line_ids:
                if line.product_id and line.product_id.categ_id:
                    category = line.product_id.categ_id.name
                    break
            
            # Fallback: try to get from sale order
            if not category and invoice.sale_id:
                for line in invoice.sale_id.order_line:
                    if line.product_id and line.product_id.categ_id:
                        category = line.product_id.categ_id.name
                        break

            # Use 'Other' if no category found
            if not category:
                category = 'Other'

            category_data[category]['count'] += 1
            category_data[category]['total_amount'] += invoice.amount_total or 0.0
            category_data[category]['paid_amount'] += invoice.paid_amount or 0.0
            category_data[category]['remaining_amount'] += invoice.remaining_amount or 0.0
            category_data[category]['invoices'].append(invoice)

        # Convert defaultdict to regular dict and sort invoices by date
        result = {}
        for cat, data in category_data.items():
            # Sort invoices by date (newest first)
            data['invoices'] = sorted(data['invoices'], key=lambda inv: inv.invoice_date or fields.Date.today(), reverse=True)
            result[cat] = data
        
        # Sort categories alphabetically
        return dict(sorted(result.items()))

    @api.model
    def get_report_data(self, domain=None):
        """
        Get invoice data grouped by category.
        domain: optional domain to filter invoices
        """
        if domain is None:
            domain = [
                ('move_type', '=', 'out_invoice'),
                ('state', 'in', ['draft', 'posted'])
            ]

        invoices = self.env['account.move'].search(domain)
        return self._get_category_data(invoices)


class AccountMove(models.Model):
    _inherit = 'account.move'

    def get_category_wise_report_data(self):
        """
        Get category-wise data for this invoice (or all invoices if called from report action).
        """
        self.ensure_one()
        report_model = self.env['category.invoice.report']
        
        # Get all invoices for the report
        invoices = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('state', 'in', ['draft', 'posted'])
        ])
        
        return report_model._get_category_data(invoices)

    def get_payment_plan_data(self):
        """
        Get payment plan data based on sale order from this invoice.
        Returns payment plan information for the specific sale order's product category.
        """
        self.ensure_one()
        
        # Get sale order from invoice
        sale_order = self.sale_id
        
        # If no sale_id, try to get from invoice lines
        if not sale_order:
            for line in self.invoice_line_ids:
                if line.sale_line_ids:
                    sale_order = line.sale_line_ids[0].order_id
                    break
        
        if not sale_order:
            return {}
        
        # Get product category from sale order
        category_name = None
        for line in sale_order.order_line:
            if line.product_id and line.product_id.categ_id:
                category_name = line.product_id.categ_id.name
                break
        
        if not category_name:
            return {}
        
        # Get payment map
        payment_map = self.env['sale.advance.payment.inv'].CATEGORY_PAYMENT_MAP
        category_data = payment_map.get(category_name, {})
        
        if not category_data:
            return {}
        
        # Get all invoices for this sale order
        all_invoices = self.env['account.move'].search([
            '|',
            ('sale_id', '=', sale_order.id),
            ('invoice_origin', '=', sale_order.name),
            ('move_type', '=', 'out_invoice'),
            ('state', 'in', ['draft', 'posted'])
        ])
        
        # Calculate actual amounts from invoices
        down_payment_amount = 0.0
        confirmation_amount = 0.0
        installment_amount = 0.0
        total_amount = sale_order.amount_total or 0.0
        
        for inv in all_invoices:
            if inv.custom_method == 'down_payment':
                down_payment_amount += inv.amount_total or 0.0
            elif inv.custom_method == 'confirmation':
                confirmation_amount += inv.amount_total or 0.0
            elif inv.custom_method == 'installment':
                installment_amount += inv.amount_total or 0.0
        
        # Get payment plan template from category
        down_payment_template = category_data.get('down_payment', 0)
        confirmation_template = category_data.get('confirmation', 0)
        monthly_template = category_data.get('installment_monthly', 0)
        tenure_months = 60
        
        # Use actual amounts if available, otherwise use template
        down_payment = down_payment_amount if down_payment_amount > 0 else down_payment_template
        confirmation = confirmation_amount if confirmation_amount > 0 else confirmation_template
        
        # Calculate monthly installment from actual or template
        if installment_amount > 0:
            # Count installment invoices to calculate monthly
            installment_invoices = all_invoices.filtered(lambda inv: inv.custom_method == 'installment')
            if installment_invoices:
                monthly_installment = installment_amount / len(installment_invoices) if len(installment_invoices) > 0 else monthly_template
            else:
                monthly_installment = monthly_template
        else:
            monthly_installment = monthly_template
        
        # Calculate totals
        if total_amount > 0:
            # Use actual sale order total
            balance = total_amount - down_payment
            final_total = total_amount
        else:
            # Calculate from template
            balance = confirmation + (monthly_installment * tenure_months)
            final_total = down_payment + balance
        
        return {
            category_name: {
                'total_price': final_total,
                'down_payment': down_payment,
                'balance': balance,
                'tenure': tenure_months,
                'monthly_installment': monthly_installment,
            }
        }

