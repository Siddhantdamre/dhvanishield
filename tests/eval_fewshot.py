"""Few-shot concept extension — an honest step toward adaptive learning.

Claim (modest, precise): the manipulation engine can acquire a NEW strategy
from ~3 examples and immediately detect it in UNSEEN instances of that
strategy. This is online concept extension, not fluid reasoning — stated so.

Demo: 'flattery / ego-appeal' ("someone as brilliant as you...") is a
manipulation lever the engine does not model. We teach it 3 examples and
test on 2 different, held-out flattery messages it never saw.
"""
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shield.manipulation import analyze, learn_strategy   # noqa: E402

# Held-out flattery-manipulation the engine will be TESTED on (never taught).
HELD_OUT = [
    "Someone as brilliant as you would never miss this once-in-a-lifetime chance, you are far too clever.",
    "An investor of your rare calibre obviously deserves this more than the ordinary crowd, only you truly get it.",
]


def flattery_activation(text):
    return analyze(text)["vector"].get("flattery", 0.0)


def main() -> None:
    before = [flattery_activation(t) for t in HELD_OUT]        # strategy absent -> 0.0
    print(f"before learning: 'flattery' activation on held-out = "
          f"{[round(b, 2) for b in before]} (not modelled)")

    # teach the new strategy from 3 examples (distinct from the held-out set)
    learn_strategy("flattery", [
        "a person as intelligent as you can surely see the truth",
        "you are far too smart to be fooled, you deserve only the best",
        "only someone as wise and special as you would truly appreciate this",
    ], weight=1.2)

    after = [flattery_activation(t) for t in HELD_OUT]
    print(f"after 3 examples: 'flattery' activation on held-out = "
          f"{[round(a, 2) for a in after]}")

    ex = analyze(HELD_OUT[0])
    print(f"\nthe engine now reads it as: dominant = {ex['dominant']}")

    # it worked if the newly-taught strategy fires on BOTH unseen instances
    ok = all(a >= 0.12 for a in after) and all(b == 0.0 for b in before)
    print("\nRESULT:", "FEW-SHOT CONCEPT EXTENSION WORKS (generalises from 3 examples)"
          if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
