"""Sensor exposing the DWD RV nowcast as state + forecast attributes."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    CONF_THRESHOLD_ENTITY,
    CONF_WARNING_ENTITY,
    DEFAULT_THRESHOLD_ENTITY,
    DOMAIN,
    UNIT_MMH,
    classify,
)
from .rv import MM5_TO_MMH

_NOT_ACTIVE = {"", "off", "unavailable", "unknown", "none", "no_warning", "keine"}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([DwdNowcastSensor(coordinator, entry)])


class DwdNowcastSensor(CoordinatorEntity, SensorEntity):
    """Current rain rate (mm/h) with a 10-min nowcast in attributes."""

    _attr_has_entity_name = False
    _attr_name = "DWD Nowcast – Hausstandort"
    _attr_icon = "mdi:weather-pouring"
    _attr_native_unit_of_measurement = UNIT_MMH
    _attr_device_class = SensorDeviceClass.PRECIPITATION_INTENSITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        cfg = {**entry.data, **entry.options}
        self._threshold_entity = cfg.get(
            CONF_THRESHOLD_ENTITY, DEFAULT_THRESHOLD_ENTITY
        )
        self._warning_entity = cfg.get(CONF_WARNING_ENTITY, "") or ""
        self._attr_unique_id = f"{entry.entry_id}_nowcast"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="DWD Nowcast – Hausstandort",
            manufacturer="Deutscher Wetterdienst",
            model="RADVOR RV (Radar-Nowcast)",
            configuration_url="https://opendata.dwd.de/weather/radar/composite/rv/",
        )

    # --- threshold helper (read live, never hardcoded) ---
    def _read_threshold(self) -> tuple[float | None, bool]:
        st = self.hass.states.get(self._threshold_entity)
        if st is None or st.state in ("unavailable", "unknown", "", None):
            return None, False
        try:
            return float(st.state), True
        except (TypeError, ValueError):
            return None, False

    def _read_warning(self) -> tuple[bool, str]:
        if not self._warning_entity:
            return False, ""
        st = self.hass.states.get(self._warning_entity)
        if st is None:
            return False, ""
        state = (st.state or "").strip().lower()
        active = state not in _NOT_ACTIVE
        if not active:
            return False, ""
        text = st.attributes.get("headline") or st.attributes.get(
            "friendly_name"
        ) or st.state
        return True, str(text)

    def _build_forecast(self, threshold, warn_active, warn_text):
        data = self.coordinator.data or {}
        ts = data.get("data_timestamp")
        series = data.get("series") or {}
        rows = []
        for lead in sorted(series):
            raw = series[lead]  # mm per 5 min
            mmh = None if raw is None else round(raw * MM5_TO_MMH, 2)
            when = dt_util.as_local(ts + timedelta(minutes=lead)) if ts else None
            rows.append(
                {
                    "datetime": when.isoformat() if when else None,
                    "time": when.strftime("%H:%M") if when else None,
                    "minutes": lead,
                    "precipitation": mmh,
                    "unit": UNIT_MMH,
                    "raw": raw,  # mm/5min (Rohwert)
                    "classification": classify(mmh, threshold),
                    "warning": warn_text if warn_active else "",
                }
            )
        return rows

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        series = data.get("series") or {}
        raw0 = series.get(0)
        if raw0 is None:
            return None
        return round(raw0 * MM5_TO_MMH, 2)

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        series = data.get("series") or {}
        ts = data.get("data_timestamp")
        threshold, threshold_ok = self._read_threshold()
        warn_active, warn_text = self._read_warning()
        forecast = self._build_forecast(threshold, warn_active, warn_text)

        mmh_values = [r["precipitation"] for r in forecast if r["precipitation"] is not None]
        all_dry = bool(mmh_values) and max(mmh_values) <= 0.0
        # first lead with at least "Regen möglich"
        next_rain = next(
            (r["minutes"] for r in forecast
             if r["precipitation"] is not None and r["precipitation"] >= 0.2),
            None,
        )

        errors = []
        if not threshold_ok:
            errors.append(
                f"Starkregen-Helfer '{self._threshold_entity}' nicht verfügbar – "
                "Klasse 'starker Regen' kann nicht bestimmt werden."
            )
        if not self.coordinator.last_update_success:
            errors.append(str(self.coordinator.last_exception or "Abruf fehlgeschlagen"))

        return {
            "forecast": forecast,
            "classification_now": forecast[0]["classification"] if forecast else None,
            "max_precipitation": max(mmh_values) if mmh_values else None,
            "next_rain_in_min": next_rain,
            # --- Debug / Nachvollziehbarkeit ---
            "last_update": dt_util.as_local(self.coordinator.last_update_success_time).isoformat()
            if getattr(self.coordinator, "last_update_success_time", None)
            else None,
            "data_timestamp": dt_util.as_local(ts).isoformat() if ts else None,
            "coordinate": [self.coordinator.latitude, self.coordinator.longitude],
            "grid_cell": [data.get("cell_row"), data.get("cell_col")],
            "cell_coordinate": [data.get("cell_lon"), data.get("cell_lat")],
            "threshold_entity": self._threshold_entity,
            "threshold_value": threshold,
            "threshold_available": threshold_ok,
            "warning_entity": self._warning_entity or None,
            "warning_active": warn_active,
            "warning_text": warn_text or None,
            "data_real": bool(series),
            "all_dry": all_dry,
            "source_file": data.get("filename"),
            "source_product": "DWD RADVOR RV (Radar-Nowcast, DE1200 1km)",
            "step_minutes": self.coordinator.step,
            "horizon_minutes": self.coordinator.horizon,
            "error": " | ".join(errors) if errors else None,
        }
