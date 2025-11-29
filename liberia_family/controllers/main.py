from odoo import http
from odoo.http import request
import base64
import mimetypes

# ---------------------- LIBERIA FAMILY ----------------------
class LiberiaFamilyController(http.Controller):

    @http.route(['/Liberia-family', '/Liberia-family/page/<int:page>'], type='http', auth='public', website=True)
    def list_families(self, page=1, **kw):
        Family = request.env['liberia.family'].sudo()
        per_page = 12
        total = Family.search_count([])
        pager = request.website.pager(
            url='/Liberia-family',
            total=total,
            page=page,
            step=per_page,
        )
        families = Family.search([], limit=per_page, offset=pager['offset'])
        user_lang = request.env.lang

        family_data = []
        for f in families:
            data = {
                'id': f.id,
                'photo': f.photo,
                'project_title_en': f.project_title_en,
                'project_title_de': f.project_title_de,
                'project_description_en': f.project_description_en,
                'project_description_de': f.project_description_de,
                'investment_needed_en': f.investment_needed_en,
                'investment_needed_de': f.investment_needed_de,
                'receivew_1_en': f.receivew_1_en,
                'receivew_1_de': f.receivew_1_de,
                'receivew_2_en': f.receivew_2_en,
                'receivew_2_de': f.receivew_2_de,
                'receivew_3_en': f.receivew_3_en,
                'receivew_3_de': f.receivew_3_de,
                'receivew_4_en': f.receivew_4_en,
                'receivew_4_de': f.receivew_4_de,
                'progress_percentage_en': f.progress_percentage_en,
                'progress_percentage_de': f.progress_percentage_de,
            }
            fields = [
                'location_en', 'location_de', 'name_en', 'name_de', 'age_en', 'age_de',
                'current_income_en', 'current_income_de',
                'additional_income_en', 'additional_income_de'
            ]
            for field in fields:
                data[field] = getattr(f, field)
            family_data.append(data)

        template = 'liberia_family.family_list_liberia_en'
        if user_lang.startswith('de'):
            template = 'liberia_family.family_list_liberia_de'

        return request.render(template, {
            'families': family_data,
            'pager': pager,
            'user_lang': user_lang,
        })

    @http.route(['/Liberia-family/<int:rec_id>'], type='http', auth='public', website=True)
    def family_page(self, rec_id, **kw):
        record = request.env['liberia.family'].sudo().browse(rec_id)
        if not record.exists():
            return request.not_found()
        user_lang = request.env.lang

        return request.render('liberia_family.family_page_liberia', {
            'record': record,
            'user_lang': user_lang,
        })


class SierraFamilyController(http.Controller):

    @http.route(['/Sierra-family', '/Sierra-family/page/<int:page>'], type='http', auth='public', website=True)
    def list_families(self, page=1, **kw):
        Family = request.env['sierra.family'].sudo()
        per_page = 12
        total = Family.search_count([])
        pager = request.website.pager(
            url='/Sierra-family',
            total=total,
            page=page,
            step=per_page,
        )
        families = Family.search([], limit=per_page, offset=pager['offset'])
        user_lang = request.env.lang

        family_data = []
        for f in families:
            data = {
                'id': f.id,
                'photo': f.photo,

                'location_en' : f.location_en,
                'project_title_en': f.project_title_en,
                'project_title_de': f.project_title_de,
                'project_description_en': f.project_description_en,
                'project_description_de': f.project_description_de,
                'investment_needed_en': f.investment_needed_en,
                'investment_needed_de': f.investment_needed_de,
                'receivew_1_en': f.receivew_1_en,
                'receivew_1_de': f.receivew_1_de,
                'receivew_2_en': f.receivew_2_en,
                'receivew_2_de': f.receivew_2_de,
                'receivew_3_en': f.receivew_3_en,
                'receivew_3_de': f.receivew_3_de,
                'receivew_4_en': f.receivew_4_en,
                'receivew_4_de': f.receivew_4_de,
                'progress_percentage_en': f.progress_percentage_en,
                'progress_percentage_de': f.progress_percentage_de,
            }
            fields = [
                'location_en', 'location_de', 'name_en', 'name_de', 'age_en', 'age_de',
                'current_income_en', 'current_income_de',
                'additional_income_en', 'additional_income_de'
            ]
            for field in fields:
                data[field] = getattr(f, field)
            family_data.append(data)

        template = 'liberia_family.family_list_sierra_en'
        if user_lang.startswith('de'):
            template = 'liberia_family.family_list_sierra_de'

        return request.render(template, {
            'families': family_data,
            'pager': pager,
            'user_lang': user_lang,
        })

    @http.route(['/Sierra-family/<int:rec_id>'], type='http', auth='public', website=True)
    def family_page(self, rec_id, **kw):
        record = request.env['sierra.family'].sudo().browse(rec_id)
        if not record.exists():
            return request.not_found()
        user_lang = request.env.lang

        return request.render('liberia_family.family_page_sierra', {
            'record': record,
            'user_lang': user_lang,
        })



