# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class SierraFamilyController(http.Controller):
    """Public website controller for Sierra Family listing and details."""

    @http.route(['/Sierra-family', '/Sierra-family/page/<int:page>'],
                type='http', auth='public', website=True)
    def list_families_sierra(self, page=1, **kw):
        """Show paginated list of Sierra Family records."""
        Family = request.env['sierra.family'].sudo()
        per_page = 12
        total = Family.search_count([])

        pager = request.website.pager(
            url='/Sierra-family',
            total=total,
            page=page,
            step=per_page,
            url_args={}
        )

        families = Family.search([], limit=per_page, offset=pager['offset'])

        # Renders the QWeb template defined in XML
        return request.render('sierra_family.family_list_sierra', {
            'families': families,
            'pager': pager,
        })

    @http.route(['/Sierra-family/<int:rec_id>'],
                type='http', auth='public', website=True)
    def family_page_sierra(self, rec_id, **kw):
        """Show details for a single Sierra Family record."""
        record = request.env['sierra.family'].sudo().browse(rec_id)
        if not record.exists():
            return request.not_found()

        return request.render('sierra_family.family_page_sierra', {
            'record': record,
        })
