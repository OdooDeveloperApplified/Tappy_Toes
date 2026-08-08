{
    "name": "Tappy Saturday Attendance",
    "version": "1.0",
    "summary": "Manage Saturday Attendance Rota",
    "description": "Module to manage Saturday working schedule for employees without affecting existing workflow.",
    "category": "Human Resources/Attendance",
    "author": "Antigravity",
    "depends": ["hr_attendance", "tappy_attendance"],
    "data": [
        "security/ir.model.access.csv",
        "views/saturday_rota_views.xml",
        "views/attendance_report_inherit_views.xml",
        "views/hr_attendance_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
