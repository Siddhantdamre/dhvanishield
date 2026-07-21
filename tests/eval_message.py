"""Real-world-validated message expert — the honest 'usable now' number.

The message expert is trained on 80% of the REAL SMS corpus; here we score
it on the held-out 20% it never saw. This is a genuine real-world result:
real human messages, held out, no authoring by us. It is the number you can
put on a slide as 'real-world validated for the forwarded-message channel'.

Also checks that adding the expert to the committee does NOT regress the
phone path — it is capped at UNCERTAIN, so phone benigns can never be
falsely accused because of it.
"""
import io
import json
import math
import random
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shield import message_model                               # noqa: E402
from shield.ml import hybrid_assess                            # noqa: E402
from shield.training import build_deployed_layer               # noqa: E402


def wilson(x, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = x / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d
    return (max(0, c - h), min(1, c + h))


if message_model.EXPERT is None:
    print("message expert unavailable (no real SMS corpus) — skipping.")
    print("RESULT: SKIPPED (fetch tests/realworld to enable)")
    sys.exit(0)

# Reproduce the SAME held-out split the expert was trained against.
SMS = ROOT / "tests" / "realworld" / "sms.tsv"
rows = [(t, 1 if lab == "spam" else 0) for lab, t in
        (l.split("\t", 1) for l in SMS.read_text(encoding="utf-8", errors="replace")
         .splitlines() if "\t" in l) if lab in ("ham", "spam")]
data = sorted(rows)
random.Random(42).shuffle(data)
test = data[int(0.8 * len(data)):]                 # held-out 20%, never trained on

E = message_model.EXPERT
tp = fp = tn = fn = 0
for t, y in test:
    pred = 1 if E.prob(t) >= E.t_red else 0
    tp += pred and y; fp += pred and not y
    tn += (not pred) and (not y); fn += (not pred) and y
n_ham = tn + fp
prec = tp / (tp + fp) if tp + fp else 1.0
rec = tp / (tp + fn) if tp + fn else 0.0
f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
acc = (tp + tn) / len(test)
fa_lo, fa_hi = wilson(fp, n_ham)

print(f"REAL held-out messages: {len(test)} ({tp+fn} scam, {n_ham} legit)\n")
print("Message expert — real-world validated (held-out real SMS):")
print(f"  accuracy   {acc:.2%}")
print(f"  precision  {prec:.2%}")
print(f"  recall     {rec:.2%}")
print(f"  F1         {f1:.3f}")
print(f"  false-alarm on real legit messages  {fp}/{n_ham} = {fp/n_ham:.2%}"
      f"  CI[{fa_lo:.2%}, {fa_hi:.2%}]")

# no phone regression: OOD/red-team benigns must not be pushed to HIGH_RISK
layer = build_deployed_layer()


def load_jsonl(p):
    return [(json.loads(l)["text"], 1 if json.loads(l)["label"] == "scam" else 0)
            for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]


phone_benigns = [t for t, y in
                 load_jsonl(ROOT / "ood_adversarial_testset.jsonl")
                 + load_jsonl(ROOT / "tests" / "redteam_set.jsonl") if y == 0]
false_alarms = sum(1 for t in phone_benigns
                   if hybrid_assess(t, layer)[0] == "HIGH_RISK")
print(f"\nCommittee safety: phone benigns falsely accused with expert on: "
      f"{false_alarms}/{len(phone_benigns)}")

passed = acc >= 0.90 and fp / n_ham <= 0.02 and false_alarms == 0
print("\nRESULT:", "MESSAGE EXPERT REAL-WORLD VALIDATED" if passed else "FAILED")
sys.exit(0 if passed else 1)
