# Impact & SDG Alignment

Written in the honest frame this project uses everywhere: a clear *mechanism*
of impact, who benefits, and an explicit line between what is *demonstrated*
and what is *potential pending a field deployment*. No unsourced numbers.

## The problem, plainly
Scam and social-engineering fraud transfers money from the people least able
to absorb the loss to organised criminal networks. In India it is a
government-flagged, large-scale problem (I4C/MHA advisories; "digital arrest"
raised at the national level). The victims are disproportionately the
elderly, non-English-speaking, low-literacy, and disabled — the people least
served by existing, English-first, app-fluent tools. A lost life-savings is
not only financial; it drives documented trauma, depression, and in reported
cases, suicide.

## SDG alignment — with the mechanism, not slogans
| SDG | Target | Mechanism of impact here |
|---|---|---|
| **16 Peace, Justice, Strong Institutions** | 16.4 reduce illicit financial flows & organised crime; 16.5 reduce fraud | Detecting and interrupting scams at the moment of coercion reduces the flow of funds to criminal networks. |
| **10 Reduced Inequalities** | 10.2 empower & include all, irrespective of age/disability | Accessibility-first (blind/deaf/low-literacy profiles), vernacular (en/hi/mr), on-device — built for the *complement* of the tech-fluent user. Protection reaches those usually excluded. |
| **3 Good Health & Well-being** | 3.4 mental health & well-being | Preventing victimisation avoids the trauma/depression that follow a scam; the misinformation pillar reduces health-hoax harm. |
| **1 No Poverty** | 1.4 resilience of the vulnerable | A single prevented scam can be the difference between security and destitution for a low-income or retired household. |
| **9 Industry, Innovation & Infrastructure** | 9.1 reliable, inclusive infrastructure | Increases trust in digital-payment infrastructure that the vulnerable are otherwise driven away from. |

## The equity core (why this is a *justice* tool, not just a security one)
The distinguishing design choice is that the most-targeted are the
most-vulnerable, so the system is built for them **first**: colour-blind-safe
alerts, spoken/haptic/pictogram renderings, the family code word, one-tap
"call someone you trust", and vernacular language. This is distributive
justice encoded as engineering — protection allocated to those with the least
means to protect themselves.

## Demonstrated vs potential (the honest line)
- **Demonstrated (reproducible):** the detection, calibration, selective
  prediction, accessibility, and cross-domain generalisation results in this
  repo (`python tests/run_all.py`).
- **Potential, pending a field pilot:** *population-level* impact — fraud
  prevented, victims protected, demographic reach. We do **not** claim
  measured SDG outcomes yet. Establishing them requires a deployment with
  pre-registered metrics (prevented-loss value, reach into target
  demographics, false-alarm burden on institutions) and an independent
  evaluation. That is the honest next step, stated as such.

## Why this is a frontier-AI-safety project, not just a fraud tool
The system is a small, concrete instance of the properties safe AI is
supposed to have:
- **Knows when it is wrong** — calibrated confidence + selective prediction
  that defers to a human to hold a target error rate (`shield/calibration.py`,
  `tests/eval_calibration.py`).
- **Interpretable** — every verdict decomposes into named manipulation
  strategies, not a black-box score (`shield/manipulation.py`).
- **Asymmetric harm model** — it is structurally forbidden from the
  catastrophic error (telling a victim a scam is "safe") and never falsely
  accuses; it abstains under uncertainty.
- **Generalises by abstraction** — detects manipulation in domains it never
  saw (`tests/eval_generalization.py`), a step toward robustness to novel
  attacks.
- **Honest about limits** — every result names its scope; nothing is
  overclaimed. (This document included.)

That combination — harm reduction for the vulnerable, calibrated humility,
interpretability, and intellectual honesty — is the same value set that
defines beneficial, safety-first AI. It is why this is defensible not just as
a product, but as a research and mission contribution.
