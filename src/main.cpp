// Uncanny Eyes for ESP32-C3 Super Mini with two GC9A01 round displays.
//
// Ported from dalori/ESP32-uncanny-eyes-halloween-skull (Arduino IDE +
// TFT_eSPI) to PlatformIO + LovyanGFX. All pins live in include/config.h.
//
// See docs/reference/ for the original sketch files this project derives
// from, and README.md for wiring and build instructions.

#include <Arduino.h>

#include "hardware/display.h"
#include "eyes/eye_motion.h"
#include "user/user_hooks.h"

void setup() {
  Serial.begin(115200);
  Serial.println("uncanny eyes starting");

  displayInit();  // bus, both displays, rotation
  initEyes();     // blink/wink buttons
  user_setup();   // optional user hardware (jaw servo)

  Serial.println("running");
}

void loop() {
  updateEye();
}
