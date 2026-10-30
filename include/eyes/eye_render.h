#pragma once

#include <cstdint>

// Renders one eye to display index e. All inputs must be pre-clipped and
// valid (see eye_motion.cpp for the callers).
void drawEye(uint8_t e, uint32_t iScale, uint32_t scleraX, uint32_t scleraY,
             uint32_t uT, uint32_t lT);
