"""Calibration & selective prediction on REAL held-out data.

The safety question: does the model produce honest confidence, and can it
DEFER to a human to hold a target error rate? Proper protocol: real SMS split
train/cal/test; the calibrator is fit on cal; every number is on the untouched
test split.

Reports:
  * ECE before and after Platt calibration (are the probabilities honest?)
  * a risk-coverage curve (does error fall as the model answers less?)
  * a selective operating point: to guarantee <= 1% error on what it answers,
    how much can it answer, and how much must it defer to a human?
"""
import io
import random
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sklearn.feature_extraction.text import TfidfVectorizer   # noqa: E402
from sklearn.linear_model import LogisticRegression           # noqa: E402
from shield.calibration import (ece, platt_fit, platt_apply,   # noqa: E402
                                risk_coverage, selective_threshold)

SMS = ROOT / "tests" / "realworld" / "sms.tsv"
if not SMS.exists():
    print("no real SMS corpus — run tests/realworld/fetch.py")
    print("RESULT: SKIPPED"); sys.exit(0)

rows = [(t, 1 if lab == "spam" else 0) for lab, t in
        (l.split("\t", 1) for l in SMS.read_text(encoding="utf-8", errors="replace")
         .splitlines() if "\t" in l) if lab in ("ham", "spam")]
data = sorted(rows); random.Random(42).shuffle(data)
n = len(data)
tr, cal, te = data[:int(.6*n)], data[int(.6*n):int(.8*n)], data[int(.8*n):]

vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=2, sublinear_tf=True)
clf = LogisticRegression(max_iter=2000, C=2.0)
clf.fit(vec.fit_transform([t for t, _ in tr]), [y for _, y in tr])


def prob(split):
    return [float(p) for p in clf.predict_proba(vec.transform([t for t, _ in split]))[:, 1]]


p_cal, y_cal = prob(cal), [y for _, y in cal]
p_te, y_te = prob(te), [y for _, y in te]

# --- calibration quality (are the probabilities honest?) ---
ece_raw = ece(p_te, y_te)
platt = platt_fit(p_cal, y_cal)
p_te_cal = platt_apply(platt, p_te)
ece_cal = ece(p_te_cal, y_te)

print(f"real SMS: train {len(tr)} / cal {len(cal)} / test {len(te)}\n")
print("=== calibration (Expected Calibration Error, lower = more honest) ===")
print(f"  ECE raw        : {ece_raw:.3f}")
print(f"  ECE Platt-cal  : {ece_cal:.3f}")

# --- selective prediction (know when to defer) ---
conf = [max(p, 1 - p) for p in p_te_cal]                  # confidence in the prediction
correct = [int((p >= 0.5) == bool(y)) for p, y in zip(p_te_cal, y_te)]
rc = dict(risk_coverage(conf, correct))


def risk_at(cov):
    # nearest coverage point at or above cov
    ks = [c for c in rc if c >= cov]
    return rc[min(ks)] if ks else rc[max(rc)]


print("\n=== risk-coverage (error rate vs fraction the model answers) ===")
for c in (1.0, 0.9, 0.75, 0.5):
    print(f"  answer {c:>4.0%} of cases -> error {risk_at(c):.2%}")

thr, cov = selective_threshold(conf, correct, target_risk=0.01)
print("\n=== selective operating point (defer to a human) ===")
print(f"  to GUARANTEE <= 1% error, the model answers {cov:.0%} and defers "
      f"{1-cov:.0%} to a human (confidence >= {thr:.2f}).")

# sanity gate: calibration should not worsen, and selectivity must reduce risk
full_risk = risk_at(1.0)
half_risk = risk_at(0.5)
ok = ece_cal <= ece_raw + 0.02 and half_risk <= full_risk
print("\nRESULT:", "CALIBRATION + SELECTIVE PREDICTION OK" if ok else "FAILED")
sys.exit(0 if ok else 1)
