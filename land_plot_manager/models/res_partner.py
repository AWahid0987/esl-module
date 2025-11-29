# -*- coding: utf-8 -*-
"""
Res Partner Extensions
Adds Pakistani-specific customer information fields
"""
import re
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """
    Res Partner Model Extended
    Adds CNIC validation, additional customer fields, and Member ID
    """
    _inherit = 'res.partner'

    relation = fields.Selection([
        ('S/O', 'Son of'),
        ('D/O', 'Daughter of'),
        ('W/O', 'Wife of'),
        ('F/O', 'Father of'),
        ('H/O', 'Husband of'),
        ('G/O', 'Guardian of'),
    ], string="Relation", required=True)

    father_name = fields.Char(string="Father Name")
    cnic = fields.Char(string="CNIC")
    nominee_name = fields.Char(string="Nominee Name", required=True)
    # relation_1 = fields.Char(string="S/O, D/O, W/O", required=True)
    nominee_cnic = fields.Char(string="Nominee CNIC", required=True)
    application = fields.Char(string="Relationship with applicant", required=True)
    nominee_name_2 = fields.Char(string="Nominee Name")
    # relation_2 = fields.Char(string="S/O, D/O, W/O")
    nominee_cnic_2 = fields.Char(string="Nominee CNIC")
    application_2 = fields.Char(string="Relationship with applicant")
    nominee_name_3 = fields.Char(string="Nominee Name")
    # relation_3 = fields.Char(string="S/O, D/O, W/O")
    nominee_cnic_3 = fields.Char(string="Nominee CNIC")
    application_3 = fields.Char(string="Relationship with applicant")
    nominee_name_4 = fields.Char(string="Nominee Name")
    # relation_4 = fields.Char(string="S/O, D/O, W/O")
    nominee_cnic_4 = fields.Char(string="Nominee CNIC")
    application_4 = fields.Char(string="Relationship with applicant")
    nominee_name_5 = fields.Char(string="Nominee Name")
    # relation_5 = fields.Char(string="S/O, D/O, W/O")
    nominee_cnic_5 = fields.Char(string="Nominee CNIC")
    application_5 = fields.Char(string="Relationship with applicant")
    mobile = fields.Char(string="Mobile Number")
    res_number = fields.Char(string="Res Number")
    member_id = fields.Char(string="Member ID", readonly=True, copy=False)

    # Name fields
    relative_name = fields.Char(string="Relative Name")
    relative_name_1 = fields.Char(string="Relative Name 1")
    relative_name_2 = fields.Char(string="Relative Name 2")
    relative_name_3 = fields.Char(string="Relative Name 3")
    relative_name_4 = fields.Char(string="Relative Name 4")
    relative_name_5 = fields.Char(string="Relative Name 5")


    relation_1 = fields.Selection([
        ('S/O', 'Son of'),
        ('D/O', 'Daughter of'),
        ('W/O', 'Wife of'),
        ('F/O', 'Father of'),
        ('H/O', 'Husband of'),
        ('G/O', 'Guardian of'),
    ], string="Relation 1")
    relation_2 = fields.Selection([
        ('S/O', 'Son of'),
        ('D/O', 'Daughter of'),
        ('W/O', 'Wife of'),
        ('F/O', 'Father of'),
        ('H/O', 'Husband of'),
        ('G/O', 'Guardian of'),
    ], string="Relation 2")
    relation_3 = fields.Selection([
        ('S/O', 'Son of'),
        ('D/O', 'Daughter of'),
        ('W/O', 'Wife of'),
        ('F/O', 'Father of'),
        ('H/O', 'Husband of'),
        ('G/O', 'Guardian of'),
    ], string="Relation 3")
    relation_4 = fields.Selection([
        ('S/O', 'Son of'),
        ('D/O', 'Daughter of'),
        ('W/O', 'Wife of'),
        ('F/O', 'Father of'),
        ('H/O', 'Husband of'),
        ('G/O', 'Guardian of'),
    ], string="Relation 4")
    relation_5 = fields.Selection([
        ('S/O', 'Son of'),
        ('D/O', 'Daughter of'),
        ('W/O', 'Wife of'),
        ('F/O', 'Father of'),
        ('H/O', 'Husband of'),
        ('G/O', 'Guardian of'),
    ], string="Relation 5")

    # Computed label fields
    relation_label = fields.Char(string="Relation Label", compute='_compute_relation_labels')
    relation_label_1 = fields.Char(string="Relation Label 1", compute='_compute_relation_labels')
    relation_label_2 = fields.Char(string="Relation Label 2", compute='_compute_relation_labels')
    relation_label_3 = fields.Char(string="Relation Label 3", compute='_compute_relation_labels')
    relation_label_4 = fields.Char(string="Relation Label 4", compute='_compute_relation_labels')
    relation_label_5 = fields.Char(string="Relation Label 5", compute='_compute_relation_labels')

    @api.depends('relation', 'relation_1', 'relation_2', 'relation_3', 'relation_4', 'relation_5')
    def _compute_relation_labels(self):
        mapping = {
            'S/O': 'Son of',
            'D/O': 'Daughter of',
            'W/O': 'Wife of',
            'F/O': 'Father of',
            'H/O': 'Husband of',
            'G/O': 'Guardian of',
        }
        for rec in self:
            rec.relation_label = mapping.get(rec.relation, "")
            rec.relation_label_1 = mapping.get(rec.relation_1, "")
            rec.relation_label_2 = mapping.get(rec.relation_2, "")
            rec.relation_label_3 = mapping.get(rec.relation_3, "")
            rec.relation_label_4 = mapping.get(rec.relation_4, "")
            rec.relation_label_5 = mapping.get(rec.relation_5, "")
    @api.model
    def create(self, vals_list):
        """Automatically generate Member ID from sequence on creation."""
        # Ensure we handle both single dict and list of dicts
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        for vals in vals_list:
            if not vals.get('member_id'):
                seq_value = self.env['ir.sequence'].next_by_code('res.partner.member.id')
                if not seq_value:
                    # Fallback: generate manually with proper format (MBR + 5 digits)
                    seq_value = 'MBR00001'
                vals['member_id'] = seq_value

        return super().create(vals_list)
