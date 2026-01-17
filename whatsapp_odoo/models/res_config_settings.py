import requests

from odoo import _, fields, models
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    whatsapp_provider = fields.Selection(
        [("cloud", "Meta WhatsApp Cloud API"), ("gateway", "WhatsApp QR Gateway")],
        default="cloud",
        config_parameter="whatsapp_odoo.provider",
        string="WhatsApp Provider",
    )
    whatsapp_base_url = fields.Char(
        default="https://graph.facebook.com/v19.0",
        config_parameter="whatsapp_odoo.base_url",
        string="Base URL",
    )
    whatsapp_phone_number_id = fields.Char(
        config_parameter="whatsapp_odoo.phone_number_id",
        string="Phone Number ID",
    )
    whatsapp_access_token = fields.Char(
        config_parameter="whatsapp_odoo.access_token",
        string="Access Token",
    )
    whatsapp_default_country_code = fields.Char(
        config_parameter="whatsapp_odoo.default_country_code",
        string="Default Country Code",
        help="Used to format phone numbers that do not start with +.",
    )
    whatsapp_gateway_base_url = fields.Char(
        config_parameter="whatsapp_odoo.gateway_base_url",
        string="Gateway Base URL",
    )
    whatsapp_gateway_instance_id = fields.Char(
        config_parameter="whatsapp_odoo.gateway_instance_id",
        string="Gateway Instance ID",
    )
    whatsapp_gateway_api_key = fields.Char(
        config_parameter="whatsapp_odoo.gateway_api_key",
        string="Gateway API Key",
    )
    whatsapp_gateway_api_header = fields.Char(
        config_parameter="whatsapp_odoo.gateway_api_header",
        string="API Header",
        default="Authorization",
        help="Header name used for API key (e.g. Authorization, X-API-KEY).",
    )
    whatsapp_gateway_api_prefix = fields.Char(
        config_parameter="whatsapp_odoo.gateway_api_prefix",
        string="API Prefix",
        default="Bearer",
        help="Prefix added before API key (e.g. Bearer). Leave empty for raw key.",
    )
    whatsapp_gateway_qr_endpoint = fields.Char(
        config_parameter="whatsapp_odoo.gateway_qr_endpoint",
        string="QR Endpoint",
        default="/qr",
    )
    whatsapp_gateway_status_endpoint = fields.Char(
        config_parameter="whatsapp_odoo.gateway_status_endpoint",
        string="Status Endpoint",
        default="/status",
    )
    whatsapp_gateway_send_endpoint = fields.Char(
        config_parameter="whatsapp_odoo.gateway_send_endpoint",
        string="Send Endpoint",
        default="/send",
    )

    def action_check_gateway_status(self):
        self.ensure_one()
        params = self.env["ir.config_parameter"].sudo()
        base_url = self.whatsapp_gateway_base_url or params.get_param(
            "whatsapp_odoo.gateway_base_url", ""
        )
        if not base_url:
            raise UserError(_("Gateway Base URL is not configured."))
        status_endpoint = self.whatsapp_gateway_status_endpoint or params.get_param(
            "whatsapp_odoo.gateway_status_endpoint", "/status"
        )
        url = (
            status_endpoint
            if status_endpoint.startswith("http")
            else f"{base_url.rstrip('/')}/{status_endpoint.lstrip('/')}"
        )
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            raise UserError(str(exc)) from exc
        status = (data or {}).get("status", "unknown")
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("WhatsApp Gateway"),
                "message": _("Status: %s") % status,
                "sticky": False,
            },
        }
