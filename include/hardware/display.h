#pragma once

#include "hardware/lgfx_config.hpp"

extern LGFX tft;

// Asserts all eye chip selects, initialises the shared bus/panel and
// configures rotation on each display individually.
void displayInit();
