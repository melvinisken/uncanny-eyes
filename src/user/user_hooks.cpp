// Optional jaw servo for the Halloween skull, ported from user_skull-jaw.cpp
// of the original project. Uses the ESP32 ledc PWM (50 Hz) directly, so no
// extra servo library is needed. Enable with config::kJawServoEnabled.

#include <Arduino.h>

#include "config.h"
#include "user/user_hooks.h"

#if defined(CONFIG_IDF_TARGET_ESP32C3) || defined(CONFIG_IDF_TARGET_ESP32) || \
    defined(ESP_PLATFORM)
#include "esp32-hal-ledc.h"
#endif

namespace {

constexpr int kLedcChannel = 0;
constexpr int kLedcResolutionBits = 16;  // duty 0-65535

// Convert a servo angle (0-180 deg) to a duty cycle for a 50 Hz / 16-bit
// LEDC channel (pulse 1-2 ms within the 20 ms period).
uint32_t servoDuty(int angle) {
  constexpr uint32_t kPeriodUs = 20000;
  constexpr uint32_t kMinPulseUs = 500;
  constexpr uint32_t kMaxPulseUs = 2500;
  uint32_t pulseUs =
      kMinPulseUs + (uint32_t)angle * (kMaxPulseUs - kMinPulseUs) / 180;
  return pulseUs * 65535UL / kPeriodUs;
}

void servoWrite(int angle) {
  ledcWrite(kLedcChannel, servoDuty(angle));
}

struct JawState {
  bool isAnimating = false;
  unsigned long animationStartTime = 0;
  unsigned long cooldownTime = 0;
};

JawState jaw;

}  // namespace

void user_setup() {
  if (!config::kJawServoEnabled) return;
  ledcSetup(kLedcChannel, 50, kLedcResolutionBits);
  ledcAttachPin(static_cast<uint8_t>(config::kJawServoPin), kLedcChannel);
  servoWrite(config::kJawClosedAngle);
}

void user_loop() {
  if (!config::kJawServoEnabled) return;

  const unsigned long biteTotal = config::kJawBiteMs * config::kJawBites;

  if (jaw.isAnimating) {
    unsigned long elapsed = millis() - jaw.animationStartTime;
    if (elapsed >= biteTotal) {
      jaw.isAnimating = false;
      servoWrite(config::kJawClosedAngle);
      jaw.cooldownTime = millis();
    } else {
      elapsed %= config::kJawBiteMs;  // time within current bite cycle
      int angle = config::kJawClosedAngle +
                  (int)(elapsed * (config::kJawOpenAngle - config::kJawClosedAngle) /
                        config::kJawBiteMs);
      servoWrite(angle);
    }
  } else {
    unsigned long elapsed = millis() - jaw.cooldownTime;
    if (elapsed >= config::kJawCooldownMs) {
      jaw.animationStartTime = millis();
      jaw.isAnimating = true;
    }
  }
}
