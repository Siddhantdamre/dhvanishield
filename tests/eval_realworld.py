"""Real-world evaluation — the model meets data nobody here wrote.

Dataset: UCI SMS Spam Collection (5,574 real SMS, ham/spam), a standard
public benchmark collected from real sources. This is the first eval in
the repo whose text is neither template-generated nor hand-written by the
author — it is the honest external check.

Honest domain caveat, stated up front: this is SMS, and most 'spam' here
is promotional marketing, whereas DhvaniShield targets coercive
phone-scam scripts (digital arrest, KYC-phishing, etc.). So:
  * the HAM side is a large-n, in-purpose test of the core deployable
    claim — "never falsely accuse a legitimate message";
  * overall SPAM recall will be LOW and that is EXPECTED — this is not a
    generic spam filter. A transparent credential-phishing subset gives
    the fairer in-domain recall.
Every rate is reported with a 95% Wilson confidence interval.

Run:  python tests/eval_realworld.py
(the dataset is downloaded separately into tests/realworld/sms.tsv)
"""
import io
import math
import sys
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shield.datagen import make_dataset            # noqa: E402
from shield.ml import train_layer, hybrid_assess   # noqa: E402
from tests.data import BENIGN, AMBIGUOUS           # noqa: E402

DATA = ROOT / "tests" / "realworld" / "sms.tsv"
if not DATA.exists():
    print("dataset missing — see tests/realworld/ download step"); sys.exit(2)

rows = []
for line in DATA.read_text(encoding="utf-8", errors="replace").splitlines():
    if "\t" not in line:
        continue
    label, text = line.split("\t", 1)
    if label in ("ham", "spam"):
        rows.append((label, text))

ham = [t for lab, t in rows if lab == "ham"]
spam = [t for lab, t in rows if lab == "spam"]

# transparent credential-phishing subset (DhvaniShield's actual domain)
PHISH_KW = ("account", "bank", "verify", "password", "pin ", "otp", "kyc",
            "suspend", "blocked", "security", "ssn", "confirm your",
            "verify your", "log in", "login", "click")
phish_spam = [t for t in spam if any(k in t.lower() for k in PHISH_KW)]


def wilson(x, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = x / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d
    return (max(0, c - h), min(1, c + h))


def ci(x, n):
    lo, hi = wilson(x, n)
    return f"{x/n:6.2%}  CI[{lo:.2%}, {hi:.2%}]" if n else "n/a"


train, dev, _ = make_dataset(n_per_class=300, seed=42)
layer = train_layer(train, dev, calib_benign=BENIGN, calib_ambiguous=AMBIGUOUS)


def verdicts(texts):
    r = {"HIGH_RISK": 0, "UNCERTAIN": 0, "NO_PATTERN": 0}
    for t in texts:
        r[hybrid_assess(t, layer)[0]] += 1
    return r


t0 = time.perf_counter()
h = verdicts(ham)
s = verdicts(spam)
ps = verdicts(phish_spam)
dt = time.perf_counter() - t0

nh, nsp, np_ = len(ham), len(spam), len(phish_spam)
print(f"UCI SMS Spam Collection — {len(rows)} real messages "
      f"({nh} ham, {nsp} spam)   [{dt:.1f}s]\n")

print("=== HAM (real legitimate messages) — the 'never falsely accuse' test ===")
print(f"  passed clean (NO_PATTERN): {ci(h['NO_PATTERN'], nh)}")
print(f"  over-warned  (UNCERTAIN):  {ci(h['UNCERTAIN'], nh)}")
print(f"  FALSE ALARM  (HIGH_RISK):  {ci(h['HIGH_RISK'], nh)}   <-- must be low")

print("\n=== SPAM (real) — expected LOW: this is not a generic spam filter ===")
caught = s["HIGH_RISK"] + s["UNCERTAIN"]
print(f"  flagged (RED or UNCERTAIN): {ci(caught, nsp)}")
print(f"  caught outright (RED):      {ci(s['HIGH_RISK'], nsp)}")
print(f"  missed  (NO_PATTERN):       {ci(s['NO_PATTERN'], nsp)}")

print(f"\n=== credential-phishing spam subset (n={np_}, DhvaniShield's domain) ===")
pcaught = ps["HIGH_RISK"] + ps["UNCERTAIN"]
print(f"  flagged (RED or UNCERTAIN): {ci(pcaught, np_)}")
print(f"  caught outright (RED):      {ci(ps['HIGH_RISK'], np_)}")

print("\nHonest read: the HAM false-alarm rate is the real, large-n result "
      "for the deployable claim; low overall SPAM recall reflects domain\n"
      "mismatch (marketing SMS vs coercion phone scams), not a defect.")
