# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta

import logging
_logger = logging.getLogger(__name__)


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    # -----------------------------
    # Payment Plan Definition
    # -----------------------------
    PAYMENT_PLAN = {
        'booking_fee': {
            'label': 'Booking Fee',
            'percent': 20.0,
            'date_type': 'booking',  # order date / today
            'fixed_date': None,
        },
        'construction_y1': {
            'label': 'Construction - 1st Year',
            'percent': 10.0,
            'date_type': 'fixed',
            'fixed_date': None,
        },
        'construction_y2': {
            'label': 'Construction - 2nd Year',
            'percent': 10.0,
            'date_type': 'fixed',
            'fixed_date': None,
        },
        'handover': {
            'label': 'On Handover',
            'percent': 20.0,
            'date_type': 'fixed',
            'fixed_date': None,
        },
        'post_1': {
            'label': 'Post Handover - 1st Installment',
            'percent': 5.0,
            'date_type': 'fixed',
            'fixed_date': None,
        },
        'post_2': {
            'label': 'Post Handover - 2nd Installment',
            'percent': 5.0,
            'date_type': 'fixed',
            'fixed_date': None,
        },
        'post_3': {
            'label': 'Post Handover - 3rd Installment',
            'percent': 5.0,
            'date_type': 'fixed',
            'fixed_date': None,
        },
        'post_4': {
            'label': 'Post Handover - 4th Installment',
            'percent': 5.0,
            'date_type': 'fixed',
            'fixed_date': None,
        },
        'post_5': {
            'label': 'Post Handover - 5th Installment',
            'percent': 5.0,
            'date_type': 'fixed',
            'fixed_date': None,
        },
        'post_6': {
            'label': 'Post Handover - 6th Installment',
            'percent': 5.0,
            'date_type': 'fixed',
            'fixed_date': None,
        },
        'post_7': {
            'label': 'Post Handover - 7th Installment',
            'percent': 5.0,
            'date_type': 'fixed',
            'fixed_date': None,
        },
        'final': {
            'label': 'Final Installment',
            'percent': 5.0,
            'date_type': 'fixed',
            'fixed_date': None,
        },
    }

    # -----------------------------
    # Wizard Fields
    # -----------------------------
    payment_plan_stage = fields.Selection(
        selection=[
            ('all', 'All (Full Payment Plan)'),
            ('regular', 'Regular Invoice (100%)'),   # ✅ NEW OPTION
            ('booking_fee', 'Booking Fee (20%)'),
            ('construction_y1', 'Construction - 1st Year (10%)'),
            ('construction_y2', 'Construction - 2nd Year (10%)'),
            ('handover', 'On Handover (20%)'),
            ('post_1', 'Post Handover - 1st Installment (5%)'),
            ('post_2', 'Post Handover - 2nd Installment (5%)'),
            ('post_3', 'Post Handover - 3rd Installment (5%)'),
            ('post_4', 'Post Handover - 4th Installment (5%)'),
            ('post_5', 'Post Handover - 5th Installment (5%)'),
            ('post_6', 'Post Handover - 6th Installment (5%)'),
            ('post_7', 'Post Handover - 7th Installment (5%)'),
            ('final', 'Final Installment (5%)'),
        ],
        string="Payment Plan Stage",
        required=True,
        default='all',
        help=(
            "Select 'All' to create the full 12-invoice payment plan, "
            "'Regular' for a standard Odoo invoice (100% of the sale order), "
            "or a specific stage to create a single installment invoice."
        ),
    )

    percentage = fields.Float(
        string='Percentage',
        digits=(5, 2),
        compute='_compute_percentage',
        store=False,
    )

    installment_amount = fields.Monetary(
        string='Installment Amount',
        currency_field='currency_id',
        compute='_compute_installment_amount',
        store=False,
    )

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
        readonly=True,
    )

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        readonly=True,
    )

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

    # -----------------------------
    # Default Get
    # -----------------------------
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self._context.get('active_ids') or []
        if active_ids:
            order = self.env['sale.order'].browse(active_ids[0])
            res['sale_order_id'] = order.id
        return res

    # -----------------------------
    # Computes
    # -----------------------------
    @api.depends('payment_plan_stage')
    def _compute_percentage(self):
        for wizard in self:
            if wizard.payment_plan_stage == 'all':
                # Sum of all plan stages (100%)
                wizard.percentage = sum(p['percent'] for p in wizard.PAYMENT_PLAN.values())
            elif wizard.payment_plan_stage == 'regular':
                # Regular invoice = full 100% of sale order
                wizard.percentage = 100.0
            else:
                plan = wizard.PAYMENT_PLAN.get(wizard.payment_plan_stage or '')
                wizard.percentage = plan['percent'] if plan else 0.0

    @api.depends('sale_order_id', 'percentage')
    def _compute_installment_amount(self):
        for wizard in self:
            if wizard.sale_order_id and wizard.percentage:
                wizard.installment_amount = (
                    wizard.sale_order_id.amount_total * wizard.percentage
                ) / 100.0
            else:
                wizard.installment_amount = 0.0

    @api.depends('sale_order_id')
    def _compute_invoice_summary(self):
        for wizard in self:
            if wizard.sale_order_id:
                invoices = self.env['account.move'].sudo().search([
                    ('sale_id', '=', wizard.sale_order_id.id),
                    ('move_type', '=', 'out_invoice'),
                    ('state', '!=', 'cancel'),
                ])
                total_invoiced = sum(invoices.mapped('amount_total'))
                remaining = max(wizard.sale_order_id.amount_total - total_invoiced, 0.0)
                wizard.already_invoiced_amount = total_invoiced
                wizard.remaining_amount = remaining
            else:
                wizard.already_invoiced_amount = 0.0
                wizard.remaining_amount = 0.0

    # -----------------------------
    # Main Create Invoice Logic
    # -----------------------------
    def create_invoices(self):
        """
        Behaviour:

        - If payment_plan_stage == 'regular':
            -> Use standard Odoo logic (super) to create a regular invoice
               (normal behaviour, usually 100% invoice according to wizard settings).

        - If payment_plan_stage == 'all':
            -> Create full 12-invoice payment plan (custom logic).

        - Else (any specific stage selected):
            -> Sirf WOH selected stage ki invoice create hogi
               (agar pehle se nahi bani hui ho).
        """
        self.ensure_one()

        # ✅ REGULAR INVOICE (Odoo default)
        if self.payment_plan_stage == 'regular':
            # Odoo ka apna create_invoices chalega
            # (advance_payment_method, etc. jaisa bhi wizard pe set hoga)
            return super(SaleAdvancePaymentInv, self).create_invoices()

        # ⬇️ Neeche se tumhara existing payment-plan custom logic as-is

        orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        invoices = self.env['account.move']

        if not orders:
            raise UserError(_("No Sale Order found for this wizard."))

        for order in orders:
            # Make sure SO is confirmed
            if order.state not in ['sale', 'done']:
                order.action_confirm()

            # NOTE: amount_total = total with taxes
            so_total = order.amount_total

            # All existing invoices for this SO
            existing_invoices = self.env['account.move'].search([
                ('sale_id', '=', order.id),
                ('move_type', '=', 'out_invoice'),
                ('state', '!=', 'cancel'),
            ])
            already_invoiced = sum(existing_invoices.mapped('amount_total'))

            # Only those invoices which are part of payment plan (have payment_plan_stage)
            existing_plan_invoices = existing_invoices.filtered(
                lambda inv: inv.payment_plan_stage in self.PAYMENT_PLAN.keys()
            )
            existing_stage_keys = set(existing_plan_invoices.mapped('payment_plan_stage') or [])

            # Base SO line used for invoices
            so_line = order.order_line.filtered(lambda l: not l.display_type)[:1]
            if not so_line:
                raise UserError(_("Please add at least one order line before creating a payment plan invoice."))

            product = so_line.product_id
            income_account = product.property_account_income_id or product.categ_id.property_account_income_categ_id
            if not income_account:
                raise UserError(_('Please configure an income account for %s or its category.') % product.display_name)

            # ---------------------------
            # Decide which stages to create
            # ---------------------------
            if self.payment_plan_stage == 'all':
                # If ANY plan-stage invoice already exists, block
                if existing_stage_keys:
                    dup_info = []
                    for inv in existing_plan_invoices:
                        dup_info.append(
                            "%s (%s)" % (inv.display_name or _('(no number yet)'), inv.payment_plan_stage)
                        )
                    raise UserError(_(
                        "Some payment plan invoices already exist for this Sales Order:\n%s\n"
                        "You cannot create the full plan again."
                    ) % "\n".join(dup_info))

                # "All" = create full 12 stages
                stages_to_create = list(self.PAYMENT_PLAN.items())

                # Pre-check total amount of all stages
                additional_total = sum(
                    (so_total * plan['percent']) / 100.0
                    for _key, plan in stages_to_create
                )

                if (already_invoiced + additional_total) - so_total > 0.01:
                    raise UserError(_(
                        "You cannot invoice more than 100%% of the Sale Order amount.\n"
                        "Order Total: %(total).2f\n"
                        "Already Invoiced: %(inv).2f\n"
                        "All Remaining Installments: %(inst).2f"
                    ) % {
                        'total': so_total,
                        'inv': already_invoiced,
                        'inst': additional_total,
                    })

            else:
                # ---------- INDIVIDUAL STAGE BEHAVIOUR ----------
                if self.payment_plan_stage not in self.PAYMENT_PLAN:
                    raise UserError(_("Invalid payment plan stage."))

                # Check if this selected stage already has an invoice
                existing_stage_invoices = existing_invoices.filtered(
                    lambda inv: inv.payment_plan_stage == self.payment_plan_stage
                )
                if existing_stage_invoices:
                    safe_names = [inv.display_name or _('(no number yet)') for inv in existing_stage_invoices]
                    msg = _("Invoice for stage '%(stage)s' is already created:\n%(invoices)s") % {
                        'stage': self.PAYMENT_PLAN[self.payment_plan_stage]['label'],
                        'invoices': ", ".join(safe_names),
                    }
                    raise UserError(msg)

                # Sirf selected stage create hogi
                stages_to_create = [(self.payment_plan_stage, self.PAYMENT_PLAN[self.payment_plan_stage])]

                # Pre-check: selected stage amount add karne se 100% se zyada to nahi ho raha
                additional_total = (so_total * stages_to_create[0][1]['percent']) / 100.0
                if (already_invoiced + additional_total) - so_total > 0.01:
                    raise UserError(_(
                        "You cannot invoice more than 100%% of the Sale Order amount.\n"
                        "Order Total: %(total).2f\n"
                        "Already Invoiced: %(inv).2f\n"
                        "This Installment: %(inst).2f"
                    ) % {
                        'total': so_total,
                        'inv': already_invoiced,
                        'inst': additional_total,
                    })

            # -----------------------------------------
            # Create invoices for chosen stages
            # -----------------------------------------
            for plan_key, plan in stages_to_create:
                # Amount check ke liye 20%, 10% etc of SO total
                installment_amount = (so_total * plan['percent']) / 100.0

                # 100% ceiling check per step (extra safety)
                if (already_invoiced + installment_amount) - so_total > 0.01:
                    raise UserError(_(
                        "You cannot invoice more than 100%% of the Sale Order amount.\n"
                        "Order Total: %(total).2f\n"
                        "Already Invoiced: %(inv).2f\n"
                        "This Installment (stage: %(stage)s): %(inst).2f"
                    ) % {
                        'total': so_total,
                        'inv': already_invoiced,
                        'stage': plan['label'],
                        'inst': installment_amount,
                    })

                # ✅ IMPORTANT:
                # Quantity ko percent ke mutabiq rakhte hain
                # Taake SO invoiced_qty < ordered_qty rahe, button hide na ho
                installment_qty = (so_line.product_uom_qty * plan['percent']) / 100.0

                # Invoice Date According to Plan
                if plan['date_type'] == 'booking':
                    invoice_date = fields.Date.to_date(order.date_order) or fields.Date.context_today(self)
                elif plan['date_type'] == 'fixed' and plan.get('fixed_date'):
                    invoice_date = plan.get('fixed_date')
                else:
                    invoice_date = fields.Date.context_today(self)

                due_date = invoice_date + relativedelta(days=30)

                invoice_vals = {
                    'move_type': 'out_invoice',
                    'partner_id': order.partner_invoice_id.id,
                    'invoice_origin': order.name,
                    'invoice_user_id': self.env.uid,
                    'currency_id': order.currency_id.id,
                    'sale_id': order.id,
                    'invoice_date': invoice_date,
                    'invoice_date_due': due_date,
                    'payment_plan_stage': plan_key,
                    'payment_plan_percentage': plan['percent'],
                    'invoice_line_ids': [(0, 0, {
                        'name': plan['label'],
                        'quantity': installment_qty,          # <-- percent qty
                        'price_unit': so_line.price_unit,     # <-- original unit price
                        'product_id': product.id,
                        'account_id': income_account.id,
                        'sale_line_ids': [(4, so_line.id)],
                    })],
                }

                invoice = self.env['account.move'].create(invoice_vals)

                if hasattr(invoice, '_compute_payment_amounts'):
                    invoice._compute_payment_amounts()

                invoices |= invoice
                already_invoiced += installment_amount

                order.message_post(body=_(
                    "Payment plan invoice created in DRAFT for stage '%(stage)s' "
                    "(%(percent)s%% of %(total).2f = %(amount).2f)."
                ) % {
                    'stage': plan['label'],
                    'percent': plan['percent'],
                    'total': so_total,
                    'amount': installment_amount,
                })

        action = self.env.ref('account.action_move_out_invoice_type').sudo().read()[0]
        action['domain'] = [('id', 'in', invoices.ids)]
        return action
