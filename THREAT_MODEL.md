# Threat Model — DhvaniShield

Scope: the DhvaniShield service (`server.py`) and its classifier
(`shield/`). Method: asset identification → trust boundaries → adversary
enumeration → attack/mitigation mapping (STRIDE-aligned) → residual-risk
register. **Kerckhoffs assumption:** the registry and method are treated
as public; security must not depend on their secrecy.

## 1. Assets
| Asset | Why it matters |
|---|---|
| Verdict integrity (esp. the FRR=0 gate) | A single false "safe" can cost a victim their savings — the highest-value asset. |
| Call content in flight (transcript / audio) | Sensitive personal data; must never be persisted or logged (see `PRIVACY.md`). |
| Service availability | A helpline signal that is down protects no one. |
| Model behaviour / calibration | Extraction or poisoning could let attackers craft reliable bypasses. |
| Operator trust | False accusations or leaks destroy adoption. |

## 2. Trust boundaries & data flow
```
[caller/message] --untrusted--> [client/WhatsApp] --HTTPS--> [server.py]
                                                                 |
        rate-limit + size-cap + (optional) API-key  ------------+
                                                                 v
                          in-process classifier (L1+L2+L3)  --> verdict
                          (no disk, no external network, no logging of content)
```
- **Untrusted:** all request bodies (text, audio, webhook form fields).
  Treated as data, never as instructions.
- **Trusted-but-verified:** the reverse proxy / load balancer supplying
  `X-Forwarded-For` (single hop honoured).
- **Trusted:** the training templates baked into the image (integrity of
  these is a supply-chain concern — §4, Tampering).

## 3. Adversaries
1. **The scammer** — wants a scam call scored `NO_PATTERN` (evasion) or
   the tool discredited (induce false alarms).
2. **The abuser of the API** — wants free compute, data exfiltration, or
   denial of service.
3. **The insider / supply chain** — wants to poison training templates or
   the registry so specific scripts pass.
4. **The curious operator** — inadvertent over-collection of user data.

## 4. Attacks & mitigations (STRIDE)

### Spoofing / unauthorised access
- **Threat:** unauthenticated callers hammering `/v1/*`; forged webhook
  traffic.
- **Mitigations (built):** secure-by-config API-key auth on `/v1/check`
  and `/v1/check-audio` (`shield/security.py`; enable by setting
  `DHVANI_API_KEY`); the public WhatsApp webhook is intentionally
  unauthenticated.
- **Residual / roadmap:** Twilio request-signature validation on the
  webhook; mTLS or OAuth2 for enterprise API clients.

### Tampering (model poisoning / registry integrity)
- **Threat:** malicious edit to training templates (`shield/datagen.py`)
  or registry so chosen scripts score benign.
- **Mitigations:** the model trains from in-repo templates only, pinned
  by `seed=42` and reproducible; changes are visible in version control
  and would move the published eval numbers.
- **Residual / roadmap:** signed releases + checksum of registry/templates
  surfaced at `/readyz`; review gate on registry changes.

### Repudiation / auditability
- **Mitigation (built):** every response carries an `X-Request-ID`;
  structured JSON access logs record request id, path, status, latency,
  verdict label — **never content** (`shield/observability.py`).
- **Residual:** logs are per-process stdout; ship to a central,
  tamper-evident store in production.

### Information disclosure (the privacy-critical class)
- **Threat:** call content leaking via logs, error traces, temp files, or
  metrics.
- **Mitigations (built):** telemetry is **aggregate-only and content-free
  by construction**; audio uploads are written to a temp file and deleted
  in a `finally` block (process-and-delete); no database, no persistence.
- **Residual / roadmap:** enforce TLS at the edge; scrub any framework
  stack traces from client-facing 500s (return generic errors).

### Denial of service
- **Threat:** flooding, oversized payloads, or expensive audio uploads
  exhausting CPU.
- **Mitigations (built):** per-IP sliding-window rate limiter, text size
  cap (`DHVANI_MAX_TEXT_CHARS`), upload size cap
  (`DHVANI_MAX_UPLOAD_BYTES`); load-tested to 143 req/s @ 100% success on
  one node.
- **Residual / roadmap:** the limiter is in-process (per replica) — move
  to Redis for a shared window across replicas; edge WAF/CDN rate limits;
  request timeouts on transcription.

### Elevation / logic bypass (evasion — the core adversary)
- **Threat:** paraphrase, euphemism, code-mixing, or scripts that never
  utter a registry word (demonstrated: OOD `s03`, `s10`).
- **Mitigations (built):** L2 learned layer (cut OOD false reassurance
  11→2), L3 temporal structure (detects the coercion grammar even when
  vocabulary mutates — order-scramble test), and the **monotone gate** so
  no learned-layer error can create a false "safe".
- **Residual / roadmap (stated honestly):** OOD FRR is 2/14, not 0. The
  L2 *semantic* (embedding) layer is the designed countermeasure for the
  residual evasions and is the next build item — **not** registry tuning
  against the test set.

### Model extraction / inversion
- **Threat:** probing the API to reconstruct thresholds or training data.
- **Mitigations:** no confidence score is required in the deployed
  response contract; rate limiting slows probing.
- **Residual:** publish only categorical verdicts externally; keep
  `ml_prob` to internal/debug responses.

## 5. Residual-risk register (honest, prioritised)
| # | Risk | Severity | Status |
|---|---|---|---|
| R1 | OOD false reassurance (2/14) on unseen evasions | High | Accepted for prototype; L2-semantic layer is the fix |
| R2 | In-process rate limiter doesn't span replicas | Medium | Documented; Redis on roadmap |
| R3 | Webhook lacks signature validation | Medium | Roadmap (Twilio signature) |
| R4 | No real-world / adversarial field validation | High | Requires partner + DPIA (see PRIVACY.md) |
| R5 | Registry/template integrity not cryptographically pinned | Low | Roadmap (signed releases) |

## 6. Security controls summary (what is enforced today)
- Auth: `Depends(require_api_key)` on `/v1/*`, off unless configured.
- Rate limiting: per-IP sliding window, tunable, `429 + Retry-After`.
- Input limits: text and upload size caps → `413`.
- Isolation: no persistence; temp files deleted; no inference-time network.
- Observability: content-free metrics + structured logs + request IDs.
- Verified by `tests/eval_hardening.py` and `tests/loadtest.py`.