# ---------------------- AFGHANISTAN FAMILY ----------------------
class AfghanistanFamilyController(http.Controller):

    @http.route(['/Afghanistan-family', '/Afghanistan-family/page/<int:page>'], type='http', auth='public', website=True)
    def list_families(self, page=1, **kw):
        Family = request.env['afghanistan.family'].sudo()
        per_page = 12
        total = Family.search_count([])
        pager = request.website.pager(
            url='/Afghanistan-family',
            total=total,
            page=page,
            step=per_page
        )
        families = Family.search([], limit=per_page, offset=pager['offset'])
        user_lang = request.env.lang

        family_data = []
        for f in families:
            data = {
                'id': f.id,
                'photo': f.photo,
                'project_title_en': f.project_title_en,
                'project_title_de': f.project_title_de,
                'project_description_en': f.project_description_en,
                'project_description_de': f.project_description_de,
                'investment_needed_en': f.investment_needed_en,
                'investment_needed_de': f.investment_needed_de,
                'receivew_1_en': f.receivew_1_en,
                'receivew_1_de': f.receivew_1_de,
                'receivew_2_en': f.receivew_2_en,
                'receivew_2_de': f.receivew_2_de,
                'receivew_3_en': f.receivew_3_en,
                'receivew_3_de': f.receivew_3_de,
                'receivew_4_en': f.receivew_4_en,
                'receivew_4_de': f.receivew_4_de,
                'progress_percentage_en': f.progress_percentage_en,
                'progress_percentage_de': f.progress_percentage_de,
            }
            fields = [
                'location_en', 'location_de', 'name_en', 'name_de', 'age_en', 'age_de',
                'current_income_en', 'current_income_de', 'additional_income_en', 'additional_income_de'
            ]
            for field in fields:
                data[field] = getattr(f, field)
            family_data.append(data)

        template = 'liberia_family.family_list_afghanistan_en'
        if user_lang.startswith('de'):
            template = 'liberia_family.family_list_afghanistan_de'

        return request.render(template, {
            'families': family_data,
            'pager': pager,
            'user_lang': user_lang,
        })

    @http.route(['/Afghanistan-family/<int:rec_id>'], type='http', auth='public', website=True)
    def family_page(self, rec_id, **kw):
        record = request.env['afghanistan.family'].sudo().browse(rec_id)
        if not record.exists():
            return request.not_found()
        user_lang = request.env.lang
        return request.render('liberia_family.family_page_afghanistan', {
            'record': record,
            'user_lang': user_lang,
        })


