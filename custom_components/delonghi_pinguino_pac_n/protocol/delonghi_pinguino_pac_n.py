"""Delonghi PAC N Eco protocol implementation based on the Pronto infrared protocol.

Timing info:
The modulation is 38 kHz.
Each message is started by a 0x015E mark and 0x00AB space
and terminated by a 0x0017 mark and 0x0180 space.
Between the start and terminal indicators, there are 32 bits of data.
Mark is 0x0017 long, space is 0x0013 for a 0 bit and 0x003E for a 1 bit.

The 32 bits are to be decoded as follows (in order of reception):

- 8 bits device id
  - seems to be static: 0b00010010
- 4 bits fan mode
  - 0b0100 = Low
  - 0b0010 = Medium
  - 0b0001 = High
- 4 bits device mode
  - 0b1000 = Cool
  - 0b0010 = Dry
  - 0b0001 = Fan
- 4 bits timer
  - value range: 1..12 hours
  - format is 4 bits LSb first
  - e.g. 1 = 0b1000, 2 = 0b0100, 3 = 0b1100, ...
- 4 bits flags
  - default low
  - 0b0001 = Power On
  - 0b0010 = Timer On
  - 0b0100 = Temperature Unit Fahrenheit
- 8 bits temperature
  - if Celsius:
    - value range: 16..32°C
    - format is 8 bits LSb first with offset of 16
    - e.g. 16°C = 0b0000000, 17°C = 0b10000000, 32°C = 0b00001000
  - if Fahrenheit:
    - value range: 61..89°F
    - format is 8 bits LSb first WITHOUT offset
    - e.g. 61°F = 0b10111100, 62°F = 0b01111100, 89°F = 0b10011010
"""

from dataclasses import dataclass
from enum import IntEnum, IntFlag
import struct
from typing import Self, SupportsIndex

from .pronto import ProntoCommand


class FanMode(IntEnum):
    """Pinguino PAC N Eco fan modes."""

    LOW = 0b0100
    MEDIUM = 0b0010
    HIGH = 0b0001


class DeviceMode(IntEnum):
    """Pinguino PAC N Eco device mode."""

    COOL = 0b1000
    DRY = 0b0010
    FAN = 0b0001


class Timer(SupportsIndex):
    """Pinguino PAC N Eco timer."""

    def __init__(self, hours: int = 1) -> None:
        """Get timer object from hours."""
        self._hours = min(max(hours, 1), 12)

    def __index__(self):
        """Interpret as number."""
        return self._hours

    @classmethod
    def from_received(cls, value: int) -> Self:
        """Interpret incoming data word of 4 bits as timer."""
        # Interpret LSb first (HVAC) as MSb first (Python) to have timer value
        return cls(int(bin(value)[2:].zfill(4)[::-1], base=2))

    def to_send(self) -> int:
        """Interpret timer as outgoing data word of 4 bits."""
        # Interpret MSb first (Python) as LSb first (HVAC) to have sendable value
        return int(bin(self)[2:].zfill(4)[::-1], base=2)


class Flag(IntFlag):
    """Pinguino PAC N Eco flags."""

    TEMP_IS_FAHRENHEIT = 0b0100
    TIMER_ACTIVE = 0b0010
    POWER_ON = 0b0001
    NONE = 0b0000


class Temperature:
    """Pinguino PAC N Eco temperature."""

    _temperature: int
    _is_fahrenheit: bool

    def __init__(self, temperature: int, is_fahrenheit: bool = False) -> None:
        """Get temperature object from temperature and respective unit."""
        if is_fahrenheit:
            # limit to allowed value range
            self._temperature = min(max(temperature, 61), 89)
        else:
            # limit to allowed value range
            self._temperature = min(max(temperature, 16), 32)
        self._is_fahrenheit = is_fahrenheit

    @property
    def temperature(self) -> int:
        """Get saved temperature."""
        return self._temperature

    @property
    def is_fahrenheit(self) -> bool:
        """Get whether saved temperature unit is Fahrenheit."""
        return self._is_fahrenheit

    def to_send(self) -> int:
        """Interpret temperature as outgoing data word of 8 bits."""
        temperature = self._temperature
        # For °C, temperature must be reduced by 16
        if not self._is_fahrenheit:
            temperature = self._temperature - 16
        # Interpret MSb first (Python) as LSb first (HVAC) to have sendable value
        return int(bin(temperature)[2:].zfill(8)[::-1], base=2)

    @classmethod
    def from_received(cls, value: int, is_fahrenheit: bool) -> Self:
        """Interpret incoming data word of 8 bits as temperature."""
        # Interpret LSb first (HVAC) as MSb first (Python) to have timer value
        temperature = int(bin(value)[2:].zfill(8)[::-1], base=2)
        # For °C, temperature must be increased by 16
        if not is_fahrenheit:
            temperature += 16
        return cls(temperature=temperature, is_fahrenheit=is_fahrenheit)


