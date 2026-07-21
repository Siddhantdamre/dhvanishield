"""Rigorous improvement of the real-data message expert.

Honest methodology (no peeking): real SMS split 60/20/20 into
train / validation / test. Feature and threshold choices are made ONLY on
validation; the test split is scored once at the end. This is where real,
measurable gains are possible (authored phone data is already at ceiling).

Compares feature sets:
  A  char n-grams (2-4)           — current baseline
  B  char n-grams (2-5)
  C  char (2-4) + word (1-2)      — sub-word + word-level signal
Selection metric: validation PR-AUC (right for imbalanced scam detection).
Operating point (threshold): chosen on validation as the highest recall at
<= 1% false-alarm. Final numbers are reported on the untouched test split.
"""
import io
import math
import random
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sklearn.feature_extraction.text import TfidfVectorizer   # noqa: E402
from sklearn.pipeline import FeatureUnion                     # noqa: E402
from sklearn.linear_model import LogisticRegression           # noqa: E402
from sklearn.metrics import roc_auc_score, average_precision_score  # noqa: E402

SMS = ROOT / "tests" / "realworld" / "sms.tsv"
if not SMS.exists():
    print("no real SMS corpus — run tests/realworld/fetch.py"); sys.exit(0)

rows = [(t, 1 if lab == "spam" else 0) for lab, t in
        (l.split("\t", 1) for l in SMS.read_text(encoding="utf-8", errors="replace")
         .splitlines() if "\t" in l) if lab in ("ham", "spam")]
data = sorted(rows); random.Random(42).shuffle(data)
n = len(data)
tr, val, te = data[:int(.6*n)], data[int(.6*n):int(.8*n)], data[int(.8*n):]
print(f"real SMS split: train {len(tr)} / val {len(val)} / test {len(te)}\n")


def wilson(x, m, z=1.96):
    if m == 0:
        return (0.0, 0.0)
    p = x/m; d = 1+z*z/m
    c = (p+z*z/(2*m))/d
    h = (z*math.sqrt(p*(1-p)/m+z*z/(4*m*m)))/d
    return (max(0, c-h), min(1, c+h))


def features(name):
    char = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=2, sublinear_tf=True)
    if name == "A":
        return char
    if name == "B":
        return TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True)
    return FeatureUnion([("char", char),
                         ("word", TfidfVectorizer(analyzer="word", ngram_range=(1, 2),
                                                  min_df=2, sublinear_tf=True))])


def fit(name):
    vec = features(name)
    clf = LogisticRegression(max_iter=2000, C=2.0)
    clf.fit(vec.fit_transform([t for t, _ in tr]), [y for _, y in tr])
    return vec, clf


def probs(vec, clf, split):
    return clf.predict_proba(vec.transform([t for t, _ in split]))[:, 1], [y for _, y in split]


# 1. pick features on validation PR-AUC
print(f"{'features':28} {'val ROC-AUC':>12} {'val PR-AUC':>11}")
best, best_ap = None, -1
for name, label in [("A", "char(2-4) [baseline]"), ("B", "char(2-5)"),
                    ("C", "char(2-4)+word(1-2)")]:
    vec, clf = fit(name)
    p, y = probs(vec, clf, val)
    ap = average_precision_score(y, p)
    print(f"{label:28} {roc_auc_score(y, p):12.4f} {ap:11.4f}")
    if ap > best_ap:
        best, best_ap = name, ap
print(f"\nselected on validation: {best}")

# 2. choose threshold on validation: highest recall at <= 1% false-alarm
vec, clf = fit(best)
pv, yv = probs(vec, clf, val)
cands = sorted(set(pv))
chosen = 0.5
for thr in cands:
    pred = [1 if x >= thr else 0 for x in pv]
    fp = sum(a and not b for a, b in zip(pred, yv))
    n_ham = sum(1 for b in yv if b == 0)
    tp = sum(a and b for a, b in zip(pred, yv)); n_scam = sum(yv)
    if n_ham and fp/n_ham <= 0.01:
        chosen = thr
        break   # cands ascending: first threshold meeting FA<=1% -> max recall
print(f"chosen operating threshold (val, FA<=1%): {chosen:.3f}\n")

# 3. FINAL report on the untouched test split
pt, yt = probs(vec, clf, te)
pred = [1 if x >= chosen else 0 for x in pt]
tp = sum(a and b for a, b in zip(pred, yt)); fp = sum(a and not b for a, b in zip(pred, yt))
tn = sum((not a) and (not b) for a, b in zip(pred, yt)); fn = sum((not a) and b for a, b in zip(pred, yt))
n_ham = tn+fp
prec = tp/(tp+fp) if tp+fp else 1.0
rec = tp/(tp+fn) if tp+fn else 0.0
f1 = 2*prec*rec/(prec+rec) if prec+rec else 0.0
fa_lo, fa_hi = wilson(fp, n_ham)
re_lo, re_hi = wilson(tp, tp+fn)
print("=== FINAL (untouched real test split) ===")
print(f"  accuracy    {(tp+tn)/len(te):.2%}")
print(f"  precision   {prec:.2%}")
print(f"  recall      {rec:.2%}   CI[{re_lo:.2%}, {re_hi:.2%}]")
print(f"  F1          {f1:.3f}")
print(f"  false-alarm {fp}/{n_ham} = {fp/n_ham:.2%}   CI[{fa_lo:.2%}, {fa_hi:.2%}]")
print(f"  ROC-AUC     {roc_auc_score(yt, pt):.4f}")
print(f"  PR-AUC      {average_precision_score(yt, pt):.4f}")
print(f"\nwinning config: features={best}, threshold={chosen:.3f}")
print("(compare recall/false-alarm vs the current expert's 97.95% / 1.03%)")
