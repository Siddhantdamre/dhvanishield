"""L2-semantic layer — intent-exemplar similarity (transparent, local).

Purpose: catch scams that use NONE of the registry's words — paraphrases
and, more importantly, scam FAMILIES the lexical registry was never built
for (sextortion, loan-app harassment, fake-job, UPI-collect 'refund',
deepfake family emergency, remote-access 'support', utility disconnection).

Design choices, all in service of trust:
  * Transparent, not a black box. Similarity is computed against a bank of
    named scam-family exemplars, so every escalation is explainable:
    "resembles the <family> script." No transformer, no download, no GPU —
    it stays fully local and CPU-fast, preserving the properties that make
    the rest of the system auditable. A sentence-transformer backend is a
    drop-in behind score(); the integration contract below is unchanged.
  * Escalate-only, capped at UNCERTAIN. This layer may turn a NO_PATTERN
    (a miss) into UNCERTAIN ("verify independently"). It may NEVER push a
    call to HIGH_RISK on its own and NEVER downgrade anything. Consequence:
    it can only *reduce* false reassurance; it can not create a false
    accusation, and it can not break the monotone safety gate.
  * A benign-context bank guards against over-escalation: if the text looks
    more like a legitimate money-mentioning call (EMI reminder, COD parcel,
    order OTP) than like a scam intent, we do not escalate.

The exemplars encode known scam typologies (I4C/MHA/RBI advisory patterns),
the same epistemic status as the lexical registry — they are NOT copied
from any evaluation transcript, so gains on the eval sets reflect
family-level generalisation, not test-set fitting.
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# --- scam-family intent exemplars (generic; en + hi-latin + some Devanagari) ---
SCAM_INTENTS: dict[str, list[str]] = {
    "digital_arrest": [
        "police cbi customs officer says a parcel or case is registered against you stay on the call and transfer money to a safe account to verify",
        "aap ke naam par case hai giraftaari hogi kisi ko mat batana verification ke liye paise transfer karo",
    ],
    "refund_collect": [
        "your payment failed but the money was deducted accept the refund request i send on your upi app to get the money back",
        "bijli ya bill ka payment fail ho gaya refund ke liye main request bhej raha hoon usse accept kar lo",
    ],
    "sextortion": [
        "i have recorded your private video from the call pay money now or i will send it to all your contacts",
        "aap ka video record kar liya hai paise do warna sab ko bhej dunga",
    ],
    "loan_harassment": [
        "you took a loan on our app pay immediately or we will message everyone in your contacts that you are a fraud and defaulter",
        "loan app se liya tha ab pay karo warna tumhare sab contacts ko bata denge ki tum fraud ho",
    ],
    "fake_job": [
        "you are selected for a work from home job pay a small refundable registration fee to confirm your seat today",
        "work from home job ke liye select hue ho bas registration fee bhar do seat pakki karne ke liye",
    ],
    "lottery_fee": [
        "you have won a lottery or lucky draw pay a processing fee or gst to release the prize amount to your account",
        "aap ko lottery lagi hai processing fee ya gst bhar do phir prize aapke account me aa jayega",
    ],
    "kyc_link": [
        "your bank account or wallet kyc is pending and will be blocked click the link and enter your card number cvv or otp to update",
        "aap ka kyc pending hai account block ho jayega link par card number cvv ya otp daal do",
    ],
    "deepfake_emergency": [
        "it is me your relative i had an accident and i am in trouble send money urgently to this number and do not tell anyone",
        "papa main hoon mera accident ho gaya jaldi paise bhej do kisi ko mat batana",
    ],
    "remote_support": [
        "i am from customer care your account has a problem install this app and share your screen so i can fix it",
        "customer care se hoon account me problem hai ye app install karo aur screen share karo",
    ],
    "disconnection": [
        "your electricity gas or service will be disconnected tonight unless you pay immediately contact this officer on this number",
        "aaj raat aapki bijli kat jayegi turant payment karo warna connection band ho jayega officer ko message karo",
    ],
}

# --- legitimate money-mentioning contexts (guard against over-escalation) ---
BENIGN_CONTEXTS: list[str] = [
    "your otp for the order is a number do not share it this is an automated message",
    "your loan emi is due tomorrow please pay on time this is a reminder from your registered bank",
    "your cash on delivery parcel is ready please pay the amount to the delivery agent",
    "we have received your payment thank you your report or order will be ready soon",
    "society maintenance payment is pending you can pay online or cash there is no hurry",
    "your background verification is complete we will email your offer letter congratulations",
    "confirming that you updated your registered mobile number today no action is needed",
    "we blocked a suspicious transaction we will never ask for your pin or otp call the number on your card",
    "passport verification officer needs to visit your address to verify details when are you home",
    "your appointment payment was received your reports will be ready tomorrow",
]

SCAM_T = 0.30      # min cosine to a scam exemplar to consider escalation
BENIGN_MARGIN = 0.05  # scam_sim must beat benign_sim by this to escalate


class SemanticLayer:
    def __init__(self):
        self._families, scam_docs = [], []
        for fam, docs in SCAM_INTENTS.items():
            for d in docs:
                self._families.append(fam)
                scam_docs.append(d)
        corpus = scam_docs + BENIGN_CONTEXTS
        self._vec = TfidfVectorizer(analyzer="word", ngram_range=(1, 2),
                                    min_df=1, sublinear_tf=True)
        self._vec.fit(corpus)
        self._scam_m = self._vec.transform(scam_docs)
        self._benign_m = self._vec.transform(BENIGN_CONTEXTS)
        self._n_scam = len(scam_docs)

    def score(self, text: str) -> tuple[float, float, str]:
        """Returns (scam_sim, benign_sim, best_scam_family)."""
        if not text or not text.strip():
            return 0.0, 0.0, ""
        q = self._vec.transform([text])
        scam_sims = cosine_similarity(q, self._scam_m)[0]
        benign_sims = cosine_similarity(q, self._benign_m)[0]
        best_i = int(scam_sims.argmax())
        return (float(scam_sims[best_i]), float(benign_sims.max()),
                self._families[best_i])

    def level(self, text: str) -> str:
        """Escalate-only suggestion: UNCERTAIN or NO_PATTERN. Never RED."""
        s, b, _fam = self.score(text)
        if s >= SCAM_T and (s - b) >= BENIGN_MARGIN:
            return "UNCERTAIN"
        return "NO_PATTERN"

    def explain(self, text: str) -> str:
        s, b, fam = self.score(text)
        if s >= SCAM_T and (s - b) >= BENIGN_MARGIN:
            return (f"Resembles the '{fam}' scam script "
                    f"(similarity {s:.2f} vs benign {b:.2f}).")
        return ""


# Module-level singleton — fits on the exemplar bank in milliseconds.
SEMANTIC = SemanticLayer()
