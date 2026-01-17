import json
import logging

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import html2plaintext

_logger = logging.getLogger(__name__)


class WhatsappMessage(models.Model):
    _name = "whatsapp.message"
    _description = "WhatsApp Message"
    _inherit = ["whatsapp.gateway.mixin"]
    _order = "id desc"

    name = fields.Char(default="New", readonly=True)
    provider = fields.Selection(
        [("cloud", "Meta WhatsApp Cloud API")],
        default="cloud",
        required=True,
        readonly=True,
    )
    model = fields.Char(index=True)
    res_id = fields.Integer(index=True)
    partner_id = fields.Many2one("res.partner", ondelete="set null")
    phone = fields.Char(required=True)
    body = fields.Text(required=True)
    state = fields.Selection(
        [("draft", "Draft"), ("sent", "Sent"), ("failed", "Failed")],
        default="draft",
        required=True,
        readonly=True,
    )
    message_uid = fields.Char(readonly=True)
    error = fields.Text(readonly=True)
    sent_at = fields.Datetime(readonly=True)
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("whatsapp.message") or "WA/New"
                )
        return super().create(vals_list)

    def action_send(self):
        for message in self:
            message._send_message()
        return True

    def _send_message(self):
        self.ensure_one()
        if not self.phone or not self.body:
            raise UserError(_("Phone number and message are required."))

        provider = self._get_provider()
        if provider not in ("cloud", "gateway"):
            raise UserError(_("Unsupported WhatsApp provider."))

        if provider == "cloud":
            base_url = self._get_config("base_url")
            phone_number_id = self._get_config("phone_number_id")
            access_token = self._get_config("access_token")
            if not (base_url and phone_number_id and access_token):
                raise UserError(_("WhatsApp configuration is incomplete."))
        else:
            if not self._gateway_get("base_url"):
                raise UserError(_("WhatsApp gateway is not configured."))

        to_number = self._normalize_phone(self.phone)

        try:
            if provider == "cloud":
                payload = {
                    "messaging_product": "whatsapp",
                    "to": to_number,
                    "type": "text",
                    "text": {"body": self.body},
                }
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                }
                url = f"{base_url.rstrip('/')}/{phone_number_id}/messages"
                response = requests.post(
                    url, data=json.dumps(payload), headers=headers, timeout=15
                )
                if response.status_code < 200 or response.status_code >= 300:
                    raise UserError(response.text or _("WhatsApp send failed."))
                data = response.json()
                message_uid = ""
                if data.get("messages"):
                    message_uid = data["messages"][0].get("id", "")
            else:
                payload = {
                    "to": to_number,
                    "message": self.body,
                }
                instance_id = self._gateway_get("instance_id")
                if instance_id:
                    payload["instance_id"] = instance_id
                endpoint = self._gateway_get("send_endpoint") or "/send"
                data = self._gateway_request(endpoint, payload=payload, method="post")
                message_uid = (
                    data.get("message_id")
                    or data.get("id")
                    or data.get("message")
                    or ""
                )
            self.write(
                {
                    "state": "sent",
                    "message_uid": message_uid,
                    "sent_at": fields.Datetime.now(),
                    "error": False,
                    "phone": to_number,
                }
            )
            self._post_to_chatter(success=True)
        except Exception as exc:
            _logger.exception("WhatsApp send failed")
            self.write(
                {
                    "state": "failed",
                    "error": str(exc),
                    "sent_at": fields.Datetime.now(),
                    "phone": to_number,
                }
            )
            self._post_to_chatter(success=False)

    def _post_to_chatter(self, success):
        if not self.model or not self.res_id:
            return
        record = self.env[self.model].browse(self.res_id).exists()
        if not record:
            return
        status = _("Sent") if success else _("Failed")
        body_text = html2plaintext(self.body or "")
        body = _(
            "<p><b>WhatsApp</b>: %(status)s</p><p>To: %(phone)s</p><p>%(body)s</p>"
        ) % {
            "status": status,
            "phone": self.phone or "",
            "body": body_text.replace("\n", "<br/>"),
        }
        if not success and self.error:
            body += _("<p>Error: %(error)s</p>") % {"error": self.error}
        record.message_post(body=body, message_type="comment", subtype_xmlid="mail.mt_note")

    def _normalize_phone(self, phone):
        phone = (phone or "").strip().replace(" ", "")
        if phone.startswith("+"):
            return phone
        if phone.startswith("00"):
            return "+" + phone[2:]
        country_code = self._get_config("default_country_code")
        if country_code:
            return f"+{country_code}{phone}"
        return phone

    def _get_config(self, key):
        params = self.env["ir.config_parameter"].sudo()
        return params.get_param(f"whatsapp_odoo.{key}", "")

    def _get_provider(self):
        provider = self._get_config("provider")
        if provider:
            return provider
        if self._gateway_get("base_url"):
            return "gateway"
        return "cloud"
