// Half Life pendant firmware v0.1  (XIAO ESP32-S3 Sense on the carrier PCB)
//
// What it does
//   * listens on an INMP441 I2S mic, but only records when someone is talking (voice detection)
//   * keeps 1.5 s of audio from BEFORE speech starts, so the first word is never cut off
//   * writes 16 kHz WAV chunks to the microSD, uploads them when Wi-Fi is up, then deletes them
//   * hardware privacy switch cuts mic power; firmware reads the mic rail on D5 and shows it
//   * bookmark button marks the moment inside the current recording
//   * red LED is on only while recording, so people nearby can see it
//
// Status: written for the real pin map but NOT yet run on hardware (see README).
#include <Arduino.h>
#include <HTTPClient.h>
#include <Preferences.h>
#include <SD.h>
#include <SPI.h>
#include <WiFi.h>
#include <driver/i2s.h>

#include "battery.h"
#include "config.h"
#include "vad.h"
#include "wav.h"

enum class State { Idle, Recording, Hangover, Private, LowBattery };

static const i2s_port_t I2S_PORT = I2S_NUM_0;
static const size_t PREROLL_SAMPLES = (size_t)SAMPLE_RATE * PREROLL_MS / 1000;

static EnergyVad vad(VAD_MIN_RMS, VAD_NOISE_RATIO, VAD_FLOOR_RISE);
static SemaphoreHandle_t sdLock;            // SD card is shared by the audio loop and the uploader task
static int16_t* preroll = nullptr;          // ring buffer in PSRAM
static size_t prerollHead = 0;
static State state = State::Idle;
static File wav;
static char wavPath[40], bmPath[40];
static uint32_t wavBytes = 0, chunkStartMs = 0, lastVoiceMs = 0, bootCount = 0, seq = 0;
static bool lastButton = HIGH;

// ---------------------------------------------------------------- helpers
static bool micPowered() {
  // the slide switch feeds the mic and this pin. HIGH = switch ON. A 100k pulldown makes it read LOW when off.
  return digitalRead(PIN_PRIV_SENSE) == HIGH;
}

static void setState(State s) {
  if (s == state) return;
  state = s;
  static const char* names[] = {"IDLE", "RECORDING", "HANGOVER", "PRIVATE", "LOW BATTERY"};
  Serial.printf("[state] %s\n", names[(int)s]);
}

static void i2sStart() {
  i2s_config_t cfg = {};
  cfg.mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX);
  cfg.sample_rate = SAMPLE_RATE;
  cfg.bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT;      // INMP441 sends 24 bit data in a 32 bit slot
  cfg.channel_format = I2S_CHANNEL_FMT_ONLY_LEFT;       // L/R pin on the mic is tied to GND
  cfg.communication_format = I2S_COMM_FORMAT_STAND_I2S;
  cfg.intr_alloc_flags = ESP_INTR_FLAG_LEVEL1;
  cfg.dma_buf_count = 8;
  cfg.dma_buf_len = FRAME_SAMPLES;
  i2s_pin_config_t pins = {};
  pins.mck_io_num = I2S_PIN_NO_CHANGE;
  pins.bck_io_num = PIN_I2S_BCLK;
  pins.ws_io_num = PIN_I2S_WS;
  pins.data_out_num = I2S_PIN_NO_CHANGE;
  pins.data_in_num = PIN_I2S_DIN;
  i2s_driver_install(I2S_PORT, &cfg, 0, nullptr);
  i2s_set_pin(I2S_PORT, &pins);
}

static size_t readFrame(int16_t* out) {
  static int32_t raw[FRAME_SAMPLES];
  size_t bytes = 0;
  i2s_read(I2S_PORT, raw, sizeof(raw), &bytes, 100 / portTICK_PERIOD_MS);
  size_t n = bytes / sizeof(int32_t);
  for (size_t i = 0; i < n; i++) {
    int32_t s = raw[i] >> MIC_SHIFT;
    out[i] = (int16_t)constrain(s, -32768, 32767);
  }
  return n;
}

