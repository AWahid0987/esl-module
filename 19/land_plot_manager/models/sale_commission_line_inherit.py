# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class LandPlotCommission(models.Model):
    _name = 'land.plot.commission'
    _description = 'Land Plot Commission Calculation'
    _order = 'create_date desc'

    # =========================
    #   Constants
    # =========================
    COMMISSION_CATEGORY_MAP = {
        'r5': {'name': 'Residential 5 Marla', 'extra_amount': 200000.0, 'commission_1': 130000.0},
        'r10': {'name': 'Residential 10 Marla', 'extra_amount': 300000.0, 'commission_1': 195000.0},
        'c4': {'name': 'Commercial 4 Marla', 'extra_amount': 400000.0, 'commission_1': 260000.0},
        'c8': {'name': 'Commercial 8 Marla', 'extra_amount': 600000.0, 'commission_1': 390000.0},
    }

    COMMISSION_RATE = 0.10

    # =========================
    #   Fields
    # =========================
    name = fields.Char(default=lambda self: _('New'), readonly=True, copy=False)

    commission_category = fields.Selection([
        ('r5', 'Residential 5 Marla'),
        ('r10', 'Residential 10 Marla'),
        ('c4', 'Commercial 4 Marla'),
        ('c8', 'Commercial 8 Marla'),
    ], required=True)

    sale_price = fields.Monetary(required=True)
    extra_amount = fields.Monetary(compute="_compute_extra_amount", store=True)
    variable_commission_base = fields.Monetary(compute="_compute_variable_base", store=True)

    commission_1 = fields.Monetary(compute="_compute_commission_values", store=True)
    commission_2 = fields.Monetary(compute="_compute_commission_values", store=True)
    commission_total = fields.Monetary(compute="_compute_commission_values", store=True)

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
        required=True
    )

    commission_partner_id = fields.Many2one(
        'res.partner',
        string="Commission Customer"
    )

    # ✅ ALL partners selectable
    bill_name = fields.Many2one(
        'res.partner',
        string="Bill Name",
        required=True
    )

    commission_invoice_id = fields.Many2one(
        'account.move',
        string="Commission Bill",
        copy=False
    )

    invoice_state = fields.Selection(
        related='commission_invoice_id.state',
        store=True,
        readonly=True
    )

    origin = fields.Char(readonly=True, copy=False)

    # =========================
    #   Compute Methods
    # =========================
    @api.depends('commission_category')
    def _compute_extra_amount(self):
        for rec in self:
            rec.extra_amount = self.COMMISSION_CATEGORY_MAP.get(
                rec.commission_category, {}
            ).get('extra_amount', 0.0)

    @api.depends('sale_price', 'extra_amount')
    def _compute_variable_base(self):
        for rec in self:
            rec.variable_commission_base = max(
                0.0, rec.sale_price - rec.extra_amount
            )

    @api.depends('commission_category', 'variable_commission_base')
    def _compute_commission_values(self):
        for rec in self:
            data = self.COMMISSION_CATEGORY_MAP.get(rec.commission_category)
            if not data:
                rec.commission_1 = rec.commission_2 = rec.commission_total = 0.0
                continue

            rec.commission_1 = data['commission_1']
            rec.commission_2 = round(rec.variable_commission_base * self.COMMISSION_RATE, 2)
            rec.commission_total = rec.commission_1 + rec.commission_2

    # =========================
    #   Create Override
    # =========================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'land.plot.commission'
                ) or 'New'

        records = super().create(vals_list)
        for rec in records:
            rec._auto_create_invoice()
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'bill_name' in vals:
            for rec in self:
                if rec.commission_invoice_id:
                    rec.commission_invoice_id.partner_id = rec.bill_name.id
                    rec.commission_invoice_id.ref = rec.bill_name.name
        return res

    # =========================
    #   Invoice Creation
    # =========================
    def _auto_create_invoice(self):
        self.ensure_one()

        if not self.commission_total:
            return False

        if not self.bill_name:
            raise UserError(_("Bill Name is required."))

        # ✅ auto-make vendor if not already
        if self.bill_name.supplier_rank == 0:
            self.bill_name.supplier_rank = 1

        product = self.env['product.product'].search(
            [('name', '=', 'Commission Service')], limit=1
        )
        if not product:
            product = self.env['product.product'].create({
                'name': 'Commission Service',
                'type': 'service',
            })

        move = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.bill_name.id,
            'currency_id': self.currency_id.id,
            'ref': self.bill_name.name,
            'invoice_line_ids': [(0, 0, {
                'product_id': product.id,
                'name': product.name,
                'quantity': 1.0,
                'price_unit': self.commission_total,
            })],
        })

        self.commission_invoice_id = move.id
        _logger.info("Commission bill created for %s", self.name)
        return move

    def action_confirm_invoice(self):
        for rec in self:
            if rec.commission_invoice_id.state == 'draft':
                rec.commission_invoice_id.action_post()
        return True


# ==========================================================
#   AUTO COMMISSION CREATION AFTER CUSTOMER INVOICE POST
# ==========================================================
class AccountMove(models.Model):
    _inherit = 'account.move'

    def _has_final_invoice(self, invoices):
        return any(
            any(not l.is_downpayment for l in inv.invoice_line_ids)
            for inv in invoices
        )

    def action_post(self):
        res = super().action_post()

        for move in self:
            origin = (move.invoice_origin or '').strip()
            if not origin or move.move_type != 'out_invoice':
                continue

            posted = self.env['account.move'].search([
                ('invoice_origin', '=', origin),
                ('state', '=', 'posted'),
                ('move_type', '=', 'out_invoice'),
            ])

            if not posted:
                continue

            if len(posted) == 1:
                if not any(not l.is_downpayment for l in posted.invoice_line_ids):
                    continue
            else:
                if not self._has_final_invoice(posted):
                    continue

            if self.env['land.plot.commission'].search([('origin', '=', origin)], limit=1):
                continue

            sale = self.env['sale.order'].search([('name', '=', origin)], limit=1)
            sale_price = sale.amount_total if sale else max(p.amount_total for p in posted)

            partner = move.partner_id or self.env.company.partner_id

            vals = {
                'name': origin,
                'origin': origin,
                'commission_category': 'r5',
                'sale_price': sale_price,
                'commission_partner_id': partner.id,
                'currency_id': move.currency_id.id,
                'bill_name': partner.id,
            }

            self.env['land.plot.commission'].create(vals)

        return res
