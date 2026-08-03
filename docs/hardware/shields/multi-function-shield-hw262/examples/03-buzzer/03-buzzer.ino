/*
  KONTAKTS Arduino UNO
  Multi-Function Shield test 03: buzzer

  Expected common mapping:
    buzzer -> Arduino D3

  The sketch plays three clearly different tones.
*/

const uint8_t BUZZER_PIN = 3;
const uint16_t NOTES[] = {523, 784, 1047};  // C5, G5, C6
const uint8_t NOTE_COUNT = sizeof(NOTES) / sizeof(NOTES[0]);

void setup() {
  Serial.begin(115200);
  pinMode(BUZZER_PIN, OUTPUT);
  noTone(BUZZER_PIN);

  Serial.println(F("KONTAKTS Multi-Function Shield: test 03 buzzer"));
  Serial.println(F("Expected: three different tones, then a pause."));
}

void loop() {
  for (uint8_t i = 0; i < NOTE_COUNT; ++i) {
    Serial.print(F("Tone "));
    Serial.print(i + 1);
    Serial.print(F(": "));
    Serial.print(NOTES[i]);
    Serial.println(F(" Hz"));

    tone(BUZZER_PIN, NOTES[i], 500);
    delay(700);
  }

  noTone(BUZZER_PIN);
  Serial.println(F("Pause"));
  delay(2000);
}