// ---------------------------------------------------------------- recording
static void openChunk() {
  snprintf(wavPath, sizeof(wavPath), "/rec/b%lu_%05lu.wav", (unsigned long)bootCount, (unsigned long)seq);
  snprintf(bmPath, sizeof(bmPath), "/rec/b%lu_%05lu.bm", (unsigned long)bootCount, (unsigned long)seq);
  seq++;
  xSemaphoreTake(sdLock, portMAX_DELAY);
  wav = SD.open(wavPath, FILE_WRITE);
  uint8_t blank[44] = {0};
  wav.write(blank, sizeof(blank));                      // real header is written when the chunk closes
  xSemaphoreGive(sdLock);
  wavBytes = 0;
  chunkStartMs = millis();
  Serial.printf("[rec] open %s\n", wavPath);
}

static void writeSamples(const int16_t* s, size_t n) {
  xSemaphoreTake(sdLock, portMAX_DELAY);
  wav.write((const uint8_t*)s, n * sizeof(int16_t));
  xSemaphoreGive(sdLock);
  wavBytes += n * sizeof(int16_t);
}

static void closeChunk() {
  if (!wav) return;
  xSemaphoreTake(sdLock, portMAX_DELAY);
  wavWriteHeader(wav, wavBytes);
  wav.close();
  xSemaphoreGive(sdLock);
  Serial.printf("[rec] closed %s (%.1f s)\n", wavPath, wavBytes / (2.0f * SAMPLE_RATE));
}

static void handleBookmark() {
  bool b = digitalRead(PIN_BOOKMARK);
  if (lastButton == HIGH && b == LOW && (state == State::Recording || state == State::Hangover)) {
    float at = (millis() - chunkStartMs) / 1000.0f;
    xSemaphoreTake(sdLock, portMAX_DELAY);
    File f = SD.open(bmPath, FILE_APPEND);
    if (f) { f.printf("%.1f\n", at); f.close(); }
    xSemaphoreGive(sdLock);
    Serial.printf("[bookmark] %.1f s\n", at);
  }
  lastButton = b;
}

// ---------------------------------------------------------------- uploader (runs on core 0)
static String readBookmarks(const String& wavName) {
  String bm = wavName.substring(0, wavName.length() - 4) + ".bm";
  String out;
  if (SD.exists(bm)) {
    File f = SD.open(bm);
    while (f.available()) { String l = f.readStringUntil('\n'); l.trim(); if (l.length()) out += (out.length() ? "," : "") + l; }
    f.close();
  }
  return out;
}

static void uploadOne(const String& path) {
  xSemaphoreTake(sdLock, portMAX_DELAY);
  File f = SD.open(path);
  String bookmarks = readBookmarks(path);
  size_t size = f ? f.size() : 0;
  xSemaphoreGive(sdLock);
  if (!f || size < 1000) { return; }
  HTTPClient http;
  http.begin(API_URL);
  http.addHeader("Authorization", String("Bearer ") + API_TOKEN);
  http.addHeader("Content-Type", "audio/wav");
  http.addHeader("X-Device-Id", DEVICE_ID);
  http.addHeader("X-Bookmarks", bookmarks);
  int code = http.sendRequest("POST", &f, size);
  http.end();
  xSemaphoreTake(sdLock, portMAX_DELAY);
  f.close();
  if (code == 200) {                                    // delete from the card only after the server confirms
    SD.remove(path);
    SD.remove(path.substring(0, path.length() - 4) + ".bm");
    Serial.printf("[upload] ok, removed %s\n", path.c_str());
  } else {
    Serial.printf("[upload] %s failed (%d), will retry\n", path.c_str(), code);
  }
  xSemaphoreGive(sdLock);
}

static void uploaderTask(void*) {
  for (;;) {
    vTaskDelay(UPLOAD_PERIOD_MS / portTICK_PERIOD_MS);
    if (WiFi.status() != WL_CONNECTED) { WiFi.reconnect(); continue; }
    xSemaphoreTake(sdLock, portMAX_DELAY);
    File dir = SD.open("/rec");
    String next;
    for (File f = dir.openNextFile(); f; f = dir.openNextFile()) {
      String n = String("/rec/") + f.name();
      if (n.endsWith(".wav") && n != String(wavPath)) { next = n; f.close(); break; }   // never touch the file being recorded
    }
    dir.close();
    xSemaphoreGive(sdLock);
    if (next.length()) uploadOne(next);
  }
}

