# Copyright <2021> <Raimundo Pereira da Silva Junior <raimundopsjr@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo import models, fields
import re

import logging
logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__) #<<<<<<<<<<<<<<<<<<<<

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'
    tracker_device = fields.Many2one('tracker.device',
                                 string='Tracker Device',
                                 help="Tracker Device.")

    _sql_constraints = [
            ('tracker_device_uniq', 
            'unique(tracker_device)', 
            _('Este rastreador está sendo usado em outro veículo!')),
    ]

    @api.model
    def update_vehicle_odometer(self):
        # Get all vehicles from the database
        vehicles = self.search([])

        # Iterate over each vehicle and update its odometer value
        for vehicle in vehicles:
            # Get the Tracker Device associated with the vehicle
            tracker_device = vehicle.tracker_device

            # Call the traccar_api method to get the latest position of the device
            response = tracker_device._traccar_api('positions', payload={'limit': 1})

            #_logger.info(f"################ response {response}")


            # Extract the odometer value from the response
            odometer_value = int(response[0]['attributes'].get('totalDistance'))
            _logger.info(f"################ odometer_value {odometer_value}")
            odometer_value = str(int(odometer_value / 1000))
            #odometer_value = odometer_value.split('.')[0]

            _logger.info(f"################ odometer_value {odometer_value}")

            # Update the odometer field of the vehicle
            if odometer_value:
                if float(odometer_value) > vehicle.odometer:
                    vehicle.odometer = float(odometer_value)

        return True