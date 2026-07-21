"""Misinformation-rhetoric detector tests — the new problem domain.

Asymmetric, like the scam engine: catch the manipulative forwards, and
NEVER flag an ordinary personal message as misinformation. CI-safe.
"""
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shield.misinfo import detect   # noqa: E402

MISINFO = [
    "Forward this to 10 people before it is deleted! Doctors don't want you to know boiling this cures cancer 100%.",
    "Government is hiding the truth. Share this with everyone before the media removes it. This really happened.",
    "Drinking hot water with lemon kills the coronavirus. Scientists have proven it. Forward as received to save lives.",
    "Ancient remedy doctors hate: this natural remedy cures all disease. Must read and share maximum.",
    "सबको भेजो, डॉक्टर नहीं बताते कि यह कैंसर ठीक करता है। डिलीट होने से पहले शेयर करो।",
    "Wake up before it's too late. They are planning something dangerous. Protect your family and forward to everyone.",
    "Shocking truth they don't want you to know: this miracle cure prevents all disease. 100% true, share before deleted.",
    "Big pharma is hiding this. A doctor friend confirmed this ancient remedy cures corona. Spread the word, make it viral.",
    "This dangerous chemical in your food will kill you. The truth about it is banned by media. Forward to all.",
    "NASA confirmed 5 days of total darkness next week. Very important message, please read carefully and share to all.",
]
BENIGN = [
    "Good morning! Have a wonderful day. Our meeting is at 10 am today.",
    "Happy birthday! Wishing you a great year ahead. See you at the party.",
    "The match starts at 7 pm, please don't be late. I'll save you a seat.",
    "Please find attached the monthly report for your review. Thanks.",
    "Reminder: your dentist appointment is tomorrow at 3 pm.",
    "Can you send me the photos from the trip when you get a chance?",
    "The train is running on time. I'll reach the station by noon.",
    "Thank you for dinner last night, we had a lovely time.",
]


def main() -> None:
    caught = sum(1 for t in MISINFO if detect(t)["level"] != "NO_PATTERN")
    false_alarm = sum(1 for t in BENIGN if detect(t)["level"] == "HIGH_RISK")
    over_warn = sum(1 for t in BENIGN if detect(t)["level"] == "UNCERTAIN")
    passed_clean = sum(1 for t in BENIGN if detect(t)["level"] == "NO_PATTERN")

    print(f"misinformation forwards flagged: {caught}/{len(MISINFO)}")
    print(f"ordinary messages: {passed_clean}/{len(BENIGN)} clean, "
          f"{over_warn} over-warned, {false_alarm} false-alarmed")

    # asymmetric contract: high recall on misinfo, ZERO false accusations
    ok = caught >= 9 and false_alarm == 0
    print("\nRESULT:", "MISINFO DETECTOR PASS" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
