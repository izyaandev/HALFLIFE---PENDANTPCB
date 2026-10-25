#pragma once
// Half Life pendant: pin map + tuning. Pins match the carrier PCB (hardware/pcb).
// XIAO ESP32-S3 pin -> GPIO: D0=1 D1=2 D2=3 D3=4 D4=5 D5=6 D6=43 D8=7 D9=8 D10=9

// --- INMP441 mic (I2S) ---
#define PIN_I2S_BCLK    1    // D0  -> mic SCK
#define PIN_I2S_WS      2    // D1  -> mic WS
#define PIN_I2S_DIN     3    // D2  -> mic SD

// --- carrier board io ---
#define PIN_VBAT_SENSE  4    // D3  <- battery through a 2 x 200k divider
#define PIN_BOOKMARK    5    // D4  <- button to GND (internal pullup)
#define PIN_PRIV_SENSE  6    // D5  <- mic power rail (HIGH = privacy switch ON, mic powered)
#define PIN_REC_LED     43   // D6  -> 220R -> red LED

// --- microSD on the Sense expansion board ---
#define PIN_SD_CS       21

// --- audio ---
#define SAMPLE_RATE     16000
#define FRAME_SAMPLES   512          // 32 ms per frame
#define MIC_SHIFT       14           // 32 bit I2S word -> 16 bit sample (smaller = louder)
#define PREROLL_MS      1500         // audio kept from just before speech starts
#define HANGOVER_MS     2500         // keep recording after speech stops
#define CHUNK_SECONDS   60           // one WAV file per minute at most

// --- voice detector ---
#define VAD_MIN_RMS     250          // never trigger below this, even in a silent room
#define VAD_NOISE_RATIO 3.0f         // speech = this many times the noise floor
#define VAD_FLOOR_RISE  0.0007f      // how fast the noise floor creeps up per 32 ms frame

// --- battery ---
#define VBAT_DIVIDER    2.0f         // 200k / 200k
#define LOW_BATTERY_V   3.45f        // stop recording below this to protect the cell

// --- upload ---
#define UPLOAD_PERIOD_MS 15000
// WIFI_SSID, WIFI_PASS, API_URL, API_TOKEN, DEVICE_ID live in secrets.h (not committed)
#include "secrets.h"
