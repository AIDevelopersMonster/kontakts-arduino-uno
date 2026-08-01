"""Tkinter GUI for controlling the Arduino UNO built-in LED over USB Serial."""

from __future__ import annotations

import queue
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

try:
    import serial
    from serial.tools import list_ports
except ImportError as exc:  # pragma: no cover - user-facing startup guard
    raise SystemExit(
        "PySerial is not installed. Run: python -m pip install -r gui/requirements.txt"
    ) from exc

from gui.protocol import command_blink, parse_state

BAUD_RATE = 115200
HANDSHAKE_DELAY_MS = 1800
PORT_HINTS = ("arduino", "ch340", "usb-serial", "usb serial", "cp210")
KNOWN_VIDS = {0x2341, 0x2A03, 0x1A86}


class GuiBlinkApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("KONTAKTS Arduino UNO — GUI Blink")
        self.root.geometry("760x540")
        self.root.minsize(680, 480)

        self.serial_port: serial.Serial | None = None
        self.reader_thread: threading.Thread | None = None
        self.stop_reader = threading.Event()
        self.rx_queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self.port_by_label: dict[str, str] = {}

        self.connection_text = tk.StringVar(value="Не подключено")
        self.device_state_text = tk.StringVar(value="Состояние платы неизвестно")
        self.frequency_hz = tk.DoubleVar(value=1.0)
        self.frequency_text = tk.StringVar(value="1.00 Гц — период 1000 мс")

        self._build_ui()
        self.refresh_ports()
        self.root.after(100, self._process_rx_queue)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=16)
        outer.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(
            outer,
            text="GUI Blink для Arduino UNO",
            font=("Segoe UI", 18, "bold"),
        )
        title.pack(anchor=tk.W)
        ttk.Label(
            outer,
            text="Управление встроенным светодиодом через USB/Serial без delay()",
        ).pack(anchor=tk.W, pady=(0, 14))

        connection = ttk.LabelFrame(outer, text="Подключение", padding=12)
        connection.pack(fill=tk.X)

        port_row = ttk.Frame(connection)
        port_row.pack(fill=tk.X)
        ttk.Label(port_row, text="COM-порт:").pack(side=tk.LEFT)
        self.port_combo = ttk.Combobox(port_row, state="readonly", width=48)
        self.port_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        ttk.Button(port_row, text="Обновить", command=self.refresh_ports).pack(side=tk.LEFT)

        connect_row = ttk.Frame(connection)
        connect_row.pack(fill=tk.X, pady=(10, 0))
        self.connect_button = ttk.Button(
            connect_row, text="Подключить", command=self.toggle_connection
        )
        self.connect_button.pack(side=tk.LEFT)
        ttk.Button(connect_row, text="Запросить состояние", command=self.request_status).pack(
            side=tk.LEFT, padx=8
        )
        ttk.Label(connect_row, textvariable=self.connection_text).pack(side=tk.LEFT, padx=12)

        control = ttk.LabelFrame(outer, text="Управление LED", padding=12)
        control.pack(fill=tk.X, pady=14)

        buttons = ttk.Frame(control)
        buttons.pack(fill=tk.X)
        ttk.Button(buttons, text="Включить", command=lambda: self.send_command("ON")).pack(
            side=tk.LEFT, expand=True, fill=tk.X
        )
        ttk.Button(buttons, text="Выключить", command=lambda: self.send_command("OFF")).pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=8
        )
        ttk.Button(buttons, text="Запустить мигание", command=self.start_blink).pack(
            side=tk.LEFT, expand=True, fill=tk.X
        )

        ttk.Label(control, text="Частота мигания:").pack(anchor=tk.W, pady=(14, 0))
        slider = ttk.Scale(
            control,
            from_=0.2,
            to=10.0,
            variable=self.frequency_hz,
            command=self._frequency_changed,
        )
        slider.pack(fill=tk.X)
        ttk.Label(control, textvariable=self.frequency_text).pack(anchor=tk.W)

        state_row = ttk.Frame(control)
        state_row.pack(fill=tk.X, pady=(12, 0))
        self.indicator = tk.Canvas(state_row, width=30, height=30, highlightthickness=0)
        self.indicator.pack(side=tk.LEFT)
        self.indicator_id = self.indicator.create_oval(5, 5, 25, 25, fill="#808080", outline="")
        ttk.Label(state_row, textvariable=self.device_state_text).pack(side=tk.LEFT, padx=8)

        log_frame = ttk.LabelFrame(outer, text="Журнал Serial", padding=8)
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log = tk.Text(log_frame, height=12, state=tk.DISABLED, wrap=tk.WORD)
        self.log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log.configure(yscrollcommand=scrollbar.set)

    def refresh_ports(self) -> None:
        previous_device = self.selected_device()
        discovered = list(list_ports.comports())
        discovered.sort(key=self._port_score, reverse=True)

        self.port_by_label.clear()
        labels: list[str] = []
        best_index = 0
        for index, port in enumerate(discovered):
            description = port.description or "без описания"
            label = f"{port.device} — {description}"
            labels.append(label)
            self.port_by_label[label] = port.device
            if port.device == previous_device:
                best_index = index

        self.port_combo["values"] = labels
        if labels:
            self.port_combo.current(best_index)
            self._append_log("SYS", f"Найдено портов: {len(labels)}")
        else:
            self.port_combo.set("")
            self._append_log("SYS", "COM-порты не найдены")

    @staticmethod
    def _port_score(port: object) -> tuple[int, str]:
        description = str(getattr(port, "description", "")).lower()
        vid = getattr(port, "vid", None)
        score = 0
        if vid in KNOWN_VIDS:
            score += 10
        if any(hint in description for hint in PORT_HINTS):
            score += 5
        return score, str(getattr(port, "device", ""))

    def selected_device(self) -> str | None:
        return self.port_by_label.get(self.port_combo.get())

    def toggle_connection(self) -> None:
        if self.serial_port is not None and self.serial_port.is_open:
            self.disconnect()
        else:
            self.connect()

    def connect(self) -> None:
        device = self.selected_device()
        if not device:
            messagebox.showwarning("Нет порта", "Выберите COM-порт Arduino UNO.")
            return

        try:
            self.serial_port = serial.Serial(
                port=device,
                baudrate=BAUD_RATE,
                timeout=0.2,
                write_timeout=1.0,
            )
        except serial.SerialException as exc:
            self.serial_port = None
            messagebox.showerror("Ошибка подключения", str(exc))
            return

        self.stop_reader.clear()
        self.reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self.reader_thread.start()
        self.connect_button.configure(text="Отключить")
        self.connection_text.set(f"Подключено к {device}; плата перезапускается…")
        self._append_log("SYS", f"Открыт {device} @ {BAUD_RATE}")
        self.root.after(HANDSHAKE_DELAY_MS, self._handshake)

    def _handshake(self) -> None:
        if self.serial_port is None or not self.serial_port.is_open:
            return
        self.connection_text.set(f"Подключено к {self.serial_port.port}")
        self.send_command("PING")
        self.send_command("STATUS")

    def disconnect(self) -> None:
        self.stop_reader.set()
        port = self.serial_port
        self.serial_port = None
        if port is not None:
            try:
                if port.is_open:
                    port.close()
            except serial.SerialException:
                pass

        self.connect_button.configure(text="Подключить")
        self.connection_text.set("Не подключено")
        self.device_state_text.set("Состояние платы неизвестно")
        self.indicator.itemconfigure(self.indicator_id, fill="#808080")
        self._append_log("SYS", "Соединение закрыто")

    def _reader_loop(self) -> None:
        while not self.stop_reader.is_set():
            port = self.serial_port
            if port is None or not port.is_open:
                return
            try:
                raw = port.readline()
                if raw:
                    line = raw.decode("utf-8", errors="replace").strip()
                    if line:
                        self.rx_queue.put(("RX", line))
            except serial.SerialException as exc:
                self.rx_queue.put(("ERROR", str(exc)))
                return

    def _process_rx_queue(self) -> None:
        try:
            while True:
                kind, payload = self.rx_queue.get_nowait()
                if kind == "ERROR":
                    self._append_log("ERR", payload)
                    self.disconnect()
                    messagebox.showerror("Ошибка Serial", payload)
                    break

                self._append_log(kind, payload)
                state = parse_state(payload)
                if state is not None:
                    led_word = "горит" if state.led_on else "погашен"
                    self.device_state_text.set(
                        f"Режим: {state.mode}; LED {led_word}; период {state.period_ms} мс"
                    )
                    self.indicator.itemconfigure(
                        self.indicator_id,
                        fill="#24a148" if state.led_on else "#404040",
                    )
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._process_rx_queue)

    def send_command(self, command: str) -> None:
        port = self.serial_port
        if port is None or not port.is_open:
            messagebox.showwarning("Нет соединения", "Сначала подключитесь к Arduino UNO.")
            return

        try:
            port.write((command + "\n").encode("ascii"))
            port.flush()
            self._append_log("TX", command)
        except serial.SerialException as exc:
            messagebox.showerror("Ошибка отправки", str(exc))
            self.disconnect()

    def request_status(self) -> None:
        self.send_command("STATUS")

    def start_blink(self) -> None:
        try:
            command = command_blink(float(self.frequency_hz.get()))
        except ValueError as exc:
            messagebox.showerror("Неверная частота", str(exc))
            return
        self.send_command(command)

    def _frequency_changed(self, _value: str) -> None:
        frequency = float(self.frequency_hz.get())
        period_ms = round(1000.0 / frequency)
        self.frequency_text.set(f"{frequency:.2f} Гц — период {period_ms} мс")

    def _append_log(self, direction: str, text: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, f"[{timestamp}] {direction}> {text}\n")
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)

    def close(self) -> None:
        self.disconnect()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    try:
        ttk.Style(root).theme_use("vista")
    except tk.TclError:
        pass
    GuiBlinkApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
