# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    # -------------------------------------------------------------------------
    # Custom Fields
    # -------------------------------------------------------------------------
    custom_method = fields.Selection([
        ('regular', 'Cash Full Invoice'),
        ('down_payment', 'Down Payment'),
        ('confirmation', 'Confirmation'),
        ('installment', 'Installment Plan'),
        ('ballot', 'Ballot'),
        ('possession', 'Possession'),
    ], string='Payment Type', default='regular', required=True)

    custom_amount = fields.Monetary(string='Payment Amount', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, readonly=True)
    pal_number = fields.Char(string='PAL Number', help='Enter PAL Number (for Regular & Possession)')

    already_invoiced_amount = fields.Monetary(
        string='Already Invoiced Amount',
        currency_field='currency_id',
        compute='_compute_invoice_summary',
        store=False,
    )
    remaining_amount = fields.Monetary(
        string='Remaining Amount',
        currency_field='currency_id',
        compute='_compute_invoice_summary',
        store=False,
    )

    sale_order_id = fields.Many2one('sale.order', string='Sale Order', readonly=True)

    # -------------------------------------------------------------------------
    # Payment Mapping
    # -------------------------------------------------------------------------
    CATEGORY_PAYMENT_MAP = {
        'Residential 5 Marla': {
            'down_payment': 490000.0,
            'confirmation': 490000.0,
            'installment_monthly': 48000.0,
            'installment_total_per_30': 48000.0 * 30,
            'ballot': 690000.0,
            'possession': 690000.0,
        },
        'Residential 10 Marla': {
            'down_payment': 900000.0,
            'confirmation': 900000.0,
            'installment_monthly': 90000.0,
            'installment_total_per_30': 90000.0 * 30,
            'ballot': 1300000.0,
            'possession': 1300000.0,
        },
        'Commercial 4 Marla': {
            'down_payment': 1600000.0,
            'confirmation': 1600000.0,
            'installment_monthly': 200000.0,
            'installment_total_per_30': 200000.0 * 30,
            'ballot': 2350000.0,
            'possession': 2350000.0,
        },
        'Commercial 8 Marla': {
            'down_payment': 3000000.0,
            'confirmation': 3000000.0,
            'installment_monthly': 370000.0,
            'installment_total_per_30': 370000.0 * 30,
            'ballot': 4500000.0,
            'possession': 4500000.0,
        },
    }

    # -------------------------------------------------------------------------
    # Default Get
    # -------------------------------------------------------------------------
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self._context.get('active_ids') or []
        if active_ids:
            order = self.env['sale.order'].browse(active_ids[0])
            res['sale_order_id'] = order.id
            method = res.get('custom_method', 'regular')
            res['custom_amount'] = self._get_default_amount(order, method)
        return res

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    def _get_default_amount(self, order, method):
        if not order or not order.order_line:
            return 0.0

        if method == 'regular':
            return order.amount_total

        product = order.order_line[0].product_id
        categ_name = product.categ_id.name if product.categ_id else False
        if not categ_name or categ_name not in self.CATEGORY_PAYMENT_MAP:
            return 0.0

        mp = self.CATEGORY_PAYMENT_MAP[categ_name]
        return mp.get('installment_total_per_30', 0.0) if method == 'installment' else mp.get(method, 0.0)

    # -------------------------------------------------------------------------
    # Onchange
    # -------------------------------------------------------------------------
    @api.onchange('sale_order_id', 'custom_method')
    def _onchange_sale_order_or_method(self):
        if self.sale_order_id:
            self.custom_amount = self._get_default_amount(self.sale_order_id, self.custom_method)

        # PAL clears except regular + possession
        if self.custom_method not in ['regular', 'possession']:
            self.pal_number = False

    # -------------------------------------------------------------------------
    # Compute Invoice Summary
    # -------------------------------------------------------------------------
    @api.depends('sale_order_id')
    def _compute_invoice_summary(self):
        for wizard in self:
            if wizard.sale_order_id:
                invoices = self.env['account.move'].sudo().search([
                    ('sale_id', '=', wizard.sale_order_id.id),
                    ('move_type', '=', 'out_invoice'),
                    ('state', '=', 'draft'),
                ])
                total_invoiced = sum(invoices.mapped('amount_total'))
                remaining = max(wizard.sale_order_id.amount_total - total_invoiced, 0.0)
                wizard.already_invoiced_amount = total_invoiced
                wizard.remaining_amount = remaining
            else:
                wizard.already_invoiced_amount = 0.0
                wizard.remaining_amount = 0.0

    # -------------------------------------------------------------------------
    # Main Create Invoice Logic (NO AUTO POSTING)
    # -------------------------------------------------------------------------
    def create_invoices(self):
        orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        invoices = self.env['account.move']

        for order in orders:
            if order.state not in ['sale', 'done']:
                order.action_confirm()

            method = self.custom_method
            amount = self.custom_amount or self._get_default_amount(order, method)

            if amount <= 0:
                raise UserError(_('Please enter a valid Payment Amount.'))

            label_map = {
                'regular': _('Regular Invoice for %s') % order.name,
                'down_payment': _('Down Payment for %s') % order.name,
                'confirmation': _('Confirmation Payment for %s') % order.name,
                'installment': _('Installment Payment for %s') % order.name,
                'ballot': _('Ballot Payment for %s') % order.name,
                'possession': _('Possession Payment for %s') % order.name,
            }
            label = label_map.get(method, _('Payment for %s') % order.name)

            # Installment Logic (NO POST)
            if method == 'installment':
                monthly = amount / 30.0
                start_date = fields.Date.context_today(self)

                for i in range(1, 31):
                    invoice_date = fields.Date.to_date(start_date) + relativedelta(months=i-1)
                    due_date = invoice_date + relativedelta(days=30)
                    inv_label = f"{label} ({i}/30)"

                    invoice = self._create_simple_invoice(
                        order, monthly, inv_label,
                        invoice_date=invoice_date,
                        due_date=due_date
                    )
                    invoices |= invoice

            else:
                pal = self.pal_number if method in ['regular', 'possession'] else None
                due_date = fields.Date.context_today(self) + relativedelta(days=30)

                invoice = self._create_simple_invoice(
                    order, amount, label,
                    invoice_date=fields.Date.context_today(self),
                    due_date=due_date,
                    pal_number=pal
                )
                invoices |= invoice

            # Log message
            order.message_post(body=_("Invoice(s) created in DRAFT for %s: %s") % (method, amount))

        action = self.env.ref('account.action_move_out_invoice_type').sudo().read()[0]
        action['domain'] = [('id', 'in', invoices.ids)]
        return action

    # -------------------------------------------------------------------------
    # Create Invoice Helper (ALWAYS DRAFT)
    # -------------------------------------------------------------------------
    def _create_simple_invoice(self, order, amount, label, invoice_date=None, due_date=None, pal_number=None):
        product = order.order_line[:1].product_id
        income_account = product.property_account_income_id or product.categ_id.property_account_income_categ_id
        if not income_account:
            raise UserError(_('Please configure an income account for %s or its category.') % product.display_name)

        vals = {
            'move_type': 'out_invoice',
            'partner_id': order.partner_invoice_id.id,
            'invoice_origin': order.name,
            'invoice_user_id': self.env.uid,
            'currency_id': order.currency_id.id,
            'sale_id': order.id,
            'invoice_date': invoice_date,
            'invoice_date_due': due_date,
            'custom_method': self.custom_method,
            'invoice_line_ids': [(0, 0, {
                'name': label,
                'quantity': 1,
                'price_unit': amount,
                'product_id': product.id,
                'account_id': income_account.id,
            })],
        }

        if pal_number:
            vals['pal_number'] = pal_number

        invoice = self.env['account.move'].create(vals)
        invoice._compute_payment_amounts()
        return invoice

    # -------------------------------------------------------------------------
    # Cron (OPTIONAL) – disabled because posting removed
    # -------------------------------------------------------------------------
    @api.model
    def cron_post_due_invoices(self):
        pass  # Disabled – since all invoices remain draft unless manually posted.

    def _create_invoice(self, order, so_line, inv_type):
        invoice = super()._create_invoice(order, so_line, inv_type)
        invoice.custom_method = self.custom_method
        return invoice
