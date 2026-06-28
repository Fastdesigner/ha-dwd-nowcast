"""Config flow for DWD Nowcast (RADVOR RV)."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_HORIZON_MINUTES,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_STEP_MINUTES,
    CONF_THRESHOLD_ENTITY,
    CONF_WARNING_ENTITY,
    DEFAULT_HORIZON_MINUTES,
    DEFAULT_STEP_MINUTES,
    DEFAULT_THRESHOLD_ENTITY,
    DOMAIN,
)

TITLE = "DWD Nowcast – Hausstandort"


def _schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_LATITUDE, default=defaults[CONF_LATITUDE]): vol.Coerce(float),
            vol.Required(CONF_LONGITUDE, default=defaults[CONF_LONGITUDE]): vol.Coerce(float),
            vol.Required(
                CONF_THRESHOLD_ENTITY, default=defaults[CONF_THRESHOLD_ENTITY]
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["input_number", "number", "sensor"])
            ),
            vol.Optional(
                CONF_WARNING_ENTITY, default=defaults.get(CONF_WARNING_ENTITY, "")
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain=["binary_sensor", "sensor"], multiple=False
                )
            ),
            vol.Required(
                CONF_STEP_MINUTES, default=defaults[CONF_STEP_MINUTES]
            ): vol.All(vol.Coerce(int), vol.Range(min=5, max=30)),
            vol.Required(
                CONF_HORIZON_MINUTES, default=defaults[CONF_HORIZON_MINUTES]
            ): vol.All(vol.Coerce(int), vol.Range(min=10, max=120)),
        }
    )


class DwdNowcastConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial setup."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title=TITLE, data=user_input)

        defaults = {
            CONF_LATITUDE: self.hass.config.latitude,
            CONF_LONGITUDE: self.hass.config.longitude,
            CONF_THRESHOLD_ENTITY: DEFAULT_THRESHOLD_ENTITY,
            CONF_WARNING_ENTITY: "",
            CONF_STEP_MINUTES: DEFAULT_STEP_MINUTES,
            CONF_HORIZON_MINUTES: DEFAULT_HORIZON_MINUTES,
        }
        return self.async_show_form(step_id="user", data_schema=_schema(defaults))

    async def async_step_import(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Auto-setup with defaults (triggered from async_setup)."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        data = {
            CONF_LATITUDE: self.hass.config.latitude,
            CONF_LONGITUDE: self.hass.config.longitude,
            CONF_THRESHOLD_ENTITY: DEFAULT_THRESHOLD_ENTITY,
            CONF_WARNING_ENTITY: "",
            CONF_STEP_MINUTES: DEFAULT_STEP_MINUTES,
            CONF_HORIZON_MINUTES: DEFAULT_HORIZON_MINUTES,
        }
        return self.async_create_entry(title=TITLE, data=data)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return DwdNowcastOptionsFlow(config_entry)


class DwdNowcastOptionsFlow(OptionsFlow):
    """Allow editing coordinates / threshold helper / horizon later."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        merged = {**self._entry.data, **self._entry.options}
        defaults = {
            CONF_LATITUDE: merged.get(CONF_LATITUDE, self.hass.config.latitude),
            CONF_LONGITUDE: merged.get(CONF_LONGITUDE, self.hass.config.longitude),
            CONF_THRESHOLD_ENTITY: merged.get(
                CONF_THRESHOLD_ENTITY, DEFAULT_THRESHOLD_ENTITY
            ),
            CONF_WARNING_ENTITY: merged.get(CONF_WARNING_ENTITY, ""),
            CONF_STEP_MINUTES: merged.get(CONF_STEP_MINUTES, DEFAULT_STEP_MINUTES),
            CONF_HORIZON_MINUTES: merged.get(
                CONF_HORIZON_MINUTES, DEFAULT_HORIZON_MINUTES
            ),
        }
        return self.async_show_form(step_id="init", data_schema=_schema(defaults))
