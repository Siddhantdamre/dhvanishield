"""DhvaniShield deployment server.

Run:      uvicorn server:app --host 0.0.0.0 --port 8000
Docker:   docker build -t dhvanishield . && docker run -p 8000:8000 dhvanishield

Endpoints
  GET  /health            liveness
  POST /v1/check          {"text": "...", "lang": "en|hi|mr"} ->
                          verdict + action + manipulation meter +
                          accessible renderings (speech/picto/codeword)
  POST /v1/check-audio    multipart file upload (a voice note) -> same
                          shape as /v1/check, plus the transcript and a
                          transcription_failed flag. A recording that
                          can't be transcribed returns UNCERTAIN, never
                          a false-safe NO_PATTERN (see shield/speech.py).
  POST /webhook/whatsapp  Twilio-compatible form webhook (field: Body).
                          Replies with plain-text verdict + Unicode meter
                          so it drops into a WhatsApp thread unchanged.

Design notes
  * The ML paraphrase-expert is trained at startup (seconds, seed-fixed,
    fully local) — no model artifacts to ship, no API keys, no GPU.
  * Process-and-delete: nothing is persisted; no call content is logged.
  * The gate is asymmetric end-to-end: no endpoint can return a
    certified-'safe' answer.
"""
import os
import tempfile
import time
import uuid

from fastapi import FastAPI, Form, UploadFile, File, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel

from shield.datagen import make_dataset
from shield.ml import train_layer, hybrid_assess
from shield.engine import assess
from shield.meter import meter
from shield.access import accessible_bundle
from shield.speech import assess_audio
from shield.policy import decide, AMBIENT
from shield.feedback import record_feedback, corpus_stats
from shield.categories import categorize
from shield.accessibility import accessible_alert
from shield.receipt import issue as issue_receipt, verify as verify_receipt
from shield import misinfo
from shield import manipulation
from shield import security
from shield.observability import (METRICS, MODEL_VERSION, prometheus_text,
                                  get_logger, log_event)
from tests.data import BENIGN, AMBIGUOUS

app = FastAPI(title="DhvaniShield", version="1.0")
logger = get_logger()

# Paths exempt from rate limiting and access logging (probes + scrape).
_INFRA_PATHS = {"/health", "/healthz", "/readyz", "/metrics", "/metrics.json"}


@app.middleware("http")
async def observe_and_limit(request: Request, call_next):
    """Cross-cutting: per-IP rate limit, latency + status metrics, and a
    structured access log line per request. Records aggregate signals
    only — never request bodies or transcripts."""
    rid = uuid.uuid4().hex[:12]
    path = request.url.path

    if path not in _INFRA_PATHS:
        allowed, retry = security.limiter.check(security.client_ip(request))
        if not allowed:
            METRICS.record_request(429, 0.0)
            log_event(logger, "rate_limited", request_id=rid, path=path,
                      client=security.client_ip(request), retry_after_s=retry)
            return JSONResponse(
                {"detail": "rate limit exceeded", "retry_after_s": retry},
                status_code=429,
                headers={"Retry-After": str(retry), "X-Request-ID": rid})

    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        latency = (time.perf_counter() - start) * 1000
        METRICS.record_request(500, latency)
        log_event(logger, "unhandled_error", request_id=rid, path=path,
                  latency_ms=round(latency, 2))
        raise
    latency = (time.perf_counter() - start) * 1000
    METRICS.record_request(response.status_code, latency)
    response.headers["X-Request-ID"] = rid
    # Standard security headers on every response.
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    if path not in _INFRA_PATHS:
        log_event(logger, "request", request_id=rid, method=request.method,
                  path=path, status=response.status_code,
                  latency_ms=round(latency, 2),
                  client=security.client_ip(request))
    return response


from shield.training import build_deployed_layer, sources
LAYER = build_deployed_layer()
log_event(logger, "model_ready", **sources())   # log the blended sources
# Refuse to silently ship an insecure config (open auth / forgeable receipts).
security.enforce_or_warn(lambda m: log_event(logger, "SECURITY_WARNING", warning=m))

