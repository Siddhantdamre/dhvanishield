"""Does training on REAL data actually make the model accurate?

Compares two models on three held-out test sets:
  synthetic-only  — the current deployed model (templates only)
  augmented       — same architecture trained on real fraud SMS + the
                    synthetic phone-scam templates (real language + domain
                    coverage). OOD and red-team sets are NEVER trained on,
                    so they stay honest held-out tests.

Reports AUC (threshold-free discrimination) on each set, plus real-SMS
accuracy/F1/false-alarm for the augmented model. The question this answers
is the blunt one: is retraining on real data worth it?
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

from sklearn.feature_extraction.text import TfidfVectorizer   # noqa: E402
from sklearn.linear_model import LogisticRegression           # noqa: E402
from sklearn.metrics import roc_auc_score                     # noqa: E402
from shield.datagen import make_dataset                        # noqa: E402
from shield.ml import train_layer                              # noqa: E402
from tests.data import BENIGN, AMBIGUOUS                       # noqa: E402


def load_jsonl(path):
    out = []
    for l in Path(path).read_text(encoding="utf-8").splitlines():
        if not l.strip():
            continue
        r = json.loads(l)
        out.append((r["text"], 1 if r["label"] == "scam" else 0))
    return out


# --- real SMS, held-out split ---
sms = [l.split("\t", 1) for l in
       (ROOT / "tests" / "realworld" / "sms.tsv").read_text(
           encoding="utf-8", errors="replace").splitlines() if "\t" in l]
real = sorted((t, 1 if lab == "spam" else 0) for lab, t in sms if lab in ("ham", "spam"))
random.Random(42).shuffle(real)
cut = int(0.8 * len(real))
real_train, real_test = real[:cut], real[cut:]

# --- synthetic templates (train+dev used for training only) ---
s_tr, s_dv, _ = make_dataset(n_per_class=300, seed=42)
synth_pairs = list(s_tr) + list(s_dv)

# --- held-out phone-scam sets (NEVER trained on) ---
ood = load_jsonl(ROOT / "ood_adversarial_testset.jsonl")
redteam = load_jsonl(ROOT / "tests" / "redteam_set.jsonl")

# --- model A: synthetic-only (current deployed) ---
synth_layer = train_layer(s_tr, s_dv, calib_benign=BENIGN, calib_ambiguous=AMBIGUOUS)
probA = synth_layer.prob

# --- model B: augmented (real fraud SMS + synthetic templates) ---
aug = real_train + synth_pairs
vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=2, sublinear_tf=True)
clf = LogisticRegression(max_iter=2000, C=2.0)
clf.fit(vec.fit_transform([t for t, _ in aug]), [y for _, y in aug])
def probB(t): return float(clf.predict_proba(vec.transform([t]))[0, 1])


def auc(data, fn):
    y = [lab for _, lab in data]
    if len(set(y)) < 2:
        return None
    return roc_auc_score(y, [fn(t) for t, _ in data])


SETS = [("real SMS (held-out)", real_test),
        ("OOD phone-scam", ood),
        ("red-team", redteam)]

print(f"train sizes: real {len(real_train)} + synthetic {len(synth_pairs)} "
      f"= {len(aug)}\n")
print(f"{'test set':22} {'synthetic-only AUC':>20} {'augmented AUC':>15}")
for name, data in SETS:
    a, b = auc(data, probA), auc(data, probB)
    print(f"{name:22} {a if a is None else f'{a:.3f}':>20} "
          f"{b if b is None else f'{b:.3f}':>15}")

# real-SMS accuracy for the augmented model (0.5 threshold)
yte = [y for _, y in real_test]
pred = [1 if probB(t) >= 0.5 else 0 for t, _ in real_test]
tp = sum(p and y for p, y in zip(pred, yte))
fp = sum(p and not y for p, y in zip(pred, yte))
tn = sum(not p and not y for p, y in zip(pred, yte))
fn = sum(not p and y for p, y in zip(pred, yte))
prec = tp / (tp + fp) if tp + fp else 0
rec = tp / (tp + fn) if tp + fn else 0
f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0
print(f"\naugmented on real SMS held-out: acc {(tp+tn)/len(yte):.2%} | "
      f"precision {prec:.2%} | recall {rec:.2%} | F1 {f1:.3f} | "
      f"false-alarm {fp}/{tn+fp} = {fp/(tn+fp):.2%}")
print("\nHonest read: compare the two AUC columns. If augmented beats")
print("synthetic-only on ALL THREE sets, real data helps everywhere and the")
print("deployed model should be retrained on real data — not fine-tuned on")
print("synthetic. If it wins on SMS but loses on phone-scam sets, the domains")
print("differ and we need real PHONE-scam data specifically.")
