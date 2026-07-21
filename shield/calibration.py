"""Calibration & selective prediction — 'know when you are wrong, defer.'

Reusable research primitives for the capability that matters most for a
safety-critical classifier: instead of always answering, the model reports
calibrated confidence and ABSTAINS (defers to a human) when it cannot meet a
target error rate. This is the selective-prediction / learning-to-defer
frame — directly the 'AI that knows when it is uncertain' problem.

  ece()                 — Expected Calibration Error (are the probabilities honest?)
  platt_fit / _apply    — post-hoc calibration (Platt scaling)
  risk_coverage()       — error rate vs fraction answered (the selective-prediction curve)
  selective_threshold() — the confidence cut that GUARANTEES <= target error on
                          the answered set, and the coverage it achieves.
No new dependencies.
"""
from sklearn.linear_model import LogisticRegression


def ece(probs, labels, bins: int = 10) -> float:
    """Expected Calibration Error: weighted gap between predicted probability
    of the positive class and the empirical positive rate, over `bins`."""
    total = len(labels)
    if total == 0:
        return 0.0
    e = 0.0
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        idx = [i for i, p in enumerate(probs) if (lo < p <= hi) or (b == 0 and p == 0)]
        if not idx:
            continue
        conf = sum(probs[i] for i in idx) / len(idx)
        acc = sum(labels[i] for i in idx) / len(idx)
        e += (len(idx) / total) * abs(conf - acc)
    return e


def platt_fit(scores, labels):
    """Fit a 1-D logistic calibrator (Platt scaling) on held-out scores."""
    clf = LogisticRegression()
    clf.fit([[s] for s in scores], labels)
    return clf


def platt_apply(clf, scores):
    return [float(p) for p in clf.predict_proba([[s] for s in scores])[:, 1]]


def risk_coverage(confidences, correct):
    """(coverage, risk) as the model answers only its most-confident cases.
    A useful selective classifier's risk falls monotonically as coverage drops."""
    order = sorted(range(len(confidences)), key=lambda i: confidences[i], reverse=True)
    out, wrong = [], 0
    for k, i in enumerate(order, start=1):
        wrong += (0 if correct[i] else 1)
        out.append((k / len(order), wrong / k))
    return out


def selective_threshold(confidences, correct, target_risk: float):
    """Largest coverage (and the confidence threshold achieving it) whose error
    rate on the answered set is <= target_risk. The rest is deferred to a human."""
    order = sorted(range(len(confidences)), key=lambda i: confidences[i], reverse=True)
    best_cov, thr, wrong = 0.0, 1.0, 0
    for k, i in enumerate(order, start=1):
        wrong += (0 if correct[i] else 1)
        if wrong / k <= target_risk:
            best_cov, thr = k / len(order), confidences[i]
    return thr, best_cov
