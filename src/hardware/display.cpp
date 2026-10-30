#include <Arduino.h>

#include "hardware/display.h"
#include "eyes/eye_config.h"

LGFX tft;

void displayInit() {
  // Assert ALL chip selects first, so both displays on the shared bus
  // receive the panel init sequence that tft.init() sends.
  for (uint8_t e = 0; e < EYE_COUNT; e++) {
    pinMode(kEyeInfo[e].cs, OUTPUT);
    digitalWrite(kEyeInfo[e].cs, LOW);
  }

  tft.init();

  // Then configure each display individually (rotation, clear screen).
  for (uint8_t e = 0; e < EYE_COUNT; e++) {
    for (uint8_t j = 0; j < EYE_COUNT; j++) {
      digitalWrite(kEyeInfo[j].cs, (j == e) ? LOW : HIGH);
    }
    tft.setRotation(kEyeInfo[e].rotation);
    tft.fillScreen(0);  // black
  }
}
