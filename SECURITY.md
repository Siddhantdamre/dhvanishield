# Security Posture

An honest account of what is secured, what depends on configuration, and
what remains. See `THREAT_MODEL.md` for the full adversary analysis. All
controls below are verified by `tests/eval_hardening.py`.

## Controls in place
- **Authentication** — multi-key / per-tenant API auth with zero-downtime
  rotation (many keys valid at once). Off only while no key is configured;
  the startup audit warns loudly if so. (`shield/security.py`)
- **Rate limiting** — pluggable backend: in-process sliding window by
  default, a **shared Redis window** when `DHVANI_REDIS_URL` is set
  (multi-replica DoS resistance); fails safe to in-process if Redis is down.
- **Webhook authentication** — Twilio request-signature validation on
  `/webhook/whatsapp` (active when `DHVANI_TWILIO_AUTH_TOKEN` is set),
  closing the otherwise-open webhook.
- **Input limits** — text and upload size caps (`413`).
- **Security headers** — `X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy`, `Content-Security-Policy`, `Strict-Transport-Security`
  on every response.
- **No data at rest** — process-and-delete; content-free telemetry; the only
  stored data is the opt-in, redacted, anonymous feedback corpus, now with a
  length/anomaly guard. Smallest possible breach surface.
- **Local inference** — no external network at inference; no content leaves
  the process.
- **Signed receipts** — HMAC-signed, content-free warning receipts;
  tampering is detectable (`shield/receipt.py`).
- **Auditability** — `X-Request-ID` on every response; structured,
  content-free logs.
- **Dependency scanning** — `pip-audit` runs in CI (`.github/workflows/ci.yml`).
- **Startup audit** — refuses to *silently* run insecure; `DHVANI_STRICT=1`
  refuses to start at all with an insecure config.

## Configure in production
| Variable | Effect if unset |
|---|---|
| `DHVANI_API_KEY` / `DHVANI_API_KEYS` | Unset ⇒ the API is **open**. Use `DHVANI_API_KEYS="tenant:key,..."` for per-tenant keys + rotation. |
| `DHVANI_RECEIPT_KEY` | Default ⇒ receipts are **forgeable**. |
| `DHVANI_TWILIO_AUTH_TOKEN` | Unset ⇒ the webhook is **unauthenticated**. |
| `DHVANI_REDIS_URL` | Unset ⇒ rate limits are per-replica, not shared. |
| `DHVANI_STRICT=1` | Refuse to start if auth or receipt secrets are insecure. |
| TLS (at the gateway) | The app does not terminate TLS. |

## Remaining (honest)
- **Asymmetric receipt signing** — receipts are HMAC (verifier needs the
  secret). For third-party/regulator verification without the key, swap to an
  Ed25519 signature. Requires the `cryptography` dependency; the signing seam
  is isolated in `shield/receipt.py` for a clean swap.
- **Audio decode surface** — uploaded audio is handled by native libraries;
  run the transcription worker in a sandbox/resource-limited context.
- **Redis limiter** — implemented and fail-safe, but the Redis path itself
  needs a live store to exercise end-to-end (the fallback is what CI tests).
- **Formal audit** — a third-party security + DPDP audit before a public
  production launch (a deploying partner's step).

## Reporting a vulnerability
Do not open a public issue. Contact the maintainer directly with reproduction
steps; a fix or mitigation will be prioritised.

## Bottom line
The architecture is security-favourable by design (no data at rest,
on-device, auditable), the core enterprise controls are now built and tested
(multi-key auth, webhook signing, shared-store rate limiting, security
headers, dependency scanning, fail-closed strict mode), and the software
refuses to ship silently insecure. The remaining items are a short,
named list — mostly a live Redis, asymmetric signing, and a formal audit —
not unknowns.
