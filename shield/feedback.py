"""Consent-based feedback capture — the data flywheel engine.

Why this exists: eval_train_real.py proved real accuracy cannot be
fine-tuned out of synthetic or wrong-domain (SMS) data — it needs real
PHONE-scam examples, which no public dataset has. The only source is real
usage. This module turns each real interaction into a labelled example,
building the proprietary corpus that is both the accuracy fix and the moat.

It is designed to NOT betray the project's privacy stance:
  * OPT-IN ONLY. Nothing is stored unless the user explicitly consents.
    Default behaviour is still process-and-delete.
  * MINIMISED + REDACTED. Only a redacted transcript + the human label +
    the model's verdict + a timestamp are written. Emails, phone numbers
    and 4+ digit runs (OTPs, card/account numbers) are stripped before
    writing — which protects the user AND stops the model memorising
    specific numbers.
  * ANONYMOUS + REVOCABLE. No user identity is stored, so entries are not
    linkable to a person. The corpus is a plain append-only JSONL the
    operator can inspect, export, or erase (DPDP-aligned; see PRIVACY.md).

The corpus loads straight back into training via load_corpus_as_training().
"""
import json
import os
import re
import time
from pathlib import Path

_DEFAULT = Path(__file__).resolve().parents[1] / "data" / "labeled_examples.jsonl"

_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_PHONE = re.compile(r"\+?\d[\d\s-]{7,}\d")
_DIGITS = re.compile(r"\d{4,}")


def _path() -> Path:
    """Read the corpus path at call time so tests can redirect it."""
    return Path(os.getenv("DHVANI_CORPUS_PATH", str(_DEFAULT)))


def redact(text: str) -> str:
    """Strip PII/secret-like tokens before anything is stored."""
    text = _EMAIL.sub("<EMAIL>", text)
    text = _PHONE.sub("<PHONE>", text)
    text = _DIGITS.sub("<NUM>", text)
    return text


def record_feedback(text: str, model_verdict: str, is_scam: bool,
                    consent: bool, lang: str = "en") -> dict:
    """Store ONE labelled example — only if the user consented.

    Returns a small, content-free receipt describing what happened."""
    if not text or not text.strip():
        return {"stored": False, "reason": "empty text"}
    # Light anti-poisoning guard: reject implausible lengths before they can
    # dilute a retrain (the real gate is that retraining is a human decision).
    if len(text.strip()) < 10 or len(text) > 20000:
        return {"stored": False, "reason": "rejected: length outside plausible range"}
    if not consent:
        # Explicitly do nothing: no text touches disk without consent.
        return {"stored": False, "reason": "no consent — nothing stored"}

    clean = redact(text.strip())
    entry = {
        "text": clean,
        "label": 1 if is_scam else 0,
        "model_verdict": model_verdict,
        "lang": lang,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return {"stored": True, "redacted": clean != text.strip(),
            "label": entry["label"]}


def _load() -> list:
    path = _path()
    if not path.exists():
        return []
    return [json.loads(l) for l in
            path.read_text(encoding="utf-8").splitlines() if l.strip()]


def corpus_stats() -> dict:
    """Content-free view of the collected corpus, including the model-vs-human
    disagreements — which ARE the training signal (where the model is wrong)."""
    rows = _load()
    scam = sum(1 for r in rows if r["label"] == 1)
    # human says scam but model said NO_PATTERN -> a real MISS to learn from
    misses = sum(1 for r in rows
                 if r["label"] == 1 and r["model_verdict"] == "NO_PATTERN")
    # human says benign but model shouted HIGH_RISK -> a real false alarm
    false_alarms = sum(1 for r in rows
                       if r["label"] == 0 and r["model_verdict"] == "HIGH_RISK")
    return {
        "total": len(rows),
        "scam": scam,
        "benign": len(rows) - scam,
        "model_misses": misses,
        "model_false_alarms": false_alarms,
    }


def load_corpus_as_training() -> list:
    """[(text, label)] pairs, ready to concatenate into the training set —
    this is the flywheel closing: usage -> corpus -> better model."""
    return [(r["text"], r["label"]) for r in _load()]


def clear_corpus() -> int:
    """Erase the whole corpus (operator-level DPDP erasure). Returns count."""
    path = _path()
    n = len(_load())
    if path.exists():
        path.unlink()
    return n
