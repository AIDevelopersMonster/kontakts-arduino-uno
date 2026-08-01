# KONTAKTS-UNO-PROJ-002 — GUI Blink

**Статус: `BENCH-TESTED`** — прошивка и Windows GUI проверены пользователем на реальной Arduino UNO.

## Что делает проект

Windows-приложение управляет встроенным светодиодом Arduino UNO через USB/Serial:

- подключение к выбранному COM-порту;
- автоматическая сортировка вероятных Arduino/CH340-портов;
- команды **Включить**, **Выключить**, **Запустить мигание**;
- регулировка частоты от 0,2 до 10 Гц;
- запрос фактического состояния платы;
- журнал переданных и полученных строк;
- неблокирующее мигание в прошивке без `delay()`.

## Требования

- Arduino UNO R3 или совместимая плата;
- Arduino IDE 2.x либо Arduino CLI;
- Windows 10/11;
- Python 3.10 или новее;
- USB-кабель с передачей данных.

## 1. Загрузка прошивки

Откройте в Arduino IDE:

```text
firmware/arduino-ide/gui_blink/gui_blink.ino
```

Выберите **Arduino UNO**, правильный COM-порт и загрузите скетч.

Сборка через Arduino CLI:

```bash
arduino-cli core update-index
arduino-cli core install arduino:avr@1.8.8
arduino-cli compile --fqbn arduino:avr:uno firmware/arduino-ide/gui_blink
arduino-cli upload -p COM3 --fqbn arduino:avr:uno firmware/arduino-ide/gui_blink
```

Замените `COM3` на фактический порт платы.

## 2. Запуск GUI в Windows

Дважды щёлкните:

```text
run_gui.bat
```

При первом запуске скрипт создаст локальное окружение `.venv` и установит `pyserial`. Tkinter входит в стандартную поставку Python для Windows.

Ручной запуск:

```powershell
py -3 -m venv .venv
.venv\Scripts\python -m pip install -r gui\requirements.txt
.venv\Scripts\python -m gui.app
```

## 3. Проверка

1. Закройте Serial Monitor Arduino IDE — один COM-порт нельзя одновременно открыть в двух программах.
2. Запустите GUI.
3. Выберите порт и нажмите **Подключить**.
4. Подождите около двух секунд: открытие Serial перезапускает UNO.
5. В журнале должны появиться строки `READY`, `PONG` и `STATE`.
6. Проверьте включение, выключение и несколько частот мигания.

## Протокол Serial

Скорость: **115200 бод**, строки завершаются `\n`.

| Команда ПК | Ответ платы | Назначение |
|---|---|---|
| `PING` | `PONG GUI_BLINK/1` | проверка совместимости |
| `STATUS` | `STATE ...` | запрос состояния |
| `ON` | `STATE MODE=ON ...` | постоянное включение |
| `OFF` | `STATE MODE=OFF ...` | выключение |
| `BLINK 1000` | `STATE MODE=BLINK ...` | полный период 1000 мс |

Допустимый период: от 100 до 10 000 мс. Ошибки возвращаются строками, начинающимися с `ERR`.

## Тесты GUI-протокола

Без подключения платы:

```powershell
py -3 -m unittest discover -s gui\tests -v
```

Либо запустите `run_tests.bat`.

## Результат стендовой проверки

Пользователь подтвердил успешную работу проекта на реальной Arduino UNO: подключение, включение и выключение LED, мигание и регулировка частоты работают. Программные тесты протокола: **5 из 5**.
