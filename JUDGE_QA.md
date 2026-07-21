# DhvaniShield — Judge Q&A

The point of these answers is not to dodge — it's that a project which names
its own limits is the one judges trust. Keep answers to ~20 seconds.

**"Isn't 100% just overfitting?"**
> It was, within one data family — so I built an independent out-of-distribution
> set and an adversarial red-team set. In-distribution false-reassurance is 0;
> out-of-distribution it's 0/14 with 100% recall; on the red-team it caught
> scam types it was never built for. And I fixed a calibration bug that was
> silently hurting recall — the tests now *gate* on it. Reproducible: 13/13.

**"How is this different from Truecaller?"**
> Truecaller answers "who is calling" — a number database. These scams use
> fresh, spoofed, or official-looking numbers, so number-reputation is always
> one step behind. We detect the *technique* — the coercion script — which
> stays constant even when the number changes. Different axis, and one they
> can't follow us to, because their model is data-harvesting and ours is
> collect-nothing.

**"Why would anyone let your app listen to their calls?"**
> They shouldn't, and v1 doesn't ask them to. It's pull-based: you forward a
> suspicious message when you choose. Zero standing access, nothing stored,
> on-device. You can't leak what you never collect — there's no central vault
> to hack. That's the whole trust model.

**"Is any of this real, or just a demo?"**
> The pipeline is real and tested end-to-end — 13 verification suites, live
> API, on-device model. On 5,574 *real* messages it false-accuses 0.02% of the
> time. What's *not* proven yet is real-world phone-scam accuracy, because no
> public dataset exists — and I built the consented feedback flywheel exactly
> to collect it. I'll tell you what's measured and what's still a proxy.

**"Why not a deep-learning model / an LLM?"**
> Three reasons it would be worse here: it wouldn't run on-device for free, it
> wouldn't be auditable (every verdict here names the exact words), and on our
> data size it would overfit. I even proved fine-tuning gives no gain — the
> model's already at ceiling on available data. The bottleneck is data, not
> model size, so a bigger model is the wrong lever.

**"What about false alarms — won't it annoy people?"**
> At the classifier level it errs toward caution, yes. But the interaction
> policy hides that: on 4,827 real messages the ambient guardian interrupts
> 0.02% of them, versus 61% for a naive "warn on anything" approach. It stays
> silent until it's confident, and it never falsely *accuses* a real caller.

**"What's the business model?"**
> B2B2C. A worried adult child installs it for a parent, or a bank / telco /
> government helpline offers it under their brand. The moat isn't the code —
> it's the proprietary real-scam dataset the flywheel builds, plus the
> privacy-first, accessible, vernacular positioning big players won't copy.

**"What about accessibility — is it real?"**
> Six profiles, tested: blind gets a spoken script + earcon, deaf gets
> pictogram + haptic, colour-blind gets shape+word not colour, low-literacy
> gets icons + easy-read, cognitive gets one step + the family code word. It's
> a gate in the test suite, not a slide. And it's the core market — the
> most-targeted victims are the most-vulnerable.

**"What would you do with more time / funding?"**
> One thing: a pilot with a real partner to get real labeled calls. Everything
> technical is built and reproducible. The next unit of value is data and
> distribution, not more features — and I can say that because I measured it.

---
**The meta-answer for anything you don't know:** "Honestly, I haven't validated
that yet — here's what I *have* measured, and here's how I'd test it." That
sentence wins more points than a confident guess.
