from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class CustomPaymentReceive(models.Model):
    _name = 'custom.payment.recieve'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Custom Payment Receive'

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
        domain="[('name','ilike','Miscellaneous Operations')]"
    )
    type = fields.Selection(
        [('sending','Sending'),('receiving','Receiving')],
        string='Type',
        required=True,
        default='receiving',
        tracking=True
    )
    label = fields.Char(string='Label', tracking=True)
    entry_date = fields.Date(default=fields.Date.context_today, required=True)
    notes = fields.Text(string='Description')
    amount = fields.Float(string='Amount', required=True)
    debit_account_id = fields.Many2one(
        'account.account',
        string='Credit Account',
        required=True,
        tracking=True,
        check_company=False,
        domain=[('code','in',['101401','101405','101406'])]
    )
    credit_account_id = fields.Many2one(
        'account.account',
        string='Debit Account',
        required=True,
        tracking=True,
        check_company=False,
        domain="[('name','ilike','Cash'),('company_id','=',company_id)]"
    )
    journal_entry_id = fields.Many2one('account.move', string='Journal Entry', readonly=True)
    journal_entry_count = fields.Integer(string='Journal Entries', compute='_compute_journal_entry_count')
    invoice_id = fields.Many2one('account.move', domain=[('move_type', '=', 'out_invoice')])

    status = fields.Selection(
        [('draft','Draft'),('sent','Sent'),('received','Received'),('cancelled','Cancelled')],
        string='Status',
        default='draft',
        tracking=True
    )
    status = fields.Selection(
        [
            ('draft', 'Draft'),
            ('waiting_for_approval', 'Waiting for Approval'),
            ('approved', 'Approved'),
            ('received', 'Received'),
            ('cancelled', 'Cancelled')
        ],
        string='Status',
        default='draft',
        tracking=True
    )
    can_approve = fields.Boolean(string='Can Approve', compute='_compute_can_approve', compute_sudo=True)
    @api.depends()
    def _compute_can_approve(self):
        """Check if current user is in Custom Payment Approver group."""
        user = self.env.user
        has_group = user.has_group(
            'custom_payment.group_custom_payment_receive_approver'  # TODO: replace custom_payment
        )
        for rec in self:
            rec.can_approve = has_group

    @api.onchange('company_id')
    def _onchange_company_id(self):
        for rec in self:
            journal = self.env['account.journal'].search([('name','ilike','Miscellaneous Operations'), ('company_id','=',rec.company_id.id)], limit=1)
            rec.journal_id = journal.id if journal else False
            rec.debit_account_id = False
            rec.credit_account_id = False
            domain = {}
            domain['debit_account_id'] = [('code','in',['101401','101405','101406']), ('company_id','=',rec.company_id.id)] if rec.company_id else [('code','in',['101401','101405','101406'])]
            domain['credit_account_id'] = [('name','ilike','Cash'),('company_id','=',rec.company_id.id)] if rec.company_id else [('name','ilike','Cash')]
            domain['journal_id'] = [('name','ilike','Miscellaneous Operations'),('company_id','=',rec.company_id.id)] if rec.company_id else [('name','ilike','Miscellaneous Operations')]
            return {'domain': domain}

    @api.model
    def create(self, vals):
        if vals.get('name','/') == '/':
            company_id = vals.get('company_id') or self.env.company.id
            sequence = self.env['ir.sequence'].sudo().search([('code','=','custom.payment.recieve'),('company_id','=',company_id)], limit=1)
            if sequence:
                vals['name'] = sequence.sudo().next_by_id()
            else:
                vals['name'] = self.env['ir.sequence'].sudo().next_by_code('custom.payment.recieve') or f"PAY/{company_id}/{self.env['custom.payment.recieve'].search_count([('company_id','=',company_id)])+1:06d}"
        if 'type' not in vals or not vals.get('type'):
            vals['type'] = 'receiving'
        return super().create(vals)

    def write(self, vals):
        if 'type' in vals and not vals.get('type'):
            vals['type'] = 'receiving'
        return super().write(vals)

    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError("Amount must be greater than zero.")

    def _compute_journal_entry_count(self):
        for rec in self:
            rec.journal_entry_count = 1 if rec.journal_entry_id else 0

    # --- Actions ---
    def action_send_payment(self):
        self.ensure_one()
        if self.status != 'draft':
            raise UserError("Only draft payments can be sent.")
        self.status = 'waiting_for_approval'



    def action_approve_payment(self):
        self.ensure_one()

        # ✅ Group-based approval (NO hard-coded logins now)
        if not self.env.user.has_group('custom_payment.group_custom_payment_receive_approver'):
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
            self.status = 'received'
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

    def action_view_journal_entry(self):
        self.ensure_one()
        if not self.journal_entry_id:
            raise UserError("No journal entry linked to this payment.")
        return {
            'type':'ir.actions.act_window',
            'res_model':'account.move',
            'view_mode':'form',
            'res_id':self.journal_entry_id.id,
            'target':'current',
        }
