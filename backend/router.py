"""AI router: cheap model for easy jobs, strong model for hard ones, fallback if a provider is down.

The real model calls are stubs on purpose. Plug a provider into call_model() when you pick one.
"""
from typing import Callable

SHORT_TRANSCRIPT_WORDS = 1500          # at or above this a summary goes to the strong model

MODELS = {
    "fast": "small-cheap-model",
    "strong": "big-smart-model",
}
FALLBACK_ORDER = {"fast": ["fast", "strong"], "strong": ["strong", "fast"]}


def pick_tier(task: str, transcript: str) -> str:
    """tags/titles are always easy. summaries and action items depend on length."""
    if task in ("tag", "title"):
        return "fast"
    words = len(transcript.split())
    return "fast" if words < SHORT_TRANSCRIPT_WORDS else "strong"


def call_model(tier: str, prompt: str) -> str:
    # TODO: replace with a real provider call (OpenRouter, Anthropic, ...)
    return f"[{MODELS[tier]}] mock answer"


def run(task: str, transcript: str, prompt: str,
        caller: Callable[[str, str], str] = call_model) -> tuple[str, str]:
    """returns (answer, model_name). tries the preferred tier first, then the other one."""
    tier = pick_tier(task, transcript)
    last_error = None
    for t in FALLBACK_ORDER[tier]:
        try:
            return caller(t, prompt), MODELS[t]
        except Exception as e:      # provider down, rate limited, ...
            last_error = e
    raise RuntimeError(f"all model tiers failed: {last_error}")
