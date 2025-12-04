# -*- encoding: utf-8 -*-

{
    "name": "Custom Payment",
    "version": "18.0",
    "author": "Ebitda Solutions LLP",
    "website": "www.ebitdasolutions.com",
    "depends": ['base', 'account_payment', 'account', 'mail'],
    "category": "payment",
    "description": """Custom Payment module with approval workflow.""",
    "data": [
        # First, load groups
        "security/security.xml",
        "security/payment_rule.xml",

        # Then, access rights
        "security/ir.model.access.csv",

        # Views
        "views/sequcence.xml",
        "views/payment.xml",
        "views/payment_recieve.xml",
        "views/account_move_views.xml",
        "views/account_account_minimal_view.xml",
    ],
    "license": "AGPL-3",
    "auto_install": False,
    "installable": True,
    "application": True,
}
