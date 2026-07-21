"""Load & latency test — capacity proof for the deployed server.

Spins up a REAL uvicorn server (not the in-process TestClient), fires a
configurable number of concurrent HTTP requests at /v1/check with a
realistic mix of scam / benign / ambiguous payloads, and reports
throughput, success rate, and latency percentiles (p50/p90/p95/p99).
Writes loadtest_results.json and a self-contained loadtest.svg chart.

Rate limiting is deliberately raised out of the way for this run (env
DHVANI_RATE_LIMIT) so we measure raw serving capacity, not the limiter —
the limiter itself is proven separately in tests/eval_hardening.py.

Honest scope: endpoints are synchronous and CPU-bound (vectorise +
logistic-regression predict + rules), so they run in FastAPI's threadpool
and throughput is bounded by CPU, not by an artificial async ceiling.
The number this prints is the honest single-node text-path capacity.

Usage:
  python tests/loadtest.py                      # 2000 reqs, concurrency 50
  python tests/loadtest.py --requests 5000 --concurrency 100 --port 8011
"""
import argparse
import io
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.data import SCAM, BENIGN, AMBIGUOUS  # noqa: E402

PAYLOADS = ([{"text": t, "lang": "hi"} for t in SCAM]
            + [{"text": t} for t in BENIGN]
            + [{"text": t} for t in AMBIGUOUS])


def _percentile(sorted_ms, pct):
    if not sorted_ms:
        return 0.0
    k = max(0, min(len(sorted_ms) - 1,
                   int(round((pct / 100) * (len(sorted_ms) - 1)))))
    return sorted_ms[k]


def wait_ready(base, timeout=90):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if httpx.get(f"{base}/readyz", timeout=2).status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def run_load(base, n, concurrency):
    client = httpx.Client(timeout=30, limits=httpx.Limits(
        max_connections=concurrency, max_keepalive_connections=concurrency))

    def one(i):
        payload = PAYLOADS[i % len(PAYLOADS)]
        t0 = time.perf_counter()
        try:
            r = client.post(f"{base}/v1/check", json=payload)
            return (time.perf_counter() - t0) * 1000, r.status_code
        except Exception:
            return (time.perf_counter() - t0) * 1000, 0

    # warmup (not measured)
    for i in range(min(20, n)):
        one(i)

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        results = list(pool.map(one, range(n)))
    elapsed = time.perf_counter() - start
    client.close()

    lat = sorted(r[0] for r in results)
    ok = sum(1 for r in results if r[1] == 200)
    return {
        "requests": n,
        "concurrency": concurrency,
        "elapsed_s": round(elapsed, 3),
        "throughput_rps": round(n / elapsed, 1) if elapsed else 0,
        "success_rate": round(100 * ok / n, 2),
        "ok": ok,
        "non_200": n - ok,
        "latency_ms": {
            "min": round(lat[0], 2),
            "p50": round(_percentile(lat, 50), 2),
            "p90": round(_percentile(lat, 90), 2),
            "p95": round(_percentile(lat, 95), 2),
            "p99": round(_percentile(lat, 99), 2),
            "max": round(lat[-1], 2),
            "mean": round(sum(lat) / len(lat), 2),
        },
    }


def render_svg(res, out_path):
    lm = res["latency_ms"]
    bars = [("p50", lm["p50"]), ("p90", lm["p90"]),
            ("p95", lm["p95"]), ("p99", lm["p99"])]
    peak = max(v for _, v in bars) or 1.0
    W, H = 720, 380
    left, top, bar_h, gap, track = 90, 150, 34, 22, 520
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" font-family="Segoe UI,Helvetica,Arial,sans-serif">',
        f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
        f'<text x="40" y="44" font-size="22" font-weight="700" fill="#0f172a">'
        f'DhvaniShield — /v1/check load test</text>',
        f'<text x="40" y="72" font-size="14" fill="#475569">'
        f'{res["requests"]} requests @ concurrency {res["concurrency"]} · '
        f'{res["throughput_rps"]} req/s · {res["success_rate"]}% success '
        f'({res["non_200"]} errors)</text>',
        f'<text x="40" y="116" font-size="13" font-weight="600" fill="#64748b" '
        f'letter-spacing="1">LATENCY PERCENTILES (ms)</text>',
    ]
    for i, (label, val) in enumerate(bars):
        y = top + i * (bar_h + gap)
        w = max(2, val / peak * track)
        shade = ["#38bdf8", "#0ea5e9", "#0284c7", "#dc2626"][i]
        parts += [
            f'<text x="{left - 12}" y="{y + bar_h * 0.68}" font-size="14" '
            f'text-anchor="end" fill="#334155" font-weight="600">{label}</text>',
            f'<rect x="{left}" y="{y}" width="{track}" height="{bar_h}" '
            f'rx="6" fill="#eef2f6"/>',
            f'<rect x="{left}" y="{y}" width="{w:.1f}" height="{bar_h}" '
            f'rx="6" fill="{shade}"/>',
            f'<text x="{left + w + 10:.1f}" y="{y + bar_h * 0.68}" '
            f'font-size="13" fill="#0f172a" font-weight="600">{val} ms</text>',
        ]
    parts.append(
        f'<text x="40" y="{H - 20}" font-size="12" fill="#94a3b8">'
        f'min {lm["min"]} · mean {lm["mean"]} · max {lm["max"]} ms · '
        f'single node, text path</text>')
    parts.append("</svg>")
    Path(out_path).write_text("\n".join(parts), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--requests", type=int, default=2000)
    ap.add_argument("--concurrency", type=int, default=50)
    ap.add_argument("--port", type=int, default=8011)
    ap.add_argument("--url", default=None,
                    help="hit an already-running server instead of spawning one")
    args = ap.parse_args()

    proc = None
    base = args.url or f"http://127.0.0.1:{args.port}"
    try:
        if not args.url:
            env = dict(os.environ, PYTHONUTF8="1",
                       DHVANI_RATE_LIMIT="100000000")  # limiter out of the way
            print(f"starting server on :{args.port} ...")
            proc = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "server:app",
                 "--host", "127.0.0.1", "--port", str(args.port),
                 "--log-level", "warning"],
                cwd=str(ROOT), env=env,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not wait_ready(base):
            print("server did not become ready in time")
            sys.exit(1)
        print(f"server ready — firing {args.requests} requests "
              f"@ concurrency {args.concurrency}\n")

        res = run_load(base, args.requests, args.concurrency)
        (ROOT / "loadtest_results.json").write_text(
            json.dumps(res, indent=2), encoding="utf-8")
        render_svg(res, ROOT / "loadtest.svg")

        lm = res["latency_ms"]
        print("=== DhvaniShield load test ===")
        print(f"requests        {res['requests']} @ concurrency {res['concurrency']}")
        print(f"throughput      {res['throughput_rps']} req/s "
              f"({res['elapsed_s']} s total)")
        print(f"success rate    {res['success_rate']}%  "
              f"({res['non_200']} non-200)")
        print(f"latency ms      p50 {lm['p50']} | p90 {lm['p90']} | "
              f"p95 {lm['p95']} | p99 {lm['p99']} | max {lm['max']}")
        print("\nwrote loadtest_results.json and loadtest.svg")
        ok = res["success_rate"] >= 99.0
        print("RESULT:", "LOAD TEST PASS" if ok else "DEGRADED (<99% success)")
        sys.exit(0 if ok else 1)
    finally:
        if proc:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except Exception:
                proc.kill()


if __name__ == "__main__":
    main()
