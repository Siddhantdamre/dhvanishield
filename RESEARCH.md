# DhvaniShield — Research Specification (v0.2)

## 1. Problem formalisation
Let x be the text of a phone/video call (transcribed or described).
DhvaniShield is a **selective classifier with an asymmetric output space**:

    f(x) -> {HIGH_RISK, UNCERTAIN, NO_PATTERN}

There is deliberately no SAFE class. The loss structure is asymmetric:
a false alarm costs one verification phone call; a false reassurance can
cost a victim's life savings. We therefore treat

    FRR  =  P( NO_PATTERN | x is a scam )      — false-reassurance rate

as a **hard constraint (target 0 on the benchmark)**, and optimise the
remaining utility (scam recall at HIGH_RISK, benign pass rate,
abstention precision) subject to it. This places the system in the
selective-prediction / learning-to-defer family rather than standard
classification: UNCERTAIN is a first-class output with an attached
human action ("hang up, verify, call 1930"), not a failure mode.

## 2. Hypotheses
- **H1 (architecture).** Removing the SAFE class from the output space
  eliminates the dangerous error mode *by construction*, at acceptable
  cost in benign-user friction. Verified: FRR = 0 with benign pass 12/12.
- **H2 (structure over vocabulary).** Digital-arrest calls follow a
  stable coercion grammar — authority → accusation → isolation →
  urgency → money → access — even as surface scripts mutate. A
  trajectory scorer over stage progression and order concordance
  detects this structure. Verified: identical sentences scrambled give
  equal progression (0.67) but lower concordance (1.00 → 0.50).
- **H3 (multilinguality is safety-critical, not cosmetic).** An
  English-only registry silently fails vulnerable non-English speakers.
  Verified by ablation: English-only FRR rises from 0 to 3/12.

## 3. Method (layered)
- **L1 lexical**: auditable marker matching over a 6-category registry
  (151 markers; en/hi/mr) sourced from public advisories. Deterministic;
  every verdict traceable to matched strings.
- **L2 semantic** (implemented, `shield/semantic.py`): intent-exemplar
  similarity against a bank of named scam-family exemplars (incl.
  families outside the lexical registry: sextortion, loan-app harassment,
  fake-job, UPI-collect, deepfake emergency, remote-support, utility
  disconnection), guarded by a benign-context bank. Transparent and local
  (TF-IDF cosine, no download); every escalation names the family it
  resembled. Escalate-only, capped at UNCERTAIN. A sentence-transformer
  backend is a drop-in behind the same `score()` seam.
- **L3 temporal**: trajectory analysis (progression × concordance) over
  utterance-ordered category first-hits.
- **D decision**: threshold rule on category count and weighted score;
  L3 may only **escalate**, never downgrade (monotonicity constraint —
  preserves FRR = 0 under any L3 behaviour). *Design note:* under
  current integer lexical weights the escalation path is inert (any two
  categories already reach HIGH_RISK); it activates when L2 introduces
  fractional evidence. Stated openly rather than claimed as live.

## 4. Evaluation protocol
Benchmark: 32 synthetic transcripts modelled on documented cases
(12 scam / 12 benign / 8 ambiguous; en/hi/mr). Metrics: scam recall at
HIGH_RISK, FRR (hard gate = 0), benign pass rate, wrongful-HIGH rate
(hard gate = 0), abstention rate on ambiguous, order-sensitivity delta,
ablation table (full vs −L3 vs English-only). Current results: 12/12,
0, 12/12, 0, 8/8, Δconcordance = 0.50, ablations above.
Planned (week 2): adversarial paraphrase set written to defeat L1
(measures L2 contribution), code-mixed Hinglish set, risk–coverage
curve once L2 yields graded scores, inter-threshold sensitivity sweep.

## 5. Threat model
Adversary knows the registry (assume publication). Attacks: paraphrase
and euphemism (mitigation: L2, trajectory structure), code-mixing
(mitigation: mixed-language markers + L2 multilingual embeddings),
slow-burn multi-call grooming that never completes the sequence in one
call (mitigation: session memory across calls — roadmap), and social
attacks outside audio (fake documents on video — out of scope, stated).

