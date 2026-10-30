// Eye animation logic (movement, blinking, iris scaling), ported from
// eye_functions.ino of dalori/ESP32-uncanny-eyes-halloween-skull, which
// adapts the Adafruit "Uncanny Eyes" sketch by Phil Burgess (MIT license).
//
// Not ported (yet): joystick control and light-sensor-driven iris
// (LIGHT_PIN) - the eyes move autonomously, like the original default config.

#include <Arduino.h>

#include "config.h"
#include "eyes/eye_assets.h"
#include "eyes/eye_config.h"
#include "eyes/eye_motion.h"
#include "eyes/eye_render.h"
#include "user/user_hooks.h"

namespace {

struct EyeBlink {
  BlinkState state = BlinkState::kNone;
  uint32_t duration = 0;
  uint32_t startTime = 0;
};

EyeBlink eyeBlink[EYE_COUNT];

uint32_t startMillis = 0;
uint32_t frames = 0;

// Ease in/out curve for eye movements 3*t^2-2*t^3
const uint8_t ease[256] = {
    0,   0,   0,   0,   0,   0,   0,   1,   1,   1,   1,   1,   2,   2,   2,   3,
    3,   3,   4,   4,   4,   5,   5,   6,   6,   7,   7,   8,   9,   9,   10,  10,
    11,  12,  12,  13,  14,  15,  15,  16,  17,  18,  18,  19,  20,  21,  22,  23,
    24,  25,  26,  27,  27,  28,  29,  30,  31,  33,  34,  35,  36,  37,  38,  39,
    40,  41,  42,  44,  45,  46,  47,  48,  50,  51,  52,  53,  54,  56,  57,  58,
    60,  61,  62,  63,  65,  66,  67,  69,  70,  72,  73,  74,  76,  77,  78,  80,
    81,  83,  84,  85,  87,  88,  90,  91,  93,  94,  96,  97,  98,  100, 101, 103,
    104, 106, 107, 109, 110, 112, 113, 115, 116, 118, 119, 121, 122, 124, 125, 127,
    128, 130, 131, 133, 134, 136, 137, 139, 140, 142, 143, 145, 146, 148, 149, 151,
    152, 154, 155, 157, 158, 159, 161, 162, 164, 165, 167, 168, 170, 171, 172, 174,
    175, 177, 178, 179, 181, 182, 183, 185, 186, 188, 189, 190, 192, 193, 194, 195,
    197, 198, 199, 201, 202, 203, 204, 205, 207, 208, 209, 210, 211, 213, 214, 215,
    216, 217, 218, 219, 220, 221, 222, 224, 225, 226, 227, 228, 228, 229, 230, 231,
    232, 233, 234, 235, 236, 237, 237, 238, 239, 240, 240, 241, 242, 243, 243, 244,
    245, 245, 246, 246, 247, 248, 248, 249, 249, 250, 250, 251, 251, 251, 252, 252,
    252, 253, 253, 253, 254, 254, 254, 254, 254, 255, 255, 255, 255, 255, 255, 255};

// Blink helpers ----------------------------------------------------------

bool blinkButtonPressed() {
  return digitalRead(static_cast<uint8_t>(config::kBlinkPin)) == LOW;
}

void startBlink(uint32_t t, uint32_t blinkDuration, uint8_t onlyEye = 0xFF) {
  for (uint8_t e = 0; e < EYE_COUNT; e++) {
    if (onlyEye != 0xFF && e != onlyEye) continue;
    if (eyeBlink[e].state == BlinkState::kNone) {
      eyeBlink[e].state = BlinkState::kClosing;
      eyeBlink[e].startTime = t;
      eyeBlink[e].duration = blinkDuration;
    }
  }
}

// Frame -------------------------------------------------------------------

// Process motion for a single frame of the left or right eye (one eye per
// call, cycling through the eyes).
void frame(uint16_t iScale) {  // Iris scale (0-1023)
  static uint8_t eyeIndex = 0;
  int16_t eyeX, eyeY;
  uint32_t t = micros();  // Time at start of function
  const eye_assets::EyeAssets& a = eye_assets::kAssets;

  if (startMillis == 0) startMillis = millis();
  if (config::kPrintFps && !(++frames & 255)) {  // Every 256 frames...
    float elapsed = (millis() - startMillis) / 1000.0;
    if (elapsed) {
      Serial.print("FPS=");
      Serial.println((uint16_t)(frames / elapsed));
    }
  }

  if (++eyeIndex >= EYE_COUNT) eyeIndex = 0;  // Cycle through eyes, 1 per call

  // Autonomous X/Y eye motion: periodically initiates motion to a new random
  // point, random speed, holds there for a random period until next motion.
  static bool eyeInMotion = false;
  static int16_t eyeOldX = 512, eyeOldY = 512, eyeNewX = 512, eyeNewY = 512;
  static uint32_t eyeMoveStartTime = 0L;
  static int32_t eyeMoveDuration = 0L;

  int32_t dt = t - eyeMoveStartTime;  // us elapsed since last eye event
  if (eyeInMotion) {                   // Currently moving?
    if (dt >= eyeMoveDuration) {       // Time up?  Destination reached.
      eyeInMotion = false;
      eyeMoveDuration = random(3000000);  // 0-3 sec stop
      eyeMoveStartTime = t;
      eyeX = eyeOldX = eyeNewX;
      eyeY = eyeOldY = eyeNewY;
    } else {  // Move time's not yet fully elapsed -- interpolate position
      int16_t e = ease[255 * dt / eyeMoveDuration] + 1;  // Ease curve
      eyeX = eyeOldX + (((eyeNewX - eyeOldX) * e) / 256);
      eyeY = eyeOldY + (((eyeNewY - eyeOldY) * e) / 256);
    }
  } else {  // Eye stopped
    eyeX = eyeOldX;
    eyeY = eyeOldY;
    if (dt > eyeMoveDuration) {  // Time up?  Begin new move.
      int16_t dx, dy;
      uint32_t d;
      do {  // Pick new dest in circle
        eyeNewX = random(1024);
        eyeNewY = random(1024);
        dx = (eyeNewX * 2) - 1023;
        dy = (eyeNewY * 2) - 1023;
      } while ((d = (dx * dx + dy * dy)) > (1023 * 1023));  // Keep trying
      eyeMoveDuration = random(72000, 144000);             // ~1/14 - ~1/7 sec
      eyeMoveStartTime = t;
      eyeInMotion = true;  // Start move on next frame
    }
  }

  // Blinking: similar to the autonomous eye movement above -- blink start
  // times and durations are random (within ranges).
  if (config::kAutoBlink) {
    static uint32_t timeOfLastBlink = 0L, timeToNextBlink = 0L;
    if ((t - timeOfLastBlink) >= timeToNextBlink) {  // Start new blink?
      timeOfLastBlink = t;
      uint32_t blinkDuration = random(36000, 72000);  // ~1/28 - ~1/14 sec
      startBlink(t, blinkDuration);
      timeToNextBlink = blinkDuration * 3 + random(4000000);
    }
  }

  if (eyeBlink[eyeIndex].state != BlinkState::kNone) {  // Eye currently blinking?
    // Check if current blink state time has elapsed
    if ((t - eyeBlink[eyeIndex].startTime) >= eyeBlink[eyeIndex].duration) {
      bool heldClosed =
          (eyeBlink[eyeIndex].state == BlinkState::kClosing) &&
          (blinkButtonPressed() ||
           (kEyeInfo[eyeIndex].wink >= 0 && digitalRead(kEyeInfo[eyeIndex].wink) == LOW));
      if (!heldClosed) {  // No buttons held, or other state...
        int newState = static_cast<int>(eyeBlink[eyeIndex].state) + 1;
        if (newState > static_cast<int>(BlinkState::kOpening)) {
          eyeBlink[eyeIndex].state = BlinkState::kNone;  // No longer blinking
        } else {  // Advancing from closing to opening mode
          eyeBlink[eyeIndex].state = BlinkState::kOpening;
          eyeBlink[eyeIndex].duration *= 2;  // Opening is 1/2 the closing speed
          eyeBlink[eyeIndex].startTime = t;
        }
      }
    }
  } else {  // Not currently blinking...check buttons!
    if (blinkButtonPressed()) {
      startBlink(t, (uint32_t)random(36000, 72000));
    } else if (kEyeInfo[eyeIndex].wink >= 0 && digitalRead(kEyeInfo[eyeIndex].wink) == LOW) {
      startBlink(t, (uint32_t)random(45000, 90000), eyeIndex);  // Wink!
    }
  }

  // Process motion, blinking and iris scale into renderable values

  // Scale eye X/Y positions (0-1023) to pixel units used by drawEye()
  eyeX = map(eyeX, 0, 1023, 0, a.scleraWidth - a.screenWidth);
  eyeY = map(eyeY, 0, 1023, 0, a.scleraHeight - a.screenHeight);

  // Horizontal position is offset so that eyes are very slightly crossed to
  // appear fixated (converged) at a conversational distance.
  if (EYE_COUNT > 1) {
    if (eyeIndex == 1) eyeX += config::kEyeConvergeX;
    else eyeX -= config::kEyeConvergeX;
  }
  if (eyeX > (a.scleraWidth - a.screenWidth)) eyeX = a.scleraWidth - a.screenWidth;

  // Eyelids are rendered using a brightness threshold image. The same map
  // makes the upper eyelid track the pupil (eyes tend to open only as much
  // as needed): a point in the upper lid map slightly above the pupil is
  // sampled to determine the rendering threshold. The lower lid is coupled
  // inversely (lT = 254 - uT) in the original algorithm - this also acts as
  // a safety mechanism: on styles with lid-map plateaus (e.g. dragonEye) the
  // upper threshold saturates high and the coupling keeps the lower lid open,
  // so the eye stays visible. Direct sampling of the lower lid would close
  // both lids on such styles (verified with scripts/analyze_lids.py).
  static uint8_t uThreshold = 128;
  uint8_t lThreshold, n;
  if (config::kPupilTracking) {
    int16_t sampleX = a.scleraWidth / 2 - (eyeX / 2);  // Reduce X influence
    if (sampleX >= a.screenWidth) sampleX = a.screenWidth - 1;
    if (sampleX < 0) sampleX = 0;
    int16_t sampleY = a.scleraHeight / 2 - (eyeY + a.irisHeight / 4);
    // Eyelid is slightly asymmetrical, so two readings are taken, averaged
    if (sampleY < 0) n = 0;
    else n = (pgm_read_byte(eye_assets::kAssets.upper + sampleY * a.screenWidth + sampleX) +
              pgm_read_byte(eye_assets::kAssets.upper + sampleY * a.screenWidth +
                            (a.screenWidth - 1 - sampleX))) /
             2;
    uThreshold = (uThreshold * 3 + n) / 4;  // Filter/soften motion
    // Lower eyelid doesn't track the same way, but seems to be pulled upward
    // by tension from the upper lid.
    lThreshold = 254 - uThreshold;
  } else {  // No tracking -- eyelids full open unless blink modifies them
    uThreshold = lThreshold = 0;
  }

  // The upper/lower thresholds are then scaled relative to the current blink
  // position so that blinks work together with pupil tracking.
  if (eyeBlink[eyeIndex].state != BlinkState::kNone) {  // Eye currently blinking?
    uint32_t s = (t - eyeBlink[eyeIndex].startTime);
    if (s >= eyeBlink[eyeIndex].duration) s = 255;  // At or past blink end
    else s = 255 * s / eyeBlink[eyeIndex].duration;  // Mid-blink
    s = (eyeBlink[eyeIndex].state == BlinkState::kOpening) ? 1 + s : 256 - s;
    n = (uThreshold * s + 254 * (257 - s)) / 256;
    lThreshold = (lThreshold * s + 254 * (257 - s)) / 256;
  } else {
    n = uThreshold;
  }

  // Pass all the derived values to the eye-rendering function:
  drawEye(eyeIndex, iScale, eyeX, eyeY, n, lThreshold);

  if (eyeIndex == (EYE_COUNT - 1)) {
    user_loop();  // Call user code after rendering last eye
  }
}

// AUTONOMOUS IRIS SCALING ---------------------------------------------------

// Subdivides motion path into two sub-paths w/randomization. Uses a fractal
// behavior to simulate both the major reaction of the eye plus the continuous
// smaller adjustments that occur.
void split(int16_t startValue, int16_t endValue, uint32_t startTime,
           int32_t duration, int16_t range) {
  const eye_assets::EyeAssets& a = eye_assets::kAssets;
  if (range >= 8) {  // Limit subdivision count, because recursion
    range /= 2;      // Split range & time in half for subdivision,
    duration /= 2;   // then pick random center point within range:
    int16_t midValue = (startValue + endValue - range) / 2 + random(range);
    uint32_t midTime = startTime + duration;
    split(startValue, midValue, startTime, duration, range);  // First half
    split(midValue, endValue, midTime, duration, range);       // Second half
  } else {            // No more subdivisions, do iris motion...
    int32_t dt;      // Time (micros) since start of motion
    int16_t v;       // Interim value
    while ((dt = (micros() - startTime)) < duration) {
      v = startValue + (((endValue - startValue) * dt) / duration);
      if (v < a.irisMin) v = a.irisMin;  // Clip just in case
      else if (v > a.irisMax) v = a.irisMax;
      frame(v);  // Draw frame w/interim iris scale value
    }
  }
}

}  // namespace

void initEyes() {
  pinMode(static_cast<uint8_t>(config::kBlinkPin), INPUT_PULLUP);  // Blink button
  for (uint8_t e = 0; e < EYE_COUNT; e++) {
    if (kEyeInfo[e].wink >= 0) pinMode(kEyeInfo[e].wink, INPUT_PULLUP);
  }
}

void updateEye() {
  static uint16_t oldIris = (eye_assets::kAssets.irisMin + eye_assets::kAssets.irisMax) / 2;
  uint16_t newIris = random(eye_assets::kAssets.irisMin, eye_assets::kAssets.irisMax);
  split(oldIris, newIris, micros(), 10000000L,
        eye_assets::kAssets.irisMax - eye_assets::kAssets.irisMin);
  oldIris = newIris;
}
