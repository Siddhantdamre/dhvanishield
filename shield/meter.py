"""Manipulation Meter — the expert committee made visible.

Architecture framing: DhvaniShield is a committee of small experts —
six lexical category-experts (one per coercion stage), a statistical
paraphrase-expert (L2), and a temporal sequence-expert (L3) — combined
by an asymmetric gate that may only escalate. This module exposes each
expert's voice as a 0-100 pressure score, so the user is never accused
("SCAM!") but shown what is being done to their mind:

    Authority      ████████░░
    Accusation     ██████░░░░
    Isolation      ██████████
    Urgency        ████░░░░░░
    Financial pull ████████░░
    Access grab    ░░░░░░░░░░

Rendered in Unicode blocks it travels inside a plain WhatsApp/SMS
message — no app, no screen requirements, fits existing workflows.
"""
from shield.registry import REGISTRY, CANONICAL_STAGES
from shield.engine import _norm

LABELS = {
    "authority_impersonation": "Authority",
    "false_accusation": "Accusation",
    "isolation": "Isolation",
    "urgency_threat": "Urgency",
    "money_movement": "Financial pull",
    "remote_access_credentials": "Access grab",
}


def pressures(text: str) -> dict:
    """Per-expert pressure, 0-100. One hit = 50; each extra hit +25
    (capped) — simple, monotone, auditable."""
    t = _norm(text)
    out = {}
    for cat in CANONICAL_STAGES:
        n = sum(1 for m in REGISTRY[cat]["markers"] if m in t)
        out[cat] = 0 if n == 0 else min(100, 50 + 25 * (n - 1))
    return out


def overall(p: dict) -> int:
    """Weight each expert by its registry weight (isolation/money/access
    count more), normalised to 0-100."""
    wsum = sum(REGISTRY[c]["weight"] for c in CANONICAL_STAGES)
    return round(sum(p[c] * REGISTRY[c]["weight"] for c in CANONICAL_STAGES) / wsum)


def bars(p: dict, width: int = 10) -> str:
    """Unicode meter — renders identically in WhatsApp, SMS, terminal."""
    lines = []
    for cat in CANONICAL_STAGES:
        filled = round(p[cat] / 100 * width)
        lines.append(f"{LABELS[cat]:<14} {'█' * filled}{'░' * (width - filled)}")
    return "\n".join(lines)


def meter(text: str) -> dict:
    p = pressures(text)
    return {"pressures": {LABELS[c]: p[c] for c in CANONICAL_STAGES},
            "overall": overall(p),
            "bars": bars(p)}
