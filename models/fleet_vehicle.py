# Copyright <2021> <Raimundo Pereira da Silva Junior <raimundopsjr@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""fleet_vehicle.py"""
import logging

from odoo import _, api, fields, models

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)  # <<<<<<<<<<<<<<<<<<<<


class FleetVehicle(models.Model):
    """fleet.vehicle is a class that inherits from the fleet.vehicle class"""

    _inherit = "fleet.vehicle"
    tracker_device = fields.Many2one(
        "tracker.device", string="Tracker Device", help="Tracker Device."
    )

    _sql_constraints = [
        (
            "tracker_device_uniq",
            "unique(tracker_device)",
            _("Este rastreador está sendo usado em outro veículo!"),
        ),
    ]

    @api.model
    def update_vehicle_odometer(self):
        """update_vehicle_odometer is a method
        that updates the odometer value of all
        vehicles"""
        # Get all vehicles from the database
        vehicles = self.search([])

        # Iterate over each vehicle and update its odometer value
        for vehicle in vehicles:
            vehicle.tracker_device._update_vehicle_odometer()
