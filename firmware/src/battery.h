#pragma once
// Battery level from the divider on D3. LiPo voltage -> percent uses a rough lookup curve.
#include <Arduino.h>
#include "config.h"

inline float readBatteryVolts() {
  uint32_t mv = 0;
  for (int i = 0; i < 8; i++) mv += analogReadMilliVolts(PIN_VBAT_SENSE);   // average out ADC noise
  return (mv / 8.0f) * VBAT_DIVIDER / 1000.0f;
}

inline int batteryPercent(float v) {
  static const float volts[] = {3.30f, 3.60f, 3.70f, 3.80f, 3.90f, 4.00f, 4.10f, 4.20f};
  static const int pct[]     = {0,     10,    25,    45,    60,    75,    90,    100};
  if (v <= volts[0]) return 0;
  for (int i = 1; i < 8; i++) {
    if (v <= volts[i]) return pct[i - 1] + (int)((v - volts[i - 1]) / (volts[i] - volts[i - 1]) * (pct[i] - pct[i - 1]));
  }
  return 100;
}
