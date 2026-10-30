// Eye rendering, ported from eye_functions.ino of the original
// dalori/ESP32-uncanny-eyes-halloween-skull project (which in turn adapts
// the Adafruit "Uncanny Eyes" sketch by Phil Burgess, MIT license).
// TFT_eSPI was replaced by LovyanGFX; chip select is toggled manually
// because both displays share one SPI bus.

#include <Arduino.h>

#include "eyes/eye_assets.h"
#include "eyes/eye_config.h"
#include "eyes/eye_render.h"
#include "hardware/display.h"

#define BUFFER_SIZE 1024

// Two ping-pong buffers: one is filled while the previous one is still
// being pushed to the display via DMA.
static uint16_t pbuffer[2][BUFFER_SIZE];

void drawEye(uint8_t e, uint32_t iScale, uint32_t scleraX, uint32_t scleraY,
             uint32_t uT, uint32_t lT) {
  const eye_assets::EyeAssets& a = eye_assets::kAssets;
  const EyeInfo& info = kEyeInfo[e];

  uint32_t screenX, screenY, scleraXsave;
  int32_t irisX, irisY;
  uint32_t p;
  uint32_t d;
  uint32_t pixels = 0;
  uint8_t dmaBuf = 0;

  // Select this eye's display on the shared bus.
  for (uint8_t j = 0; j < EYE_COUNT; j++) {
    digitalWrite(kEyeInfo[j].cs, (j == e) ? LOW : HIGH);
  }

  // Set up raw pixel dump to the whole screen. The region is reset on each
  // frame in case of an SPI glitch.
  tft.startWrite();
  tft.setAddrWindow(info.xposition, 0, a.screenWidth, a.screenHeight);

  scleraXsave = scleraX;  // Save initial X value to reset on each line
  irisY = scleraY - (a.scleraHeight - a.irisHeight) / 2;

  // Iris edge trim: pixels within kIrisEdgeTrimPx of the polar box boundary
  // (their polar distance code is small) render sclera instead of iris,
  // shrinking the visible iris disc. Code rate is ~127 per box half-width.
  const uint32_t trimCode = (config::kIrisEdgeTrimPx > 0)
                                ? (uint32_t)config::kIrisEdgeTrimPx * 127 / (a.irisWidth / 2)
                                : 0;

  // Eyelid image is left<>right swapped for the two displays.
  uint16_t lidX = 0;
  uint16_t dlidX = (uint16_t)-1;
  if (e) dlidX = 1;

  for (screenY = 0; screenY < (uint32_t)a.screenHeight; screenY++, scleraY++, irisY++) {
    scleraX = scleraXsave;
    irisX = scleraX - (a.scleraWidth - a.irisWidth) / 2;
    if (e) lidX = 0; else lidX = a.screenWidth - 1;

    for (screenX = 0; screenX < (uint32_t)a.screenWidth;
         screenX++, scleraX++, irisX++, lidX += dlidX) {
      if ((pgm_read_byte(a.lower + screenY * a.screenWidth + lidX) <= lT) ||
          (pgm_read_byte(a.upper + screenY * a.screenWidth + lidX) <= uT)) {
        p = 0;  // Covered by eyelid
      } else if ((irisY < 0) || (irisY >= a.irisHeight) || (irisX < 0) ||
                 (irisX >= a.irisWidth)) {
        p = pgm_read_word(a.sclera + scleraY * a.scleraWidth + scleraX);  // In sclera
      } else {
        // Maybe iris...
        p = pgm_read_word(a.polar + irisY * a.irisWidth + irisX);  // Polar angle/dist
        uint32_t dist = p & 0x7F;
        d = (iScale * dist) / 128;  // Distance (Y)
        if (d < (uint32_t)a.irisMapHeight && dist >= trimCode) {  // Within iris area
          uint32_t ang = (a.irisMapWidth * (p >> 7)) / 512;  // Angle (X)
          p = pgm_read_word(a.iris + d * a.irisMapWidth + ang);  // Pixel = iris
        } else {
          p = pgm_read_word(a.sclera + scleraY * a.scleraWidth + scleraX);  // Pixel = sclera
        }
      }

      // RGB565 byte swap for the big-endian SPI panel; the ping-pong buffer
      // alternates while DMA pushes the previous chunk.
      pbuffer[dmaBuf][pixels++] = p >> 8 | p << 8;

      if (pixels >= BUFFER_SIZE) {
        yield();
        tft.waitDMA();
        tft.writePixelsDMA(&pbuffer[dmaBuf][0], (int32_t)pixels, false);
        dmaBuf = !dmaBuf;
        pixels = 0;
      }
    }
  }

  if (pixels) {
    tft.waitDMA();
    tft.writePixelsDMA(&pbuffer[dmaBuf][0], (int32_t)pixels, false);
  }
  tft.waitDMA();
  tft.endWrite();
}
