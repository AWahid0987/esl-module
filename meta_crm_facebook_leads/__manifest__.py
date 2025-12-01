# {
#     'name': "CRM Meta Lead Ads",
#     'summary': "Sync Facebook Leads with Odoo CRM",
#     'description': """
#         Automatically sync Facebook Lead Ads into Odoo CRM.
#     """,

#     'author': "EBITDA SOLUTIONS LLP",
#     'website': "https://www.ebitdasolutions.com/",
    
#     'category': 'Lead Automation',
#     'version': '18.0.18.0',

#     'depends': ['crm','base'],

#     'license': 'LGPL-3',

#     'images': ['static/description/banner.gif'],

#     'data': [
#         'data/ir_cron.xml',
#         'data/crm.facebook.form.mapping.csv',
#         'security/ir.model.access.csv',
#         'views/crm_view.xml',
#         'views/res_config_settings_views.xml',
#     ],

#     'assets': {
#         'web.assets_frontend': [
            
#             'meta_crm_facebook_leads\static\src\scss\style.css',
#             'meta_crm_facebook_leads\static\src\js\script.js',
  
#         ],
#     },

#     'installable': True,
#     'auto_install': False,
#     'application': True,
# }
{
    'name': "CRM Meta Lead Ads",
    'summary': "Sync Facebook Leads with Odoo CRM",
    'description': """
        Automatically sync Facebook Lead Ads into Odoo CRM.
    """,
    'author': "EBITDA SOLUTIONS LLP",
    'website': "https://www.ebitdasolutions.com/",
    'category': 'Lead Automation',
    'version': '18.0.18.0',
    'depends': ['crm','base'],
    'license': 'LGPL-3',
    'images': ['static/description/banner.gif'],
    'data': [
        'data/ir_cron.xml',
        'data/crm.facebook.form.mapping.csv',
        'security/ir.model.access.csv',
        'views/crm_view.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'meta_crm_facebook_leads/static/src/js/script.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
}
