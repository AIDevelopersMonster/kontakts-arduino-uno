/*
  KONTAKTS Arduino UNO
  Multi-Function Shield test 01: LEDs D1-D4

  Expected common mapping:
    D1 -> Arduino D13
    D2 -> Arduino D12
    D3 -> Arduino D11
    D4 -> Arduino D10

  Many boards use active-low LEDs:
    LOW  = LED on
    HIGH = LED off

  Record whether the real board follows this order and logic.
*/

const uint8_t LED_PINS[] = {13, 12, 11, 10};
const uint8_t LED_COUNT = sizeof(LED_PINS) / sizeof(LED_PINS[0]);

const uint8_t LED_ON = LOW;
const uint8_t LED_OFF = HIGH;

void setAll(uint8_t state) {
  for (uint8_t i = 0; i < LED_COUNT; ++i) {
    digitalWrite(LED_PINS[i], state);
  }
}

void setup() {
  Serial.begin(115200);

  for (uint8_t i = 0; i < LED_COUNT; ++i) {
    pinMode(LED_PINS[i], OUTPUT);
  }

  setAll(LED_OFF);
  Serial.println(F("KONTAKTS Multi-Function Shield: test 01 LEDs"));
  Serial.println(F("Expected order: D1, D2, D3, D4, then all LEDs"));
}

void loop() {
  setAll(LED_OFF);
  delay(700);

  for (uint8_t i = 0; i < LED_COUNT; ++i) {
    Serial.print(F("LED D"));
    Serial.println(i + 1);

    digitalWrite(LED_PINS[i], LED_ON);
    delay(1000);
    digitalWrite(LED_PINS[i], LED_OFF);
    delay(300);
  }

  Serial.println(F("ALL LEDs"));
  for (uint8_t cycle = 0; cycle < 3; ++cycle) {
    setAll(LED_ON);
    delay(500);
    setAll(LED_OFF);
    delay(500);
  }

  Serial.println(F("Cycle complete"));
  delay(1500);
}
