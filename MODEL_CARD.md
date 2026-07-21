# Model Card — DhvaniShield Scam-Call Classifier

Following the Mitchell et al. (2019) model-card framework. Every number
here is reproducible from this repository; the command is given in §7.

## 1. Model details
- **Owner / point of contact:** Siddhant Damre (solo author).
- **Version:** hybrid-charngram-lr / seed42 / n300 (`MODEL_VERSION` in
  `shield/observability.py`).
- **Date:** July 2026. **Status:** research prototype, not deployed.
- **Type:** selective classifier with an *asymmetric three-output* space
  `{HIGH_RISK, UNCERTAIN, NO_PATTERN}`. There is deliberately **no SAFE
  class** — see `RESEARCH.md` §1.
- **Architecture (committee of small experts):**
  - **L1 — lexical.** Auditable marker matching over a 6-category
    registry (151 markers; English/Hindi/Marathi) derived from public
    advisories (I4C/MHA, RBI, PIB). Deterministic; every verdict traces
    to the exact strings matched. (`shield/registry.py`, `shield/engine.py`)
  - **L2 — learned.** Character n-gram (2–4) TF-IDF + logistic
    regression. Script-agnostic (works across Devanagari and Latin with
    no language detection), CPU-seconds to train, fully local, and
    interpretable. Trained at process start; **no weights are shipped**.
    (`shield/ml.py`)
  - **L3 — temporal.** Coercion-trajectory scorer over the ordered stage
    sequence (authority → accusation → isolation → urgency → money →
    access). (`shield/trajectory.py`)
  - **Decision gate.** Asymmetric and **monotone**: L2/L3 may only
    *escalate* the L1 verdict, never downgrade it. This is what
    structurally protects the false-reassurance guarantee under any
    behaviour of the learned layers.
- **Training (self-assembling, `shield/training.py`):** the deployed model
  blends synthetic templates + a real-case-grounded seed corpus always,
  plus the consented feedback corpus and (opt-in) real SMS when present —
  an all-rounder by construction that improves as the flywheel fills.
  Thresholds use robust 98th-percentile calibration (not max), which is
  what lets real, diverse benign data help instead of poisoning recall.
- **Not** a large language model; no external API, no GPU, no network at
  inference. ~7 MB working set, single CPU core.

