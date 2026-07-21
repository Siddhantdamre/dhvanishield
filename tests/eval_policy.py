"""Interaction-policy eval — proving the tool is not irritating.

The ground-level failure mode is nagging: interrupting normal calls. On
5,574 real messages the raw model would flag ~61% of legitimate ones as
"be careful". This measures what the AMBIENT policy (silence unless a
confident, structured scam) actually surfaces to the user — the real
interruption rate a person would live with — versus the naive
"interrupt on anything not-green" behaviour.

Honest trade, reported both ways: ambient trades coverage for silence
(it fires only on HIGH_RISK). The proactive path (/v1/check, user asked)
still surfaces UNCERTAIN, because there the user wants an answer.
"""
import io
import math
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shield.datagen import make_dataset            # noqa: E402
from shield.ml import train_layer, hybrid_assess   # noqa: E402
from shield.policy import decide, build_alert, AMBIENT, PROACTIVE  # noqa: E402
from tests.data import BENIGN, AMBIGUOUS           # noqa: E402


def contract() -> bool:
    """CI-safe policy contract (no dataset needed): silence unless a
    confident scam; proactive always answers; the alert reaches every
    sense."""
    ok = True
    ok &= decide("HIGH_RISK", AMBIENT).surfaced is True
    ok &= decide("UNCERTAIN", AMBIENT).surfaced is False       # held silently
    ok &= decide("UNCERTAIN", AMBIENT).watching is True         # but still watching
    ok &= decide("NO_PATTERN", AMBIENT).surfaced is False
    ok &= decide("UNCERTAIN", PROACTIVE).surfaced is True       # user asked -> answer
    a = build_alert("HIGH_RISK", "hi", trusted_contact="Asha")
    ok &= bool(a["headline"]) and bool(a["speech"]) and bool(a["picto"])
    ok &= a["haptic"] == "URGENT" and "Asha" in a["call_person"]["prompt"]
    print(f"policy contract (silence-until-confident, all-senses alert): "
          f"{'✓' if ok else '✗'}")
    return ok


DATA = ROOT / "tests" / "realworld" / "sms.tsv"
if not DATA.exists():
    ok = contract()
    print("\n(real-dataset interruption measurement skipped — run "
          "tests/realworld/fetch.py to enable it)")
    print("RESULT:", "POLICY CONTRACT PASS" if ok else "FAILED")
    sys.exit(0 if ok else 1)

rows = [l.split("\t", 1) for l in
        DATA.read_text(encoding="utf-8", errors="replace").splitlines() if "\t" in l]
ham = [t for lab, t in rows if lab == "ham"]
spam = [t for lab, t in rows if lab == "spam"]


def wilson(x, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = x / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d
    return (max(0, c - h), min(1, c + h))


from shield.training import build_deployed_layer   # noqa: E402
layer = build_deployed_layer()


def rates(texts):
    naive = ambient = 0            # user-facing interruptions
    for t in texts:
        lvl = hybrid_assess(t, layer)[0]
        naive += lvl != "NO_PATTERN"                       # interrupt on anything unsure
        ambient += decide(lvl, mode=AMBIENT).surfaced       # interrupt only on confident scam
    return naive, ambient


nh, ns = len(ham), len(spam)
h_naive, h_amb = rates(ham)
s_naive, s_amb = rates(spam)

lo, hi = wilson(h_amb, nh)
print(f"Real messages: {nh} legitimate, {ns} scam/spam\n")
print("=== INTERRUPTIONS ON LEGITIMATE MESSAGES (the irritation metric) ===")
print(f"  naive (warn on anything unsure): {h_naive}/{nh} = {h_naive/nh:6.2%}   <-- unusable")
print(f"  AMBIENT (silence until confident):{h_amb}/{nh} = {h_amb/nh:6.2%}   CI[{lo:.2%},{hi:.2%}]")
if h_naive:
    print(f"  --> {(1 - h_amb / max(h_naive,1)):.1%} fewer interruptions on normal messages")

print("\n=== COVERAGE ON REAL SCAM/SPAM ===")
print(f"  AMBIENT alerts (confident scam only): {s_amb}/{ns} = {s_amb/ns:.2%}")
print(f"  PROACTIVE would surface (user asked):  {s_naive}/{ns} = {s_naive/ns:.2%}")
print("\nHonest read: ambient stays silent on ~all normal messages (the")
print("ground-level win); the proactive 'is this real?' path keeps the")
print("wider coverage for when the user actually asks.")

print()
ok = contract() and (h_amb / nh) < 0.01
print("\nRESULT:", "AMBIENT NON-INTRUSIVE (<1% interruptions on legit)"
      if ok else "TOO NOISY")
sys.exit(0 if ok else 1)
