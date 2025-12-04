{
    "name": "Liberia Family Website",
    "version": "18.0.1.0.0",
    "summary": "Show family project cards on website at /Liberia-family",
    "description": "Manage family profiles and display them on the website page /Liberia-family.",
    "category": "Website",
    "author": "EBITDA Solutions LLP",
    "website": "https://www.ebitdasolutions.com/",
    "license": "LGPL-3",
    "depends": ["base", "website"],
    "data": [
        "security/ir.model.access.csv",
        "views/liberia_family_views.xml",
        "views/templates.xml",
        "views/assets.xml",
        # "views/sierra_family_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "/liberia_family/static/src/scss/style.scss",
        ],
    },
    "images": [
        "static/description/icon.png"
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
