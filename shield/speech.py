"""Speech input -- lets DhvaniShield check a voice note, not just typed text.

shield.access serves users who can't read a text verdict. This module is
the mirror case: a caller who can only speak, or a frightened relative
forwarding a WhatsApp voice note instead of a transcript. Transcription
runs locally via faster-whisper (no API, no keys) -- same
process-and-delete contract as the rest of the system: the audio file is
read once and never persisted or logged.

Design principle carried over from the rest of the engine, and the reason
this is its own module rather than a two-line wrapper: a recording that
fails to transcribe cleanly is NOT evidence of safety. Silence, noise, a
bad connection, or an unsupported format must never quietly become
NO_PATTERN (a false "looks fine") -- it becomes UNCERTAIN with an honest,
specific reason, consistent with the asymmetric-trust gate everywhere
else in this system.

NOTE on language: "tiny"/"base" Whisper handles Hindi/Marathi but with
lower accuracy than English. AI4Bharat's IndicConformer is the intended
higher-accuracy swap for hi/mr specifically -- the model-loading seam
below (`_load_model` / `_model_override`) is exactly where that swap
plugs in later; not built here because it needs its own eval, not because
the interface isn't ready for it.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable, Optional

from shield.engine import assess, Verdict
from shield.meter import meter
from shield.access import accessible_bundle

# Smallest CPU-friendly multilingual Whisper checkpoint -- no GPU needed,
# downloads once (~75 MB) on first use, then fully offline.
DEFAULT_MODEL_SIZE = "tiny"
MIN_CONFIDENT_CHARS = 3  # below this, treat transcription as failed, not empty-but-fine

_model_cache: dict = {}


class TranscriptionError(Exception):
    """Raised for a problem we can name. assess_audio() catches this and
    turns it into an honest UNCERTAIN verdict rather than a crash or a
    silent false-safe result."""


def _load_model(model_size: str = DEFAULT_MODEL_SIZE):
    """Lazy-load and cache the faster-whisper model. Imported inside the
    function (not at module top) so importing shield.speech doesn't
    require the faster-whisper package unless speech features are
    actually invoked -- text-only deployments stay dependency-free."""
    if model_size in _model_cache:
        return _model_cache[model_size]
    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        raise TranscriptionError(
            "faster-whisper is not installed. Run: "
            "pip install faster-whisper") from e
    try:
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
    except Exception as e:
        raise TranscriptionError(
            f"Could not load the Whisper '{model_size}' model "
            f"({type(e).__name__}: {e}). First run needs network access "
            "to download model weights once; after that it is fully "
            "local and offline.") from e
    _model_cache[model_size] = model
    return model


def transcribe(audio_path: str, model_size: str = DEFAULT_MODEL_SIZE,
               _model_override: Optional[Callable[[str], str]] = None) -> str:
    """Transcribe an audio file to text. Raises TranscriptionError with a
    specific, honest reason on any failure -- never returns a silent
    empty string as if that were a normal, checkable result.

    _model_override lets tests (and alternative backends, e.g. a future
    IndicConformer wrapper) supply a `path -> text` function without
    touching this function's contract.
    """
    if not os.path.isfile(audio_path):
        raise TranscriptionError(f"Audio file not found: {audio_path}")
    if os.path.getsize(audio_path) == 0:
        raise TranscriptionError("Audio file is empty (0 bytes).")

    if _model_override is not None:
        text = _model_override(audio_path)
    else:
        model = _load_model(model_size)
        segments, _info = model.transcribe(audio_path, beam_size=1)
        text = " ".join(seg.text.strip() for seg in segments).strip()

    if len(text.strip()) < MIN_CONFIDENT_CHARS:
        raise TranscriptionError(
            "Transcription produced no usable text (silence, background "
            "noise, or an unsupported audio format).")
    return text


@dataclass
class AudioVerdict:
    verdict: Verdict
    transcript: Optional[str]
    transcription_failed: bool
    failure_reason: Optional[str]


def assess_audio(audio_path: str, model_size: str = DEFAULT_MODEL_SIZE,
                 _model_override: Optional[Callable[[str], str]] = None
                 ) -> AudioVerdict:
    """Audio-input mirror of shield.engine.assess(). On any transcription
    failure this returns UNCERTAIN, never NO_PATTERN -- a failed
    transcription is not evidence the call was safe, it's a gap in our
    own coverage, and the user is told that plainly."""
    try:
        text = transcribe(audio_path, model_size, _model_override)
    except TranscriptionError as e:
        fallback = Verdict(
            level="UNCERTAIN", score=0, categories_hit={},
            action=("We could not clearly understand this recording. "
                    "Please type what the caller said instead, or ask "
                    "someone to help. Do not assume a call is safe just "
                    "because it could not be checked."),
            explanation=[f"Transcription failed: {e}"])
        return AudioVerdict(fallback, None, True, str(e))

    v = assess(text)
    return AudioVerdict(v, text, False, None)


def assess_audio_bundle(audio_path: str, lang: str = "en",
                        model_size: str = DEFAULT_MODEL_SIZE,
                        _model_override: Optional[Callable[[str], str]] = None
                        ) -> dict:
    """Full API-shaped result (verdict + meter + accessibility) for a
    voice-note input, mirroring server.py's /v1/check for text."""
    av = assess_audio(audio_path, model_size, _model_override)
    m = (meter(av.transcript) if av.transcript
         else {"pressures": {}, "overall": 0, "bars": "(no transcript)"})
    return {
        "verdict": av.verdict.level,
        "action": av.verdict.action,
        "transcript": av.transcript,
        "transcription_failed": av.transcription_failed,
        "meter": m,
        "explanation": av.verdict.explanation,
        "accessibility": accessible_bundle(av.verdict.level, lang),
    }
