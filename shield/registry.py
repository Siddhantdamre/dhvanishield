"""Digital-arrest playbook registry.

Categories double as STAGES of the canonical coercion sequence.
Sources: publicly documented patterns (I4C/MHA advisories, RBI cautions,
PIB fact-checks, reported cases). Languages: en, hi, mr (extensible).
"""

REGISTRY: dict[str, dict] = {
    "authority_impersonation": {
        "weight": 2,
        "why": "Impersonating CBI/ED/police/customs/TRAI/courts. Real agencies never conduct enforcement over phone or video calls.",
        "markers": [
            "cbi", "enforcement directorate", " ed ", "police station",
            "customs", "narcotics", "trai", "crime branch", "cyber cell",
            "cyber crime", "mumbai police", "delhi police", "income tax department",
            "interpol", "supreme court", "high court", "ips officer", "inspector calling",
            "arrest warrant", "warrant issued", "fir registered", "fir against you",
            "fir number", "case number", "court summons", "legal notice issued",
            "सीबीआई", "पुलिस", "गिरफ्तारी", "वारंट", "अपराध शाखा",
            "प्रवर्तन निदेशालय", "आयकर विभाग", "न्यायालय", "एफआईआर",
            "पोलीस", "गुन्हा", "अटक वॉरंट",
            # South/East Indian languages (police / CBI / arrest)
            "சிபிஐ", "போலீஸ்", "காவல்துறை", "கைது",           # Tamil
            "సిబిఐ", "పోలీసు", "అరెస్టు",                      # Telugu
            "সিবিআই", "পুলিশ", "গ্রেপ্তার",                    # Bengali
            "ಸಿಬಿಐ", "ಪೊಲೀಸ್",                                # Kannada
            "સીબીઆઈ", "પોલીસ",                                # Gujarati
        ],
    },
    "false_accusation": {
        "weight": 2,
        "why": "A fabricated crime tied to your identity: parcel with drugs, Aadhaar 'linked' to laundering, SIM used in crime.",
        "markers": [
            "parcel in your name", "parcel contains", "courier contains",
            "found in the parcel", "drugs found", "drugs", "mdma",
            "money laundering", "aadhaar linked", "aadhaar card linked",
            "aadhaar misused", "identity misused", "your sim was used",
            "illegal items", "illegal shipment", "human trafficking",
            "human organs", "fake passports", "suspicious transactions in your account",
            "account involved in", "linked to a criminal",
            "मनी लॉन्ड्रिंग", "आधार", "पार्सल", "ड्रग्स", "अवैध", "तस्करी",
            "तुमच्या नावावर",
        ],
    },
    "isolation": {
        "weight": 3,
        "why": "The core coercion move: keep the victim silent, alone, and watched. No genuine authority demands secrecy or continuous video.",
        "markers": [
            "do not tell anyone", "don't tell anyone", "tell no one",
            "do not disclose", "do not inform family", "do not contact a lawyer",
            "do not go to the police station", "confidential", "national secret",
            "secrecy bond", "non-disclosure", "stay on the call",
            "remain on video", "keep camera on", "camera must stay on",
            "video call for verification", "report every hour",
            "cannot leave the room", "under surveillance", "digital arrest",
            "digital custody", "house arrest",
            "किसी को मत बताना", "गोपनीय", "निगरानी", "डिजिटल अरेस्ट",
            "वीडियो कॉल पर रहें", "कैमरा चालू", "कोणालाही सांगू नका",
            # "do not tell anyone" — the strongest, most scam-specific signal,
            # and the one that must never be missed in ANY language.
            "சொல்லாதீர்கள்", "யாரிடமும் சொல்ல",              # Tamil
            "చెప్పకండి", "ఎవరికీ చెప్ప",                       # Telugu
            "বলবেন না", "কাউকে বল",                           # Bengali
            "ಯಾರಿಗೂ ಹೇಳ",                                    # Kannada
            "કોઈને કહેશો નહીં",                               # Gujarati
        ],
    },
    "urgency_threat": {
        "weight": 2,
        "why": "Manufactured time pressure so the victim cannot think or consult anyone.",
        "markers": [
            "immediately", "within 30 minutes", "within one hour", "within 24 hours",
            "right now", "last warning", "final notice", "arrest team dispatched",
            "will be arrested today", "non-bailable", "account will be frozen",
            "account will be blocked", "aadhaar will be blocked", "cancel your aadhaar",
            "sim will be deactivated", "immediate action",
            "तुरंत", "अभी", "आज ही गिरफ्तार", "आखिरी चेतावनी", "खाता फ्रीज",
        ],
    },
    "money_movement": {
        "weight": 3,
        "why": "The goal of the script: move money 'for verification'. No agency verifies funds by transfer. Ever.",
        "markers": [
            "safe account", "rbi account", "supreme court account",
            "government verification account", "verification of funds",
            "transfer the amount", "refundable deposit", "security deposit",
            "refund after verification", "audit of funds", "clear your name",
            "break your fd", "fixed deposit break", "liquidate your",
            "mutual fund redemption", "rtgs", "neft",
            "सुरक्षित खाते", "पैसे ट्रांसफर", "जांच के लिए",
        ],
    },
    "remote_access_credentials": {
        "weight": 3,
        "why": "Requests for OTP, PINs, passwords or screen access. No bank, agency or company legitimately asks for these on a call.",
        "markers": [
            "anydesk", "teamviewer", "share your screen", "screen share",
            "screen sharing", "upi pin", "cvv", "net banking password",
            "atm pin", "install this app",
            # OTP/code ELICITATION (scam asks you to give/read the code) — NOT
            # bare "otp", which fires on legit delivery ("your OTP is X, do not
            # share it") and even on reassurance ("we will never ask for OTP").
            "share the otp", "share your otp", "tell me the otp", "give me the otp",
            "provide the otp", "read me the otp", "read the otp", "read out the otp",
            "otp batao", "otp bata", "share the code", "tell me the code",
            "read me the code", "read the code", "read me the message",
            "read the message that", "padh ke suna", "code batao",
            "ओटीपी बताइए", "ओटीपी बताओ", "स्क्रीन शेयर", "पिन बताइए",
        ],
    },
}


# Canonical order of the digital-arrest script — the "grammar" of the scam.
CANONICAL_STAGES = [
    "authority_impersonation",
    "false_accusation",
    "isolation",
    "urgency_threat",
    "money_movement",
    "remote_access_credentials",
]
