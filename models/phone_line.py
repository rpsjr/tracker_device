# Copyright <2021> <Raimundo Pereira da Silva Junior <raimundopsjr@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo import models, fields
import re

class PhoneLine(models.Model):
    _name = 'phone.line'
    _description = 'Phone Line Management'

    name = fields.Char(compute="_compute_phone_line_name", store=True)
    tel_operator = fields.Selection([('claro', 'Claro'), ('oi', 'Oi'), ('tim', 'Tim'), ('vivo', 'Vivo')], 'Network Provider', help='Network Telephone Provider')
    phone_nr = fields.Char('Line Number', required=True)
    tel_operator_plan = fields.Char('Plan', default='Easy')
    tel_operator_user = fields.Char('Plan Login')
    tel_operator_pass = fields.Char('Plan Pass')
    l10n_br_cnpj_cpf = fields.Char('CNPJ/CPF', size=20)
    holder = fields.Char('Line Holder')
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
