import pytest
from pathlib import Path
from unittest.mock import patch

from custom_components.creg.const import DOMAIN, UNIT, REGIONS
from custom_components.creg.coordinator import _parse_csv

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "creg_tariff_ev.csv"


def _fixture_data():
    text = FIXTURE_PATH.read_text(encoding="utf-8-sig")
    return _parse_csv(text)


@pytest.mark.asyncio
async def test_price_sensors_created(hass, config_entry):
    data = _fixture_data()
    with patch(
        "custom_components.creg.coordinator.CregCoordinator._async_update_data",
        return_value=data,
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    for region in REGIONS:
        state = hass.states.get(f"sensor.creg_tariff_{region}")
        assert state is not None, f"Missing entity sensor.creg_tariff_{region}"
        assert state.attributes.get("unit_of_measurement") == UNIT


@pytest.mark.asyncio
async def test_avg_3m_sensors_created(hass, config_entry):
    data = _fixture_data()
    with patch(
        "custom_components.creg.coordinator.CregCoordinator._async_update_data",
        return_value=data,
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    for region in REGIONS:
        state = hass.states.get(f"sensor.creg_tariff_{region}_avg_3m")
        assert state is not None, f"Missing entity sensor.creg_tariff_{region}_avg_3m"
        assert state.attributes.get("unit_of_measurement") == UNIT


@pytest.mark.asyncio
async def test_price_sensor_state_matches_latest_csv(hass, config_entry):
    data = _fixture_data()
    with patch(
        "custom_components.creg.coordinator.CregCoordinator._async_update_data",
        return_value=data,
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    assert float(hass.states.get("sensor.creg_tariff_flanders").state) == pytest.approx(32.71)
    assert float(hass.states.get("sensor.creg_tariff_brussels").state) == pytest.approx(37.64)
    assert float(hass.states.get("sensor.creg_tariff_wallonia").state) == pytest.approx(38.38)


@pytest.mark.asyncio
async def test_avg_3m_sensor_state_matches_latest_quarterly(hass, config_entry):
    data = _fixture_data()
    with patch(
        "custom_components.creg.coordinator.CregCoordinator._async_update_data",
        return_value=data,
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    assert float(hass.states.get("sensor.creg_tariff_flanders_avg_3m").state) == pytest.approx(32.22)
    assert float(hass.states.get("sensor.creg_tariff_brussels_avg_3m").state) == pytest.approx(37.19)
    assert float(hass.states.get("sensor.creg_tariff_wallonia_avg_3m").state) == pytest.approx(37.83)


@pytest.mark.asyncio
async def test_price_sensor_data_attribute_contains_all_rows(hass, config_entry):
    data = _fixture_data()
    with patch(
        "custom_components.creg.coordinator.CregCoordinator._async_update_data",
        return_value=data,
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.creg_tariff_flanders")
    assert len(state.attributes["data"]) == 10
    first = state.attributes["data"][0]
    assert first["year"] == 2026
    assert first["month"] == 4
    assert first["flanders"]["price"] == pytest.approx(32.71)


@pytest.mark.asyncio
async def test_avg_3m_sensor_period_attributes(hass, config_entry):
    data = _fixture_data()
    with patch(
        "custom_components.creg.coordinator.CregCoordinator._async_update_data",
        return_value=data,
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.creg_tariff_flanders_avg_3m")
    assert state.attributes["period_year"] == 2026
    assert state.attributes["period_month"] == 4
