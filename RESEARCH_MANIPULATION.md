# Manipulation-Strategy Detection: a domain-general primitive

A research note in the honest frame: *specific limitation → gap → method →
evidence → limits → open question.* No "world's first" claims — related
work on influence detection, coercion, and social-engineering exists. The
contribution here is a **measured cross-domain generalization gap** and a
small **reusable primitive**.

## 1. The specific limitation
Keyword / registry detectors — including this project's own scam registry —
recognise the **vocabulary of one domain**. They do not transfer. A coercive
sales pitch, a guilt-trip, or a workplace-coercion message contains no scam
words, so a scam detector is effectively blind to it. Measured: on
manipulation drawn from domains the scam registry never saw, its recall is
**30%** and its ranking ROC-AUC is **0.65** — barely above chance.

## 2. The gap we target
A representation of the manipulation **strategy** itself, independent of
domain or vocabulary. We ground it in Cialdini's principles of influence
(authority, scarcity, social proof, reciprocity, commitment, liking) plus
three coercion levers (fear, urgency, isolation). Each strategy is defined by
exemplars drawn from *multiple* domains, so an activation reflects the
tactic, not the topic.

## 3. Method (`shield/manipulation.py`)
`analyze(text)` returns:
- a **manipulation vector** — activation of each strategy (exemplar
  similarity);
- a scalar **pressure score** — weighted sum over active strategies
  (manipulation *stacks* strategies, so the sum, not the count, is the
  signal);
- **dominant strategies** — a feature-contribution explanation;
- an **uncertainty** value — a margin heuristic (see limits).

## 4. Evidence (`tests/eval_generalization.py`, reproducible)
On a cross-domain probe (coercive sales, guilt-trips, workplace coercion,
love-bombing, high-pressure recruitment) vs benign messages from the same
domains:

| representation | ROC-AUC (rank manip > benign) | recall |
|---|---|---|
| keyword / scam registry | 0.65 | 30% |
| **strategy engine** | **0.95** | **90%** at 0% false-alarm |

The strategy representation ranks unseen-domain manipulation above benign
95% of the time, versus 65% for the keyword baseline — evidence of
**abstraction over memorisation**. The threshold-free AUC is the primary
number; the 90%/0% operating point is Youden-optimal *on this probe*.

## 4a. The honest number: real data, not probes
The §4 result (AUC 0.95) is on a small **hand-authored** probe. Tested on
**5,574 real messages** written by real scammers and real people
(`tests/eval_manip_real.py`), the same engine — never trained or tuned on
this data — scores **AUC 0.659**, versus **0.502** for the phone-domain
keyword registry (pure chance on this channel). So:
- the strategy representation **does** transfer to genuine, third-party
  manipulation and clearly beats keywords — but
- it is **far weaker on real data (0.659) than on our probe (0.95)**. The
  gap is the honest correction: hand-authored probes overstate performance.

Diagnostic: real fraud and real legitimate messages share most strategies
(urgency, authority, commitment); the engine's main discriminator is
*isolation* (fraud) vs *liking_trust* (legit). Weak separation follows from
genuinely overlapping tactics — a real limit, not a bug. **0.659 is the
number to defend; 0.95 is not.**

## 5. Honest limits (named, not hidden)
- **Not compositional reasoning.** This is exemplar similarity, not
  inference over a structured argument. It captures *which* strategies are
  present, not *how* they compose into an argument.
- **Small, hand-authored probe.** 20 messages the author wrote — a probe
  that motivates the direction, not a benchmark. A large, multi-domain,
  independently-labelled corpus is required to make a strong claim.
- **Uncertainty is a heuristic, not calibrated.** The `uncertainty` field is
  a distance-to-boundary proxy. Reliable, calibrated uncertainty
  ("I'm 42% sure because the evidence is contradictory") remains an open
  problem here, as in the field.
- **Operating threshold is probe-calibrated.** Only the AUC is
  threshold-free.

## 6. The reframe and the open question
Scam detection becomes *one application* of a general pipeline:

    language -> strategy vector -> risk -> explanation

The same primitive applies wherever human decision-making is attacked:
scams, coercive sales, insider threats, social engineering, extremist
recruitment. The durable research question this project can pursue:

> Can a system **infer** manipulation strategy, **estimate** its own
> uncertainty, and **explain** its reasoning, in a way that **generalises to
> attack types it has never seen**?

This note establishes a first, measurable step on the first and third parts
(generalisation + explanation). The open, harder parts — calibrated
uncertainty, compositional reasoning, and continual learning without
forgetting — are stated as future work, and are where the frontier actually
is.

## 7. The strongest test: does it transfer from humans to AI attacks?
If manipulation strategies are truly target-invariant, an engine built on
human scams should — with no AI-attack data — flag the SOCIALLY-ENGINEERED
attacks on AI systems (prompt injection / jailbreaks that use authority,
urgency, roleplay, reciprocity, social proof). We tested this
(`tests/eval_ai_manipulation.py`).

Honest arc:
1. **Naive transfer failed.** The unchanged human engine reached only
   AUC 0.59 — it decomposed AI attacks correctly (an "admin authorises you
   to ignore the rules" prompt reads as authority + social proof + urgency)
   but did not *discriminate* them from ordinary directive prompts.
2. **Diagnosis.** AI attacks carry a primitive human scams lack: **rule
   override** ("ignore your instructions", "bypass your guidelines"). This
   refines the theory — manipulation has a shared Cialdini core PLUS
   target-specific primitives.
3. **Refinement.** Adding a domain-general `override` strategy (rule
   subversion, which also appears in coercion and insider threat) raised
   transfer to **AUC 0.78** — recall 70% at 10% false-alarm — without harming
   human-scam generalisation (still AUC 0.94).

Claim, stated at its true strength: **influence strategies are largely
target-invariant.** One interpretable engine spans human scams AND AI
social-engineering attacks, detecting and *explaining* both in a shared
vocabulary. This is **meaningful partial transfer, not a production
jailbreak defence** — encoding/technical jailbreaks (base64, token games)
carry no social strategy and are out of scope by construction, and the
0.78 figure is on a small hand-authored probe needing held-out validation.

Why it matters: it is direct evidence for the deepest version of the thesis
— that manipulation is a *domain- and target-invariant* phenomenon — and it
connects consumer-safety detection to AI-safety (social-engineering of
models) through a single, interpretable primitive. That bridge is the novel
contribution; the honest limits above are stated so it can be defended with
data rather than rhetoric.
