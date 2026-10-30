#pragma once

#define LGFX_USE_V1
#include <LovyanGFX.hpp>

#include "config.h"

// LovyanGFX device: GC9A01 on SPI. Pin values come from config.h.
//
// Chip select is deliberately NOT configured on the panel (-1): both
// displays hang on the same bus and LovyanGFX 1.2.x has no multi-panel
// support. The eye code toggles the CS pins manually (see eyes/eye_config.h
// and src/hardware/display.cpp), exactly like the original TFT_eSPI sketch.
class LGFX : public lgfx::LGFX_Device {
  lgfx::Bus_SPI _bus;
  lgfx::Panel_GC9A01 _panel;

public:
  LGFX() {
    {
      auto cfg = _bus.config();
      cfg.spi_host = SPI2_HOST;
      cfg.freq_write = config::kDisplaySpiWriteHz;
      cfg.pin_sclk = static_cast<int>(config::kDisplayPinSclk);
      cfg.pin_mosi = static_cast<int>(config::kDisplayPinMosi);
      cfg.pin_miso = -1;
      cfg.pin_dc = static_cast<int>(config::kDisplayPinDc);
      _bus.config(cfg);
      _panel.setBus(&_bus);
    }
    {
      auto cfg = _panel.config();
      cfg.pin_cs = -1;  // CS is toggled manually per eye
      cfg.pin_rst = static_cast<int>(config::kDisplayPinRst);
      cfg.invert = config::kDisplayInvert;
      cfg.rgb_order = config::kDisplayRgbOrder;
      _panel.config(cfg);
    }
    setPanel(&_panel);
  }
};
