from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, REGIONS, UNIT
from .coordinator import CregCoordinator, MonthData

_DEVICE_INFO = DeviceInfo(
    identifiers={(DOMAIN, DOMAIN)},
    name="CREG Tariff",
    manufacturer="thomasgodon",
    configuration_url=(
        "https://www.creg.be/nl/consumenten/prijzen-en-tarieven"
        "/creg-tarief-voor-terugbetaling-thuisladen-bedrijfswagens"
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: CregCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []
    for region in REGIONS:
        entities.append(CregPriceSensor(coordinator, region))
        entities.append(CregAvg3mSensor(coordinator, region))
    entities.append(CregLastUpdatedSensor(coordinator))
    async_add_entities(entities)


def _data_as_dicts(data: list[MonthData]) -> list[dict]:
    return [
        {
            "year": row.year,
            "month": row.month,
            "flanders": {"price": row.flanders.price, "avg_3m": row.flanders.avg_3m},
            "brussels": {"price": row.brussels.price, "avg_3m": row.brussels.avg_3m},
            "wallonia": {"price": row.wallonia.price, "avg_3m": row.wallonia.avg_3m},
        }
        for row in data
    ]


class CregPriceSensor(CoordinatorEntity[CregCoordinator], SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UNIT
    _attr_suggested_display_precision = 2
    _attr_has_entity_name = False
    _attr_device_info = _DEVICE_INFO

    def __init__(self, coordinator: CregCoordinator, region: str) -> None:
        super().__init__(coordinator)
        self._region = region
        self._attr_unique_id = f"creg_tariff_{region}"
        self._attr_name = f"CREG Tariff {region.title()}"

    @property
    def native_value(self) -> float | None:
        return self.coordinator.latest_price(self._region)

    @property
    def extra_state_attributes(self) -> dict:
        data = self.coordinator.data or []
        latest = data[0] if data else None
        return {
            "data": _data_as_dicts(data),
            "latest_year": latest.year if latest else None,
            "latest_month": latest.month if latest else None,
        }


class CregAvg3mSensor(CoordinatorEntity[CregCoordinator], SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UNIT
    _attr_suggested_display_precision = 2
    _attr_has_entity_name = False
    _attr_device_info = _DEVICE_INFO

    def __init__(self, coordinator: CregCoordinator, region: str) -> None:
        super().__init__(coordinator)
        self._region = region
        self._attr_unique_id = f"creg_tariff_{region}_avg_3m"
        self._attr_name = f"CREG Tariff {region.title()} Avg 3M"

    @property
    def native_value(self) -> float | None:
        result = self.coordinator.latest_avg_3m(self._region)
        return result.value if result else None

    @property
    def extra_state_attributes(self) -> dict:
        result = self.coordinator.latest_avg_3m(self._region)
        if result is None:
            return {}
        return {"period_year": result.year, "period_month": result.month}


class CregLastUpdatedSensor(CoordinatorEntity[CregCoordinator], SensorEntity):
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = False
    _attr_device_info = _DEVICE_INFO
    _attr_unique_id = "creg_tariff_last_updated"
    _attr_name = "CREG Tariff Last Updated"

    @property
    def native_value(self) -> datetime | None:
        return self.coordinator.last_update_success_time
