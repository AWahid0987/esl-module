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
    ], string="Commission Category", required=True)

    sale_price = fields.Monetary(string="Sale Price", currency_field="currency_id", required=True)
    extra_amount = fields.Monetary(string="Padding Amount", compute="_compute_extra_amount", store=True)
    variable_commission_base = fields.Monetary(string="Variable Base", compute="_compute_variable_base", store=True)
    commission_1 = fields.Monetary(string="65% Padding Commission", compute="_compute_commission_values", store=True)
    commission_2 = fields.Monetary(string="10% Padding Commission", compute="_compute_commission_values", store=True)
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

    # FIELD: jis naam per bill create hona hai
    bill_name = fields.Char(
        string="Bill Name",
        help="Jis naam par bill create hona hai, woh yahan likhein. Ye vendor aur bill reference dono banega."
    )

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
    #   Create / Write overrides
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

    def write(self, vals):
        """Sync bill_name -> vendor bill (partner + ref) on change."""
        res = super().write(vals)
        if 'bill_name' in vals:
            for rec in self:
                if rec.commission_invoice_id:
                    # Update reference
                    rec.commission_invoice_id.ref = rec.bill_name or False
                    # Update vendor according to bill_name
                    if rec.bill_name:
                        partner = self.env['res.partner'].search(
                            [('name', '=', rec.bill_name)],
                            limit=1
                        )
                        if not partner:
                            partner = self.env['res.partner'].create({
                                'name': rec.bill_name,
                                'supplier_rank': 1,
                            })
                        rec.commission_invoice_id.partner_id = partner.id
        return res

    # =========================
    #   Invoice Auto-Creation
    # =========================
    def _auto_create_invoice(self):
        """Automatically create a draft supplier bill for this commission."""
        self.ensure_one()
        if not self.commission_total:
            return False

        # Partner: agar bill_name diya hua hai to us naam ka vendor use/create karo
        partner = False
        if self.bill_name:
            partner = self.env['res.partner'].search([('name', '=', self.bill_name)], limit=1)
            if not partner:
                partner = self.env['res.partner'].create({
                    'name': self.bill_name,
                    'supplier_rank': 1,
                })
        else:
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

        # Bill Reference: hamesha current bill_name ko follow kare
        move_vals = {
            'move_type': 'in_invoice',
            'partner_id': partner.id if partner else False,
            'invoice_line_ids': [(0, 0, line_vals)],
            'currency_id': self.currency_id.id,
            'ref': self.bill_name or (partner.name if partner else False) or self.origin or self.name,
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
# customer invoices are posted and then create the commission record
# automatically.
#
# Conditions:
#   - Cash Full Invoice:
#       -> 1 posted out_invoice for that origin
#       -> us invoice me kam az kam 1 line non-downpayment ho
#   - Down Payment + Confirmation:
#       -> same origin ke posted invoices me kam az kam 1 invoice
#          jisme non-downpayment line ho (final invoice)
# ------------------------------------------------------------------
class AccountMove(models.Model):
    _inherit = 'account.move'

    def _has_final_invoice(self, posted_moves):
        """Return True if at least one invoice has a non-downpayment line."""
        for inv in posted_moves:
            # Odoo standard field on advance lines from SO: is_downpayment
            if any(not line.is_downpayment for line in inv.invoice_line_ids):
                return True
        return False

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

            if not posted_moves:
                continue

            # Decide if commission should be created:
            # 1) Single posted invoice -> create only if it's a full (non-downpayment) invoice
            # 2) Multiple posted invoices -> create if any invoice has final (non-downpayment) lines
            create_commission = False
            if len(posted_moves) == 1:
                inv = posted_moves[0]
                # agar tamam lines downpayment hain to abhi commission mat banao
                if any(not l.is_downpayment for l in inv.invoice_line_ids):
                    create_commission = True
            else:
                # 2 ya zyada invoices -> at least 1 final invoice hona chahe
                if self._has_final_invoice(posted_moves):
                    create_commission = True

            if not create_commission:
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
                # Default bill_name partner ke naam se, lekin baad me user change kare
                # to write() ke through invoice ref + vendor update ho jayega.
                'bill_name': partner.name if partner else origin,
            }

            try:
                created = self.env['land.plot.commission'].create(vals)
                _logger.info(f"✅ Created commission record (auto) for origin {origin}: {created.id}")
            except Exception as e:
                _logger.exception(f"Failed to auto-create commission for origin {origin}: {e}")

        return res
