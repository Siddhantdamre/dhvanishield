"""Red-team stress test — mapping the boundary of trust.

Unlike eval_ood.py (unseen-but-natural transcripts), this set actively
ATTACKS the model along three axes people actually face:
  obfuscation     surface tricks that evade the lexical registry
                  (spacing, transliteration, leetspeak, punctuation)
  novel_family    scam TYPES the registry was never built for
                  (sextortion, loan-app harassment, fake job, UPI-collect,
                   deepfake family emergency, fake customer care)
  code_mix        heavy Hinglish
  polite_slowburn scams with no pressure vocabulary
  alarm_fatigue   LEGIT calls that mention otp/payment/police/account —
                  if these turn RED, people stop trusting the tool
  hard_benign     plausibly scary but legitimate calls

A trustworthy tool is not one that never fails; it is one whose failures
are known and bounded. This report states them, with 95% Wilson
confidence intervals so small-sample numbers are not over-read.
"""
import io
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shield.datagen import make_dataset            # noqa: E402
from shield.ml import train_layer, hybrid_assess   # noqa: E402
from tests.data import BENIGN, AMBIGUOUS           # noqa: E402

rows = [json.loads(l) for l in
        (ROOT / "tests" / "redteam_set.jsonl").read_text(encoding="utf-8").splitlines()
        if l.strip()]

from shield.training import build_deployed_layer   # noqa: E402
layer = build_deployed_layer()


def wilson(x, n, z=1.96):
    """95% Wilson score interval for a proportion (honest for small n)."""
    if n == 0:
        return (0.0, 0.0)
    p = x / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (max(0, center - half), min(1, center + half))


def verdict(text):
    return hybrid_assess(text, layer)[0]


by_cat = defaultdict(lambda: {"n": 0, "bad": 0, "cases": []})
scam_n = scam_reassured = 0
ben_n = ben_red = ben_unc = 0

for r in rows:
    lvl = verdict(r["text"])
    cat = by_cat[r["attack_type"]]
    cat["n"] += 1
    if r["label"] == "scam":
        scam_n += 1
        bad = lvl == "NO_PATTERN"          # false reassurance = the fatal error
        scam_reassured += bad
    else:
        ben_n += 1
        ben_red += lvl == "HIGH_RISK"
        ben_unc += lvl == "UNCERTAIN"
        bad = lvl == "HIGH_RISK"           # false alarm on a legit call
    cat["bad"] += bad
    if bad:
        cat["cases"].append(r["id"])

print(f"Red-team set: {scam_n} scam attacks, {ben_n} benign traps\n")
print(f"{'attack type':16} {'n':>3} {'failures':>9}   failing ids")
order = ["obfuscation", "novel_family", "code_mix", "polite_slowburn",
         "alarm_fatigue", "hard_benign"]
for cat in order:
    c = by_cat[cat]
    kind = "reassured" if cat not in ("alarm_fatigue", "hard_benign") else "false-RED"
    print(f"{cat:16} {c['n']:>3} {c['bad']:>4} {kind:>10}   "
          f"{', '.join(c['cases']) if c['cases'] else '-'}")

fr_lo, fr_hi = wilson(scam_reassured, scam_n)
fa_lo, fa_hi = wilson(ben_red, ben_n)
print("\n=== trust-critical metrics (95% Wilson CI) ===")
print(f"FALSE REASSURANCE (scam called safe): {scam_reassured}/{scam_n} "
      f"= {scam_reassured/scam_n:.1%}  CI[{fr_lo:.1%}, {fr_hi:.1%}]")
print(f"FALSE ALARM (legit call called scam): {ben_red}/{ben_n} "
      f"= {ben_red/ben_n:.1%}  CI[{fa_lo:.1%}, {fa_hi:.1%}]")
print(f"Over-warn on legit calls (UNCERTAIN): {ben_unc}/{ben_n} "
      f"= {ben_unc/ben_n:.1%}  (alarm-fatigue risk, not a safety error)")
print(f"Scam recall (caught as RED or UNCERTAIN): "
      f"{scam_n - scam_reassured}/{scam_n} = {(scam_n-scam_reassured)/scam_n:.1%}")

# Real gate: no false accusation, and false reassurance within an honest
# small bound (catches deployed-model regressions like the max-calibration bug).
MAX_FR = 2
gate = ben_red == 0 and scam_reassured <= MAX_FR
print("\nRESULT:", "RED-TEAM PASS" if gate else "RED-TEAM REGRESSION")
sys.exit(0 if gate else 1)
