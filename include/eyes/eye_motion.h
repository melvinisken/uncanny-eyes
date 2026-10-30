#pragma once

// Sets up blink/wink button pins (chip selects are set up by displayInit()).
void initEyes();

// Autonomous iris scaling - drives frame() continuously and is effectively
// the main loop of the eye animation.
void updateEye();
