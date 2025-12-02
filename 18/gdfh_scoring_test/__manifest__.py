{
    'name': 'GDfH Scoring Test',
    'version': '1.0',
    'author': 'Green It Hub',
    'website': 'https://github08.com/',
    'category': 'Website',
    'summary': 'Global Development for Humanity - Scoring Test',
    'description': """
        This module provides a scoring test for Global Citizenship.
    """,
    'depends': ['base', 'stock', 'website','web'],
    'data': [
        'security/ir.model.access.csv',
        'views/gdfh_templates.xml',
        'views/gdfh_backend_views.xml',
        'views/gdfh_member_menu.xml',
        'views/result.xml',
        'views/report_gdfh.xml',
        'views/templates.xml',
        'views/previous_results_template.xml',
    ],
    'assets': {
    'web.assets_frontend': [
        'views/assets.xml',
        'https://cdn.jsdelivr.net/npm/chart.js', 
    ],
},
    'installable': True,
    'application': True,
    'auto_install': False,
}