VERDICT_HEAD = {
    "HIGH_RISK": "🔴 DANGER — likely scam",
    "UNCERTAIN": "🟡 Be careful — verify first",
    "NO_PATTERN": "🟢 Looks like a normal call",
}


class CheckIn(BaseModel):
    text: str
    lang: str = "en"
    profile: str = "default"      # accessibility profile


class ScreenIn(BaseModel):
    text: str
    lang: str = "en"
    trusted_contact: str | None = None
    profile: str = "default"      # blind | deaf | low_literacy | cognitive | colorblind


class AnalyzeIn(BaseModel):
    text: str
    lang: str = "en"


class ManipulationIn(BaseModel):
    text: str


class FeedbackIn(BaseModel):
    text: str
    model_verdict: str        # the verdict the user is reacting to
    is_scam: bool             # the human ground-truth label
    consent: bool = False     # store ONLY if the user explicitly consents
    lang: str = "en"


class ReceiptVerifyIn(BaseModel):
    receipt: dict             # a receipt previously issued by /v1/check
    text: str | None = None   # optionally, the original message to match


@app.get("/health")
def health():
    """Liveness — process is up. Kept for backward compatibility."""
    return {"ok": True}


@app.get("/healthz")
def healthz():
    """Liveness probe (k8s convention)."""
    return {"ok": True}


@app.get("/readyz")
def readyz():
    """Readiness probe — the ML expert must be trained before we serve."""
    ready = LAYER is not None
    return JSONResponse(
        {"ready": ready, "model_version": MODEL_VERSION,
         "t_red": round(LAYER.t_red, 3), "t_yellow": round(LAYER.t_yellow, 3)},
        status_code=200 if ready else 503)


@app.get("/metrics")
def metrics_prometheus():
    """Prometheus scrape target — aggregate, content-free signals."""
    return PlainTextResponse(prometheus_text(),
                             media_type="text/plain; version=0.0.4")


@app.get("/metrics.json")
def metrics_json():
    """Same signals as /metrics in JSON — convenient for a demo dashboard."""
    return METRICS.snapshot()


@app.post("/v1/check", dependencies=[Depends(security.require_api_key)])
def check(body: CheckIn):
    if len(body.text) > security.MAX_TEXT_CHARS:
        raise HTTPException(status_code=413,
                            detail=f"text exceeds {security.MAX_TEXT_CHARS} chars")
    final, rules_lvl, ml_lvl, p = hybrid_assess(body.text, LAYER)
    METRICS.record_verdict(final)
    v = assess(body.text)
    cat = categorize(body.text) if final != "NO_PATTERN" else None
    return {
        "verdict": final,
        "action": v.action if final == v.level else
                  {"HIGH_RISK": "This matches scam patterns. Hang up now. "
                                "Call 1930. Tell a family member.",
                   "UNCERTAIN": v.action, "NO_PATTERN": v.action}[final],
        "meter": meter(body.text),
        "explanation": v.explanation,
        "category": cat,
        "accessibility": accessible_bundle(final, body.lang),
        "accessible": accessible_alert(final, body.text, body.profile, body.lang),
        "committee": {"rules": rules_lvl, "ml": ml_lvl,
                      "ml_prob": round(p, 3)},
        # Duty-of-care warning receipt: tamper-proof, content-free proof that
        # this message was assessed and (if a scam) the customer was warned.
        "receipt": issue_receipt(body.text, final,
                                 cat["category"] if cat else None,
                                 warned=(final != "NO_PATTERN")),
    }


@app.post("/v1/manipulation", dependencies=[Depends(security.require_api_key)])
def manipulation_analyze(body: ManipulationIn):
    """Universal manipulation analysis — the domain-general strategy engine.
    Scores the influence STRATEGY (authority, urgency, isolation, override...),
    not the domain, so it works on a scam call, a coercive message, OR a
    prompt-injection attempt aimed at an AI. Returns the strategy vector, a
    pressure score, the dominant strategies (explanation) and an uncertainty."""
    if len(body.text) > security.MAX_TEXT_CHARS:
        raise HTTPException(status_code=413,
                            detail=f"text exceeds {security.MAX_TEXT_CHARS} chars")
    return manipulation.analyze(body.text)


