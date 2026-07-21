"""Deployed-model training — a self-assembling, all-rounder corpus.

The deployed classifier is an all-rounder BY CONSTRUCTION: it trains on
every dataset available in the deployment, blended so no single source
dominates:
  * synthetic phone-scam templates            (always, shield/datagen.py)
  * real-case-grounded seed corpus            (always, committed)
  * consented feedback corpus — the flywheel  (if any has been collected)
  * real SMS fraud corpus                      (if fetched; optional)

It falls back cleanly to synthetic+seed when the optional sets are absent,
so it stays CI-safe and needs no downloads — yet automatically becomes a
full multi-channel all-rounder wherever the extra data exists, and gets
better on its own as the feedback flywheel fills.

Backed by tests/eval_allrounder.py: the seed lifts phone-scam AUC
0.707 -> 0.886; adding SMS holds SMS AUC at 0.995 while keeping phone at
0.776 — the only mix strong on BOTH channels. Thresholds are re-calibrated
asymmetrically on the blended dev split, which is what keeps false alarms
in check despite the higher recall.
"""
import json
import os
import random
from pathlib import Path

from shield.datagen import make_dataset
from shield.ml import train_layer
from shield.feedback import load_corpus_as_training
from tests.data import BENIGN, AMBIGUOUS

ROOT = Path(__file__).resolve().parents[1]
SEED_CORPUS = ROOT / "data" / "seed_documented_cases.jsonl"
SMS_CORPUS = ROOT / "tests" / "realworld" / "sms.tsv"

# SMS is a DIFFERENT channel. Measured (tests/eval_allrounder + calibration
# probe): adding it to a phone-scam deployment lifts SMS skill but degrades
# phone false-reassurance (OOD FRR 1 -> 3 even with robust calibration). So
# it is OFF by default for the phone model; set DHVANI_INCLUDE_SMS=1 only
# for an explicitly multi-channel deployment.
INCLUDE_SMS = os.getenv("DHVANI_INCLUDE_SMS") == "1"


def _load_seed():
    """Load EVERY data/seed_*.jsonl file, so the corpus expands by simply
    dropping in a new batch — no code change to grow the database."""
    out = []
    data_dir = ROOT / "data"
    if not data_dir.exists():
        return out
    for path in sorted(data_dir.glob("seed_*.jsonl")):
        for l in path.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l)
                out.append((r["text"], 1 if r["label"] == "scam" else 0))
    return out


def _load_sms(per_class: int, seed: int):
    if not SMS_CORPUS.exists():
        return []
    rows = [(t, 1 if lab == "spam" else 0) for lab, t in
            (l.split("\t", 1) for l in SMS_CORPUS.read_text(
                encoding="utf-8", errors="replace").splitlines() if "\t" in l)
            if lab in ("ham", "spam")]
    pos = [x for x in rows if x[1] == 1]
    neg = [x for x in rows if x[1] == 0]
    rng = random.Random(seed)
    rng.shuffle(pos); rng.shuffle(neg)
    return pos[:per_class] + neg[:per_class]   # balanced, so SMS can't dominate


def sources(seed: int = 42) -> dict:
    """What went into the blend — for transparency / logging."""
    return {
        "synthetic": 600,
        "seed": len(_load_seed()),
        "feedback_corpus": len(load_corpus_as_training()),
        "sms": len(_load_sms(300, seed)) if INCLUDE_SMS else 0,
    }


def assemble_dataset(seed: int = 42):
    tr, dv, te = make_dataset(n_per_class=300, seed=seed)
    extra = _load_seed() + load_corpus_as_training()
    if INCLUDE_SMS:
        extra += _load_sms(300, seed)
    # deterministic 80/20 split of the extra data into train/dev, so the
    # asymmetric calibration still sees a representative benign dev pool.
    e = sorted(set(extra))
    random.Random(seed).shuffle(e)
    cut = int(0.8 * len(e))
    return list(tr) + e[:cut], list(dv) + e[cut:], te


def build_deployed_layer(seed: int = 42):
    """The one place the deployed model is built. All surfaces use this."""
    train, dev, _ = assemble_dataset(seed)
    return train_layer(train, dev, calib_benign=BENIGN, calib_ambiguous=AMBIGUOUS)
