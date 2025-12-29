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
    def _get_custom_method_selection(self):
        """
        Dynamic selection for custom_method based on plan_type.
        - Standard plans (full, installment): 6 payment methods
        - Navy plans (full_navy_1, full_navy_2, installment_navy_1, installment_navy_2): 3 payment methods
        """
        # Standard plans (full, installment) - 6 payment methods
        standard_methods = [
            ('regular', 'Cash Full Invoice'),
            ('down_payment', 'Down Payment'),
            ('confirmation', 'Confirmation'),
            ('installment', 'Installment Plan'),
            ('ballot', 'Ballot'),
            ('possession', 'Possession'),
        ]
        
        # Navy plans - only 3 payment methods
        navy_methods = [
            ('regular', 'Cash Full Invoice'),
            ('down_payment', 'Down Payment'),
            ('installment', 'Installment Plan'),
        ]
        
        # Get plan_type from record - try multiple methods
        plan_type = ''
        
        # First priority: Try to get from context (most reliable when form opens)
        try:
            env = getattr(self, 'env', None)
            if not env and hasattr(self, '__class__'):
                try:
                    env = self.env
                except:
                    pass
            
            if env:
                active_ids = env.context.get('active_ids', [])
                if active_ids:
                    order = env['sale.order'].browse(active_ids[0])
                    if order.exists():
                        plan_type = order.plan_type or ''
                        if plan_type:
                            # Found from context, use it
                            if plan_type in ['full', 'installment']:
                                return standard_methods
                            return navy_methods
        except Exception:
            pass
        
        # Second priority: Try to get from record's fields
        try:
            # Check if this is a recordset
            if hasattr(self, '__iter__') and not isinstance(self, type):
                for record in self:
                    # Try plan_type_for_selection first
                    if hasattr(record, 'plan_type_for_selection'):
                        try:
                            plan_type = record.plan_type_for_selection or ''
                            if plan_type:
                                break
                        except:
                            pass
                    # Then try sale_order_id
                    if not plan_type and hasattr(record, 'sale_order_id') and record.sale_order_id:
                        try:
                            so = record.sale_order_id
                            if hasattr(so, 'plan_type'):
                                plan_type = so.plan_type or ''
                                if plan_type:
                                    break
                        except:
                            pass
            # Check if this is a single record
            elif not isinstance(self, type):
                # Try plan_type_for_selection first
                if hasattr(self, 'plan_type_for_selection'):
                    try:
                        plan_type = self.plan_type_for_selection or ''
                    except:
                        pass
                # Then try sale_order_id
                if not plan_type and hasattr(self, 'sale_order_id') and self.sale_order_id:
                    try:
                        so = self.sale_order_id
                        if hasattr(so, 'plan_type'):
                            plan_type = so.plan_type or ''
                    except:
                        pass
        except Exception:
            pass
        
        # Standard plans (full, installment) - 6 payment methods
        if plan_type in ['full', 'installment']:
            return standard_methods
        
        # Navy plans or any other (or when plan_type is empty) - only 3 payment methods
        return navy_methods

    custom_method = fields.Selection(
        selection=_get_custom_method_selection,
        string='Payment Type',
        default='regular',
        required=True
    )

    custom_amount = fields.Monetary(string='Payment Amount', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, readonly=True)
    pal_number = fields.Char(string='PAL Number', help='Enter PAL Number (for Regular, Possession & All Invoice)')

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
    
    # Related field to track plan_type for selection refresh
    plan_type_for_selection = fields.Selection(
        related='sale_order_id.plan_type',
        string='Plan Type (for selection)',
        readonly=True,
        store=False
    )
    
    # -------------------------------------------------------------------------
    # Payment Mapping - Standard Plans (full, installment)
    # -------------------------------------------------------------------------
    CATEGORY_PAYMENT_MAP = {
        'Residential 5 Marla': {
            'down_payment': 490000.0,
            'confirmation': 490000.0,
            'installment_monthly': 48000.0,
            'installment_total_per_30': 48000.0 * 30,
            'all_invoice_total_per_34': 48000.0 * 34,
            'ballot': 690000.0,
            'possession': 690000.0,
        },
        'Residential 10 Marla': {
            'down_payment': 900000.0,
            'confirmation': 900000.0,
            'installment_monthly': 90000.0,
            'installment_total_per_30': 90000.0 * 30,
            'all_invoice_total_per_34': 90000.0 * 34,
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
    # Payment Mapping - Navy 1 Plans (full_navy_1, installment_navy_1)
    # -------------------------------------------------------------------------
    CATEGORY_PAYMENT_MAP_NAVY_1 = {
        'Residential 5 Marla': {
            'down_payment': 500000.0,
            'installment_monthly': 50000.0,
            'installment_total_per_60': 50000.0 * 60,
            'total_price': 3500000.0,
            'balance': 3000000.0,
        },
        'Residential 10 Marla': {
            'down_payment': 1400000.0,
            'installment_monthly': 85000.0,
            'installment_total_per_60': 85000.0 * 60,
            'total_price': 6500000.0,
            'balance': 5100000.0,
        },
    }

    # -------------------------------------------------------------------------
    # Payment Mapping - Navy 2 Plans (full_navy_2, installment_navy_2)
    # -------------------------------------------------------------------------
    CATEGORY_PAYMENT_MAP_NAVY_2 = {
        'Residential 5 Marla': {
            'down_payment': 500000.0,
            'installment_monthly': 48350.0,
            'installment_total_per_60': 48350.0 * 60,
            'total_price': 3400000.0,
            'balance': 2900000.0,
        },
        'Residential 10 Marla': {
            'down_payment': 1400000.0,
            'installment_monthly': 85000.0,
            'installment_total_per_60': 85000.0 * 60,
            'total_price': 6500000.0,
            'balance': 5100000.0,
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
        if not categ_name:
            return 0.0

        # Get plan_type from order
        plan_type = order.plan_type or ''
        
        # Determine which payment map to use based on plan_type
        navy_plan_types_1 = ['full_navy_1', 'installment_navy_1']
        navy_plan_types_2 = ['full_navy_2', 'installment_navy_2']
        
        # For Navy plans, validate category
        if plan_type in navy_plan_types_1 + navy_plan_types_2:
            allowed_categories = ['Residential 5 Marla', 'Residential 10 Marla']
            if categ_name not in allowed_categories:
                return 0.0
            
            # Use Navy-specific payment maps
            if plan_type in navy_plan_types_1:
                if categ_name not in self.CATEGORY_PAYMENT_MAP_NAVY_1:
                    return 0.0
                mp = self.CATEGORY_PAYMENT_MAP_NAVY_1[categ_name]
            else:  # navy_plan_types_2
                if categ_name not in self.CATEGORY_PAYMENT_MAP_NAVY_2:
                    return 0.0
                mp = self.CATEGORY_PAYMENT_MAP_NAVY_2[categ_name]
            
            # Navy plans: installment uses 60 months
            if method == 'installment':
                return mp.get('installment_total_per_60', 0.0)
            else:
                return mp.get(method, 0.0)
        
        # Standard plans - use standard payment map
        if categ_name not in self.CATEGORY_PAYMENT_MAP:
            return 0.0
        
        mp = self.CATEGORY_PAYMENT_MAP[categ_name]
        if method == 'installment':
            return mp.get('installment_total_per_30', 0.0)
        elif method == 'all_invoice':
            return mp.get('all_invoice_total_per_34', 0.0)
        else:
            return mp.get(method, 0.0)

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------
    def _get_available_payment_methods(self, plan_type=None):
        """
        Get list of available payment method codes based on plan_type.
        Returns list of method codes (e.g., ['regular', 'down_payment', 'installment'])
        """
        if not plan_type and self.sale_order_id:
            plan_type = self.sale_order_id.plan_type or ''
        
        navy_plan_types = ['full_navy_1', 'full_navy_2', 'installment_navy_1', 'installment_navy_2']
        if plan_type in navy_plan_types:
            return ['regular', 'down_payment', 'installment']
        
        # Standard plans (full, installment) - all 6 methods
        return ['regular', 'down_payment', 'confirmation', 'installment', 'ballot', 'possession']

    # -------------------------------------------------------------------------
    # Onchange
    # -------------------------------------------------------------------------
    @api.onchange('sale_order_id')
    def _onchange_sale_order_id(self):
        """
        Update payment methods and amounts when sale_order_id changes.
        Also validates and resets custom_method if it's not valid for the new plan_type.
        The selection field will automatically update based on _get_custom_method_selection.
        """
        if self.sale_order_id:
            plan_type = self.sale_order_id.plan_type or ''
            available_methods = self._get_available_payment_methods(plan_type)
            
            # Validate category for Navy plans
            navy_plan_types = ['full_navy_1', 'full_navy_2', 'installment_navy_1', 'installment_navy_2']
            if plan_type in navy_plan_types and self.sale_order_id.order_line:
                product = self.sale_order_id.order_line[0].product_id
                categ_name = product.categ_id.name if product.categ_id else None
                allowed_categories = ['Residential 5 Marla', 'Residential 10 Marla']
                
                if categ_name and categ_name not in allowed_categories:
                    return {
                        'warning': {
                            'title': _('Invalid Product Category'),
                            'message': _(
                                'For Navy plan types, only products with categories "Residential 5 Marla" '
                                'or "Residential 10 Marla" are allowed.\n'
                                'Current product category: %s'
                            ) % (categ_name or _('No Category'))
                        }
                    }
            
            # If current custom_method is not valid for the new plan_type, reset it
            if self.custom_method and self.custom_method not in available_methods:
                # Set to first available method (usually 'regular')
                self.custom_method = available_methods[0] if available_methods else 'regular'
            
            # Update amount based on current method
            if self.custom_method:
                self.custom_amount = self._get_default_amount(self.sale_order_id, self.custom_method)

    @api.onchange('sale_order_id', 'custom_method')
    def _onchange_sale_order_or_method(self):
        if self.sale_order_id:
            self.custom_amount = self._get_default_amount(self.sale_order_id, self.custom_method)

        # PAL clears except regular + possession + all_invoice + Navy installment
        plan_type = self.sale_order_id.plan_type if self.sale_order_id else ''
        navy_plan_types = ['full_navy_1', 'full_navy_2', 'installment_navy_1', 'installment_navy_2']
        is_navy_installment = (plan_type in navy_plan_types and self.custom_method == 'installment')
        
        if self.custom_method not in ['regular', 'possession', 'all_invoice'] and not is_navy_installment:
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
                    ('state', '=', 'post'),
                ])
                total_invoiced = sum(invoices.mapped('amount_total'))
                remaining = max(wizard.sale_order_id.amount_total - total_invoiced, 0.0)
                wizard.already_invoiced_amount = total_invoiced
                wizard.remaining_amount = remaining
            else:
                wizard.already_invoiced_amount = 0.0
                wizard.remaining_amount = 0.0

    # -------------------------------------------------------------------------
    # Main Create Invoice Logic (AUTO POSTING for all_invoice)
    # -------------------------------------------------------------------------
    def create_invoices(self):
        orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        invoices = self.env['account.move']

        for order in orders:
            if order.state not in ['sale', 'done']:
                order.action_confirm()

            method = self.custom_method
            
            # Validate that the selected payment method is valid for the plan_type
            plan_type = order.plan_type or ''
            available_methods = self._get_available_payment_methods(plan_type)
            
            # Validate category for Navy plans
            navy_plan_types = ['full_navy_1', 'full_navy_2', 'installment_navy_1', 'installment_navy_2']
            if plan_type in navy_plan_types and order.order_line:
                product = order.order_line[0].product_id
                categ_name = product.categ_id.name if product.categ_id else None
                allowed_categories = ['Residential 5 Marla', 'Residential 10 Marla']
                
                if not categ_name:
                    raise UserError(_(
                        'Product must have a category for Navy plan types.'
                    ))
                
                if categ_name not in allowed_categories:
                    raise UserError(_(
                        'For Navy plan types, only products with categories "Residential 5 Marla" '
                        'or "Residential 10 Marla" are allowed.\n'
                        'Current product category: %s\n'
                        'Product: %s'
                    ) % (categ_name, product.display_name))
            
            # Allow 'all_invoice' as a special programmatic method (not in selection but used internally)
            if method not in available_methods and method != 'all_invoice':
                raise UserError(_(
                    'Payment method "%s" is not available for plan type "%s".\n'
                    'Available methods: %s'
                ) % (
                    dict(self._get_custom_method_selection()).get(method, method),
                    plan_type or _('Not Set'),
                    ', '.join([dict(self._get_custom_method_selection()).get(m, m) for m in available_methods])
                ))

            # For all_invoice, always use amount from CATEGORY_PAYMENT_MAP (ignore custom_amount)
            if method == 'all_invoice':
                amount = self._get_default_amount(order, method)
                if amount <= 0:
                    raise UserError(
                        _('Could not determine amount from product category. Please ensure product has a valid category.'))
            else:
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
                'all_invoice': _('All Invoice for %s') % order.name,
            }
            label = label_map.get(method, _('Payment for %s') % order.name)

            # All Invoice Logic - Create 34 invoices and auto post one by one
            if method == 'all_invoice':
                # Validate PAL Number is required for all_invoice
                if not self.pal_number:
                    raise UserError(_('PAL Number is required for All Invoice payment type.'))

                monthly = amount / 34.0
                start_date = fields.Date.context_today(self)

                # Create and auto post each invoice one by one
                for i in range(1, 35):
                    invoice_date = fields.Date.to_date(start_date) + relativedelta(months=i - 1)
                    due_date = invoice_date + relativedelta(days=30)
                    inv_label = f"{label} ({i}/34)"

                    invoice = self._create_simple_invoice(
                        order, monthly, inv_label,
                        invoice_date=invoice_date,
                        due_date=due_date,
                        pal_number=self.pal_number
                    )
                    # Auto post invoice immediately after creation (one by one)
                    if invoice.state == 'draft':
                        invoice.action_post()
                    invoices |= invoice

            # Installment Logic - Auto post one by one
            elif method == 'installment':
                # Navy plans use 60 months, standard plans use 30 months
                navy_plan_types = ['full_navy_1', 'full_navy_2', 'installment_navy_1', 'installment_navy_2']
                if plan_type in navy_plan_types:
                    num_months = 60
                    monthly = amount / 60.0
                    # PAL Number is required for Navy installment plans
                    pal_number = self.pal_number
                    if not pal_number:
                        raise UserError(_('PAL Number is required for Navy Installment payment type.'))
                else:
                    num_months = 30
                    monthly = amount / 30.0
                    pal_number = None
                
                start_date = fields.Date.context_today(self)

                for i in range(1, num_months + 1):
                    invoice_date = fields.Date.to_date(start_date) + relativedelta(months=i - 1)
                    due_date = invoice_date + relativedelta(days=30)
                    inv_label = f"{label} ({i}/{num_months})"

                    invoice = self._create_simple_invoice(
                        order, monthly, inv_label,
                        invoice_date=invoice_date,
                        due_date=due_date,
                        pal_number=pal_number
                    )
                    # Auto post invoice immediately after creation (one by one)
                    if invoice.state == 'draft':
                        invoice.action_post()
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
                # Auto post invoice immediately after creation
                if invoice.state == 'draft':
                    invoice.action_post()
                invoices |= invoice

            # Log message
            order.message_post(body=_("Invoice(s) created in post for %s: %s") % (method, amount))

        action = self.env.ref('account.action_move_out_invoice_type').sudo().read()[0]
        action['domain'] = [('id', 'in', invoices.ids)]
        return action

    # -------------------------------------------------------------------------
    # Create Invoice Helper (ALWAYS post)
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
            'plan_type': order.plan_type,  # Link plan_type from sale order
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
        pass  # Disabled – since all invoices remain post unless manually posted.

    def _create_invoice(self, order, so_line, inv_type):
        invoice = super()._create_invoice(order, so_line, inv_type)
        invoice.custom_method = self.custom_method
        return invoice
