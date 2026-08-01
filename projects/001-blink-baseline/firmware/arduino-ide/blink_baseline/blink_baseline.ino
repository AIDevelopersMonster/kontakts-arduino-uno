#include <Arduino.h>

namespace {
constexpr unsigned long kBaudRate = 115200UL;
constexpr unsigned long kTogglePeriodMs = 500UL;
constexpr char kProjectId[] = "KONTAKTS-UNO-PROJ-001";

unsigned long lastToggleMs = 0;
unsigned long transitionCount = 0;
bool ledState = false;
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  Serial.begin(kBaudRate);
  Serial.println();
  Serial.print(F("project="));
  Serial.println(kProjectId);
  Serial.println(F("status=started"));
}

void loop() {
  const unsigned long nowMs = millis();
  if (nowMs - lastToggleMs < kTogglePeriodMs) {
    return;
  }

  lastToggleMs = nowMs;
  ledState = !ledState;
  digitalWrite(LED_BUILTIN, ledState ? HIGH : LOW);
  ++transitionCount;

  Serial.print(F("transition="));
  Serial.print(transitionCount);
  Serial.print(F(" millis="));
  Serial.print(nowMs);
  Serial.print(F(" led="));
  Serial.println(ledState ? 1 : 0);
}
