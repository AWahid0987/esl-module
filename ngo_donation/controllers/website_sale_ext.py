from odoo import http
import json
from datetime import datetime

from werkzeug.exceptions import Forbidden, NotFound
from werkzeug.urls import url_decode, url_encode, url_parse

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.fields import Command
from odoo.http import request, route
from odoo.osv import expression
from odoo.tools import clean_context, float_round, groupby, lazy, single_email_re, str2bool, SQL
from odoo.tools.json import scriptsafe as json_scriptsafe
from odoo.tools.translate import _

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment.controllers import portal as payment_portal
from odoo.addons.portal.controllers.portal import _build_url_w_params
from odoo.addons.sale.controllers import portal as sale_portal
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website.models.ir_http import sitemap_qs2dom

# Import the original WebsiteSale controller
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleInherit(WebsiteSale):
    
    @route('/website/get_donation_translations', type='json', auth='public', website=True)
    def get_donation_translations_json(self, lang=None):
        """JSON endpoint to get donation translations for current language"""
        if not lang:
            lang = request.env.context.get('lang') or request.env.user.lang or 'en_US'
        
        website = request.website
        translations = website.get_donation_translations()
        return translations
    
    def _get_donation_translations(self):
        """Helper method to get translated donation strings"""
        return {
            'donation_amount_label': _('Donation Amount:'),
            'donation_amount_help': _('Enter any amount'),
            'thank_you_donation': _('Thank you for your donation.'),
            'donation': _('Donation'),
            'donation_summary': _('Donation summary'),
        }
    
    @route(['/shop/cart/update_json'], type='json', auth="public", methods=['POST'], website=True)
    def cart_update_json(
            self, product_id, line_id=None, add_qty=None, set_qty=None, display=True,
            product_custom_attribute_values=None, no_variant_attribute_value_ids=None, **kwargs
    ):
        """
        This route is called :
            - When changing quantity from the cart.
            - When adding a product from the wishlist.
            - When adding a product to cart on the same page (without redirection).
        """
        order = request.website.sale_get_order(force_create=True)
        if order.state != 'draft':
            request.website.sale_reset()
            if kwargs.get('force_create'):
                order = request.website.sale_get_order(force_create=True)
            else:
                return {}

        if product_custom_attribute_values:
            product_custom_attribute_values = json_scriptsafe.loads(product_custom_attribute_values)

        # old API, will be dropped soon with product configurator refactorings
        no_variant_attribute_values = kwargs.pop('no_variant_attribute_values', None)
        if no_variant_attribute_values and no_variant_attribute_value_ids is None:
            no_variants_attribute_values_data = json_scriptsafe.loads(no_variant_attribute_values)
            no_variant_attribute_value_ids = [
                int(ptav_data['value']) for ptav_data in no_variants_attribute_values_data
            ]

        values = order._cart_update(
            product_id=product_id,
            line_id=line_id,
            add_qty=add_qty,
            set_qty=set_qty,
            product_custom_attribute_values=product_custom_attribute_values,
            no_variant_attribute_value_ids=no_variant_attribute_value_ids,
            **kwargs
        )
        # If the line is a combo product line, and it already has combo items, we need to update
        # the combo item quantities as well.
        line = request.env['sale.order.line'].browse(values['line_id'])
        line.sudo().write({'price_unit': float(request.cookies['donation_amount'])})
        if line.product_type == 'combo' and line.linked_line_ids:
            for linked_line_id in line.linked_line_ids:
                if values['quantity'] != linked_line_id.product_uom_qty:
                    order._cart_update(
                        product_id=linked_line_id.product_id.id,
                        line_id=linked_line_id.id,
                        set_qty=values['quantity'],
                    )

        values['notification_info'] = self._get_cart_notification_information(order, [values['line_id']])
        values['notification_info']['warning'] = values.pop('warning', '')
        request.session['website_sale_cart_quantity'] = order.cart_quantity

        if not order.cart_quantity:
            request.website.sale_reset()
            return values

        values['cart_quantity'] = order.cart_quantity
        values['minor_amount'] = payment_utils.to_minor_currency_units(
            order.amount_total, order.currency_id
        )
        values['amount'] = order.amount_total

        if not display:
            return values

        values['cart_ready'] = order._is_cart_ready()
        values['website_sale.cart_lines'] = request.env['ir.ui.view']._render_template(
            "website_sale.cart_lines", {
                'website_sale_order': order,
                'date': fields.Date.today(),
                'suggested_products': order._cart_accessories()
            }
        )
        values['website_sale.total'] = request.env['ir.ui.view']._render_template(
            "website_sale.total", {
                'website_sale_order': order,
            }
        )
        return values

    @route(['/shop/confirm_order'], type='http', auth="public", website=True, sitemap=False)
    def shop_confirm_order(self, **post):
        order_sudo = request.website.sale_get_order()

        if redirection := self._check_cart_and_addresses(order_sudo):
            return redirection

        order_sudo._recompute_taxes()
        order_sudo._recompute_prices()
        
        # Check if coming from donation payment page
        is_from_donation = (
            request.httprequest.referrer and '/shop/donate_payment' in request.httprequest.referrer
        ) or post.get('from_donation') == 'true'
        
        extra_step = request.website.viewref('website_sale.extra_info')
        if extra_step.active:
            if is_from_donation:
                return request.redirect("/shop/extra_info?from_donation=true")
            return request.redirect("/shop/extra_info")

        # Redirect back to donation payment page if coming from there
        if is_from_donation:
            return request.redirect("/shop/donate_payment")

        return request.redirect("/shop/payment")

    @route(['/shop/donate_payment'], type='http', auth="public", methods=['GET', 'POST'], website=True, sitemap=False)
    def shop_donate_payment(self, product_id=None, add_qty=1, set_qty=0, product_custom_attribute_values=None,
                           no_variant_attribute_value_ids=None, **post):
        """
        Combined donation payment page that:
        1. Updates the cart if product_id is provided (only once, not on refresh)
        2. Shows delivery address form + payment methods on the same page
        """
        # Update cart if product_id is provided (from Donate button)
        # Use session flag to prevent duplicate cart updates on page refresh
        if product_id:
            sale_order = request.website.sale_get_order(force_create=True)
            if sale_order.state != 'draft':
                request.session['sale_order_id'] = None
                sale_order = request.website.sale_get_order(force_create=True)

            # Check if we've already processed this product for this session
            # Use a session key that combines product_id and order_id to track if product was already added
            session_key = f'donation_product_{product_id}_order_{sale_order.id}'
            already_processed = request.session.get(session_key, False)
            
            # Only update cart if not already processed
            if not already_processed:
                if product_custom_attribute_values:
                    product_custom_attribute_values = json_scriptsafe.loads(product_custom_attribute_values)

                # old API support
                no_variant_attribute_values = post.pop('no_variant_attribute_values', None)
                if no_variant_attribute_values and no_variant_attribute_value_ids is None:
                    no_variants_attribute_values_data = json_scriptsafe.loads(no_variant_attribute_values)
                    no_variant_attribute_value_ids = [
                        int(ptav_data['value']) for ptav_data in no_variants_attribute_values_data
                    ]

                sale_order._cart_update(
                    product_id=int(product_id),
                    add_qty=add_qty,
                    set_qty=set_qty,
                    product_custom_attribute_values=product_custom_attribute_values,
                    no_variant_attribute_value_ids=no_variant_attribute_value_ids,
                    **post
                )

                # Mark as processed in session
                request.session[session_key] = True

                # Update donation amount if provided
                if 'donation_amount' in request.cookies:
                    try:
                        donation_amount = float(request.cookies.get('donation_amount', 0))
                        if donation_amount > 0:
                            line = sale_order.order_line.filtered(lambda l: l.product_id.id == int(product_id))
                            if line:
                                line.sudo().write({'price_unit': donation_amount})
                    except (ValueError, TypeError):
                        pass

                request.session['website_sale_cart_quantity'] = sale_order.cart_quantity
            else:
                # If already processed, just update donation amount if cookie changed
                if 'donation_amount' in request.cookies:
                    try:
                        donation_amount = float(request.cookies.get('donation_amount', 0))
                        if donation_amount > 0:
                            line = sale_order.order_line.filtered(lambda l: l.product_id.id == int(product_id))
                            if line and line.price_unit != donation_amount:
                                line.sudo().write({'price_unit': donation_amount})
                    except (ValueError, TypeError):
                        pass

        # Get the current order
        order_sudo = request.website.sale_get_order()

        # Check cart validity
        if redirection := self._check_cart(order_sudo):
            return redirection

        # Prepare checkout values (delivery addresses, billing addresses, etc.)
        checkout_values = self._prepare_checkout_page_values(order_sudo, **post)

        # Load delivery methods if needed
        if order_sudo._has_deliverable_products():
            available_dms = order_sudo._get_delivery_methods()
            checkout_values['delivery_methods'] = available_dms
            if delivery_method := order_sudo._get_preferred_delivery_method(available_dms):
                rate = delivery_method.rate_shipment(order_sudo)
                if (
                    not order_sudo.carrier_id
                    or not rate.get('success')
                    or order_sudo.amount_delivery != rate['price']
                ):
                    order_sudo._set_delivery_method(delivery_method, rate=rate)

        # Prepare address form values for anonymous users
        ResCountrySudo = request.env['res.country'].sudo()
        partner_sudo = order_sudo.partner_id
        country_sudo = partner_sudo.country_id
        if not country_sudo:
            if order_sudo._is_anonymous_cart():
                if request.geoip.country_code:
                    country_sudo = ResCountrySudo.search([
                        ('code', '=', request.geoip.country_code),
                    ], limit=1)
                else:
                    country_sudo = order_sudo.website_id.user_id.country_id
            else:
                country_sudo = partner_sudo.country_id

        state_id = partner_sudo.state_id.id if partner_sudo.state_id else None

        # Prepare payment values
        payment_values = self._get_shop_payment_values(order_sudo, **post)
        payment_values['only_services'] = order_sudo and order_sudo.only_services
        # Enable submit button for payment form
        payment_values['display_submit_button'] = True
        payment_values['submit_button_label'] = _('Complete Donation')

        # Merge both sets of values
        render_values = {
            **checkout_values,
            **payment_values,
            'website_sale_order': order_sudo,
            'order': order_sudo,
            'partner': order_sudo.partner_invoice_id,
            'json_pickup_location_data': json.dumps(order_sudo.pickup_location_data or {}),
            # Address form values for anonymous users
            'countries': ResCountrySudo.search([]),
            'country': country_sudo,
            'country_states': country_sudo.state_ids if country_sudo else request.env['res.country.state'],
            'state_id': state_id,
        }

        # Check for errors
        if render_values.get('errors'):
            render_values.pop('payment_methods_sudo', '')
            render_values.pop('tokens_sudo', '')

        return request.render("ngo_donation.donate_payment", render_values)

    def _get_mandatory_billing_address_fields(self, country_sudo):
        """Override to exclude phone and state_id for donation payments."""
        # Get the standard mandatory fields
        field_names = super()._get_mandatory_billing_address_fields(country_sudo)
        
        # Check if this is from donation payment page
        is_from_donation = (
            request.httprequest.referrer and '/shop/donate_payment' in request.httprequest.referrer
        )
        
        # Remove phone and state_id for donation payments
        if is_from_donation:
            field_names.discard('phone')
            field_names.discard('state_id')
        
        return field_names

    def _validate_address_values(
        self, address_values, partner_sudo, address_type, use_delivery_as_billing,
        required_fields, is_main_address=False, **extra_form_data
    ):
        """Override to make phone and state_id optional for donation payments."""
        # Check if this is from donation payment page
        is_from_donation = (
            request.httprequest.referrer and '/shop/donate_payment' in request.httprequest.referrer
        )
        
        # Call parent validation first
        invalid_fields, missing_fields, error_messages = super()._validate_address_values(
            address_values, partner_sudo, address_type, use_delivery_as_billing,
            required_fields, is_main_address=is_main_address, **extra_form_data
        )
        
        # If from donation payment, remove phone and state_id from missing_fields
        if is_from_donation:
            if 'phone' in missing_fields:
                missing_fields.remove('phone')
            if 'state_id' in missing_fields:
                missing_fields.remove('state_id')
            # Also remove from invalid_fields if present
            if 'phone' in invalid_fields:
                invalid_fields.remove('phone')
            if 'state_id' in invalid_fields:
                invalid_fields.remove('state_id')
        
        return invalid_fields, missing_fields, error_messages

    @route(
        '/shop/address/submit', type='http', methods=['POST'], auth='public', website=True,
        sitemap=False
    )
    def shop_address_submit(
        self, partner_id=None, address_type='billing', use_delivery_as_billing=None, callback=None,
        required_fields=None, **form_data
    ):
        """ Override to handle callback for donation payment page and make state and phone optional """
        # If coming from donation payment page, exclude state_id and phone from required fields
        is_from_donation = (
            callback == '/shop/donate_payment' or 
            (request.httprequest.referrer and '/shop/donate_payment' in request.httprequest.referrer)
        )
        
        if is_from_donation:
            # Remove state_id and phone from required_fields if present
            if required_fields:
                required_list = [f.strip() for f in required_fields.split(',')]
                if 'state_id' in required_list:
                    required_list.remove('state_id')
                if 'phone' in required_list:
                    required_list.remove('phone')
                required_fields = ','.join(required_list)
            else:
                # If no required_fields provided, set it to only essential fields (excluding phone and state_id)
                required_fields = 'name,country_id'
        
        # Call parent method
        result = super().shop_address_submit(
            partner_id=partner_id,
            address_type=address_type,
            use_delivery_as_billing=use_delivery_as_billing,
            callback=callback or ('/shop/donate_payment' if is_from_donation else None),
            required_fields=required_fields,
            **form_data
        )
        
        # If callback is set to donation payment page, use it
        if is_from_donation:
            # Parse the JSON response and update callback if needed
            try:
                import json
                if isinstance(result, str):
                    response_data = json.loads(result)
                    if 'successUrl' in response_data:
                        response_data['successUrl'] = '/shop/donate_payment'
                        return json.dumps(response_data)
            except:
                pass
        
        return result
    
    def _get_shop_payment_errors(self, order):
        """Override to handle empty order recordset gracefully."""
        # If order is empty, return empty errors list
        if not order:
            return []
        
        # Call parent method for non-empty orders
        return super()._get_shop_payment_errors(order)

    @route(['/shop/confirmation'], type='http', auth="public", website=True, sitemap=False)
    def shop_payment_confirmation(self, **post):
        """Override to clear donation session flags and cookies after payment confirmation."""
        # Clear all donation session flags to allow new donations
        session_keys_to_clear = [key for key in request.session.keys() if key.startswith('donation_product_')]
        for key in session_keys_to_clear:
            del request.session[key]
        
        # Call parent to render confirmation page
        response = super().shop_payment_confirmation(**post)
        
        # Clear donation amount cookie
        if hasattr(response, 'set_cookie'):
            response.set_cookie('donation_amount', '', max_age=0, path='/')
        
        return response