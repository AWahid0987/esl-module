# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class FbrUom(models.Model):
    _name = 'fbr.uom'
    _description = 'FBR Unit of Measurement'
    _rec_name = 'name'
    _order = 'name'
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'FBR UOM must be unique!'),
    ]

    name = fields.Char(string='UOM Name', )


class FbrSroItemSerial(models.Model):
    _name = 'fbr.sro.item.serial'
    _description = 'FBR SRO Item Serial Number'
    _rec_name = 'name'
    _order = 'name'
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'FBR SRO Item Serial Number must be unique!'),
    ]

    name = fields.Char(string='SRO Item Serial Number', )

class FbrDocumentType(models.Model):
    _name = 'fbr.document.type'
    _description = 'FBR Document Type'
    _rec_name = 'name'
    _order = 'name'
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'FBR Document Type must be unique!'),
    ]

    name = fields.Char(string='Document Type Name', )


class FbrProvince(models.Model):
    _name = 'fbr.province'
    _description = 'FBR Province'
    _rec_name = 'name'
    _order = 'name'
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'FBR Province must be unique!'),
    ]

    name = fields.Char(string='Province Name', )


class FbrSaleType(models.Model):
    _name = 'fbr.sale.type'
    _description = 'FBR Sale Type'
    _rec_name = 'name'
    _order = 'name'
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'FBR Sale Type must be unique!'),
    ]

    name = fields.Char(string='Sale Type Name', )


class FbrSro(models.Model):
    _name = 'fbr.sro'
    _description = 'FBR SRO'
    _rec_name = 'name'
    _order = 'name'
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'FBR SRO must be unique!'),
    ]

    name = fields.Char(string='SRO Name', )


class FbrScenarios(models.Model):
    _name = 'fbr.scenarios'
    _description = 'FBR Scenarios'
    _rec_name = 'name'
    _order = 'name'
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'FBR Scenarios must be unique!'),
    ]

    name = fields.Char(string='Scenario Name', )
    code = fields.Char(string='Scenario Code', )


class FbrBuyerType(models.Model):
    _name = 'fbr.buyer.type'
    _description = 'FBR Buyer Type'
    _rec_name = 'name'
    _order = 'name'
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'FBR Buyer Type must be unique!'),
    ]

    name = fields.Char(string='Buyer Type Name', )


class FbrReason(models.Model):
    _name = 'fbr.reason'
    _description = 'FBR Reason'
    _rec_name = 'name'
    _order = 'name'
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'FBR Reason must be unique!'),
    ]

    name = fields.Char(string='Reason Name', )


