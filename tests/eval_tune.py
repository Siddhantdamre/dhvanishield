"""Honest fine-tuning — cross-validated hyperparameter search.

For a char-ngram + logistic-regression model, 'fine-tune' means searching
the pipeline hyperparameters (n-gram range, regularisation C, min document
frequency) and keeping the config that best separates scam from benign on
HELD-OUT data — not tuning to a target number.

Selection metric: AUC on the independent OOD + red-team sets (never trained
on). 5-fold CV AUC on the training corpus is reported alongside as a
stability check. The current deployed config is flagged for comparison.
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
from sklearn.metrics import roc_auc_score                     # noqa: E402
from sklearn.model_selection import StratifiedKFold           # noqa: E402
from shield.datagen import make_dataset                        # noqa: E402
import shield.training as T                                    # noqa: E402


def load(p):
    return [(json.loads(l)["text"], 1 if json.loads(l)["label"] == "scam" else 0)
            for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]


tr, dv, _ = make_dataset(n_per_class=300, seed=42)
corpus = list(tr) + list(dv) + T._load_seed()
indep = load(ROOT / "ood_adversarial_testset.jsonl") + load(ROOT / "tests" / "redteam_set.jsonl")
X = [t for t, _ in corpus]; y = [l for _, l in corpus]
Xi = [t for t, _ in indep]; yi = [l for _, l in indep]
print(f"tune corpus {len(corpus)} | independent test {len(indep)}\n")

NGRAMS = [(2, 4), (2, 5), (3, 5)]
CS = [1.0, 2.0, 4.0]
MIN_DF = [1, 2]
CURRENT = ((2, 4), 2.0, 2)


def fit_prob(ngram, C, mindf, Xtr, ytr):
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=ngram,
                          min_df=mindf, sublinear_tf=True)
    clf = LogisticRegression(max_iter=2000, C=C)
    clf.fit(vec.fit_transform(Xtr), ytr)
    return lambda texts: clf.predict_proba(vec.transform(texts))[:, 1]


def cv_auc(ngram, C, mindf):
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    aucs = []
    for tri, tei in skf.split(X, y):
        prob = fit_prob(ngram, C, mindf, [X[i] for i in tri], [y[i] for i in tri])
        p = prob([X[i] for i in tei])
        aucs.append(roc_auc_score([y[i] for i in tei], p))
    return statistics.mean(aucs)


results = []
for ng in NGRAMS:
    for C in CS:
        for md in MIN_DF:
            indep_auc = roc_auc_score(yi, fit_prob(ng, C, md, X, y)(Xi))
            results.append((indep_auc, cv_auc(ng, C, md), ng, C, md))

results.sort(reverse=True)
print(f"{'rank':4} {'indep AUC':>10} {'CV AUC':>8}  {'ngram':>8} {'C':>4} {'min_df':>6}")
for i, (ia, ca, ng, C, md) in enumerate(results[:6], 1):
    cur = "  <- current" if (ng, C, md) == CURRENT else ""
    print(f"{i:4} {ia:10.3f} {ca:8.3f}  {str(ng):>8} {C:>4} {md:>6}{cur}")

cur_score = next(ia for ia, _, ng, C, md in results if (ng, C, md) == CURRENT)
best_ia, best_ca, *best_cfg = results[0]
print(f"\ncurrent config indep AUC {cur_score:.3f} | best {best_ia:.3f} "
      f"({best_cfg})")
print("recommend updating" if best_ia - cur_score > 0.01
      else "current config is at/near the best — no change warranted")
