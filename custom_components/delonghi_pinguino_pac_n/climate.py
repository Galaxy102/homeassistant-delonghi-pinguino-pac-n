from logging import getLogger
from typing import Any

from homeassistant.components.climate import (
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.components.infrared import (
    InfraredEmitterConsumerEntity,
    InfraredReceivedSignal,
    InfraredReceiverConsumerEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

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
)
from .protocol.delonghi_pinguino_pac_n import (
    DeviceMode,
    FanMode,
    Flag,
    RemoteCommand,
    Temperature,
    Timer,
)
from .protocol.pronto import ProntoCommand

logger = getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Delonghi climate from config entry."""
    device_model = entry.data[CONF_MODEL]
    if device_model == DelonghiInfraredModel.PAC_N_82_ECO:
        async_add_entities([DelonghiClimatePacNEcoSeries(entry=entry)])


class DelonghiClimatePacNEcoSeries(
    InfraredEmitterConsumerEntity, InfraredReceiverConsumerEntity, ClimateEntity
):
    """Delonghi Climate PAC N Eco Series entity."""

    _attr_name = None
    _attr_assumed_state = True
    _attr_fan_modes = [
        FAN_LOW,
        FAN_MEDIUM,
        FAN_HIGH,
    ]
    _attr_hvac_modes = [
        HVACMode.COOL,
        HVACMode.DRY,
        HVACMode.FAN_ONLY,
        HVACMode.OFF,
    ]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )

    _attr_precision = 1.0
    _attr_target_temperature_step = 1.0
    # State
    _attr_hvac_mode = HVACMode.OFF
    __hvac_mode_before_off = HVACMode.COOL

    def __init__(
        self,
        entry: ConfigEntry,
    ) -> None:
        """Initialize Delonghi climate PAC N Eco Series climate entity."""
        self._attr_unique_id = f"{entry.entry_id}_climate"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=MODEL_NAMES[entry.data[CONF_MODEL]],
            manufacturer="Delonghi",
        )
        self._infrared_emitter_entity_id = entry.data[CONF_INFRARED_EMITTER_ENTITY_ID]
        self._infrared_receiver_entity_id = entry.data[CONF_INFRARED_RECEIVER_ENTITY_ID]
        self._attr_temperature_unit = TEMPERATURE_UNIT_TO_NATIVE[
            entry.data[CONF_TEMPERATURE_UNIT]
        ]
        if self._attr_temperature_unit == UnitOfTemperature.CELSIUS:
            self._attr_max_temp = 32
            self._attr_min_temp = 16
        elif self._attr_temperature_unit == UnitOfTemperature.FAHRENHEIT:
            self._attr_max_temp = 89
            self._attr_min_temp = 61
        else:
            raise ValueError(
                "Unit of Temperature not supported: " + self._attr_temperature_unit
            )
        self._attr_target_temperature = entry.data[CONF_DEFAULT_TEMPERATURE]
        self._attr_fan_mode = entry.data[CONF_DEFAULT_FAN_MODE]

    @callback
    def _handle_signal(self, signal: InfraredReceivedSignal) -> None:
        """Handle a received IR signal."""
        try:
            pronto = ProntoCommand.from_raw_timings(
                timings=signal.timings, modulation=signal.modulation
            )
            command = RemoteCommand.from_pronto(pronto=pronto)
        except ValueError as e:
            logger.debug(
                "Ignoring signal", extra={"timings": signal.timings, "message": repr(e)}
            )
            return

        match command.fan_mode:
            case FanMode.LOW:
                self._attr_fan_mode = FAN_LOW
            case FanMode.MEDIUM:
                self._attr_fan_mode = FAN_MEDIUM
            case FanMode.HIGH:
                self._attr_fan_mode = FAN_HIGH
        hvac_mode = None
        match command.device_mode:
            case DeviceMode.COOL:
                hvac_mode = HVACMode.COOL
            case DeviceMode.DRY:
                hvac_mode = HVACMode.DRY
            case DeviceMode.FAN:
                hvac_mode = HVACMode.FAN_ONLY
        # a valid hvac_mode is always part of the received command and can be used when reactivating the appliance using turn_on
        self.__hvac_mode_before_off = hvac_mode
        if Flag.POWER_ON in command.flags:
            self._attr_hvac_mode = hvac_mode
        else:
            self._attr_hvac_mode = HVACMode.OFF
        if Flag.TEMP_IS_FAHRENHEIT in command.flags:
            self._attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
        else:
            self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_target_temperature = command.temperature.temperature
        self.async_write_ha_state()

    async def _send_current_state(self) -> None:
        fan_mode = FanMode.LOW
        match self._attr_fan_mode:  # TODO: Only enum supported in match
            case "low":
                fan_mode = FanMode.LOW
            case "medium":
                fan_mode = FanMode.MEDIUM
            case "high":
                fan_mode = FanMode.HIGH
            case _:
                raise ValueError("Invalid fan mode")
        hvac_mode_hass = (
            self.__hvac_mode_before_off
            if self._attr_hvac_mode == HVACMode.OFF
            else self._attr_hvac_mode
        )
        device_mode = DeviceMode.COOL
        match hvac_mode_hass:
            case HVACMode.COOL:
                device_mode = DeviceMode.COOL
            case HVACMode.DRY:
                device_mode = DeviceMode.DRY
            case HVACMode.FAN_ONLY:
                device_mode = DeviceMode.FAN
        flags: Flag = Flag.NONE
        if self.temperature_unit == UnitOfTemperature.FAHRENHEIT:
            flags |= Flag.TEMP_IS_FAHRENHEIT
        if self._attr_hvac_mode != HVACMode.OFF:
            flags |= Flag.POWER_ON
        # Timer is ignored for good
        timer = Timer()
        temperature = Temperature(
            temperature=int(self._attr_target_temperature),
            is_fahrenheit=Flag.TEMP_IS_FAHRENHEIT in flags,
        )
        command = RemoteCommand(
            fan_mode=fan_mode,
            device_mode=device_mode,
            timer=timer,
            flags=flags,
            temperature=temperature,
        )
        await self._send_command(command=command.to_pronto())

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        self._attr_hvac_mode = hvac_mode
        await self._send_current_state()
        self.async_write_ha_state()

    async def async_turn_on(self) -> None:
        """Turn the entity on."""
        if self._attr_hvac_mode == HVACMode.OFF:
            self._attr_hvac_mode = self.__hvac_mode_before_off
        await self._send_current_state()
        self.async_write_ha_state()

    async def async_turn_off(self) -> None:
        """Turn the entity off."""
        self.__hvac_mode_before_off = self._attr_hvac_mode
        self._attr_hvac_mode = HVACMode.OFF
        await self._send_current_state()
        self.async_write_ha_state()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        self._attr_fan_mode = fan_mode
        await self._send_current_state()
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        self._attr_target_temperature = kwargs[ATTR_TEMPERATURE]
        await self._send_current_state()
        self.async_write_ha_state()
