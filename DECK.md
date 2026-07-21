# DhvaniShield — Hackathon Deck

A slide-by-slide script for a ~6-minute pitch. Every number is real and
reproducible (`python tests/run_all.py` → 13/13). Lead with the demo and
the honesty; that combination is what wins with technical judges.

Judging-criteria map (fill your event's weights):
Innovation · Technical depth · Impact · Feasibility · Presentation.

---

## Slide 1 — Title / hook  (20s)
**DhvaniShield**
> The scam-call guardian that explains *how* you're being manipulated —
> and is built so it can never tell you a scam is "safe."

Say: "Every day, someone's parent gets a call from a fake CBI officer and
loses their life savings in 40 minutes. We built the second opinion that
reaches them at that exact moment."

Show: the app name + the Manipulation Meter graphic.

---

## Slide 2 — The problem  (40s)
- "Digital arrest" and impersonation scams are a national-scale problem —
  flagged by I4C/MHA, called out by the PM. Losses run to thousands of crores.
- The victims are disproportionately **elderly, vernacular-speaking, and
  disabled** — the people existing tools serve worst.
- The scam works through **fear + isolation**, over a long live call. The
  victim is told "don't hang up, don't tell anyone."

Say: "The damage doesn't happen on the number. It happens in the words."

---

## Slide 3 — Why existing tools miss it  (30s)
- Truecaller / carrier labels answer **"who is calling?"** — a number
  database. But these scams use fresh SIMs, spoofed IDs, WhatsApp calls,
  and official-looking numbers. By the time a number is flagged, it's gone.
- Nobody reads the **content** of the manipulation. That's the gap.

Say: "Truecaller tells you who's calling. We tell you whether what they're
*saying* is a scam."

---

## Slide 4 — The insight  (30s)
Three design choices, each a differentiator:
1. **Detect the technique, not the number** — authority → isolation →
   urgency → money. The coercion grammar is invariant even when the number changes.
2. **Asymmetric safety** — there is *no "safe" verdict*. A false alarm
   costs one phone call; a false reassurance costs a life's savings.
3. **Silence is the feature** — it says nothing on normal calls, and fires
   once, unmissably, at the moment before money moves.

---

## Slide 5 — LIVE DEMO  (90s)  ← the heart of the pitch
Run `check.py` live (see DEMO.md for the exact script). Show, in order:
1. A **normal message** → the guardian stays silent (`--ambient`). No nagging.
2. A **digital-arrest scam** → 🔴, the Manipulation Meter lights up, and the
   **category-tailored** action ("Hang up. No police arrests you by call.").
3. A **sextortion scam** → completely *different* correct advice
   ("Don't pay. Keep evidence. It's not your fault.").
4. Switch `--profile=blind` → the same alert as a spoken script + haptic +
   "call someone you trust." Accessibility is real, not a checkbox.

Say while demoing: "Notice it never says 'you're safe', it never accuses a
real caller, and it explains the manipulation instead of just blocking."

---

## Slide 6 — How it works  (40s)
A **committee of small experts**, fully on-device, ~7MB, CPU-only:
- **L1 lexical** — auditable marker registry (en/hi/mr).
- **L2 semantic** — intent-similarity to known scam families (catches
  paraphrases and *new* scam types).
- **L3 temporal** — the coercion-trajectory (fires before the money stage).
- **Monotone gate** — the learned layers may only *escalate*, never
  downgrade, so false-reassurance is structurally bounded.

Say: "Every verdict is explainable — it names the exact words and the scam
family. No black box."

---

## Slide 7 — Results (measured, not claimed)  (45s)
Reproducible via `python tests/run_all.py` → **13/13 gates green**.

| | result |
|---|---|
| Never falsely accuses (4,827 **real** messages) | **0.02%** false alarm |
| Out-of-distribution scams | **100% recall, 0 false-reassurance** |
| Red-team (evasion + scam types it wasn't built for) | **100% recall, 0 false-accusation** |
| Per-call latency / capacity | **13 ms** / **143 req/s** |
| Method on real data (retrained) | **98% acc, F1 0.92** |

Say: "These are held-out and reproducible. And I found and fixed a real
calibration bug that was silently hurting recall — the gates now catch it."

---

## Slide 8 — Trust: why anyone would use it  (35s)
- **Pull-based v1** — you forward a suspicious message; zero call access,
  nothing to grant.
- **Collect-nothing** — on-device, process-and-delete, content-free
  telemetry. *You can't leak what you never store.* No central honeypot.
- **Distributed by trust** — a child sets it up for a parent; a bank/telco
  offers it. The user never trusts a stranger.

Say: "The ask is inverted from Truecaller's — not 'trust me with your data',
but 'a tool that keeps your data on your side.'"

---

## Slide 9 — Accessibility = the core market  (30s)
The most-targeted are the most-vulnerable, so we designed for them first:
- **blind** → spoken + audio earcon · **deaf** → pictogram + haptic ·
  **colour-blind** → shape + word, never colour · **low-literacy** → icons +
  easy-read · **cognitive/elderly** → one step + family code word.
- The **family code word** defeats even AI voice-cloning, and costs nothing.

Say: "This isn't compliance. It's who the scammers actually target."

---

## Slide 10 — It gets better on its own (the flywheel)  (30s)
- Honest finding: accuracy can't be fine-tuned out of synthetic data — it
  needs *real* scam data, which no dataset has.
- So every user's consented "yes, that was a scam" becomes a **redacted,
  anonymous training example**. Hard-negative mining picks the highest-value
  labels. The model — and the proprietary dataset (the moat) — compounds with use.

---

## Slide 11 — Honest limits & roadmap  (20s)
What we're *not* hiding:
- Real-world accuracy needs the flywheel's real data; current numbers are on
  documented-case + cross-channel proxy data.
- Distribution (the WhatsApp wedge, a pilot partner) is the real bottleneck.

Roadmap: WhatsApp pull-based pilot → on-device screening → carrier layer.

Say: "A system that names its own limits is the one you can trust."

---

## Slide 12 — Close / the ask  (20s)
> **DhvaniShield: explains the manipulation in real time, in your language,
> for the people scammers target — and can never tell you a scam is safe.**

The ask: a pilot partner (a bank / telco / helpline) and the first real
labeled calls. Everything else is built, tested, and on GitHub.

---

### Timing (≈6 min): 1(20) 2(40) 3(30) 4(30) 5(90) 6(40) 7(45) 8(35) 9(30) 10(30) 11(20) 12(20)
### If you only get 3 minutes: slides 1, 4, **5 (demo)**, 7, 12.
