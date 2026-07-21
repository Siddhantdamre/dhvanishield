"""Honest accuracy of the real-case-grounded seed batch.

No number is targeted. Fixed methodology, reported as-is:
  A. 5-fold stratified cross-validation on the seed (within-distribution).
  B. Train on the FULL seed, test on the INDEPENDENT OOD + red-team sets
     (written in earlier sessions, different scenarios) — the honest
     generalization number, the one worth quoting.

Same architecture as the deployed model: char n-gram (2-4) TF-IDF +
logistic regression.
"""
import io
import json
import statistics
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sklearn.feature_extraction.text import TfidfVectorizer   # noqa: E402
from sklearn.linear_model import LogisticRegression           # noqa: E402
from sklearn.model_selection import StratifiedKFold           # noqa: E402


def load(path):
    return [(json.loads(l)["text"], 1 if json.loads(l)["label"] == "scam" else 0)
            for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]


seed = load(ROOT / "data" / "seed_documented_cases.jsonl")
indep = load(ROOT / "ood_adversarial_testset.jsonl") + load(ROOT / "tests" / "redteam_set.jsonl")
print(f"seed: {sum(y for _,y in seed)} scam / {sum(1-y for _,y in seed)} benign "
      f"= {len(seed)}   |   independent test: {len(indep)}\n")


def make_model():
    return (TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4),
                            min_df=2, sublinear_tf=True),
            LogisticRegression(max_iter=2000, C=2.0))


def metrics(y_true, y_pred):
    tp = sum(p and t for p, t in zip(y_pred, y_true))
    fp = sum(p and not t for p, t in zip(y_pred, y_true))
    tn = sum(not p and not t for p, t in zip(y_pred, y_true))
    fn = sum(not p and t for p, t in zip(y_pred, y_true))
    acc = (tp + tn) / len(y_true)
    prec = tp / (tp + fp) if tp + fp else 1.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    fa = fp / (tn + fp) if tn + fp else 0.0
    return acc, prec, rec, f1, fa


# --- A. 5-fold stratified CV on the seed ---
X = [t for t, _ in seed]; y = [lab for _, lab in seed]
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
accs, f1s, recs, fas = [], [], [], []
for tr, te in skf.split(X, y):
    vec, clf = make_model()
    clf.fit(vec.fit_transform([X[i] for i in tr]), [y[i] for i in tr])
    pred = clf.predict(vec.transform([X[i] for i in te]))
    a, p, r, f, fa = metrics([y[i] for i in te], list(pred))
    accs.append(a); f1s.append(f); recs.append(r); fas.append(fa)

print("A. 5-fold cross-validation on the seed (within-distribution)")
print(f"   accuracy   {statistics.mean(accs):.1%}  (±{statistics.pstdev(accs):.1%})")
print(f"   recall     {statistics.mean(recs):.1%}")
print(f"   F1         {statistics.mean(f1s):.3f}")
print(f"   false-alarm{statistics.mean(fas):.1%}\n")

# --- B. train on full seed, test on independent OOD + red-team ---
vec, clf = make_model()
clf.fit(vec.fit_transform(X), y)
yi = [lab for _, lab in indep]
pred = list(clf.predict(vec.transform([t for t, _ in indep])))
a, p, r, f, fa = metrics(yi, pred)
print("B. Generalization to INDEPENDENT sets (the honest number to quote)")
print(f"   accuracy   {a:.1%}")
print(f"   precision  {p:.1%}")
print(f"   recall     {r:.1%}")
print(f"   F1         {f:.3f}")
print(f"   false-alarm{fa:.1%}")
print("\n(No threshold or data was tuned to hit a target — these are the")
print(" numbers the fixed methodology produced.)")