# ---------------------- COMMUNITY PAGES ----------------------
class CommunityController(http.Controller):

    # ---------------------- LIBERIA COMMUNITY ----------------------
    @http.route(['/small-projects', '/small-projects/page/<int:page>'], type='http', auth='public', website=True)
    def list_small_communities(self, page=1, **kw):
        Community = request.env['liberia.community'].sudo()
        per_page = 12
        total = Community.search_count([])
        pager = request.website.pager(url='/small-projects', total=total, page=page, step=per_page)
        communities = Community.search([], limit=per_page, offset=pager['offset'])
        user_lang = request.env.lang
        return request.render('liberia_family.community_list_liberia', {
            'communities': communities,
            'pager': pager,
            'user_lang': user_lang,
        })

    @http.route(['/small-projects/<int:rec_id>'], type='http', auth='public', website=True)
    def small_community_page(self, rec_id, **kw):
        record = request.env['liberia.community'].sudo().browse(rec_id)
        if not record.exists():
            return request.not_found()
        user_lang = request.env.lang
        return request.render('liberia_family.community_page_liberia', {
            'record': record,
            'user_lang': user_lang,
        })

    @http.route(['/community/download/<int:rec_id>'],
                type='http', auth='public', website=True)
    def download_community_file(self, rec_id, **kw):
        """Download attached binary file from liberia.community"""
        record = request.env['liberia.community'].sudo().browse(rec_id)
        if not record.exists() or not record.community_liberia_file:
            return request.not_found()

        # Decode the Base64 binary data
        try:
            file_content = base64.b64decode(record.community_liberia_file)
        except Exception:
            return request.not_found()

        # Get filename and content type
        file_name = record.community_file_filename or "ProjectFile"
        content_type, _ = mimetypes.guess_type(file_name)
        if not content_type:
            content_type = 'application/octet-stream'  # fallback for unknown types

        # Return downloadable response
        return request.make_response(
            file_content,
            headers=[
                ('Content-Type', content_type),
                ('Content-Length', str(len(file_content))),
                ('Content-Disposition', f'attachment; filename="{file_name}"')
            ]
        )

    # ---------------------- SIERRA COMMUNITY ----------------------
    @http.route(['/medium-projects', '/medium-projects/page/<int:page>'], type='http', auth='public', website=True)
    def list_medium_communities(self, page=1, **kw):
        Community = request.env['sierra.community'].sudo()
        per_page = 12
        total = Community.search_count([])
        pager = request.website.pager(url='/medium-projects', total=total, page=page, step=per_page)
        communities = Community.search([], limit=per_page, offset=pager['offset'])
        user_lang = request.env.lang
        return request.render('liberia_family.community_list_sierra', {
            'communities': communities,
            'pager': pager,
            'user_lang': user_lang,
        })

    @http.route(['/medium-projects/<int:rec_id>'], type='http', auth='public', website=True)
    def medium_community_page(self, rec_id, **kw):
        record = request.env['sierra.community'].sudo().browse(rec_id)
        if not record.exists():
            return request.not_found()
        user_lang = request.env.lang
        return request.render('liberia_family.community_page_sierra', {
            'record': record,
            'user_lang': user_lang,
        })

    @http.route(['/community/download/<int:rec_id>'],
                type='http', auth='public', website=True)
    def download_community_file(self, rec_id, **kw):
        """Download attached binary file from sierra.community"""
        record = request.env['sierra.community'].sudo().browse(rec_id)
        if not record.exists() or not record.community_sierra_file:
            return request.not_found()

        # Decode the Base64 binary data
        try:
            file_content = base64.b64decode(record.community_sierra_file)
        except Exception:
            return request.not_found()

        # Get filename and content type
        file_name = record.community_file_filename or "ProjectFile"
        content_type, _ = mimetypes.guess_type(file_name)
        if not content_type:
            content_type = 'application/octet-stream'  # fallback for unknown types

        # Return downloadable response
        return request.make_response(
            file_content,
            headers=[
                ('Content-Type', content_type),
                ('Content-Length', str(len(file_content))),
                ('Content-Disposition', f'attachment; filename="{file_name}"')
            ]
        )

    # ---------------------- AFGHANISTAN COMMUNITY ----------------------
    @http.route(['/large-projects', '/large-projects/page/<int:page>'], type='http', auth='public', website=True)
    def list_large_communities(self, page=1, **kw):
        Community = request.env['afghanistan.community'].sudo()
        per_page = 12
        total = Community.search_count([])
        pager = request.website.pager(url='/large-projects', total=total, page=page, step=per_page)
        communities = Community.search([], limit=per_page, offset=pager['offset'])
        user_lang = request.env.lang
        return request.render('liberia_family.community_list_afghanistan', {
            'communities': communities,
            'pager': pager,
            'user_lang': user_lang,
        })

    @http.route(['/large-projects/<int:rec_id>'], type='http', auth='public', website=True)
    def large_community_page(self, rec_id, **kw):
        record = request.env['afghanistan.community'].sudo().browse(rec_id)
        if not record.exists():
            return request.not_found()
        user_lang = request.env.lang
        return request.render('liberia_family.community_page_afghanistan', {
            'record': record,
            'user_lang': user_lang,
        })

    @http.route(['/community/download/<int:rec_id>'],
                type='http', auth='public', website=True)
    def download_community_file(self, rec_id, **kw):
        """Download attached binary file from afghanistan.community"""
        record = request.env['afghanistan.community'].sudo().browse(rec_id)
        if not record.exists() or not record.community_afghanistan_file:
            return request.not_found()

        # Decode the Base64 binary data
        try:
            file_content = base64.b64decode(record.community_afghanistan_file)
        except Exception:
            return request.not_found()

        # Get filename and content type
        file_name = record.community_file_filename or "ProjectFile"
        content_type, _ = mimetypes.guess_type(file_name)
        if not content_type:
            content_type = 'application/octet-stream'  # fallback for unknown types

        # Return downloadable response
        return request.make_response(
            file_content,
            headers=[
                ('Content-Type', content_type),
                ('Content-Length', str(len(file_content))),
                ('Content-Disposition', f'attachment; filename="{file_name}"')
            ]
        )

    # ---------------------- FILE DOWNLOAD ----------------------
    @http.route(['/community/download/<string:country>/<int:rec_id>'], type='http', auth='public', website=True)
    def download_community_file(self, country, rec_id, **kw):
        """Download file depending on country"""
        model_map = {
            'liberia': 'liberia.community',
            'sierra': 'sierra.community',
            'afghanistan': 'afghanistan.community',
        }
        if country not in model_map:
            return request.not_found()

        record = request.env[model_map[country]].sudo().browse(rec_id)
        file_field_map = {
            'liberia.community': 'community_liberia_file',
            'sierra.community': 'community_sierra_file',
            'afghanistan.community': 'community_afghanistan_file',
        }
        file_field = file_field_map[record._name]



        if not record.exists() or not getattr(record, file_field):
            return request.not_found()

        try:
            file_content = base64.b64decode(getattr(record, file_field))
        except Exception:
            return request.not_found()

        file_name = getattr(record, 'community_file_filename', 'ProjectFile') or "ProjectFile"
        content_type, _ = mimetypes.guess_type(file_name)
        if not content_type:
            content_type = 'application/octet-stream'

        return request.make_response(
            file_content,
            headers=[
                ('Content-Type', content_type),
                ('Content-Length', str(len(file_content))),
                ('Content-Disposition', f'attachment; filename="{file_name}"')
            ]
        )


