# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class DonationProjectTransfer(models.Model):
    _name = "donation.project.transfer"
    _description = "Donation Project Transfer"

    donor_project_id = fields.Many2one("donation.projects", string="Donor Project", required=True)
    recipient_project_id = fields.Many2one("donation.projects", string="Recipient Project", required=True)
    amount = fields.Monetary("Amount", required=True, currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", string="Currency", required=True, default=lambda self: self.env.company.currency_id.id)

    date = fields.Date("Date", default=fields.Date.context_today)

    @api.constrains('amount')
    def _check_amount_positive(self):
        for rec in self:
            if rec.amount <= 0:
                raise UserError(_("Transfer amount must be positive!"))

    @api.constrains('donor_project_id', 'recipient_project_id')
    def _check_projects_different(self):
        for rec in self:
            if rec.donor_project_id == rec.recipient_project_id:
                raise UserError(_("Donor and recipient projects must be different!"))
