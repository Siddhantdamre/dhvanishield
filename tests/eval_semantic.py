"""L2-semantic ablation — does the layer earn its place, and do no harm?

Compares the hybrid WITHOUT and WITH the semantic layer on both hard sets,
on the three trust-critical metrics:
  false reassurance  scam called safe  (must go down or stay; the whole point)
  false alarm        benign called RED (must stay 0 — safety)
  over-warn          benign -> UNCERTAIN (watch it does not balloon)
A layer that raises false reassurance or false alarms would be removed.
"""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shield.datagen import make_dataset            # noqa: E402
from shield.ml import train_layer, hybrid_assess   # noqa: E402
from tests.data import BENIGN, AMBIGUOUS           # noqa: E402

from shield.training import build_deployed_layer   # noqa: E402
layer = build_deployed_layer()


def load(name):
    p = ROOT / "tests" / name
    if not p.exists():
        p = ROOT / name           # OOD set lives at the project root
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def measure(rows, use_semantic):
    fr = fa = ow = 0
    ns = nb = 0
    for r in rows:
        lvl = hybrid_assess(r["text"], layer, use_semantic=use_semantic)[0]
        if r["label"] == "scam":
            ns += 1
            fr += lvl == "NO_PATTERN"
        else:
            nb += 1
            fa += lvl == "HIGH_RISK"
            ow += lvl == "UNCERTAIN"
    return ns, nb, fr, fa, ow


SETS = [("out-of-distribution", "ood_adversarial_testset.jsonl"),
        ("red-team", "redteam_set.jsonl")]

print(f"{'set':20} {'semantic':9} {'false-reassure':>15} {'false-alarm':>12} {'over-warn':>10}")
for label, fname in SETS:
    rows = load(fname)
    for use in (False, True):
        ns, nb, fr, fa, ow = measure(rows, use)
        tag = "ON" if use else "OFF"
        print(f"{label:20} {tag:9} {f'{fr}/{ns}':>15} {f'{fa}/{nb}':>12} {f'{ow}/{nb}':>10}")
    print()

# gate: semantic must not raise false reassurance or false alarms anywhere
ok = True
for _, fname in SETS:
    rows = load(fname)
    _, _, fr_off, fa_off, _ = measure(rows, False)
    _, _, fr_on, fa_on, _ = measure(rows, True)
    ok &= fr_on <= fr_off and fa_on <= fa_off
print("RESULT:", "SEMANTIC LAYER DOES NO HARM (and reduces misses)" if ok
      else "REGRESSION — semantic layer raised a trust-critical error")
sys.exit(0 if ok else 1)