// ---------------------------------------------------------------- arduino entry points
void setup() {
  Serial.begin(115200);
  pinMode(PIN_REC_LED, OUTPUT);
  pinMode(PIN_BOOKMARK, INPUT_PULLUP);
  pinMode(PIN_PRIV_SENSE, INPUT);
  analogReadResolution(12);

  Preferences prefs;
  prefs.begin("pendant", false);
  bootCount = prefs.getUInt("boot", 0) + 1;
  prefs.putUInt("boot", bootCount);
  prefs.end();

  sdLock = xSemaphoreCreateMutex();
  preroll = (int16_t*)ps_malloc(PREROLL_SAMPLES * sizeof(int16_t));
  if (!preroll || !SD.begin(PIN_SD_CS)) {
    Serial.println("[fatal] need PSRAM and a microSD card");
    while (true) { digitalWrite(PIN_REC_LED, !digitalRead(PIN_REC_LED)); delay(150); }   // fast blink = hardware problem
  }
  SD.mkdir("/rec");
  i2sStart();
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  // learn the room noise for ~1 s before listening for speech (only if the mic is powered)
  if (micPowered()) {
    static int16_t calib[FRAME_SAMPLES];
    float sum = 0; int frames = 0;
    for (int i = 0; i < 30; i++) { size_t n = readFrame(calib); if (n) { sum += EnergyVad::rms(calib, n); frames++; } }
    if (frames) vad.seed(sum / frames);
  }
  xTaskCreatePinnedToCore(uploaderTask, "uploader", 8192, nullptr, 1, nullptr, 0);
  Serial.printf("[boot] pendant ready, battery %.2f V (%d%%)\n", readBatteryVolts(), batteryPercent(readBatteryVolts()));
}

void loop() {
  static int16_t frame[FRAME_SAMPLES];
  static uint32_t lastBatCheck = 0;
  uint32_t now = millis();

  if (now - lastBatCheck > 10000) {                      // check the battery every 10 s
    lastBatCheck = now;
    if (readBatteryVolts() < LOW_BATTERY_V) {
      if (wav) closeChunk();
      setState(State::LowBattery);
    }
  }
  if (state == State::LowBattery) { digitalWrite(PIN_REC_LED, LOW); delay(1000); return; }

  if (!micPowered()) {                                   // privacy switch OFF: no recording is possible
    if (wav) closeChunk();
    wav = File();
    setState(State::Private);
    digitalWrite(PIN_REC_LED, LOW);
    delay(100);
    return;
  }
  if (state == State::Private) setState(State::Idle);

  size_t n = readFrame(frame);
  if (n == 0) return;
  bool speech = vad.update(frame, n);
  if (speech) lastVoiceMs = now;

  if (state == State::Idle) {
    if (speech) {                                        // start: write the pre-roll first so the first word is kept
      openChunk();
      for (size_t i = 0; i < PREROLL_SAMPLES; i++) {
        int16_t s = preroll[(prerollHead + i) % PREROLL_SAMPLES];
        writeSamples(&s, 1);
      }
      setState(State::Recording);
    } else {
      for (size_t i = 0; i < n; i++) {                   // keep rolling the pre-roll buffer while idle
        preroll[prerollHead] = frame[i];
        prerollHead = (prerollHead + 1) % PREROLL_SAMPLES;
      }
    }
  }
  if (state == State::Recording || state == State::Hangover) {
    writeSamples(frame, n);
    if (speech) setState(State::Recording);
    else if (state == State::Recording) setState(State::Hangover);
    if (state == State::Hangover && now - lastVoiceMs > HANGOVER_MS) { closeChunk(); wav = File(); setState(State::Idle); }
    else if (now - chunkStartMs > CHUNK_SECONDS * 1000UL) { closeChunk(); openChunk(); }
    handleBookmark();
  }
  digitalWrite(PIN_REC_LED, (state == State::Recording || state == State::Hangover) ? HIGH : LOW);
}
