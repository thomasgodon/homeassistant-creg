import asyncio
import socket as _socket_module
import sys

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.creg.const import DOMAIN

pytest_plugins = "pytest_homeassistant_custom_component"

# Capture the real socket class before pytest-socket's autouse fixture patches it.
# On Windows, asyncio event loops need socket.socketpair() (AF_INET) to init their
# self-pipe. pytest-socket blocks AF_INET by default, which breaks event loop creation.
# We save the real class here (at import time, before any test fixture runs) so we can
# temporarily restore it while the event loop is being constructed.
_REAL_SOCKET = _socket_module.socket


if sys.platform == "win32":
    @pytest.fixture
    def event_loop(request):
        """On Windows, bypass pytest-socket's AF_INET block for event loop init."""
        patched = _socket_module.socket
        _socket_module.socket = _REAL_SOCKET
        try:
            loop = asyncio.SelectorEventLoop()
        finally:
            _socket_module.socket = patched
        yield loop
        loop.close()


@pytest.fixture
async def config_entry(hass, enable_custom_integrations):
    entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    entry.add_to_hass(hass)
    return entry
