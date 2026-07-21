# Architecture

DhvaniShield is a **manipulation-defence layer**: a committee of small,
auditable experts that score the *strategy* of manipulation, combined by an
asymmetric safety gate, wrapped in calibration, accessibility, and a
compliance receipt. Everything is on-device, CPU-only, and content-free.

## 1. Data flow (one request)
```
                       text (a call transcript / a forwarded message)
                                        │
                        ┌───────────────┴───────────────┐
                        ▼                                ▼
             DETECTION COMMITTEE                 MANIPULATION ENGINE
        (shield/engine, ml, semantic,          (shield/manipulation.py)
             trajectory, message)            strategy vector + counterfactual
                        │                                │
                        ▼                                │
     escalate-only monotone gate  ◄────────── may only RAISE, never clear
     (rules ⊔ ML ⊔ semantic ⊔ msg)                      │
                        │                                │
        ┌───────────────┼────────────────┬──────────────┤
        ▼               ▼                ▼              ▼
   category        calibration       accessibility   receipt
 (categories.py)  (selective       (accessibility)  (receipt.py)
  scam family +    prediction/       6 profiles      signed, content-free
  tailored advice  defer-to-human)                   duty-of-care proof
        │               │                ▼              │
        └───────────────┴──────►  verdict + explanation + action ◄────┘
                                (+ threat_class via /v1/analyze: scam | misinfo | none)
```

## 2. The experts (why each exists)
| Layer | File | Role | Property |
|---|---|---|---|
| L1 lexical | `engine.py` + `registry.py` | marker matching over 6 coercion categories (en/hi/mr) | deterministic, auditable |
| L2 learned | `ml.py` | char n-gram + logistic regression, robust percentile calibration | script-agnostic, CPU-seconds |
| L2 semantic | `semantic.py` | intent-exemplar similarity | catches paraphrase / novel families |
| L3 temporal | `trajectory.py`, `stream.py` | coercion-arc progression | fires before the money stage |
| Message expert | `message_model.py` | trained on real SMS (opt-in, capped at UNCERTAIN) | real-data grounding, never false-accuses |
| Training | `training.py` | self-assembling blend (synthetic + seed + feedback), robust calibration | one place, all data |

## 3. The invariants (the safety core — never violated)
1. **No SAFE class.** Output is `{HIGH_RISK, UNCERTAIN, NO_PATTERN}`; nothing
   certifies a call safe.
2. **Monotone gate.** Learned layers may only *escalate*, so no learned error
   can create a false "safe" — false reassurance is structurally bounded.
3. **Never falsely accuse.** Benign→HIGH_RISK held at 0 across every eval;
   under uncertainty it abstains.
4. **Content-free.** Process-and-delete; telemetry and receipts store only
   labels/hashes, never text.

## 4. Cross-cutting concerns
- **Calibration / defer-to-human** (`calibration.py`): honest confidence +
  a selective threshold that guarantees a target error rate by deferring.
- **Accessibility** (`accessibility.py`, `access.py`): one alert, six
  disability profiles; colour-blind-safe, spoken, haptic, easy-read.
- **Compliance** (`receipt.py`): tamper-proof, content-free warning receipt.
- **Security** (`security.py`): multi-key auth, Twilio webhook signing,
  pluggable rate limiter, startup audit.
- **Observability** (`observability.py`): Prometheus metrics, structured
  content-free logs.

## 5. The manipulation engine (the research core)
`manipulation.py` scores 10 influence strategies (Cialdini + coercion
levers + override) as a domain-general vector, with:
- `analyze()` — strategy vector, pressure score, dominant strategies
  (explanation), uncertainty;
- `learn_strategy()` — few-shot concept extension;
- `minimal_core()` — counterfactual "which tactics are load-bearing" (with a
  documented reliability limit).
It generalises across attack domains (scam → sales → coercion → AI attacks),
with the honest real-data number recorded in `RESEARCH_MANIPULATION.md §4a`.

## 6. Surfaces (API)
| Endpoint | Purpose |
|---|---|
| `POST /v1/check` | scam verdict + category + accessibility + receipt |
| `POST /v1/screen` | ambient (silence-until-confident) alert |
| `POST /v1/analyze` | scam **and** misinformation → threat_class |
| `POST /v1/manipulation` | universal strategy analysis (human or AI text) |
| `POST /v1/feedback` | consent-gated flywheel |
| `POST /v1/receipt/verify` | verify a duty-of-care receipt |
| `POST /webhook/whatsapp` | Twilio-compatible forwarded-message channel |
| `GET /healthz /readyz /metrics` | ops |

## 7. Design principle
Small, auditable, honest parts beat one opaque model: every verdict traces
to matched strings and named strategies, every claim maps to a test
(`tests/run_all.py`), and every limit is written down. The intelligence is
in the *composition and the honesty*, not in model size.
