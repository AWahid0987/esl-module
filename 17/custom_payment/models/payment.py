from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class CustomPayment(models.Model):
    _name = 'custom.payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Custom Payment'

    name = fields.Char(
        string='Payment Reference',
        required=True,
        copy=False,
        readonly=True,
        default='/',
        tracking=True
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        index=True
    )

    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        required=True,
        tracking=True,
        check_company=False,
        domain="[('name', 'ilike', 'Miscellaneous Operations')]"
    )

    type = fields.Selection(
        [
            ('sending', 'Sending'),
            ('receiving', 'Receiving'),
        ],
        string="Type",
        required=True,
        default='sending',
        tracking=True,
    )

    customer_id = fields.Many2one("res.partner", string="Partner")
    label = fields.Char(string="Label", tracking=True)
    entry_date = fields.Date(default=fields.Date.context_today, required=True)
    notes = fields.Text(string="Description")
    amount = fields.Float(string='Amount', required=True)

    journal_entry_id = fields.Many2one(
        'account.move',
        string='Journal Entry',
        readonly=True,
        copy=False
    )

    debit_account_id = fields.Many2one(
        'account.account',
        string='Debit Account',
        required=True,
        check_company=False,
        domain="['|', ('code', 'in', ['101401','101405','101406','640000','640001','101001']), ('code', '>=', '510001'), ('code', '<=', '599999')]",
        ondelete='restrict'
    )

    credit_account_id = fields.Many2one(
        'account.account',
        string='Credit Account',
        required=True,
        tracking=True,
        check_company=False,
        domain="[('name', 'ilike', 'Cash Multan Zone')]",
        ondelete='restrict'
    )

    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        readonly=True,
        copy=False
    )

    status = fields.Selection(
        [
            ('draft', 'Draft'),
            ('waiting_for_approval', 'Waiting for Approval'),
            ('done', 'Done'),
            ('cancelled', 'Cancelled')
        ],
        default='draft',
        string='Status',
        tracking=True
    )

    # New helper field (optional – for view attrs)
    can_approve = fields.Boolean(
        string='Can Approve',
        compute='_compute_can_approve',
        compute_sudo=True
    )

    show_customer = fields.Boolean(compute="_compute_show_customer")

    @api.depends('debit_account_id')
    def _compute_show_customer(self):
        for rec in self:
            rec.show_customer = rec.debit_account_id.code == '101001'

    @api.depends()
    def _compute_can_approve(self):
        """Check if current user is in Custom Payment Approver group."""
        user = self.env.user
        has_group = user.has_group(
            'custom_payment.group_custom_payment_approver'  # TODO: replace custom_payment
        )
        for rec in self:
            rec.can_approve = has_group

    # --- Dynamic domain for credit/debit account and journal ---
    @api.onchange('company_id')
    def _onchange_company_id(self):
        for rec in self:
            journal = self.env['account.journal'].search([
                ('name', 'ilike', 'Miscellaneous Operations'),
                ('company_id', '=', rec.company_id.id)
            ], limit=1)
            rec.journal_id = journal.id if journal else False

            rec.debit_account_id = False
            rec.credit_account_id = False

            credit_account = self.env['account.account'].search([
                ('name', 'ilike', 'Cash Multan Zone'),
                ('company_id', '=', rec.company_id.id)
            ], limit=1)
            rec.credit_account_id = credit_account.id if credit_account else False

            domain = {}
            if rec.company_id:
                domain['debit_account_id'] = [
                    '|',
                    ('code', 'in', ['101401', '101405', '101406']),
                    '&', ('code', '>=', '510001'), ('code', '<=', '599999')
                ]
            return {'domain': domain}

    # --- Sequence handling ---
    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            company_id = vals.get('company_id') or self.env.company.id
            sequence = self.env['ir.sequence'].sudo().search([
                ('code', '=', 'custom.payment'),
                ('company_id', '=', company_id)
            ], limit=1)
            if not sequence:
                sequence_vals = {
                    'name': f'Custom Payment - Company {company_id}',
                    'code': 'custom.payment',
                    'prefix': f'C{company_id}/PAY/',
                    'padding': 6,
                    'company_id': company_id,
                    'implementation': 'standard',
                    'active': True,
                }
                sequence = self.env['ir.sequence'].sudo().create(sequence_vals)
                _logger.info(f"Created sequence for company {company_id}")

            try:
                vals['name'] = sequence.sudo().next_by_id() or f"C{company_id}/PAY/000001"
            except Exception as e:
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                vals['name'] = f"C{company_id}/PAY/{timestamp}"
                _logger.warning(f"Fallback sequence used for payment: {vals['name']} - Error: {e}")

        if 'type' not in vals or not vals.get('type'):
            vals['type'] = 'sending'

        return super(CustomPayment, self).create(vals)

    def write(self, vals):
        if 'type' in vals and not vals.get('type'):
            vals['type'] = 'sending'
        return super(CustomPayment, self).write(vals)

    @api.constrains('amount')
    def _check_amount(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError("Amount must be greater than zero.")

    # --- Actions ---
    def action_send_payment(self):
        self.ensure_one()
        if self.status != 'draft':
            raise UserError('Only draft payments can be sent.')
        self.status = 'waiting_for_approval'

    def action_approve_payment(self):
        self.ensure_one()

        # ✅ Group-based approval (NO hard-coded logins now)
        if not self.env.user.has_group('custom_payment.group_custom_payment_approver'):
            raise UserError("You are not allowed to approve cash payments.")

        if self.status != 'waiting_for_approval':
            raise UserError('Only waiting payments can be approved.')

        if not self.debit_account_id or not self.credit_account_id:
            raise ValidationError("Both Debit and Credit accounts are required.")

        if self.amount <= 0:
            raise ValidationError("Amount must be greater than zero.")

        move_vals = {
            'ref': f"{self.name} - {self.invoice_id.name if self.invoice_id else ''}",
            'date': self.entry_date,
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
            'line_ids': [
                (0, 0, {
                    'name': self.label or self.name,
                    'account_id': self.debit_account_id.id,
                    'debit': self.amount,
                    'credit': 0.0,
                    'partner_id': self.invoice_id.partner_id.id if self.invoice_id else False,
                }),
                (0, 0, {
                    'name': self.label or self.name,
                    'account_id': self.credit_account_id.id,
                    'debit': 0.0,
                    'credit': self.amount,
                    'partner_id': self.invoice_id.partner_id.id if self.invoice_id else False,
                }),
            ],
        }

        try:
            move = self.env['account.move'].sudo().create(move_vals)
            move.sudo().action_post()
            self.journal_entry_id = move.id
            self.status = 'done'
            _logger.info(f"Journal entry created: {move.name} for payment {self.name}")
        except Exception as e:
            _logger.error(f"Failed to create journal entry: {e}")
            raise UserError(f"Failed to create journal entry: {e}")

    def action_reset_to_draft(self):
        self.ensure_one()
        if self.status not in ['waiting_for_approval', 'cancelled']:
            raise UserError("Only waiting or cancelled payments can be reset to draft.")
        self.status = 'draft'

    def action_cancel(self):
        self.ensure_one()
        if self.status == 'done':
            raise UserError("Cannot cancel a processed payment. Please reverse it manually.")
        self.status = 'cancelled'
