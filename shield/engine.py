"""DhvaniShield decision engine.

Layered method:
  L1 lexical  — auditable marker matching per category (registry.py)
  L2 semantic — embedding-similarity matcher for paraphrased scripts
                (interface defined; implementation is a week-2 layer)
  L3 temporal — coercion-trajectory scoring (trajectory.py)
  D  decision — asymmetric three-output verdict; 'safe' is not in the
                output space. Trajectory may only ESCALATE, never clear:
                a monotonicity constraint that preserves the hard gate
                FALSE_REASSURANCE = 0 under any L3 behaviour.

Ablation flags allow each layer to be disabled independently so every
claimed contribution is measurable (see tests/eval.py ablation table).
"""
from dataclasses import dataclass, field
import re
import unicodedata

from shield.registry import REGISTRY
from shield import trajectory

HIGH_RISK_MIN_CATEGORIES = 2
HIGH_RISK_MIN_SCORE = 4
UNCERTAIN_MIN_SCORE = 2
TRAJ_ESCALATE_STAGES = 3       # >=3 canonical stages present, and
TRAJ_ESCALATE_SCORE = 0.5      # ordered enough -> escalate UNCERTAIN->HIGH


@dataclass
class Verdict:
    level: str
    score: int
    categories_hit: dict
    action: str
    explanation: list
    trajectory: object = None
    escalated_by_trajectory: bool = False


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower()
    return re.sub(r"\s+", " ", f" {text} ")


ACTIONS = {
    "HIGH_RISK": ("This matches the digital-arrest scam pattern. HANG UP NOW. "
                  "Call the national cyber helpline 1930. Tell a family member."),
    "UNCERTAIN": ("Some warning signs are present but the pattern is incomplete. "
                  "Hang up and verify independently: call the official number "
                  "yourself, or dial 1930. Do not act on this call."),
    "NO_PATTERN": "This looks like a normal call. Nothing suspicious found.",
}

# Shown ONLY when a green-verdict call still mentioned money/credentials —
# a gentle tip, not a scare banner.
GREEN_TIP_TRIGGERS = ["money", "transfer", "payment", "otp", "pin", "account",
                      "पैसे", "भुगतान", "ओटीपी", "खाते"]
GREEN_TIP = ("Tip: since this call mentioned money or account details, take a "
             "moment to verify with the official number before acting. Real "
             "agencies and banks never mind you double-checking.")


def assess(text: str, use_trajectory: bool = True,
           languages: set | None = None) -> Verdict:
    """languages: optional ablation filter, e.g. {'ascii'} keeps only
    ASCII markers (simulating an English-only registry)."""
    t = _norm(text)
    hits, score = {}, 0
    for cat, spec in REGISTRY.items():
        markers = spec["markers"]
        if languages == {"ascii"}:
            markers = [m for m in markers if m.isascii()]
        matched = [m for m in markers if m in t]
        if matched:
            hits[cat] = matched
            score += spec["weight"]

    if len(hits) >= HIGH_RISK_MIN_CATEGORIES and score >= HIGH_RISK_MIN_SCORE:
        level = "HIGH_RISK"
    elif score >= UNCERTAIN_MIN_SCORE:
        # Authority-only (police/court/TRAI named, no other signal) deliberately
        # ABSTAINS -> UNCERTAIN. A real and a fake police call are textually
        # identical, so "verify independently" is the honest, safe answer; the
        # system abstains uniformly rather than guess. (Tried carving this out
        # to reduce over-warning; it broke the intended abstention on the
        # AMBIGUOUS set, so it was reverted — the abstention is by design.)
        level = "UNCERTAIN"
    else:
        level = "NO_PATTERN"

    traj, escalated = None, False
    if use_trajectory:
        traj = trajectory.analyse(text, _norm)
        if (level == "UNCERTAIN"
                and len(traj.stages_hit) >= TRAJ_ESCALATE_STAGES
                and traj.score >= TRAJ_ESCALATE_SCORE):
            level, escalated = "HIGH_RISK", True
        # Monotonicity: trajectory never downgrades a verdict.

    explanation = [f"{cat.replace('_', ' ').title()}: {REGISTRY[cat]['why']} "
                   f"(matched: {', '.join(m.strip() for m in ms)})"
                   for cat, ms in hits.items()]
    if traj and traj.stages_hit:
        explanation.append(
            f"Script progression: {len(traj.stages_hit)}/6 stages of the "
            f"digital-arrest sequence present, order consistency "
            f"{traj.concordance:.0%} (trajectory score {traj.score:.2f}).")

    action = ACTIONS[level]
    if level == "NO_PATTERN" and any(k in t for k in GREEN_TIP_TRIGGERS):
        action = f"{action} {GREEN_TIP}"
    return Verdict(level, score, hits, action, explanation,
                   traj, escalated)
