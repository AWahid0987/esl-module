# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    # Link invoice back to Sale Order
    sale_id = fields.Many2one(
        'sale.order',
        string="Sale Order",
        readonly=True,
        copy=False,
        help="Source Sale Order for this invoice."
    )

    # Same stages as wizard (MUST match keys used in invoice_vals)
    payment_plan_stage = fields.Selection(
        selection=[
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
        copy=False,
    )

    payment_plan_percentage = fields.Float(
        string="Payment Plan %",
        digits=(5, 2),
        copy=False,
        help="Percentage of the Sale Order amount represented by this invoice."
    )
