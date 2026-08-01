from __future__ import annotations

import unittest

from gui.protocol import DeviceState, command_blink, parse_state, period_ms_from_hz


class ProtocolTests(unittest.TestCase):
    def test_frequency_to_period(self) -> None:
        self.assertEqual(period_ms_from_hz(1.0), 1000)
        self.assertEqual(period_ms_from_hz(2.0), 500)
        self.assertEqual(period_ms_from_hz(10.0), 100)

    def test_frequency_range(self) -> None:
        with self.assertRaises(ValueError):
            period_ms_from_hz(0.1)
        with self.assertRaises(ValueError):
            period_ms_from_hz(10.1)

    def test_blink_command(self) -> None:
        self.assertEqual(command_blink(4.0), "BLINK 250")

    def test_parse_state(self) -> None:
        state = parse_state("STATE MODE=BLINK LED=1 PERIOD_MS=1000")
        self.assertEqual(state, DeviceState("BLINK", True, 1000))

    def test_parse_state_rejects_bad_lines(self) -> None:
        self.assertIsNone(parse_state("STATE MODE=INVALID LED=1 PERIOD_MS=1000"))
        self.assertIsNone(parse_state("STATE MODE=ON LED=1 PERIOD_MS=99"))
        self.assertIsNone(parse_state("hello"))


if __name__ == "__main__":
    unittest.main()
