"""Synthetic dataset generator — train/dev/test for the learned layer.

Template slot-filling over the digital-arrest grammar. Crucially, many
slot fillers are PARAPHRASES that avoid registry markers on purpose
("central investigation agency", "keep this strictly between us",
"monitored government ledger") — so the held-out test set measures
whether a learned layer generalises beyond the hand-written rules.

Honest scope note (also in RESEARCH.md): train and test share the same
generator family, so this measures paraphrase-robustness, not full
out-of-distribution robustness. True OOD evaluation = the hand-written
adversarial set (human task).
"""
import random

AUTHORITY = [
    "I am calling from CBI Mumbai", "This is the Enforcement Directorate",
    "I am an officer of the central investigation agency",
    "This is the federal crime unit speaking",
    "You are speaking with the national telecom authority",
    "I am from the special anti smuggling division",
    "This is the financial offences wing",
    "मैं केंद्रीय जांच एजेंसी से बोल रहा हूँ",
    "मैं अपराध शाखा से अधिकारी बोल रहा हूँ",
]
ACCUSATION = [
    "a parcel in your name contains drugs",
    "a shipment registered against your identity has contraband",
    "your identity documents were used in a laundering racket",
    "your bank account shows movements tied to a criminal syndicate",
    "a courier booked on your identity carried restricted substances",
    "आपके नाम से बुक पार्सल में प्रतिबंधित सामान मिला है",
    "आपके दस्तावेज़ एक बड़े घोटाले में इस्तेमाल हुए हैं",
]
ISOLATION = [
    "do not tell anyone about this matter",
    "keep this strictly between us",
    "you must not discuss this with your family or any advocate",
    "this investigation is sealed, speak of it to no one",
    "remain on this video line until cleared",
    "यह मामला किसी से साझा नहीं करना है",
    "जांच पूरी होने तक कॉल पर बने रहिए",
]
THREAT = [
    "officers will reach your address today",
    "a non bailable case will be opened this evening",
    "your accounts and identity will be frozen within hours",
    "the arrest team is on standby",
    "आज ही कार्रवाई होगी",
    "कुछ ही घंटों में आपके खाते बंद हो जाएंगे",
]
MONEY = [
    "transfer the amount to a safe account for verification",
    "move your funds to a monitored government ledger until cleared",
    "pay the verification levy through the officer's channel",
    "shift your savings to the custody account we provide",
    "share the code you receive so we can secure your account",
    "अपनी राशि जांच खाते में भेज दीजिए",
    "जो कोड आया है वह अधिकारी को बताइए",
]

BENIGN_TEMPLATES = [
    "Hello, your {thing} delivery is scheduled for {day} between {t1} and {t2}. Please keep your phone reachable",
    "Good morning, this is the {org} confirming your appointment on {day} at {t1}. Please carry your documents",
    "Hi, this is the society office. The {utility} will be off on {day} for maintenance between {t1} and {t2}",
    "Namaste, your {policy} renewal is due this month. You can renew on the official portal at your convenience",
    "This is your bank. Your fixed deposit matures on {day}. You may visit the branch anytime to renew it",
    "Hello sir, your interview with our team is confirmed for {day} at {t1} at the office address shared by email",
    "Beta, {day} ko shaam ko ghar jaldi aa jana, mehmaan aa rahe hain",
    "बेटा, {day} को शाम को मंदिर चलना है, समय से घर आ जाना",
    "नमस्ते, आपकी {thing} की डिलीवरी {day} को {t1} से {t2} के बीच होगी",
    "आपके बिजली बिल का भुगतान {day} तक करना है, आधिकारिक वेबसाइट पर कर सकते हैं",
    "अस्पताल से बोल रहे हैं, आपकी जांच {day} को {t1} बजे है, पुरानी रिपोर्ट साथ लाइए",
    "उद्या {day} ला सोसायटीची मीटिंग आहे, वेळेवर या",
    "This is the school office. The parent teacher meeting is on {day} morning. Kindly confirm attendance",
    "Hello, the {thing} you ordered is ready. Which day of the week suits you for delivery",
    "Your monthly mobile plan was renewed successfully and is valid till the {t2}. Thank you",
]
FILL = {
    "thing": ["furniture", "grocery", "medicine", "book parcel", "washing machine"],
    "org": ["hospital front desk", "dental clinic", "passport office", "bank branch"],
    "utility": ["water supply", "electricity", "lift service"],
    "policy": ["car insurance", "health insurance", "two wheeler insurance"],
    "day": ["Monday", "Tuesday", "Friday", "Saturday", "tomorrow", "the 15th"],
    "t1": ["10 am", "11 am", "3 pm", "4 pm"],
    "t2": ["12 pm", "1 pm", "6 pm", "the 28th"],
}


def _fill(t, rng):
    for k, opts in FILL.items():
        while "{" + k + "}" in t:
            t = t.replace("{" + k + "}", rng.choice(opts), 1)
    return t


def make_dataset(n_per_class: int = 300, seed: int = 42):
    rng = random.Random(seed)
    scams, benigns = set(), set()
    while len(scams) < n_per_class:
        parts = [rng.choice(AUTHORITY), rng.choice(ACCUSATION)]
        if rng.random() < 0.85:
            parts.append(rng.choice(ISOLATION))
        if rng.random() < 0.7:
            parts.append(rng.choice(THREAT))
        parts.append(rng.choice(MONEY))
        if rng.random() < 0.2:  # occasional stage scrambling
            rng.shuffle(parts)
        scams.add(". ".join(parts) + ".")
    while len(benigns) < n_per_class:
        benigns.add(_fill(rng.choice(BENIGN_TEMPLATES), rng) + ".")

    # sorted() before the seeded shuffle makes the split reproducible
    # regardless of PYTHONHASHSEED — set iteration order is otherwise
    # randomised per process, which made trained-model verdicts flicker
    # run-to-run on borderline cases.
    data = [(s, 1) for s in sorted(scams)] + [(b, 0) for b in sorted(benigns)]
    rng.shuffle(data)
    n = len(data)
    train = data[: int(0.6 * n)]
    dev = data[int(0.6 * n): int(0.8 * n)]
    test = data[int(0.8 * n):]
    return train, dev, test
