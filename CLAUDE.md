# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Home Assistant custom integration for CREG (Commission de Régulation de l'Électricité et du Gaz — Belgian energy regulator). Python-based HA custom component.

## Standard HA custom component layout

When source code is added, expect:
- `custom_components/creg/` — integration root (`manifest.json`, `__init__.py`, `config_flow.py`, `sensor.py`, etc.)
- `tests/` — pytest-based tests

## Home Assistant integration conventions

- The integration domain must match the folder name under `custom_components/` and the `domain` key in `manifest.json`.
- Config entries are preferred over YAML configuration for new integrations.
- Use `homeassistant.helpers.aiohttp_client.async_get_clientsession` for HTTP calls — never create a raw `aiohttp.ClientSession`.
- All I/O must be async; blocking calls belong in `hass.async_add_executor_job`.

## Documentation

Any change to integration code or behavior MUST update `README.md` in the same task. Stale docs are a bug.
