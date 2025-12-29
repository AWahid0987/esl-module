# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _, Command
from odoo.tools import str2bool

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    donation_project_id = fields.Many2one('donation.projects', string="Linked Donation Project")

    def _set_done(self):
        """Hook into transaction confirmation to create donation.donor."""
        res = super()._set_done()

        for tx in self:
            if tx.donation_project_id:
                existing = self.env['donation.donor'].sudo().search([
                    ('sale_order_id', '=', tx.sale_order_id.id),
                    ('project_id', '=', tx.donation_project_id.id),
                ])
                if not existing:
                    self.env['donation.donor'].sudo().create({
                        'partner_id': tx.partner_id.id,
                        'amount': tx.amount,
                        'project_id': tx.donation_project_id.id,
                        'product_id': tx.sale_order_line_ids.product_id.id if tx.sale_order_line_ids else False,
                        'currency_id': tx.currency_id.id,
                        'company_id': tx.company_id.id,
                        'sale_order_id': tx.sale_order_id.id,
                    })
        return res

    def _check_amount_and_confirm_order(self):
        """Override to disable email sending for website/donation orders to avoid template errors."""
        # For website orders, confirm without sending email to avoid template rendering errors
        confirmed_orders = self.env['sale.order']
        for tx in self:
            if len(tx.sale_order_ids) == 1:
                quotation = tx.sale_order_ids.filtered(lambda so: so.state in ('draft', 'sent'))
                _logger.info(f"Checking order {quotation.id if quotation else 'None'}, state: {quotation.state if quotation else 'N/A'}, amount_reached: {quotation._is_confirmation_amount_reached() if quotation else 'N/A'}")
                
                if quotation and quotation._is_confirmation_amount_reached():
                    # For website orders, disable email to avoid template errors
                    if quotation.website_id:
                        _logger.info(f"Attempting to confirm website order {quotation.id}, current state: {quotation.state}")
                        
                        # Check for confirmation errors before attempting
                        error_msg = quotation._confirmation_error_message()
                        if error_msg:
                            _logger.error(f"Order {quotation.id} cannot be confirmed: {error_msg}")
                            continue
                        
                        try:
                            # Use action_confirm with context to bypass email sending
                            # This avoids any template rendering issues
                            result = quotation.with_context(send_email=False, tracking_disable=True).action_confirm()
                            _logger.info(f"Order {quotation.id} action_confirm() returned: {result}")
                            
                            # Refresh to get updated state - need to browse again to get fresh data
                            quotation.invalidate_recordset(['state'])
                            quotation = self.env['sale.order'].browse(quotation.id)
                            _logger.info(f"Order {quotation.id} confirmation called, new state: {quotation.state}")
                            
                            if quotation.state == 'sale':
                                confirmed_orders |= quotation
                                _logger.info(f"Order {quotation.id} confirmed successfully, state is now 'sale'")
                            else:
                                _logger.error(f"Order {quotation.id} confirmation failed, state is still '{quotation.state}'")
                                # Try to get more info about why it failed
                                _logger.error(f"Order {quotation.id} details: state={quotation.state}, amount_total={quotation.amount_total}, confirmation_amount={quotation._is_confirmation_amount_reached()}")
                        except Exception as e:
                            _logger.error(f"Exception while confirming order {quotation.id}: {str(e)}", exc_info=True)
                            # Re-raise to ensure we know the order wasn't confirmed
                            raise
                    else:
                        # For non-website orders, use standard flow with email
                        _logger.info(f"Confirming non-website order {quotation.id}")
                        quotation.with_context(send_email=True).action_confirm()
                        quotation.invalidate_recordset(['state'])
                        if quotation.state == 'sale':
                            confirmed_orders |= quotation
                            _logger.info(f"Non-website order {quotation.id} confirmed successfully")
                        else:
                            _logger.error(f"Non-website order {quotation.id} confirmation failed, state: {quotation.state}")
                elif quotation:
                    _logger.warning(f"Order {quotation.id} cannot be confirmed: state={quotation.state}, amount_reached={quotation._is_confirmation_amount_reached()}")
        return confirmed_orders

    def _post_process(self):
        """Override to ensure automatic invoice creation and posting for donation orders.
        
        IMPORTANT: The sale module's _post_process() has special handling for 'done' transactions:
        1. It calls _check_amount_and_confirm_order() FIRST (which we override)
        2. Then it creates invoices if auto_invoice is enabled
        3. Then it calls super()._post_process() to post invoices
        4. Then it sends invoices if auto_invoice is enabled
        
        We need to ensure this flow runs correctly, so we call the sale module's _post_process()
        directly for 'done' transactions, and handle other states normally.
        """
        # Separate transactions by state
        pending_txs = self.filtered(lambda tx: tx.state == 'pending')
        authorized_txs = self.filtered(lambda tx: tx.state == 'authorized')
        done_txs = self.filtered(lambda tx: tx.state == 'done')
        other_txs = self.filtered(lambda tx: tx.state not in ['pending', 'authorized', 'done'])
        
        # For non-done transactions, call parent normally
        if other_txs:
            super(PaymentTransaction, other_txs)._post_process()
        
        # Handle pending transactions (sale module logic)
        if pending_txs:
            pending_txs.filtered(lambda tx: tx.state == 'pending')._post_process()

        # Handle authorized transactions (sale module logic)
        if authorized_txs:
            authorized_txs.filtered(lambda tx: tx.state == 'authorized')._post_process()
        
        # Handle done transactions - this is where order confirmation happens
        if done_txs:
            # For done transactions, we need to replicate the sale module's _post_process() logic
            # because calling it directly might not use our overrides correctly.
            # The sale module's flow for done transactions:
            # 1. Calls _check_amount_and_confirm_order() (our override will be used)
            # 2. Creates invoices if auto_invoice is enabled
            # 3. Calls super()._post_process() to post invoices
            # 4. Sends invoices if auto_invoice is enabled
            
            for done_tx in done_txs:
                # Step 1: Confirm the order (this calls our overridden _check_amount_and_confirm_order)
                confirmed_orders = done_tx._check_amount_and_confirm_order()
                _logger.info(f"Confirmed orders for transaction {done_tx.id}: {confirmed_orders.ids}")
                
                # Skip sending payment succeeded email for website orders to avoid template errors
                # (done_tx.sale_order_ids - confirmed_orders)._send_payment_succeeded_for_order_mail()
                
                # Step 2: Create invoices if auto_invoice is enabled
                auto_invoice = str2bool(
                    self.env['ir.config_parameter'].sudo().get_param('sale.automatic_invoice')
                )
                if auto_invoice:
                    # Invoice the sales orders of confirmed transactions
                    done_tx._invoice_sale_orders()
                
                # Step 3: Post invoices directly without going through sale module's _post_process
                # to avoid email sending errors that cause template rendering issues
                # Post all draft invoices linked to this transaction
                for invoice in done_tx.invoice_ids:
                    if invoice.state == 'draft':
                        try:
                            _logger.info(f"Posting invoice {invoice.id} for transaction {done_tx.id}")
                            invoice.action_post()
                            _logger.info(f"Invoice {invoice.id} posted successfully")
                        except Exception as e:
                            _logger.error(f"Failed to post invoice {invoice.id}: {str(e)}", exc_info=True)
                
                # Step 3.5: Create payment and link to invoice using account_payment module's logic
                # The account_payment module's _post_process creates payments for done transactions
                # We need to replicate this logic here to create the payment and reconcile it
                if done_tx.invoice_ids and done_tx.operation != 'validation' and not done_tx.payment_id:
                    try:
                        _logger.info(f"Creating payment for transaction {done_tx.id} with invoices {done_tx.invoice_ids.ids}")
                        # Call _create_payment from account_payment module
                        # This will create the payment, post it, and reconcile with invoices
                        done_tx_sudo = done_tx.sudo().with_company(done_tx.company_id)
                        payment = done_tx_sudo._create_payment()
                        _logger.info(f"Payment {payment.id} created and posted for transaction {done_tx.id}")
                    except Exception as e:
                        _logger.error(f"Failed to create payment for transaction {done_tx.id}: {str(e)}", exc_info=True)
                
                # Step 4: Send invoices if auto_invoice is enabled
                if auto_invoice:
                    done_tx._send_invoice()
            
            # Now handle invoice creation and posting for website orders (even if auto_invoice is disabled)
            for done_tx in done_txs:
                for order in done_tx.sale_order_ids:
                    # Only process website orders (donation orders) that are confirmed
                    if order.state == 'sale' and order.website_id:
                        _logger.info(f"Processing invoice for confirmed order {order.id}")
                        
                        # Force invoice creation even if auto_invoice is disabled
                        auto_invoice = str2bool(
                            self.env['ir.config_parameter'].sudo().get_param('sale.automatic_invoice')
                        )
                        if not auto_invoice or not done_tx.invoice_ids:
                            try:
                                _logger.info(f"Creating invoice for order {order.id}")
                                done_tx._invoice_sale_orders()
                                _logger.info(f"Invoice created for order {order.id}")
                            except Exception as e:
                                _logger.error(f"Failed to create invoice for order {order.id}: {str(e)}")
                        
                        # Post all draft invoices linked to this transaction
                        for invoice in done_tx.invoice_ids:
                            if invoice.state == 'draft':
                                try:
                                    _logger.info(f"Posting invoice {invoice.id} for order {order.id}")
                                    invoice.action_post()
                                    _logger.info(f"Invoice {invoice.id} posted successfully")
                                except Exception as e:
                                    _logger.error(f"Failed to post invoice {invoice.id}: {str(e)}")
                        
                        # Create payment and link to invoice if not already created
                        if not done_tx.payment_id and done_tx.invoice_ids and done_tx.operation != 'validation':
                            try:
                                _logger.info(f"Creating payment for transaction {done_tx.id} and invoice {done_tx.invoice_ids.ids}")
                                # Call _create_payment from account_payment module
                                # This will create the payment, post it, and reconcile with invoices
                                done_tx_sudo = done_tx.sudo().with_company(done_tx.company_id)
                                payment = done_tx_sudo._create_payment()
                                _logger.info(f"Payment {payment.id} created and posted for transaction {done_tx.id}")
                            except Exception as e:
                                _logger.error(f"Failed to create payment for transaction {done_tx.id}: {str(e)}", exc_info=True)
                        
                        # Note: Cart clearing is handled by shop_payment_validate route
                        # which calls request.website.sale_reset() after successful payment
                        # We don't need to clear it here as it's done in the standard flow