{
    "name": "Land Management System",
    "summary": "Comprehensive land plot management with automated commission calculation",
    "version": "19.0.1.0.0",
    "license": "LGPL-3",
    "author": "Abdul Wahid",
    "website": "https://www.linkedin.com/in/abdul-wahid-7aab6b240",


    "depends": ["purchase", "documents", "sale_management", "accountant", "stock", "base", "mail", "web"],

    "data": [
        # "security/ir.model.access.csv",
        # "views/assets.xml",
        # "views/plot_views.xml",
        # "views/menu.xml",
        # "views/automated_action.xml",
        # "views/sale_order_view.xml",
        # "views/purchase_land_views.xml",
        # "views/product_land_view.xml",
        "views/account_move.xml",
        # "views/res_partner.xml",
        "views/sale_advance_payment_inv_view.xml",
        # "views/sale_commission_line_inherit.xml",
        # "views/land_project_summary_views.xml",
        "reports/proforma_invoice.xml",
        "reports/sale_order_reports.xml",
        "reports/statement_of_account.xml",
        # "report/sale_user_report.xml",
        # "report/report_saleorder.xml",
        # "report/payment_report.xml",
        # "report/file_report.xml",
        # "report/email_template.xml",
        # "report/challan_report.xml",
        # "data/corn.xml",
        # "data/ir_sequence_data.xml",
        # "data/commission_sequence.xml",

    ],

    # "assets": {
    #     "web.assets_backend": [
    #         "land_plot_manager/static/src/js/hide_duplicate.js",
    #     ],
    # },
    # "images": [
    #     "static/description/icon.png",
    # ],
    "application": True,
    "installable": True,
}
