"""Observability — privacy-preserving metrics and structured logging.

Deliberately content-free. We record verdict *labels*, latencies, status
codes and counts — never transcript text, request bodies, or any call
content. This keeps the process-and-delete privacy contract intact while
still giving an operator the signals they need: throughput, latency
percentiles, verdict mix, error rate, transcription-failure rate.

Honest note on FRR: false-reassurance rate — the metric that matters most
— cannot be measured live, because it needs ground-truth labels that we
deliberately do not collect. Production FRR monitoring therefore requires
an opt-in labelled-feedback channel (roadmap). What is exposed here is
everything measurable *without* touching content.
"""
import json
import logging
import sys
import threading
import time
from collections import Counter, deque

MODEL_VERSION = "hybrid-charngram-lr/seed42/n300"


class _Metrics:
    """In-process, thread-safe, aggregate-only. No content ever stored."""

    def __init__(self, window: int = 2048):
        self.started = time.time()
        self.requests = 0
        self.errors = 0
        self.status = Counter()
        self.verdicts = Counter()
        self.transcription_failures = 0
        self.latencies_ms = deque(maxlen=window)
        self._lock = threading.Lock()

    def record_request(self, status_code: int, latency_ms: float) -> None:
        with self._lock:
            self.requests += 1
            self.status[str(status_code)] += 1
            if status_code >= 500:
                self.errors += 1
            self.latencies_ms.append(latency_ms)

    def record_verdict(self, verdict: str) -> None:
        with self._lock:
            self.verdicts[verdict] += 1

    def record_transcription_failure(self) -> None:
        with self._lock:
            self.transcription_failures += 1

    @staticmethod
    def _percentile(data: list, pct: float) -> float:
        if not data:
            return 0.0
        s = sorted(data)
        k = max(0, min(len(s) - 1, int(round((pct / 100) * (len(s) - 1)))))
        return s[k]

    def snapshot(self) -> dict:
        with self._lock:
            lat = list(self.latencies_ms)
            return {
                "uptime_s": round(time.time() - self.started, 1),
                "requests_total": self.requests,
                "errors_total": self.errors,
                "status": dict(self.status),
                "verdicts": dict(self.verdicts),
                "transcription_failures_total": self.transcription_failures,
                "latency_ms": {
                    "p50": round(self._percentile(lat, 50), 2),
                    "p95": round(self._percentile(lat, 95), 2),
                    "p99": round(self._percentile(lat, 99), 2),
                    "count": len(lat),
                },
                "model_version": MODEL_VERSION,
            }


METRICS = _Metrics()


def prometheus_text() -> str:
    """Prometheus text exposition format (v0.0.4) — scrapeable, no dep."""
    s = METRICS.snapshot()
    out: list[str] = []

    def metric(name, value, help_, typ="gauge", labels=""):
        out.append(f"# HELP {name} {help_}")
        out.append(f"# TYPE {name} {typ}")
        out.append(f"{name}{labels} {value}")

    metric("dhvani_uptime_seconds", s["uptime_s"], "Process uptime in seconds")
    metric("dhvani_requests_total", s["requests_total"],
           "Total HTTP requests handled", "counter")
    metric("dhvani_errors_total", s["errors_total"],
           "Total 5xx responses", "counter")
    metric("dhvani_transcription_failures_total",
           s["transcription_failures_total"],
           "Audio uploads that could not be transcribed", "counter")

    out.append("# HELP dhvani_verdicts_total Verdicts emitted, by label")
    out.append("# TYPE dhvani_verdicts_total counter")
    for label, n in s["verdicts"].items():
        out.append(f'dhvani_verdicts_total{{verdict="{label}"}} {n}')

    for q in ("p50", "p95", "p99"):
        metric(f"dhvani_latency_ms_{q}", s["latency_ms"][q],
               f"Request latency {q} in milliseconds")

    metric("dhvani_build_info", 1, "Build/version info", "gauge",
           f'{{model_version="{s["model_version"]}"}}')
    return "\n".join(out) + "\n"


# ---------------- structured logging ----------------
class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        extra = getattr(record, "extra_fields", None)
        if extra:
            payload.update(extra)
        return json.dumps(payload, ensure_ascii=False)


def get_logger(name: str = "dhvanishield") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def log_event(logger: logging.Logger, msg: str, **fields) -> None:
    """Log one structured line. Callers pass only non-content fields —
    request_id, path, status, latency_ms, verdict, client — never text."""
    logger.info(msg, extra={"extra_fields": fields})
