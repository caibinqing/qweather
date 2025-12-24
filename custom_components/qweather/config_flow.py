from http import HTTPStatus
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .const import CONF_API_HOST, CONF_GIRD, CONF_LOCATION_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)


class QWeatherFlowHandler(ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors = {}
        if user_input is not None:
            api_host = user_input.get(CONF_API_HOST, "")
            longitude = round(user_input[CONF_LONGITUDE], 2)
            latitude = round(user_input[CONF_LATITUDE], 2)
            use_grid = user_input.get(CONF_GIRD, True)

            await self.async_set_unique_id(f"{longitude}_{latitude}".replace(".", "_"))
            self._abort_if_unique_id_configured()

            """城市搜索-城市信息查询"""
            geo_url = f"https://{api_host}/geo/v2/city/lookup"
            params = {
                "location": f"{longitude},{latitude}",
                "key": user_input[CONF_API_KEY],
            }
            session = async_get_clientsession(self.hass)
            resp = await session.get(geo_url, params=params)
            if resp.status == HTTPStatus.OK:
                json_data = await resp.json()
                _LOGGER.debug(json_data)
                if locations := json_data.get("location"):
                    location_id = locations[0].get("id")
                    # noinspection PyTypeChecker
                    return self.async_create_entry(
                        title=user_input[CONF_NAME],
                        data={
                            CONF_API_HOST: api_host,
                            CONF_NAME: user_input[CONF_NAME],
                            CONF_API_KEY: user_input[CONF_API_KEY],
                            CONF_LONGITUDE: user_input[CONF_LONGITUDE],
                            CONF_LATITUDE: user_input[CONF_LATITUDE],
                            CONF_LOCATION_ID: location_id,
                        },
                        options={
                            CONF_GIRD: use_grid,
                        },
                    )

            _LOGGER.warning("Failed to communicate with QWeather: %s", resp.status)
            errors["base"] = "communication"

        my = self.hass.config
        # noinspection PyTypeChecker
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_HOST): str,
                    vol.Required(CONF_API_KEY): str,
                    vol.Required(CONF_LONGITUDE, default=my.longitude): cv.longitude,
                    vol.Required(CONF_LATITUDE, default=my.latitude): cv.latitude,
                    vol.Required(CONF_NAME, default=my.location_name): str,
                    vol.Optional(CONF_GIRD, default=True): bool,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return QWeatherOptionsFlow(config_entry)


class QWeatherOptionsFlow(OptionsFlow):
    """Config options flow for Qweather."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize Qweather options flow."""
        self.use_grid = config_entry.options.get(CONF_GIRD, False)

    async def async_step_init(self, user_input=None) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        if user_input is not None:
            # noinspection PyTypeChecker
            return self.async_create_entry(data=user_input)

        # noinspection PyTypeChecker
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_GIRD, default=self.use_grid): bool,
                }
            ),
        )
