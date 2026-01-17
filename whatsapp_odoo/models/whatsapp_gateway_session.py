import base64
import logging

import requests

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WhatsappGatewaySession(models.Model):
    _name = "whatsapp.gateway.session"
    _description = "WhatsApp Gateway Session"
    _inherit = ["whatsapp.gateway.mixin"]
    _order = "id desc"

    name = fields.Char(default="Gateway Session", required=True)
    state = fields.Selection(
        [("disconnected", "Disconnected"), ("connected", "Connected")],
        default="disconnected",
        readonly=True,
    )
    qr_image = fields.Image(readonly=True)
    qr_payload = fields.Text(readonly=True)
    last_sync = fields.Datetime(readonly=True)
    error = fields.Text(readonly=True)

    def action_fetch_qr(self):
        self.ensure_one()
        endpoint = self._gateway_get("qr_endpoint") or "/qr"
        payload = self._gateway_payload()
        data = self._gateway_request(endpoint, payload=payload, method="post")
        qr_image, qr_payload = self._extract_qr_data(data)
        if not qr_image and not qr_payload:
            raise UserError(_("QR data not found in gateway response."))
        self.write(
            {
                "qr_image": qr_image,
                "qr_payload": qr_payload,
                "last_sync": fields.Datetime.now(),
                "error": False,
            }
        )
        return True

    def action_check_status(self):
        self.ensure_one()
        endpoint = self._gateway_get("status_endpoint") or "/status"
        payload = self._gateway_payload()
        data = self._gateway_request(endpoint, payload=payload, method="get")
        state = self._parse_status(data)
        self.write(
            {
                "state": state,
                "last_sync": fields.Datetime.now(),
                "error": False,
            }
        )
        return True

    def _gateway_payload(self):
        payload = {}
        instance_id = self._gateway_get("instance_id")
        if instance_id:
            payload["instance_id"] = instance_id
        return payload

    def _parse_status(self, data):
        status = (data or {}).get("status") or (data or {}).get("state") or ""
        status = str(status).lower()
        if status in ("connected", "ready", "online"):
            return "connected"
        return "disconnected"

    def _extract_qr_data(self, data):
        data = data or {}
        qr_value = (
            data.get("qr")
            or data.get("qr_image")
            or data.get("qr_image_base64")
            or data.get("qrcode")
        )
        if qr_value and isinstance(qr_value, str) and qr_value.startswith("http"):
            try:
                response = requests.get(qr_value, timeout=20)
                if response.status_code < 400:
                    return base64.b64encode(response.content), False
            except Exception:
                _logger.exception("Failed to download QR image")
        if qr_value and isinstance(qr_value, str):
            # assume base64 data
            return qr_value, False
        qr_payload = data.get("qr_data") or data.get("payload")
        if qr_payload:
            return False, str(qr_payload)
        return False, False
