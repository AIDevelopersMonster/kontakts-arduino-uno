from __future__ import annotations
from pathlib import Path
import tempfile, unittest
from gui.symbols import BUILTIN_SYMBOLS, load_user_symbols, save_user_symbols, validate_glyph
class SymbolLibraryTests(unittest.TestCase):
    def test_all_builtins_are_valid(self):
        self.assertGreaterEqual(len(BUILTIN_SYMBOLS),20)
        for rows in BUILTIN_SYMBOLS.values(): self.assertEqual(validate_glyph(rows),rows)
    def test_round_trip_user_library(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"symbols.json"; save_user_symbols(path,{"Тест":[0,1,2,3,4,5,6,7]}); self.assertEqual(load_user_symbols(path)["Тест"],(0,1,2,3,4,5,6,7))
    def test_invalid_json_is_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"symbols.json"; path.write_text("not-json",encoding="utf-8"); self.assertEqual(load_user_symbols(path),{})
if __name__ == "__main__": unittest.main()
