// Host-side test for the voice detector. Build + run without any hardware:
//   g++ -std=c++17 -I../src test_vad.cpp -o test_vad && ./test_vad
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <vector>
#include "vad.h"

static std::vector<int16_t> tone(float amp, int n, float hz = 220, int sr = 16000) {
  std::vector<int16_t> v(n);
  for (int i = 0; i < n; i++) v[i] = (int16_t)(amp * std::sin(2 * M_PI * hz * i / sr));
  return v;
}
static std::vector<int16_t> noise(float amp, int n) {
  std::vector<int16_t> v(n);
  for (int i = 0; i < n; i++) v[i] = (int16_t)(amp * ((rand() / (float)RAND_MAX) * 2 - 1));
  return v;
}
static int fails = 0;
#define CHECK(cond, msg) do { if (!(cond)) { printf("FAIL: %s\n", msg); fails++; } else printf("ok:   %s\n", msg); } while (0)

int main() {
  const int N = 512;
  auto talk = tone(6000, N);                 // rms about 4200
  auto quiet = noise(40, N);

  { EnergyVad vad(250, 3.0f, 0.0007f);
    bool any = false;
    for (int i = 0; i < 200; i++) any |= vad.update(quiet.data(), N);
    CHECK(!any, "silent room is never speech");
    CHECK(vad.update(talk.data(), N), "loud voice-like tone is speech");
    CHECK(!vad.update(quiet.data(), N), "back to quiet is not speech"); }

  { EnergyVad vad(250, 3.0f, 0.0007f);       // noisy room, floor seeded at boot from ~1 s of room noise
    auto hum = noise(900, N);                // rms about 520
    float lvl = EnergyVad::rms(hum.data(), N);
    vad.seed(lvl);
    int trig = 0;
    for (int i = 0; i < 300; i++) trig += vad.update(hum.data(), N);
    CHECK(trig == 0, "seeded floor: steady background noise does not trigger");
    CHECK(vad.update(talk.data(), N), "seeded floor: speech over background noise still triggers"); }

  { EnergyVad vad(250, 3.0f, 0.0007f);       // never seeded: cold start in a noisy room
    auto hum = noise(900, N);
    int early = 0, late = 0;
    for (int i = 0; i < 4000; i++) { bool s = vad.update(hum.data(), N); if (i < 100) early += s; if (i >= 3900) late += s; }
    CHECK(early > 0, "cold start in a noisy room triggers at first (why we seed at boot)");
    CHECK(late == 0, "floor adapts and steady noise stops triggering after about a minute"); }

  { EnergyVad vad(250, 3.0f, 0.0007f);       // sustained talking must not raise the floor enough to cut the speaker off
    vad.seed(60);
    int missed = 0;
    for (int i = 0; i < 1900; i++) missed += vad.update(talk.data(), N) ? 0 : 1;   // about 60 s of continuous loud speech
    CHECK(missed == 0, "a full minute of continuous speech is never cut off"); }

  { EnergyVad vad(250, 3.0f, 0.0007f);
    vad.seed(800);
    for (int i = 0; i < 30; i++) vad.update(quiet.data(), N);
    CHECK(vad.floorLevel() < 100, "floor drops quickly when the room gets quiet"); }

  CHECK(EnergyVad::rms(nullptr, 0) == 0.0f, "rms of nothing is zero");
  printf("%s\n", fails ? "SOME TESTS FAILED" : "all vad tests passed");
  return fails;
}
