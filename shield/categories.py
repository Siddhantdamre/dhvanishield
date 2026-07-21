"""Scam categorisation — the right advice for the specific scam.

Binary "scam / not" is not enough: the correct action for sextortion
("do not pay, keep evidence, you are not at fault") is nothing like the
one for a KYC-phishing call ("open your bank app yourself"). This module
maps a flagged call to its scam FAMILY and returns family-specific,
action-first guidance, so the tool works for any scenario, not one.

Simple and auditable by design: a per-category cue-word score, boosted by
the L2-semantic family match (shield/semantic.py). argmax wins; if nothing
matches it falls back to generic_scam. No new model, no training.
"""
from shield.semantic import SEMANTIC
from shield.engine import _norm

# family (from shield/semantic.py) -> category key
FAMILY_MAP = {
    "digital_arrest": "digital_arrest", "kyc_link": "kyc_phishing",
    "refund_collect": "refund_upi", "sextortion": "sextortion",
    "loan_harassment": "loan_harassment", "fake_job": "job_task",
    "lottery_fee": "lottery_prize", "remote_support": "tech_support",
    "disconnection": "utility_disconnection",
    "deepfake_emergency": "impersonation_family",
}

CATEGORIES = {
    "digital_arrest": {
        "name": "Digital arrest / fake police",
        "icon": "👮🚫",
        "cues": ["arrest", "digital arrest", "cbi", "police", "customs officer",
                 "enforcement", "warrant", "case registered", "narcotics",
                 "गिरफ्तार", "पुलिस", "सीबीआई", "वारंट", "अटक"],
        "why": "No real agency ever arrests you over a phone or video call, or asks for money to 'clear' a case.",
        "action": {"en": "Hang up now. No police arrests you by call. Never transfer money to 'clear a case'. Call 1930.",
                   "hi": "फोन तुरंत रखिए। पुलिस कॉल पर गिरफ्तार नहीं करती। 'केस' के लिए पैसे कभी मत भेजिए। 1930 पर कॉल कीजिए।"},
    },
    "kyc_phishing": {
        "name": "Fake KYC / account-block",
        "icon": "🏦🎣",
        "cues": ["kyc", "account block", "account will be blocked", "card number",
                 "cvv", "verify your account", "update your", "click the link",
                 "केवाईसी", "खाता बंद", "लिंक"],
        "why": "Your bank never asks for KYC, card number, CVV or OTP over a call or link.",
        "action": {"en": "Do not share any code, card number or link details. Open your bank app yourself to check.",
                   "hi": "कोई कोड, कार्ड नंबर या लिंक की जानकारी मत दीजिए। खुद अपने बैंक ऐप में जाकर जाँचिए।"},
    },
    "refund_upi": {
        "name": "UPI 'refund' / QR trick",
        "icon": "💸🔄",
        "cues": ["refund", "scan the qr", "scan this", "qr code", "accept the request",
                 "upi pin", "money was deducted", "wapas", "request bhej"],
        "why": "Receiving money never needs your PIN or scanning a QR. Scanning or entering a PIN SENDS money, it never receives it.",
        "action": {"en": "Do not scan any QR or enter your UPI PIN to 'receive' money. That only sends money away.",
                   "hi": "पैसे 'पाने' के लिए कोई QR स्कैन मत कीजिए, न UPI पिन डालिए। इससे पैसे जाते हैं, आते नहीं।"},
    },
    "sextortion": {
        "name": "Sextortion / blackmail",
        "icon": "📹⛔",
        "cues": ["recorded you", "video call", "recording", "send it to your contacts",
                 "viral", "intimate", "private video", "video record"],
        "why": "Blackmailers keep demanding more even after you pay. Paying never ends it.",
        "action": {"en": "Do not pay. Stop replying. Keep the evidence. Report to 1930. This is not your fault.",
                   "hi": "पैसे मत दीजिए। जवाब देना बंद कीजिए। सबूत रखिए। 1930 पर रिपोर्ट कीजिए। इसमें आपकी गलती नहीं है।"},
    },
    "loan_harassment": {
        "name": "Loan-app harassment",
        "icon": "📱😡",
        "cues": ["loan", "defaulter", "your contacts", "message everyone", "recovery",
                 "overdue", "chor", "fraud bata"],
        "why": "Threatening to shame you to your contacts is illegal recovery, whatever you owe.",
        "action": {"en": "Do not pay under threat. Threatening your contacts is a crime. Screenshot it and report to 1930.",
                   "hi": "धमकी में पैसे मत दीजिए। आपके संपर्कों को धमकाना अपराध है। स्क्रीनशॉट लेकर 1930 पर रिपोर्ट कीजिए।"},
    },
    "lottery_prize": {
        "name": "Lottery / prize / cashback",
        "icon": "🎁🚫",
        "cues": ["lottery", "lucky draw", "you have won", "prize", "kbc", "cashback",
                 "processing fee", "gst", "लॉटरी", "इनाम", "जीता"],
        "why": "No real prize ever needs you to pay a fee first. If you must pay to receive, it is a scam.",
        "action": {"en": "Never pay any fee to 'release' a prize. Real prizes cost nothing. Stop and delete the message.",
                   "hi": "इनाम 'छुड़ाने' के लिए कोई फीस कभी मत दीजिए। असली इनाम मुफ्त होता है। रुक जाइए।"},
    },
    "job_task": {
        "name": "Fake job / task earning",
        "icon": "💼🚫",
        "cues": ["job", "work from home", "task", "part-time", "registration fee",
                 "prepaid task", "like and earn", "recharge", "seat"],
        "why": "No real job asks you to pay a fee or 'recharge' to earn. The prepaid task never pays back.",
        "action": {"en": "Do not pay any fee or 'recharge' for a job or task. Stop before you invest anything.",
                   "hi": "नौकरी या टास्क के लिए कोई फीस या 'रिचार्ज' मत कीजिए। कुछ भी लगाने से पहले रुक जाइए।"},
    },
    "investment_crypto": {
        "name": "Fake investment / crypto",
        "icon": "📈🚫",
        "cues": ["invest", "crypto", "usdt", "double", "guaranteed", "returns",
                 "profit", "trading app", "stock tips", "multibagger", "wallet"],
        "why": "Guaranteed or 'double your money' returns are always fake.",
        "action": {"en": "Never send money to a stranger's wallet or app for 'guaranteed' returns. There are none.",
                   "hi": "'गारंटीड' रिटर्न के लिए किसी अजनबी के वॉलेट या ऐप में पैसे कभी मत भेजिए। ऐसा कुछ नहीं होता।"},
    },
    "tech_support": {
        "name": "Fake support / remote access",
        "icon": "🖥️🔓",
        "cues": ["anydesk", "screen share", "share your screen", "install this app",
                 "customer care", "remote", "team viewer", "quick support"],
        "why": "No real support ever needs AnyDesk or screen-sharing. It hands them your bank.",
        "action": {"en": "Do not install any app or share your screen. Uninstall it if you did. It gives them full access.",
                   "hi": "कोई ऐप इंस्टॉल मत कीजिए, न स्क्रीन शेयर कीजिए। अगर किया है तो हटा दीजिए। इससे उन्हें पूरा एक्सेस मिलता है।"},
    },
    "courier_customs": {
        "name": "Courier / customs parcel",
        "icon": "📦🚫",
        "cues": ["courier", "parcel", "customs", "fedex", "shipment", "clearance",
                 "seized", "held at customs", "पार्सल", "कस्टम"],
        "why": "Couriers and customs never call to transfer you to a police officer or ask for money.",
        "action": {"en": "Hang up. Verify only on the courier's official number. Never pay a 'clearance' fee by call.",
                   "hi": "फोन रखिए। सिर्फ कूरियर के आधिकारिक नंबर पर जाँचिए। कॉल पर 'क्लीयरेंस' फीस कभी मत दीजिए।"},
    },
    "utility_disconnection": {
        "name": "Electricity / utility cut-off",
        "icon": "⚡🚫",
        "cues": ["electricity", "bijli", "disconnect", "connection will be cut",
                 "gas", "power cut", "बिजली", "कनेक्शन"],
        "why": "Real utilities do not cut your power tonight over one call, and never ask you to pay an 'officer'.",
        "action": {"en": "Do not pay any 'officer' or scan a QR. Check your bill only in the official app or office.",
                   "hi": "किसी 'अधिकारी' को पैसे मत दीजिए, न QR स्कैन कीजिए। बिल सिर्फ आधिकारिक ऐप या दफ्तर में जाँचिए।"},
    },
    "impersonation_family": {
        "name": "Family / known-person impersonation",
        "icon": "👨‍👩‍👧❓",
        "cues": ["papa", "beta", "your son", "your relative", "accident", "urgent help",
                 "do not tell", "read me the message", "code word", "रिश्तेदार", "बेटा"],
        "why": "Voices can be cloned by AI. A real relative will pass your family code word.",
        "action": {"en": "Ask for your family code word. Call the person back on their own known number before doing anything.",
                   "hi": "अपना पारिवारिक कोड शब्द पूछिए। कुछ भी करने से पहले उस व्यक्ति को उनके अपने नंबर पर वापस कॉल कीजिए।"},
    },
    "generic_scam": {
        "name": "Suspicious call",
        "icon": "⚠️",
        "cues": [],
        "why": "This call shows manipulation signs even if the exact type is unclear.",
        "action": {"en": "Do not send money or share any code. Hang up and verify on an official number yourself.",
                   "hi": "पैसे मत भेजिए, कोई कोड मत बताइए। फोन रखकर खुद किसी आधिकारिक नंबर पर जाँचिए।"},
    },
}


def categorize(text: str) -> dict:
    """Return the best-matching scam category with tailored guidance."""
    t = _norm(text)
    scores = {k: 0.0 for k in CATEGORIES if k != "generic_scam"}
    for key, spec in CATEGORIES.items():
        if key == "generic_scam":
            continue
        scores[key] = sum(1 for c in spec["cues"] if c in t)

    # boost the semantic family's category (disambiguates overlapping cues)
    sim, _b, family = SEMANTIC.score(text)
    mapped = FAMILY_MAP.get(family)
    if mapped and sim >= 0.20:
        scores[mapped] = scores.get(mapped, 0) + 2.0 + sim

    best = max(scores, key=scores.get)
    if scores[best] <= 0:
        best = "generic_scam"
    spec = CATEGORIES[best]
    total = sum(scores.values()) or 1.0
    return {
        "category": best,
        "name": spec["name"],
        "icon": spec["icon"],
        "why": spec["why"],
        "action": spec["action"],
        "confidence": round(scores[best] / total, 2) if best != "generic_scam" else 0.0,
    }
