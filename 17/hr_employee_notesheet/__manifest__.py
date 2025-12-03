{
    "name": "Employee Notesheet ",
    "version": "17.0.1.0.0",
    "category": "Employee Ration",
    "website": "https://ebitdasolutions.com/",
    "author": "Ebitda Solutions",
    "summary": "Create Custom Ration Report in Employee Ration",
    "depends": ["hr"],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_employee_notesheet_views.xml",
    ],
    'assets': {
        'web.assets_backend': [
            'hr_employee_notesheet/static/src/css/urdu_font.css',
            'hr_employee_notesheet/static/src/css/notesheet.css',
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,

}
