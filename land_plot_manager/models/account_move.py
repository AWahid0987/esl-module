# -*- coding: utf-8 -*-
from datetime import timedelta
import base64
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


# ---------------- Account Move ----------------
class AccountMove(models.Model):
    _inherit = "account.move"

    # ---------------- FIELDS ----------------
    sale_id = fields.Many2one("sale.order", string="Sale Order", index=True)
    pal_number = fields.Char(
        string="PAL Number",
        help="PAL Number for Regular and Possession payments."
    )
    journal_id = fields.Many2one(
        'account.journal',
        string="Journal",
        domain="[('type', '=', 'sale')]",
        required=True
    )
    plan_type = fields.Selection(
        [('full', 'Full Payment'), ('installment', 'Installment')],
        string="Plan Type",
        default='full',
        store=True
    )
    duration_years = fields.Selection(
        [('1', '1 Year'), ('2', '2 Years'), ('3', '3 Years')],
        string="Duration (Years)",
        store=True
    )
    fixed_monthly_total = fields.Monetary(
        string="Fixed Monthly Total",
        help="If set (>0), EVERY installment invoice total (tax-included) will be exactly this value."
    )
    installment_target_total = fields.Monetary(
        string="Installment Target Total",
        help="The grand total (tax-included) each installment must have.",
        copy=False
    )
    start_date = fields.Date(
        compute="_compute_start_date",
        store=True,
        readonly=False
    )
    next_invoice_date = fields.Date(store=True)
    monthly_amount = fields.Monetary(
        string="Monthly Installment (Est.)",
        store=True, readonly=True, currency_field='currency_id'
    )
    invoice_ids = fields.One2many(
        'account.move', 'sale_id',
        string='Invoices', readonly=True
    )
    posted_amount = fields.Monetary(
        related='sale_id.amount_untaxed',
        store=True, readonly=True
    )
    paid_amount = fields.Monetary(
        string="Paid Amount",
        compute="_compute_paid_remaining",
        store=True,
        currency_field='currency_id'
    )
    remaining_amount = fields.Monetary(
        string="Remaining Amount",
        compute="_compute_paid_remaining",
        store=True,
        currency_field='currency_id'
    )
    installment_generated = fields.Boolean(default=False, copy=False)
    installment_invoice_ids = fields.One2many(
        comodel_name='account.move',
        compute='_compute_installment_invoices',
        string='Installment Invoices',
        readonly=True
    )
    amount_total_in_words = fields.Char(
        string="Amount in Words",
        compute="_compute_amount_in_words",
        store=True,
    )

    # ---------------- Payment type ----------------
    custom_method = fields.Selection([
        ('regular', 'Cash Full Invoice'),
        ('down_payment', 'Down Payment'),
        ('confirmation', 'Confirmation'),
        ('installment', 'Installment Plan'),
        ('ballot', 'Ballot'),
        ('possession', 'Possession'),
    ], string='Payment Type', compute='_compute_custom_method',
        store=True, readonly=False)

    amount_down_payment = fields.Monetary(
        string="Down Payment Amount",
        compute='_compute_payment_amounts', store=True)
    amount_installment = fields.Monetary(
        string="Installment Amount",
        compute='_compute_payment_amounts', store=True)
    amount_confirmation = fields.Monetary(
        string="Confirmation Amount",
        compute='_compute_payment_amounts', store=True)
    amount_ballot = fields.Monetary(
        string="Ballot Amount",
        compute='_compute_payment_amounts', store=True)
    amount_possession = fields.Monetary(
        string="Possession Amount",
        compute='_compute_payment_amounts', store=True)

    # ---------------- HELPERS / COMPUTE METHODS ----------------
    @api.depends('invoice_line_ids', 'invoice_line_ids.sale_line_ids', 'sale_id')
    def _compute_custom_method(self):
        """
        Attempt to infer custom_method from the related sale.order.
        If custom_method is already set on the move, do not override.
        """
        for move in self:
            if move.custom_method:
                continue

            move.custom_method = False
            sale_order = move.sale_id or False

            # fallback: try to get sale order from invoice lines
            if not sale_order:
                for line in move.invoice_line_ids:
                    if line.sale_line_ids:
                        sale_order = line.sale_line_ids[0].order_id
                        break

            if sale_order and getattr(sale_order, 'custom_method', False):
                move.custom_method = sale_order.custom_method

    @api.depends('custom_method', 'amount_total')
    def _compute_payment_amounts(self):
        for move in self:
            move.amount_down_payment = 0.0
            move.amount_installment = 0.0
            move.amount_confirmation = 0.0
            move.amount_ballot = 0.0
            move.amount_possession = 0.0

            if move.custom_method == 'down_payment':
                move.amount_down_payment = move.amount_total or 0.0
            elif move.custom_method == 'installment':
                move.amount_installment = move.amount_total or 0.0
            elif move.custom_method == 'confirmation':
                move.amount_confirmation = move.amount_total or 0.0
            elif move.custom_method == 'ballot':
                move.amount_ballot = move.amount_total or 0.0
            elif move.custom_method == 'possession':
                move.amount_possession = move.amount_total or 0.0

    def get_payment_type_name(self):
        """Optional: human readable payment type name for reports."""
        self.ensure_one()
        if self.custom_method:
            return dict(self._fields['custom_method'].selection).get(self.custom_method)
        return False

    @api.depends('amount_total', 'currency_id')
    def _compute_amount_in_words(self):
        for rec in self:
            try:
                rec.amount_total_in_words = rec.currency_id.amount_to_text(rec.amount_total)
            except Exception:
                rec.amount_total_in_words = ""

    @api.depends('sale_id.date_order', 'invoice_date')
    def _compute_start_date(self):
        for move in self:
            sale_date = False
            if move.sale_id and move.sale_id.date_order:
                # date_order is datetime, convert to date
                sale_date = move.sale_id.date_order.date()
            move.start_date = sale_date or move.invoice_date or fields.Date.context_today(move)

    @api.depends('amount_total', 'amount_residual')
    def _compute_paid_remaining(self):
        for move in self:
            total = move.amount_total or 0.0
            residual = move.amount_residual or 0.0
            move.remaining_amount = residual
            move.paid_amount = max(total - residual, 0.0)

    def _compute_installment_invoices(self):
        for move in self:
            domain = [
                ('move_type', '=', 'out_invoice'),
                ('plan_type', '=', 'installment'),
            ]
            if move.sale_id:
                domain.append(('sale_id', '=', move.sale_id.id))
            move.installment_invoice_ids = self.env['account.move'].search(domain)

    # ---------------- HELPERS ----------------
    def _get_total_months(self):
        self.ensure_one()
        if self.plan_type != 'installment':
            return 1
        if not self.duration_years:
            raise UserError(_("Please select duration for installments."))
        months = int(self.duration_years) * 12
        if months < 12 or months > 36:
            raise UserError(_("Duration must be between 1 and 3 years (12–36 months)."))
        return months

    # ---------------- REPORT / EMAIL HELPERS ----------------
    def challan_report_action(self):
        """Normal print action if user clicks 'Print Challan' button."""
        self.ensure_one()
        report = self.env.ref('land_plot_manager.challan_report_action')
        return report.report_action(self)

    def _send_invoice_email(self):
        """Basic invoice email (without forcing challan attachment)."""
        self.ensure_one()
        if self.move_type != 'out_invoice':
            return False

        if not self.partner_id or not self.partner_id.email:
            _logger.warning(
                "Invoice %s: No email address for customer %s",
                self.name,
                self.partner_id and self.partner_id.name
            )
            return False

        try:
            template = self.env.ref(
                'land_plot_manager.email_template_invoice_created',
                raise_if_not_found=False
            )
            if template:
                mail_id = template.send_mail(self.id, force_send=True)
                if mail_id:
                    self.message_post(
                        body=_("Invoice email sent to %s") % self.partner_id.email,
                        subject=_("Invoice Email Sent")
                    )
                _logger.info(
                    "Email sent to %s for invoice %s",
                    self.partner_id.email, self.name
                )
                return True
            else:
                _logger.warning(
                    "Email template 'land_plot_manager.email_template_invoice_created' not found"
                )
        except Exception as e:
            _logger.error("Error sending invoice email for %s: %s", self.name, str(e))
        return False

    def _check_due_date_for_reminder(self):
        """Check if invoice due date is exactly 2 days away."""
        self.ensure_one()
        if not self.invoice_date_due:
            return False

        today = fields.Date.context_today(self)
        due_date = self.invoice_date_due  # already a date in account.move

        if not due_date:
            return False

        days_until_due = (due_date - today).days
        return days_until_due == 2

    @api.model
    def _cron_invoice_due_reminder(self):
        """Cron job to send reminder emails for invoices due in 2 days."""
        today = fields.Date.context_today(self)
        invoices = self.search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date_due', '!=', False),
            ('payment_state', 'in', ('not_paid', 'partial')),
        ])

        template = self.env.ref(
            'land_plot_manager.email_invoice_due_reminder',
            raise_if_not_found=False
        )
        if not template:
            _logger.error(
                "Email template 'land_plot_manager.email_invoice_due_reminder' not found"
            )
            return

        sent_count = 0
        skipped_count = 0
        no_email_count = 0
        not_due_count = 0

        for invoice in invoices:
            # Avoid duplicate reminders (already sent in last 2 days)
            two_days_ago = today - timedelta(days=2)
            recent_messages = []
            for msg in invoice.message_ids:
                if msg.subject and 'Reminder' in msg.subject and msg.date:
                    msg_date = msg.date.date() if hasattr(msg.date, 'date') else msg.date
                    if msg_date and msg_date >= two_days_ago:
                        recent_messages.append(msg)

            if recent_messages:
                skipped_count += 1
                _logger.debug(
                    "Skipping invoice %s - reminder already sent recently",
                    invoice.name
                )
                continue

            # Check if due in exactly 2 days
            if not invoice._check_due_date_for_reminder():
                not_due_count += 1
                _logger.debug(
                    "Invoice %s not due in 2 days (Due: %s, Today: %s)",
                    invoice.name, invoice.invoice_date_due, today
                )
                continue

            if invoice.partner_id and invoice.partner_id.email:
                try:
                    mail_id = template.send_mail(invoice.id, force_send=True)
                    if mail_id:
                        invoice.message_post(
                            body=_(
                                "Reminder email sent to %s - Invoice due date: %s"
                            ) % (
                                invoice.partner_id.email,
                                invoice.invoice_date_due.strftime('%Y-%m-%d')
                                if invoice.invoice_date_due else 'N/A'
                            ),
                            subject=_("Invoice Due Reminder Sent")
                        )
                    sent_count += 1
                    _logger.info(
                        "✅ Reminder email sent for invoice %s (Due: %s) to %s",
                        invoice.name, invoice.invoice_date_due,
                        invoice.partner_id.email
                    )
                except Exception as e:
                    _logger.error(
                        "❌ Error sending reminder email for %s: %s",
                        invoice.name, str(e)
                    )
            else:
                no_email_count += 1
                _logger.warning(
                    "⚠️ Invoice %s has no customer email address (Customer: %s)",
                    invoice.name,
                    invoice.partner_id.name if invoice.partner_id else 'None'
                )

        _logger.info(
            "📧 Invoice due reminder cron completed: %s sent, %s skipped (already sent), "
            "%s no email, %s not due yet",
            sent_count, skipped_count, no_email_count, not_due_count
        )

    # ---------------- POST + CHALLAN EMAIL ----------------
    def action_post(self):
        """Override to send email + challan after posting invoice."""
        res = super(AccountMove, self).action_post()
        for invoice in self:
            if invoice.move_type == 'out_invoice' and invoice.state == 'posted':
                if not invoice.partner_id or not invoice.partner_id.email:
                    _logger.warning(
                        "Invoice %s: No email address for customer %s",
                        invoice.name,
                        invoice.partner_id and invoice.partner_id.name or 'Unknown'
                    )
                    continue
                try:
                    # Main path: send invoice email with challan attached
                    ok = invoice.action_send_invoice_with_challan()
                    if ok:
                        _logger.info(
                            "Invoice email with challan sent to %s for invoice %s",
                            invoice.partner_id.email, invoice.name
                        )
                except Exception as e:
                    _logger.exception(
                        "Error sending invoice email with challan after posting: %s",
                        e
                    )
                    # Fallback: try basic email
                    try:
                        if invoice._send_invoice_email():
                            _logger.info(
                                "Fallback invoice email sent to %s for invoice %s",
                                invoice.partner_id.email, invoice.name
                            )
                    except Exception as e2:
                        _logger.exception(
                            "Error sending fallback invoice email: %s", e2
                        )
        return res

    def action_send_invoice_with_challan(self):
        """
        Generate Challan PDF via qweb report and send invoice email
        with challan attached (creating ir.attachment + linking to mail.mail).
        """
        self.ensure_one()

        template = self.env.ref(
            'land_plot_manager.email_template_invoice_created',
            raise_if_not_found=False
        )
        report = self.env.ref(
            'land_plot_manager.challan_report_action',
            raise_if_not_found=False
        )

        if not template:
            _logger.warning(
                "Template 'land_plot_manager.email_template_invoice_created' not found; "
                "sending basic email without challan."
            )
            return self._send_invoice_email()

        if not report:
            _logger.warning(
                "Report 'land_plot_manager.challan_report_action' not found; "
                "sending email without challan attachment."
            )
            return self._send_invoice_email()

        try:
            # 1) Challan PDF generate (IMPORTANT: use keyword res_ids)
            pdf_result = report._render_qweb_pdf(res_ids=self.ids)
            try:
                pdf_content, content_type = pdf_result
            except ValueError:
                pdf_content = pdf_result

            if isinstance(pdf_content, str):
                pdf_bytes = pdf_content.encode('utf-8')
            else:
                pdf_bytes = pdf_content

            pdf_base64 = base64.b64encode(pdf_bytes).decode('ascii')

            # 2) Template se email_values banao
            email_values = template.generate_email(self.id)
            email_values.setdefault('email_to', self.partner_id.email or False)

            Mail = self.env['mail.mail'].sudo()
            Attachment = self.env['ir.attachment'].sudo()

            # 3) Pehle attachment record banao (res_model=mail.mail, res_id temporary 0)
            attachment = Attachment.create({
                'name': 'Challan-%s.pdf' % (self.name or self.id),
                'type': 'binary',
                'datas': pdf_base64,
                'res_model': 'mail.mail',
                'res_id': 0,
                'mimetype': 'application/pdf',
            })

            # 4) Purane template attachments bhi preserve karo, aur naya challan add karo
            attachment_cmds = []
            for val in (email_values.get('attachment_ids') or []):
                if isinstance(val, tuple):
                    # already a command
                    attachment_cmds.append(val)
                else:
                    # id -> (4, id)
                    attachment_cmds.append((4, val))
            attachment_cmds.append((4, attachment.id))
            email_values['attachment_ids'] = attachment_cmds

            # 5) Mail create + link attachment ka res_id + send
            mail = Mail.create(email_values)
            attachment.write({'res_id': mail.id})
            mail.send()

            self.message_post(
                body=_("Challan PDF attached and email sent to %s") %
                     (self.partner_id.email or "-"),
                subject=_("Invoice Email with Challan Sent")
            )
            _logger.info(
                "Challan attached and email sent for invoice %s to %s",
                self.name, self.partner_id.email or "-"
            )
            return True

        except Exception as e:
            _logger.exception(
                "Failed to generate/send challan for invoice %s: %s",
                self.name, e
            )
            # Fallback: simple email without challan
            return self._send_invoice_email()


# ---------------- Account Move Line ----------------
class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    product_category = fields.Char(
        string="Category",
        compute="_compute_category_size",
        store=True
    )
    product_size = fields.Char(
        string="Size",
        compute="_compute_category_size",
        store=True
    )

    @api.depends('product_id', 'product_id.categ_id', 'product_id.name')
    def _compute_category_size(self):
        """
        Compute product category and size.
        product_category = product.categ_id.name
        product_size = remaining words of product.name after first word.
        """
        for line in self:
            product = line.product_id
            if product:
                line.product_category = product.categ_id.name or ''
                name_parts = (product.name or "").strip().split()
                if len(name_parts) > 1:
                    line.product_size = " ".join(name_parts[1:])
                else:
                    line.product_size = ''
            else:
                line.product_category = ''
                line.product_size = ''
