"""Hardening tests — API-key auth, rate limiting, size caps, metrics.

These verify the production controls added around the (unchanged)
classifier. Config is environment-driven, so we set env vars, call
security.reload_config(), and build a fresh TestClient per scenario.
"""
import importlib
import io
import os
import sys
from pathlib import Path

# UTF-8 stdout so the check marks never crash on a Windows cp1252 console.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient  # noqa: E402

BENIGN = "Hello, your furniture delivery is scheduled for Friday between 10 and 12."


def _client():
    """Fresh app + reloaded security config for the current environment."""
    import shield.security as security
    importlib.reload(security)
    import server
    importlib.reload(server)
    return server, TestClient(server.app)


def test_metrics_and_probes() -> bool:
    for k in ("DHVANI_API_KEY", "DHVANI_RATE_LIMIT", "DHVANI_MAX_TEXT_CHARS"):
        os.environ.pop(k, None)
    server, c = _client()
    ok = c.get("/healthz").json()["ok"] is True
    ok &= c.get("/readyz").json()["ready"] is True
    c.post("/v1/check", json={"text": BENIGN})            # generate one datapoint
    body = c.get("/metrics").text
    ok &= "dhvani_requests_total" in body
    ok &= "dhvani_latency_ms_p95" in body
    ok &= 'dhvani_verdicts_total{verdict="NO_PATTERN"}' in body
    snap = c.get("/metrics.json").json()
    ok &= snap["requests_total"] >= 1 and snap["verdicts"].get("NO_PATTERN", 0) >= 1
    # X-Request-ID is stamped on every response
    ok &= "x-request-id" in {k.lower() for k in c.get("/healthz").headers}
    print(f"metrics + probes: {'✓' if ok else '✗'}")
    return ok


def test_auth() -> bool:
    os.environ["DHVANI_API_KEY"] = "secret-test-key"
    os.environ.pop("DHVANI_RATE_LIMIT", None)
    server, c = _client()
    unauth = c.post("/v1/check", json={"text": BENIGN})
    good = c.post("/v1/check", json={"text": BENIGN},
                  headers={"X-API-Key": "secret-test-key"})
    wrong = c.post("/v1/check", json={"text": BENIGN},
                   headers={"X-API-Key": "nope"})
    # webhook must stay open (Twilio cannot send our header)
    wa = c.post("/webhook/whatsapp", data={"Body": "hi"})
    ok = (unauth.status_code == 401 and good.status_code == 200
          and wrong.status_code == 401 and wa.status_code == 200)
    del os.environ["DHVANI_API_KEY"]
    print(f"api-key auth (401 without / 200 with / webhook open): {'✓' if ok else '✗'}")
    return ok


def test_rate_limit() -> bool:
    os.environ.pop("DHVANI_API_KEY", None)
    os.environ["DHVANI_RATE_LIMIT"] = "3"
    os.environ["DHVANI_RATE_WINDOW"] = "60"
    server, c = _client()
    codes = [c.post("/v1/check", json={"text": BENIGN}).status_code
             for _ in range(5)]
    ok = codes.count(200) == 3 and codes.count(429) == 2
    limited = c.post("/v1/check", json={"text": BENIGN})
    ok &= "retry-after" in {k.lower() for k in limited.headers}
    del os.environ["DHVANI_RATE_LIMIT"], os.environ["DHVANI_RATE_WINDOW"]
    print(f"rate limit (3 ok, then 429 + Retry-After): {'✓' if ok else '✗'}")
    return ok


def test_size_cap() -> bool:
    os.environ.pop("DHVANI_API_KEY", None)
    os.environ["DHVANI_MAX_TEXT_CHARS"] = "50"
    os.environ.pop("DHVANI_RATE_LIMIT", None)
    server, c = _client()
    small = c.post("/v1/check", json={"text": "short call"})
    big = c.post("/v1/check", json={"text": "x" * 200})
    ok = small.status_code == 200 and big.status_code == 413
    del os.environ["DHVANI_MAX_TEXT_CHARS"]
    print(f"size cap (413 over limit): {'✓' if ok else '✗'}")
    return ok


