# 🛡️ DhvaniShield

**One sentence:** A second opinion on a suspicious call, in your language —
it can warn you or admit it isn't sure, but it is never allowed to tell you
a call is safe.

ET AI Hackathon 2026 — Problem 6 (Digital Public Safety).
SDG alignment: 16.4 (illicit financial flows / organised crime),
10 (protects elderly & non-English-speaking citizens), 3, 1.

## Status — v7: SPEECH INPUT WIRED
Run the service:  `pip install -r requirements.txt && uvicorn server:app --port 8000`
Or:               `docker build -t dhvanishield . && docker run -p 8000:8000 dhvanishield`
Wire to WhatsApp: point a Twilio WhatsApp Sandbox number's webhook at
`POST /webhook/whatsapp` — verdict + Manipulation Meter arrive as a
normal WhatsApp reply. Demo UI: `streamlit run app_live.py`.
Test suites: eval.py | eval_ml.py | eval_access.py | eval_server.py | eval_speech.py
- [x] Registry: 6 manipulation categories, 151 markers (English/Hindi/Marathi)
- [x] Three-output abstention verdict engine (no 'safe' output exists)
- [x] Eval benchmark: 32 transcripts (12 scam / 12 benign / 8 ambiguous) — ALL PASS
      * scam catch rate 12/12, false reassurance 0, benign pass 12/12,
        wrongful HIGH_RISK 0, ambiguous abstention 8/8
- [x] Family-alert module (demo log, webhook-ready)
- [x] Streamlit demo UI (elder-readable, three verdicts, alert toggle)
- [x] Streaming assessor + EARLINESS metric: alarm at avg 50% of call,
      at-or-before the money stage in 12/12 benchmark scams
- [x] Live call simulation UI (app_live.py): stage tracker lights up in
      real time, screen flips red mid-call, family alert fires
- [x] Speech input (shield/speech.py + POST /v1/check-audio): a voice
      note is transcribed with faster-whisper and run through the exact
      same committee as typed text. A recording that fails to transcribe
      (silence, noise, bad format) returns UNCERTAIN, never a false-safe
      NO_PATTERN — verified by tests/eval_speech.py Tier 1 (6 wiring/
      robustness checks + the live endpoint, all passing with a
      controlled fake transcriber). Tier 2 (the real faster-whisper
      model) could not be verified in the sandboxed build environment —
      it needs a one-time network call to download model weights
      (~75 MB), which that environment blocks. It will download
      automatically and work fully offline afterward on a normal
      machine; eval_speech.py prints the exact one-line command to
      confirm this yourself before the demo. AI4Bharat IndicConformer
      remains the intended higher-accuracy swap for Hindi/Marathi
      specifically — the model-loading seam in shield/speech.py is
      built for that swap, not yet implemented.
- [ ] Embedding-similarity matcher for paraphrased scam scripts,
      adversarial eval expansion (obfuscated/polite scam variants)
- [ ] Week 3: metrics slide, 5-slide deck, architecture diagram, demo video

## Run
    python tests/eval.py        # zero dependencies
    python tests/eval_speech.py # speech wiring; Tier 2 needs network once
    pip install streamlit && streamlit run app.py

## Beyond scams — a manipulation-defence layer (shield/misinfo.py)
The core capability is detecting *manipulation in messages* — which
generalises past scams to the other epidemic on the same channel and the
same at-risk users: **misinformation**. `POST /v1/analyze` runs both domains
and returns a `threat_class` (scam / misinformation / none) plus each
assessment. Honest scope: it does **not** fact-check claims — it detects the
*rhetoric* misinformation reliably uses (forward-pressure, fake authority,
miracle claims, fear framing, missing sources), with the same asymmetric
design (never assert truth; only "verify before sharing"). Verified by
`tests/eval_misinfo.py`: 10/10 hoax forwards flagged, 0 false alarms on
ordinary messages.

