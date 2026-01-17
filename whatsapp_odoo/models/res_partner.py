from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def action_open_whatsapp_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Send WhatsApp",
            "res_model": "whatsapp.send.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_model": self._name,
                "default_res_id": self.id,
                "default_partner_id": self.id,
            },
        }
