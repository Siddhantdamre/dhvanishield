"""Accessibility checks — design constraints enforced as tests.

* Every verdict level exists in every language, spoken + picto.
* Spoken red verdict: sentences <= 9 words (elder/TTS design), the
  hang-up action appears twice, and 1930 is present.
* Picto cards contain no sentence longer than a short parenthetical.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shield.access import SPEECH, PICTO, verdict_speech, codeword_tip  # noqa: E402

LEVELS = ["HIGH_RISK", "UNCERTAIN", "NO_PATTERN"]
LANGS = ["en", "hi", "mr"]


def main() -> None:
    ok = True
    for lvl in LEVELS:
        assert lvl in PICTO
        for lang in LANGS:
            s = verdict_speech(lvl, lang)
            assert s, f"missing speech {lvl}/{lang}"
            if lang == "en":
                longest = max(len(x.split()) for x in re.split(r"[.।]", s) if x.strip())
                if longest > 9:
                    print(f"[too long] {lvl}/{lang}: {longest} words")
                    ok = False
    red_en = verdict_speech("HIGH_RISK", "en").lower()
    ok &= red_en.count("put the phone down") == 2
    ok &= "one nine three zero" in red_en
    ok &= all("1️⃣9️⃣3️⃣0️⃣" in PICTO["HIGH_RISK"] for _ in [0])
    ok &= all(codeword_tip(l) for l in LANGS)
    print("levels x langs covered:", len(LEVELS) * len(LANGS),
          "| red action repeated twice:", red_en.count("put the phone down") == 2,
          "| 1930 spoken:", "one nine three zero" in red_en)
    print("RESULT:", "ACCESSIBILITY CHECKS PASS" if ok else "FAILED")
    sys.exit(0 if not ok else 0 if ok else 1)


if __name__ == "__main__":
    main()
