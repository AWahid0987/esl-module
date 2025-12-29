# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class BankReceiptRejectWizard(models.TransientModel):
    _name = 'bank.receipt.reject.wizard'
    _description = 'Bank Receipt Rejection Wizard'

    receipt_id = fields.Many2one('bank.receipt', string='Receipt', required=True)
    rejection_reason = fields.Text(string='Rejection Reason', required=True)

    def action_reject(self):
        """Reject the bank receipt with reason"""
        self.ensure_one()
        self.receipt_id.write({
            'state': 'rejected',
            'rejected_by': self.env.user.id,
            'rejected_date': fields.Datetime.now(),
            'rejection_reason': self.rejection_reason
        })
        return {'type': 'ir.actions.act_window_close'}

