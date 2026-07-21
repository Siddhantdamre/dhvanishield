"""Duty-of-Care Warning Receipt — scam detection as a compliance asset.

The enterprise insight: a bank's biggest scam-related exposure is not
detection, it's LIABILITY. Regulators increasingly expect institutions to
warn customers, and disputes turn on "were you warned?". So the feature a
compliance officer actually wants is tamper-proof PROOF that a warning was
issued — at a given time, for a given message, of a given scam type.

This module issues such a receipt for every assessment:
  * tamper-evident   — HMAC-signed; any edit invalidates it.
  * content-free      — stores a keyed HASH of the message, never the text,
                        so it is DPDP-safe (nothing sensitive is retained)
                        yet can still prove a specific message maps to it.
  * non-repudiable    — only the issuer's key produces a valid signature.
  * verifiable        — anyone with the key (or, in production, the public
                        key) can verify authenticity and the content match.

Simple by design (stdlib hmac/hashlib, no deps). Production upgrade path:
swap the shared-secret HMAC for an asymmetric signature (e.g. Ed25519) so a
regulator can verify receipts without holding the signing key.
"""
import hashlib
import hmac
import json
import os
import time

ISSUER = "DhvaniShield"
VERSION = 1


def _key() -> bytes:
    return os.getenv("DHVANI_RECEIPT_KEY", "dev-demo-key-change-in-prod").encode()


def _fingerprint(text: str) -> str:
    """Keyed hash of the normalised message — proves 'this exact message was
    assessed' WITHOUT storing the message itself."""
    norm = " ".join((text or "").lower().split())
    return hmac.new(_key(), norm.encode("utf-8"), hashlib.sha256).hexdigest()[:32]


def _sign(payload: dict) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hmac.new(_key(), body, hashlib.sha256).hexdigest()


def issue(text: str, verdict: str, scam_type: str | None,
          warned: bool, issued_at: str | None = None) -> dict:
    """Issue a signed, content-free warning receipt for one assessment."""
    payload = {
        "issuer": ISSUER,
        "version": VERSION,
        "verdict": verdict,
        "scam_type": scam_type,
        "warned": bool(warned),
        "content_fingerprint": _fingerprint(text),
        "issued_at": issued_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    signature = _sign(payload)
    return {"receipt_id": signature[:16], **payload, "signature": signature}


def verify(receipt: dict, text: str | None = None) -> dict:
    """Verify a receipt's authenticity and (optionally) that a given message
    is the one it was issued for."""
    r = dict(receipt)
    sig = r.pop("signature", "")
    r.pop("receipt_id", None)
    valid = hmac.compare_digest(sig, _sign(r))
    out = {"authentic": valid, "tampered": not valid,
           "warned": receipt.get("warned"), "scam_type": receipt.get("scam_type"),
           "issued_at": receipt.get("issued_at")}
    if text is not None:
        out["content_matches"] = valid and hmac.compare_digest(
            receipt.get("content_fingerprint", ""), _fingerprint(text))
    return out
