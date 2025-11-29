# -*- coding: utf-8 -*-
import math

from odoo import models, fields, api, _
from odoo.exceptions import UserError

# ==================== CONSTANTS ====================
ACRE_TO_MARLA = 37.5
FIVE_MARLA = 5.0
TEN_MARLA = 10.0
FOUR_MARLA_C = 4.0
EIGHT_MARLA_C = 8.0


class LandProject(models.Model):
    _name = "land.project"
    _description = "Land Project / Block"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    # ---------------- Basic Info ----------------
    name = fields.Char(required=True, default=lambda self: _("New Project"), tracking=True)
    total_acres = fields.Float(string="Total Acres", required=True, tracking=True)
    total_marla = fields.Float(string="Total Marla", compute="_compute_totals", store=True)
    remaining_marla = fields.Float(string="Remaining (Marla)", compute="_compute_remaining_marla", store=True)

    project_type = fields.Selection([
        ('', ''),
        ('compact', 'Compact'),
        ('non_compact', 'Non Compact')
    ], string="Project Type", required=True, default='compact')
    security_pct = fields.Float(string="Security %", compute="_compute_security_pct", store=True)

    # ratio fields used for plot generation
    ratio_r5 = fields.Float(string="Ratio 5 Marla", compute="_compute_ratios", store=True, digits=(16, 4))
    ratio_r10 = fields.Float(string="Ratio 10 Marla", compute="_compute_ratios", store=True, digits=(16, 4))
    ratio_c4 = fields.Float(string="Ratio 4 Marla (Comm)", compute="_compute_ratios", store=True, digits=(16, 4))
    ratio_c8 = fields.Float(string="Ratio 8 Marla (Comm)", compute="_compute_ratios", store=True, digits=(16, 4))

    # ---------------- Costs ----------------
    registry_fee = fields.Monetary(string="Registry Fee", currency_field="currency_id")
    fard_fee = fields.Monetary(string="Fard Fee", currency_field="currency_id")
    land_price = fields.Monetary(string="Land Price", currency_field="currency_id")
    intiqal_fee = fields.Monetary(string="Intiqal Fee", currency_field="currency_id")
    purchase_tax = fields.Monetary(string="236k Purchase Tax", currency_field="currency_id")
    commission_amount = fields.Monetary(string="Commission Amount", currency_field="currency_id")
    other_fee = fields.Monetary(string="Other Fee", currency_field="currency_id")
    land_base_cost = fields.Monetary(string="Base Land Cost", currency_field="currency_id")

    total_cost = fields.Monetary(string="Total Land Cost", compute="_compute_total_cost", store=True,
                                 currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", string="Currency",
                                  default=lambda self: self.env.company.currency_id)
    cost_per_marla = fields.Float(string="Cost per Marla", compute="_compute_cost_per_marla", store=True)
    commercial_premium_pct = fields.Float(string="Commercial Premium (%)", default=3.0)

    # Plot Costs
    cost_r10 = fields.Monetary(string="10 Marla (Res)", compute="_compute_plot_costs", store=True,
                               currency_field="currency_id")
    cost_r5 = fields.Monetary(string="5 Marla (Res)", compute="_compute_plot_costs", store=True,
                              currency_field="currency_id")
    cost_c8 = fields.Monetary(string="8 Marla (Comm)", compute="_compute_plot_costs", store=True,
                              currency_field="currency_id")
    cost_c4 = fields.Monetary(string="4 Marla (Comm)", compute="_compute_plot_costs", store=True,
                              currency_field="currency_id")

    # Normal Plot Counts (display)
    cnt_r10 = fields.Float(string="10 Marla (Res) Plots", default=0.0, digits=(16, 4))
    cnt_r5 = fields.Float(string="5 Marla (Res) Plots", default=0.0, digits=(16, 4))
    cnt_c8 = fields.Float(string="8 Marla (Comm) Plots", default=0.0, digits=(16, 4))
    cnt_c4 = fields.Float(string="4 Marla (Comm) Plots", default=0.0, digits=(16, 4))

    # Security counts computed from plot_ids
    sec_cnt_r10 = fields.Float(string="Security 10 Marla", default=0.0, digits=(16, 4))
    sec_cnt_r5 = fields.Float(string="Security 5 Marla", default=0.0, digits=(16, 4))
    sec_cnt_c8 = fields.Float(string="Security 8 Marla", default=0.0, digits=(16, 4))
    sec_cnt_c4 = fields.Float(string="Security 4 Marla", default=0.0, digits=(16, 4))


    # Plots
    plot_ids = fields.One2many("land.plot", "project_id", string="All Plots")

    # ---------------- Project-level attachments (binary fields storing base64 content) ----------------
    # Project-level documents
    registry_attachment_project = fields.Binary(string="Registry Document", attachment=True)
    registry_filename_project = fields.Char(string="Registry Filename")
    tax_challan_attachment_project = fields.Binary(string="Tax Challan", attachment=True)
    tax_challan_filename_project = fields.Char("Tax Challan Filename")
    commission_receiving_attachment_project = fields.Binary(string="Commission Receiving Document", attachment=True)
    commission_receiving_filename_project = fields.Char(string="Commission Receiving Filename")

    fard_attachment_project = fields.Binary(string="Fard Document", attachment=True)
    fard_filename_project = fields.Char(string="Fard Filename")
    intiqal_attachment_project = fields.Binary(string="Intiqal Document", attachment=True)
    intiqal_filename_project = fields.Char(string="Intiqal Filename")

    # Optional supplier for the created purchase order
    supplier_id = fields.Many2one("res.partner", string="Preferred Supplier")

    # ---------------- Computed Fields ----------------
    @api.depends("total_acres")
    def _compute_totals(self):
        for rec in self:
            rec.total_marla = round((rec.total_acres or 0.0) * ACRE_TO_MARLA, 2)

    @api.depends("total_acres")
    def _compute_ratios(self):
        for rec in self:
            # These ratio multipliers are taken from original code; adjust if your business logic differs
            rec.ratio_r5 = round((rec.total_acres or 0.0) * 3.0, 4)
            rec.ratio_r10 = round((rec.total_acres or 0.0) * 1.25, 4)
            rec.ratio_c4 = round((rec.total_acres or 0.0) * 2.0, 4)
            rec.ratio_c8 = round((rec.total_acres or 0.0) * 0.25, 4)

    @api.depends("plot_ids.size_marla", "total_marla")
    def _compute_remaining_marla(self):
        for rec in self:
            used = sum([p.size_marla for p in rec.plot_ids if not getattr(p, "is_security", False)])
            rec.remaining_marla = round((rec.total_marla or 0.0) - used, 2)

    @api.depends("land_base_cost", "registry_fee", "fard_fee", "land_price", "intiqal_fee",
                 "commission_amount", "purchase_tax", "other_fee")
    def _compute_total_cost(self):
        for rec in self:
            rec.total_cost = round(
                (rec.land_base_cost or 0.0)
                + (rec.registry_fee or 0.0)
                + (rec.fard_fee or 0.0)
                + (rec.land_price or 0.0)
                + (rec.intiqal_fee or 0.0)
                + (rec.purchase_tax or 0.0)
                + (rec.commission_amount or 0.0)
                + (rec.other_fee or 0.0), 2
            )

    @api.depends("total_cost", "total_marla")
    def _compute_cost_per_marla(self):
        for rec in self:
            rec.cost_per_marla = round(rec.total_cost / ACRE_TO_MARLA, 2) if rec.total_marla else 0.0

    @api.depends("cost_per_marla")
    def _compute_plot_costs(self):
        for rec in self:
            rec.cost_r10 = round(rec.cost_per_marla * TEN_MARLA, 2)
            rec.cost_r5 = round(rec.cost_per_marla * FIVE_MARLA, 2)
            rec.cost_c8 = round(rec.cost_per_marla * EIGHT_MARLA_C * 1.2, 2)
            rec.cost_c4 = round(rec.cost_per_marla * FOUR_MARLA_C * 1.2, 2)

    @api.depends("project_type")
    def _compute_security_pct(self):
        for rec in self:
            if rec.project_type == 'compact':
                rec.security_pct = 0.15
            elif rec.project_type == 'non_compact':
                rec.security_pct = 0.30
            else:
                rec.security_pct = 0.0

    # ---------------- Automatic Plot Generation ----------------

    @api.onchange("total_acres", "project_type")
    def _onchange_total_acres_auto_generate_plots(self):
        for rec in self:

            # ---------------- RESET IF INVALID ----------------
            if not rec.total_acres or rec.total_acres <= 0:
                rec.plot_ids = [(5, 0, 0)]
                rec.cnt_r5 = rec.cnt_r10 = rec.cnt_c4 = rec.cnt_c8 = 0.0
                rec.sec_cnt_r10 = rec.sec_cnt_r5 = rec.sec_cnt_c4 = rec.sec_cnt_c8 = 0.0
                continue

            sec_pct = rec.security_pct or 0.0

            # ---------------- BASE RATIOS ----------------
            base_r5 = rec.ratio_r5
            base_r10 = rec.ratio_r10
            base_c4 = rec.ratio_c4
            base_c8 = rec.ratio_c8

            # ---------------- DISPLAY COUNTS (FLOATS) ----------------
            rec.cnt_r5 = base_r5 * (1 - sec_pct)
            rec.cnt_r10 = base_r10 * (1 - sec_pct)
            rec.cnt_c4 = base_c4 * (1 - sec_pct)
            rec.cnt_c8 = base_c8 * (1 - sec_pct)

            rec.sec_cnt_r5 = base_r5 - rec.cnt_r5
            rec.sec_cnt_r10 = base_r10 - rec.cnt_r10
            rec.sec_cnt_c4 = base_c4 - rec.cnt_c4
            rec.sec_cnt_c8 = base_c8 - rec.cnt_c8

            # ---------------- PURE INTEGER COUNTS ----------------
            full_r5 = int(rec.cnt_r5)
            full_r10 = int(rec.cnt_r10)
            full_c4 = int(rec.cnt_c4)
            full_c8 = int(rec.cnt_c8)

            # For security plots, truncate decimals (floor behavior)
            sec_r5 = int(rec.sec_cnt_r5)
            sec_r10 = int(rec.sec_cnt_r10)
            sec_c4 = int(rec.sec_cnt_c4)
            sec_c8 = int(rec.sec_cnt_c8)

            cmds = [(5, 0, 0)]  # clear old plots

            size_map = {
                "r10": TEN_MARLA,
                "r5": FIVE_MARLA,
                "c8": EIGHT_MARLA_C,
                "c4": FOUR_MARLA_C,
            }
            code_map = {
                "r10": "RES_10",
                "r5": "RES_5",
                "c8": "COM_8",
                "c4": "COM_4",
            }

            # ---------------- PROCESS EACH CATEGORY ----------------
            for cat, normal_cnt, sec_cnt in [
                ("r10", full_r10, sec_r10),
                ("r5", full_r5, sec_r5),
                ("c8", full_c8, sec_c8),
                ("c4", full_c4, sec_c4),
            ]:
                size = size_map[cat]
                prefix = code_map[cat]
                parent_indexes = []

                # ------ NORMAL PLOTS ------
                for i in range(normal_cnt):
                    idx = i + 1
                    cmds.append((0, 0, {
                        "category": cat,
                        "number": idx,
                        "name": f"{prefix}_{idx:03d}",
                        "size_marla": size,
                        "is_security": False,
                    }))
                    parent_indexes.append(idx)

                # ------ SECURITY PLOTS ------
                sec_cnt_int = int(sec_cnt)  # <-- truncate decimals
                for i in range(sec_cnt_int):
                    idx = i + 1
                    parent_id = parent_indexes[0] if parent_indexes else False
                    cmds.append((0, 0, {
                        "category": cat,
                        "number": idx,
                        "name": f"{prefix}_{idx:03d}_SEC",
                        "size_marla": size,
                        "is_security": True,
                        "parent_plot_id": parent_id,
                    }))

            rec.plot_ids = cmds

    # ---------------- FIX CREATE METHOD ----------------
    @api.model
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            normal_plots = rec.plot_ids.filtered(lambda p: not p.is_security)
            for plot in rec.plot_ids.filtered(lambda p: p.is_security):
                if normal_plots and not plot.parent_plot_id:
                    plot.parent_plot_id = normal_plots[0].id
        return records

    # ---------------- Security Counts & Totals ----------------
    # @api.depends("plot_ids", "plot_ids.is_security", "plot_ids.category", "plot_ids.security_amount")
    # def _compute_security_counts(self):
    #     for rec in self:
    #         rec.sec_cnt_r10 = rec.ratio_r10 - rec.cnt_r10
    #         rec.sec_cnt_r5 = rec.ratio_r5 - rec.cnt_r5
    #         rec.sec_cnt_c8 = rec.ratio_c8 - rec.cnt_c8
    #         rec.sec_cnt_c4 = rec.ratio_c4 - rec.cnt_c4

    # ---------------- Convert to Inventory ----------------
    def action_convert_to_inventory(self):
        Template = self.env["product.template"]
        ProductCategory = self.env["product.category"]
        Attachment = self.env["ir.attachment"]
        Account = self.env["account.account"]
        PurchaseOrder = self.env["purchase.order"]
        PurchaseLine = self.env["purchase.order.line"]

        field_name = "detailed_type" if "detailed_type" in Template._fields else "type"
        sel_keys = [k for k, _ in (Template._fields[field_name].selection or [])]
        preferred_order = ["product", "storable", "consu", "service"]
        field_value = next((p for p in preferred_order if p in sel_keys), sel_keys[0] if sel_keys else None)

        category_map = {
            "r10": "Residential 10 Marla",
            "r5": "Residential 5 Marla",
            "c8": "Commercial 8 Marla",
            "c4": "Commercial 4 Marla",
            "sec": "Security",
        }

        if "product_uom_id" in PurchaseLine._fields:
            po_line_uom_field = "product_uom_id"
        elif "product_uom" in PurchaseLine._fields:
            po_line_uom_field = "product_uom"
        else:
            po_line_uom_field = None

        ResPartner = self.env["res.partner"]

        for rec in self:
            if not rec.plot_ids:
                raise UserError(_("No plots found in project '%s'. Generate plots first.") % rec.name)

        created_products = []
        for plot in rec.plot_ids:
            # Skip if already converted
            if plot.product_id:
                created_products.append(plot.product_id)
                continue

            # set attachments and product info depending on security
            if plot.is_security and plot.parent_plot_id:
                registry_b64 = plot.registry_attachment or plot.parent_plot_id.registry_attachment or rec.registry_attachment_project
                fard_b64 = plot.fard_attachment or plot.parent_plot_id.fard_attachment or rec.fard_attachment_project
                intiqal_b64 = plot.intiqal_attachment or plot.parent_plot_id.intiqal_attachment or rec.intiqal_attachment_project
                registry_fname = plot.registry_filename or plot.parent_plot_id.registry_filename or rec.registry_filename_project
                fard_fname = plot.fard_filename or plot.parent_plot_id.fard_filename or rec.fard_filename_project
                intiqal_fname = plot.intiqal_filename or plot.parent_plot_id.intiqal_filename or rec.intiqal_filename_project
                prod_name = f"{plot.parent_plot_id.name}-SECURITY"
                prod_price = plot.security_amount or plot.cost or 0.0
                cat_name = "Security Charge"
            else:
                registry_b64 = plot.registry_attachment or rec.registry_attachment_project
                fard_b64 = plot.fard_attachment or rec.fard_attachment_project
                intiqal_b64 = plot.intiqal_attachment or rec.intiqal_attachment_project
                registry_fname = plot.registry_filename or rec.registry_filename_project
                fard_fname = plot.fard_filename or rec.fard_filename_project
                intiqal_fname = plot.intiqal_filename or rec.intiqal_filename_project
                prod_name = plot.name
                prod_price = plot.cost or 0.0
                cat_name = category_map.get(plot.category, "Other")

            # Validate docs (for non-security ensure docs exist; security may reuse parent/project)
            missing = []
            if not registry_b64: missing.append("Registry")
            if not fard_b64: missing.append("Fard")
            if not intiqal_b64: missing.append("Intiqal")
            if missing:
                raise UserError(_("Please upload missing docs (%s) for project %s") %
                                (", ".join(missing),  rec.name))

            # Product Category
            product_categ = ProductCategory.search([("name", "=", cat_name)], limit=1)
            if not product_categ:
                product_categ = ProductCategory.create({"name": cat_name})

            # Product Template values
            vals = {
                "name": prod_name,
                "list_price": prod_price,
                "standard_price": prod_price,
                "sale_ok": True,
                "purchase_ok": True,
                "categ_id": product_categ.id,
            }
            if field_value:
                vals[field_name] = field_value

            tmpl = Template.create(vals)

            # Optional: set income account if present
            income_acc = Account.search([("code", "=", "400000")], limit=1)
            if income_acc:
                tmpl.property_account_income_id = income_acc.id

            product_variant = tmpl.product_variant_id
            plot.product_id = product_variant.id
            created_products.append(product_variant)

            # Attach docs to product.template as ir.attachment
            for b64, fname in [
                (registry_b64, registry_fname),
                (fard_b64, fard_fname),
                (intiqal_b64, intiqal_fname),
            ]:
                if not b64:
                    continue
                Attachment.sudo().create({
                    "name": (fname or f"{prod_name}.pdf"),
                    "res_model": "product.template",
                    "res_id": tmpl.id,
                    "type": "binary",
                    "datas": b64,
                    "mimetype": "application/pdf",
                })

        # ---------------- Create Purchase Order for created products ----------------
        if created_products:
            vendor = getattr(rec, "supplier_id", False) or False

            if not vendor:
                if "supplier_rank" in ResPartner._fields:
                    vendor = ResPartner.search([("supplier_rank", ">", 0)], limit=1)

            if not vendor:
                if "supplier" in ResPartner._fields:
                    vendor = ResPartner.search([("supplier", "=", True)], limit=1)

            if not vendor:
                vendor = ResPartner.search([], limit=1)

            if not vendor:
                vendor_vals = {
                    "name": _("Default Supplier for %s") % (rec.name or self.env.company.name),
                    "supplier_rank": 1,
                    "company_type": "company",
                }
                vendor = ResPartner.sudo().create(vendor_vals)
                rec.message_post(body=_(
                    "No supplier found; created default supplier <b>%s</b> to continue conversion.") % vendor.name)

            po_vals = {
                "partner_id": vendor.id,
                "origin": rec.name,
            }
            po = PurchaseOrder.create(po_vals)

            uom = self.env.ref("uom.product_uom_unit", raise_if_not_found=False)
            for product in created_products:
                price = getattr(product, "list_price", False) or (
                    product.product_tmpl_id.list_price if product.product_tmpl_id else 0.0)
                line_vals = {
                    "order_id": po.id,
                    "name": product.display_name,
                    "product_id": product.id,
                    "product_qty": 1,
                    "price_unit": price,
                }
                if po_line_uom_field and uom:
                    line_vals[po_line_uom_field] = uom.id
                PurchaseLine.create(line_vals)

            rec.message_post(body=_("✅ %s products created and added to Purchase Order <b>%s</b>.") %
                                  (len(created_products), po.name))

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Inventory & Purchase Creation"),
                    "message": _("Plots successfully converted into Products and Purchase Order created."),
                    "sticky": False,
                    "type": "success",
                },
            }


