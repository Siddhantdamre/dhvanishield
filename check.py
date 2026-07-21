"""DhvaniShield CLI — one-shot check of a call transcript or message.

  python check.py "he said he is from CBI and I must transfer money"
  echo "your parcel has drugs, stay on the line" | python check.py
  python check.py --json "..."

Prints the verdict, the Manipulation Meter, what the caller is doing, and
the action to take. No server needed; the local model trains in a couple
of seconds at startup.
"""
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from shield.datagen import make_dataset            # noqa: E402
from shield.ml import train_layer, hybrid_assess   # noqa: E402
from shield.engine import assess                    # noqa: E402
from shield.meter import meter                      # noqa: E402
from shield.semantic import SEMANTIC               # noqa: E402
from shield.policy import decide, AMBIENT           # noqa: E402
from shield.categories import categorize            # noqa: E402
from shield.accessibility import accessible_alert   # noqa: E402
from tests.data import BENIGN, AMBIGUOUS           # noqa: E402

HEAD = {
    "HIGH_RISK": "🔴 DANGER — likely scam",
    "UNCERTAIN": "🟡 BE CAREFUL — verify before you act",
    "NO_PATTERN": "🟢 No scam pattern found",
}


def main() -> None:
    as_json = "--json" in sys.argv
    ambient = "--ambient" in sys.argv       # simulate the always-on guardian
    profile = "default"
    args = []
    for a in sys.argv[1:]:
        if a in ("--json", "--ambient"):
            continue
        if a.startswith("--profile="):
            profile = a.split("=", 1)[1]
            continue
        args.append(a)
    text = " ".join(args).strip() or sys.stdin.read().strip()
    if not text:
        print('usage: python check.py [--ambient] [--profile=blind] "transcript"')
        sys.exit(2)

    from shield.training import build_deployed_layer
    layer = build_deployed_layer()

    final, rules_lvl, ml_lvl, prob = hybrid_assess(text, layer)

    if ambient:
        # Silence is the feature: on a normal or merely-uncertain call the
        # always-on guardian says NOTHING. It speaks once, for a confident
        # scam, and then it is impossible to miss.
        it = decide(final, mode=AMBIENT)
        if not it.surfaced:
            print("· (silent — no interruption)" if not as_json
                  else json.dumps({"surfaced": False, "state": it.state}))
            return
        a = accessible_alert(final, text, profile)
        if as_json:
            print(json.dumps({"surfaced": True, "alert": a}, ensure_ascii=False,
                             indent=2))
            return
        print(f"\n{a['shape']}  {a['shape_word']}   [profile: {profile}]")
        if a.get("category_name"):
            print(f"🏷️  {a['category_name']}")
        print(f"➡️  {a['action']}")
        if a.get("speech"):
            print(f"🗣️  {a['speech']}")
        if a.get("easy"):
            print(f"📖  {a['easy']}")
        if a.get("earcon"):
            print(f"🔊  earcon: {a['earcon']}")
        if a.get("picto"):
            print(a["picto"])
        if a.get("haptic"):
            print(f"📳  haptic: {a['haptic']}")
        print(f"📞  {a['call_person']['prompt']}")
        if a.get("note"):
            print(f"ℹ️  {a['note']}")
        print()
        return
    v = assess(text)
    m = meter(text)
    sem = SEMANTIC.explain(text)
    cat = categorize(text) if final != "NO_PATTERN" else None

    if as_json:
        print(json.dumps({
            "verdict": final, "action": v.action, "meter": m,
            "explanation": v.explanation,
            "semantic": sem or None,
            "category": cat,
            "committee": {"rules": rules_lvl, "ml": ml_lvl,
                          "ml_prob": round(prob, 3)},
        }, ensure_ascii=False, indent=2))
        return

    print(f"\n{HEAD[final]}\n")
    print(m["bars"])
    print(f"\nManipulation pressure: {m['overall']}/100")
    if cat:
        print(f"\nScam type: {cat['icon']}  {cat['name']}")
        print(f"Why: {cat['why']}")
    if v.explanation:
        print("\nWhat the caller is doing:")
        for line in v.explanation:
            print(f"  • {line}")
    if sem:
        print(f"  • {sem}")
    action = cat["action"]["en"] if cat else v.action
    print(f"\nAction: {action}")
    print(f"\n(committee — rules:{rules_lvl}  ml:{ml_lvl}  p={prob:.2f})\n")


if __name__ == "__main__":
    main()
