# -*- coding: utf-8 -*-
from odoo import  fields, models


class ResCompany(models.Model):
    """ This model represents res.company."""
    _inherit = 'res.company'
    _description = 'ResCompany'

    fbr_url=fields.Char(string='Fbr Url')
    fbr_token=fields.Char(string="Fbr Token")

