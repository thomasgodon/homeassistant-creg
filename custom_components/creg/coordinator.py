from __future__ import annotations

import csv
import io
import logging
from dataclasses import dataclass
from datetime import datetime

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import TimestampDataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import CSV_URL, DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


@dataclass
class RegionData:
    price: float | None
    avg_3m: float | None


@dataclass
class MonthData:
    year: int
    month: int
    flanders: RegionData
    brussels: RegionData
    wallonia: RegionData


@dataclass
class Avg3mResult:
    value: float
    year: int
    month: int


def _parse_float(value: str) -> float | None:
    value = value.strip()
    if not value:
        return None
    return float(value.replace(",", "."))


def _parse_csv(text: str) -> list[MonthData]:
    reader = csv.reader(io.StringIO(text), delimiter=";")
    rows: list[MonthData] = []
    for i, row in enumerate(reader):
        if i == 0:
            continue
        if len(row) < 8:
            continue
        try:
            year = int(row[0])
            month = int(row[1])
        except ValueError:
            continue
        rows.append(
            MonthData(
                year=year,
                month=month,
                flanders=RegionData(
                    price=_parse_float(row[2]), avg_3m=_parse_float(row[3])
                ),
                brussels=RegionData(
                    price=_parse_float(row[4]), avg_3m=_parse_float(row[5])
                ),
                wallonia=RegionData(
                    price=_parse_float(row[6]), avg_3m=_parse_float(row[7])
                ),
            )
        )
    rows.sort(key=lambda r: (r.year, r.month), reverse=True)
    return rows


class CregCoordinator(TimestampDataUpdateCoordinator[list[MonthData]]):
    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> list[MonthData]:
        try:
            session = async_get_clientsession(self.hass)
            async with session.get(CSV_URL) as response:
                response.raise_for_status()
                raw = await response.read()
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error fetching CREG CSV: {err}") from err

        try:
            text = raw.decode("utf-8-sig")
            return _parse_csv(text)
        except Exception as err:
            raise UpdateFailed(f"Error parsing CREG CSV: {err}") from err

    def latest_price(self, region: str) -> float | None:
        if not self.data:
            return None
        return getattr(self.data[0], region).price

    def latest_avg_3m(self, region: str) -> Avg3mResult | None:
        if not self.data:
            return None
        for row in self.data:
            value = getattr(row, region).avg_3m
            if value is not None:
                return Avg3mResult(value=value, year=row.year, month=row.month)
        return None

    def this_quarter_avg(self, region: str, now: datetime | None = None) -> Avg3mResult | None:
        if not self.data:
            return None
        if now is None:
            now = dt_util.now()
        q_start = ((now.month - 1) // 3) * 3 + 1
        # CREG publishes the rate for quarter Q in the CSV row 3 months before Q starts.
        # E.g. the April row carries Q3 (Jul-Sep), the January row carries Q2 (Apr-Jun).
        pub_month = q_start - 3
        pub_year = now.year
        if pub_month <= 0:
            pub_month += 12
            pub_year -= 1
        for row in self.data:
            if row.year == pub_year and row.month == pub_month:
                value = getattr(row, region).avg_3m
                if value is None:
                    return None
                return Avg3mResult(value=value, year=now.year, month=q_start)
        return None
