/*
  KONTAKTS-UNO-PROJ-002 — GUI Blink

  Text protocol over USB Serial, 115200 baud:
    PING
    STATUS
    ON
    OFF
    BLINK <period_ms>

  The blink loop is non-blocking and does not use delay().
*/

#include <Arduino.h>
#include <ctype.h>
#include <stdlib.h>
#include <string.h>

namespace {

constexpr unsigned long SERIAL_BAUD = 115200;
constexpr unsigned long DEFAULT_PERIOD_MS = 1000;
constexpr unsigned long MIN_PERIOD_MS = 100;
constexpr unsigned long MAX_PERIOD_MS = 10000;
constexpr size_t COMMAND_BUFFER_SIZE = 48;

enum LedMode : uint8_t {
  MODE_OFF,
  MODE_ON,
  MODE_BLINK
};

LedMode mode = MODE_OFF;
bool ledState = false;
unsigned long blinkPeriodMs = DEFAULT_PERIOD_MS;
unsigned long lastToggleMs = 0;
char commandBuffer[COMMAND_BUFFER_SIZE];
size_t commandLength = 0;

const __FlashStringHelper* modeName() {
  switch (mode) {
    case MODE_ON:
      return F("ON");
    case MODE_BLINK:
      return F("BLINK");
    case MODE_OFF:
    default:
      return F("OFF");
  }
}

void applyLed(bool enabled) {
  ledState = enabled;
  digitalWrite(LED_BUILTIN, enabled ? HIGH : LOW);
}

void reportState() {
  Serial.print(F("STATE MODE="));
  Serial.print(modeName());
  Serial.print(F(" LED="));
  Serial.print(ledState ? 1 : 0);
  Serial.print(F(" PERIOD_MS="));
  Serial.println(blinkPeriodMs);
}

void setModeOff() {
  mode = MODE_OFF;
  applyLed(false);
  reportState();
}

void setModeOn() {
  mode = MODE_ON;
  applyLed(true);
  reportState();
}

void setModeBlink(unsigned long periodMs) {
  blinkPeriodMs = periodMs;
  mode = MODE_BLINK;
  applyLed(true);
  lastToggleMs = millis();
  reportState();
}

void uppercaseInPlace(char* text) {
  for (; *text != '\0'; ++text) {
    *text = static_cast<char>(toupper(static_cast<unsigned char>(*text)));
  }
}

void processCommand(char* command) {
  while (*command == ' ') {
    ++command;
  }

  char* end = command + strlen(command);
  while (end > command && end[-1] == ' ') {
    --end;
  }
  *end = '\0';

  uppercaseInPlace(command);

  if (strcmp(command, "PING") == 0) {
    Serial.println(F("PONG GUI_BLINK/1"));
    return;
  }

  if (strcmp(command, "STATUS") == 0) {
    reportState();
    return;
  }

  if (strcmp(command, "ON") == 0) {
    setModeOn();
    return;
  }

  if (strcmp(command, "OFF") == 0) {
    setModeOff();
    return;
  }

  constexpr char BLINK_PREFIX[] = "BLINK ";
  if (strncmp(command, BLINK_PREFIX, sizeof(BLINK_PREFIX) - 1) == 0) {
    char* valueText = command + sizeof(BLINK_PREFIX) - 1;
    char* parseEnd = nullptr;
    const unsigned long value = strtoul(valueText, &parseEnd, 10);

    while (parseEnd != nullptr && *parseEnd == ' ') {
      ++parseEnd;
    }

    if (valueText == parseEnd || parseEnd == nullptr || *parseEnd != '\0') {
      Serial.println(F("ERR BAD_PERIOD"));
      return;
    }

    if (value < MIN_PERIOD_MS || value > MAX_PERIOD_MS) {
      Serial.println(F("ERR PERIOD_RANGE 100..10000"));
      return;
    }

    setModeBlink(value);
    return;
  }

  Serial.println(F("ERR UNKNOWN_COMMAND"));
}

void readSerialCommands() {
  while (Serial.available() > 0) {
    const char incoming = static_cast<char>(Serial.read());

    if (incoming == '\r') {
      continue;
    }

    if (incoming == '\n') {
      commandBuffer[commandLength] = '\0';
      if (commandLength > 0) {
        processCommand(commandBuffer);
      }
      commandLength = 0;
      continue;
    }

    if (commandLength < COMMAND_BUFFER_SIZE - 1) {
      commandBuffer[commandLength++] = incoming;
    } else {
      commandLength = 0;
      Serial.println(F("ERR LINE_TOO_LONG"));
    }
  }
}

void updateBlink() {
  if (mode != MODE_BLINK) {
    return;
  }

  const unsigned long now = millis();
  const unsigned long halfPeriod = blinkPeriodMs / 2;
  if (now - lastToggleMs >= halfPeriod) {
    lastToggleMs = now;
    applyLed(!ledState);
  }
}

}  // namespace

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  applyLed(false);

  Serial.begin(SERIAL_BAUD);
  Serial.println(F("READY KONTAKTS-UNO-PROJ-002 GUI_BLINK/1"));
  reportState();
}

void loop() {
  readSerialCommands();
  updateBlink();
}
