# Copyright <2021> <Raimundo Pereira da Silva Junior <raimundopsjr@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
import re
import requests
import json
from datetime import datetime, timedelta, timezone

import logging
logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__) #<<<<<<<<<<<<<<<<<<<<

class TrackerDevice(models.Model):
    _name = 'tracker.device'
    _description = 'Tracker Device Management'

    name = fields.Char(compute="_compute_tracker_device_name", store=True)
    maker = fields.Char('Unit Maker')
    model = fields.Char('Unit Model')
    imei = fields.Char('Unit IMEI')
    unit_pass = fields.Char('Unit Pass')
    m2m_network_id = fields.Many2one('phone.line',
                                 string='m2m Line Number',
                                 help="m2m network line number running the tracker.")
    admin_lines = fields.Char('Unit admin lines')
    engine_last_cmd = fields.Selection([('blocked', 'Engine cut'), ('unblocked', 'Engine Resume')], 'Engine last command', help='Engine last command sent by odoo')
    vehicle_id = fields.Many2one('fleet.vehicle', compute='_compute_vehicle_id', inverse='_vehicle_id_inverse')
    vehicle_ids = fields.One2many('fleet.vehicle', 'tracker_device', string='vehicle_ids', ondelete='cascade')
    traccar_deviceId = fields.Char('Traccar deviceId')

    _sql_constraints = [
        ('vehicle_ids_uniq', 
        'unique(vehicle_ids)', 
        _('Este rastreador está sendo usado em outro veículo!')),
    ]

    def _fetch_traccar_deviceId(self):
        if not self.traccar_deviceId:
            device_status = self._traccar_api('devices', 'GET')
            self.write({'traccar_deviceId': device_status[0]["id"]})
        return self.traccar_deviceId      

    def stop_engine(self, only_stopped=True):
        """"
        The stop_engine method is responsible for sending the command to stop the 
        engine of a device. However, the method has been modified to only send the 
        engine stop command if the device's fixTime attribute is older than 30 minutes 
        or the device's speed is less than one. Additionally, when the block command 
        is sent, the engine_last_cmd field is updated to reflect that the command is 
        blocked. This method is useful in scenarios where it is necessary to prevent 
        the engine of a device from stopping when the device is in motion or has been 
        recently active. By checking the fixTime attribute and speed of the device, 
        the method ensures that the engine stop command is only sent when it is safe 
        to do so. The engine_last_cmd field provides a record of the last command 
        sent to the device, which can be useful for tracking and monitoring purposes.
        """

        device_positions = self._traccar_api('positions', 'GET')
        fix_time_str = device_positions[0]['fixTime']
        fix_time = datetime.strptime(fix_time_str, '%Y-%m-%dT%H:%M:%S.%f%z')
        now = datetime.now(timezone.utc)
        # check if device fixTime is older than 30 min or if device speed is less than one
        if now - fix_time > timedelta(minutes=30) or device_positions[0]['speed'] < 1:           
                # update engine_last_cmd field to blocked
                payload = {'type': 'engineStop', 'deviceId': self._fetch_traccar_deviceId()}
                response = self._traccar_api('commands/send', 'POST', payload)
                if response:
                    self.write({'engine_last_cmd': 'blocked'})
                    _logger.info(f"################ send_traccar_api_command response {response}")
                    return response
        else:
            _logger.warning('Device fixTime is less than 30 minutes old or Device speed is greater than or equal to 1')

    def resume_engine(self, only_stopped=True):
        """"
        The resume_engine method is responsible for sending the command to resume the 
        engine of a device. 
        """

        payload = {'type': 'engineResume', 'deviceId': self._fetch_traccar_deviceId}
        response = self._traccar_api('commands/send', 'POST', payload)
        if response:
            self.write({'engine_last_cmd': 'unblocked'})
            _logger.info(f"################ send_traccar_api_command response {response}")
            return response

    def _traccar_api(self, api_endpoint, request_type='GET', payload=None):
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
        params = self.env['ir.config_parameter'].sudo()
        api_url = str(params.get_param('fleet.traccar_api_url'))
        api_key = f"Bearer {str(params.get_param('fleet.traccar_api_key'))}"

        headers = {
        'Authorization': api_key,
        'Content-Type': 'application/json'
        }

        if not payload:
            payload = {}
        payload['uniqueId'] = self.imei

        url = f'{api_url}/api/{api_endpoint}'

        if request_type == 'GET':
            response = requests.get(url, headers=headers, params=payload)
        elif request_type == 'POST':
            response = requests.post(url, headers=headers, json=payload)
        elif request_type == 'PUT':
            response = requests.put(url, headers=headers, json=payload)
        elif request_type == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError('Invalid request type.')

        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError(f'Request failed with status code {response.status_code}.')

    @api.depends('vehicle_ids')
    def _compute_vehicle_id(self):
        
        for tracker in self:
            _logger.info(len(tracker.vehicle_ids))
            if len(tracker.vehicle_ids) > 0:
                tracker.vehicle_id = tracker.vehicle_ids[-1]

    def _vehicle_id_inverse(self):
        for tracker in self:
            if len(tracker.vehicle_ids) > 0:
                # delete previous reference
                for veic in tracker.vehicle_ids:
                    vehicle = self.env['fleet.vehicle'].browse(veic.id)
                    vehicle.tracker_device = False
                # set new reference
                tracker.vehicle_id.tracker_device = tracker

    @api.depends('m2m_network_id', 'model')
    def _compute_tracker_device_name(self):
        for record in self:
            record.name = (record.m2m_network_id.name or '') + '/' + (record.model or '')

    @api.depends('m2m_network_id', 'model')
    def _compute_tracker_device_name(self):
        for record in self:
            record.name = (record.m2m_network_id.name or '') + '/' + (record.model or '')