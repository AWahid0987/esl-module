from odoo import models, api, _

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.model
    def create(self, vals):
        # Call the super to create the payment first
        payment = super(AccountPayment, self).create(vals)

        # Find the related invoice(s)
        invoice = payment.reconciled_invoice_ids

        if invoice:
            for inv in invoice:
                partner = inv.partner_id
                user = partner.user_ids[0] if partner.user_ids else None

                # Compose the message
                company_name = self.env.user.company_id.name  # Your company's name, e.g., "Lahore Fund"
                partner_name = partner.name  # The partner's name, e.g., "Tech Society"
                amount = payment.amount  # The payment amount
                payment_date = payment.payment_date  # The payment date

                message = _("%s acknowledges the cash receipt of Rs. %.2f from %s on %s.") % (
                    company_name, amount, partner_name, payment_date.strftime('%d.%m.%Y')
                )

                # Notify the user associated with the partner
                if user:
                    user.message_post(body=message, subject="Invoice Payment Notification")

        return payment