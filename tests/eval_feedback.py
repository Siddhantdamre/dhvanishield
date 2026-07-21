"""Feedback-loop tests — consent, redaction, and the flywheel closing.

CI-safe: uses a temp corpus path (DHVANI_CORPUS_PATH), no network. Verifies
the privacy contract (nothing stored without consent; PII redacted) and
that stored examples load back as training data.
"""
import io
import os
import sys
import tempfile
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# isolate the corpus to a temp file BEFORE importing the module's callers
_tmp = Path(tempfile.mkdtemp()) / "corpus.jsonl"
os.environ["DHVANI_CORPUS_PATH"] = str(_tmp)

from shield.feedback import (record_feedback, corpus_stats,          # noqa: E402
                            load_corpus_as_training, clear_corpus, redact)


def main() -> None:
    ok = True

    # 1) NO consent -> nothing stored (the privacy default)
    r = record_feedback("I am from CBI, transfer money", "HIGH_RISK",
                        is_scam=True, consent=False)
    ok &= r["stored"] is False and not _tmp.exists()
    print(f"no-consent stores nothing: {'✓' if ok else '✗'}")

    # 2) consent -> stored, and PII/secrets redacted
    pii = ("Share the OTP 483920 and call me on +91 98765 43210 or "
           "mail scam@fraud.co to release your account 000123456789")
    r = record_feedback(pii, "UNCERTAIN", is_scam=True, consent=True)
    stored = _tmp.read_text(encoding="utf-8")
    red_ok = (r["stored"] and "483920" not in stored and "98765" not in stored
              and "scam@fraud.co" not in stored and "000123456789" not in stored
              and "<NUM>" in stored)
    ok &= red_ok
    print(f"consent stores + redacts PII (OTP/phone/email/account): {'✓' if red_ok else '✗'}")

    # 3) a benign human label + a model MISS are recorded for error analysis
    record_feedback("your parcel is out for delivery", "NO_PATTERN",
                    is_scam=False, consent=True)
    record_feedback("polite bank-safety scam that model missed", "NO_PATTERN",
                    is_scam=True, consent=True)   # human says scam, model said green
    s = corpus_stats()
    stats_ok = (s["total"] == 3 and s["scam"] == 2 and s["benign"] == 1
                and s["model_misses"] == 1)
    ok &= stats_ok
    print(f"stats + model-miss signal ({s['model_misses']} miss captured): "
          f"{'✓' if stats_ok else '✗'}")

    # 4) the flywheel closes: corpus loads back as training pairs
    pairs = load_corpus_as_training()
    train_ok = len(pairs) == 3 and all(isinstance(t, str) and l in (0, 1)
                                       for t, l in pairs)
    ok &= train_ok
    print(f"corpus loads as training data ({len(pairs)} pairs): {'✓' if train_ok else '✗'}")

    # 5) erasure works (DPDP)
    n = clear_corpus()
    erase_ok = n == 3 and not _tmp.exists()
    ok &= erase_ok
    print(f"erasure removes the corpus: {'✓' if erase_ok else '✗'}")

    print("\nRESULT:", "FEEDBACK-LOOP CHECKS PASS" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
