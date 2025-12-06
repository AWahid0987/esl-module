{
   'name': 'Donations',
   'version': '17.0.0.1',
   'summary': """Dontation system """,
   'description': """Dontation system   """,
   'category': 'Generic Modules/Human Resources',
   'author': 'AmazeWorks Technologies, Ahad Rasool',
   'company': 'AmazeWorks Technologies',
   'website': "https://www.odoospecialist.com",
   'depends': ['base','base_setup','product','account','stock','sales_team'],
   'data': [
        # 'security/own_record.xml',
        'security/groups.xml',
      'security/ir.model.access.csv',
      'data/sequence.xml',
      'views/donation_order.xml',
      'views/res_partner.xml',
      'views/print.xml',
      'views/donation_report_tree_views.xml',
      'views/donation_report_wizard_views.xml',

      'report/report_template.xml',



   ],
   'assets': {
       'web.assets_backend': [
           "/aw_donation_management/static/src/css/style.css",
       ],
       'web.report_assets_common': [
           "/aw_donation_management/static/src/css/style.css",
       ],
   },

   'installable': True,
   'auto_install': False,
   'application': False,
}
