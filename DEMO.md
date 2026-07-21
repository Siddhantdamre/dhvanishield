# DhvaniShield — Live Demo Runbook (90 seconds)

Rehearse this twice before you present. Every command is copy-paste. If the
laptop/wifi acts up, the fallback is a screen recording of this exact script
(record it the night before — that IS your safety net).

## Before you walk up
```
cd path/to/dhvanishield_v6_deploy_1
export PYTHONUTF8=1            # Windows PowerShell: $env:PYTHONUTF8=1
python check.py "hi"          # warm-up: trains the model once (~2s), ignore output
```
Font size up. Terminal on a light theme. That's it — no server, no internet.

## The 4 beats (say the line, run the command)

**Beat 1 — it stays silent on normal calls (the anti-nag).**
Say: "A guardian that cries wolf gets muted. Watch a normal message."
```
python check.py --ambient "Hi, your furniture delivery is scheduled for Friday between 10 and 12"
```
→ `· (silent — no interruption)`  ← point at it. "Nothing. That's the feature."

**Beat 2 — it fires, decisively, on a real scam, and explains it.**
Say: "Now a fake-CBI digital-arrest call."
```
python check.py --ambient "This is CBI, you are under digital arrest, do not tell anyone, transfer money to the safe account now"
```
→ ⛔ STOP, scam type = **Digital arrest / fake police**, the tailored action,
the spoken script, the haptic code, "Call someone you trust."

**Beat 3 — different scam, DIFFERENT correct advice (the categorizer).**
Say: "Same tool, a sextortion call — notice the advice completely changes."
```
python check.py "I recorded your video call, pay 10000 or I send it to your family"
```
→ Scam type = **Sextortion**, Action = *"Do not pay. Keep the evidence.
This is not your fault."*  Say: "A number-blocklist can't do this."

**Beat 4 — it reaches a blind user the same way.**
Say: "And it works for the people scammers actually target."
```
python check.py --ambient --profile=blind "This is CBI, you are under digital arrest, transfer money to the safe account"
```
→ shape+word (colour-blind safe), spoken script, haptic, call-a-person.
Say: "Blind, deaf, low-literacy, cognitive — one alert, rendered for each."

## The closing line (memorize this)
"It never said you're safe. It never accused a real caller. It explained the
manipulation — on-device, in your language. And it's all reproducible:
`python tests/run_all.py`, thirteen out of thirteen."

## If a judge says "run it on THIS":
```
python check.py "whatever the judge dictates"
```
It won't crash and it won't false-clear an obvious scam — that's tested
(`tests/eval_reliability.py`). Confidence sells; the reliability gate is why
you can be confident.

## Fallback order if live fails
1. The screen recording you made the night before.
2. Screenshots on slides 5a–5d.
3. Just narrate slide 7 (the results table) — the numbers stand alone.
