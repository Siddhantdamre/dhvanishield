# Positioning & Trust Model — DhvaniShield

This document answers the two questions every serious reviewer, partner,
and user asks first: *how is this different from Truecaller?* and *why
would anyone trust it with something as sensitive as their calls?* The
answers are deliberately honest — including where the approach is hard.

## 1. The one line
> **Truecaller tells you *who* is calling. DhvaniShield tells you whether
> what they are *saying* is a scam — in real time, in your language, and
> without collecting your data.**

## 2. Why not Truecaller / number-reputation tools
Truecaller, carrier spam labels, and blocklists all work on **the number**:
crowdsourced reputation of the caller ID. That is a huge network effect and
we do **not** try to beat them there.

But the scams that cause the most harm — digital arrest, fake CBI/customs,
KYC coercion — **do not lose on the number**:
- they come from fresh SIMs, spoofed IDs, WhatsApp calls, and numbers that
  look official;
- by the time a number is flagged, the scammer has discarded it;
- number-based defense is therefore *always one step behind* a disposable
  identifier.

DhvaniShield detects the **manipulation technique** — authority → accusation
→ isolation → urgency → money → access — which stays constant even as the
number changes every hour. We compete on the axis where the incumbent is
**structurally blind**: a caller-ID product never sees the *content* of the
call, and a data-harvesting business model will never go privacy-first.

| | Number-reputation (Truecaller etc.) | DhvaniShield |
|---|---|---|
| Detects | who is calling (the number) | what is being done to you (the script) |
| Fails when | number is fresh / spoofed / "official" | — (technique is invariant) |
| Output | block / "spam" label | explains the manipulation, guides the action |
| User served | app-fluent, English-first | elderly, vernacular, disabled |
| Data model | uploads your contacts | collects nothing; on-device |

**Honest caveat:** content/technique detection is *harder* and less mature
than a number lookup. That difficulty is exactly why the space is open —
and why the real moat is data (see the flywheel), not the algorithm.

## 3. The trust question — answered by *not* asking for access
"Why would anyone let your software listen to their calls?" — they
shouldn't, and the product is designed so they don't have to.

- **v1 is pull-based.** The user forwards a suspicious message or types what
  the caller said *when they choose to ask.* Zero standing access, zero
  listening, nothing to grant. The system only ever sees what the user
  hands it, in the moment of doubt. (`POST /v1/check`, WhatsApp webhook,
  `check.py`.)
- **Collect-nothing beats trust-me.** You cannot leak what you never store.
  Processing is on-device, process-and-delete; telemetry is content-free;
  the only stored data is the *opt-in, redacted, anonymous* feedback corpus.
  There is no central vault of call recordings to breach — which is the only
  thing that makes a service a target. This is written down and tested:
  [`PRIVACY.md`](PRIVACY.md), [`THREAT_MODEL.md`](THREAT_MODEL.md).
- **The ask is inverted from Truecaller's.** Not "trust me with your data,"
  but "install a tool that watches *your* phone *for* you and tells no one,
  not even us."
- **Users don't have to trust a stranger.** Distribution is through a trusted
  intermediary: a worried adult child sets it up for a parent, or a
  bank / telco / government helpline offers it under their own brand
  (B2B2C). The end user trusts their child or their bank; we are the engine.

## 4. "It could be hacked / misused"
Every piece of software carries risk; the honest mitigations are
*architectural*, not promises:
- **Minimal attack surface:** no call access in v1, no central data store,
  on-device inference (nothing to exfiltrate at scale).
- **Kerckhoffs-safe:** the registry and method are assumed public; security
  does not depend on their secrecy (see `THREAT_MODEL.md`).
- **Never false-accuses:** measured 0.02% on ~4,800 real messages, so a
  compromise cannot easily weaponise it into a defamation tool.
- **For a real deployment:** third-party security + privacy (DPDP) audit —
  named as the deploying partner's duty, not glossed over.

## 5. The honest product arc
```
v1  pull-based, on-device, collect-nothing   -> zero-access value in the moment of doubt
      + consent-based feedback (the flywheel) -> real phone-scam data nobody else has
v2  better model from that real data          -> accuracy climbs; data becomes the moat
v3  ambient / on-device call screening        -> ONLY safe because v1 built the
                                                 collect-nothing foundation first
```
The scary "listen to everything" product is not v1 — it is a maybe-never v3
that becomes acceptable *because* the privacy-first foundation exists first.

## 6. What is genuinely still unproven (stated plainly)
- Real-world accuracy needs the flywheel's real data; current numbers are on
  documented-case and cross-channel proxy data (see `MODEL_CARD.md`).
- Distribution (the WhatsApp wedge, the B2B2C partner) is go-to-market work,
  not code, and is the true bottleneck to impact.
- The ambient path (v3) carries real risk and is deliberately deferred.
