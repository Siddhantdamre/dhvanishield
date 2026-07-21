"""Multilingual coverage — no language barrier on the fatal error.

A scam missed because it is written in Tamil instead of Hindi is a false
reassurance, and false reassurance is the one error this system may never
make. This gate holds the same digital-arrest scam across languages and
requires it is never called safe, while ordinary messages in those same
languages stay clean.
"""
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shield.training import build_deployed_layer   # noqa: E402
from shield.ml import hybrid_assess                 # noqa: E402

LAYER = build_deployed_layer()

SCAMS = {
    "English": "This is CBI, a case is registered in your name, do not tell anyone, transfer the money to the safe account",
    "Hindi": "मैं सीबीआई से बोल रहा हूँ, आपके नाम पर केस है, किसी को मत बताना, पैसे ट्रांसफर करो",
    "Marathi": "मी सीबीआयमधून बोलतोय, तुमच्या नावावर गुन्हा आहे, कोणालाही सांगू नका, पैसे पाठवा",
    "Tamil": "நான் சிபிஐ யிலிருந்து பேசுகிறேன், உங்கள் பெயரில் வழக்கு உள்ளது, யாரிடமும் சொல்லாதீர்கள், பணத்தை மாற்றுங்கள்",
    "Telugu": "నేను సిబిఐ నుండి మాట్లాడుతున్నాను, మీ పేరు మీద కేసు ఉంది, ఎవరికీ చెప్పకండి, డబ్బు బదిలీ చేయండి",
    "Bengali": "আমি সিবিআই থেকে বলছি, আপনার নামে মামলা আছে, কাউকে বলবেন না, টাকা ট্রান্সফার করুন",
}
BENIGN = {
    "Tamil": "வணக்கம், நாளை மருத்துவரிடம் உங்கள் நேரம் காலை பத்து மணிக்கு உள்ளது",
    "Bengali": "আপনার পার্সেল আজ বিকেলে পৌঁছে যাবে, ধন্যবাদ",
    "Hindi": "नमस्ते, कल आपकी डॉक्टर से अपॉइंटमेंट सुबह दस बजे है",
}


def main() -> None:
    reassured, false_alarm = [], []
    print("scam across languages (must never be NO_PATTERN):")
    for lang, t in SCAMS.items():
        lvl = hybrid_assess(t, LAYER)[0]
        print(f"  {lvl:11} {lang}")
        if lvl == "NO_PATTERN":
            reassured.append(lang)

    print("\nordinary messages (must never be HIGH_RISK):")
    for lang, t in BENIGN.items():
        lvl = hybrid_assess(t, LAYER)[0]
        print(f"  {lvl:11} {lang}")
        if lvl == "HIGH_RISK":
            false_alarm.append(lang)

    ok = not reassured and not false_alarm
    if reassured:
        print(f"\nFALSE REASSURANCE in: {reassured}")
    if false_alarm:
        print(f"\nFALSE ALARM in: {false_alarm}")
    print("\nRESULT:", f"NO LANGUAGE BARRIER ({len(SCAMS)} languages)" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
