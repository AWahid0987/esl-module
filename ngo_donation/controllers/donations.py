from odoo import http, _
from odoo.exceptions import ValidationError

from odoo.addons.payment.controllers import portal as payment_portal
from odoo.addons.payment import utils as payment_utils


class Donations(http.Controller):
    @http.route("/my/donation", type="http", auth="public", website=True)
    def index(self, **kw):

        # Filter donations based on the logged-in user
        partner = http.request.env.user.partner_id
        if partner:
            donations = http.request.env["donation.donor"].sudo().search([("partner_id", "=", partner.id)])
        else:
            donations = []
        total_donations = sum(donations.mapped("amount"))
        return http.request.render(
            "ngo_donation.portal_donations_view_id", {"donations": donations, "total_donations": total_donations}
        )

    @http.route('/donation/projects', type='http', auth='public', website=True)
    def list_projects(self):
        projects = http.request.env['donation.projects'].sudo().search([]) #[('stage', '=', 'in_progress')]
        return http.request.render('ngo_donation.website_donation_projects', {
            'projects': projects
        })
        
class PaymentPortal(payment_portal.PaymentPortal):

    @http.route('/donation/transaction/<minimum_amount>', type='json', auth='public', website=True, sitemap=False)
    def donation_transaction(self, amount, currency_id, partner_id, access_token, minimum_amount=0, **kwargs):
        _logger = http.logging.getLogger(__name__)
        _logger.info("\n\n\n[INFO] donation_transaction called with kwargs: %s", kwargs)

        # 🧠 Extract & validate project_id
        project_id = int(kwargs.get('project_id') or http.request.httprequest.form.get('project_id') or 0)
        _logger.info("\n\n\n[INFO] Using donation project_id: %s", project_id)
        project = http.request.env['donation.projects'].sudo().browse(project_id)

        if project_id and (not project):
            raise ValidationError(_("Invalid or inactive donation project."))

        # 👤 Handle public or logged-in partner
        use_public_partner = http.request.env.user._is_public() or not partner_id
        if use_public_partner:
            details = kwargs.get('partner_details', {})
            if not details.get('name'):
                raise ValidationError(_('Name is required.'))
            if not details.get('email'):
                raise ValidationError(_('Email is required.'))
            if not details.get('country_id'):
                raise ValidationError(_('Country is required.'))
            partner_id = http.request.website.user_id.partner_id.id
            del kwargs['partner_details']
        else:
            partner_id = http.request.env.user.partner_id.id

        # ✅ Validate transaction kwargs
        self._validate_transaction_kwargs(kwargs, additional_allowed_keys=[
            'donation_comment', 'donation_recipient_email', 'partner_details', 'reference_prefix', 'project_id'
        ])
        if use_public_partner:
            kwargs['custom_create_values'] = {'tokenize': False}

        # 💳 Create transaction
        tx_sudo = self._create_transaction(
            amount=amount,
            currency_id=currency_id,
            partner_id=partner_id,
            **kwargs
        )
        tx_sudo.is_donation = True

        # 🧩 Attach donation project
        if project_id:
            tx_sudo.donation_project_id = project_id

        # 👤 Set partner info
        if use_public_partner:
            tx_sudo.update({
                'partner_name': details['name'],
                'partner_email': details['email'],
                'partner_country_id': int(details['country_id']),
            })
        elif not tx_sudo.partner_country_id and 'partner_details' in kwargs:
            tx_sudo.partner_country_id = int(kwargs['partner_details']['country_id'])

        # 🔁 Recompute landing route (important!)
        access_token = payment_utils.generate_access_token(
            tx_sudo.partner_id.id, tx_sudo.amount, tx_sudo.currency_id.id
        )
        self._update_landing_route(tx_sudo, access_token)

        # 📬 Send email
        recipient_email = kwargs.get('donation_recipient_email')
        comment = kwargs.get('donation_comment')
        tx_sudo._send_donation_email(True, comment, recipient_email)

        # ✅ Return processing values
        return tx_sudo._get_processing_values()