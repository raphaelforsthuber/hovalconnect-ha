"""Hoval Connect select entities."""
from __future__ import annotations
import logging
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, MANUFACTURER

_LOGGER = logging.getLogger(__name__)

PROGRAMS = ("week1", "week2", "constant", "ecoMode")

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    circuits = data["coordinator"].data.get("circuits", [])
    entities = [
        HovalProgramSelect(data["coordinator"], data["api"], data["plant_id"], c)
        for c in circuits if c.get("selectable") and c.get("type") in ("HK", "WW")
    ]
    async_add_entities(entities)

class HovalProgramSelect(CoordinatorEntity, SelectEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "program"
    _attr_options = list(PROGRAMS)

    def __init__(self, coordinator, api, plant_id, circuit):
        super().__init__(coordinator)
        self._api = api
        self._plant_id = plant_id
        self._path = circuit["path"]
        circuit_name = circuit.get("name") or circuit.get("type", "Circuit")
        if circuit_name.startswith(f"{MANUFACTURER} "):
            circuit_name = circuit_name[len(MANUFACTURER) + 1:]
        self._attr_translation_placeholders = {"circuit_name": circuit_name}
        self._attr_unique_id = f"hoval_{plant_id}_{self._path}_program"

    def _c(self):
        for c in self.coordinator.data.get("circuits", []):
            if c["path"] == self._path:
                return c
        return {}

    @property
    def current_option(self):
        active = self._c().get("activeProgram")
        return active if active in PROGRAMS else None

    async def async_select_option(self, option: str) -> None:
        await self._api.set_program(self._plant_id, self._path, option)
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self):
        c = self._c()
        return {
            "week_program": c.get("activeWeekProgramName"),
            "day_program":  c.get("activeDayProgramName"),
        }

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._plant_id)},
            "name": "Hoval Belaria Compact IR",
            "manufacturer": MANUFACTURER,
        }
