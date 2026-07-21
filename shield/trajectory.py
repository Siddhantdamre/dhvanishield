"""Coercion-trajectory scoring.

Hypothesis H2: a digital-arrest call is not a bag of scary words but a
STRUCTURED SEQUENCE — authority -> accusation -> isolation -> threat ->
money -> access. Scripts mutate weekly; the grammar of coercion does not.

We therefore score (a) how much of the canonical sequence is present
(progression) and (b) whether stages appear in canonical order
(concordance, a Kendall-tau-style pairwise statistic). The product is a
trajectory score in [0, 1]. Identical sentences in scrambled order yield
the same progression but lower concordance — the order-sensitivity test
in the eval suite verifies that the system detects structure, not
vocabulary.
"""
import re
from dataclasses import dataclass

from shield.registry import REGISTRY, CANONICAL_STAGES

_SENT_SPLIT = re.compile(r"[.!?\u0964\u0965\n]+")


@dataclass
class Trajectory:
    stages_hit: list          # in canonical order
    first_hit: dict           # stage -> utterance index
    progression: float        # |stages hit| / |canonical stages|
    concordance: float        # ordered pairs consistent with canon, in [0,1]
    score: float              # progression * concordance


def _utterances(text: str) -> list:
    return [u.strip() for u in _SENT_SPLIT.split(text) if u.strip()]


def analyse(text: str, norm) -> Trajectory:
    first_hit = {}
    for i, utt in enumerate(_utterances(text)):
        t = norm(utt)
        for stage in CANONICAL_STAGES:
            if stage in first_hit:
                continue
            if any(m in t for m in REGISTRY[stage]["markers"]):
                first_hit[stage] = i

    stages_hit = [s for s in CANONICAL_STAGES if s in first_hit]
    progression = len(stages_hit) / len(CANONICAL_STAGES)

    pairs = concordant = 0
    for a_idx, a in enumerate(stages_hit):
        for b in stages_hit[a_idx + 1:]:
            pairs += 1
            if first_hit[a] <= first_hit[b]:
                concordant += 1
    concordance = concordant / pairs if pairs else 1.0

    return Trajectory(stages_hit, first_hit, progression,
                      concordance, progression * concordance)
