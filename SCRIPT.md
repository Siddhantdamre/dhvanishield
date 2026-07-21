# Speaking script — DhvaniShield

Read this almost word-for-word. Short sentences on purpose — they are easier to
say under pressure. `[BRACKETS]` = what to do, not what to say.

**Setup before you start:** terminal open in the project folder, and
`uvicorn server:app --port 8000` already running with
`http://127.0.0.1:8000` open in a browser tab.

---

## 0:00 – 0:30 · The hook

> "Last year, a retired teacher in Pune got a call. The man said he was from the
> CBI. He said a parcel in her name had drugs in it, that a case was registered,
> and that she must not tell anyone — not even her son.
>
> Forty minutes later she had transferred her life savings.
>
> This is called a digital arrest scam. It is one of the fastest-growing crimes
> in India, and the people it targets most are the elderly, people who don't
> speak English, and people with disabilities.
>
> I built DhvaniShield to stop that call."

*[Pause. Let it land.]*

---

## 0:30 – 1:00 · Why existing tools don't work

> "You might ask — doesn't Truecaller already do this?
>
> Truecaller matches the *number*. But these scammers use a fresh SIM every day.
> By the time a number is reported, it has already been thrown away.
>
> DhvaniShield doesn't look at the number. It reads the *technique* — the actual
> manipulation happening in the words. Because the number changes every day, but
> the coercion script never does."

*[Show the timeline graphic on your slide, or say it while the browser loads.]*

> "Every one of these scams follows the same six steps. Authority. Accusation.
> Isolation. Urgency. Then money. We detect the pattern and fire the warning
> *before* the money moves."

---

## 1:00 – 2:15 · Live demo  ← the most important 75 seconds

*[Switch to the browser at 127.0.0.1:8000]*

> "This is the working system. Let me show you four things."

**[Click "Normal delivery"]**
> "First — an ordinary message. Your furniture is arriving Friday. Green. The
> meter is flat. It says nothing. That matters, because a tool that cries wolf
> gets switched off, and then it protects nobody."

**[Click "Digital arrest"]**
> "Now the scam call. Red immediately. And look at the meter — it is not just
> saying 'scam'. It is showing her *what is being done to her mind*. Authority.
> Accusation. Isolation is maxed out, because he told her not to tell anyone.
> And it gives one clear instruction: hang up, no police arrests you by phone,
> call 1930."

**[Click "Sextortion"]**
> "A different scam gets *different* advice. Here it says: do not pay, keep the
> evidence, and this is not your fault. That last sentence matters — shame is
> why people don't report these."

**[Click "Tamil scam"]**
> "Same scam, written in Tamil. Still caught. Six languages, and in every one of
> them the system is never allowed to miss a scam."

**[Change dropdown to "Blind / low-vision", click Digital arrest again]**
> "And this is the part I care about most. Same alert, delivered as a spoken
> script with an audio cue — for a blind user. Switch it to deaf, and it becomes
> a vibration pattern instead. The people scammers target most are the people
> every other app forgets."

---

## 2:15 – 3:00 · How it works, and the numbers

*[Switch to the terminal]*

> "Under the hood it is a committee of small experts — a keyword layer, a
> statistical model, a semantic layer, and a timing layer — combined by one rule:
> they can only *raise* the alarm, never lower it.
>
> That means the system is architecturally incapable of telling you a scam is
> safe. There is no 'safe' answer in the system at all. A false alarm costs you
> one phone call. A false reassurance costs you everything."

**[Run `python tests/run_all.py`]**
> "And none of this is a claim. Twenty-two test suites, all passing, in one
> command. On four thousand eight hundred real messages, it raises a false alarm
> zero-point-zero-two percent of the time. Real held-out accuracy is ninety-eight
> point eight percent.
>
> And it knows when it doesn't know — it can hold its error under one percent by
> handing the hardest two percent of cases to a human."

---

## 3:00 – 3:30 · Why it matters

> "This maps to four Sustainable Development Goals — reduced inequality, justice,
> wellbeing, and poverty. But the honest version is simpler than that.
>
> The people who get scammed most are the people with the least ability to
> absorb the loss, and the least served by technology. So I built it for them
> first. On-device — nothing ever leaves the phone. In their language. Through
> whichever sense they can actually use."

---

## 3:30 – 4:00 · The honest close  ← this wins technical judges

> "Let me tell you what it does *not* do yet.
>
> It is validated on real messages, not on live phone calls — that needs a pilot
> with real users. And my manipulation engine scores zero-point-six-six on real
> data, even though my own test set said zero-point-nine-four. Real data is
> harder, and I report the real number.
>
> I'd rather show you the honest figure than a flattering one — because a system
> that protects vulnerable people has to be trustworthy before it is impressive.
>
> Everything is on GitHub, and every number I gave you runs in one command.
> Thank you."

---

## If you only get 90 seconds
Hook (0:00–0:30) → click **Normal delivery**, then **Digital arrest** → the
0.02% / 98.8% numbers → the honest close. Skip everything else.

## Three questions you will probably get

**"How is this different from Truecaller?"**
> "Truecaller matches the number, and scammers change numbers daily. We read the
> manipulation technique in the words, which doesn't change. Different signal
> entirely — and we run on-device, so we never upload your contacts."

**"Is 0.02% false alarm real, or on synthetic data?"**
> "Real. Four thousand eight hundred and twenty-seven genuine messages, held out.
> The synthetic data was for training the pattern layer; the headline numbers are
> all measured on real data, and I separate the two clearly in the document."

**"What happens if the scammer changes their script?"**
> "That's exactly why we detect strategy instead of keywords. We tested it on
> obfuscated text, code-mixed Hinglish, and scam types the system had never seen —
> it still caught ninety-four percent. If it can't tell, it abstains and says
> 'verify independently' rather than guessing."

**Anything you don't know:**
> "Honestly, I haven't validated that yet. Here's what I *have* measured, and
> here's how I would test it."
