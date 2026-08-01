# KONTAKTS-UNO-PROJ-001 — Blink Baseline

## Цель

Проверить минимальный полный тракт: компиляция → загрузчик → MCU → встроенный LED → Serial → неблокирующий таймер.

Это контрольный проект для новой платы и новой среды. Он не использует `delay()` в основном цикле, поэтому позже может стать основой аппаратного smoke test.

## Поддерживаемая плата

- Arduino UNO R3 и совместимые платы с корректным определением `LED_BUILTIN`;
- базовая цель Arduino CLI: `arduino:avr:uno`;
- базовая цель PlatformIO: `uno`.

## Ожидаемое поведение

- Serial: 115200 бод;
- при старте выводится идентификатор проекта;
- встроенный LED меняет состояние каждые 500 мс;
- в Serial печатается номер перехода и значение `millis()`.

## Arduino IDE / CLI

Открыть:

`firmware/arduino-ide/blink_baseline/blink_baseline.ino`

Сборка CLI:

```bash
arduino-cli core update-index
arduino-cli core install arduino:avr@1.8.8
arduino-cli compile --fqbn arduino:avr:uno firmware/arduino-ide/blink_baseline
```

Загрузка выполняется после подстановки фактического порта:

```bash
arduino-cli upload -p COM3 --fqbn arduino:avr:uno firmware/arduino-ide/blink_baseline
```

## PlatformIO

```bash
cd firmware/platformio
pio run
pio run -t upload
pio device monitor
```

## Критерий `BENCH-TESTED`

Нужны фотография конкретной платы, журнал Serial не менее 20 переключений и указание среды/версии core.