class ProjectController(http.Controller):

    @http.route('/support-project-level', type='http', auth='public', website=True)
    def projects_hub(self, **kw):

        Liberia = request.env['liberia.community'].sudo()
        Sierra = request.env['sierra.community'].sudo()
        Afghanistan = request.env['afghanistan.community'].sudo()

        user_lang = request.env.lang  # ex: 'en_US', 'de_DE'

        return request.render('liberia_family.projects_hub', {
            'communities_small': Liberia.search([]),
            'communities_medium': Sierra.search([]),
            'communities_large': Afghanistan.search([]),
            'user_lang': user_lang,
        })

    class CommunityDownloadController(http.Controller):

        @http.route(['/community/download/<string:country>/<int:rec_id>/<string:lang>'],
                    type='http', auth='public', website=True)
        def download_community_file(self, country, rec_id, lang='en', **kw):
            model_map = {
                'liberia': 'liberia.community',
                'sierra': 'sierra.community',
                'afghanistan': 'afghanistan.community',
            }

            if country not in model_map:
                return request.not_found()

            record = request.env[model_map[country]].sudo().browse(rec_id)
            if not record.exists():
                return request.not_found()

            # Determine the correct file field based on language
            file_field = None
            file_name_field = None

            if country == 'liberia':
                file_field = 'community_liberia_file_en' if lang == 'en' else 'community_liberia_file_de'
                file_name_field = 'community_file_filename_en' if lang == 'en' else 'community_file_filename_de'
            elif country == 'sierra':
                file_field = 'community_sierra_file_en' if lang == 'en' else 'community_sierra_file_de'
                file_name_field = 'community_file_filename_en' if lang == 'en' else 'community_file_filename_de'
            elif country == 'afghanistan':
                file_field = 'community_afghanistan_file_en' if lang == 'en' else 'community_afghanistan_file_de'
                file_name_field = 'community_file_filename_en' if lang == 'en' else 'community_file_filename_de'

            if not getattr(record, file_field, False):
                return request.not_found()

            try:
                file_content = base64.b64decode(getattr(record, file_field))
            except Exception:
                return request.not_found()

            file_name = getattr(record, file_name_field)
            content_type, _ = mimetypes.guess_type(file_name)
            if not content_type:
                content_type = 'application/octet-stream'

            return request.make_response(
                file_content,
                headers=[
                    ('Content-Type', content_type),
                    ('Content-Length', str(len(file_content))),
                    ('Content-Disposition', f'attachment; filename="{file_name}"')
                ]
            )



