# Design notes

## Session 1 (5.5 hours): the first half of the design
Decided: microcontroller (XIAO ESP32-S3 Sense), microphone (INMP441 over I2S), the hardware privacy switch, voice detection with
pre-roll and hangover, microSD buffering, upload then delete-on-confirm, the database and the AI pipeline with a router.

## Privacy
- the slide switch cuts the mic supply, so firmware cannot override it
- the mic rail is also read on D5 (with a 100k pulldown) so the firmware knows the switch state
- the LED is on only while recording
- delete-everything must always be one tap

## Voice detection
Idle, listen, start on speech, include 1.5 s pre-roll, stop after 2.5 s of silence. The v1 detector is energy based with an adaptive
noise floor (drops instantly, rises slowly, seeded at boot). It is unit tested. A model-based detector (Silero or WebRTC VAD) can replace it later.

## Storage
60 s WAV chunks on the microSD; upload in the background; delete from the card only after the server returns 200.
Cloud side planned as Supabase (Postgres, file storage) with pgvector for semantic search.

## AI
audio, transcript, router, summary / action items / tags, database. The router sends tags and titles (and summaries under 1,500 words)
to a fast cheap model, longer ones to a strong model, and falls back to the other tier if a provider fails.

## Open questions
- real transcription provider (hosted Whisper vs Deepgram for speaker labels)
- how to slim the enclosure (low-profile sockets, or solder the XIAO directly)
- bare MEMS microphone on the board instead of the breakout module
- encryption at rest and auto-delete policy
