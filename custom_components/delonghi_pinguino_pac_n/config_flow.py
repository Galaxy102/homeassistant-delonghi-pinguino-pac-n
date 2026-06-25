"""Config flow for the Delonghi PAC N integration."""

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.infrared import (
    DOMAIN as INFRARED_DOMAIN,
    async_get_emitters,
    async_get_receivers,
)
from homeassistant.config_entries import (
    SOURCE_RECONFIGURE,
    ConfigFlow,
    ConfigFlowResult,
)
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_DEFAULT_FAN_MODE,
    CONF_DEFAULT_TEMPERATURE,
    CONF_INFRARED_EMITTER_ENTITY_ID,
    CONF_INFRARED_RECEIVER_ENTITY_ID,
    CONF_MODEL,
    CONF_TEMPERATURE_UNIT,
    DOMAIN,
    MODEL_NAMES,
    TEMPERATURE_UNIT_TO_NATIVE,
    DelonghiInfraredModel,
    ConfigFanMode,
    TemperatureUnit,
)

_LOGGER = logging.getLogger(__name__)


class DelonghiInfraredConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle config flow for Delonghi Infrared."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        emitter_entity_ids = async_get_emitters(self.hass)
        receiver_entity_ids = async_get_receivers(self.hass)
        if not emitter_entity_ids and not receiver_entity_ids:
            return self.async_abort(reason="no_infrared_entities")

        errors: dict[str, str] = {}

        if user_input is not None:
            if not (entity_id := user_input.get(CONF_INFRARED_EMITTER_ENTITY_ID)):
                errors["base"] = "missing_infrared_entity"
            temperature_unit = user_input.get(CONF_TEMPERATURE_UNIT)
            default_temperature = user_input.get(CONF_DEFAULT_TEMPERATURE)
            if temperature_unit == TemperatureUnit.CELSIUS and not (
                16 <= default_temperature <= 32
            ):
                errors["base"] = "default_temperature_out_of_bounds"
            if temperature_unit == TemperatureUnit.FAHRENHEIT and not (
                61 <= default_temperature <= 89
            ):
                errors["base"] = "default_temperature_out_of_bounds"

            if not errors:
                device_model = user_input[CONF_MODEL]

                # Get IR device name for the title
                dev_reg = dr.async_get(self.hass)
                ent_reg = er.async_get(self.hass)
                entry = ent_reg.async_get(entity_id)
                parent_device = dev_reg.async_get(entry.device_id)
                parent_name = (
                    parent_device.name_by_user or parent_device.name or parent_device.id
                    if parent_device
                    else entity_id
                )
                device_model_name = MODEL_NAMES[DelonghiInfraredModel(device_model)]
                title = f"Delonghi {device_model_name} via {parent_name}"

                await self.async_set_unique_id(f"{DOMAIN}_{device_model}_{entity_id}")
                if self.source == SOURCE_RECONFIGURE:
                    self._abort_if_unique_id_mismatch()
                    return self.async_update_reload_and_abort(
                        self._get_reconfigure_entry(),
                        data_updates=user_input,
                        title=title,
                    )
                else:
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(title=title, data=user_input)

        schema_dict: dict[vol.Marker, Any] = {
            vol.Required(CONF_MODEL): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        SelectOptionDict(
                            value=device_model.value, label=MODEL_NAMES[device_model]
                        )
                        for device_model in DelonghiInfraredModel
                    ],
                    translation_key=CONF_MODEL,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(CONF_INFRARED_EMITTER_ENTITY_ID): EntitySelector(
                EntitySelectorConfig(
                    domain=INFRARED_DOMAIN,
                    include_entities=emitter_entity_ids,
                )
            ),
            vol.Optional(CONF_INFRARED_RECEIVER_ENTITY_ID): EntitySelector(
                EntitySelectorConfig(
                    domain=INFRARED_DOMAIN,
                    include_entities=receiver_entity_ids,
                )
            ),
            vol.Required(CONF_TEMPERATURE_UNIT): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        SelectOptionDict(
                            value=temperature_unit.value,
                            label=TEMPERATURE_UNIT_TO_NATIVE[temperature_unit].value,
                        )
                        for temperature_unit in TemperatureUnit
                    ],
                    translation_key=CONF_TEMPERATURE_UNIT,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(CONF_DEFAULT_TEMPERATURE): NumberSelector(
                NumberSelectorConfig(
                    min=16.0,
                    max=89.0,
                    step=1.0,
                    mode=NumberSelectorMode.BOX,
                    translation_key=CONF_DEFAULT_TEMPERATURE,
                )
            ),
            vol.Required(CONF_DEFAULT_FAN_MODE): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        SelectOptionDict(value=fan_mode.value, label=fan_mode.value)
                        for fan_mode in ConfigFanMode
                    ],
                    translation_key=CONF_DEFAULT_FAN_MODE,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
        }

        return self.async_show_form(
            step_id="reconfigure" if self.source == SOURCE_RECONFIGURE else "user",
            data_schema=vol.Schema(schema_dict),
            last_step=True,
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Run reconfiguration which is essentially the same as creating."""
        return await self.async_step_user(user_input=user_input)
