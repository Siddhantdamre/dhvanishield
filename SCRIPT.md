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

*[Say this over the idle screen — do NOT point at the page yet, the stage
lights only appear after the first Analyse.]*

> "Every one of these scams follows the same six steps. Authority. Accusation.
> Isolation. Urgency. Then money. In a moment you'll see those six steps light
> up on screen as the system reads them. We fire the warning *before* the money
> moves."

---

## 1:00 – 2:15 · Live demo  ← the most important 75 seconds

*[Switch to the browser at 127.0.0.1:8000]*

> "This is the working system. The examples on the left are real scams. The ones
> on the right are ordinary, legitimate messages. Let me show you four things."

**[Click "Delivery"]** *(right-hand column, under Legitimate)*
> "First — an ordinary message. Your furniture is arriving Friday. Green. The
> meter is flat, the six lights stay dark. It says nothing. That matters,
> because a tool that cries wolf gets switched off, and then it protects nobody."

**[Click "Your OTP"]** *(still under Legitimate)*
> "Here's the harder version of that. A real OTP from your bank — the exact
> words a scam would also use. Still silent. Because it isn't the word 'OTP'
> that's dangerous. It's someone *asking you to read it out.*"

**[Click "Digital arrest"]** *(left-hand column)*
> "Now the scam call. Red immediately — and look at the top. Three lights:
> authority, isolation, financial pull. That is the exact anatomy of a digital
> arrest. He claims to be the police. He cuts her off from anyone who could
> help. He moves her money. It is not just saying 'scam' — it is showing her
> *what is being done to her mind*. And it gives one clear instruction: hang up,
> no police arrests you by phone, call 1930."

**[Click "Tamil scam"]**
> "Same scam, written in Tamil. Still caught — and look, isolation has gone to
> full red here, because that message leans on it even harder. Six languages,
> and in every one of them the system is never allowed to miss a scam."

**[Click "Sextortion"]**
> "Now watch this one — it comes back *amber*, not red. Only one pressure fires.
> The system is telling you it is not confident enough to call this a scam
> outright, so it says 'verify first' instead of guessing.
>
> That is deliberate. It would rather admit uncertainty than be confidently
> wrong. And it still gives the right advice: do not pay, keep the evidence,
> and this is not your fault. That last line matters — shame is why people
> don't report these."

**[Change the profile dropdown to "Blind / low-vision", click Digital arrest again]**
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
Hook (0:00–0:30) → click **Delivery**, then **Digital arrest** (point at the six
lights) → the 0.02% / 98.8% numbers → the honest close. Skip everything else.

## Three questions you will probably get

**"How is this different from Truecaller?"**
> "Truecaller matches the number, and scammers change numbers daily. We read the
> manipulation technique in the words, which doesn't change. Different signal
> entirely — and we run on-device, so we never upload your contacts."

**"Is 0.02% false alarm real, or on synthetic data?"**
> "Real. Four thousand eight hundred and twenty-seven genuine messages, held out.
> The synthetic data was for training the pattern layer; the headline numbers are
> all measured on real data, and I separate the two clearly in the document."

**"Why did the sextortion one only come back amber, not red?"** ← they will ask
> "Because only one pressure fired — urgency. There's no fake authority and no
> isolation in that message, so the evidence genuinely is thinner. The system is
> built to abstain rather than over-claim, and amber still routes the user to
> the right advice. I'd rather it say 'I'm not sure, verify first' than teach
> people to trust a red light it hasn't earned. The design rule is that it can
> never say *safe* — amber and red both protect you; only a false green hurts."

**"What happens if the scammer changes their script?"**
> "That's exactly why we detect strategy instead of keywords. We tested it on
> obfuscated text, code-mixed Hinglish, and scam types the system had never seen —
> it still caught ninety-four percent. If it can't tell, it abstains and says
> 'verify independently' rather than guessing."

**Anything you don't know:**
> "Honestly, I haven't validated that yet. Here's what I *have* measured, and
> here's how I would test it."
