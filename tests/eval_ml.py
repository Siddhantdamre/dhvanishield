"""Train / validate / test protocol — the paper-grade evaluation.

Compares three systems on the HELD-OUT test split:
  rules-only  — the hand-built registry (L1+L3)
  ML-only     — the learned layer (L2)
  hybrid      — rules escalated by ML (deployed configuration)

Reported per system:
  scam recall at RED, FALSE REASSURANCE rate (scam -> green; the metric
  that must be ~0), benign green rate, benign wrongly-RED rate.

Also re-runs the original 32-case hand-written benchmark under the
hybrid to confirm no regression.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shield.datagen import make_dataset            # noqa: E402
from shield.ml import train_layer, hybrid_assess   # noqa: E402
from shield.engine import assess as rules_assess   # noqa: E402
from tests.data import SCAM, BENIGN, AMBIGUOUS     # noqa: E402


def score(system, test):
    res = {"scam_red": 0, "scam_green": 0, "ben_green": 0, "ben_red": 0,
           "n_scam": 0, "n_ben": 0}
    for text, y in test:
        lvl = system(text)
        if y == 1:
            res["n_scam"] += 1
            res["scam_red"] += lvl == "HIGH_RISK"
            res["scam_green"] += lvl == "NO_PATTERN"
        else:
            res["n_ben"] += 1
            res["ben_green"] += lvl == "NO_PATTERN"
            res["ben_red"] += lvl == "HIGH_RISK"
    return res


def pct(a, b):
    return f"{100*a/b:5.1f}%" if b else "  n/a"


def main() -> None:
    train, dev, test = make_dataset(n_per_class=300, seed=42)
    print(f"dataset: train {len(train)} / dev {len(dev)} / test {len(test)}")
    layer = train_layer(train, dev, calib_benign=BENIGN, calib_ambiguous=AMBIGUOUS)
    print(f"calibrated on dev: t_red={layer.t_red:.3f}  t_yellow={layer.t_yellow:.3f}")

    systems = {
        "rules-only": lambda t: rules_assess(t).level,
        "ML-only":    layer.level,
        "hybrid":     lambda t: hybrid_assess(t, layer)[0],
    }
    print(f"\n{'system':11} {'scam recall@RED':>16} {'FALSE REASSURE':>15} "
          f"{'benign green':>13} {'benign RED':>11}")
    results = {}
    for name, fn in systems.items():
        r = score(fn, test)
        results[name] = r
        print(f"{name:11} {pct(r['scam_red'], r['n_scam']):>16} "
              f"{pct(r['scam_green'], r['n_scam']):>15} "
              f"{pct(r['ben_green'], r['n_ben']):>13} "
              f"{pct(r['ben_red'], r['n_ben']):>11}")

    print("\n=== Regression check: original 32-case benchmark under hybrid ===")
    fr = sum(1 for t in SCAM if hybrid_assess(t, layer)[0] == "NO_PATTERN")
    caught = sum(1 for t in SCAM if hybrid_assess(t, layer)[0] == "HIGH_RISK")
    b_red = sum(1 for t in BENIGN if hybrid_assess(t, layer)[0] == "HIGH_RISK")
    b_green = sum(1 for t in BENIGN if hybrid_assess(t, layer)[0] == "NO_PATTERN")
    amb_red = sum(1 for t in AMBIGUOUS if hybrid_assess(t, layer)[0] == "HIGH_RISK")
    print(f"scam RED {caught}/12 | false reassurance {fr} | "
          f"benign green {b_green}/12 | benign RED {b_red} | ambiguous RED {amb_red}")

    h = results["hybrid"]
    r0 = results["rules-only"]
    ok = (h["scam_green"] == 0 and h["ben_red"] == 0
          and h["scam_red"] >= r0["scam_red"]
          and fr == 0 and caught == 12 and b_red == 0)
    print("\nRESULT:", "TRAIN/VALIDATE/TEST PASS" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
