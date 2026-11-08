# Copyright 2021 - TODAY, RPSJR <raimundops.jr@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class FleetVehicleInspectionTraccarWizard(models.TransientModel):
    _name = "fleet.vehicle.inspection.traccar.wizard"
    _description = "Aviso de Replicação de Odômetro para o Traccar"

    inspection_id = fields.Many2one(
        "fleet.vehicle.inspection",
        string="Vistoria",
        required=True,
        readonly=True,
        ondelete="cascade",
    )
    vehicle_id = fields.Many2one(
        "fleet.vehicle",
        string="Veículo",
        required=True,
        readonly=True,
    )
    tracker_device_id = fields.Many2one(
        "tracker.device",
        string="Rastreador",
        readonly=True,
    )
    inspection_odometer = fields.Float(
        string="Odômetro na Inspeção (km)",
        readonly=True,
    )
    traccar_odometer = fields.Float(
        string="Odômetro no Traccar (km)",
        readonly=True,
    )
    confirm_inspection = fields.Boolean(
        string="Confirmar Vistoria após decisão",
        default=False,
        readonly=True,
    )

    def action_apply_traccar_odometer(self):
        """Replica o valor de odômetro no Traccar e confirma a inspeção se aplicável."""
        self.ensure_one()
        self.inspection_id.action_sync_odometer_to_traccar()
        if self.confirm_inspection and self.inspection_id.state in ("draft", "cancel"):
            self.inspection_id.with_context(
                skip_traccar_odometer_check=True
            ).button_confirm()
        return {"type": "ir.actions.act_window_close"}

    def action_skip_traccar_odometer(self):
        """Mantém o odômetro do Traccar inalterado e confirma a inspeção se aplicável."""
        self.ensure_one()
        if self.confirm_inspection and self.inspection_id.state in ("draft", "cancel"):
            self.inspection_id.with_context(
                skip_traccar_odometer_check=True
            ).button_confirm()
        return {"type": "ir.actions.act_window_close"}

