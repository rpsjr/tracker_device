# Copyright 2021 - TODAY, RPSJR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "GPS Track Device",
    "summary": """
        This is a bridge module ....""",
    "version": "13.0.1.0.0",
    "category": "Human Resources/Fleet",
    "license": "AGPL-3",
    "author": "RPSJR",
    "maintainers": ["rpsjr"],
    "website": "https://github.com/",
    "depends": [
        "fleet",
        "base",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/fleet_vehicle_views.xml",
        "views/tracker_device_views.xml",
        "views/phone_line_views.xml",
    ],
    "demo": [],
}
