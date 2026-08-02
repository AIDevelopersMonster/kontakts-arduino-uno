/*
  KONTAKTS-UNO-PROJ-003 — GUI LCD1602 I2C

  USB Serial protocol, 115200 baud:
    PING
    STATUS
    CLEAR
    BACKLIGHT ON|OFF
    TEXT <32 hex chars> <32 hex chars>
    GLYPH <slot 0..7> <16 hex chars>
*/

#include <Arduino.h>
#include <LiquidCrystal_I2C.h>
#include <Wire.h>
#include <ctype.h>
#include <string.h>

namespace {
constexpr unsigned long SERIAL_BAUD = 115200;
constexpr uint8_t LCD_ADDRESS = 0x27;
constexpr uint8_t LCD_COLUMNS = 16;
constexpr uint8_t LCD_ROWS = 2;
constexpr size_t COMMAND_BUFFER_SIZE = 96;

LiquidCrystal_I2C lcd(LCD_ADDRESS, LCD_COLUMNS, LCD_ROWS);
char commandBuffer[COMMAND_BUFFER_SIZE];
size_t commandLength = 0;
bool backlightEnabled = true;

const uint8_t DEFAULT_GLYPHS[8][8] PROGMEM = {
  {0,10,31,31,31,14,4,0},{0,10,10,0,17,14,0,0},
  {4,14,21,4,4,4,4,0},{4,4,4,4,21,14,4,0},
  {0,1,2,20,8,0,0,0},{0,17,10,4,10,17,0,0},
  {4,10,10,10,17,17,14,0},{14,17,27,27,27,17,31,0}
};

void uppercaseInPlace(char* text) {
  for (; *text; ++text) *text = static_cast<char>(toupper(static_cast<unsigned char>(*text)));
}

int8_t hexValue(char value) {
  if (value >= '0' && value <= '9') return value - '0';
  if (value >= 'A' && value <= 'F') return value - 'A' + 10;
  return -1;
}

bool decodeHexBytes(const char* text, uint8_t* output, size_t count) {
  if (strlen(text) != count * 2) return false;
  for (size_t i = 0; i < count; ++i) {
    int8_t hi = hexValue(text[i * 2]);
    int8_t lo = hexValue(text[i * 2 + 1]);
    if (hi < 0 || lo < 0) return false;
    output[i] = static_cast<uint8_t>((hi << 4) | lo);
  }
  return true;
}

void reportState() {
  Serial.print(F("STATE ADDR=0x"));
  if (LCD_ADDRESS < 0x10) Serial.print('0');
  Serial.print(LCD_ADDRESS, HEX);
  Serial.print(F(" BACKLIGHT="));
  Serial.println(backlightEnabled ? 1 : 0);
}

void writeRow(uint8_t row, const uint8_t data[LCD_COLUMNS]) {
  lcd.setCursor(0, row);
  for (uint8_t col = 0; col < LCD_COLUMNS; ++col) lcd.write(data[col]);
}

void loadDefaultGlyphs() {
  uint8_t rows[8];
  for (uint8_t slot = 0; slot < 8; ++slot) {
    for (uint8_t row = 0; row < 8; ++row) rows[row] = pgm_read_byte(&DEFAULT_GLYPHS[slot][row]);
    lcd.createChar(slot, rows);
  }
}

void processText(char* args) {
  char* separator = strchr(args, ' ');
  if (!separator) { Serial.println(F("ERR TEXT_FORMAT")); return; }
  *separator = '\0';
  char* firstHex = args;
  char* secondHex = separator + 1;
  if (strchr(secondHex, ' ')) { Serial.println(F("ERR TEXT_FORMAT")); return; }
  uint8_t first[LCD_COLUMNS], second[LCD_COLUMNS];
  if (!decodeHexBytes(firstHex, first, LCD_COLUMNS) || !decodeHexBytes(secondHex, second, LCD_COLUMNS)) {
    Serial.println(F("ERR BAD_HEX_TEXT")); return;
  }
  writeRow(0, first);
  writeRow(1, second);
  Serial.println(F("OK TEXT"));
}

void processGlyph(char* args) {
  if (args[0] < '0' || args[0] > '7' || args[1] != ' ') { Serial.println(F("ERR GLYPH_SLOT")); return; }
  uint8_t slot = args[0] - '0';
  char* payload = args + 2;
  uint8_t rows[8];
  if (strchr(payload, ' ') || !decodeHexBytes(payload, rows, 8)) { Serial.println(F("ERR BAD_HEX_GLYPH")); return; }
  for (uint8_t row = 0; row < 8; ++row) if (rows[row] > 31) { Serial.println(F("ERR GLYPH_ROW_RANGE")); return; }
  lcd.createChar(slot, rows);
  lcd.setCursor(0, 0);
  Serial.print(F("OK GLYPH "));
  Serial.println(slot);
}

void processCommand(char* command) {
  while (*command == ' ') ++command;
  char* end = command + strlen(command);
  while (end > command && end[-1] == ' ') --end;
  *end = '\0';
  uppercaseInPlace(command);
  if (!strcmp(command, "PING")) { Serial.println(F("PONG GUI_LCD1602/1")); return; }
  if (!strcmp(command, "STATUS")) { reportState(); return; }
  if (!strcmp(command, "CLEAR")) { lcd.clear(); Serial.println(F("OK CLEAR")); return; }
  if (!strcmp(command, "BACKLIGHT ON")) { lcd.backlight(); backlightEnabled = true; Serial.println(F("OK BACKLIGHT ON")); reportState(); return; }
  if (!strcmp(command, "BACKLIGHT OFF")) { lcd.noBacklight(); backlightEnabled = false; Serial.println(F("OK BACKLIGHT OFF")); reportState(); return; }
  if (!strncmp(command, "TEXT ", 5)) { processText(command + 5); return; }
  if (!strncmp(command, "GLYPH ", 6)) { processGlyph(command + 6); return; }
  Serial.println(F("ERR UNKNOWN_COMMAND"));
}

void readSerialCommands() {
  while (Serial.available() > 0) {
    char incoming = static_cast<char>(Serial.read());
    if (incoming == '\r') continue;
    if (incoming == '\n') {
      commandBuffer[commandLength] = '\0';
      if (commandLength) processCommand(commandBuffer);
      commandLength = 0;
    } else if (commandLength < COMMAND_BUFFER_SIZE - 1) {
      commandBuffer[commandLength++] = incoming;
    } else {
      commandLength = 0;
      Serial.println(F("ERR LINE_TOO_LONG"));
    }
  }
}
}  // namespace

void setup() {
  Wire.begin();
  lcd.init();
  lcd.backlight();
  loadDefaultGlyphs();
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(F("KONTAKTS LCD1602"));
  lcd.setCursor(0, 1);
  lcd.print(F("USB GUI READY"));
  Serial.begin(SERIAL_BAUD);
  Serial.println(F("READY KONTAKTS-UNO-PROJ-003 GUI_LCD1602/1"));
  reportState();
}

void loop() { readSerialCommands(); }
