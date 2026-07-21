"""Message expert — trained and validated on REAL data.

The phone-call path is grounded in real advisory patterns but cannot be
validated without real call data (a pilot). The FORWARDED-MESSAGE path is
different: real message data exists, so here we CAN train on real data and
report an honest held-out real-world number.

This module trains a char-ngram + logistic-regression expert on the real
SMS corpus (once, then cached to models/message_model.joblib) and exposes
it as another committee member. In the shared verdict it is capped at
UNCERTAIN — like the semantic layer, it may raise a miss to "verify" but
can never create a false accusation, preserving the never-false-accuse
invariant. Its STANDALONE real-world accuracy (tests/eval_message.py) is
the number you can defend as real-world-validated for the message channel.

Graceful: if neither the cached artifact nor the raw corpus is present
(e.g. CI), EXPERT is None and the committee runs without it.
"""
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "models" / "message_model.joblib"
SMS = ROOT / "tests" / "realworld" / "sms.tsv"


def _percentile(vals, p):
    if not vals:
        return 0.0
    s = sorted(vals)
    k = (len(s) - 1) * p / 100.0
    f = int(k); c = min(f + 1, len(s) - 1)
    return s[f] + (s[c] - s[f]) * (k - f)


class MessageExpert:
    def __init__(self, vec, clf, t_yellow, t_red):
        self.vec, self.clf = vec, clf
        self.t_yellow, self.t_red = t_yellow, t_red

    def prob(self, text: str) -> float:
        return float(self.clf.predict_proba(self.vec.transform([text]))[0, 1])

    def level(self, text: str) -> str:
        p = self.prob(text)
        if p >= self.t_red:
            return "HIGH_RISK"
        if p >= self.t_yellow:
            return "UNCERTAIN"
        return "NO_PATTERN"


def _train_from_real(seed: int = 42):
    import random
    rows = [(t, 1 if lab == "spam" else 0) for lab, t in
            (l.split("\t", 1) for l in SMS.read_text(encoding="utf-8", errors="replace")
             .splitlines() if "\t" in l) if lab in ("ham", "spam")]
    data = sorted(rows)
    random.Random(seed).shuffle(data)
    cut = int(0.8 * len(data))
    train = data[:cut]
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4),
                          min_df=2, sublinear_tf=True)
    clf = LogisticRegression(max_iter=2000, C=2.0)
    clf.fit(vec.fit_transform([t for t, _ in train]), [y for _, y in train])
    ham_p = [float(clf.predict_proba(vec.transform([t]))[0, 1])
             for t, y in train if y == 0]
    t_yellow = min(0.99, _percentile(ham_p, 98) + 0.02)
    t_red = min(0.99, _percentile(ham_p, 99.5) + 0.02)
    return MessageExpert(vec, clf, t_yellow, max(t_red, t_yellow))


def load():
    if ART.exists():
        try:
            return joblib.load(ART)
        except Exception:
            pass
    if SMS.exists():
        expert = _train_from_real()
        try:
            ART.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(expert, ART)
        except Exception:
            pass
        return expert
    return None


EXPERT = load()
