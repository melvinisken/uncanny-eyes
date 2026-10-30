#pragma once

// User hooks, called by the eye animation:
//   user_setup() - once after the displays are initialised
//   user_loop()  - after the last eye of a frame was rendered
void user_setup();
void user_loop();
