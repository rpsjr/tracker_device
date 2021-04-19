# Copyright <2021> <Raimundo Pereira da Silva Junior <raimundopsjr@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo import models, fields
import re

class TrackerDevice(models.Model):
    _name = 'tracker.device'
    _description = 'Tracker Device Management'

    name = fields.Char(compute="_compute_tracker_device_name", store=True)
    maker = fields.Char('Unit Maker')
    model = fields.Char('Unit Model')
    imei = fields.Char('Unit IMEI', required=True)
    #name = fields.Char('Unit IMEI')
    unit_pass = fields.Char('Unit Pass', required=True)
    m2m_network_id = fields.Many2one('phone.line',
                                 string='m2m Line Number',
                                 help="m2m network line number running the tracker.")
    vehicle_id = fields.Many2one('fleet.vehicle',
                                 string='Vehicle',
                                 help="Vehicle using the tracker unit.")
    admin_lines = fields.Char('Unit admin number lines', required=True)

    @api.depends('m2m_network_id', 'model')
    def _compute_tracker_device_name(self):
        for record in self:
            record.name = (record.m2m_network_id.name or '') + '/' + (record.model or '')

    @api.depends('m2m_network_id', 'model')
    def _compute_tracker_device_name(self):
        for record in self:
            record.name = (record.m2m_network_id.name or '') + '/' + (record.model or '')

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'
    tracker_device_id = fields.Many2one('tracker.device',
                                 string='Tracker Device',
                                 help="Tracker Device.")

class PhoneLine(models.Model):
    _name = 'phone.line'
    _description = 'Phone Line Management'

    name = fields.Char(compute="_compute_phone_line_name", store=True)
    tel_operator = fields.Selection([('claro', 'Claro'), ('oi', 'Oi'), ('tim', 'Tim'), ('vivo', 'Vivo')], 'Network Provider', help='Network Telephone Provider')
    #name = fields.Char('Unit Phone')
    phone_nr = fields.Char('Unit Phone')
    tel_operator_pass = fields.Char('Network Provider Pass')
    l10n_br_cnpj_cpf = fields.Char('CNPJ/CPF', size=20)
    tracker_device_id = fields.Many2one('tracker.device',
                                 string='Tracker Device',
                                 help="Tracker Device using the phone line.")

    @api.depends('tel_operator', 'phone_nr')
    def _compute_phone_line_name(self):
        for record in self:
            record.name = (record.phone_nr or '') + '/' + (record.tel_operator or '')

    @api.onchange('l10n_br_cnpj_cpf')
    def _onchange_l10n_br_cnpj_cpf(self):
        if self.l10n_br_cnpj_cpf:
            val = re.sub('[^0-9]', '', self.l10n_br_cnpj_cpf)
            if len(val) == 14:
                cnpj_cpf = "%s.%s.%s/%s-%s"\
                    % (val[0:2], val[2:5], val[5:8], val[8:12], val[12:14])
                self.l10n_br_cnpj_cpf = cnpj_cpf
            elif len(val) == 11:
                cnpj_cpf = "%s.%s.%s-%s"\
                    % (val[0:3], val[3:6], val[6:9], val[9:11])
                self.l10n_br_cnpj_cpf = cnpj_cpf