## Scam categorisation — the right advice per scenario (shield/categories.py)
Beyond scam / not-scam, the tool names the scam FAMILY (digital arrest,
KYC-phishing, UPI-refund, sextortion, loan-harassment, lottery, job/task,
investment, tech-support, courier/customs, utility cut-off, family
impersonation) and gives family-specific, action-first guidance — because
the right move for sextortion ("don't pay, keep evidence, it's not your
fault") is nothing like the one for KYC-phishing ("open your bank app
yourself"). Simple, auditable cue-scoring boosted by the L2-semantic
family match; verified by `tests/eval_categories.py` (9/10 routing).

## Accessibility profiles — special features for disabled users (shield/accessibility.py)
One alert, rendered for how each user actually perceives — set the profile
once (by the user or the family member who installs it):
- **blind** — spoken script + an audio earcon; no visual dependency.
- **deaf / hard-of-hearing** — pictogram + a distinct haptic vibration code; no audio dependency.
- **colour-blind** — meaning carried by SHAPE + WORD (⛔ STOP), never colour alone.
- **low-literacy** — scam icon + a grade-1 easy-read one-liner.
- **cognitive / elderly** — one step only + the family code word + one-tap trusted contact.

Every profile always carries the scam type, the tailored action, and the
one-tap "call someone you trust" (the counter to the scam's isolation).
`POST /v1/screen` and `/v1/check` take a `profile`; `check.py --profile=blind`.
Verified by `tests/eval_accessibility.py`.

## Accessibility base renderings (shield/access.py)
Every verdict renders three ways: standard, SPOKEN (TTS-ready, <=9-word
sentences, key action said twice, for blind users and read-aloud), and
PICTOGRAM (emoji action card for deaf & low-literacy users) — in en/hi/mr.
Plus the Family Code Word: a zero-tech countermeasure that defeats even
AI voice-cloning. Design constraints are enforced as tests
(tests/eval_access.py).

## Design principle
Asymmetric trust: a false alarm costs one phone call; a false reassurance
can cost someone's life savings. Therefore reassurance is not in the
output space. Evaluation enforces FALSE REASSURANCE = 0 as a hard gate.
This now extends to speech input: a failed transcription is treated the
same way a failed check would be — it escalates to a human decision
(UNCERTAIN), it does not default to safe.

---

## Results at a glance (all reproducible)
| | rules-only | hybrid (deployed) |
|---|---|---|
| In-distribution false reassurance (`eval_ml.py`) | 38.1% | **0%** |
| Out-of-distribution false reassurance (`eval_ood.py`) | 11/14 | **2/14** |
| Wrongful accusation (benign→RED), both distributions | 0 | **0** |
| Per-call latency (`loadtest.py`) | — | **p50 12.9 ms / p99 18 ms** |
| Capacity, single node | — | **143 req/s @ 100% success** |

The hybrid's learned layer cuts the dangerous error (false reassurance)
from 11/14 to 2/14 on independently hand-written out-of-distribution data
— real generalisation. The two residual misses are reported honestly and
left untuned (see `MODEL_CARD.md` §5b). "Wrongful accusation = 0 on both
distributions" is the property that makes it deployable: under
uncertainty it abstains, it never accuses.

## Production readiness & operations
Built and verified (`tests/eval_hardening.py`, `tests/loadtest.py`):
- **Security** — API-key auth (secure-by-config: set `DHVANI_API_KEY` to
  require it), per-IP sliding-window rate limiting (`429 + Retry-After`),
  request/upload size caps (`413`). `shield/security.py`.
- **Observability** — Prometheus `/metrics` (verdict mix, latency
  p50/p95/p99, error rate), JSON `/metrics.json`, structured JSON access
  logs, and an `X-Request-ID` on every response — **content-free by
  construction** (no transcript ever logged). `shield/observability.py`.
- **Probes** — `/healthz` (liveness), `/readyz` (readiness + model
  version). Container-ready (`Dockerfile`).
- **Config (env):** `DHVANI_API_KEY`, `DHVANI_RATE_LIMIT`,
  `DHVANI_RATE_WINDOW`, `DHVANI_MAX_TEXT_CHARS`, `DHVANI_MAX_UPLOAD_BYTES`.

## Use it (one line, no server)
    python check.py "he said he is from CBI and I must transfer money to verify"
    echo "your parcel has drugs, stay on the line" | python check.py
    python check.py --json "..."      # machine-readable output
    python check.py --ambient "..."   # always-on guardian: silent unless a real scam
Prints the verdict, the Manipulation Meter, what the caller is doing (each
line traceable), and the action to take.

## Interaction model — silence is the feature
A guardian that interrupts normal calls gets muted, and then it protects
no one. So there are two modes:
- **Ambient** (`POST /v1/screen`, `check.py --ambient`) — an always-on
  listener that stays **silent** unless the call is a confident, structured
  scam (the money/credentials moment). UNCERTAIN is held silently
  ("watching"), never pushed. On 4,827 real legitimate messages this
  interrupts **0.02%** of them vs **61%** for naive "warn on anything
  unsure" — a 100% reduction in nagging (`tests/eval_policy.py`).
- **Proactive** (`POST /v1/check`, `check.py`) — the user forwarded a
  message / asked "is this real?", so it always answers.

Go-to-market note: the **proactive / pull-based** path is v1 — it needs
zero call access and nothing stored, so there is no trust or hack barrier
to adoption. The ambient path is a later, on-device-only step that is safe
*only because* the collect-nothing foundation exists first. Rationale and
the "why not Truecaller" positioning: [`POSITIONING.md`](POSITIONING.md).

When ambient fires, it fires once and reaches every sense at once — one
action-first line (warns against the *action*, never accuses the caller),
a spoken script, a pictogram, a haptic cue, and one tap to a trusted
person (breaking the scam's isolation). `shield/policy.py` + `shield/access.py`.

## Reproduce every claim
    python tests/run_all.py           # full gate: all 8 suites (fast, no network)
    python tests/run_all.py --load    # also run the latency/capacity benchmark
    python tests/loadtest.py          # writes loadtest.svg + loadtest_results.json
    python tests/realworld/fetch.py   # download the real UCI SMS dataset (once)
    python tests/eval_realworld.py        # deployed model on 5,574 real messages
    python tests/eval_realworld_method.py # method validation on real held-out data
CI runs the same `tests/run_all.py` on every push (`.github/workflows/ci.yml`).

## The data flywheel (how accuracy actually improves)
A measured, uncomfortable truth (`tests/eval_train_real.py`): the model
**cannot be fine-tuned to accuracy** on synthetic or wrong-domain data —
training on real *SMS* spam lifts SMS AUC to 0.998 but drops phone-scam
AUC to 0.40 (below chance). Real accuracy needs real *phone-scam* data,
which no public dataset has. The only source is usage:

    zero-friction use (forward a message)  ->  user confirms scam / not (consent)
      ->  redacted, anonymous labelled example stored (shield/feedback.py)
      ->  retrain on real phone-scam data  ->  accuracy climbs
      ->  proprietary corpus no competitor has  =  the moat

`POST /v1/feedback` captures one example **only with explicit consent**,
PII redacted before writing; `GET /v1/corpus/stats` shows a content-free
view including where the model disagreed with humans (the training
signal). Verified by `tests/eval_feedback.py`. Privacy contract:
[`PRIVACY.md`](PRIVACY.md) §3a.

## Real-world results (measured, not claimed)
On 5,574 real messages the model has never seen (UCI SMS Spam, an honest
cross-channel proxy): **0.02% false-alarm on 4,827 real legitimate
messages** — the "never falsely accuse" property holds at scale. The
deployed model discriminates real SMS only weakly (AUC 0.638) because it
was trained on synthetic templates; the *same method retrained on real
data* scores **98.1% accuracy, F1 0.924, 0.21% false-alarm** on held-out
real data. The method is sound — the gap to a real product is training
data, not design. Details in [`MODEL_CARD.md`](MODEL_CARD.md) §5c.

## Documentation
| Doc | What it covers |
|---|---|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | How the whole system is built — data flow, experts, invariants, surfaces |
| [`PRESENT.md`](PRESENT.md) | Start-to-finish hackathon runbook (copy-paste, with what to say) |
| [`RESEARCH.md`](RESEARCH.md) | Formal method, hypotheses, ablations, generalisation-gap analysis |
| [`RESEARCH_MANIPULATION.md`](RESEARCH_MANIPULATION.md) | The research direction: domain-general manipulation-strategy detection + cross-domain generalization evidence |
| [`MODEL_CARD.md`](MODEL_CARD.md) | Intended use, metrics, biases, caveats (Mitchell-style card) |
| [`THREAT_MODEL.md`](THREAT_MODEL.md) | Assets, adversaries, STRIDE attack/mitigation map, residual-risk register |
| [`PRIVACY.md`](PRIVACY.md) | DPDP Act 2023 mapping, data flow, DPIA-lite, deployer checklist |
| [`POSITIONING.md`](POSITIONING.md) | Why not Truecaller, the collect-nothing trust model, the honest product arc |
| [`DECK.md`](DECK.md) | Hackathon pitch — 12 slides with speaker notes and timing |
| [`DEMO.md`](DEMO.md) | 90-second live-demo runbook (exact commands + fallbacks) |
| [`JUDGE_QA.md`](JUDGE_QA.md) | Anticipated judge questions with honest, ~20s answers |
| [`SCALING.md`](SCALING.md) | Deployment + scaling ladder: WhatsApp bot first, infra only on real load |
| [`ENTERPRISE.md`](ENTERPRISE.md) | Why a bank/telco buys it — the Duty-of-Care Warning Receipt (compliance proof) |
| [`SECURITY.md`](SECURITY.md) | Honest security posture: controls in place, config to set, known gaps |
| [`IMPACT.md`](IMPACT.md) | SDG alignment with mechanisms, the equity core, and the frontier-safety framing |

## Honest limitations (the boundary I'm not hiding)
- Evaluation is synthetic + a small hand-written OOD set; **no real field
  data**. A consented field pilot is the gap between prototype and
  product and needs an institutional partner + DPIA (`PRIVACY.md` §5).
- OOD false reassurance is 2/14, not 0 — the embedding (L2-semantic)
  layer is the designed fix, not registry tuning against the test set.
- The in-process rate limiter is per-replica; a multi-node deployment
  needs a shared store (Redis). Documented, on the roadmap.
