"""Scam-categoriser tests — right scenario, right advice.

Verifies the categoriser routes representative scams to the correct family
and that the guidance is genuinely tailored (digital-arrest advice differs
from sextortion advice, etc.). CI-safe, no network.
"""
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shield.categories import categorize, CATEGORIES   # noqa: E402

CASES = [
    ("This is Inspector from CBI, you are under digital arrest, transfer money to clear the case", "digital_arrest"),
    ("Your account will be blocked, update your KYC, share your card number and CVV on this link", "kyc_phishing"),
    ("I recorded you on the video call, pay ten thousand or I send it to all your contacts", "sextortion"),
    ("You took a loan on our app, pay now or we message all your contacts you are a defaulter", "loan_harassment"),
    ("Congratulations you won a lottery, pay the processing fee to release the prize money", "lottery_prize"),
    ("Install AnyDesk and share your screen so I can fix the problem in your bank account", "tech_support"),
    ("Your parcel at customs contains drugs, I am connecting you to the police officer", "courier_customs"),
    ("Your electricity connection will be disconnected tonight unless you pay immediately", "utility_disconnection"),
    ("Send USDT to this wallet and get double back guaranteed within one hour", "investment_crypto"),
    ("Papa I had an accident and I am at the police station, send money urgently, do not tell anyone", "impersonation_family"),
]


def main() -> None:
    correct = 0
    print(f"{'expected':22} {'got':22} action-first?")
    for text, expected in CASES:
        r = categorize(text)
        ok = r["category"] == expected
        correct += ok
        tailored = r["action"]["en"] != CATEGORIES["generic_scam"]["action"]["en"]
        print(f"{expected:22} {r['category']:22} {'✓' if ok else '✗'}"
              f"  {'tailored' if tailored else 'generic'}")

    # tailoring: different scams must yield different advice
    a_arrest = categorize(CASES[0][0])["action"]["en"]
    a_sext = categorize(CASES[2][0])["action"]["en"]
    tailored_ok = a_arrest != a_sext

    passed = correct >= 8 and tailored_ok
    print(f"\ncategorised {correct}/{len(CASES)} correctly | "
          f"advice differs by scam type: {tailored_ok}")
    print("RESULT:", "CATEGORISER PASS" if passed else "FAILED")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
