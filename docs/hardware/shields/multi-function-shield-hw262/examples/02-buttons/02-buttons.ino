/*
  KONTAKTS Arduino UNO
  Multi-Function Shield test 02: buttons S1-S3

  Expected common mapping:
    S1 -> A1
    S2 -> A2
    S3 -> A3

  Buttons are expected to be active-low. Internal pull-ups are enabled.
  Matching LEDs D1-D3 are used as visible indicators.
*/

const uint8_t BUTTON_PINS[] = {A1, A2, A3};
const uint8_t LED_PINS[] = {13, 12, 11};
const uint8_t BUTTON_COUNT = sizeof(BUTTON_PINS) / sizeof(BUTTON_PINS[0]);

const unsigned long DEBOUNCE_MS = 30;

bool stablePressed[BUTTON_COUNT] = {false, false, false};
bool lastRawPressed[BUTTON_COUNT] = {false, false, false};
unsigned long changedAt[BUTTON_COUNT] = {0, 0, 0};

void setup() {
  Serial.begin(115200);

  for (uint8_t i = 0; i < BUTTON_COUNT; ++i) {
    pinMode(BUTTON_PINS[i], INPUT_PULLUP);
    pinMode(LED_PINS[i], OUTPUT);
    digitalWrite(LED_PINS[i], HIGH);  // active-low LED off
  }

  Serial.println(F("KONTAKTS Multi-Function Shield: test 02 buttons"));
  Serial.println(F("Press S1, S2 and S3 separately, then two together."));
}

void loop() {
  const unsigned long now = millis();

  for (uint8_t i = 0; i < BUTTON_COUNT; ++i) {
    const bool rawPressed = digitalRead(BUTTON_PINS[i]) == LOW;

    if (rawPressed != lastRawPressed[i]) {
      lastRawPressed[i] = rawPressed;
      changedAt[i] = now;
    }

    if ((now - changedAt[i] >= DEBOUNCE_MS) &&
        (stablePressed[i] != rawPressed)) {
      stablePressed[i] = rawPressed;

      Serial.print(F("S"));
      Serial.print(i + 1);
      Serial.println(stablePressed[i] ? F(" PRESSED") : F(" RELEASED"));
    }

    digitalWrite(LED_PINS[i], stablePressed[i] ? LOW : HIGH);
  }
}
