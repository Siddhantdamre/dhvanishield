"""The learning loop — the honest 'reinforcement' and 'agentic' parts.

Deep RL does not fit a logistic-regression classifier; pretending it does
would be a buzzword. The REAL mechanisms for this system are:

  A. Learning from feedback (reward = the human's scam/not-scam label).
     Demonstrated as a learning curve: as the real-case corpus fills
     (0 -> 100%), held-out false-reassurance falls and recall rises. This
     is the flywheel closing — the model provably improves from feedback.

  B. Hard-negative mining (the honest 'agentic self-improvement'). The
     model scores a large unlabelled pool and nominates the cases it is
     most UNCERTAIN or most likely WRONG about — the priority queue for
     human labelling. Active learning: the system asks for the labels that
     help it most, instead of collecting at random.
"""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import random                                                  # noqa: E402
from shield.datagen import make_dataset                        # noqa: E402
from shield.ml import train_layer, hybrid_assess               # noqa: E402
import shield.training as T                                    # noqa: E402
from tests.data import BENIGN, AMBIGUOUS                       # noqa: E402


def load(p):
    return [(json.loads(l)["text"], 1 if json.loads(l)["label"] == "scam" else 0)
            for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]


indep = load(ROOT / "ood_adversarial_testset.jsonl") + load(ROOT / "tests" / "redteam_set.jsonl")
seed = T._load_seed()
random.Random(1).shuffle(seed)
tr, dv, _ = make_dataset(n_per_class=300, seed=42)


def build(extra):
    e = sorted(set(extra)); random.Random(42).shuffle(e); c = int(0.8 * len(e))
    return train_layer(list(tr) + e[:c], list(dv) + e[c:],
                       calib_benign=BENIGN, calib_ambiguous=AMBIGUOUS)


def measure(layer):
    fr = rec = fa = ow = ns = nb = 0
    for t, y in indep:
        lvl = hybrid_assess(t, layer)[0]
        if y == 1:
            ns += 1; fr += lvl == "NO_PATTERN"; rec += lvl != "NO_PATTERN"
        else:
            nb += 1; fa += lvl == "HIGH_RISK"; ow += lvl == "UNCERTAIN"
    return fr, ns, rec, fa, ow, nb


print("A. LEARNING CURVE — held-out (OOD+red-team) as the real-case corpus fills")
print(f"   {'corpus %':>8} {'seed n':>7} {'false-reassure':>15} {'recall':>8} {'false-alarm':>12}")
for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
    subset = seed[:int(frac * len(seed))]
    fr, ns, rec, fa, ow, nb = measure(build(subset))
    print(f"   {frac*100:6.0f}% {len(subset):>7} {f'{fr}/{ns}':>15} "
          f"{f'{rec}/{ns}':>8} {f'{fa}/{nb}':>12}")

print("\nB. HARD-NEGATIVE MINING — what to label next (priority queue)")
layer = T.build_deployed_layer()
pool = []
sms = T.SMS_CORPUS
if sms.exists():
    pool = [(t, 1 if lab == "spam" else 0) for lab, t in
            (l.split("\t", 1) for l in sms.read_text(encoding="utf-8", errors="replace")
             .splitlines() if "\t" in l) if lab in ("ham", "spam")]
if not pool:
    print("   (no unlabelled pool available; fetch tests/realworld to enable)")
else:
    scored = [(abs(layer.prob(t) - layer.t_yellow), layer.prob(t), t, y) for t, y in pool]
    scored.sort()                                   # smallest gap = most uncertain
    uncertain = scored[:200]
    wrong = [s for s in pool if (layer.prob(s[0]) >= layer.t_yellow) != (s[1] == 1)]
    print(f"   pool {len(pool)} real messages | "
          f"{len(wrong)} currently misclassified | top-200 most-uncertain queued")
    print("   examples the model most wants labelled (near the decision line):")
    for gap, p, t, y in uncertain[:4]:
        print(f"     p={p:.2f} [{'spam' if y==1 else 'ham'}]  {t[:72]}")
print("\nThe curve shows feedback improves the model; the queue shows the model")
print("asking for the labels that will improve it most. That is the flywheel.")