@app.post("/v1/analyze", dependencies=[Depends(security.require_api_key)])
def analyze(body: AnalyzeIn):
    """Manipulation-defence analysis over BOTH problem domains: scam and
    misinformation. Returns the dominant threat class plus each assessment.
    The layer's reach beyond scams, on the same forwarded-message channel."""
    if len(body.text) > security.MAX_TEXT_CHARS:
        raise HTTPException(status_code=413,
                            detail=f"text exceeds {security.MAX_TEXT_CHARS} chars")
    order = {"NO_PATTERN": 0, "UNCERTAIN": 1, "HIGH_RISK": 2}
    scam_final, *_ = hybrid_assess(body.text, LAYER)
    METRICS.record_verdict(scam_final)
    scam_cat = categorize(body.text) if scam_final != "NO_PATTERN" else None
    mis = misinfo.detect(body.text)

    if order[scam_final] == 0 and order[mis["level"]] == 0:
        threat = "none"
    elif order[scam_final] >= order[mis["level"]]:
        threat = "scam"
    else:
        threat = "misinformation"
    return {
        "threat_class": threat,
        "scam": {"verdict": scam_final, "category": scam_cat},
        "misinformation": {"level": mis["level"], "why": mis["explanation"],
                           "action": mis["action"]},
        "receipt": issue_receipt(body.text, threat, scam_cat["category"] if scam_cat else
                                 (mis["level"] if threat == "misinformation" else None),
                                 warned=(threat != "none")),
    }


@app.post("/v1/screen", dependencies=[Depends(security.require_api_key)])
def screen(body: ScreenIn):
    """Ambient (always-on) surface. Silence is the default: this returns a
    user-facing alert ONLY for a confident, structured scam; UNCERTAIN is
    held silently ("watching"), NO_PATTERN says nothing. This is what an
    on-device call-screening client polls so it never nags on normal calls.
    Use /v1/check for the proactive 'is this real?' path where the user
    asked and always wants an answer."""
    if len(body.text) > security.MAX_TEXT_CHARS:
        raise HTTPException(status_code=413,
                            detail=f"text exceeds {security.MAX_TEXT_CHARS} chars")
    final, *_ = hybrid_assess(body.text, LAYER)
    METRICS.record_verdict(final)
    interaction = decide(final, mode=AMBIENT, lang=body.lang,
                         trusted_contact=body.trusted_contact)
    alert = accessible_alert(final, body.text, body.profile, body.lang,
                             body.trusted_contact) if interaction.surfaced else None
    return {
        "surfaced": interaction.surfaced,
        "state": interaction.state,
        "watching": interaction.watching,
        "alert": alert,
    }


@app.post("/v1/feedback", dependencies=[Depends(security.require_api_key)])
def feedback(body: FeedbackIn):
    """The data flywheel. If (and only if) the user consents, store one
    redacted, anonymous labelled example so the model can be retrained on
    real phone-scam data — the only thing that improves real accuracy
    (see tests/eval_train_real.py). No consent => nothing is stored."""
    if len(body.text) > security.MAX_TEXT_CHARS:
        raise HTTPException(status_code=413,
                            detail=f"text exceeds {security.MAX_TEXT_CHARS} chars")
    return record_feedback(body.text, body.model_verdict, body.is_scam,
                           body.consent, body.lang)


@app.post("/v1/receipt/verify", dependencies=[Depends(security.require_api_key)])
def receipt_verify(body: ReceiptVerifyIn):
    """Verify a duty-of-care warning receipt — for a bank's dispute or a
    regulator. Confirms the receipt is authentic (not tampered) and, if the
    original message is supplied, that it is the exact message assessed."""
    return verify_receipt(body.receipt, body.text)


