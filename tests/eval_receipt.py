"""Duty-of-care warning receipt tests — the enterprise/compliance feature.

Proves the properties a bank's compliance team needs:
  * authentic round-trip      — a genuine receipt verifies as authentic.
  * tamper-evident            — changing ANY field invalidates it.
  * content-match             — the original message maps to the receipt;
                                a different message does not.
  * content-free (DPDP-safe)  — the receipt never contains the raw message.
CI-safe, no network.
"""
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shield.receipt import issue, verify   # noqa: E402

MSG = "Your account will be blocked, share your card number and OTP on this link"


def main() -> None:
    ok = True
    r = issue(MSG, "HIGH_RISK", "kyc_phishing", warned=True,
              issued_at="2026-01-05T14:32:00Z")

    # 1. authentic round-trip
    v = verify(r, MSG)
    auth = v["authentic"] and not v["tampered"] and v["content_matches"]
    ok &= auth
    print(f"authentic round-trip (signature + content match): {'PASS' if auth else 'FAIL'}")

    # 2. tamper-evident: flip 'warned' true->false (the field a bank would fake)
    forged = dict(r); forged["warned"] = False
    tamper = verify(forged)["tampered"] is True
    ok &= tamper
    print(f"tamper-evident (editing 'warned' invalidates it): {'PASS' if tamper else 'FAIL'}")

    # 3. tamper-evident: change the scam type
    forged2 = dict(r); forged2["scam_type"] = "generic_scam"
    ok &= verify(forged2)["tampered"] is True

    # 4. content-match: a DIFFERENT message must not match this receipt
    mism = verify(r, "hi mom, running late for dinner")["content_matches"] is False
    ok &= mism
    print(f"content-match (wrong message does NOT match): {'PASS' if mism else 'FAIL'}")

    # 5. content-free: the raw message must never appear in the receipt
    blob = str(r).lower()
    content_free = ("card number" not in blob and "otp" not in blob
                    and "blocked" not in blob)
    ok &= content_free
    print(f"content-free (DPDP-safe; only a hash is stored): {'PASS' if content_free else 'FAIL'}")

    # what a bank actually gets to present in a dispute
    print(f"\nreceipt a bank can present: id={r['receipt_id']} "
          f"verdict={r['verdict']} type={r['scam_type']} warned={r['warned']} "
          f"at={r['issued_at']}")

    print("\nRESULT:", "WARNING RECEIPT VERIFIED" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
