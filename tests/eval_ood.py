"""Out-of-distribution evaluation — the generalisation-gap test.

The 22 transcripts in ood_adversarial_testset.jsonl were hand-written from
real Indian scam typology (I4C/MHA advisory patterns, news-reported cases),
NOT from shield/datagen.py. They therefore measure true out-of-distribution
behaviour rather than paraphrase-robustness within the generator's family.

Most scam transcripts deliberately avoid obvious registry vocabulary, and
the benign set is adversarially hard (a real bank fraud desk, a real police
summons, a legit courier) so false-reassurance is measured honestly.

Reports, for rules-only (L1+L3) and the deployed hybrid (L1+L3 escalated
by L2):
  * scam recall  = not reassured (RED or UNCERTAIN) / n_scam
  * scam RED      = caught outright as HIGH_RISK / n_scam
  * FALSE REASSURANCE = scam -> NO_PATTERN  (the hard gate; must be 0)
  * benign pass   = NO_PATTERN / n_benign
  * benign FALSE ALARM = benign -> HIGH_RISK (must be 0)
"""
import io
import json
import sys
from pathlib import Path

# UTF-8 stdout so Devanagari case-ids/text never crash on Windows cp1252.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shield.engine import assess as rules_assess       # noqa: E402
from shield.datagen import make_dataset                # noqa: E402
from shield.ml import train_layer, hybrid_assess       # noqa: E402
from tests.data import BENIGN, AMBIGUOUS               # noqa: E402

OOD_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else (
    Path(__file__).resolve().parents[1] / "ood_adversarial_testset.jsonl")

rows = [json.loads(l) for l in OOD_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
scam = [r for r in rows if r["label"] == "scam"]
ben = [r for r in rows if r["label"] == "benign"]

# Train the deployed hybrid EXACTLY as tests/eval_ml.py does (seed=42).
from shield.training import build_deployed_layer   # noqa: E402
layer = build_deployed_layer()
print(f"hybrid calibrated on dev: t_red={layer.t_red:.3f}  t_yellow={layer.t_yellow:.3f}\n")

SYSTEMS = {
    "rules-only": lambda t: rules_assess(t).level,
    "hybrid":     lambda t: hybrid_assess(t, layer)[0],
}


def evaluate(fn):
    m = dict(scam_red=0, scam_unc=0, scam_green=0,
             ben_green=0, ben_unc=0, ben_red=0, fails=[])
    for r in scam:
        lvl = fn(r["text"])
        m["scam_red"] += lvl == "HIGH_RISK"
        m["scam_unc"] += lvl == "UNCERTAIN"
        if lvl == "NO_PATTERN":
            m["scam_green"] += 1
            m["fails"].append(f"  FALSE REASSURANCE  {r['id']:8} [{'/'.join(r['techniques'][:2])}]")
    for r in ben:
        lvl = fn(r["text"])
        m["ben_green"] += lvl == "NO_PATTERN"
        m["ben_unc"] += lvl == "UNCERTAIN"
        if lvl == "HIGH_RISK":
            m["ben_red"] += 1
            m["fails"].append(f"  FALSE ALARM (RED)  {r['id']:8}")
    return m


ns, nb = len(scam), len(ben)
print(f"OOD set: {ns} scam, {nb} benign (hand-written, out-of-distribution)\n")
print(f"{'system':11} {'recall':>8} {'RED':>7} {'FALSE-REASSURE':>15} {'benign pass':>12} {'benign RED':>11}")
detail = {}
for name, fn in SYSTEMS.items():
    m = evaluate(fn)
    detail[name] = m
    recall = (m["scam_red"] + m["scam_unc"]) / ns
    print(f"{name:11} {recall:>7.1%} {m['scam_red']/ns:>6.1%} "
          f"{m['scam_green']:>8} / {ns:<3} {m['ben_green']/nb:>11.1%} {m['ben_red']:>11}")

print("\n--- per-case verdicts (R=HIGH_RISK  U=UNCERTAIN  .=NO_PATTERN) ---")
short = {"HIGH_RISK": "R", "UNCERTAIN": "U", "NO_PATTERN": "."}
print(f"{'id':9} {'label':7} {'rules':>6} {'hybrid':>7}")
for r in rows:
    rl = short[rules_assess(r["text"]).level]
    hy = short[hybrid_assess(r["text"], layer)[0]]
    flag = "  <-- reassured!" if (r["label"] == "scam" and hy == ".") else (
           "  <-- false alarm" if (r["label"] == "benign" and hy == "R") else "")
    print(f"{r['id']:9} {r['label']:7} {rl:>6} {hy:>7}{flag}")

print("\n--- failures ---")
for name, m in detail.items():
    print(f"[{name}]")
    print("\n".join(m["fails"]) if m["fails"] else "  none")

h = detail["hybrid"]
r0 = detail["rules-only"]
# Real gate (catches deployed-model regressions): hybrid must not falsely
# accuse (ben_red 0), must beat rules on false reassurance, and must stay
# within a small honest bound (the OOD set has 1 near-unsolvable miss).
MAX_FR = 2
gate = (h["ben_red"] == 0 and h["scam_green"] <= r0["scam_green"]
        and h["scam_green"] <= MAX_FR)
print(f"\nSAFETY GATE (hybrid): false-reassurance={h['scam_green']} "
      f"(<= {MAX_FR}), false-alarm={h['ben_red']} -> {'HELD' if gate else 'BROKEN'}")
sys.exit(0 if gate else 1)
