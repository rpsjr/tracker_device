# Copyright 2021 - TODAY, RPSJR raimundops.jr@gmail.com
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "GPS Tracker Device",
    "summary": """
        This is a bridge module ....""",
    "version": "13.0.1.0.3",
    "category": "Human Resources/Fleet",
    "license": "AGPL-3",
    "author": "RPSJR",
    "maintainers": ["rpsjr"],
    "website": "https://github.com/rpsjr/tracker_device",
    "depends": [
        "fleet",
        "base",
    ],
    "data": [
        "views/fleet_vehicle_views.xml",
        "views/tracker_device_views.xml",
        "views/phone_line_views.xml",
        "security/ir.model.access.csv",
    ],
    "demo": [],
}
