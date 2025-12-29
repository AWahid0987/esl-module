# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for sale_order in self:
            for line in sale_order.order_line:
                product = line.product_id
                amount = line.price_total

                # Find the project linked with the product
                project = self.env["donation.projects"].search([("product_id", "=", product.id)], limit=1)
                if not project:
                    continue  # Or log warning

                # Create donation record
                self.env["donation.donor"].create(
                    {
                        "partner_id": sale_order.partner_id.id,
                        "project_id": project.id,
                        "amount": amount,
                        "product_id": product.id,
                        "sale_order_id": sale_order.id,
                        
                    }
                )
        return res

    def unlink(self):
        for sale_order in self:
            # Delete related donation records
            donations = self.env["donation.donor"].search([("sale_order_id", "=", sale_order.id)])
            donations.unlink()
        return super(SaleOrder, self).unlink()
