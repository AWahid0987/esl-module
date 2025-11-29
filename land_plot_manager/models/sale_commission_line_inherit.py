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

    COMMISSION_RATE = 0.05

    # =========================
    #   Fields
    # =========================
    name = fields.Char(default=lambda self: _('New'), readonly=True, copy=False)
    commission_category = fields.Selection([
        ('r5', 'Residential 5 Marla'),
        ('r10', 'Residential 10 Marla'),
        ('c4', 'Commercial 4 Marla'),
        ('c8', 'Commercial 8 Marla'),
    ], string="Commission Category", required=True)

    sale_price = fields.Monetary(string="Sale Price", currency_field="currency_id", required=True)
    extra_amount = fields.Monetary(string="Padding Amount", compute="_compute_extra_amount", store=True)
    variable_commission_base = fields.Monetary(string="Variable Base", compute="_compute_variable_base", store=True)
    commission_1 = fields.Monetary(string="65% Padding Commission", compute="_compute_commission_values", store=True)
    commission_2 = fields.Monetary(string="5% Padding Commission", compute="_compute_commission_values", store=True)
    commission_total = fields.Monetary(string="Total Commission", compute="_compute_commission_values", store=True)

    commission_invoice_id = fields.Many2one('account.move', string='Commission Invoice', copy=False)
    invoice_state = fields.Selection(
        related='commission_invoice_id.state',
        string='Invoice Status',
        readonly=True,
        store=True
    )

    commission_partner_id = fields.Many2one('res.partner', string='Commission Partner')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, required=True)

    # Link back to sale/order origin if available
    origin = fields.Char(string='Origin (Sale)', readonly=True, copy=False)

    # =========================
    #   Computed Fields
    # =========================
    @api.depends('commission_category')
    def _compute_extra_amount(self):
        for rec in self:
            data = self.COMMISSION_CATEGORY_MAP.get(rec.commission_category)
            rec.extra_amount = data['extra_amount'] if data else 0.0

    @api.depends('sale_price', 'extra_amount')
    def _compute_variable_base(self):
        for rec in self:
            rec.variable_commission_base = max(0.0, (rec.sale_price or 0.0) - (rec.extra_amount or 0.0))

    @api.depends('commission_category', 'variable_commission_base')
    def _compute_commission_values(self):
        for rec in self:
            data = self.COMMISSION_CATEGORY_MAP.get(rec.commission_category)
            if data:
                rec.commission_1 = data['commission_1']
                rec.commission_2 = round((rec.variable_commission_base or 0.0) * self.COMMISSION_RATE, 2)
                rec.commission_total = rec.commission_1 + rec.commission_2
            else:
                rec.commission_1 = rec.commission_2 = rec.commission_total = 0.0

    # =========================
    #   Invoice Auto-Creation
    # =========================
    @api.model_create_multi
    def create(self, vals_list):
        # Handle both single dict and list of dicts
        if isinstance(vals_list, dict):
            vals_list = [vals_list]
        
        # Generate sequence numbers for name field if not provided
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('land.plot.commission') or 'New'
        
        records = super().create(vals_list)
        for rec in records:
            # Auto-create draft supplier bill for commission
            rec._auto_create_invoice()
        return records

    def _auto_create_invoice(self):
        """Automatically create a draft supplier bill for this commission."""
        self.ensure_one()
        if not self.commission_total:
            return False

        partner = self.commission_partner_id or self.env.company.partner_id

        # Create/find a product named 'Commission Service'
        product = self.env['product.product'].search([('name', '=', 'Commission Service')], limit=1)
        if not product:
            product = self.env['product.product'].create({
                'name': 'Commission Service',
                'type': 'service',
                'list_price': 0.0,
            })

        line_vals = {
            'name': product.name,
            'product_id': product.id,
            'quantity': 1.0,
            'price_unit': self.commission_total,
        }

        move_vals = {
            'move_type': 'in_invoice',
            'partner_id': partner.id,
            'invoice_line_ids': [(0, 0, line_vals)],
            'currency_id': self.currency_id.id,
        }

        move = self.env['account.move'].create(move_vals)
        self.commission_invoice_id = move.id
        _logger.info(f"✅ Auto-created draft commission invoice {move.name or move.id} for {self.name}")
        return move

    # =========================
    #   Actions
    # =========================
    def action_confirm_invoice(self):
        """Confirm (post) the linked draft invoice."""
        for rec in self:
            if rec.commission_invoice_id and rec.commission_invoice_id.state == 'draft':
                rec.commission_invoice_id.action_post()
        return True


# ------------------------------------------------------------------
# Hook into account.move posting so we can detect when the relevant
# customer invoices (downpayment + confirmation) are both posted and
# then create the commission record automatically.
# ------------------------------------------------------------------
class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        res = super(AccountMove, self).action_post()

        # After posting invoice(s), check origin grouping
        for move in self:
            origin = (move.invoice_origin or '').strip()
            # Only proceed if there is an origin (usually sale order name)
            if not origin:
                continue

            # Find posted customer invoices with same origin
            domain = [
                ('invoice_origin', '=', origin),
                ('state', '=', 'posted'),
                ('move_type', '=', 'out_invoice'),
            ]
            posted_moves = self.env['account.move'].search(domain)

            # Heuristic: consider commission eligible when there are at least 2 posted customer invoices
            # for the same origin (commonly: a downpayment + a confirmation invoice).
            if len(posted_moves) < 2:
                continue

            # Avoid duplicate commission records for the same origin
            existing = self.env['land.plot.commission'].search([('origin', '=', origin)], limit=1)
            if existing:
                continue

            # Try to detect sale order to get better data
            sale = self.env['sale.order'].search([('name', '=', origin)], limit=1)

            # Determine sale_price (fall back to largest posted invoice amount)
            sale_price = 0.0
            if sale:
                sale_price = sale.amount_total or 0.0
            else:
                for m in posted_moves:
                    sale_price = max(sale_price, m.amount_total or 0.0)

            # Try to detect commission_category from sale.order lines product names
            commission_category = 'r5'  # default
            if sale:
                found = False
                for line in sale.order_line:
                    pname = (line.product_id.name or '').lower()
                    if '5 marla' in pname or '5-marla' in pname or 'r5' in pname:
                        commission_category = 'r5'
                        found = True
                        break
                    if '10 marla' in pname or '10-marla' in pname or 'r10' in pname:
                        commission_category = 'r10'
                        found = True
                        break
                    if '4 marla' in pname or '4-marla' in pname or 'c4' in pname:
                        commission_category = 'c4'
                        found = True
                        break
                    if '8 marla' in pname or '8-marla' in pname or 'c8' in pname:
                        commission_category = 'c8'
                        found = True
                        break
                # If sale has an explicit field (custom) named commission_category, prefer it
                if not found and hasattr(sale, 'commission_category') and sale.commission_category:
                    commission_category = sale.commission_category

            partner = move.partner_id or (sale.partner_id if sale else None) or self.env.company.partner_id
            currency = move.currency_id or (sale.currency_id if sale else self.env.company.currency_id)

            vals = {
                'name': origin,
                'origin': origin,
                'commission_category': commission_category,
                'sale_price': sale_price,
                'commission_partner_id': partner.id if partner else False,
                'currency_id': currency.id if currency else False,
            }

            try:
                created = self.env['land.plot.commission'].create(vals)
                _logger.info(f"✅ Created commission record (auto) for origin {origin}: {created.id}")
            except Exception as e:
                _logger.exception(f"Failed to auto-create commission for origin {origin}: {e}")

        return res
