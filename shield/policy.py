"""Interaction policy — "silence is the feature".

The classifier produces three internal states (HIGH_RISK / UNCERTAIN /
NO_PATTERN). This module decides what the USER actually experiences,
because a tool that interrupts a normal call is torn off the wall before
the one call that matters. On real messages the raw model would have said
"be careful, verify" on ~61% of legitimate ones — unusable as a live
guardian. The fix is not a different model; it is a presentation policy.

Two modes, because irritation is context-dependent:

  AMBIENT   — always-on background listener (on-device call screening).
              The user did NOT ask. So we stay SILENT unless the call is a
              confident, structured scam (HIGH_RISK — which the engine only
              reaches once the coercion trajectory completes, i.e. at the
              money/credentials moment: the "turn left now"). UNCERTAIN is
              held silently ("keep watching"), never pushed. This is what
              takes the 61% down to the ~0.02% of calls that truly warrant
              an interruption.

  PROACTIVE — the user forwarded a message / asked "is this real?". They
              WANT an answer, so we always respond (silence would be worse).

The classifier is unchanged and still never emits "safe": this is a policy
on top of it, not a downgrade of it.
"""
from dataclasses import dataclass

from shield.access import accessible_bundle

AMBIENT = "ambient"
PROACTIVE = "proactive"

# Action-first, non-accusatory headline. We warn against the irreversible
# ACTION, never accuse the caller — so even the rare false positive gives
# advice that is still correct ("don't wire money to a caller").
HEADLINE = {
    "HIGH_RISK": {
        "en": "Don't send money or share any code. Hang up now.",
        "hi": "पैसे मत भेजिए, कोई कोड मत बताइए। फोन अभी रख दीजिए।",
        "mr": "पैसे पाठवू नका, कोणताही कोड सांगू नका. फोन आत्ताच ठेवा.",
    },
    "UNCERTAIN": {
        "en": "Before you do anything, don't send money or share a code — check first.",
        "hi": "कुछ भी करने से पहले, पैसे मत भेजिए या कोड मत बताइए — पहले जाँच लीजिए।",
        "mr": "काहीही करण्यापूर्वी, पैसे पाठवू नका किंवा कोड सांगू नका — आधी तपासा.",
    },
    "NO_PATTERN": {
        "en": "Nothing suspicious found. Still, never send money or codes on a call.",
        "hi": "कुछ संदिग्ध नहीं मिला। फिर भी, कॉल पर कभी पैसे या कोड मत दीजिए।",
        "mr": "संशयास्पद काही आढळले नाही. तरीही, कॉलवर कधीही पैसे किंवा कोड देऊ नका.",
    },
}

# Haptic cue a device layer plays, so deaf / not-looking users feel it.
HAPTIC = {"HIGH_RISK": "URGENT", "UNCERTAIN": "SOFT", "NO_PATTERN": "NONE"}


@dataclass
class Interaction:
    surfaced: bool          # does the user experience anything at all?
    state: str              # "alert" | "silent"
    level: str              # internal verdict (kept for logs, not shown when silent)
    watching: bool          # ambient is holding an UNCERTAIN (keep listening)
    alert: dict | None      # the single accessibility-first payload, or None


def build_alert(level: str, lang: str = "en",
                trusted_contact: str | None = None) -> dict:
    """The ONE moment, rendered for every sense at once — so it lands
    whether the user can see, hear, or only feel the phone. One
    instruction, one action, one tap to a trusted person."""
    bundle = accessible_bundle(level, lang)
    who = trusted_contact or "someone you trust"
    call_prompt = {
        "en": f"Call {who} now",
        "hi": f"अभी {who} को कॉल कीजिए",
        "mr": f"आत्ताच {who} ला कॉल करा",
    }.get(lang, f"Call {who} now")
    return {
        "headline": HEADLINE[level].get(lang, HEADLINE[level]["en"]),
        "speech": bundle["speech"],       # blind / not looking
        "picto": bundle["picto"],         # deaf / low-literacy
        "haptic": HAPTIC[level],          # deaf / not looking
        "call_person": {"name": trusted_contact, "prompt": call_prompt},
        "codeword_tip": bundle["codeword_tip"],
        "level": level,
    }


def decide(level: str, mode: str = AMBIENT, lang: str = "en",
           trusted_contact: str | None = None) -> Interaction:
    """Map an internal verdict to what the user experiences."""
    if mode == PROACTIVE:
        # user asked — always answer (even a green "nothing found")
        return Interaction(True, "alert", level, False,
                           build_alert(level, lang, trusted_contact))

    # AMBIENT — silence unless it is a confident, structured scam.
    if level == "HIGH_RISK":
        return Interaction(True, "alert", level, False,
                           build_alert(level, lang, trusted_contact))
    # UNCERTAIN: keep watching, but do not interrupt. NO_PATTERN: nothing.
    return Interaction(False, "silent", level, level == "UNCERTAIN", None)
