"""Is the METHOD sound on real data, or just the synthetic model weak?

Two experiments on the real UCI SMS Spam Collection, held-out split:

  A. TRANSFER — the currently deployed model (char-ngram+LR trained on
     synthetic phone-scam templates) scored on real SMS. Measures how far
     the synthetic training distribution transfers. AUC near 0.5 = it does
     not; the synthetic model is guessing on real text.

  B. METHOD-ON-REAL — the SAME architecture (identical hyperparameters)
     retrained on a real train split and evaluated on a held-out real test
     split. This isolates the method from the training data: if it scores
     well here, the approach is sound and the real gap is DATA, not design.

Honest note: this trains an SMS classifier, which is a different task from
DhvaniShield's coercion phone-scam detection. It is a method-validation
experiment, not a new product — it answers 'does char-ngram+LR actually
work on real data when given real data?'
"""
import io
import math
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sklearn.feature_extraction.text import TfidfVectorizer   # noqa: E402
from sklearn.linear_model import LogisticRegression           # noqa: E402
from sklearn.metrics import roc_auc_score                     # noqa: E402
from shield.datagen import make_dataset                        # noqa: E402
from shield.ml import train_layer                              # noqa: E402
from tests.data import BENIGN, AMBIGUOUS                       # noqa: E402

rows = [l.split("\t", 1) for l in
        (ROOT / "tests" / "realworld" / "sms.tsv").read_text(
            encoding="utf-8", errors="replace").splitlines() if "\t" in l]
data = [(t, 1 if lab == "spam" else 0) for lab, t in rows if lab in ("ham", "spam")]

# deterministic 80/20 split (no hash-order dependence)
import random
rng = random.Random(42)
data = sorted(data)
rng.shuffle(data)
cut = int(0.8 * len(data))
train, test = data[:cut], data[cut:]
Xtr = [t for t, _ in train]; ytr = [y for _, y in train]
Xte = [t for t, _ in test]; yte = [y for _, y in test]
print(f"real SMS: {len(train)} train / {len(test)} test "
      f"({sum(yte)} spam in test)\n")


def wilson(x, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = x / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d
    return (max(0, c - h), min(1, c + h))


# --- A. transfer of the synthetic-trained model ---
s_tr, s_dv, _ = make_dataset(n_per_class=300, seed=42)
synth = train_layer(s_tr, s_dv, calib_benign=BENIGN, calib_ambiguous=AMBIGUOUS)
p_synth = [synth.prob(t) for t in Xte]
auc_synth = roc_auc_score(yte, p_synth)
print(f"A. TRANSFER  synthetic-trained model on real SMS test:  AUC = {auc_synth:.3f}")
print("   (0.5 = no transfer / guessing; the synthetic model has not seen real text)\n")

# --- B. same architecture, retrained on real train ---
vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4),
                      min_df=2, sublinear_tf=True)
clf = LogisticRegression(max_iter=2000, C=2.0)
clf.fit(vec.fit_transform(Xtr), ytr)
proba = clf.predict_proba(vec.transform(Xte))[:, 1]
pred = [1 if p >= 0.5 else 0 for p in proba]

tp = sum(1 for p, y in zip(pred, yte) if p == 1 and y == 1)
fp = sum(1 for p, y in zip(pred, yte) if p == 1 and y == 0)
tn = sum(1 for p, y in zip(pred, yte) if p == 0 and y == 0)
fn = sum(1 for p, y in zip(pred, yte) if p == 0 and y == 1)
prec = tp / (tp + fp) if tp + fp else 0
rec = tp / (tp + fn) if tp + fn else 0
f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0
acc = (tp + tn) / len(yte)
n_ham = tn + fp
fa_lo, fa_hi = wilson(fp, n_ham)
re_lo, re_hi = wilson(tp, tp + fn)

print("B. METHOD-ON-REAL  same char-ngram+LR, retrained on real train,")
print("   held-out real test:")
print(f"     AUC        {roc_auc_score(yte, proba):.3f}")
print(f"     accuracy   {acc:.2%}")
print(f"     precision  {prec:.2%}")
print(f"     recall     {rec:.2%}   CI[{re_lo:.2%}, {re_hi:.2%}]")
print(f"     F1         {f1:.3f}")
print(f"     false-alarm on real ham  {fp}/{n_ham} = {fp/n_ham:.2%}  "
      f"CI[{fa_lo:.2%}, {fa_hi:.2%}]")
print(f"     confusion  TP={tp} FP={fp} TN={tn} FN={fn}")
print("\nHonest read: if B is strong and A is near 0.5, the METHOD works on")
print("real data — the deployed model's weakness is its synthetic TRAINING")
print("DATA, not the approach. The fix is real phone-scam data, not a new model.")
