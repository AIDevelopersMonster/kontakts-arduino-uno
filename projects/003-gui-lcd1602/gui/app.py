"""Windows GUI for Arduino UNO + LCD1602 I2C over USB Serial."""
from __future__ import annotations
import queue
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import serial
from serial.tools import list_ports
from gui.protocol import CUSTOM_MARKERS, command_glyph, command_text, parse_state, unsupported_characters
from gui.symbols import BUILTIN_SYMBOLS, DEFAULT_SLOT_NAMES, Glyph, load_user_symbols, save_user_symbols

BAUD_RATE = 115200
HANDSHAKE_DELAY_MS = 1800
USER_LIBRARY_PATH = Path(__file__).with_name("user_symbols.json")


class Lcd1602App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("KONTAKTS Arduino UNO — LCD1602 GUI")
        root.geometry("930x720")
        root.minsize(820, 650)
        self.port: serial.Serial | None = None
        self.reader: threading.Thread | None = None
        self.stop_reader = threading.Event()
        self.rx: queue.Queue[tuple[str, str]] = queue.Queue()
        self.port_map: dict[str, str] = {}
        self.connection = tk.StringVar(value="Не подключено")
        self.device = tk.StringVar(value="LCD не опрошен")
        self.status = tk.StringVar(value="Готово")
        self.lines = [tk.StringVar(), tk.StringVar()]
        self.counters = [tk.StringVar(value="0/16"), tk.StringVar(value="0/16")]
        self.active_line = 0
        self.slot = tk.IntVar(value=0)
        self.slot_names = [tk.StringVar(value=name) for name in DEFAULT_SLOT_NAMES]
        self.slot_patterns: list[Glyph] = [BUILTIN_SYMBOLS[name] for name in DEFAULT_SLOT_NAMES]
        self.editor_rows = list(self.slot_patterns[0])
        self.editor_name = tk.StringVar(value=DEFAULT_SLOT_NAMES[0])
        self.pixel_buttons: list[list[tk.Button]] = []
        self.user_symbols = load_user_symbols(USER_LIBRARY_PATH)
        self._build()
        self.refresh_ports()
        self._refresh_pixels()
        self._refresh_library()
        root.after(100, self._poll_rx)
        root.protocol("WM_DELETE_WINDOW", self.close)

    def _build(self) -> None:
        outer = ttk.Frame(self.root, padding=14)
        outer.pack(fill=tk.BOTH, expand=True)
        ttk.Label(outer, text="LCD1602 I2C для Arduino UNO", font=("Segoe UI", 18, "bold")).pack(anchor=tk.W)
        ttk.Label(outer, text="Две строки по 16 символов и редактор восьми пользовательских знаков 5×8").pack(anchor=tk.W, pady=(0, 10))

        conn = ttk.LabelFrame(outer, text="Подключение", padding=10)
        conn.pack(fill=tk.X)
        row = ttk.Frame(conn); row.pack(fill=tk.X)
        ttk.Label(row, text="COM-порт:").pack(side=tk.LEFT)
        self.port_combo = ttk.Combobox(row, state="readonly", width=48)
        self.port_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        ttk.Button(row, text="Обновить", command=self.refresh_ports).pack(side=tk.LEFT)
        self.connect_button = ttk.Button(row, text="Подключить", command=self.toggle_connection)
        self.connect_button.pack(side=tk.LEFT, padx=(8, 0))
        ttk.Label(conn, textvariable=self.connection).pack(anchor=tk.W, pady=(7, 0))
        ttk.Label(conn, textvariable=self.device).pack(anchor=tk.W)

        tabs = ttk.Notebook(outer)
        tabs.pack(fill=tk.BOTH, expand=True, pady=10)
        screen = ttk.Frame(tabs, padding=12)
        glyphs = ttk.Frame(tabs, padding=12)
        tabs.add(screen, text="Экран 16×2")
        tabs.add(glyphs, text="Генератор символов 5×8")
        self._build_screen(screen)
        self._build_glyphs(glyphs)

        ttk.Label(outer, textvariable=self.status).pack(anchor=tk.W)
        log_frame = ttk.LabelFrame(outer, text="Журнал Serial", padding=6)
        log_frame.pack(fill=tk.BOTH, expand=False, pady=(8, 0))
        self.log = tk.Text(log_frame, height=7, state=tk.DISABLED, wrap=tk.WORD)
        self.log.pack(fill=tk.BOTH, expand=True)

    def _build_screen(self, parent: ttk.Frame) -> None:
        for index in range(2):
            row = ttk.Frame(parent); row.pack(fill=tk.X, pady=5)
            ttk.Label(row, text=f"Строка {index + 1}:", width=10).pack(side=tk.LEFT)
            entry = ttk.Entry(row, textvariable=self.lines[index], font=("Consolas", 15), width=20)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            entry.bind("<FocusIn>", lambda _e, i=index: setattr(self, "active_line", i))
            self.lines[index].trace_add("write", lambda *_args, i=index: self._line_changed(i))
            ttk.Label(row, textvariable=self.counters[index], width=6).pack(side=tk.LEFT, padx=8)

        markers = ttk.LabelFrame(parent, text="Пользовательские символы", padding=8)
        markers.pack(fill=tk.X, pady=10)
        for index, marker in enumerate(CUSTOM_MARKERS):
            ttk.Button(markers, text=marker, width=4, command=lambda i=index: self.insert_marker(i)).pack(side=tk.LEFT, padx=3)
            ttk.Label(markers, textvariable=self.slot_names[index]).pack(side=tk.LEFT, padx=(0, 8))

        buttons = ttk.Frame(parent); buttons.pack(fill=tk.X, pady=8)
        ttk.Button(buttons, text="Отправить экран", command=self.send_screen).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(buttons, text="Очистить LCD", command=lambda: self.send("CLEAR")).pack(side=tk.LEFT, padx=8)
        ttk.Button(buttons, text="Подсветка ВКЛ", command=lambda: self.send("BACKLIGHT ON")).pack(side=tk.LEFT)
        ttk.Button(buttons, text="Подсветка ВЫКЛ", command=lambda: self.send("BACKLIGHT OFF")).pack(side=tk.LEFT, padx=(8, 0))

    def _build_glyphs(self, parent: ttk.Frame) -> None:
        left = ttk.Frame(parent); left.pack(side=tk.LEFT, fill=tk.Y)
        right = ttk.Frame(parent); right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(18, 0))
        slot_row = ttk.Frame(left); slot_row.pack(fill=tk.X)
        ttk.Label(slot_row, text="Слот:").pack(side=tk.LEFT)
        for index in range(8):
            ttk.Radiobutton(slot_row, text=str(index + 1), value=index, variable=self.slot, command=self.load_slot).pack(side=tk.LEFT)
        name_row = ttk.Frame(left); name_row.pack(fill=tk.X, pady=8)
        ttk.Label(name_row, text="Название:").pack(side=tk.LEFT)
        ttk.Entry(name_row, textvariable=self.editor_name, width=23).pack(side=tk.LEFT, padx=5)
        grid = ttk.Frame(left); grid.pack(pady=4)
        for y in range(8):
            row: list[tk.Button] = []
            for x in range(5):
                button = tk.Button(grid, width=3, height=1, command=lambda x=x, y=y: self.toggle_pixel(x, y))
                button.grid(row=y, column=x, padx=1, pady=1)
                row.append(button)
            self.pixel_buttons.append(row)
        action = ttk.Frame(left); action.pack(fill=tk.X, pady=8)
        ttk.Button(action, text="Очистить", command=self.clear_editor).pack(side=tk.LEFT)
        ttk.Button(action, text="Применить к слоту", command=self.apply_slot).pack(side=tk.LEFT, padx=6)
        ttk.Button(action, text="Отправить слот", command=self.send_current_glyph).pack(side=tk.LEFT)
        ttk.Button(left, text="Отправить все 8 слотов", command=self.send_all_glyphs).pack(fill=tk.X)
        ttk.Button(left, text="Сохранить в библиотеку", command=self.save_to_library).pack(fill=tk.X, pady=6)

        ttk.Label(right, text="Библиотека символов", font=("Segoe UI", 12, "bold")).pack(anchor=tk.W)
        self.library = tk.Listbox(right, height=18)
        self.library.pack(fill=tk.BOTH, expand=True, pady=6)
        self.library.bind("<<ListboxSelect>>", lambda _e: self.preview_library())
        ttk.Button(right, text="Загрузить выбранный в редактор", command=self.load_library_symbol).pack(fill=tk.X)
        ttk.Button(right, text="Удалить пользовательский символ", command=self.delete_user_symbol).pack(fill=tk.X, pady=5)

    def _line_changed(self, index: int) -> None:
        value = self.lines[index].get()
        if len(value) > 16:
            self.lines[index].set(value[:16]); return
        self.counters[index].set(f"{len(value)}/16")

    def insert_marker(self, slot: int) -> None:
        value = self.lines[self.active_line].get()
        if len(value) < 16:
            self.lines[self.active_line].set(value + CUSTOM_MARKERS[slot])

    def toggle_pixel(self, x: int, y: int) -> None:
        self.editor_rows[y] ^= 1 << (4 - x)
        self._refresh_pixels()

    def _refresh_pixels(self) -> None:
        for y, row in enumerate(self.pixel_buttons):
            for x, button in enumerate(row):
                active = bool(self.editor_rows[y] & (1 << (4 - x)))
                button.configure(bg="#202020" if active else "#f0f0f0")

    def clear_editor(self) -> None:
        self.editor_rows = [0] * 8
        self._refresh_pixels()

    def load_slot(self) -> None:
        index = self.slot.get()
        self.editor_rows = list(self.slot_patterns[index])
        self.editor_name.set(self.slot_names[index].get())
        self._refresh_pixels()

    def apply_slot(self) -> None:
        index = self.slot.get()
        name = self.editor_name.get().strip() or f"Символ {index + 1}"
        self.slot_patterns[index] = tuple(self.editor_rows)  # type: ignore[assignment]
        self.slot_names[index].set(name)
        self.status.set(f"Символ применён к слоту {index + 1}")

    def _all_symbols(self) -> dict[str, Glyph]:
        return {**BUILTIN_SYMBOLS, **self.user_symbols}

    def _refresh_library(self) -> None:
        self.library.delete(0, tk.END)
        for name in sorted(self._all_symbols()): self.library.insert(tk.END, name)

    def selected_library_name(self) -> str | None:
        selection = self.library.curselection()
        return self.library.get(selection[0]) if selection else None

    def preview_library(self) -> None:
        name = self.selected_library_name()
        if name:
            self.editor_name.set(name)
            self.editor_rows = list(self._all_symbols()[name])
            self._refresh_pixels()

    def load_library_symbol(self) -> None:
        self.preview_library(); self.apply_slot()

    def save_to_library(self) -> None:
        name = self.editor_name.get().strip()
        if not name:
            name = simpledialog.askstring("Название", "Введите название символа:") or ""
        if not name: return
        self.user_symbols[name] = tuple(self.editor_rows)  # type: ignore[assignment]
        save_user_symbols(USER_LIBRARY_PATH, self.user_symbols)
        self._refresh_library()
        self.status.set(f"Символ «{name}» сохранён")

    def delete_user_symbol(self) -> None:
        name = self.selected_library_name()
        if name and name in self.user_symbols:
            del self.user_symbols[name]
            save_user_symbols(USER_LIBRARY_PATH, self.user_symbols)
            self._refresh_library()

    def send_screen(self) -> None:
        bad = unsupported_characters(self.lines[0].get() + self.lines[1].get())
        if bad and not messagebox.askyesno("Неподдерживаемые знаки", "Часть Unicode-символов будет заменена на ?. Продолжить?"):
            return
        self.send(command_text(self.lines[0].get(), self.lines[1].get()))

    def send_current_glyph(self) -> None:
        self.apply_slot()
        index = self.slot.get()
        self.send(command_glyph(index, self.slot_patterns[index]))

    def send_all_glyphs(self) -> None:
        if not self.connected(): self._warn(); return
        self.apply_slot()
        for index, pattern in enumerate(self.slot_patterns):
            self._write(command_glyph(index, pattern))

    def refresh_ports(self) -> None:
        ports = list(list_ports.comports())
        labels = []
        self.port_map.clear()
        for port in ports:
            label = f"{port.device} — {port.description or 'без описания'}"
            labels.append(label); self.port_map[label] = port.device
        self.port_combo["values"] = labels
        if labels: self.port_combo.current(0)

    def toggle_connection(self) -> None:
        self.disconnect() if self.connected() else self.connect()

    def connected(self) -> bool:
        return self.port is not None and self.port.is_open

    def connect(self) -> None:
        device = self.port_map.get(self.port_combo.get())
        if not device: messagebox.showwarning("Нет порта", "Выберите COM-порт."); return
        try: self.port = serial.Serial(device, BAUD_RATE, timeout=0.2, write_timeout=1)
        except serial.SerialException as exc: messagebox.showerror("Ошибка подключения", str(exc)); return
        self.stop_reader.clear()
        self.reader = threading.Thread(target=self._reader_loop, daemon=True); self.reader.start()
        self.connect_button.configure(text="Отключить")
        self.connection.set(f"Подключено к {device}; UNO перезапускается…")
        self.root.after(HANDSHAKE_DELAY_MS, self._handshake)

    def _handshake(self) -> None:
        if self.connected():
            self.connection.set(f"Подключено к {self.port.port}")
            self._write("PING"); self._write("STATUS")

    def disconnect(self) -> None:
        self.stop_reader.set()
        port, self.port = self.port, None
        if port:
            try: port.close()
            except serial.SerialException: pass
        self.connect_button.configure(text="Подключить")
        self.connection.set("Не подключено")

    def _reader_loop(self) -> None:
        while not self.stop_reader.is_set() and self.port:
            try:
                raw = self.port.readline()
                if raw:
                    line = raw.decode("utf-8", errors="replace").strip()
                    if line: self.rx.put(("RX", line))
            except serial.SerialException as exc:
                self.rx.put(("ERR", str(exc))); return

    def _poll_rx(self) -> None:
        try:
            while True:
                kind, text = self.rx.get_nowait(); self._append_log(kind, text)
                state = parse_state(text)
                if state: self.device.set(f"I2C 0x{state.i2c_address:02X}; подсветка {'вкл.' if state.backlight_on else 'выкл.'}")
                if kind == "ERR": self.disconnect(); messagebox.showerror("Ошибка Serial", text)
        except queue.Empty: pass
        self.root.after(100, self._poll_rx)

    def _warn(self) -> None:
        messagebox.showwarning("Нет соединения", "Сначала подключитесь к Arduino UNO.")

    def send(self, command: str) -> None:
        if not self.connected(): self._warn(); return
        self._write(command)

    def _write(self, command: str) -> None:
        if not self.port: return
        try:
            self.port.write((command + "\n").encode("ascii")); self.port.flush(); self._append_log("TX", command)
        except serial.SerialException as exc: messagebox.showerror("Ошибка отправки", str(exc)); self.disconnect()

    def _append_log(self, direction: str, text: str) -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {direction}> {text}\n")
        self.log.see(tk.END); self.log.configure(state=tk.DISABLED)

    def close(self) -> None:
        self.disconnect(); self.root.destroy()


def main() -> None:
    root = tk.Tk()
    try: ttk.Style(root).theme_use("vista")
    except tk.TclError: pass
    Lcd1602App(root)
    root.mainloop()


if __name__ == "__main__": main()