@app.get("/v1/corpus/stats", dependencies=[Depends(security.require_api_key)])
def corpus():
    """Transparency: content-free view of the collected corpus, including
    where the model disagreed with humans (the training signal)."""
    return corpus_stats()


@app.post("/v1/check-audio", dependencies=[Depends(security.require_api_key)])
async def check_audio(file: UploadFile = File(...), lang: str = "en"):
    """Voice-note input. Saves the upload to a temp path (deleted right
    after, same process-and-delete contract as text), transcribes it,
    then runs the SAME hybrid rules+ML pipeline as /v1/check so a spoken
    complaint gets exactly the same scrutiny as a typed one."""
    suffix = os.path.splitext(file.filename or "")[1] or ".ogg"
    tmp_path = None
    try:
        data = await file.read()
        if len(data) > security.MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"upload exceeds {security.MAX_UPLOAD_BYTES} bytes")
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name

        av = assess_audio(tmp_path)
        if av.transcription_failed:
            METRICS.record_transcription_failure()
            METRICS.record_verdict(av.verdict.level)
            return {
                "verdict": av.verdict.level,
                "action": av.verdict.action,
                "transcript": None,
                "transcription_failed": True,
                "meter": {"pressures": {}, "overall": 0, "bars": "(no transcript)"},
                "explanation": av.verdict.explanation,
                "accessibility": accessible_bundle(av.verdict.level, lang),
            }

        # Same committee as /v1/check: hybrid rules+ML final verdict,
        # rules-only Verdict for the richer action/explanation text.
        final, rules_lvl, ml_lvl, p = hybrid_assess(av.transcript, LAYER)
        METRICS.record_verdict(final)
        v = assess(av.transcript)
        return {
            "verdict": final,
            "action": v.action if final == v.level else
                      {"HIGH_RISK": "This matches scam patterns. Hang up now. "
                                    "Call 1930. Tell a family member.",
                       "UNCERTAIN": v.action, "NO_PATTERN": v.action}[final],
            "transcript": av.transcript,
            "transcription_failed": False,
            "meter": meter(av.transcript),
            "explanation": v.explanation,
            "accessibility": accessible_bundle(final, lang),
            "committee": {"rules": rules_lvl, "ml": ml_lvl, "ml_prob": round(p, 3)},
        }
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/webhook/whatsapp", response_class=PlainTextResponse)
async def whatsapp(request: Request):
    form = await request.form()
    Body = (form.get("Body") or "").strip()
    # Twilio request-signature validation — active whenever the auth token is
    # configured, closing the otherwise-open webhook. Skipped in dev (no token).
    token = os.getenv("DHVANI_TWILIO_AUTH_TOKEN")
    if token:
        params = {k: str(v) for k, v in form.items()}
        if not security.validate_twilio(
                str(request.url), params,
                request.headers.get("X-Twilio-Signature", ""), token):
            raise HTTPException(status_code=403, detail="invalid Twilio signature")
    if not Body:
        return ("Namaste 🙏 Forward the suspicious message here, or type "
                "what the caller said, and I will check it. "
                "मैं किसी भी भाषा में जाँच कर सकता हूँ।")
    # NOTE: the UCI-trained message expert is deliberately NOT used here.
    # Measured (this channel): it over-flags legit transactional messages
    # (delivery/EMI/OTP) because UCI 'ham' is casual chat, not transactional
    # text — a distribution bias. The phone committee handles these correctly
    # (its seed data includes real transactional benigns). The message expert
    # returns once the flywheel provides real forwarded-message labels.
    final, *_ = hybrid_assess(Body, LAYER)
    METRICS.record_verdict(final)
    v = assess(Body)
    m = meter(Body)
    b = accessible_bundle(final, "en")
    lines = [VERDICT_HEAD[final], ""]
    if final != "NO_PATTERN":
        cat = categorize(Body)                     # name the scam + tailored advice
        lines += [f"Type: {cat['icon']} {cat['name']}", cat["action"]["en"]]
    else:
        lines.append(v.action)
    lines += ["", m["bars"], "", b["picto"], "", f"💡 {b['codeword_tip']}"]
    return "\n".join(lines)
