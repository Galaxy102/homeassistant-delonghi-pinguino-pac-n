"""Constants for the Delonghi PAC N integration."""

from enum import StrEnum

from homeassistant.components.climate import FAN_HIGH, FAN_LOW, FAN_MEDIUM
from homeassistant.const import (  # noqa: F401 imported for use in config_flow and climate
    CONF_MODEL,
    CONF_TEMPERATURE_UNIT,
    UnitOfTemperature,
)

CONF_DEFAULT_FAN_MODE = "default_fan_mode"
CONF_DEFAULT_TEMPERATURE = "default_temperature"
CONF_INFRARED_EMITTER_ENTITY_ID = "infrared_entity_id"
CONF_INFRARED_RECEIVER_ENTITY_ID = "infrared_receiver_entity_id"
DOMAIN = "delonghi_pinguino_pac_n"


class ConfigFanMode(StrEnum):
    """Delonghi Infrared fan modes limited to available ones."""

    LOW = FAN_LOW
    MEDIUM = FAN_MEDIUM
    HIGH = FAN_HIGH


class TemperatureUnit(StrEnum):
    """Delonghi Infrared temperature units limited to available ones."""

    CELSIUS = "celsius"
    FAHRENHEIT = "fahrenheit"


TEMPERATURE_UNIT_TO_NATIVE: dict[TemperatureUnit, UnitOfTemperature] = {
    TemperatureUnit.CELSIUS: UnitOfTemperature.CELSIUS,
    TemperatureUnit.FAHRENHEIT: UnitOfTemperature.FAHRENHEIT,
}
