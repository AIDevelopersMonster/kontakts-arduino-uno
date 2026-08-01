"""Pure helpers for the GUI Blink serial protocol."""

from __future__ import annotations

from dataclasses import dataclass
import re

MIN_FREQUENCY_HZ = 0.2
MAX_FREQUENCY_HZ = 10.0
MIN_PERIOD_MS = 100
MAX_PERIOD_MS = 10_000

_STATE_RE = re.compile(
    r"^STATE MODE=(OFF|ON|BLINK) LED=([01]) PERIOD_MS=(\d+)$"
)


@dataclass(frozen=True)
class DeviceState:
    mode: str
    led_on: bool
    period_ms: int


def period_ms_from_hz(frequency_hz: float) -> int:
    """Convert GUI frequency to a device period and enforce protocol limits."""
    if not MIN_FREQUENCY_HZ <= frequency_hz <= MAX_FREQUENCY_HZ:
        raise ValueError(
            f"frequency must be between {MIN_FREQUENCY_HZ} and {MAX_FREQUENCY_HZ} Hz"
        )
    period_ms = round(1000.0 / frequency_hz)
    return max(MIN_PERIOD_MS, min(MAX_PERIOD_MS, period_ms))


def command_blink(frequency_hz: float) -> str:
    return f"BLINK {period_ms_from_hz(frequency_hz)}"


def parse_state(line: str) -> DeviceState | None:
    match = _STATE_RE.fullmatch(line.strip())
    if match is None:
        return None

    mode, led, period_text = match.groups()
    period_ms = int(period_text)
    if not MIN_PERIOD_MS <= period_ms <= MAX_PERIOD_MS:
        return None

    return DeviceState(mode=mode, led_on=(led == "1"), period_ms=period_ms)
