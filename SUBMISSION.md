# Submission Checklist — DhvaniShield

Everything below is done unless marked `[ ]`. Work top to bottom on the 22nd.

## 1. Verify it runs (do this first, on the machine you'll submit from)
```
cd dhvanishield_v6_deploy_1
pip install -r requirements.txt
export PYTHONUTF8=1        # PowerShell: $env:PYTHONUTF8=1
python tests/run_all.py    # expect: 22/22 suites passed
```
Screenshot the `22/22` line — it goes on your results slide.

## 2. `[ ]` Make it a git repo (it currently is NOT one)
```
git init
git add .
git commit -m "DhvaniShield: manipulation-defence layer for scam calls"
# then create an empty repo on GitHub and:
git remote add origin <your-repo-url>
git branch -M main
git push -u origin main
```
`.gitignore` already excludes the SMS dataset, the trained model cache, the
feedback corpus, and `__pycache__` — so nothing private or heavy ships.

## 3. `[ ]` Record the demo video (your safety net)
Follow `PRESENT.md` §3 and screen-record the four beats (~90s):
silent on normal → fires on scam → different advice for sextortion →
blind profile. If the laptop fails live, you play this.

## 4. `[ ]` Build the slides
`DECK.md` has all 12 slides with speaker notes and timing. Paste into your
template. Put the `22/22` screenshot and the numbers table on the results slide.

## 5. Submission blurb (paste-ready)
> **DhvaniShield** — an on-device manipulation-defence layer that protects
> people from scam calls and messages in their own language, and explains
> *how* they are being manipulated. Unlike caller-ID tools, which match the
> *number*, it reads the *technique* — so it works on fresh SIMs, spoofed
> IDs, and scripts it has never seen. It is built so it can never tell you a
> scam is safe, and never falsely accuses a real caller. Runs fully
> on-device (nothing leaves the phone), in 6 languages, with six
> accessibility profiles for blind, deaf, low-literacy and elderly users.
> Validated on 5,574 real messages: 0.02% false-alarm, calibrated to defer
> 2% of cases to a human to hold ≤1% error. 22 reproducible test suites.

## 6. The numbers to quote (all reproducible)
| Claim | Number |
|---|---|
| False alarm on 4,827 **real** legitimate messages | **0.02%** |
| Real held-out message accuracy | **98.8%** |
| Calibrated defer-to-human | **2% deferred → ≤1% error** |
| Languages with no false reassurance | **6** |
| Out-of-distribution scam recall / false-reassurance | **100% / 0** |
| Manipulation engine on **real** data (honest) | **AUC 0.66** (probe said 0.94) |

## 7. Say the limits out loud (this is what makes it credible)
- Validated on real **messages**, not live **phone calls** — that needs a pilot.
- The manipulation engine is 0.66 on real data; my hand-authored probe said
  0.94. Real data is harder, and I report the real number.
- ~27% of ambiguous authority calls get "verify independently" — deliberate
  abstention, not a defect.

## 8. Where everything is
| Need | File |
|---|---|
| How to present, start to finish | `PRESENT.md` |
| Slides | `DECK.md` |
| Live demo commands | `DEMO.md` |
| Hard questions + answers | `JUDGE_QA.md` |
| How it's built | `ARCHITECTURE.md` |
| Why not Truecaller / trust model | `POSITIONING.md` |
| SDG / impact | `IMPACT.md` |
| Metrics, biases, caveats | `MODEL_CARD.md` |
| Security posture | `SECURITY.md` |
| Research direction | `RESEARCH_MANIPULATION.md` |
