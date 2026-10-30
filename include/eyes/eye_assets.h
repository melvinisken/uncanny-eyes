#pragma once

#include <cstdint>

// Eye asset tables for the selected style. The data itself is compiled in
// exactly one translation unit (src/eyes/eye_assets.cpp), which includes the
// style header from data/eyes/ (include path set in platformio.ini). This
// keeps the ~580 KB tables out of every other file and gives them external
// linkage here.
namespace eye_assets {

struct EyeAssets {
  // 16-bit RGB565 images
  const uint16_t* sclera;
  const uint16_t* iris;
  const uint16_t* polar;
  // 8-bit eyelid masks (row stride = screenWidth)
  const uint8_t* upper;
  const uint8_t* lower;

  int16_t scleraWidth, scleraHeight;
  int16_t irisWidth, irisHeight;    // polar map dimensions
  int16_t irisMapWidth, irisMapHeight;
  int16_t screenWidth, screenHeight;

  // Autonomous iris scale range defined by the asset (0-1023 scale).
  int16_t irisMin, irisMax;
};

extern const EyeAssets kAssets;

}  // namespace eye_assets
