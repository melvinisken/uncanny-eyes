#pragma once

#include <cstdint>

#include "config.h"

// Blink state machine (one state per eye).
enum class BlinkState : uint8_t { kNone, kClosing, kOpening };

// One line per eye: chip select pin, wink button pin, rotation and
// x offset of the eye image on the display.
struct EyeInfo {
  int8_t cs;
  int8_t wink;
  uint8_t rotation;
  int16_t xposition;
};

#if EYE_COUNT == 2
constexpr EyeInfo kEyeInfo[EYE_COUNT] = {
    {static_cast<int8_t>(config::kEye1PinCs), static_cast<int8_t>(config::kEye1WinkPin), EYE_ROTATION, EYE_XPOSITION},
    {static_cast<int8_t>(config::kEye2PinCs), static_cast<int8_t>(config::kEye2WinkPin), EYE_ROTATION, EYE_XPOSITION},
};
#else
constexpr EyeInfo kEyeInfo[EYE_COUNT] = {
    {static_cast<int8_t>(config::kEye1PinCs), static_cast<int8_t>(config::kEye1WinkPin), EYE_ROTATION, EYE_XPOSITION},
};
#endif