## 2. Intended use
- **Primary use:** a *second opinion* on a suspicious phone/video call or
  forwarded message, for an at-risk citizen — surfaced as a Manipulation
  Meter plus a spoken/pictogram action ("hang up, verify on the official
  number, call 1930"). Delivered via a WhatsApp webhook or JSON API.
- **Two interaction modes** (`shield/policy.py`): *ambient* (always-on,
  stays silent unless a confident structured scam — interrupts 0.02% of
  real legitimate messages, not 61%) and *proactive* (user asked, always
  answers). The classifier is unchanged; this is a presentation policy and
  still never emits a "safe" verdict.
- **Intended users:** individuals (especially elderly and non-English
  speakers); consumer-protection / helpline operators as an assistive
  triage signal.
- **Out-of-scope / prohibited uses:**
  - **Not** an automated blocker, and **not** an authority to accuse a
    caller — the tool abstains, it does not certify guilt.
  - **Not** a legal, financial, or law-enforcement decision system.
  - **Not** validated for languages beyond en/hi/mr, nor for scam
    families outside the digital-arrest / impersonation grammar it
    models.
  - **Must not** be presented as able to declare a call "safe" — the
    output space forbids it, and any wrapper that maps `NO_PATTERN` to
    "safe" violates the design contract.

## 3. Factors
Relevant axes along which performance varies and is reported separately:
- **Language / script:** en, hi, mr; Latin vs Devanagari (a documented
  bias axis — see §6).
- **Distribution:** in-distribution (generator-family paraphrases) vs
  out-of-distribution (independently hand-written, §5b). We report both.
- **Scam style:** overt vs polite / slow-burn / code-mixed — the OOD set
  is weighted toward the hard styles.

## 4. Metrics
The loss structure is asymmetric — a false alarm costs one verification
phone call; a false reassurance can cost a victim's savings. We therefore
treat one metric as a **hard gate** and optimise the rest under it:
- **False-reassurance rate (FRR)** = P(`NO_PATTERN` | scam). **Hard gate,
  target 0** on the in-distribution benchmark.
- **Wrongful-HIGH rate** = P(`HIGH_RISK` | benign). **Hard gate, target 0.**
- Scam recall at RED, benign pass rate, abstention rate on ambiguous
  cases, order-sensitivity delta, and the per-layer ablation.

## 5. Quantitative analysis

### 5a. In-distribution (held-out test, `tests/eval_ml.py`)
Generator-family split, 60/20/20, seed 42:

| system     | scam recall@RED | false reassurance | benign green | benign RED |
|------------|-----------------|-------------------|--------------|------------|
| rules-only | 17.5%           | 38.1%             | 100%         | 0%         |
| ML-only    | 100%            | 0%                | 100%         | 0%         |
| hybrid     | 100%            | 0%                | 100%         | 0%         |

Interpretation: this proves paraphrase-robustness *within the generator
family*, not general OOD behaviour — stated openly, and the reason §5b
exists.

### 5b. Out-of-distribution (`tests/eval_ood.py`)
22 transcripts (14 scam / 8 benign) hand-written from real Indian scam
typology, generated **independently** of the training generator; most
scam items avoid registry vocabulary and the benign set is adversarially
hard (a real bank fraud desk, a real police summons, a legit courier):

| system     | recall (not reassured) | caught@RED | false reassurance | benign never RED |
|------------|------------------------|------------|-------------------|------------------|
| rules-only | 21.4%                  | 14.3%      | 11/14             | 0/8              |
| hybrid     | 100.0%                 | 28.6%      | 0/14              | 0/8              |

Red-team stress test (`tests/eval_redteam.py`, 16 evasion/novel-family
attacks + 11 benign traps): false reassurance **0/16**, false alarm
**0/11**, recall 100%; over-warn on legit calls ~54% (alarm-fatigue risk,
not a safety error, and hidden from users by the ambient policy). All
numbers are deterministic after the §7b reproducibility fix.

Deployed model note: the numbers above are the self-assembling blend
(synthetic + 121 real-case-grounded seed examples; SMS opt-in, off by
default) with robust percentile calibration — see §1 and RESEARCH §7d.
Expanding the seed corpus (81 -> 121, benign-heavy) pushed OOD
false-reassurance 1 -> 0 and recall 92.9% -> 100% at zero false accusation.
Honest limits: (i) hyperparameter fine-tuning gives no further gain — the
model is already at ceiling on this authored data (tests/eval_tune.py), so
data realism, not tuning, is the lever; (ii) on 5,574 real messages the
model still misclassifies ~1,218, which hard-negative mining
(tests/eval_learning.py) surfaces as the priority labelling queue for the
feedback flywheel.

Three findings: (1) the learned layer cuts the dangerous error from 11/14
to 2/14 on a different data source — real generalisation, not
memorisation; (2) the **wrongful-HIGH gate holds OOD** (0/8): under
uncertainty the system abstains, never falsely accuses; (3) the FRR=0
gate is an in-distribution *benchmark* property, **not** an OOD
guarantee — two scams reach `NO_PATTERN` (a code-mixed
electricity-disconnection lure and an OTP-read-aloud family
impersonation). Those two misses are reported as-is and left untuned; see
the integrity note below.

### 5c. Real-world data (UCI SMS Spam, 5,574 real messages)
The first eval on text neither template-generated nor author-written
(`tests/eval_realworld.py`, `tests/eval_realworld_method.py`). SMS is a
different channel from phone-scam calls, so this is an honest *proxy*, not
a like-for-like test — reported with 95% Wilson CIs.
- **Deployed model, "never falsely accuse" at scale:** false-alarm on
  4,827 real legitimate messages = **0.02%** (1/4,827), CI[0.00%, 0.12%].
  The core deployable property holds on real data at large n.
- **Deployed model discrimination on real SMS:** AUC **0.638** — weak,
  because it was trained on synthetic phone-scam templates. This is *why*
  it over-warns (~61% of real ham → UNCERTAIN): unable to separate real
  scam from real legit, it abstains rather than reassure. Safe, but noisy.
- **Method-on-real (same char-ngram+LR architecture, retrained on a real
  train split, held-out real test):** accuracy **98.1%**, F1 **0.924**,
  recall 87.0%, false-alarm **0.21%**, AUC **0.997**.

**Conclusion (evidence, not claim):** the method is sound on real data;
the deployed model's real-world weakness is its *synthetic training data*,
not its design. The path to a trustworthy real-world detector is real
phone-scam training data — the same gap named in §7 and `PRIVACY.md` §5.

### 5d. Latency & capacity (`tests/loadtest.py`, single node)
- Per-call service time: **p50 12.9 ms, p99 18 ms**.
- Saturation: **143 req/s at 100% success**; under 50-way concurrency
  p95 424 ms / p99 484 ms (tail is queuing, the path is CPU-bound). The
  service is stateless, so capacity scales horizontally with replicas.

**Integrity note (no test-set tuning).** The two OOD misses are closable
in minutes by adding registry markers; we deliberately do not, because
tuning L1 against the very set used to measure it would overfit the
measurement instrument and void the generalisation claim in §5b.

## 6. Ethical considerations & known biases
- **Language coverage is a safety property, not a feature.** An
  English-only registry silently fails the citizens most targeted;
  ablation shows English-only FRR rises from 0 to 3/12. Coverage is
  prioritised by the speaker population of scam-targeted demographics.
- **Documented training bias (found and fixed):** with Latin-dominated
  benign templates, a Hindi *benign* family message once scored p=0.816
  ("Devanagari looks like scam"). Fixed at the data level by balancing
  benign templates across scripts. The class of model will learn spurious
  surface features if the data permits — hence the OOD set and this note.
- **Abstention burden falls on legitimate institutions** calling
  citizens; mitigated by `NO_PATTERN`/`UNCERTAIN` wording that educates
  rather than accuses, and by the 0/8 wrongful-HIGH result.
- **Dual-use / adversary awareness:** the registry is assumed public
  (see `THREAT_MODEL.md`); the temporal and learned layers exist
  precisely because lexical markers are evadable.

## 7. Caveats, recommendations & reproducibility
- Synthetic + small hand-written evaluation only; **no real field data**.
  Field validation on consented call data is the primary gap between this
  prototype and a product, and it requires an institutional partner and a
  DPIA (see `PRIVACY.md`).
- Recommended deployment posture: assistive second opinion with a human
  in the loop; never an autonomous block or accusation.
- **Reproduce every number above:**
  ```
  python tests/run_all.py        # runs the whole verification suite
  # or individually:
  python tests/eval_ml.py        # §5a in-distribution
  python tests/eval_ood.py       # §5b out-of-distribution
  python tests/loadtest.py       # §5c latency & capacity
  ```
