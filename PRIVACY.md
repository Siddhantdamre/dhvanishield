# Privacy & Data Protection — DhvaniShield

DhvaniShield processes call content, which under India's **Digital
Personal Data Protection Act, 2023 (DPDP Act)** is personal data. This
document states the data-protection posture, maps it to the Act's
obligations, and is honest about what a real deployment still requires.
It is engineering-and-design documentation, not legal advice.

## 1. Design stance: privacy by architecture, not by policy
The strongest privacy guarantee is the data you never hold. DhvaniShield
is built so that **call content is transient and never persisted or
logged**:
- **No database. No storage layer.** Nothing about a call survives the
  request.
- **Process-and-delete for audio.** An uploaded voice note is written to
  a temporary file and removed in a `finally` block in the same request
  (`server.py::check_audio`); the transcript lives only in memory for the
  duration of the call.
- **Content-free telemetry by construction.** Metrics and logs record
  only aggregate, non-content signals — verdict *label*, latency, status,
  request id — **never the transcript, request body, or any call
  content** (`shield/observability.py`). This is enforced in code, not
  promised in prose.
- **No inference-time network egress.** The classifier is fully local
  (char-ngram + logistic regression + rules); no call content is sent to
  any third party or LLM API.

## 2. Data inventory
| Data | Category | Where it lives | Retention |
|---|---|---|---|
| Call transcript text | Personal data (may include sensitive financial context) | In memory, request-scoped | Discarded when the response returns |
| Uploaded audio | Personal data | Temp file, request-scoped | Deleted in `finally` (process-and-delete) |
| Verdict label + latency + status + request id | Operational metadata (non-content) | Aggregate metrics / stdout logs | Operator-defined; no content to retain |
| Client IP (rate limiting) | Personal data (limited) | In-memory window only | Ages out of the sliding window (seconds) |
| Consented feedback example (redacted text + label) | Personal data, **opt-in only** | `data/labeled_examples.jsonl` (gitignored) | Kept for model retraining; operator-erasable (§3a) |

## 3. DPDP Act 2023 — obligation mapping
| DPDP principle / obligation | How DhvaniShield addresses it | Gap / who owns it |
|---|---|---|
| **Lawful purpose & consent** (§4–6) | Purpose is narrow and user-serving: score the user's own call at their request. | A deploying **Data Fiduciary** must present a clear consent notice; app default is user-initiated checks. |
| **Purpose limitation** (§6) | Data used only to produce the verdict; no secondary use, profiling, or training on user calls. | Enforced by no-persistence design. |
| **Data minimisation** (§6) | Only the text needed to classify is processed; telemetry is content-free. | — |
| **Storage limitation** (§8(7)) | No storage; content discarded at end of request. | — |
| **Accuracy** (§8(3)) | Asymmetric design refuses to certify "safe"; abstains under uncertainty (see MODEL_CARD). | Accuracy limits disclosed to users. |
| **Security safeguards** (§8(5)) | Auth, rate limiting, size caps, no persistence, local inference (see THREAT_MODEL). | TLS termination + central log security owned by the deployer. |
| **Breach notification** (§8(6)) | Minimal blast radius: no data at rest to breach. | Deployer must define the notification runbook. |
| **Data principal rights** (§11–14: access, correction, erasure, grievance) | Trivially satisfied for content — nothing is retained to access, correct, or erase. | Deployer must provide a grievance/contact channel. |
| **Children's data** (§9) | Not directed at children; no age data collected. | Deployer duty if context changes. |

## 3a. Opt-in feedback corpus (the only stored data)
The one place DhvaniShield stores content is the **consent-based feedback
loop** (`shield/feedback.py`, `POST /v1/feedback`), which exists because
real accuracy can only come from real labelled examples (see
`MODEL_CARD.md` §5c). It is built to keep the privacy stance intact:
- **Opt-in only.** Nothing is written unless the user explicitly sets
  `consent = true`. Without consent the request stores *nothing* — the
  default process-and-delete behaviour is unchanged.
- **Minimised + redacted.** Only a redacted transcript, the human label,
  the model's verdict, and a timestamp are stored. Emails, phone numbers,
  and 4+ digit runs (OTPs, card/account numbers) are stripped *before*
  writing (`redact()`), verified by `tests/eval_feedback.py`.
- **Anonymous.** No user identity, phone number, or device id is stored,
  so entries are not linkable to an individual.
- **Purpose-bound.** Used only to retrain the scam model; no profiling,
  no sale, no secondary use.
- **Revocable.** The corpus is a plain append-only JSONL the operator can
  inspect, export, or erase in full (`clear_corpus()`); it is gitignored
  and never redistributed. Because entries are anonymous, there is no
  per-user linkage to erase — the whole corpus is erasable instead.

DPDP note: consent here is specific, informed, and freely given (the tool
works fully without it); the deploying Data Fiduciary still owns the
consent-notice wording at the point of collection.

## 4. Roles
- **This software** acts as a **Data Processor** component.
- The **institution that deploys it** (bank, telco, helpline, or the app
  publisher) is the **Data Fiduciary** and owns consent, notice, the
  grievance channel, breach notification, and any DPIA.
- These responsibilities are named here so they are not silently dropped.

## 5. Data Protection Impact Assessment (DPIA) — lite
- **Nature:** transient classification of user-supplied call content.
- **Necessity/proportionality:** content processing is the minimum needed
  to warn a user; no profiling, no retention, no enrichment.
- **Risks to data principals:** (a) content leakage — mitigated by
  no-persistence + content-free telemetry; (b) false accusation —
  mitigated by the abstain-don't-accuse design (wrongful-HIGH = 0/8 OOD);
  (c) exclusion of non-English speakers — mitigated by multilingual
  coverage as a first-class requirement.
- **Residual risk requiring a partner:** a **field pilot on real,
  consented call data** — the one step that needs an institutional Data
  Fiduciary, a full DPIA, and (for a bank deployer) alignment with RBI /
  CERT-In directions. This is stated as the gap between prototype and
  production, not glossed over.

## 6. What a deployer must add (honest checklist)
- [ ] TLS at the edge; scrub framework stack traces from client 500s.
- [ ] Consent notice + purpose statement at point of collection.
- [ ] Grievance officer / contact channel (DPDP §13).
- [ ] Central, access-controlled log store (logs are content-free but
      still operational data).
- [ ] If any retention is later introduced, a retention schedule and an
      erasure workflow — currently unnecessary because nothing is stored.
- [ ] Full DPIA before any real-user pilot.

## 7. Summary
DhvaniShield minimises privacy risk the most durable way available — by
not retaining call content at all, and by making its telemetry
content-free in code. That converts most DPDP obligations from "policies
to enforce" into "conditions that cannot be violated," and isolates the
remaining, genuinely organisational duties (consent, grievance, breach
runbook, field-pilot DPIA) as the deploying Data Fiduciary's to own.
