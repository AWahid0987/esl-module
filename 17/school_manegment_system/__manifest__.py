{
    'name': 'School Management System',
    'version': '1.0',
    'category': 'Education',
    'summary': 'Manage school operations',

    'description': """
        School Management System
        =======================
        * Student Management
        * Class Management
        * Attendance Management
        * Fee Management
        * SMS Notifications
        * Sale Order Line Access Control
        * Third Party Intigration
    """,
    'author': 'Abdul Wahid',
    'website': 'linkedin.com/in/abdul-wahid-7aab6b240',
    'depends': [
        'base',
        'mail',
        'sms',
        'website',
        'sale',
        'om_account_accountant',
    ],
    'data': [
        'security/sale_security.xml',
        'data/sequences.xml',
        'security/ir.model.access.csv',
        'security/school_security.xml',
        'views/student_views.xml',
        'views/class_views.xml',
        'views/attendance_views.xml',
        'views/fee_views.xml',
        'views/website_templates.xml',
        'views/school_result_form.xml',
        'views/school_subject_views.xml',
        'views/fee_views.xml',
        'views/bank.xml',
        'views/exam.xml',
        'views/teacher.xml',
        'views/timetable.xml',
        'views/school_groups.xml',
        'reports/student_report_template.xml',
        'reports/school_result_report.xml',
        'reports/school_fee_report.xml',
        'reports/timetable.xml',
        'reports/salary_report.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
} 
