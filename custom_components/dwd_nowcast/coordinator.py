"""DataUpdateCoordinator for the DWD RV nowcast."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_HORIZON_MINUTES,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_STEP_MINUTES,
    DEFAULT_HORIZON_MINUTES,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DEFAULT_STEP_MINUTES,
    DOMAIN,
)
from .rv import fetch_rv_series

_LOGGER = logging.getLogger(__name__)


class DwdNowcastCoordinator(DataUpdateCoordinator):
    """Polls the DWD RV composite and extracts the home-cell rain series."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        data = {**entry.data, **entry.options}
        self.latitude = float(data.get(CONF_LATITUDE, hass.config.latitude))
        self.longitude = float(data.get(CONF_LONGITUDE, hass.config.longitude))
        self.step = int(data.get(CONF_STEP_MINUTES, DEFAULT_STEP_MINUTES))
        self.horizon = int(data.get(CONF_HORIZON_MINUTES, DEFAULT_HORIZON_MINUTES))
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL_SECONDS),
        )

    @property
    def leads(self) -> list[int]:
        return list(range(0, self.horizon + 1, self.step))

    async def _async_update_data(self) -> dict:
        try:
            result = await self.hass.async_add_executor_job(
                fetch_rv_series, self.latitude, self.longitude, self.leads
            )
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(str(err)) from err
        result["fetched_at"] = dt_util.utcnow()
        return result
