# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class DonationProjectTransferWizard(models.TransientModel):
    _name = "donation.project.transfer.wizard"
    _description = "Donation Project Transfer Wizard"

    donor_project_id = fields.Many2one("donation.projects", string="Donor Project", required=True, readonly=True)
    recipient_project_id = fields.Many2one("donation.projects", string="Recipient Project", required=True)
    amount = fields.Monetary("Amount", required=True, currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", string="Currency", required=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        donor_project_id = self.env.context.get('default_donor_project_id')

        if donor_project_id:
            donor_project = self.env['donation.projects'].browse(donor_project_id)
            res.update({
                'donor_project_id': donor_project.id,
                'currency_id': donor_project.currency_id.id,
            })

        return res

    def action_transfer(self):
        self.ensure_one()
        if self.amount <= 0:
            raise UserError(_("Transfer amount must be positive!"))
        if self.donor_project_id == self.recipient_project_id:
            raise UserError(_("Donor and recipient projects must be different!"))

        self.env['donation.project.transfer'].create([{
            'donor_project_id': self.donor_project_id.id,
            'recipient_project_id': self.recipient_project_id.id,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'date': fields.Date.context_today(self),
        }])
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Transfer Successful'),
                'message': _('Successfully transferred %.2f %s from %s to %s.') % (
                    self.amount,
                    self.currency_id.name,
                    self.donor_project_id.name,
                    self.recipient_project_id.name,
                ),
                'type': 'success',
                'sticky': False,
            }
        }