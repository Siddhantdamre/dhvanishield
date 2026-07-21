"""All-rounder experiment — one model across variable datasets.

We have data from several distributions:
  * synthetic  — templated phone-scam grammar (shield/datagen.py)
  * seed       — real-case-grounded phone scams (data/seed_documented_cases)
  * SMS        — real human SMS, a DIFFERENT channel (UCI, tests/realworld)
  * OOD/redteam— independent phone-scam probes (held out, never trained on)

Earlier we saw SMS-only training destroys phone-scam skill (AUC 0.40). So
'all-rounder' is a claim to TEST, not assume: does a balanced multi-domain
mix stay strong on BOTH real SMS and phone scams at once? Four training
mixes are each evaluated on two held-out domains. Nothing is tuned to a
target; balanced sampling + fixed seeds, reported as-is.
"""
import io
import json
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


def load_jsonl(p):
    return [(json.loads(l)["text"], 1 if json.loads(l)["label"] == "scam" else 0)
            for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]


def split(data, frac, seed):
    d = sorted(data); random.Random(seed).shuffle(d)
    cut = int(frac * len(d))
    return d[:cut], d[cut:]


# --- assemble the variable datasets, each with a clean held-out slice ---
sms = [(t, 1 if lab == "spam" else 0) for lab, t in
       (l.split("\t", 1) for l in (ROOT / "tests" / "realworld" / "sms.tsv")
        .read_text(encoding="utf-8", errors="replace").splitlines() if "\t" in l)
       if lab in ("ham", "spam")]
sms_train, sms_test = split(sms, 0.8, 42)

seed = load_jsonl(ROOT / "data" / "seed_documented_cases.jsonl")
seed_train, seed_test = split(seed, 0.7, 42)

s_tr, s_dv, _ = make_dataset(n_per_class=300, seed=42)
synthetic = list(s_tr) + list(s_dv)

phone_test = seed_test + load_jsonl(ROOT / "ood_adversarial_testset.jsonl") \
    + load_jsonl(ROOT / "tests" / "redteam_set.jsonl")


def balanced(pool, n_per_class, seed):
    pos = [x for x in pool if x[1] == 1]; neg = [x for x in pool if x[1] == 0]
    rng = random.Random(seed)
    rng.shuffle(pos); rng.shuffle(neg)
    return pos[:n_per_class] + neg[:n_per_class]


sms_bal = balanced(sms_train, 300, 7)      # keep SMS from dominating the mix

MIXES = {
    "synthetic only":            synthetic,
    "SMS only (balanced)":       sms_bal,
    "synthetic + seed":          synthetic + seed_train,
    "synth + seed + SMS (ALL)":  synthetic + seed_train + sms_bal,
}


def train(data):
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4),
                          min_df=2, sublinear_tf=True)
    clf = LogisticRegression(max_iter=2000, C=2.0)
    clf.fit(vec.fit_transform([t for t, _ in data]), [y for _, y in data])
    return lambda t: float(clf.predict_proba(vec.transform([t])[0:1])[0, 1])


def evaluate(prob, data):
    y = [lab for _, lab in data]
    p = [prob(t) for t, _ in data]
    pred = [1 if x >= 0.5 else 0 for x in p]
    tp = sum(a and b for a, b in zip(pred, y)); fp = sum(a and not b for a, b in zip(pred, y))
    tn = sum(not a and not b for a, b in zip(pred, y)); fn = sum(not a and b for a, b in zip(pred, y))
    auc = roc_auc_score(y, p) if len(set(y)) > 1 else float("nan")
    acc = (tp + tn) / len(y)
    rec = tp / (tp + fn) if tp + fn else 0.0
    fa = fp / (tn + fp) if tn + fp else 0.0
    return auc, acc, rec, fa


print(f"held-out: real SMS {len(sms_test)} | phone-scam {len(phone_test)}\n")
hdr = f"{'training mix':26} | {'SMS AUC':>7} {'acc':>6} {'rec':>6} {'FA':>6} | " \
      f"{'PHONE AUC':>9} {'acc':>6} {'rec':>6} {'FA':>6}"
print(hdr); print("-" * len(hdr))
for name, data in MIXES.items():
    prob = train(data)
    sa, sacc, srec, sfa = evaluate(prob, sms_test)
    pa, pacc, prec_, pfa = evaluate(prob, phone_test)
    print(f"{name:26} | {sa:7.3f} {sacc:6.1%} {srec:6.1%} {sfa:6.1%} | "
          f"{pa:9.3f} {pacc:6.1%} {prec_:6.1%} {pfa:6.1%}")

print("\nAll-rounder = the row that stays strong in BOTH halves. Specialists")
print("win one half and collapse in the other (watch SMS-only on phone).")
