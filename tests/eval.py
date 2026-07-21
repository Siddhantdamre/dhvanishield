"""DhvaniShield eval — Holup-style, asymmetric by design.

Hard requirements:
  * FALSE REASSURANCE = 0: no scam transcript may receive NO_PATTERN.
  * No benign transcript may receive HIGH_RISK (benign may at worst abstain).
Reported metrics: scam catch rate, benign pass rate, abstention rate on
ambiguous cases, plus per-case failures for debugging.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core import assess          # noqa: E402
from tests.data import SCAM, BENIGN, AMBIGUOUS   # noqa: E402


def main() -> None:
    fr, caught = 0, 0
    for t in SCAM:
        v = assess(t)
        if v.level == "NO_PATTERN":
            fr += 1
            print(f"[FALSE REASSURANCE] {t[:70]}...")
        if v.level == "HIGH_RISK":
            caught += 1
        elif v.level == "UNCERTAIN":
            print(f"[scam only UNCERTAIN, score {v.score}] {t[:70]}...")

    b_pass, b_high = 0, 0
    for t in BENIGN:
        v = assess(t)
        if v.level == "NO_PATTERN":
            b_pass += 1
        elif v.level == "HIGH_RISK":
            b_high += 1
            print(f"[FALSE ALARM HIGH] {v.categories_hit} :: {t[:70]}...")
        else:
            print(f"[benign UNCERTAIN] {v.categories_hit} :: {t[:70]}...")

    a_abst = 0
    for t in AMBIGUOUS:
        v = assess(t)
        if v.level == "UNCERTAIN":
            a_abst += 1
        else:
            print(f"[ambiguous -> {v.level}, score {v.score}] {t[:70]}...")

    print("\n=== DhvaniShield eval ===")
    print(f"Scam caught as HIGH_RISK:        {caught}/{len(SCAM)}")
    print(f"FALSE REASSURANCE (must be 0):   {fr}")
    print(f"Benign passed as NO_PATTERN:     {b_pass}/{len(BENIGN)}")
    print(f"Benign wrongly HIGH_RISK (must be 0): {b_high}")
    print(f"Ambiguous abstained (UNCERTAIN): {a_abst}/{len(AMBIGUOUS)}")

    ok = (fr == 0 and caught == len(SCAM) and b_high == 0
          and b_pass == len(BENIGN) and a_abst == len(AMBIGUOUS))
    ok = order_sensitivity() and ok
    ok = ablation_table() and ok
    ok = earliness_report() and ok
    print("\nRESULT:", "ALL CHECKS PASS" if ok else "CHECKS FAILED")
    sys.exit(0 if ok else 1)




# ---------------- Research extensions ----------------
import random
from shield.engine import assess as assess_e, _norm
from shield import trajectory as traj_mod


def order_sensitivity() -> bool:
    """H2 test: identical sentences, scrambled order -> same progression,
    lower concordance; verdict must NOT downgrade (monotonicity)."""
    ordered = SCAM[4]
    sents = [s.strip() for s in ordered.replace("\n", " ").split(".") if s.strip()]
    rng = random.Random(7)
    scrambled = ". ".join(rng.sample(sents, len(sents))) + "."
    t_o = traj_mod.analyse(ordered, _norm)
    t_s = traj_mod.analyse(scrambled, _norm)
    v_s = assess_e(scrambled)
    print("\n=== Order sensitivity (structure vs vocabulary) ===")
    print(f"Ordered:   progression {t_o.progression:.2f}, concordance {t_o.concordance:.2f}, traj {t_o.score:.2f}")
    print(f"Scrambled: progression {t_s.progression:.2f}, concordance {t_s.concordance:.2f}, traj {t_s.score:.2f}")
    ok = (t_s.progression == t_o.progression
          and t_s.concordance < t_o.concordance
          and v_s.level == "HIGH_RISK")
    print("Structure detected beyond vocabulary:", "YES" if ok else "NO")
    return ok


def ablation_table() -> bool:
    """Each claimed component must earn its place measurably."""
    configs = {
        "full system": dict(use_trajectory=True, languages=None),
        "no trajectory (L3 off)": dict(use_trajectory=False, languages=None),
        "English-only registry": dict(use_trajectory=True, languages={"ascii"}),
    }
    print("\n=== Ablation table ===")
    print(f"{'config':26} {'scam HIGH':>9} {'FALSE REASSURE':>15} {'benign pass':>12} {'abstain':>8}")
    fr_full = fr_ascii = None
    for name, kw in configs.items():
        caught = sum(1 for t in SCAM if assess_e(t, **kw).level == "HIGH_RISK")
        fr = sum(1 for t in SCAM if assess_e(t, **kw).level == "NO_PATTERN")
        bp = sum(1 for t in BENIGN if assess_e(t, **kw).level == "NO_PATTERN")
        ab = sum(1 for t in AMBIGUOUS if assess_e(t, **kw).level == "UNCERTAIN")
        print(f"{name:26} {caught:>6}/12 {fr:>15} {bp:>9}/12 {ab:>5}/8")
        if name == "full system":
            fr_full = fr
        if name.startswith("English-only"):
            fr_ascii = fr
    ok = fr_full == 0 and fr_ascii > 0
    print("Multilingual registry prevents false reassurance on Hindi/Marathi scams:",
          "DEMONSTRATED" if ok else "NOT DEMONSTRATED")
    return ok




def earliness_report() -> bool:
    """Headline metric: the alarm should fire BEFORE the money stage."""
    from shield.stream import earliness
    fracs, before = [], 0
    print("\n=== Detection earliness (streaming) ===")
    for i, t in enumerate(SCAM):
        e = earliness(t)
        if e["fired_at"] is None:
            print(f"scam {i+1:02d}: NEVER FIRED")
            continue
        fracs.append(e["fired_fraction"])
        before += e["before_money"]
        tag = "before money" if e["before_money"] else "AFTER money"
        print(f"scam {i+1:02d}: red at utterance {e['fired_at']+1}/{e['utterances']}"
              f" ({e['fired_fraction']:.0%} of call) — {tag}")
    avg = sum(fracs)/len(fracs)
    print(f"Average: alarm at {avg:.0%} of the call | "
          f"fired at-or-before money stage: {before}/{len(SCAM)}")
    return len(fracs) == len(SCAM) and before == len(SCAM)


if __name__ == "__main__":
    main()
