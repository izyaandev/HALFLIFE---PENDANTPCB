# firmware

Arduino-framework firmware for the XIAO ESP32-S3 Sense, built with PlatformIO.

| file | what it does |
|---|---|
| `src/main.cpp` | state machine: idle, recording, hangover, private, low battery. Pre-roll buffer, WAV chunks, bookmarks, uploader task |
| `src/config.h` | pin map (matches the carrier PCB) and all the tuning numbers |
| `src/vad.h` | voice detector with an adaptive noise floor. No Arduino code in it, so it is unit tested on a PC |
| `src/battery.h` | battery voltage and percent from the divider on D3 |
| `src/wav.h` | tiny WAV header writer |
| `src/secrets.example.h` | copy to `secrets.h` and add your Wi-Fi + server details |
| `test/test_vad.cpp` | host-side tests for the voice detector |

## build

```
cd firmware
cp src/secrets.example.h src/secrets.h     # then edit it
pio run -e xiao_esp32s3 -t upload
```

## test the voice detector (no hardware needed)

```
cd firmware/test
g++ -std=c++17 -Wall -I../src test_vad.cpp -o test_vad && ./test_vad
```

All 10 checks pass, including: a silent room never triggers, a full minute of continuous speech is never cut off,
and steady background noise stops triggering once the noise floor adapts.

## honest status

The detector logic is tested on a PC. The rest of the firmware is written against the real pin map but **has not been compiled
for the ESP32 or run on hardware yet** (no board exists yet). Expect to fix small things on first flash.