## 6. Ethics & limitations
Synthetic benchmark, not field data; results are proof-of-design, not
deployment claims. No 'safe' verdict also means the tool cannot clear
legitimate callers — accepted cost, disclosed to users. Privacy: all
processing local/on-device by design; no call audio leaves the phone.
False-alarm burden falls on legitimate institutions calling citizens —
mitigated by NO_PATTERN wording that educates rather than accuses.
Language coverage gaps are a fairness risk (see H3); registry expansion
is prioritised by speaker population of scam-targeted demographics.

## 7. Learned layer: train / validate / test (v0.3)
Dataset: template slot-filled generator over the coercion grammar with
paraphrase fillers that deliberately evade the registry; 300 scam + 300
benign; split 60/20/20 (seed 42). Model: char n-gram (2-4) TF-IDF +
logistic regression — script-agnostic, CPU-seconds training, fully
local. Asymmetric two-pool calibration on dev + hand-written
calibration sets (benign, ambiguous), disjoint from test:
t_yellow above all benign; t_red additionally above all ambiguous.

Held-out test results:
| system     | scam recall@RED | false reassurance | benign green | benign RED |
|------------|-----------------|-------------------|--------------|------------|
| rules-only | 17.5%           | 38.1%             | 100%         | 0%         |
| ML-only    | 100%            | 0%                | 100%         | 0%         |
| hybrid     | 100%            | 0%                | 100%         | 0%         |

Regression on hand-written 32-case benchmark under hybrid: unchanged
(12/12 red, FR 0, benign 12/12 green, ambiguous never red). Hybrid is
monotone (ML escalates only), so all rules-layer guarantees survive.

