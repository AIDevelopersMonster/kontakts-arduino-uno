"""Built-in and user-defined 5x8 symbol library for LCD1602."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Mapping, Sequence
Glyph = tuple[int, int, int, int, int, int, int, int]
BUILTIN_SYMBOLS: dict[str, Glyph] = {
    "Сердце": (0,10,31,31,31,14,4,0), "Улыбка": (0,10,10,0,17,14,0,0),
    "Стрелка вверх": (4,14,21,4,4,4,4,0), "Стрелка вниз": (4,4,4,4,21,14,4,0),
    "Галочка": (0,1,2,20,8,0,0,0), "Крест": (0,17,10,4,10,17,0,0),
    "Термометр": (4,10,10,10,17,17,14,0), "Батарея": (14,17,27,27,27,17,31,0),
    "Колокольчик": (4,14,14,14,31,4,0,0), "Капля": (4,4,10,10,17,17,14,0),
    "Дом": (4,14,31,17,21,21,31,0), "Часы": (14,17,21,21,19,17,14,0),
    "Динамик": (1,3,21,21,21,3,1,0), "Без звука": (1,3,21,11,21,19,17,0),
    "Воспроизведение": (8,12,14,15,14,12,8,0), "Пауза": (0,10,10,10,10,10,0,0),
    "Стоп": (0,14,17,17,17,14,0,0), "Папка": (0,24,20,31,17,17,31,0),
    "Антенна": (4,14,21,4,4,4,4,0), "Градус": (6,9,9,6,0,0,0,0),
    "Молния": (2,4,8,31,2,4,8,0), "Замок": (14,17,17,31,27,27,31,0),
    "Открытый замок": (14,16,16,31,27,27,31,0), "Курсор": (16,24,28,30,28,24,16,0),
}
DEFAULT_SLOT_NAMES = ("Сердце","Улыбка","Стрелка вверх","Стрелка вниз","Галочка","Крест","Термометр","Батарея")
def validate_glyph(rows: Sequence[int]) -> Glyph:
    values = tuple(int(value) for value in rows)
    if len(values) != 8: raise ValueError("symbol must contain 8 rows")
    if any(value < 0 or value > 31 for value in values): raise ValueError("symbol rows must be values from 0 to 31")
    return values  # type: ignore[return-value]
def load_user_symbols(path: Path) -> dict[str, Glyph]:
    if not path.exists(): return {}
    try: raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError): return {}
    if not isinstance(raw, dict): return {}
    result: dict[str, Glyph] = {}
    for name, rows in raw.items():
        if not isinstance(name, str) or not name.strip() or not isinstance(rows, list): continue
        try: result[name.strip()] = validate_glyph(rows)
        except (TypeError, ValueError): continue
    return result
def save_user_symbols(path: Path, symbols: Mapping[str, Sequence[int]]) -> None:
    clean = {name: list(validate_glyph(rows)) for name, rows in sorted(symbols.items())}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(clean, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
