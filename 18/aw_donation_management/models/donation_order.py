from odoo import models, fields, api
import datetime
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class DonationOrder(models.Model):
    _name = 'donation.order'
    _description = 'Donation Order'

    collection_center_id = fields.Many2one('res.partner', string='Collection Center', required=True, default=lambda self: self.env.user.partner_id)
    order_line_ids = fields.One2many('donation.product.line', 'donation_order_id', string='Donation Lines')
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Term')
    region_id = fields.Many2one('donation.region', string='Region', )
    donor_ref = fields.Char(string='Donor Ref')
    name = fields.Char(string='Donation Reference', required=True, copy=False, readonly=True, default='New')
    collecter = fields.Char(string="Collecter")
    user_id = fields.Many2one('res.users', string="Responsible User", default=lambda self: self.env.user)

    father_name = fields.Char(string="Father Name")
    father = fields.Char(string="Father Name")
    
    payment_status = fields.Selection(
        [
            ('not_paid', 'Unpaid'),
            ('in_payment', 'In Payment'),
            ('partial', 'Partially Paid'),
            ('reversed', 'Reversed'),
            ('invoicinig_legacy', 'Invoicing App legacy'),
            ('paid', 'Paid'),
        ],
        string="Payment Status",
        default='not_paid',

    )
    invoice_name = fields.Char(string="Invoice Name", compute="_compute_invoice_name")
    created_by = fields.Char(string="Created By / Resposible")
    
    @api.depends('invoice_count')     
    def _compute_invoice_name(self):
        for rec in self:
            invoices = self.env['account.move'].search([
                ('donation_order_id', '=', rec.id),
                ('move_type', '=', 'out_invoice')
            ])
            if invoices:
                rec.invoice_name = invoices[0].name
            else:
                rec.invoice_name = False
                    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], string='Status', default='draft')
    
    
    months = fields.Selection(
        [
            ('January','January'),
            ('February','February'),
            ('March','March'),
            ('April','April'),
            ('May','May'),
            ('June','June'),
            ('July','July'),
            ('August','August'),
            ('September','September'),
            ('October','October'),
            ('November','November'),
            ('December','December'),
        ]
        )
    
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount', store=True)
    narration = fields.Char(string="Note")
    donantion_date = fields.Datetime(string="Donation Date", default=datetime.datetime.now(), readonly=True)
    currency_id = fields.Many2one(
            'res.currency', 
            string='Currency', 
            default=lambda self: self.env.company.currency_id.id
        )
    company_id = fields.Many2one(
            'res.company', 
            string='Company', 
            default=lambda self: self.env.company.id
        )
    
    @api.depends('order_line_ids.amount')
    def _compute_total_amount(self):
        for order in self:
            order.total_amount = sum(line.amount for line in order.order_line_ids)
            
            
    invoice_count = fields.Integer(string='Invoice Count', compute='_compute_invoice_count')

    @api.depends('name')
    def _compute_invoice_count(self):
        for order in self:
            order.invoice_count = self.env['account.move'].search_count([
                ('donation_order_id', '=', self.id),
                ('move_type', '=', 'out_invoice')
            ])        
                 
    def action_view_invoices(self):
        action = self.env['ir.actions.act_window']._for_xml_id('account.action_move_in_invoice_type')
        action['domain'] = [('donation_order_id', '=', self.id)]
        action['view_mode'] = 'tree,form'
        action['views'] = [(k, v) for k, v in action['views'] if v in ['tree', 'form']]
        return action


    def action_confirm(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError("Only draft orders can be confirmed.")
        
        # Create a customer invoice
        invoice_lines = [(0, 0, {
            'account_id': line.account_id.id,
            'quantity': 1,
            'price_unit': line.amount,
            'tax_ids': False,
            'name': line.account_id.name,
        }) for line in self.order_line_ids if line.amount > 0]  # Only include lines where amount is greater than 0

        if not invoice_lines:
            raise UserError("Cannot create an invoice with no valid donation lines.")

        invoice_vals = {
            'move_type': 'out_invoice',  # Customer Invoice
            'partner_id': self.collection_center_id.id,
            'invoice_date': self.donantion_date,
            'invoice_origin': self.name,
            'donation_order_id': self.id,
            'invoice_line_ids': invoice_lines,
            'currency_id': self.currency_id.id,
            'company_id': self.company_id.id,
            'payment_reference': self.donor_ref,
            'invoice_payment_term_id': self.payment_term_id.id,
        }

        invoice = self.env['account.move'].sudo().create(invoice_vals)
        invoice.action_post()

        # Update the state of the order
        self.write({'state': 'confirmed'})
        
        # Return the action to display the created invoice
        return True

        
        
    def action_cancel(self):
        """Cancel the donation order and its invoice."""
        self.ensure_one() 
        if self.state == 'done':
            raise UserError("Cannot cancel a done order.")

        # Cancel the associated invoice
        invoices = self.env['account.move'].search([
            ('donation_order_id', '=', self.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '!=', 'cancel')
        ])
        for invoice in invoices:
            invoice.button_cancel()

        self.write({'state': 'cancel'})

    def action_done(self):
        self.ensure_one() 
        if self.state != 'confirmed':
            raise UserError("Only confirmed orders can be marked as done.")
        self.write({'state': 'done'})
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('donation.order.seq') or 'New'
        return super(DonationOrder, self).create(vals)
    
    
    
    @api.model
    def default_get(self, fields):
        res = super(DonationOrder, self).default_get(fields)

        if 'order_line_ids' in fields:
            account_obj = self.env['account.account']
            income_accounts = account_obj.search([('account_type', '=', 'income')])  # Fetch income accounts

            order_lines = []
            for account in income_accounts:
                order_lines.append((0, 0, {
                    'name': account.name,
                    'account_id': account.id,
                }))
            res['order_line_ids'] = order_lines

        return res

    
    @api.onchange('collection_center_id')
    def _onchange_collection_center_id(self):
        for record in self:
            if record.collection_center_id and record.collection_center_id.region_id:
                record.region_id = record.collection_center_id.region_id
            else:
                record.region_id = False
    
    
  
  
    def print_invoice_report(self):
        return self.env.ref(
            "aw_donation_management.custom_print"
        ).report_action(self)
