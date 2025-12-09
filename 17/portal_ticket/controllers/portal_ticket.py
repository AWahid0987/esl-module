# controllers/portal_ticket.py
# -*- coding: utf-8 -*-
import base64
from odoo import http
from odoo.http import request


class PortalTicketCustom(http.Controller):

    @http.route('/my/tickets/new', type='http', auth='user', website=True)
    def ticket_new(self, **kw):
        # Use Helpdesk Teams as "Category"
        try:
            teams = request.env['helpdesk.team'].sudo().search([])
            return request.render('portal_ticket.portal_ticket_new', {
                'teams': teams,  # pass teams to the template
            })
        except Exception as e:
            # Fallback if helpdesk.team doesn't exist or error occurs
            return request.render('portal_ticket.portal_ticket_new', {
                'teams': request.env['helpdesk.team'].sudo().browse([]),
            })

    @http.route('/my/tickets/create', type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def ticket_create(self, **post):
        try:
            subject = (post.get('subject') or '').strip()
            description = (post.get('description') or '').strip()
            team_id = post.get('team_id')

            if not subject and not description:
                # Redirect back to form if both are empty
                return request.redirect('/my/tickets/new')

            vals = {
                'name': subject or 'No subject',
                'description': description,
                'partner_id': request.env.user.partner_id.id,
            }
            if team_id:
                try:
                    vals['team_id'] = int(team_id)
                except (ValueError, TypeError):
                    pass  # Skip invalid team_id

            ticket = request.env['helpdesk.ticket'].sudo().create(vals)

            # attachments (multi)
            files = request.httprequest.files.getlist('attachments')
            for f in files:
                if not f or not f.filename:
                    continue
                try:
                    file_data = f.read()
                    if file_data:
                        request.env['ir.attachment'].sudo().create({
                            'name': f.filename,
                            'datas': base64.b64encode(file_data),
                            'res_model': 'helpdesk.ticket',
                            'res_id': ticket.id,
                            'type': 'binary',
                            'mimetype': f.content_type or f.mimetype or 'application/octet-stream',
                        })
                except Exception as e:
                    # Log error but continue - don't fail ticket creation due to attachment error
                    pass

            # Always redirect to tickets list page after successful creation
            return request.redirect('/my/tickets')
        except Exception as e:
            # On error, redirect back to form
            return request.redirect('/my/tickets/new')

