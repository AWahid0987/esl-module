# -*- coding: utf-8 -*-
"""
Res Partner Extensions
Adds Pakistani-specific customer information fields
"""
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

    # --- Basic customer fields ---
    relation = fields.Selection([
        ('S/O', 'Son of'),
        ('D/O', 'Daughter of'),
        ('W/O', 'Wife of'),
        ('F/O', 'Father of'),
        ('H/O', 'Husband of'),
        ('G/O', 'Guardian of'),
        ('M/O', 'Mother of'),
    ], string="Relation")   # <<< required=False (handled in view/constraints)

    father_name = fields.Char(string="Father Name")
    cnic = fields.Char(string="CNIC")
    mobile = fields.Char(string="Mobile Number")
    res_number = fields.Char(string="Res Number")
    member_id = fields.Char(string="Member ID", readonly=True, copy=False)

    # Name fields
    relative_name = fields.Char(string="Relative Name")

    # single radio: Person / Company / Customer
    customer_type = fields.Selection(
        [
            ('person', 'Person'),
            ('company', 'Company'),
            ('customer', 'Customer'),
        ],
        string="Type",
        default='person',
    )

    # --- Nominee fields (Nominee 1 is mandatory when customer) ---
    nominee_name = fields.Char(string="Nominee Name")      # required via constraint
    nominee_cnic = fields.Char(string="Nominee CNIC")      # required via constraint
    application = fields.Char(string="Relationship with applicant")  # required via constraint

    nominee_name_2 = fields.Char(string="Nominee Name")
    nominee_cnic_2 = fields.Char(string="Nominee CNIC")
    application_2 = fields.Char(string="Relationship with applicant")

    nominee_name_3 = fields.Char(string="Nominee Name")
    nominee_cnic_3 = fields.Char(string="Nominee CNIC")
    application_3 = fields.Char(string="Relationship with applicant")

    nominee_name_4 = fields.Char(string="Nominee Name")
    nominee_cnic_4 = fields.Char(string="Nominee CNIC")
    application_4 = fields.Char(string="Relationship with applicant")

    nominee_name_5 = fields.Char(string="Nominee Name")
    nominee_cnic_5 = fields.Char(string="Nominee CNIC")
    application_5 = fields.Char(string="Relationship with applicant")

    # Relative name per nominee
    relative_name_1 = fields.Char(string="Relative Name 1")
    relative_name_2 = fields.Char(string="Relative Name 2")
    relative_name_3 = fields.Char(string="Relative Name 3")
    relative_name_4 = fields.Char(string="Relative Name 4")
    relative_name_5 = fields.Char(string="Relative Name 5")

    # Relations per nominee
    relation_1 = fields.Selection([
        ('S/O', 'Son of'),
        ('D/O', 'Daughter of'),
        ('W/O', 'Wife of'),
        ('F/O', 'Father of'),
        ('H/O', 'Husband of'),
        ('G/O', 'Guardian of'),
        ('M/O', 'Mother of'),
    ], string="Relation 1")
    relation_2 = fields.Selection([
        ('S/O', 'Son of'),
        ('D/O', 'Daughter of'),
        ('W/O', 'Wife of'),
        ('F/O', 'Father of'),
        ('H/O', 'Husband of'),
        ('G/O', 'Guardian of'),
        ('M/O', 'Mother of'),
    ], string="Relation 2")
    relation_3 = fields.Selection([
        ('S/O', 'Son of'),
        ('D/O', 'Daughter of'),
        ('W/O', 'Wife of'),
        ('F/O', 'Father of'),
        ('H/O', 'Husband of'),
        ('G/O', 'Guardian of'),
        ('M/O', 'Mother of'),
    ], string="Relation 3")
    relation_4 = fields.Selection([
        ('S/O', 'Son of'),
        ('D/O', 'Daughter of'),
        ('W/O', 'Wife of'),
        ('F/O', 'Father of'),
        ('H/O', 'Husband of'),
        ('G/O', 'Guardian of'),
        ('M/O', 'Mother of'),
    ], string="Relation 4")
    relation_5 = fields.Selection([
        ('S/O', 'Son of'),
        ('D/O', 'Daughter of'),
        ('W/O', 'Wife of'),
        ('F/O', 'Father of'),
        ('H/O', 'Husband of'),
        ('G/O', 'Guardian of'),
        ('M/O', 'Mother of'),
    ], string="Relation 5")

    # Computed label fields
    relation_label = fields.Char(string="Relation Label", compute='_compute_relation_labels')
    relation_label_1 = fields.Char(string="Relation Label 1", compute='_compute_relation_labels')
    relation_label_2 = fields.Char(string="Relation Label 2", compute='_compute_relation_labels')
    relation_label_3 = fields.Char(string="Relation Label 3", compute='_compute_relation_labels')
    relation_label_4 = fields.Char(string="Relation Label 4", compute='_compute_relation_labels')
    relation_label_5 = fields.Char(string="Relation Label 5", compute='_compute_relation_labels')

    # ---------------- Onchange / Compute -----------------

    @api.onchange('customer_type')
    def _onchange_customer_type(self):
        """Sync Odoo ka original company_type with our radio."""
        for rec in self:
            if rec.customer_type in ('person', 'company'):
                rec.company_type = rec.customer_type
            else:
                # Customer ko person treat kar rahe hain
                rec.company_type = 'person'

    @api.depends('relation', 'relation_1', 'relation_2', 'relation_3', 'relation_4', 'relation_5')
    def _compute_relation_labels(self):
        mapping = {
            'S/O': 'Son of',
            'D/O': 'Daughter of',
            'W/O': 'Wife of',
            'F/O': 'Father of',
            'H/O': 'Husband of',
            'G/O': 'Guardian of',
            'M/O': 'Mother of',
        }
        for rec in self:
            rec.relation_label = mapping.get(rec.relation, "")
            rec.relation_label_1 = mapping.get(rec.relation_1, "")
            rec.relation_label_2 = mapping.get(rec.relation_2, "")
            rec.relation_label_3 = mapping.get(rec.relation_3, "")
            rec.relation_label_4 = mapping.get(rec.relation_4, "")
            rec.relation_label_5 = mapping.get(rec.relation_5, "")

    # ---------------- Create: Member ID sequence -----------------

    @api.model
    def create(self, vals_list):
        """Automatically generate Member ID from sequence on creation."""
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        for vals in vals_list:
            if not vals.get('member_id'):
                seq_value = self.env['ir.sequence'].next_by_code('res.partner.member.id')
                if not seq_value:
                    seq_value = 'MBR00001'
                vals['member_id'] = seq_value

        partners = super().create(vals_list)
        return partners

    # ---------------- Constraint: customer ke liye fields must -----------------

    @api.constrains(
        'customer_type',
        'relation', 'cnic', 'mobile',
        'nominee_name', 'nominee_cnic', 'application'
    )
    def _check_customer_required_fields(self):
        for rec in self:
            if rec.customer_type != 'customer':
                continue

            missing = []
            if not rec.relation:
                missing.append(_("Relation"))
            if not rec.cnic:
                missing.append(_("CNIC"))
            if not rec.mobile:
                missing.append(_("Mobile Number"))
            if not rec.nominee_name:
                missing.append(_("Nominee Name (Nominee 1)"))
            if not rec.nominee_cnic:
                missing.append(_("Nominee CNIC (Nominee 1)"))
            if not rec.application:
                missing.append(_("Relationship with applicant (Nominee 1)"))

            if missing:
                raise ValidationError(
                    _("For Customer type, the following fields are required:\n- %s")
                    % "\n- ".join(missing)
                )
