# -*- coding: utf-8 -*-
{
 'name': 'FBR Digital Invoicing Connector',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Localization',
    'summary': 'Pakistan FBR (Federal Board of Revenue) Integration for Tax Compliance under SRO 709',
    'description': """
Pakistan FBR Integration Module
===============================

This module provides integration with Pakistan's Federal Board of Revenue (FBR) system under SRO 709 for:

* FBR Invoice Integration
* Tax Compliance Management
* Reference Data Management (UOM, Provinces, Document Types, etc.)
* Sales Tax Return Filing
* Purchase Tax Management
* FBR Rate Configuration
* SRO (Statutory Regulatory Orders) Management

Key Features:
-------------
* Complete FBR reference data setup
* Automated invoice data submission to FBR
* Tax calculation as per FBR rules
* Compliance reporting
* Province-wise tax management
* Document type classification
* Buyer type categorization
* Sales scenarios management

    """,
    'author': 'EBITDA SOLUTIONS LLP',
    'website': 'https://www.ebitdasolutions.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'account',
        'stock',
        'product',
        "contacts"
    ],

    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "data/config_data.xml",
        "data/fbr_buyer_type_data.xml",
        "data/fbr_document_type_data.xml",
        "data/fbr_province_data.xml",
        "data/fbr_reason_data.xml",
        "data/fbr_sale_type_data.xml",
        "data/fbr_scenarios_data.xml",
        "data/fbr_sro_data.xml",
        "data/fbr_uom_data.xml",
        "data/fbr_sro_item_serial_data.xml",
        "views/fbr_uom_views.xml",
        "views/account_move_line_views.xml",
        # "views/account_move_views.xml",
        "views/account_move_views_copy.xml",
        "views/fbr_buyer_type_views.xml",
        "views/fbr_document_type_views.xml",
        "views/fbr_province_views.xml",
        "views/fbr_reason_views.xml",
        "views/fbr_sale_type_views.xml",
        "views/fbr_scenarios_views.xml",
        "views/fbr_sro_item_serial_views.xml",
        "views/fbr_sro_views.xml",
        "views/menus.xml",
        "views/product_template_views.xml",
        "views/res_partner_views.xml",
        "views/templates.xml",
        "reports/invoice_report_template.xml",
    ],

    # Assets and Images
    'assets': {
        'web.assets_backend': [],
        'web.assets_frontend': [],
    },

   'images': [
        'static/description/Cover.jpeg',
    ],

     # Module configuration
    'installable': True,
    'application': True,
    'auto_install': False,
    'external_dependencies': {
        'python': ['qrcode', 'requests', 'Pillow'],
    },
    'price': 390.00,
    'currency': 'USD',
    'maintainers': ['EBITDA SOLUTIONS LLP'],
}

