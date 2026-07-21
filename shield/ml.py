"""L2 learned layer — paraphrase robustness, trained/validated/tested.

Model: character n-gram TF-IDF + logistic regression. Chosen because it
is script-agnostic (works across Devanagari and Latin without language
detection), trains in seconds on CPU, is fully local (zero credits),
and is interpretable enough to audit.

Asymmetric calibration on the DEV split (never on test):
  t_red    = just above the highest benign dev probability
             -> on dev, no benign call can turn red
  t_yellow = just below the lowest scam dev probability
             -> on dev, no scam call can turn green
Test-set numbers then measure honest generalisation of both guarantees.

Hybrid rule (monotone): ML may only ESCALATE the rules verdict, never
downgrade it — preserving every rules-layer guarantee.
"""
from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from shield.engine import assess as rules_assess

_ORDER = {"NO_PATTERN": 0, "UNCERTAIN": 1, "HIGH_RISK": 2}
_NAME = {v: k for k, v in _ORDER.items()}


def _percentile(vals, p: float) -> float:
    """Linear-interpolated percentile, no numpy dependency."""
    if not vals:
        return 0.0
    s = sorted(vals)
    k = (len(s) - 1) * p / 100.0
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return s[f] + (s[c] - s[f]) * (k - f)


@dataclass
class MLLayer:
    vec: TfidfVectorizer
    clf: LogisticRegression
    t_red: float
    t_yellow: float

    def prob(self, text: str) -> float:
        return float(self.clf.predict_proba(self.vec.transform([text]))[0, 1])

    def level(self, text: str) -> str:
        p = self.prob(text)
        if p >= self.t_red:
            return "HIGH_RISK"
        if p >= self.t_yellow:
            return "UNCERTAIN"
        return "NO_PATTERN"


def train_layer(train, dev, margin: float = 0.02,
                calib_benign=(), calib_ambiguous=(),
                benign_percentile: float = 98.0) -> MLLayer:
    """calib_benign / calib_ambiguous: hand-written calibration pools
    (documented as calibration data, disjoint from the synthetic test).
    t_yellow separates benign from everything suspicious; t_red
    additionally clears the ambiguous pool so RED means scam-grade.

    t_yellow uses the benign_percentile (98th by default), NOT the max.
    Rationale (tests/eval_allrounder + calibration probe): with diverse
    REAL benign data a single high-scoring benign outlier drags a max-based
    threshold up to ~0.72 and silently destroys recall (OOD FRR 1 -> 7). A
    high percentile is robust to a few outliers — it keeps ~all benign
    below t_yellow while letting the threshold track the real distribution,
    which is what makes training on real data actually help."""
    Xtr = [t for t, _ in train]
    ytr = [y for _, y in train]
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4),
                          min_df=2, sublinear_tf=True)
    clf = LogisticRegression(max_iter=2000, C=2.0)
    clf.fit(vec.fit_transform(Xtr), ytr)

    layer = MLLayer(vec, clf, 1.0, 0.0)
    dev_scam = [layer.prob(t) for t, y in dev if y == 1]
    ben_pool = [layer.prob(t) for t, y in dev if y == 0]
    ben_pool += [layer.prob(t) for t in calib_benign]
    amb_pool = [layer.prob(t) for t in calib_ambiguous]
    layer.t_yellow = min(0.99, _percentile(ben_pool, benign_percentile) + margin)
    layer.t_red = min(0.99, max([layer.t_yellow] + [a + margin for a in amb_pool]))
    if dev_scam and layer.t_red >= min(dev_scam):
        print(f"[calibration warning] t_red {layer.t_red:.3f} >= min dev scam "
              f"{min(dev_scam):.3f}; recall on dev will drop")
    return layer


def hybrid_assess(text: str, layer: MLLayer, use_semantic: bool = True,
                  use_message: bool = False):
    """Rules verdict, escalated (never downgraded) by the learned layers.

    The L2-semantic layer (shield/semantic.py) may only raise a miss to
    UNCERTAIN — it is capped below HIGH_RISK — so it can reduce false
    reassurance without ever creating a false accusation or violating the
    monotone gate. use_semantic=False disables it for ablation."""
    rv = rules_assess(text)
    ml = layer.level(text)
    rank = max(_ORDER[rv.level], _ORDER[ml])
    if use_semantic:
        from shield.semantic import SEMANTIC
        rank = max(rank, _ORDER[SEMANTIC.level(text)])
    # Real-data-trained message expert — used ONLY for the forwarded-message
    # channel (use_message=True), never the phone committee. Measured: an
    # SMS-trained expert over-flags phone messages (different channel), so it
    # is kept out of the phone path by default. Capped at UNCERTAIN regardless.
    if use_message:
        from shield import message_model
        if message_model.EXPERT is not None:
            rank = max(rank, min(_ORDER["UNCERTAIN"],
                                 _ORDER[message_model.EXPERT.level(text)]))
    final = _NAME[rank]
    return final, rv.level, ml, layer.prob(text)
