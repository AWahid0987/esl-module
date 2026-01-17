from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import html2plaintext


class WhatsappSendWizard(models.TransientModel):
    _name = "whatsapp.send.wizard"
    _description = "Send WhatsApp Wizard"

    model = fields.Char(readonly=True)
    res_id = fields.Integer(readonly=True)
    partner_id = fields.Many2one("res.partner", string="Recipient")
    phone = fields.Char(string="Phone")
    template_id = fields.Many2one(
        "mail.template",
        string="Template",
        domain="[('model', '=', model)]",
    )
    body = fields.Text(string="Message", required=True)

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        model = self.env.context.get("default_model") or self.env.context.get("active_model")
        res_id = self.env.context.get("default_res_id") or self.env.context.get("active_id")
        partner_id = self.env.context.get("default_partner_id")
        if model and res_id:
            record = self.env[model].browse(res_id).exists()
            if record and not partner_id:
                if model == "res.partner":
                    partner_id = record.id
                elif "partner_id" in record:
                    partner_id = record.partner_id.id
        if partner_id:
            partner = self.env["res.partner"].browse(partner_id)
            values.setdefault("partner_id", partner.id)
            values.setdefault("phone", partner.mobile or partner.phone or "")
        if model:
            values.setdefault("model", model)
        if res_id:
            values.setdefault("res_id", res_id)
        template_id = self.env.context.get("default_template_id")
        if template_id:
            values.setdefault("template_id", template_id)
            values.setdefault("body", self._render_template_body(template_id, model, res_id))
        return values

    @api.onchange("template_id", "model", "res_id")
    def _onchange_template_id(self):
        if self.template_id and self.model and self.res_id:
            self.body = self._render_template_body(
                self.template_id.id, self.model, self.res_id
            )

    def action_send(self):
        self.ensure_one()
        if not self.phone:
            raise UserError(_("Recipient phone number is missing."))
        if not self.body:
            raise UserError(_("Message body is empty."))
        message = self.env["whatsapp.message"].create(
            {
                "model": self.model,
                "res_id": self.res_id,
                "partner_id": self.partner_id.id if self.partner_id else False,
                "phone": self.phone,
                "body": self.body,
            }
        )
        message.action_send()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("WhatsApp"),
                "message": _("Message sent.") if message.state == "sent" else _("Message failed."),
                "sticky": False,
            },
        }

    def _render_template_body(self, template_id, model, res_id):
        template = self.env["mail.template"].browse(template_id)
        if not template or not model or not res_id:
            return ""
        if template.model and template.model != model:
            return ""
        body_html = template._render_field("body_html", [res_id]).get(res_id, "")
        return html2plaintext(body_html or "")