def test_multikey_rotation() -> bool:
    """Multiple API keys valid at once (per-tenant + zero-downtime rotation)."""
    os.environ.pop("DHVANI_API_KEY", None)
    os.environ.pop("DHVANI_RATE_LIMIT", None)
    os.environ["DHVANI_API_KEYS"] = "tenantA:keyA,tenantB:keyB"
    server, c = _client()
    a = c.post("/v1/check", json={"text": BENIGN}, headers={"X-API-Key": "keyA"}).status_code
    b = c.post("/v1/check", json={"text": BENIGN}, headers={"X-API-Key": "keyB"}).status_code
    bad = c.post("/v1/check", json={"text": BENIGN}, headers={"X-API-Key": "nope"}).status_code
    del os.environ["DHVANI_API_KEYS"]
    ok = a == 200 and b == 200 and bad == 401
    print(f"multi-key auth (2 tenants valid at once, rotation-ready): {'✓' if ok else '✗'}")
    return ok


def test_twilio_signature() -> bool:
    """Webhook rejects requests without a valid Twilio signature (when the
    auth token is configured)."""
    import base64, hashlib, hmac
    for k in ("DHVANI_API_KEY", "DHVANI_API_KEYS", "DHVANI_RATE_LIMIT"):
        os.environ.pop(k, None)
    os.environ["DHVANI_TWILIO_AUTH_TOKEN"] = "tok123"
    server, c = _client()
    url = "http://testserver/webhook/whatsapp"
    body = "hello there"
    payload = url + "".join(f"{k}{v}" for k, v in sorted({"Body": body}.items()))
    good_sig = base64.b64encode(
        hmac.new(b"tok123", payload.encode(), hashlib.sha1).digest()).decode()
    good = c.post("/webhook/whatsapp", data={"Body": body},
                  headers={"X-Twilio-Signature": good_sig}).status_code
    bad = c.post("/webhook/whatsapp", data={"Body": body},
                 headers={"X-Twilio-Signature": "forged"}).status_code
    del os.environ["DHVANI_TWILIO_AUTH_TOKEN"]
    ok = good == 200 and bad == 403
    print(f"twilio signature (valid=200, forged=403): {'✓' if ok else '✗'}")
    return ok


def test_security_headers() -> bool:
    for k in ("DHVANI_API_KEY", "DHVANI_API_KEYS", "DHVANI_RATE_LIMIT"):
        os.environ.pop(k, None)
    server, c = _client()
    h = {k.lower() for k in c.get("/healthz").headers}
    ok = {"x-content-type-options", "x-frame-options",
          "content-security-policy"} <= h
    print(f"security headers present on responses: {'✓' if ok else '✗'}")
    return ok


def test_security_defaults() -> bool:
    """The startup audit must flag insecure defaults (open auth / forgeable
    receipts) and go quiet once secrets are set."""
    import shield.security as security
    for k in ("DHVANI_API_KEY", "DHVANI_RECEIPT_KEY"):
        os.environ.pop(k, None)
    importlib.reload(security)
    insecure = len(security.startup_audit()) == 2          # both defaults flagged
    os.environ["DHVANI_API_KEY"] = "set"
    os.environ["DHVANI_RECEIPT_KEY"] = "set-secret"
    importlib.reload(security)
    secure = len(security.startup_audit()) == 0            # clean when configured
    del os.environ["DHVANI_API_KEY"], os.environ["DHVANI_RECEIPT_KEY"]
    importlib.reload(security)
    ok = insecure and secure
    print(f"startup audit flags insecure defaults, clears when configured: "
          f"{'✓' if ok else '✗'}")
    return ok


def main() -> None:
    ok = True
    ok &= test_metrics_and_probes()
    ok &= test_auth()
    ok &= test_rate_limit()
    ok &= test_size_cap()
    ok &= test_multikey_rotation()
    ok &= test_twilio_signature()
    ok &= test_security_headers()
    ok &= test_security_defaults()
    print("\nRESULT:", "HARDENING CHECKS PASS" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