class SupportFamilyLevelController(http.Controller):

    # ---------------------- MAIN PAGE WITH ALL 3 TABS ----------------------
    @http.route('/support-family-level', type='http', auth='public', website=True)
    def support_family_page(self, **kw):

        Liberia = request.env['liberia.family'].sudo()
        Sierra = request.env['sierra.family'].sudo()
        Afghanistan = request.env['afghanistan.family'].sudo()

        user_lang = request.env.lang

        return request.render('liberia_family.support_family_level_tabs', {
            'families_small': Liberia.search([]),        # Liberia
            'families_medium': Sierra.search([]),        # Sierra Leone
            'families_large': Afghanistan.search([]),    # Afghanistan
            'active_level': "all",
            'user_lang': user_lang,
        })

    # ---------------------- SEPARATE PAGES (SMALL / MEDIUM / LARGE) ----------------------
    @http.route('/support-family-level/<string:level>', type='http', auth='public', website=True)
    def support_family_single_page(self, level, **kw):

        user_lang = request.env.lang

        model_map = {
            'small': 'liberia.family',
            'medium': 'sierra.family',
            'large': 'afghanistan.family',
        }

        if level not in model_map:
            return request.not_found()

        model = model_map[level]
        records = request.env[model].sudo().search([])

        # Only send data for the active tab
        return request.render('liberia_family.support_family_level_tabs', {
            'families_small': records if level == 'small' else [],
            'families_medium': records if level == 'medium' else [],
            'families_large': records if level == 'large' else [],
            'active_level': level,
            'user_lang': user_lang,
        })


    # ---------------------- DOWNLOAD FILE ----------------------
    @http.route('/support-family-level/download/<string:country>/<int:rec_id>',
                type='http', auth='public', website=True)
    def download_family_file(self, country, rec_id, **kw):

        model_map = {
            'liberia': 'liberia.family',
            'sierra': 'sierra.family',
            'afghanistan': 'afghanistan.family',
        }

        if country not in model_map:
            return request.not_found()

        record = request.env[model_map[country]].sudo().browse(rec_id)
        if not record.exists():
            return request.not_found()

        file_field = f'{country}_file'
        if not getattr(record, file_field, False):
            return request.not_found()

        import base64
        import mimetypes

        try:
            file_content = base64.b64decode(getattr(record, file_field))
        except Exception:
            return request.not_found()

        file_name = getattr(record, f'{country}_file_name', 'file.pdf')

        content_type, _ = mimetypes.guess_type(file_name)
        if not content_type:
            content_type = 'application/octet-stream'

        return request.make_response(
            file_content,
            headers=[
                ('Content-Type', content_type),
                ('Content-Length', str(len(file_content))),
                ('Content-Disposition', f'attachment; filename="{file_name}"')
            ]
        )
