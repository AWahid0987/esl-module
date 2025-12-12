# -*- coding: utf-8 -*-
"""
Product Land Extensions
Extends product template with land-specific information
"""
import base64
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ProductLand(models.Model):
    """
    Product Template Model Extended
    Adds land plot specific fields and document management
    """
    _inherit = 'product.template'

    # Land Info Fields
    notebook_name = fields.Char(string="Notebook Name")
    map_parameter = fields.Char(string="Plot Parameter")

    north = fields.Float(string="North (ft)")
    south = fields.Float(string="South (ft)")
    east = fields.Float(string="East (ft)")
    west = fields.Float(string="West (ft)")

    marla = fields.Float(string="Marla", compute="_compute_marla", store=True)

    # Near Places
    north_place = fields.Char(string="North Place")
    south_place = fields.Char(string="South Place")
    east_place = fields.Char(string="East Place")
    west_place = fields.Char(string="West Place")
    near_plot_ids = fields.One2many('land.near.plot', 'product_id', string="Near Plots")

    # Images
    north_image = fields.Binary(string="North Image")
    south_image = fields.Binary(string="South Image")
    east_image = fields.Binary(string="East Image")
    west_image = fields.Binary(string="West Image")

    # Plot selection flags

    # Link to land plot record
    plot_id = fields.Many2one(
        "land.plot",
        string="Related Land Plot",
        help="Links this product to a registered land plot record.",
    )

    # NEW FIELD (requested)
    size_marla = fields.Char(string="Size (Marla)")

    # -------------------------------
    # COMPUTE METHODS
    # -------------------------------

    @api.depends('north', 'south', 'east', 'west')
    def _compute_marla(self):
        """Compute marla area from entered plot dimensions."""
        for rec in self:
            if all([rec.north, rec.south, rec.east, rec.west]):
                avg_width = (rec.east + rec.west) / 2
                avg_length = (rec.north + rec.south) / 2
                rec.marla = (avg_width * avg_length) / 272
            else:
                rec.marla = 0.0

    @api.depends('plot_id')
    def _compute_size_marla(self):
        """Bring size from linked land.plot record."""
        for rec in self:
            if rec.plot_id:
                rec.size_marla = rec.plot_id.size_marla
            else:
                rec.size_marla = 0.0

    # -------------------------------
    # ONCHANGE METHODS
    # -------------------------------

