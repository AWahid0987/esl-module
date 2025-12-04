{
    'name': 'Geolocation in HR Attendance',
    'version': '17.0.1.0.1',
    'summary': "The attendance location of the employee",
    'author': 'Abdul Wahid',
    'maintainer': 'Abdul Wahid',
    'company': 'Ebitda Solutions',
    'website': 'https://www.ebitdasolutions.com',
    'category': 'Human Resources',
    'depends': ['base', 'hr', 'hr_attendance'],
    'data': [
        'views/hr_attendance_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_attendance/static/src/js/my_attendances.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'external_dependencies': {'python': ['geopy']},
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
