import pytest
from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.creg.const import DOMAIN


@pytest.mark.asyncio
async def test_config_flow_creates_entry(hass, enable_custom_integrations):
    with patch(
        "custom_components.creg.coordinator.CregCoordinator._async_update_data",
        return_value=[],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "CREG Tariff"
        assert result["data"] == {}


@pytest.mark.asyncio
async def test_config_flow_single_instance(hass, enable_custom_integrations):
    with patch(
        "custom_components.creg.coordinator.CregCoordinator._async_update_data",
        return_value=[],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
        await hass.async_block_till_done()

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "single_instance_allowed"
