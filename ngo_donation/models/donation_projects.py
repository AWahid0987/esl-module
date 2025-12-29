# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class DonationProjects(models.Model):
    _name = "donation.projects"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Donation Projects"

    name = fields.Char("Name", required=True)
    description = fields.Text("Description")
    target_amount = fields.Monetary("Funds Target Amount", required=True, currency_field="currency_id")
    product_amount = fields.Monetary("Amount", required=True, currency_field="currency_id")
    collected_amount = fields.Monetary(
        "Collected Amount", compute="_compute_collected_amount", store=True, currency_field="currency_id"
    )
    spent_amount = fields.Monetary("Spent Amount", compute="_compute_spent_amount", store=True, currency_field="currency_id")

    donor_ids = fields.One2many("donation.donor", "project_id", string="Donors")
    purchase_order_ids = fields.One2many("purchase.order", "donation_project_id", string="Related Purchases",readonly=True)

    product_id = fields.Many2one("product.product", string="Linked Project", readonly=True)
    stage = fields.Selection(
        [
            ("draft", "Draft"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Stage",
        default="draft",
        required=True,
    )
    currency_id = fields.Many2one(
        "res.currency", string="Currency", required=True, default=lambda self: self.env.company.currency_id
    )
    company_id = fields.Many2one("res.company", string="Company", required=True, default=lambda self: self.env.company)
    progress_percentage = fields.Float("Progress Percentage", compute="_compute_progress_percentage", store=True)

    transfer_out_ids = fields.One2many("donation.project.transfer", "donor_project_id", string="Transfers Given")
    transfer_in_ids = fields.One2many("donation.project.transfer", "recipient_project_id", string="Transfers Received")

    @api.depends("collected_amount", "target_amount")
    def _compute_progress_percentage(self):
        for project in self:
            if project.target_amount > 0:
                project.progress_percentage = (project.collected_amount / project.target_amount) * 100
            else:
                project.progress_percentage = 0

    @api.constrains("target_amount")
    def tagret_amount(self):
        for rec in self:
            if rec.target_amount < 1:
                raise UserError(_("Target Amount must be greater than 0!"))

    @api.depends("donor_ids.amount", "transfer_in_ids.amount", "transfer_out_ids.amount")
    def _compute_collected_amount(self):
        for project in self:
            donation_sum = sum(d.amount for d in project.donor_ids)
            transfer_in = sum(t.amount for t in project.transfer_in_ids)
            transfer_out = sum(t.amount for t in project.transfer_out_ids)
            project.collected_amount = donation_sum + transfer_in - transfer_out

    @api.depends("purchase_order_ids.amount_total")
    def _compute_spent_amount(self):
        for project in self:
            if not project.purchase_order_ids:
                project.spent_amount = 0.0
            else:
                project.spent_amount = sum(order.amount_total for order in project.purchase_order_ids)

    @api.model_create_multi
    def create(self, vals_list):
        projects = super(DonationProjects, self).create(vals_list)
        for project in projects:
            product = self.env["product.product"].create(
                {
                    "name": project.name,
                    "type": "service",
                    "categ_id": self.env.ref("product.product_category_all").id,
                    "list_price": project.product_amount,
                }
            )
            project.product_id = product.id
        return projects

    def action_open_transfer_wizard(self):
        self.ensure_one()
        return {
            'name': _('Transfer Funds'),
            'type': 'ir.actions.act_window',
            'res_model': 'donation.project.transfer.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_donor_project_id': self.id},
        }

    def _get_all_donor_emails(self):
        self.ensure_one()
        emails = [donor.email for donor in self.donor_ids if donor.email]
        return ",".join(emails)

    def action_send_donor_email(self):
        self.ensure_one()
        template = self.env.ref("ngo_donation.email_donation_project_update", raise_if_not_found=False)
        if not template:
            raise UserError(_("Email template not found."))
        template.send_mail(self.id, force_send=True)



class DonationDonor(models.Model):
    _name = "donation.donor"
    _description = "Donation Donor"

    partner_id = fields.Many2one("res.partner", string="Donor", required=True)
    email = fields.Char("Email", related="partner_id.email", readonly=True)
    phone = fields.Char("Phone", related="partner_id.phone", readonly=True)
    amount = fields.Monetary("Donation Amount", required=True, currency_field="currency_id")
    project_id = fields.Many2one("donation.projects", string="Donation Project", required=True)
    product_id = fields.Many2one(
        string="Product ID Linked",
        ondelete="restrict",
    )
    date = fields.Date("Donation Date", default=fields.Date.today)
    currency_id = fields.Many2one(
        "res.currency", string="Currency", required=True, default=lambda self: self.env.company.currency_id
    )
    company_id = fields.Many2one("res.company", string="Company", required=True, default=lambda self: self.env.company)
    sale_order_id = fields.Many2one("sale.order", string="Sale Order", required=True)
