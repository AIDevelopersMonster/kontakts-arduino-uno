from __future__ import annotations
import unittest
from gui.protocol import CUSTOM_MARKERS, command_glyph, command_text, encode_display_line, parse_state, unsupported_characters, validate_display_text
class ProtocolTests(unittest.TestCase):
    def test_display_text_limit(self):
        self.assertTrue(validate_display_text("1234567890123456")); self.assertFalse(validate_display_text("12345678901234567"))
    def test_ascii_line_is_padded_to_16_bytes(self): self.assertEqual(encode_display_line("ABC"), b"ABC" + b" " * 13)
    def test_custom_markers_map_to_slots(self): self.assertEqual(encode_display_line(CUSTOM_MARKERS)[:8], bytes(range(8)))
    def test_unicode_is_replaced(self):
        self.assertEqual(encode_display_line("Привет")[:6], b"??????"); self.assertEqual(unsupported_characters("AЯЯ"), ("Я",))
    def test_text_command_contains_two_fixed_hex_rows(self):
        prefix, first, second = command_text("A", "B").split(); self.assertEqual(prefix, "TEXT"); self.assertEqual(len(first), 32); self.assertEqual(len(second), 32)
    def test_glyph_command(self): self.assertEqual(command_glyph(3,[0,1,2,3,4,5,30,31]), "GLYPH 3 0001020304051E1F")
    def test_glyph_rejects_bad_slot(self):
        with self.assertRaises(ValueError): command_glyph(8,[0]*8)
    def test_glyph_rejects_bad_rows(self):
        with self.assertRaises(ValueError): command_glyph(0,[0]*7)
        with self.assertRaises(ValueError): command_glyph(0,[32]*8)
    def test_parse_state(self):
        state=parse_state("STATE ADDR=0x27 BACKLIGHT=1"); self.assertIsNotNone(state); self.assertEqual(state.i2c_address,0x27); self.assertTrue(state.backlight_on)
    def test_parse_state_rejects_noise(self): self.assertIsNone(parse_state("OK TEXT"))
if __name__ == "__main__": unittest.main()
