#pragma once
// Energy based voice activity detector with an adaptive noise floor.
// Header-only and free of Arduino dependencies so it can be unit tested on a PC.
//
// How the noise floor works (a simple "minimum statistics" tracker):
//   * if a frame is quieter than the floor, the floor drops to it right away (pauses between words reset it)
//   * if a frame is louder, the floor creeps up very slowly, so steady background noise (fan, traffic)
//     eventually stops counting as speech, but a normal sentence does not drag the floor up
//   * seed() sets the starting floor from a few frames of room noise at boot
//
// This is the v1 detector. A model based one (Silero / WebRTC VAD) can replace it later without
// touching the rest of the firmware: only update() has to keep its signature.
#include <cmath>
#include <cstddef>
#include <cstdint>

class EnergyVad {
 public:
  // minRms: never trigger below this. noiseRatio: speech must be this many times the floor.
  // floorRise: how fast the floor creeps up per frame while it is louder than the floor.
  EnergyVad(float minRms, float noiseRatio, float floorRise)
      : minRms_(minRms), ratio_(noiseRatio), rise_(floorRise), floor_(minRms / noiseRatio) {}

  static float rms(const int16_t* s, size_t n) {
    if (n == 0) return 0.0f;
    double acc = 0.0;
    for (size_t i = 0; i < n; i++) acc += (double)s[i] * (double)s[i];
    return (float)std::sqrt(acc / (double)n);
  }

  void seed(float roomLevel) { floor_ = std::fmax(1.0f, roomLevel); }

  // returns true if this frame contains speech
  bool update(const int16_t* samples, size_t n) {
    float level = rms(samples, n);
    last_ = level;
    if (level < floor_) floor_ = std::fmax(1.0f, floor_ + 0.3f * (level - floor_));   // quieter: follow it down
    else floor_ *= (1.0f + rise_);                                                    // louder: creep up slowly
    float threshold = std::fmax(minRms_, floor_ * ratio_);
    return level > threshold;
  }

  float floorLevel() const { return floor_; }
  float lastLevel() const { return last_; }

 private:
  float minRms_, ratio_, rise_, floor_, last_ = 0.0f;
};
