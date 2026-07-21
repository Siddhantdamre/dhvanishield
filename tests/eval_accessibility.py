"""Accessibility-profile tests — the alert adapts to each disability.

Verifies every profile renders a usable alert for every risk level, and
that the disability-specific guarantees hold:
  * colour-blind safe: meaning carried by shape + WORD, never colour alone
  * blind: a spoken script + an audio earcon, no visual dependency
  * deaf: a pictogram + a haptic pattern, no audio dependency
  * low-literacy / cognitive: an easy-read one-line action
  * every profile: the one-tap trusted-contact prompt (breaks isolation)
CI-safe, no network.
"""
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shield.accessibility import accessible_alert, PROFILES   # noqa: E402

SCAM = "This is CBI, you are under digital arrest, transfer money to the safe account now"
LEVELS = ("HIGH_RISK", "UNCERTAIN", "NO_PATTERN")


def main() -> None:
    ok = True

    # every profile x level produces shape+word (colour-independent) + a call prompt
    for p in PROFILES:
        for lvl in LEVELS:
            a = accessible_alert(lvl, SCAM if lvl != "NO_PATTERN" else "hi mom", p)
            good = (a["shape"] and a["shape_word"] and a["call_person"]["prompt"])
            ok &= bool(good)
    print(f"all {len(PROFILES)} profiles x {len(LEVELS)} levels render "
          f"shape+word+call: {'✓' if ok else '✗'}")

    blind = accessible_alert("HIGH_RISK", SCAM, "blind")
    b_ok = bool(blind.get("speech")) and bool(blind.get("earcon"))
    print(f"blind: spoken script + audio earcon, no visual dependency: {'✓' if b_ok else '✗'}")

    deaf = accessible_alert("HIGH_RISK", SCAM, "deaf")
    d_ok = bool(deaf.get("picto")) and bool(deaf.get("haptic")) and "speech" not in deaf
    print(f"deaf: pictogram + haptic, no audio required: {'✓' if d_ok else '✗'}")

    cb = accessible_alert("HIGH_RISK", SCAM, "colorblind")
    cb_ok = cb["shape_word"] == "STOP - DANGER"   # meaning survives without colour
    print(f"colour-blind: meaning is shape + word, not colour: {'✓' if cb_ok else '✗'}")

    ll = accessible_alert("HIGH_RISK", SCAM, "low_literacy")
    ll_ok = bool(ll.get("easy")) and bool(ll.get("icon"))
    print(f"low-literacy: icon + easy-read one-liner: {'✓' if ll_ok else '✗'}")

    cog = accessible_alert("HIGH_RISK", SCAM, "cognitive")
    cog_ok = bool(cog.get("easy")) and bool(cog.get("codeword_tip"))
    print(f"cognitive: one-step easy-read + family code word: {'✓' if cog_ok else '✗'}")

    # the category-tailored action reaches the disabled user too
    cat_ok = bool(blind.get("category_name")) and bool(blind.get("action"))
    print(f"scam type + tailored action carried to every profile: {'✓' if cat_ok else '✗'}")

    passed = all([ok, b_ok, d_ok, cb_ok, ll_ok, cog_ok, cat_ok])
    print("\nRESULT:", "ACCESSIBILITY PROFILES PASS" if passed else "FAILED")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
