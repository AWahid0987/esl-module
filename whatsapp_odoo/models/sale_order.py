from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_open_whatsapp_wizard(self):
        self.ensure_one()
        partner = self.partner_id
        return {
            "type": "ir.actions.act_window",
            "name": "Send WhatsApp",
            "res_model": "whatsapp.send.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_model": self._name,
                "default_res_id": self.id,
                "default_partner_id": partner.id if partner else False,
            },
        }
