# Copyright 2021 - TODAY, RPSJR raimundops.jr@gmail.com
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "GPS Tracker Device",
    "summary": """
        Integração com Traccar para rastreadores GPS, controle de ignição e sincronização bidirecional de odômetro em vistorias.""",
    "version": "13.0.1.1.0",
    "category": "Human Resources/Fleet",
    "license": "AGPL-3",
    "author": "RPSJR",
    "maintainers": ["rpsjr"],
    "website": "https://github.com/rpsjr/tracker_device",
    "depends": [
        "fleet",
        "fleet_vehicle_inspection",
        "base",
        "web",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/assets.xml",
        "views/fleet_vehicle_views.xml",
        "views/tracker_device_views.xml",
        "views/phone_line_views.xml",
        "views/fleet_vehicle_inspection_traccar_wizard_views.xml",
    ],
    "demo": [],
}
