from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = "account.move"

    custom_payment_state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('paid', 'Paid'),
            ('cancel', 'Cancelled'),
        ],
        string="Custom Payment State",
        default='draft',
    )

    # IMPORTANT:
    # Keep this as Char (or Selection with text keys) because the DB
    # already contains text values like "verified".
    verification = fields.Char(
        string="Verification",
        help="Verification status (e.g. 'verified', 'unverified', etc.).",
    )
    # If you prefer a selection instead of plain Char, you can use:
    # verification = fields.Selection(
    #     [
    #         ('verified', 'Verified'),
    #         ('unverified', 'Unverified'),
    #     ],
    #     string="Verification",
    #     default='unverified',
    # )

    reconciled = fields.Boolean(
        string="Reconciled",
        compute="_compute_reconciled",
        store=True,
    )

    @api.depends('payment_state')
    def _compute_reconciled(self):
        """
        Very simple logic:
        - If payment_state == 'paid' => reconciled = True
        - Else => False
        """
        for move in self:
            move.reconciled = (move.payment_state == 'paid')
