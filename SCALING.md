# DhvaniShield — Scaling & Deployment

The honest scaling principle: **the tech is done and at its data ceiling;
the bottleneck is users and real data.** So scale distribution first, and
scale infrastructure only when real load forces it. Building the plumbing
before you have water is the classic way to waste the run.

North-star metric: **weekly active users × consented real labels collected.**
Not accuracy (capped), not features (enough) — that number.

---

## Step 1 (do this first): put the WhatsApp bot in real hands
The forwarded-message channel needs zero install and zero call access, and
your `/webhook/whatsapp` endpoint already serves it — now with the scam
category and the real-data message expert. Getting it live:

1. **Deploy the server** (any container host — Render/Railway/Fly/a VPS):
   ```
   docker build -t dhvanishield .
   docker run -p 8000:8000 dhvanishield          # or push to the host
   ```
   It's stateless and CPU-only (~7 MB model), so the smallest instance is fine.
2. **Get a public HTTPS URL** (the host gives you one; or `ngrok http 8000`
   for a same-day test).
3. **Twilio WhatsApp Sandbox** (free, ~10 min): in the Twilio console →
   Messaging → Try it out → WhatsApp sandbox. Set the "When a message comes
   in" webhook to `https://YOUR_URL/webhook/whatsapp` (HTTP POST).
4. **Test it**: from your phone, join the sandbox, forward a suspicious SMS.
   You get back the verdict + scam type + what to do + the meter. Done.
5. **Get 50 real users**: not strangers — *adult children setting it up for a
   parent*, or one local NGO / senior-citizens' group. Teach one sentence:
   "when in doubt, forward it to this number."

That single step validates real-world usage and starts the flywheel. Nothing
else on this page matters until it's done.

## Step 2: close the flywheel (already built)
Each user's consented "yes, that was a scam" tap → `POST /v1/feedback` →
a redacted, anonymous labelled example. `tests/eval_learning.py` shows the
hard-negative miner picking the highest-value labels. The model improves past
the authored-data ceiling, and the dataset becomes the moat.

## Step 3: scale infrastructure — ONLY when real traffic arrives
You are already built for this (stateless + collect-nothing = trivial to
scale, and privacy liability does not grow with users). When load justifies
it, in order:
- [ ] Containerised deploy behind a load balancer; run N stateless replicas.
- [ ] **Redis-backed rate limiter** (the one documented single-node gap in
      `shield/security.py`) so limits are shared across replicas.
- [ ] Ship `/metrics` to Prometheus + alerting (verdict mix, p95 latency,
      error rate — all content-free).
- [ ] CI is already wired (`.github/workflows/ci.yml`); add deploy-on-green.
- [ ] Ship the trained message model as an artifact (`models/`) so replicas
      don't each retrain.
Capacity today: ~143 req/s per node at 100% success (`tests/loadtest.py`);
horizontal scaling is linear because there's no shared state.

## Step 4: scale channels — one at a time, each with its own real data
Message/SMS → WhatsApp → on-device call screening. **Never merge channels
into one model** (proven to poison calibration). Each channel is its own
expert, validated on its own real data, combined by the escalate-only
committee rule. Add the next only after the current one has users.

## Step 5: scale through partners (B2B2C)
A bank / telco / government helpline is the real multiplier — hundreds to
millions. The materials for that conversation already exist:
`POSITIONING.md`, `THREAT_MODEL.md`, `PRIVACY.md`. The gate is a DPDP +
security audit, which is a partner-funded step.

## Step 6: scale the team
Solo cannot do mobile + partnerships + ops + ML. Bring in complementary
people, or aim to be acquired into the carrier/OS layer where this belongs.

## Do NOT do yet (premature-scaling traps)
- ❌ k8s / microservices / Redis before there is traffic.
- ❌ more model complexity (at ceiling — `tests/eval_message_improve.py`).
- ❌ more features (categoriser + accessibility are enough for v1).
- ❌ live-call ambient (v3) before pull-based v1 has users.

**One line:** scale the distribution (WhatsApp → one NGO/partner) and let the
flywheel scale the data; the infrastructure only needs to grow *after* the
users do.
