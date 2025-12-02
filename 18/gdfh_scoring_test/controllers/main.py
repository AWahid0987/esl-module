from odoo import http
from odoo.http import request
import json

class GDFHScoringTestController(http.Controller):

    @http.route(['/GDfH_Scoring_Test'], type='http', auth='public', website=True)
    def show_form(self, **kw):
        return request.render('gdfh_scoring_test.form_template1')

    @http.route(['/GDfH_Scoring_Test/submit'], type='http', auth='public', website=True, csrf=False)
    def submit_form(self, **post):
        name = post.get('name')
        email = post.get('email')
        country = post.get('country')

        # Collect scores
        scores = {}
        for i in range(1, 19):
            try:
                scores[f"score_{i}"] = int(post.get(f"score_{i}", 0))
            except:
                scores[f"score_{i}"] = 0

        values = {
            "name": name,
            "email": email,
            "country": country,
            **scores
        }

        request.env['gdfh.result'].sudo().create(values)

        results = request.env['gdfh.result'].sudo().search(
            [('email', '=', email)], order="id desc"
        )

        return request.render("gdfh_scoring_test.result_template", {
            "results": results
        })

    @http.route(['/GDfH_Scoring_Test/previous_results'], type='http', auth='public', website=True, csrf=False)
    def previous_results(self, email=None):
        results = []
        if email:
            results = request.env['gdfh.result'].sudo().search(
                [('email', '=', email)], order="id desc"
            )
        return request.render('gdfh_scoring_test.previous_results_template', {
            'results': results,
            'email': email,
        })

    @http.route(['/GDfH_Scoring_Test/view_result/<int:result_id>'], type='http', auth='public', website=True)
    def view_result(self, result_id, **kwargs):
        result = request.env['gdfh.result'].sudo().browse(result_id)
        if not result.exists():
            return request.render('gdfh_scoring_test.no_result_template')
        return request.render('gdfh_scoring_test.view_result_template', {
            'results': [result],
        })

    @http.route(['/GDfH_Scoring_Test/fetch_result'], type='http', auth='public', csrf=False)
    def fetch_result(self, email=None, **kwargs):
        result = request.env['gdfh.result'].sudo().search([('email', '=', email)], limit=1, order='id desc')
        if result:
            return json.dumps({
                'found': True,
                'name': result.name,
                'email': result.email,
                'country': result.country,
                'total_score': result.total_score,
                'level': result.level
            })
        return json.dumps({'found': False})

    @http.route(['/GDfH_Scoring_Test/fetch_all_results'], type='http', auth='public', csrf=False)
    def fetch_all_results(self, email=None, **kwargs):
        records = request.env['gdfh.result'].sudo().search([('email', '=', email)], order="id desc")
        if records:
            return json.dumps({
                'found': True,
                'results': [{
                    'id': rec.id,
                    'name': rec.name,
                    'email': rec.email,
                    'country': rec.country,
                    'total_score': rec.total_score,
                    'level': rec.level
                } for rec in records]
            })
        return json.dumps({'found': False})

    @http.route(['/submit_donation'], type='http', auth='public', website=True, csrf=True)
    def submit_donation(self, **post):
        first_name = post.get('first_name', '')
        last_name = post.get('last_name', '')
        full_name = f"{first_name} {last_name}".strip()
        amount = float(post.get('amount') or 0)
        product_id = int(post.get('product_id') or 0)
        product = request.env['product.product'].sudo().browse(product_id)

        request.env['donation.record'].sudo().create({
            'donor_name': full_name,
            'email': post.get('email'),
            'phone': post.get('phone'),
            'street': post.get('street'),
            'city': post.get('city'),
            'state': post.get('state'),
            'zip': post.get('zip'),
            'country': post.get('country'),
            'amount': amount,
            'monthly': bool(post.get('monthly')),
            'product_id': product.id if product else False
        })

        return request.render('gdfh_scoring_test.thank_you_page', {
            'full_name': full_name,
            'amount': amount,
            'product_name': product.name if product else 'N/A',
        })

    @http.route('/gdfh/results', type='http', auth='public', website=True)
    def show_results(self, **kwargs):
        all_results = request.env['gdfh.result'].sudo().search([], order='create_date desc')
        grouped = {}
        for res in all_results:
            grouped.setdefault(res.email, []).append(res)
        return request.render('gdfh_scoring_test.gdfh_result_table', {
            'grouped_results': grouped
        })

    @http.route('/GDfH_Scoring_Test/fetch_result_by_email', type='json', auth='public')
    def fetch_result_by_email(self, email):
        result = request.env['gdfh.result'].sudo().search([('email', '=', email)], limit=1)
        if not result:
            return {'result': None}
        return {
            'result': {
                'global_awareness_pct': result.global_awareness_pct,
                'civic_participation_pct': result.civic_participation_pct,
                'environment_pct': result.environment_pct,
                'ethical_pct': result.ethical_pct,
                'peace_pct': result.peace_pct,
                'intercultural_pct': result.intercultural_pct,
            }
        }
