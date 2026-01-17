import logging

import requests

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WhatsappGatewayMixin(models.AbstractModel):
    _name = "whatsapp.gateway.mixin"
    _description = "WhatsApp Gateway Mixin"

    def _gateway_get(self, key):
        params = self.env["ir.config_parameter"].sudo()
        return params.get_param(f"whatsapp_odoo.gateway_{key}", "")

    def _gateway_build_url(self, endpoint):
        if not endpoint:
            raise UserError(_("Gateway endpoint is missing."))
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        base_url = self._gateway_get("base_url")
        if not base_url:
            raise UserError(_("Gateway base URL is missing."))
        return f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"

    def _gateway_headers(self):
        headers = {"Content-Type": "application/json"}
        api_key = self._gateway_get("api_key")
        api_header = self._gateway_get("api_header") or "Authorization"
        api_prefix = self._gateway_get("api_prefix")
        if api_key:
            value = api_key if not api_prefix else f"{api_prefix} {api_key}"
            headers[api_header] = value
        return headers

    def _gateway_request(self, endpoint, payload=None, method="post"):
        url = self._gateway_build_url(endpoint)
        headers = self._gateway_headers()
        method = (method or "post").lower()
        try:
            if method == "get":
                response = requests.get(
                    url, params=payload or {}, headers=headers, timeout=20
                )
            else:
                response = requests.post(
                    url, json=payload or {}, headers=headers, timeout=20
                )
        except Exception as exc:
            _logger.exception("Gateway request failed")
            raise UserError(str(exc)) from exc

        if response.status_code >= 400:
            raise UserError(response.text or _("Gateway request failed."))
        try:
            return response.json()
        except ValueError:
            return {}
