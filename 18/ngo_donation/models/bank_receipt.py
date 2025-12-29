# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class BankReceipt(models.Model):
    _name = 'bank.receipt'
    _description = 'Bank Receipt'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Receipt Number', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    transaction_id = fields.Many2one('payment.transaction', string='Payment Transaction', required=True, ondelete='cascade')
    transaction_reference = fields.Char(string='Transaction ID', required=True, help='Transaction ID provided by customer')
    receipt_photo = fields.Binary(string='Receipt Photo', required=True, attachment=True)
    receipt_photo_filename = fields.Char(string='Receipt Photo Filename')
    state = fields.Selection([
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='pending', required=True, tracking=True)
    approved_by = fields.Many2one('res.users', string='Approved By', readonly=True)
    approved_date = fields.Datetime(string='Approved Date', readonly=True)
    rejected_by = fields.Many2one('res.users', string='Rejected By', readonly=True)
    rejected_date = fields.Datetime(string='Rejected Date', readonly=True)
    rejection_reason = fields.Text(string='Rejection Reason')
    company_id = fields.Many2one('res.company', string='Company', related='transaction_id.company_id', store=True, readonly=True)
    partner_id = fields.Many2one('res.partner', string='Donor', related='transaction_id.partner_id', store=True, readonly=True)
    amount = fields.Monetary(string='Amount', related='transaction_id.amount', store=True, readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', related='transaction_id.currency_id', store=True, readonly=True)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('bank.receipt') or _('New')
        return super(BankReceipt, self).create(vals)

    def action_approve(self):
        """Approve the bank receipt and mark transaction as done"""
        for receipt in self:
            if receipt.state != 'pending':
                raise ValidationError(_('Only pending receipts can be approved.'))
            
            receipt.write({
                'state': 'approved',
                'approved_by': self.env.user.id,
                'approved_date': fields.Datetime.now()
            })
            
            # Mark the transaction as done if it's pending
            if receipt.transaction_id.state == 'pending':
                receipt.transaction_id._set_done()
                receipt.transaction_id._post_process()

    def action_reject(self):
        """Reject the bank receipt"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reject Receipt'),
            'res_model': 'bank.receipt.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_receipt_id': self.id}
        }

