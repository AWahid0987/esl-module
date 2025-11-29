# -*- coding: utf-8 -*-
from odoo import models, fields

class SaleCommissionPlan(models.Model):
    _inherit = 'sale.commission.plan'   # <-- change if your plan model name differs

    commission_line_ids = fields.One2many(
        'sale.order.commission.line',
        'commission_plan_id',
        string='Achievements (Lines)'
    )
