"""Security controls — auth, rate limiting, size caps, webhook auth, audit.

Enterprise hardening, all stdlib-only so it stays CI-safe:
  * Multi-key / per-tenant API auth with zero-downtime rotation.
  * Rate limiting with a pluggable backend — in-process by default, a
    shared Redis window when DHVANI_REDIS_URL is set (multi-replica DoS
    resistance); fails safe to in-process if Redis is unavailable.
  * Twilio request-signature validation for the otherwise-open webhook.
  * Request/upload size caps.
  * Startup audit that refuses to silently ship an insecure config.

Config (all optional; secure-by-configuration):
  DHVANI_API_KEY            single key (back-compat)
  DHVANI_API_KEYS           "tenantA:keyA,tenantB:keyB" — many valid at once
  DHVANI_RATE_LIMIT / _WINDOW   requests / seconds
  DHVANI_MAX_TEXT_CHARS / DHVANI_MAX_UPLOAD_BYTES
  DHVANI_REDIS_URL          shared rate-limit store across replicas
  DHVANI_TWILIO_AUTH_TOKEN  enables webhook signature validation
  DHVANI_STRICT=1           refuse to start with an insecure config
"""
import base64
import hashlib
import hmac
import os
import threading
import time
from collections import defaultdict, deque

from fastapi import Header, HTTPException, Request


class SlidingWindowLimiter:
    """In-process per-key sliding window. Correct for a single instance."""

    def __init__(self, limit: int, window_s: int):
        self.limit = limit
        self.window_s = window_s
        self._hits: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> tuple[bool, float]:
        now = time.time()
        with self._lock:
            dq = self._hits[key]
            cutoff = now - self.window_s
            while dq and dq[0] < cutoff:
                dq.popleft()
            if len(dq) >= self.limit:
                return False, round(dq[0] + self.window_s - now, 1)
            dq.append(now)
            return True, 0.0


class RedisSlidingWindow:
    """Distributed per-key sliding window (Redis sorted set), shared across
    replicas. Fails OPEN on any Redis error so a store outage cannot take the
    service down."""

    def __init__(self, url: str, limit: int, window_s: int):
        import redis  # guarded: imported only when configured
        self._r = redis.Redis.from_url(url, socket_timeout=0.25)
        self._r.ping()
        self.limit = limit
        self.window_s = window_s

    def check(self, key: str) -> tuple[bool, float]:
        now = time.time()
        try:
            k = f"rl:{key}"
            p = self._r.pipeline()
            p.zremrangebyscore(k, 0, now - self.window_s)
            p.zadd(k, {f"{now}:{os.getpid()}": now})
            p.zcard(k)
            p.expire(k, self.window_s + 1)
            count = p.execute()[2]
            return (count <= self.limit), (0.0 if count <= self.limit else float(self.window_s))
        except Exception:
            return True, 0.0            # fail open on store errors


# --- config (rebuilt by reload_config) ---
API_KEYS: dict = {}
RATE_LIMIT = 120
RATE_WINDOW_S = 60
MAX_TEXT_CHARS = 20000
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
limiter = SlidingWindowLimiter(RATE_LIMIT, RATE_WINDOW_S)


def _load_keys() -> dict:
    keys = {}
    single = os.getenv("DHVANI_API_KEY")
    if single:
        keys[single] = "default"
    for part in os.getenv("DHVANI_API_KEYS", "").split(","):
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            tenant, k = part.split(":", 1)
            keys[k.strip()] = tenant.strip()
        else:
            keys[part] = "unnamed"
    return keys


def reload_config() -> None:
    global API_KEYS, RATE_LIMIT, RATE_WINDOW_S, MAX_TEXT_CHARS, MAX_UPLOAD_BYTES, limiter
    API_KEYS = _load_keys()
    RATE_LIMIT = int(os.getenv("DHVANI_RATE_LIMIT", "120"))
    RATE_WINDOW_S = int(os.getenv("DHVANI_RATE_WINDOW", "60"))
    MAX_TEXT_CHARS = int(os.getenv("DHVANI_MAX_TEXT_CHARS", "20000"))
    MAX_UPLOAD_BYTES = int(os.getenv("DHVANI_MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
    url = os.getenv("DHVANI_REDIS_URL")
    if url:
        try:
            limiter = RedisSlidingWindow(url, RATE_LIMIT, RATE_WINDOW_S)
            return
        except Exception:
            pass                         # Redis unavailable -> safe fallback
    limiter = SlidingWindowLimiter(RATE_LIMIT, RATE_WINDOW_S)


reload_config()


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Auth is OFF while no keys are configured (dev). With any key set, a
    matching X-API-Key is required. Multiple keys are valid at once, which is
    what makes zero-downtime rotation possible (add new, drain old, remove)."""
    if not API_KEYS:
        return
    if not x_api_key or x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="invalid or missing API key")


def tenant_for(x_api_key: str | None) -> str | None:
    return API_KEYS.get(x_api_key or "")


def validate_twilio(url: str, params: dict, signature: str, token: str) -> bool:
    """Twilio request-signature check: HMAC-SHA1 over the full URL followed by
    each POST param name+value in sorted order, base64-encoded."""
    payload = url + "".join(f"{k}{params[k]}" for k in sorted(params))
    mac = hmac.new(token.encode(), payload.encode("utf-8"), hashlib.sha1).digest()
    expected = base64.b64encode(mac).decode()
    return hmac.compare_digest(expected, signature or "")


def client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def startup_audit() -> list[str]:
    from shield import receipt
    warnings = []
    if not API_KEYS:
        warnings.append("API authentication is DISABLED (no DHVANI_API_KEY / DHVANI_API_KEYS)")
    if receipt._key() == b"dev-demo-key-change-in-prod":
        warnings.append("DHVANI_RECEIPT_KEY is the default demo key — receipts are FORGEABLE")
    return warnings


def enforce_or_warn(log) -> list[str]:
    warnings = startup_audit()
    for w in warnings:
        log(w)
    if os.getenv("DHVANI_STRICT") == "1" and warnings:
        raise RuntimeError("DHVANI_STRICT=1 but insecure config: " + "; ".join(warnings))
    return warnings
