import router


def transcribe(audio_bytes: bytes) -> str:
    # TODO: Whisper / Deepgram. Mock transcript so the rest of the pipeline can be tested.
    return "mock transcript of a conversation about the budget and next week's deadline"


def process(audio_bytes: bytes, bookmarks: list[float] | None = None) -> dict:
    transcript = transcribe(audio_bytes)
    summary, model = router.run("summary", transcript, f"Summarize this conversation:\n{transcript}")
    actions, _ = router.run("actions", transcript, f"List the action items:\n{transcript}")
    tags, _ = router.run("tag", transcript, f"Give 3 short tags:\n{transcript}")
    return {
        "transcript": transcript,
        "summary": summary,
        "action_items": actions,
        "tags": tags,
        "model_used": model,
        "bookmarks": bookmarks or [],
        "duration_s": max(0.0, (len(audio_bytes) - 44) / (16000 * 2)),   # 16 kHz 16 bit mono WAV
    }
