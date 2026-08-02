"""Pure helpers for the LCD1602 USB Serial protocol."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, Sequence

DISPLAY_COLUMNS = 16
DISPLAY_ROWS = 2
CUSTOM_MARKERS = "①②③④⑤⑥⑦⑧"

_STATE_RE = re.compile(r"^STATE ADDR=0x([0-9A-Fa-f]{2}) BACKLIGHT=([01])$")


@dataclass(frozen=True)
class DeviceState:
    i2c_address: int
    backlight_on: bool


def validate_display_text(text: str) -> bool:
    """Return True when text fits one 16-cell LCD row."""
    return len(text) <= DISPLAY_COLUMNS and "\n" not in text and "\r" not in text


def unsupported_characters(text: str) -> tuple[str, ...]:
    """Return unique characters that will be replaced by '?' on the LCD."""
    unsupported: list[str] = []
    for char in text:
        if char in CUSTOM_MARKERS:
            continue
        code = ord(char)
        if 0x20 <= code <= 0x7E:
            continue
        if char not in unsupported:
            unsupported.append(char)
    return tuple(unsupported)


def encode_display_line(text: str) -> bytes:
    """Encode one GUI row to exactly 16 LCD bytes.

    Printable ASCII is transferred directly. Circled digits ①..⑧ represent
    custom character slots 0..7. Other Unicode characters become '?'.
    """
    if not validate_display_text(text):
        raise ValueError("LCD row must contain at most 16 characters")

    encoded = bytearray()
    for char in text:
        if char in CUSTOM_MARKERS:
            encoded.append(CUSTOM_MARKERS.index(char))
            continue

        code = ord(char)
        encoded.append(code if 0x20 <= code <= 0x7E else ord("?"))

    encoded.extend(b" " * (DISPLAY_COLUMNS - len(encoded)))
    return bytes(encoded)


def command_text(line1: str, line2: str) -> str:
    first = encode_display_line(line1).hex().upper()
    second = encode_display_line(line2).hex().upper()
    return f"TEXT {first} {second}"


def _normalize_rows(rows: Iterable[int]) -> tuple[int, ...]:
    normalized = tuple(int(value) for value in rows)
    if len(normalized) != 8:
        raise ValueError("custom glyph must contain exactly 8 rows")
    if any(value < 0 or value > 0x1F for value in normalized):
        raise ValueError("each glyph row must be a 5-bit value from 0 to 31")
    return normalized


def command_glyph(slot: int, rows: Sequence[int]) -> str:
    if slot < 0 or slot > 7:
        raise ValueError("custom glyph slot must be between 0 and 7")
    normalized = _normalize_rows(rows)
    payload = "".join(f"{row:02X}" for row in normalized)
    return f"GLYPH {slot} {payload}"


def parse_state(line: str) -> DeviceState | None:
    match = _STATE_RE.fullmatch(line.strip())
    if match is None:
        return None
    address_text, backlight_text = match.groups()
    return DeviceState(
        i2c_address=int(address_text, 16),
        backlight_on=(backlight_text == "1"),
    )
