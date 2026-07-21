"""Output reliability — can you DEPEND on what the system returns?

Not a feature test; a dependability test of the visible output along four
axes a consumer actually relies on:

  1. DETERMINISM      same input -> identical verdict, run to run and across
                      a freshly rebuilt model (no hidden randomness).
  2. CONSISTENCY      every surface agrees: /v1/check, /v1/screen and the
                      direct model give the same verdict; screen surfaces
                      iff HIGH_RISK; a category appears iff it is a scam.
  3. ROBUSTNESS       degenerate/messy input never crashes and never yields
                      a false 'safe'; obvious scams are never NO_PATTERN.
  4. CONTRACT         the response shape and types are stable and bounded.

CI-safe, no network. Non-ASCII probes are written as escapes so the source
parses identically on any platform encoding.
"""
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient                       # noqa: E402
import server                                                   # noqa: E402
from shield.training import build_deployed_layer                # noqa: E402
from shield.ml import hybrid_assess                             # noqa: E402

c = TestClient(server.app)
VALID = {"HIGH_RISK", "UNCERTAIN", "NO_PATTERN"}
layer = build_deployed_layer()

SCAMS = [
    "This is CBI, you are under digital arrest, do not tell anyone, transfer money to the safe account",
    "Your account will be blocked, share your card number, CVV and the OTP to update KYC",
    "I recorded your video call, pay ten thousand or I send it to all your contacts",
]
BENIGNS = [
    "Hi, your furniture delivery is scheduled for Friday between 10 and 12",
    "Your OTP for the Flipkart order is 4471, do not share it with anyone",
    "Namaste, aapke loan ki EMI kal due hai, kripya samay par payment kar dijiye",
]
DEGENERATE = ["", " ", "\n\t  ", "\U0001F600\U0001F600\U0001F600",
              "1234567890", "!!!???...,,,", "aaaaaaaaaaaaaaaaaaaa",
              "  test control", "अ आ इ ई",
              "CBI " * 300]


def check(text):
    return c.post("/v1/check", json={"text": text})


# 1. determinism
layer2 = build_deployed_layer()
det = all(hybrid_assess(t, layer)[0] == hybrid_assess(t, layer)[0]
          and hybrid_assess(t, layer)[0] == hybrid_assess(t, layer2)[0]
          for t in SCAMS + BENIGNS)
print(f"1. determinism  (same input -> same verdict, incl. rebuilt model): "
      f"{'PASS' if det else 'FAIL'}")

# 2. cross-surface consistency
cons = True
for t in SCAMS + BENIGNS:
    r = check(t).json()
    v = r["verdict"]
    s = c.post("/v1/screen", json={"text": t}).json()
    cons &= v in VALID
    cons &= v == hybrid_assess(t, layer)[0]                 # server == direct model
    cons &= s["surfaced"] == (v == "HIGH_RISK")             # ambient fires iff RED
    cons &= (r["category"] is not None) == (v != "NO_PATTERN")
print(f"2. consistency  (check == screen == model; category iff scam): "
      f"{'PASS' if cons else 'FAIL'}")

# 3. robustness / graceful degradation
robust = True
for t in DEGENERATE:
    resp = check(t)
    if resp.status_code == 413:            # oversized -> capped, still graceful
        continue
    if resp.status_code != 200 or resp.json().get("verdict") not in VALID:
        robust = False
robust &= all(hybrid_assess(t, layer)[0] != "NO_PATTERN" for t in SCAMS)
print(f"3. robustness   (messy input never crashes / never false-safe): "
      f"{'PASS' if robust else 'FAIL'}")

# 4. output contract
r = check(SCAMS[0]).json()
try:
    contract = (
        r["verdict"] in VALID
        and isinstance(r["meter"]["overall"], int) and 0 <= r["meter"]["overall"] <= 100
        and isinstance(r["explanation"], list)
        and (r["category"] is None or isinstance(r["category"], dict))
        and isinstance(r["accessible"]["call_person"]["prompt"], str)
        and isinstance(r["accessible"]["shape"], str)
    )
except (KeyError, TypeError):
    contract = False
print(f"4. contract     (stable, typed, bounded response shape): "
      f"{'PASS' if contract else 'FAIL'}")

passed = det and cons and robust and contract
print("\nRESULT:", "OUTPUT RELIABILITY PASS" if passed else "FAILED")
sys.exit(0 if passed else 1)
