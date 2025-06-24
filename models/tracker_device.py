"""tracker_device.py"""
# Copyright <2021> <Raimundo Pereira da Silva Junior <raimundopsjr@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime, timedelta, timezone

import requests
from requests.exceptions import HTTPError

from odoo import _, api, fields, models

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)  # <<<<<<<<<<<<<<<<<<<<


class TrackerDevice(models.Model):
    """Tracker Device Management"""

    _name = "tracker.device"
    _description = "Tracker Device Management"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(compute="_compute_tracker_device_name", store=True)
    maker = fields.Char("Unit Maker")
    model = fields.Char("Unit Model")
    imei = fields.Char(
        "Unit IMEI",
        track_visibility="onchange",
    )
    unit_pass = fields.Char("Unit Pass")
    m2m_network_id = fields.Many2one(
        "phone.line",
        string="m2m Line Number",
        help="m2m network line number running the tracker.",
    )
    admin_lines = fields.Char("Unit admin lines")
    engine_last_cmd = fields.Selection(
        [("blocked", "Engine cut"), ("unblocked", "Engine Resume")],
        "Engine last command",
        help="Engine last command sent by odoo",
        track_visibility="onchange",
    )
    vehicle_id = fields.Many2one(
        "fleet.vehicle", compute="_compute_vehicle_id", inverse="_inverse_vehicle_id"
    )
    vehicle_ids = fields.One2many(
        "fleet.vehicle",
        "tracker_device",
        string="vehicle_ids",
        ondelete="cascade",
    )
    traccar_deviceId = fields.Char(
        "Traccar deviceId",
        track_visibility="onchange",
    )

    _sql_constraints = [
        (
            "vehicle_ids_uniq",
            "unique(vehicle_ids)",
            _("Este rastreador está sendo usado em outro veículo!"),
        ),
    ]

    def _fetch_traccar_device_id(self):
        if not self.traccar_deviceId:
            device_status = self._traccar_api("devices", "GET").json()
            self.write({"traccar_deviceId": device_status[0]["id"]})
        return self.traccar_deviceId

    def queue_notification(self):
        return self.env.user.notify_info(
                        message='Command accepted but not yet processed. Cod. 202',
                        title=_('Alerta!'),
                        sticky=False,
                        display_type='info',
                        message_type='info',
                    )

    def stop_engine(self, safe_not_moving_vehicle=True):
        """
        Sends a command to stop the device's engine after a safety check.

        The command is only sent if the vehicle is considered safe to stop. The
        safety conditions are:
        1. The last position update (`fixTime`) is older than a set threshold
        (e.g., 30 minutes), indicating the vehicle has been inactive.
        2. The vehicle's 'motion' attribute is False.

        If the safety conditions are met, the stop command is sent to the Traccar
        API, and the device's `engine_last_cmd` field is updated to 'blocked'.
        """
        
        device_positions = self._traccar_api("positions", "GET").json()
        fix_time_str = device_positions[0]["fixTime"]
        fix_time = datetime.strptime(fix_time_str, "%Y-%m-%dT%H:%M:%S.%f%z")
        now = datetime.now(timezone.utc)
        motion = device_positions[0]["attributes"]["motion"]
        # check if device is moving
        if not (
            now - fix_time > timedelta(minutes=10)
            or motion
            ):
                safe_not_moving_vehicle = False

        if safe_not_moving_vehicle:
            # update engine_last_cmd field to blocked
            payload = {
                "type": "engineStop",
                "deviceId": self._fetch_traccar_device_id(),
            }
            response = self._traccar_api("commands/send", "POST", payload)
            if response:
                if response.status_code == 202:
                    self.queue_notification()
                    _logger.warning(_(f"TrackerDevice ID {self.id}: Command accepted but not yet processed."))
                self.write({"engine_last_cmd": "blocked"})
                return response.json()
        else:
            _logger.warning(
                f"TrackerDevice {self.id} is not safe to stop, fixTime is less than 30 minutes old or speed is greater than or equal to 1km/h"
            )

    def resume_engine(self, safe_not_moving_vehicle=True):
        """ "
        The resume_engine method is responsible for sending
        the command to resume the engine of a device.
        """
        if safe_not_moving_vehicle:
            payload = {
                "type": "engineResume",
                "deviceId": self._fetch_traccar_device_id(),
            }
            response = self._traccar_api("commands/send", "POST", payload)
            if response:
                if response.status_code == 202:
                    self.queue_notification()
                    _logger.warning(_(f"TrackerDevice ID {self.id}: Command accepted but not yet processed."))
                self.write({"engine_last_cmd": "unblocked"})
                return response.json()

    def toggle_engine_status(self, safe_not_moving_vehicle=True):
        """This method is responsible for toggling
        the engine status of a device between blocked
        and unblocked"""
        if self.engine_last_cmd == "unblocked":
            self.stop_engine(safe_not_moving_vehicle)
        else:
            self.resume_engine(safe_not_moving_vehicle)

    def _traccar_api(self, api_endpoint, request_type="GET", payload=None):
        """
        Sends a Traccar API command to the specified endpoint.

        Parameters:
        api_endpoint (str): The Traccar API endpoint to send the command to.
        api_key (str): The Traccar API key to use for authentication.
        request_type (str): The HTTP request type (e.g. 'GET', 'POST', etc.).
        payload (dict): The payload to send with the request (optional).

        Returns:
        dict: The JSON response from the API.
        """
        params = self.env["ir.config_parameter"].sudo()
        api_url = str(params.get_param("fleet.traccar_api_url"))
        api_key = f"Bearer {str(params.get_param('fleet.traccar_api_key'))}"

        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if not payload:
            payload = {}
        payload["uniqueId"] = self.imei

        url = f"{api_url}/api/{api_endpoint}"
        # _logger.info(f"################ send_traccar_api_command url {url}")
        if request_type == "GET":
            response = requests.get(url, headers=headers, params=payload, timeout=5000)
        elif request_type == "POST":
            response = requests.post(url, headers=headers, json=payload, timeout=5000)
        elif request_type == "PUT":
            response = requests.put(url, headers=headers, json=payload, timeout=5000)
        elif request_type == "DELETE":
            response = requests.delete(url, headers=headers, timeout=5000)
        else:
            _logger.warning(f'Invalid request type: {request_type}')
            raise ValueError(f'Invalid request type: {request_type}')

        try:
            # If the response was successful, no Exception will be raised
            response.raise_for_status()

        except HTTPError as http_err:
            _logger.warning(f'HTTP error occurred: {http_err}')  # Python 3.6+
            _logger.warning(f'payload: {payload}')
            # The 'http_err' object contains the response, so you can inspect it
            _logger.warning(f'Status Code: {http_err.response.status_code}')
            return False

        except Exception as err:
            _logger.warning(f'Other error occurred: {err}')
            _logger.warning(f'payload: {payload}')
            return False

        else:
            # This block runs only if the 'try' block was successful (no exceptions)
            return response

    @api.depends("vehicle_ids")
    def _compute_vehicle_id(self):

        for tracker in self:

            if len(tracker.vehicle_ids) > 0:

                tracker.vehicle_id = tracker.vehicle_ids[-1]

            elif len(tracker.vehicle_ids) == 0:
                tracker.vehicle_id = None

    def _inverse_vehicle_id(self):
        for tracker in self:

            if len(tracker.vehicle_ids) > 0:
                # delete previous reference
                for veic in tracker.vehicle_ids:
                    vehicle = self.env["fleet.vehicle"].browse(veic.id)
                    vehicle.tracker_device = False
                # set new reference
                tracker.vehicle_id.tracker_device = tracker

    @api.depends("m2m_network_id", "model")
    def _compute_tracker_device_name(self):
        for record in self:
            record.name = (
                (record.m2m_network_id.name or "") + "/" + (record.model or "")
            )

    @api.depends("vehicle_id", "imei")
    def _update_vehicle_odometer(self):
        if self.vehicle_id and self.imei:
            # Call the traccar_api method to get
            #  the latest position of the device
            response = None
            payload = {"deviceId": self._fetch_traccar_device_id(), "limit": 1}
            response = self._traccar_api("positions", payload=payload)
            if response:

                # Extract the odometer value from the response
                odometer_value = response.json()[0]["attributes"].get("totalDistance")
                odometer_value = int(odometer_value)
                odometer_value = str(int(odometer_value / 1000))

                # Update the odometer field of the vehicle
                if odometer_value:
                    if float(odometer_value) > self.vehicle_id.odometer:
                        self.vehicle_id.odometer = float(odometer_value)

                        return True