@dataclass
class RemoteCommand:
    """Pinguino PAC N Eco exchangeable remote command.

    See module docstring for protocol description.
    """

    fan_mode: FanMode
    device_mode: DeviceMode
    timer: Timer
    flags: Flag
    temperature: Temperature

    _DEVICE_ID: int = 0b00010010
    _PRONTO_PREAMBLE: bytes = b"\x01\x5e\x00\xab"
    _PRONTO_MARK: bytes = b"\x00\x17"
    _PRONTO_SPACE_0BIT: bytes = b"\x00\x13"
    _PRONTO_SPACE_1BIT: bytes = b"\x00\x3e"
    _PRONTO_TRAILER: bytes = b"\x00\x17\x01\x80"

    def to_control_word(self) -> int:
        """Transform object to exchangeable control word."""
        if self.temperature.is_fahrenheit and Flag.TEMP_IS_FAHRENHEIT not in self.flags:
            raise ValueError(
                "Temperature was set as fahrenheit, but TEMP_IS_FAHRENHEIT flag is unset."
            )
        return (
                ((self._DEVICE_ID & 0b11111111) << 24)
                + ((self.fan_mode & 0b1111) << 20)
                + ((self.device_mode & 0b1111) << 16)
                + ((self.timer.to_send() & 0b1111) << 12)
                + ((self.flags & 0b1111) << 8)
                + (self.temperature.to_send() & 0b11111111)
        )

    def to_pronto(self) -> ProntoCommand:
        """Transform object to pronto command."""
        # I sadly couldn't find a better way than using a str intermediate...
        payload_bin = "".join(
            [bin(byte).lstrip("0b").rjust(8, "0") for byte in struct.pack(">L", self.to_control_word())]
        )
        payload_pronto = b"".join(
            [
                self._PRONTO_MARK
                + (self._PRONTO_SPACE_1BIT if bit == "1" else self._PRONTO_SPACE_0BIT)
                for bit in payload_bin
            ]
        )
        return ProntoCommand(
            timing_data=self._PRONTO_PREAMBLE + payload_pronto + self._PRONTO_TRAILER,
        )

    @classmethod
    def from_control_word(cls, control_word: int) -> Self:
        """Transform exchangeable control word to object."""
        device_id = (control_word & 0b11111111000000000000000000000000) >> 24
        if device_id != cls._DEVICE_ID:
            raise ValueError("Device ID mismatch. This packet must be ignored.")
        fan_mode = (control_word & 0b00000000111100000000000000000000) >> 20
        dev_mode = (control_word & 0b00000000000011110000000000000000) >> 16
        timer = (control_word & 0b00000000000000001111000000000000) >> 12
        flags = (control_word & 0b00000000000000000000111100000000) >> 8
        temperature = control_word & 0b00000000000000000000000011111111

        parsed_flags = Flag(flags)
        return RemoteCommand(
            fan_mode=FanMode(fan_mode),
            device_mode=DeviceMode(dev_mode),
            timer=Timer.from_received(timer),
            flags=parsed_flags,
            temperature=Temperature.from_received(
                temperature,
                is_fahrenheit=Flag.TEMP_IS_FAHRENHEIT in parsed_flags,
            ),
        )

    @classmethod
    def from_pronto(cls, pronto: ProntoCommand) -> Self:
        """Transform pronto command to object."""
        try:
            pronto_words: list[int] = [
                word[0]
                for word in struct.iter_unpack(
                    ">L", pronto.timing_data
                )
                # split as blocks of 4 byte of data (unsigned long) (remember: pronto needs 4 bytes to encode one symbol)
            ]
        except struct.error as e:
            raise ValueError("Invalid data received.") from e
        space_0bit_int = struct.unpack(">h", cls._PRONTO_SPACE_0BIT)[0]
        space_1bit_int = struct.unpack(">h", cls._PRONTO_SPACE_1BIT)[0]
        pronto_bits = [
            (byte & 0xFFFF)     # only space (last two bytes) is interesting - skip mark (first two bytes)
            > (
                    space_0bit_int
                    + (space_0bit_int + space_1bit_int) / 2
                # Interpretation of 0 or 1 is done by finding the nearest neighbor space interpretation (remember: space of 0 bit < space of 1 bit, otherwise the logic must be inverted)
            )
            for byte in pronto_words[1:-1]  # skip preamble and trailer
        ]
        # Convert LSb first bitfield (HVAC) to MSb first int (Python)
        control_word = sum(bit << idx for idx, bit in enumerate(pronto_bits[::-1]))
        return cls.from_control_word(control_word=control_word)
