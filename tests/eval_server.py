"""Deployment tests — the API contract, verified."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient  # noqa: E402
from server import app                      # noqa: E402
from tests.data import SCAM                 # noqa: E402
from shield.meter import meter              # noqa: E402

c = TestClient(app)


def main() -> None:
    ok = c.get("/health").json()["ok"]

    r = c.post("/v1/check", json={"text": SCAM[0], "lang": "hi"}).json()
    ok &= r["verdict"] == "HIGH_RISK"
    ok &= r["meter"]["pressures"]["Isolation"] > 0
    ok &= r["meter"]["pressures"]["Financial pull"] > 0
    ok &= "1930" in r["accessibility"]["picto"].replace("1️⃣9️⃣3️⃣0️⃣", "1930")
    ok &= "फोन" in r["accessibility"]["speech"]

    benign = "Hello, your furniture delivery is scheduled for Friday between 10 and 12."
    r2 = c.post("/v1/check", json={"text": benign}).json()
    ok &= r2["verdict"] == "NO_PATTERN"
    ok &= r2["meter"]["overall"] == 0

    wa = c.post("/webhook/whatsapp", data={"Body": SCAM[2]})
    ok &= wa.status_code == 200 and "🔴" in wa.text and "█" in wa.text
    wa2 = c.post("/webhook/whatsapp", data={"Body": ""})
    ok &= "Namaste" in wa2.text

    m = meter(SCAM[0])
    ok &= m["overall"] >= 50
    print("health ✓ | scam→RED with meter ✓ | benign→green, meter 0 ✓ | "
          "WhatsApp webhook ✓ | onboarding message ✓")
    print("RESULT:", "DEPLOYMENT CHECKS PASS" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
