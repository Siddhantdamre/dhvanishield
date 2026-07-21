# DhvaniShield for Enterprises

## The feature that changes the buying conversation
Most scam tools sell *detection*. A bank's real exposure is *liability* —
regulators increasingly expect institutions to warn customers, and scam
disputes turn on a single question: **"was the customer warned?"**

DhvaniShield answers it with proof. Every assessment issues a
**Duty-of-Care Warning Receipt** (`shield/receipt.py`, returned by
`/v1/check`, checked by `/v1/receipt/verify`):

- **Tamper-proof** — HMAC-signed; editing any field (even flipping
  `warned` to false) invalidates it. A bank cannot forge it, and neither
  can anyone else.
- **Content-free / DPDP-safe** — it stores a keyed *hash* of the message,
  never the message. So it proves *which* message was assessed without
  retaining anything sensitive. Zero new privacy liability.
- **Non-repudiable & verifiable** — a regulator or a dispute-resolution
  body can verify a receipt is authentic and that a given message is the
  exact one assessed.

What a bank can present in a dispute or audit:
```
receipt_id  3859f471476ffab2
verdict     HIGH_RISK
scam_type   digital_arrest
warned      true
issued_at   2026-07-15T12:10:40Z
```
Nobody else in this space frames scam detection as a **compliance asset**.
That's the wedge into a bank's budget — it maps to risk and P&L, not just
a nicer UX.

## Why the rest of it is already enterprise-ready
- **Drop-in API** — `POST /v1/check` returns verdict, scam category,
  tailored guidance, accessibility renderings, and the receipt. One call.
- **Runs anywhere, cheaply** — on-device / on-prem capable, ~7 MB model,
  CPU-only, no GPU, no per-call cloud AI cost. ~143 req/s per node,
  ~13 ms per call; scales horizontally (stateless).
- **Privacy by architecture** — process-and-delete, content-free telemetry,
  consent-gated data (`PRIVACY.md`) — a bank's DPO can sign off.
- **Auditable, not a black box** — every verdict names the words and the
  scam family it matched (`THREAT_MODEL.md`).
- **Observability built in** — `/metrics` (Prometheus), structured logs,
  `/healthz` + `/readyz`, API-key auth, rate limiting (`shield/security.py`).
- **Accessible + vernacular** — six disability profiles, en/hi/mr — reaches
  the customers a bank is most criticised for failing.
- **Verified** — `python tests/run_all.py` → all suites green, on every push.

## Deployment
See `SCALING.md`. Containerised (`Dockerfile`), stateless, HTTPS behind the
bank's own gateway. Production hardening: set `DHVANI_API_KEY` and
`DHVANI_RECEIPT_KEY`; move the rate limiter to Redis for multi-replica; swap
the receipt HMAC for an asymmetric signature (Ed25519) so a regulator can
verify receipts without holding the signing key.
