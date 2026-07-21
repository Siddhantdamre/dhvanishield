"""Manipulation engine on REAL data — no hand-authored probes.

The standing criticism of the generalization result is that the probe was
written by us. This removes that: the strategy engine (built from Cialdini
exemplars for PHONE scams, never trained on SMS, never tuned on this data)
is scored on 5,574 REAL messages written by real scammers and real people.

Reported threshold-free (ROC-AUC) so no operating point is tuned here.
Honest framing: real SMS fraud is a different channel from phone coercion,
so this measures cross-channel transfer of the strategy representation to
genuine, third-party-authored manipulation.
"""
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sklearn.metrics import roc_auc_score          # noqa: E402
from shield.manipulation import analyze             # noqa: E402
from shield.engine import assess as rules_assess    # noqa: E402

SMS = ROOT / "tests" / "realworld" / "sms.tsv"
if not SMS.exists():
    print("no real corpus — run tests/realworld/fetch.py")
    print("RESULT: SKIPPED"); sys.exit(0)

rows = [(t, 1 if lab == "spam" else 0) for lab, t in
        (l.split("\t", 1) for l in SMS.read_text(encoding="utf-8", errors="replace")
         .splitlines() if "\t" in l) if lab in ("ham", "spam")]
y = [lab for _, lab in rows]
print(f"REAL corpus: {len(rows)} messages "
      f"({sum(y)} real fraud / {len(y)-sum(y)} real legitimate)\n")

manip = [analyze(t)["manipulation_score"] for t, _ in rows]
kw = [float(rules_assess(t).score) for t, _ in rows]

auc_manip = roc_auc_score(y, manip)
auc_kw = roc_auc_score(y, kw) if len(set(kw)) > 1 else 0.5

print("Ranking real fraud above real legitimate messages (threshold-free):")
print(f"  scam-registry (keyword, phone-domain) : ROC-AUC {auc_kw:.3f}")
print(f"  manipulation-strategy engine          : ROC-AUC {auc_manip:.3f}")

# what tactics does the engine attribute to REAL fraud vs REAL legit?
from collections import Counter
def top(label):
    c = Counter()
    for t, lab in rows:
        if lab == label:
            for s in analyze(t)["dominant"]:
                c[s] += 1
    return [s for s, _ in c.most_common(4)]
print(f"\n  strategies it attributes to REAL fraud     : {top(1)}")
print(f"  strategies it attributes to REAL legitimate: {top(0)}")

# Honest gate: MEANINGFUL transfer to real data (well above chance and the
# keyword baseline). Note it is FAR below the hand-authored probe (0.94) -
# that gap is the point: real, third-party data is harder, and this number is
# the defensible one.
ok = auc_manip >= 0.60 and (auc_manip - auc_kw) >= 0.08
print(f"\nRESULT: {'MEANINGFUL (BUT WEAK) TRANSFER TO REAL FRAUD' if ok else 'NO TRANSFER'}"
      f"  [AUC={auc_manip:.3f} vs keyword {auc_kw:.3f}; probe was 0.94 - real data is harder]")
sys.exit(0 if ok else 1)
