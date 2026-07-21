"""Streaming assessment — DhvaniShield as a live listener.

Feeds the call utterance-by-utterance and yields a verdict after each,
exactly as a real-time listener would experience it. Enables the
headline metric:

  EARLINESS — at which utterance does the alarm fire, and is that
  BEFORE the scammer reaches the money/credentials stage?

A tool that flags the scam only when money is requested is a witness;
one that flags it during the isolation stage is a bodyguard.
"""
from dataclasses import dataclass

from shield.engine import assess, Verdict
from shield.trajectory import _utterances


@dataclass
class StreamStep:
    index: int              # utterance number (0-based)
    utterance: str
    verdict: Verdict
    stages_so_far: list


def stream(text: str):
    utts = _utterances(text)
    acc = []
    for i, u in enumerate(utts):
        acc.append(u)
        v = assess(". ".join(acc))
        stages = v.trajectory.stages_hit if v.trajectory else []
        yield StreamStep(i, u, v, stages)


def earliness(text: str) -> dict:
    """First utterance index at which HIGH_RISK fires, vs first index at
    which the money/credentials stages appear. Returns fractions of call."""
    utts = _utterances(text)
    n = len(utts)
    fired_at = money_at = None
    for step in stream(text):
        if fired_at is None and step.verdict.level == "HIGH_RISK":
            fired_at = step.index
        hit = step.verdict.trajectory.first_hit if step.verdict.trajectory else {}
        if money_at is None and ("money_movement" in hit
                                 or "remote_access_credentials" in hit):
            money_at = step.index
    return {
        "utterances": n,
        "fired_at": fired_at,
        "money_at": money_at,
        "fired_fraction": (fired_at + 1) / n if fired_at is not None else None,
        "before_money": (fired_at is not None
                         and (money_at is None or fired_at <= money_at)),
    }
