"""Misinformation-rhetoric detection — the second pillar of the layer.

Same architecture as the scam engine, a new problem domain on the same
channel (forwarded messages) and the same at-risk users. We do NOT verify
facts (that needs external knowledge). We detect the RHETORIC that
misinformation reliably uses, and — like the scam engine — we never assert
truth, only surface manipulation signs so the reader verifies before sharing.

Asymmetric by design: there is no 'this is true' verdict; the worst error we
allow is asking someone to double-check a genuine message, never telling
them a manipulative one is fine.
"""
from shield.engine import _norm

MISINFO_REGISTRY = {
    "forward_pressure": {
        "weight": 2,
        "why": "Pressure to forward/share is the signature of a chain hoax; real news never needs you to spread it.",
        "markers": [
            "forward to", "forward this", "share this with", "share to all",
            "share before", "before it is deleted", "before it's removed",
            "before they delete", "don't break the chain", "do not break",
            "spread the word", "share maximum", "share as much", "make it viral",
            "forward as received", "send to 10", "send to everyone",
            "आगे भेजो", "सबको भेजो", "शेयर करो", "वायरल करो", "डिलीट होने से पहले",
        ],
    },
    "fake_authority": {
        "weight": 2,
        "why": "Vague, unnameable authority ('doctors', 'scientists', 'they') that hides the real source.",
        "markers": [
            "doctors don't want", "doctors won't tell", "they don't want you to know",
            "government is hiding", "govt is hiding", "media won't show",
            "media is hiding", "banned by", "scientists have proven",
            "who confirmed", "nasa confirmed", "big pharma", "the truth they hide",
            "as per experts", "forwarded as received", "a doctor friend",
            "डॉक्टर नहीं बताते", "सरकार छिपा", "मीडिया नहीं दिखा",
        ],
    },
    "miracle_claim": {
        "weight": 3,
        "why": "Miracle cures and absolute claims ('cures cancer', '100% cure') are hallmark health hoaxes.",
        "markers": [
            "cures cancer", "cure for cancer", "kills the virus", "cures corona",
            "cures covid", "miracle cure", "100% cure", "instant cure",
            "natural remedy they", "ancient remedy", "detox your", "boil and drink",
            "drink this every", "prevents all", "cures all disease",
            "कैंसर ठीक", "कोरोना ठीक", "रामबाण इलाज",
        ],
    },
    "fear_manipulation": {
        "weight": 2,
        "why": "Fear, conspiracy and us-vs-them framing that pushes sharing before thinking.",
        "markers": [
            "they are planning", "wake up before", "before it's too late",
            "the truth about", "dangerous chemical in", "will kill you",
            "avoid at all cost", "conspiracy", "they are putting", "secret agenda",
            "protect your family from", "जाग जाओ", "साजिश",
        ],
    },
    "unverified": {
        "weight": 1,
        "why": "Credibility theatre — 'this is 100% true', 'shocking', with no checkable source.",
        "markers": [
            "100% true", "this really happened", "true story", "must read",
            "shocking truth", "you won't believe", "forwarded many times",
            "genuine message", "very important message", "please read carefully",
            "सच है", "जरूर पढ़ें", "बहुत जरूरी",
        ],
    },
}

HIGH_MIN_CATEGORIES = 2
HIGH_MIN_SCORE = 4
UNCERTAIN_MIN_SCORE = 2

ACTIONS = {
    "HIGH_RISK": ("This message uses classic misinformation tactics. Do NOT "
                  "forward it. Verify on an official fact-check source (e.g. "
                  "PIB Fact Check) before believing or sharing."),
    "UNCERTAIN": ("Some misinformation signs are present. Don't forward yet — "
                  "check the facts on a trusted source first."),
    "NO_PATTERN": "No obvious misinformation tactics found. Still, verify before forwarding anything important.",
}


def detect(text: str) -> dict:
    """Return a misinformation-rhetoric assessment mirroring the scam engine:
    a level, the categories hit, a plain reason, and an action."""
    t = _norm(text)
    hits, score = {}, 0
    for cat, spec in MISINFO_REGISTRY.items():
        matched = [m for m in spec["markers"] if m in t]
        if matched:
            hits[cat] = matched
            score += spec["weight"]

    if len(hits) >= HIGH_MIN_CATEGORIES and score >= HIGH_MIN_SCORE:
        level = "HIGH_RISK"
    elif score >= UNCERTAIN_MIN_SCORE:
        level = "UNCERTAIN"
    else:
        level = "NO_PATTERN"

    explanation = [f"{cat.replace('_', ' ').title()}: {MISINFO_REGISTRY[cat]['why']}"
                   for cat in hits]
    return {
        "level": level,
        "score": score,
        "categories": {k: v for k, v in hits.items()},
        "explanation": explanation,
        "action": ACTIONS[level],
    }
