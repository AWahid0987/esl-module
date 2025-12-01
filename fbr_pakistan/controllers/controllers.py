# -*- coding: utf-8 -*-
# from odoo import http


# class FbrPakistan(http.Controller):
#     @http.route('/fbr_pakistan/fbr_pakistan', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fbr_pakistan/fbr_pakistan/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('fbr_pakistan.listing', {
#             'root': '/fbr_pakistan/fbr_pakistan',
#             'objects': http.request.env['fbr_pakistan.fbr_pakistan'].search([]),
#         })

#     @http.route('/fbr_pakistan/fbr_pakistan/objects/<model("fbr_pakistan.fbr_pakistan"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fbr_pakistan.object', {
#             'object': obj
#         })

