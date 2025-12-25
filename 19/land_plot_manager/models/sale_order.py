# -*- coding: utf-8 -*-
"""
Sale Order Extensions
Adds land plot specific fields and functionality
"""
import logging
from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError, ValidationError


_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    """
    Sale Order Model Extended
    Adds plot management and commission functionality
    """
    _inherit = 'sale.order'

    # ----------------------------------------------------------
    # Custom Fields
    # ----------------------------------------------------------
    plan_type = fields.Selection([
        ("full", "Full Payment"),
        ("installment", "Installment"),
        ("full_navy_1", "Full Payment Navy 1"),
        ("full_navy_2", "Full Payment Navy 2"),
        ("installment_navy_1", "Installment Navy 1"),
        ("installment_navy_2", "Installment Navy 2"),
    ], string="Plan Type", default="installment", required=True)
    app_no = fields.Char(string="Application No", required=True)

    allotment_no = fields.Char(string='Allotment No', readonly=True)
    any_invoice_exists = fields.Boolean(compute='_compute_any_invoice_exists', store=False)
    project_type = fields.Selection([
        ('anchorage', 'Anchorage Lahore'),
    ], string="Project", default="anchorage", required=True)

    land_project_id = fields.Selection([
        ('anchorage lahore', 'Anchorage Lahore'),
    ])
    reg_number = fields.Char(string="Registration Number", required=True)
    pal_number = fields.Char(
        string="PAL Number",
        help="PAL Number for Regular and Possession payments."
    )

    amount_total_in_words = fields.Char(
        string="Amount in Words",
        compute="_compute_amount_in_words",
        store=True,
    )

    def _default_project(self):
        return self.env['land.project'].search([('name', '=', 'Anchorage Lahore')], limit=1)

    land_project_id = fields.Many2one(
        'land.project',
        string="Project Name",
        default=_default_project,
        readonly=True
    )


    @api.depends('amount_total')
    def _compute_amount_in_words(self):
        for rec in self:
            rec.amount_total_in_words = rec.currency_id.amount_to_text(rec.amount_total)


    # ----------------------------------------------------------
    # Auto-generate Allotment Number from first product name
    # ----------------------------------------------------------
    @api.model
    def create(self, vals):
        record = super(SaleOrder, self).create(vals)
        record._generate_allotment_no()
        record._validate_plan_type_categories()
        return record

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        if 'order_line' in vals or 'name' in vals:
            for rec in self:
                rec._generate_allotment_no()
        # Validate plan_type and categories after write
        if 'plan_type' in vals or 'order_line' in vals:
            for rec in self:
                rec._validate_plan_type_categories()
        return res

    def _validate_plan_type_categories(self):
        """
        Validate that Navy plan types only allow Residential 5 Marla and Residential 10 Marla categories.
        Standard plans (full, installment) allow all 4 categories.
        """
        navy_plan_types = ['full_navy_1', 'full_navy_2', 'installment_navy_1', 'installment_navy_2']
        allowed_navy_categories = ['Residential 5 Marla', 'Residential 10 Marla']
        
        for order in self:
            if not order.plan_type:
                continue
                
            # If plan_type is Navy type, validate categories
            if order.plan_type in navy_plan_types:
                if not order.order_line:
                    continue
                    
                invalid_products = []
                for line in order.order_line:
                    if not line.product_id:
                        continue
                        
                    product_category = line.product_id.categ_id.name if line.product_id.categ_id else None
                    
                    if not product_category:
                        invalid_products.append({
                            'product': line.product_id.display_name or 'Unknown',
                            'category': 'No Category'
                        })
                    elif product_category not in allowed_navy_categories:
                        invalid_products.append({
                            'product': line.product_id.display_name or 'Unknown',
                            'category': product_category
                        })
                
                if invalid_products:
                    error_msg = _(
                        "For plan type '%s', only products with categories 'Residential 5 Marla' or 'Residential 10 Marla' are allowed.\n\n"
                        "Invalid products found:\n"
                    ) % order.plan_type
                    
                    for item in invalid_products:
                        error_msg += _("- Product: %s (Category: %s)\n") % (item['product'], item['category'])
                    
                    error_msg += _("\nPlease remove these products or change the plan type.")
                    raise ValidationError(error_msg)

    def _generate_allotment_no(self):
        """
        Generate allotment number based on product name
        Format: PRODUCT-NAME-### (e.g., RES-10_001-001)
        """
        for order in self:
            if order.order_line:
                product_name = order.order_line[0].product_id.name or "SO"
                # Count how many allotments exist with same product prefix
                existing_count = self.search_count([
                    ('allotment_no', 'like', f"{product_name}-%")
                ])
                order.allotment_no = f"{product_name}-{str(existing_count + 1).zfill(3)}"

    @api.onchange('plan_type', 'order_line')
    def _onchange_plan_type_validate_categories(self):
        """Validate categories when plan_type or order_line changes"""
        if self.plan_type and self.order_line:
            try:
                self._validate_plan_type_categories()
            except ValidationError as e:
                return {
                    'warning': {
                        'title': _('Invalid Product Category'),
                        'message': str(e)
                    }
                }

    # ----------------------------------------------------------
    # Invoice Helpers
    # ----------------------------------------------------------
    @api.depends('state')
    def _compute_any_invoice_exists(self):
        Move = self.env['account.move']
        for so in self:
            so.any_invoice_exists = bool(Move.search_count(so._invoice_domain_all_for_self()))

    def _invoice_domain_all_for_self(self):
        """
        Show ALL invoices tied to the SO:
        - via direct link: sale_id = SO
        - via invoice line links: invoice_line_ids.sale_line_ids.order_id = SO
        - via origin name: invoice_origin = SO.name
        Include drafts & posted, invoices & credit notes.
        """
        self.ensure_one()
        return [
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', 'in', ['draft', 'posted']),
            '|', '|',
            ('sale_id', '=', self.id),
            ('invoice_line_ids.sale_line_ids.order_id', '=', self.id),
            ('invoice_origin', '=', self.name),
        ]

    def _get_invoiced(self):
        super()._get_invoiced()
        Move = self.env['account.move']
        for so in self:
            so.invoice_count = Move.search_count(so._invoice_domain_all_for_self())

    # ----------------------------------------------------------
    # Helper functions for actions
    # ----------------------------------------------------------
    def _normalize_action_to_dict(self, action):
        if isinstance(action, dict):
            return action
        if getattr(action, 'read', None):
            return action.read()[0]
        return {}

    def _safe_ctx(self, ctx):
        if not ctx:
            return {}
        if isinstance(ctx, dict):
            return dict(ctx)
        if isinstance(ctx, str):
            try:
                val = safe_eval(ctx, {})
                return val if isinstance(val, dict) else {}
            except Exception:
                return {}
        return {}

    # ----------------------------------------------------------
    # Invoices view action
    # ----------------------------------------------------------
    def action_view_invoice(self, invoices=None):
        self.ensure_one()
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        action = self._normalize_action_to_dict(action)
        action['domain'] = self._invoice_domain_all_for_self()

        base_ctx = self._safe_ctx(action.get('context'))
        base_ctx.update({
            'default_move_type': 'out_invoice',
            'search_disable_custom_filters': True,
        })
        action['context'] = base_ctx

        try:
            count = self.env['account.move'].search_count(self._invoice_domain_all_for_self())
            action['name'] = _("Invoices (%s)") % count
        except Exception:
            action['name'] = _("Invoices")

        return action

    # ----------------------------------------------------------
    # Report Actions
    # ----------------------------------------------------------
    def action_print_sale(self):
        """Print the Allotment / Sale report as PDF."""
        report = self.env.ref('land_plot_manager.action_report_sale', raise_if_not_found=False)
        return report.report_action(self)

    def action_print_sale_user(self):
        """Print Sale Report (User Version)."""
        report = self.env.ref('land_plot_manager.action_report_sale_user', raise_if_not_found=False)
        return report.report_action(self)

    def challan_report_action(self):
        """Print Challan 3-Copy Report"""
        self.ensure_one()
        report = self.env.ref('land_plot_manager.challan_report_action')
        return report.report_action(self)

    def action_print_installment_letter(self):
        """Print the Installment Letter report as PDF."""
        self.ensure_one()
        report = self.env.ref('land_plot_manager.action_report_installment_letter', raise_if_not_found=False)
        if not report:
            raise UserError(_("Installment letter report not found. Please reinstall the module."))

        AccountMove = self.env['account.move']
        invoices = AccountMove.search([
            '|', '|',
            ('invoice_origin', '=', self.name),
            ('invoice_line_ids.sale_line_ids.order_id', '=', self.id),
            ('partner_id', '=', self.partner_id.id),
            ('move_type', '=', 'out_invoice')
        ])

        ctx = dict(self.env.context, inv_item=invoices)
        return report.report_action(self.with_context(ctx))

    def action_print_payment_acknowledgement(self):
        """Print appropriate payment acknowledgement based on plan_type."""
        self.ensure_one()
        plan = (self.plan_type or '').strip().lower()

        if plan in ['full', 'full_payment']:
            report = self.env.ref('land_plot_manager.action_full_payment_acknowledgement')
        else:
            report = self.env.ref('land_plot_manager.action_installment_acknowledgement')

        return report.report_action(self)

    def action_print_final_file(self):
        """Print Confirmation Letter — with validation check for required fields."""
        required_fields = {
            "partner_id": "Customer",
            "date_order": "Order Date",
            "allotment_no": "Allotment No",
            "order_line": "Order Lines",
            "land_project_id": "Project Name",
        }

        for order in self:
            missing = []

            # Validate required fields
            for field, label in required_fields.items():
                value = getattr(order, field)
                if not value:
                    missing.append(label)

            # Check if order lines have valid products
            if not order.order_line or any(not line.product_id for line in order.order_line):
                missing.append("Product in Order Lines")

            # If any missing fields, raise a user-friendly error
            if missing:
                raise UserError(
                    _("Missing required fields before printing:\n\n%s") %
                    "\n".join(f"- {field}" for field in missing)
                )

        # Print the report if everything is OK
        report = self.env.ref('land_plot_manager.action_report_final_file', raise_if_not_found=False)
        return report.report_action(self)

    def action_confirm(self):
        """Override to send email when sale order is confirmed."""
        result = super(SaleOrder, self).action_confirm()
        
        # Send confirmation email to customer
        for order in self:
            if order.partner_id and order.partner_id.email:
                try:
                    template = self.env.ref('land_plot_manager.email_template_sale_order_confirmed', raise_if_not_found=False)
                    if template:
                        mail_id = template.send_mail(order.id, force_send=True)
                        if mail_id:
                            order.message_post(
                                body=_("Confirmation email sent to %s - Your request has been approved") % order.partner_id.email,
                                subject=_("Sale Order Confirmed")
                            )
                        _logger.info(f"Confirmation email sent to {order.partner_id.email} for sale order {order.name}")
                except Exception as e:
                    _logger.error(f"Error sending confirmation email: {str(e)}")
        
        return result

    def action_create_commission(self):
        """
        Create commission record for sale order.

        Requires at least two posted customer invoices linked to the sale (invoice_origin = sale.name).
        Raises a UserError with details if not satisfied.
        """
        Commission = self.env['land.plot.commission']

        for order in self:
            invoices = self.env['account.move'].search([('invoice_origin', '=', order.name)])
            posted = invoices.filtered(lambda m: m.state == 'posted' and m.move_type == 'out_invoice')

            # If we don't have 2 posted customer invoices, raise a detailed error
            if len(posted) < 2:
                if not invoices:
                    raise UserError(_(
                        "Commission cannot be created because there are no invoices linked to this sale (origin: %s).\n"
                        "Please create and validate the downpayment and confirmation invoices first."
                    ) % order.name)

                msgs = [_("Found %d invoice(s) linked to this sale.\n") % len(invoices)]
                for inv in invoices:
                    msgs.append(_("- %s : state = %s, amount = %s\n") %
                                (inv.name or _('(no name)'), inv.state, inv.amount_total))

                msgs.append(_(
                    "\nYou need at least two posted customer invoices (downpayment + confirmation).\n"
                    "Please post the following draft invoices first."
                ))
                raise UserError(''.join(msgs))

            # Avoid duplicate commission records for this origin
            existing = Commission.search([('origin', '=', order.name)], limit=1)
            if existing:
                # open existing record
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'land.plot.commission',
                    'res_id': existing.id,
                    'view_mode': 'form',
                    'target': 'current',
                }

            # Map product category name to commission_category code
            category_map = {
                'Residential 5 Marla': 'r5',
                'Residential 10 Marla': 'r10',
                'Commercial 4 Marla': 'c4',
                'Commercial 8 Marla': 'c8',
            }

            commission_category = 'r5'  # default
            for line in order.order_line:
                cat = line.product_id.categ_id.name if line.product_id and line.product_id.categ_id else False
                if cat and cat in category_map:
                    commission_category = category_map[cat]
                    break

            vals = {
                'name': order.name,
                'origin': order.name,
                'commission_category': commission_category,
                'sale_price': order.amount_total,
                'commission_partner_id': order.partner_id.id,
                'currency_id': (order.pricelist_id.currency_id.id
                                if order.pricelist_id
                                else (order.company_id.currency_id.id
                                      if order.company_id
                                      else self.env.company.currency_id.id)),
            }

            commission = Commission.create(vals)
            order.message_post(body=_("Commission %s created.") % commission.name)

            return {
                'type': 'ir.actions.act_window',
                'res_model': 'land.plot.commission',
                'res_id': commission.id,
                'view_mode': 'form',
                'target': 'current',
            }

        return True

    class AccountMove(models.Model):
        _inherit = 'account.move'

        pal_number = fields.Char(
            string="PAL Number",
            help="PAL Number passed from sale order or payment wizard."
        )

        @api.model
        def create(self, vals):
            """Auto-fill PAL number and plan_type on invoice from sale order"""
            move = super().create(vals)

            if move.sale_id:
                if move.pal_number:
                    # Store PAL number on Sale Order (if not already saved)
                    move.sale_id.pal_number = move.pal_number
                # Copy plan_type from sale order if not already set
                if not move.plan_type and move.sale_id.plan_type:
                    move.plan_type = move.sale_id.plan_type

            return move

    class SaleAdvancePaymentInv(models.TransientModel):
        _inherit = 'sale.advance.payment.inv'

        pal_number = fields.Char(string="PAL Number")

        def create_invoices(self):
            """Override to save PAL number into Sale Order."""
            res = super().create_invoices()

            orders = self.env['sale.order'].browse(self._context.get('active_ids', []))

            for order in orders:
                # Save PAL only for regular + possession
                if self.custom_method in ['regular', 'possession'] and self.pal_number:
                    order.pal_number = self.pal_number

            return res

