"""Accessibility layer — DhvaniShield for ALL of its actual users.

Design facts this module exists for:
  * Blind users cannot read a warning banner  -> spoken verdicts (TTS-ready
    scripts: short sentences, no jargon, key action said twice).
  * Deaf and low-literacy users cannot parse paragraphs -> pictogram action
    cards (emoji strip + <=8-word lines, grade-2 reading level).
  * Voice-cloning scams defeat voice recognition -> the FAMILY CODE WORD:
    a zero-technology countermeasure every household can set in one minute.

Every verdict is available in three renderings: standard, spoken, picto.
Languages: en / hi / mr (extensible — pure data, no logic change).
"""

SPEECH = {
    "HIGH_RISK": {
        "en": ("This call is dangerous. It is a scam. Put the phone down now. "
               "Put the phone down now. Then call one nine three zero. "
               "Tell your family today."),
        "hi": ("यह कॉल खतरनाक है। यह धोखा है। फोन अभी रख दीजिए। "
               "फोन अभी रख दीजिए। फिर एक नौ तीन शून्य पर कॉल कीजिए। "
               "आज ही परिवार को बताइए।"),
        "mr": ("हा कॉल धोकादायक आहे. हा घोटाळा आहे. फोन आत्ताच ठेवा. "
               "फोन आत्ताच ठेवा. मग एक नऊ तीन शून्य वर कॉल करा. "
               "आजच कुटुंबाला सांगा."),
    },
    "UNCERTAIN": {
        "en": ("Be careful with this call. Do not send money. Do not share "
               "any code. Put the phone down. Check with the real office "
               "yourself. Ask your family first."),
        "hi": ("इस कॉल से सावधान रहिए। पैसे मत भेजिए। कोई कोड मत बताइए। "
               "फोन रख दीजिए। खुद असली दफ्तर से पूछिए। पहले परिवार से पूछिए।"),
        "mr": ("या कॉलपासून सावध रहा. पैसे पाठवू नका. कोणताही कोड सांगू नका. "
               "फोन ठेवा. स्वतः खऱ्या कार्यालयात विचारा. आधी कुटुंबाला विचारा."),
    },
    "NO_PATTERN": {
        "en": ("This looks like a normal call. Nothing bad was found. "
               "Still, never send money on a phone call. "
               "Never share a code on a phone call."),
        "hi": ("यह सामान्य कॉल लगती है। कुछ गलत नहीं मिला। "
               "फिर भी, फोन पर कभी पैसे मत भेजिए। फोन पर कभी कोड मत बताइए।"),
        "mr": ("हा सामान्य कॉल वाटतो. काही चुकीचे आढळले नाही. "
               "तरीही, फोनवर कधीही पैसे पाठवू नका. फोनवर कधीही कोड सांगू नका."),
    },
}

# Pictogram action cards — readable with zero literacy, shareable as-is
# on WhatsApp. One action per line, action first.
PICTO = {
    "HIGH_RISK": ("🔴🔴🔴\n"
                  "📵  ✋  (hang up / फोन रखें / फोन ठेवा)\n"
                  "📞  1️⃣9️⃣3️⃣0️⃣\n"
                  "👨‍👩‍👧  🗣️  (tell family / परिवार को बताएं / कुटुंबाला सांगा)"),
    "UNCERTAIN": ("🟡🟡🟡\n"
                  "✋  🚫💸  (no money / पैसे नहीं / पैसे नाही)\n"
                  "🚫🔢  (no OTP / कोड नहीं / कोड नाही)\n"
                  "☎️  🏢  (call real office / असली दफ्तर / खरे कार्यालय)"),
    "NO_PATTERN": ("🟢🟢🟢\n"
                   "🙂  👍\n"
                   "💡 🚫💸 🚫🔢  (never money or OTP on a call)"),
}

CODEWORD_TIP = {
    "en": ("Family Code Word: pick one secret word with your family today "
           "— like 'mango tree'. If a caller claims to be family or police "
           "about family, ask for the word. No word, no trust. This defeats "
           "even AI-cloned voices, and it costs nothing."),
    "hi": ("पारिवारिक कोड शब्द: आज ही परिवार के साथ एक गुप्त शब्द चुनिए — "
           "जैसे 'आम का पेड़'। कोई परिवार या पुलिस बनकर कॉल करे तो वह शब्द "
           "पूछिए। शब्द नहीं, तो भरोसा नहीं। यह नकली AI आवाज़ को भी हरा देता है।"),
    "mr": ("कौटुंबिक कोड शब्द: आजच कुटुंबासोबत एक गुप्त शब्द ठरवा — "
           "जसे 'आंब्याचे झाड'. कोणी कुटुंब किंवा पोलीस म्हणून कॉल केला तर "
           "तो शब्द विचारा. शब्द नाही, तर विश्वास नाही."),
}


def verdict_speech(level: str, lang: str = "en") -> str:
    """TTS-ready spoken verdict: short sentences, no jargon, action twice."""
    return SPEECH[level].get(lang, SPEECH[level]["en"])


def verdict_picto(level: str) -> str:
    """Emoji action card for deaf and low-literacy users."""
    return PICTO[level]


def codeword_tip(lang: str = "en") -> str:
    return CODEWORD_TIP.get(lang, CODEWORD_TIP["en"])


def accessible_bundle(level: str, lang: str = "en") -> dict:
    """Everything a channel (WhatsApp/IVR) needs to serve every user."""
    return {
        "speech": verdict_speech(level, lang),
        "picto": verdict_picto(level),
        "codeword_tip": codeword_tip(lang),
    }