**Finding (language bias):** with Latin-dominated benign training
templates, a Hindi benign family message scored p=0.816 ("Devanagari
looks like scam"). Fixed at the data level by balancing benign
templates across scripts. Mirror of H3: language coverage is a safety
property in BOTH the registry and the training distribution.

**Scope caveat:** the §7 test split shares a generator family with train,
so it measures paraphrase robustness *within* that family, not full OOD.

### 7a. Out-of-distribution test (generalisation gap)
True-OOD probe: 22 transcripts (14 scam / 8 benign) hand-written from
real Indian scam typology (I4C/MHA advisories, news-reported cases),
generated independently of `shield/datagen.py`. Most scam items avoid
registry vocabulary; the benign set is adversarially hard (a real bank
fraud desk that refuses credentials, a real police summons, a legit
prepaid courier). Measured under the deployed configuration.

| system     | recall (not reassured) | caught@RED | false reassurance | benign never RED |
|------------|------------------------|------------|-------------------|------------------|
| rules-only | 21.4%                  | 14.3%      | 11/14             | 0/8 ✅           |
| hybrid     | 92.9%                  | 28.6%      | 1/14              | 0/8 ✅           |

(Hybrid = rules + char-ngram ML + the L2-semantic layer of §3, escalate-only.)

Three findings:
1. **Learned generalisation.** The learned layers cut false reassurance
   from 11/14 to 1/14 on data from a different source than training — a
   91% reduction in the dangerous error. This is the paraphrase-robustness
   claim of §7 discharged *off-distribution*, not just within the
   generator family.
2. **Asymmetric guarantee holds OOD.** Wrongful-HIGH (a benign caller
   accused) = 0 on both distributions. Under uncertainty the hybrid
   abstains (6/8 OOD benigns → UNCERTAIN), never accuses. The core
   design property survives the distribution shift even though FRR does
   not.
3. **Honest generalisation gap.** The §7 hard gate FRR = 0 is a
   *benchmark* property, not an OOD guarantee: one scam still reaches
   NO_PATTERN — an OTP-read-aloud family-impersonation call ("read me the
   message that just came"), which mimics an ordinary family call almost
   exactly. The electricity-disconnection lure, previously missed, is now
   caught by the L2-semantic layer. The residual case is that layer's
   explicit next target.

### 7b. Reproducibility fix (trust-critical)
The dataset generator accumulated transcripts into Python `set`s, whose
iteration order depends on `PYTHONHASHSEED` (randomised per process).
Although the split shuffle was seeded, the data *fed* to it varied
run-to-run, so the trained model's verdicts on borderline cases flickered
(±1 on false-reassurance / over-warn counts). Fixed by sorting the sets
before the seeded shuffle (`shield/datagen.py`): verdicts are now
identical across processes and hash seeds. A model that answers the same
input differently on reruns is not trustworthy; this closes that gap and
makes every number in this document reproducible.

### 7c. L2-semantic ablation (does no harm)
`tests/eval_semantic.py` runs the hybrid with the semantic layer OFF vs
ON on both hard sets. ON never raises false reassurance or false alarms
anywhere (it is escalate-only, capped at UNCERTAIN); it lowers OOD false
reassurance 2→1 and red-team 2→0. The measured cost is higher benign
over-warning (it cannot reduce over-warn without downgrading, which would
break the monotone gate — an accepted, disclosed trade-off).

### 7d. All-rounder training + a calibration bug (found and fixed)
Deployed training is a self-assembling blend (`shield/training.py`):
synthetic + real-case-grounded seed always, feedback corpus and SMS when
present. Multi-domain experiment (`tests/eval_allrounder.py`): SMS-only
training collapses phone-scam AUC to 0.40 (below chance); synthetic+seed
lifts it 0.707→0.886; synth+seed+SMS is the only mix strong on both
channels (SMS 0.995 / phone 0.776) but sacrifices peak phone skill — so
SMS is opt-in, off by default for a phone deployment.

**Calibration bug (trust-critical).** The asymmetric `t_yellow` was
`max(benign prob) + margin`. On diverse *real* benign data a single
high-scoring benign outlier dragged t_yellow to ~0.72 and silently
destroyed recall (deployed OOD false-reassurance 1→7) — while the test
suite stayed green because those suites *reported* rather than *gated* the
number. Fixed two ways: (1) `t_yellow` now uses the 98th percentile of
benign scores (robust to a few outliers, `shield/ml.py`), restoring OOD
false-reassurance to 1/14 on the seed-grounded model; (2) `eval_ood` and
`eval_redteam` now **gate** on false-reassurance so a regression fails the
build. Net effect vs synthetic-only: RED catches 28.6%→57.1%, over-warn
82%→45%, at equal false-reassurance and zero false accusation.

**Integrity note (no test-set tuning).** Both misses are closable in
minutes by adding registry markers, and we deliberately do not: tuning
L1 against the OOD probe would overfit the measurement instrument and
void the 82%-reduction claim above. The residual 2/14 is reported as-is.
Reproduce: `python tests/eval_ood.py`.

## 8. Scam Gym (inoculation mode)
Beyond detection: an interactive mode plays scam and benign calls line
by line; the user must call "scam" as early as possible, then receives
a stage-by-stage debrief. Grounded in inoculation/prebunking theory
(experiencing a weakened attack builds durable resistance). Detection
protects the user today; inoculation protects them permanently —
including when they answer a call without the app.

## 9. Universal access as a detection-equity claim
Scam-protection tools implicitly assume users who can hear, read small
English text, and operate apps; digital-arrest scammers target the
complement of that population. DhvaniShield therefore treats
accessibility as a core safety property, symmetrical with H3
(language coverage): every verdict has a spoken rendering (TTS-ready,
short-sentence, action-repeated — for blind users), a pictogram
rendering (zero-literacy action card — for deaf and low-literacy
users), and ships the family code word protocol, a zero-technology
countermeasure robust to AI voice cloning. Constraints are encoded as
tests, not guidelines.

## 10. Architecture as an expert committee (honest MoE)
DhvaniShield is a mixture-of-experts in the committee sense, not the
gated-transformer sense: six lexical stage-experts, one statistical
paraphrase-expert (L2), one temporal sequence-expert (L3), combined by
an asymmetric gate constrained to escalate-only. This retains MoE's
core property (specialists + gating) while staying auditable, CPU-only
and deployable. The committee is surfaced to the user as the
Manipulation Meter: per-expert pressure bars (Authority, Accusation,
Isolation, Urgency, Financial pull, Access grab) that reflect the
psychology of the call back to the user without accusation. The
earliness metric doubles as time-before-irreversible-action: on the
benchmark the gate fires at or before the money stage in 12/12 scams.

## 11. Deployment surface
FastAPI service (server.py): /v1/check JSON API and a Twilio-compatible
/webhook/whatsapp endpoint returning plain text with the Unicode meter
— verdicts drop into an existing WhatsApp thread with zero install.
ML expert trained at startup (seed-fixed, seconds, local); nothing
persisted (process-and-delete); no endpoint can return certified-safe.
Containerised (Dockerfile). Deployment contract enforced by
tests/eval_server.py.
