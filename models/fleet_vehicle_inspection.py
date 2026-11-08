# Copyright 2021 - TODAY, RPSJR <raimundops.jr@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class FleetVehicleInspection(models.Model):
    _inherit = "fleet.vehicle.inspection"

    @api.model
    def default_get(self, fields_list):
        res = super(FleetVehicleInspection, self).default_get(fields_list)
        vehicle_id = res.get("vehicle_id") or self.env.context.get("default_vehicle_id")
        if vehicle_id:
            vehicle = self.env["fleet.vehicle"].browse(vehicle_id)
            if vehicle.exists():
                max_odometer = vehicle.get_max_odometer_odoo_traccar()
                current_odometer = float(res.get("odometer") or 0.0)
                if max_odometer > current_odometer:
                    res["odometer"] = max_odometer
        return res

    @api.onchange("vehicle_id")
    def _onchange_vehicle_id_set_max_odometer(self):
        if self.vehicle_id:
            max_odometer = self.vehicle_id.get_max_odometer_odoo_traccar()
            if max_odometer > 0:
                self.odometer = max_odometer
            if self.vehicle_id.odometer_unit:
                self.odometer_unit = self.vehicle_id.odometer_unit

    @api.model
    def create(self, vals):
        vehicle_id = vals.get("vehicle_id")
        if vehicle_id:
            vehicle = self.env["fleet.vehicle"].browse(vehicle_id)
            if vehicle.exists():
                max_odometer = vehicle.get_max_odometer_odoo_traccar()
                current_odometer = float(vals.get("odometer") or 0.0)
                best_odometer = max(current_odometer, max_odometer)
                if best_odometer > 0:
                    vals["odometer"] = best_odometer
        return super(FleetVehicleInspection, self).create(vals)

    def _prepare_traccar_odometer_wizard_action(self, confirm_inspection=False):
        """Verifica se o odômetro da inspeção é maior que o do Traccar.
        Se for maior, cria o wizard de confirmação e retorna a action modal.
        Caso contrário, retorna False.
        """
        self.ensure_one()
        if not self.vehicle_id or not self.vehicle_id.tracker_device:
            return False
        if not self.odometer or self.odometer <= 0:
            return False

        traccar_odometer = self.vehicle_id.get_traccar_odometer_km()
        if traccar_odometer is None:
            return False

        if float(self.odometer) > float(traccar_odometer):
            wizard = self.env["fleet.vehicle.inspection.traccar.wizard"].create(
                {
                    "inspection_id": self.id,
                    "vehicle_id": self.vehicle_id.id,
                    "tracker_device_id": self.vehicle_id.tracker_device.id,
                    "inspection_odometer": float(self.odometer),
                    "traccar_odometer": float(traccar_odometer),
                    "confirm_inspection": bool(confirm_inspection),
                }
            )
            return {
                "name": _("Atualizar Odômetro no Traccar?"),
                "type": "ir.actions.act_window",
                "res_model": "fleet.vehicle.inspection.traccar.wizard",
                "view_mode": "form",
                "res_id": wizard.id,
                "target": "new",
            }
        return False

    def action_check_traccar_odometer_on_save(self):
        """Chamado após salvar a inspeção no formulário para verificar se o
        odômetro informado é maior que o do Traccar e exibir o aviso de confirmação.
        """
        self.ensure_one()
        return self._prepare_traccar_odometer_wizard_action(confirm_inspection=False)

    def action_sync_odometer_to_traccar(self):
        """Replica o valor de odômetro da inspeção para o dispositivo no Traccar."""
        self.ensure_one()
        if not self.vehicle_id or not self.vehicle_id.tracker_device:
            raise UserError(
                _("O veículo não possui um rastreador (Tracker Device) vinculado.")
            )
        if not self.odometer or self.odometer <= 0:
            raise UserError(
                _(
                    "O valor do odômetro deve ser maior que zero para sincronizar com o Traccar."
                )
            )
        ok = self.vehicle_id.set_traccar_odometer_km(self.odometer)
        if not ok:
            raise UserError(
                _(
                    "Não foi possível atualizar o odômetro no Traccar. "
                    "Verifique a conexão e as configurações da API do Traccar."
                )
            )
        self.with_context(allow_confirmed_inspection_system_write=True).message_post(
            body=_(
                "Odômetro replicado no Traccar a partir da vistoria <b>%s</b>: <b>%.2f km</b>."
            )
            % (self.name, self.odometer)
        )
        return True

    def button_confirm(self):
        if any(not rec.inspection_line_ids for rec in self) or any(
            line.result == "todo" for line in self.mapped("inspection_line_ids")
        ):
            raise UserError(
                _("Inspection cannot be completed. There are uninspected items.")
            )
        if any(rec.state not in ["draft", "cancel"] for rec in self):
            raise ValidationError(
                _("Only inspections in 'draft' or 'cancel' states can be confirmed")
            )
        if not self.env.context.get("skip_traccar_odometer_check") and len(self) == 1:
            wizard_action = self._prepare_traccar_odometer_wizard_action(
                confirm_inspection=True
            )
            if wizard_action:
                return wizard_action
        return super(FleetVehicleInspection, self).button_confirm()

