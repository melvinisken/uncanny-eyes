#pragma once

#include <cstdint>
#include <driver/gpio.h>

// ---------------------------------------------------------------------------
// Central configuration: pins, display setup and eye behaviour.
// Nothing in the LovyanGFX library needs to be edited - everything is set
// from this file (same principle as synex-c21/ESP32-Plane-Radar-metrers).
// ---------------------------------------------------------------------------

namespace config {

// --- Display: GC9A01 1.28" round 240x240 (SPI) ---------------------------
// Shared bus: SCLK/MOSI/DC/RST go to BOTH displays in parallel.
constexpr gpio_num_t kDisplayPinSclk = GPIO_NUM_4;  // display SCL
constexpr gpio_num_t kDisplayPinMosi = GPIO_NUM_3;  // display SDA
constexpr gpio_num_t kDisplayPinDc = GPIO_NUM_10;
constexpr gpio_num_t kDisplayPinRst = GPIO_NUM_0;  // shared reset

// Per-eye chip selects on the shared bus.
constexpr gpio_num_t kEye1PinCs = GPIO_NUM_1;
constexpr gpio_num_t kEye2PinCs = GPIO_NUM_2;  // unused when EYE_COUNT == 1

constexpr int kDisplayWidth = 240;
constexpr int kDisplayHeight = 240;

constexpr uint32_t kDisplaySpiWriteHz = 40000000;
// GC9A01 modules often need invert for correct colors.
// IMPORTANT: rgb_order MUST stay false here. The eye renderer pushes raw
// RGB565 pixels (writePixelsDMA, no LovyanGFX color conversion), and the
// asset tables use the standard RGB565 convention (R in bits 11-15, verified
// with scripts/check_color_order.py). With rgb_order = true the panel's
// MADCTL BGR bit would swap red and blue on screen. (The radar reference
// project used true - harmless there, because its drawing goes through
// LovyanGFX color conversions which compensate the swap in software.)
constexpr bool kDisplayInvert = true;
constexpr bool kDisplayRgbOrder = false;

// --- Buttons (active LOW, internal pullups) -------------------------------
// BOOT button on the Super Mini: blink button (both eyes).
constexpr gpio_num_t kBlinkPin = GPIO_NUM_9;
// Per-eye wink buttons, -1 = none. Free pins on the C3 Super Mini: 6, 7, 8.
constexpr int kEye1WinkPin = -1;
constexpr int kEye2WinkPin = -1;

// --- Iris size -------------------------------------------------------------
// The iris disc's outer edge sits at the polar box boundary (default_large:
// 180px box = 90px radius). kIrisEdgeTrimPx shrinks the visible iris disc
// by this many pixels per edge (radius); the freed ring shows sclera.
// Works for every eye style, scaling with the style's box size.
// 0 = asset geometry unchanged.
constexpr int kIrisEdgeTrimPx = 5;

// --- Behaviour -------------------------------------------------------------
constexpr bool kAutoBlink = true;       // blink autonomously at random intervals
constexpr bool kPupilTracking = true;   // upper eyelid follows the pupil
                                        // (lower lid is coupled inversely)
// Both eyes converge slightly (cross-eyed) like the original sketch.
constexpr int kEyeConvergeX = 4;  // pixel offset per eye
constexpr bool kPrintFps = true;

// --- Jaw servo (optional Halloween skull) --------------------------------
// Classic ledc PWM (50 Hz), no extra servo library required.
constexpr bool kJawServoEnabled = false;
constexpr gpio_num_t kJawServoPin = GPIO_NUM_5;
constexpr int kJawClosedAngle = 20;  // degrees
constexpr int kJawOpenAngle = 55;    // degrees
constexpr unsigned long kJawBiteMs = 500;
constexpr unsigned long kJawBites = 2;             // bites per animation
constexpr unsigned long kJawCooldownMs = 10000;    // pause between animations

}  // namespace config

// Number of eyes (1 for a single-display test setup, 2 for the skull).
#define EYE_COUNT 1

// Display rotation: 0 = 0 deg pins bottom, 2 = 180 deg pins top.
#define EYE_ROTATION 2

// X offset of the eye image on the display.
#define EYE_XPOSITION 0
