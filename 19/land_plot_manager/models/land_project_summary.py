from odoo import models, fields, api

class LandProjectSummary(models.Model):
    _name = "land.project.summary"
    _description = "Land Project Summary"

    project_id = fields.Many2one("land.project", string="Project", required=True)
    name = fields.Char(related="project_id.name", string="Project Name", store=True)
    total_acres = fields.Float(related="project_id.total_acres", string="Total Acres", store=True)
    total_marla = fields.Float(related="project_id.total_marla", string="Total Marla", store=True)
    project_type = fields.Selection(related="project_id.project_type", string="Project Type", store=True)

    compact_non = fields.Float(string="Compact/Non- compact", compute="_compute_compact_show", store=True)

    @api.depends("total_acres", "project_type")
    def _compute_compact_show(self):
        for rec in self:
            if rec.project_type == "compact":
                rec.compact_non = rec.total_acres * 0.15
            elif rec.project_type == "non_compact":
                rec.compact_non = rec.total_acres * 0.30
            else:
                rec.compact_non = 0.0
