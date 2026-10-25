#pragma once
// Minimal 16 bit mono PCM WAV writer for Arduino File objects.
#include <FS.h>
#include "config.h"

inline void wavWriteHeader(File& f, uint32_t dataBytes) {
  const uint32_t sampleRate = SAMPLE_RATE, byteRate = SAMPLE_RATE * 2, riffSize = 36 + dataBytes, fmtSize = 16;
  const uint16_t pcm = 1, channels = 1, blockAlign = 2, bits = 16;
  f.seek(0);
  f.write((const uint8_t*)"RIFF", 4);  f.write((const uint8_t*)&riffSize, 4);
  f.write((const uint8_t*)"WAVEfmt ", 8);  f.write((const uint8_t*)&fmtSize, 4);
  f.write((const uint8_t*)&pcm, 2);  f.write((const uint8_t*)&channels, 2);
  f.write((const uint8_t*)&sampleRate, 4);  f.write((const uint8_t*)&byteRate, 4);
  f.write((const uint8_t*)&blockAlign, 2);  f.write((const uint8_t*)&bits, 2);
  f.write((const uint8_t*)"data", 4);  f.write((const uint8_t*)&dataBytes, 4);
}
