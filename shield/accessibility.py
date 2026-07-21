"""Accessibility profiles — the alert, tuned to how each user perceives.

Most scam tools assume a sighted, literate, app-fluent user — exactly the
person scammers do NOT target. This module renders the single alert for
whichever disability profile the user (or the family member who set it up)
selected, once. It composes the existing spoken/pictogram/code-word
renderings (shield/access.py) with the scam category (shield/categories.py)
and adds features specifically for disabled users:

  * COLOUR-BLIND SAFE: risk is carried by SHAPE + WORD, never colour alone.
  * HAPTIC CODES: distinct vibration patterns per risk (deaf / not looking).
  * EARCONS: audio-cue spec a client plays for blind users.
  * EASY-READ: one grade-1 action for low-literacy / cognitive users.
  * CALL-A-PERSON: one tap to a trusted human — the counter to isolation.

profiles: default | blind | deaf | low_literacy | cognitive | colorblind
"""
from shield.access import accessible_bundle
from shield.categories import categorize

PROFILES = ("default", "blind", "deaf", "low_literacy", "cognitive", "colorblind")

# Colour-blind safe: SHAPE + WORD, so the meaning survives with no colour.
SHAPE = {
    "HIGH_RISK": ("⛔", "STOP - DANGER"),      # ⛔
    "UNCERTAIN": ("△", "CHECK FIRST"),        # △
    "NO_PATTERN": ("✓", "LOOKS OK"),          # ✓
}
HAPTIC = {
    "HIGH_RISK": "long-long-long (urgent)",
    "UNCERTAIN": "short-short",
    "NO_PATTERN": "none",
}
EARCON = {
    "HIGH_RISK": "three rising urgent tones",
    "UNCERTAIN": "two soft tones",
    "NO_PATTERN": "one soft tone",
}
# Grade-1 easy-read, one action, for low-literacy / cognitive users.
EASY = {
    "HIGH_RISK": {"en": "STOP. Do not pay. Put the phone down.",
                  "hi": "रुकिए। पैसे मत दीजिए। फोन रख दीजिए।"},
    "UNCERTAIN": {"en": "Wait. Do not pay yet. Ask someone you trust.",
                  "hi": "रुकिए। अभी पैसे मत दीजिए। किसी अपने से पूछिए।"},
    "NO_PATTERN": {"en": "Looks okay. Still, never pay on a call.",
                   "hi": "ठीक लगता है। फिर भी, कॉल पर कभी पैसे मत दीजिए।"},
}


def _call_prompt(who, lang):
    who = who or ("किसी अपने" if lang == "hi" else "someone you trust")
    return f"अभी {who} को कॉल कीजिए" if lang == "hi" else f"Call {who} now"


def accessible_alert(level: str, text: str = "", profile: str = "default",
                     lang: str = "en", trusted_contact: str | None = None) -> dict:
    """Return the alert rendered for the given disability profile."""
    if profile not in PROFILES:
        profile = "default"
    bundle = accessible_bundle(level, lang)
    shape_sym, shape_word = SHAPE[level]
    cat = categorize(text) if (text and level != "NO_PATTERN") else None
    cat_action = cat["action"].get(lang, cat["action"]["en"]) if cat else None
    call = {"name": trusted_contact, "prompt": _call_prompt(trusted_contact, lang)}

    # every profile always carries: what kind of scam + the tailored action,
    # the shape+word (never colour alone), and the one-tap trusted contact.
    base = {
        "level": level,
        "profile": profile,
        "shape": shape_sym,
        "shape_word": shape_word,
        "category": (cat and cat["category"]),
        "category_name": (cat and cat["name"]),
        "why": (cat and cat["why"]),
        "action": cat_action or bundle["speech"],
        "call_person": call,
    }

    if profile == "blind":
        base.update(mode="audio-first", speech=bundle["speech"],
                    earcon=EARCON[level], haptic=HAPTIC[level],
                    note="no visual reliance; everything is spoken")
    elif profile == "deaf":
        base.update(mode="visual+haptic", picto=bundle["picto"],
                    haptic=HAPTIC[level], flash=(level == "HIGH_RISK"),
                    note="no audio reliance; visual + vibration")
    elif profile == "low_literacy":
        base.update(mode="pictogram", icon=(cat and cat["icon"]) or shape_sym,
                    picto=bundle["picto"], easy=EASY[level].get(lang, EASY[level]["en"]),
                    note="icons + one very short action, minimal text")
    elif profile == "cognitive":
        base.update(mode="one-step", easy=EASY[level].get(lang, EASY[level]["en"]),
                    codeword_tip=bundle["codeword_tip"],
                    note="one step only; a trusted person is one tap away")
    elif profile == "colorblind":
        base.update(mode="shape+text", speech=bundle["speech"], picto=bundle["picto"],
                    haptic=HAPTIC[level],
                    note="meaning is shape + word, never colour alone")
    else:  # default — every channel at once
        base.update(mode="all-channels", speech=bundle["speech"],
                    picto=bundle["picto"], haptic=HAPTIC[level],
                    earcon=EARCON[level], codeword_tip=bundle["codeword_tip"])
    return base