# ---------------- LAND PLOT ----------------
class LandPlot(models.Model):
    _name = "land.plot"
    _description = "Individual Land Plot"
    _order = "project_id, category, number"

    name = fields.Char(required=True)
    project_id = fields.Many2one("land.project", required=True, ondelete="cascade")
    category = fields.Selection([
        ("r10", "Residential 10 Marla"),
        ("r5", "Residential 5 Marla"),
        ("c8", "Commercial 8 Marla"),
        ("c4", "Commercial 4 Marla"),
        ("sec", "Security"),
    ], required=True)
    number = fields.Integer(string="No.", required=True)
    size_marla = fields.Float(string="Size (Marla)", readonly=True)
    cost = fields.Monetary(string="Cost", compute="_compute_cost", store=True, currency_field="currency_id")
    currency_id = fields.Many2one(related="project_id.currency_id", store=True, readonly=True)

    # Security fields
    is_security = fields.Boolean(string="Is Security Entry", default=False)
    security_amount = fields.Monetary(string="Security Amount", currency_field="currency_id")

    # relation to parent plot (used for security entries linking to a parent)
    parent_plot_id = fields.Many2one("land.plot", string="Parent Plot", ondelete="set null")

    # attachments on plot level (binary base64 fields)
    registry_attachment = fields.Binary(string="Registry Document")
    fard_attachment = fields.Binary(string="Fard Document")
    intiqal_attachment = fields.Binary(string="Intiqal Document")

    registry_filename = fields.Char(string="Registry Filename")
    fard_filename = fields.Char(string="Fard Filename")
    intiqal_filename = fields.Char(string="Intiqal Filename")

    # optional product link once converted
    product_id = fields.Many2one("product.product", string="Product")

    # Unique constraint - keep for compatibility (warning in logs may remain on newer Odoo versions)
    _sql_constraints = [
        ("uniq_project_cat_num", "unique(project_id, category, number, is_security)",
         "Plot number must be unique."),
    ]


    @api.depends("category", "project_id.cost_per_marla", "is_security", "project_id.project_type",
                 "project_id.security_pct")
    def _compute_cost(self):
        for rec in self:
            base = rec.project_id.cost_per_marla or 0.0

            if rec.category == "r10":
                size_marla, premium = TEN_MARLA, 1.0
            elif rec.category == "r5":
                size_marla, premium = FIVE_MARLA, 1.0
            elif rec.category == "c8":
                size_marla, premium = EIGHT_MARLA_C, 1.2
            elif rec.category == "c4":
                size_marla, premium = FOUR_MARLA_C, 1.2
            else:
                size_marla, premium = 0.0, 1.0

            normal_cost = base * size_marla * premium
            rec.size_marla = size_marla

            if rec.is_security:
                # Calculate security amount as percentage of normal_cost
                sec_pct = rec.project_id.security_pct or 0.0
                security_amount = base * size_marla * premium
                rec.security_amount = round(security_amount, 2)
                rec.cost = round(security_amount, 2)  # If cost is only security amount
            else:
                rec.security_amount = 0.0
                rec.cost = round(normal_cost, 2)
