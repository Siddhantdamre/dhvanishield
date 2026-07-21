"""One-command verification — the single entry point CI and reviewers use.

Runs every suite, captures exit codes, prints a summary, and fails if any
gate suite fails. This is the 'does the whole thing still hold?' button.

  python tests/run_all.py          # correctness + hardening gate (fast, no network)
  python tests/run_all.py --load   # also run the load/latency benchmark
"""
import io
import subprocess
import sys
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]

# (label, argv, is_gate). Gate suites must exit 0 or the run fails.
GATE = [
    ("correctness (registry + trajectory + earliness)", ["tests/eval.py"], True),
    ("train/validate/test (in-distribution)",           ["tests/eval_ml.py"], True),
    ("out-of-distribution (generalisation gap)",        ["tests/eval_ood.py"], True),
    ("real-world message expert (held-out real data)",  ["tests/eval_message.py"], True),
    ("calibration + selective prediction (defer-to-human)", ["tests/eval_calibration.py"], True),
    ("red-team stress test (evasion + novel families)", ["tests/eval_redteam.py"], True),
    ("interaction policy (silence-until-confident)",     ["tests/eval_policy.py"], True),
    ("feedback loop (consent + redaction + flywheel)",   ["tests/eval_feedback.py"], True),
    ("duty-of-care warning receipt (compliance proof)",  ["tests/eval_receipt.py"], True),
    ("scam categoriser (right advice per scenario)",     ["tests/eval_categories.py"], True),
    ("misinformation-rhetoric detector (2nd domain)",    ["tests/eval_misinfo.py"], True),
    ("manipulation-strategy generalization (research)",  ["tests/eval_generalization.py"], True),
    ("human->AI manipulation transfer (research)",       ["tests/eval_ai_manipulation.py"], True),
    ("manipulation engine on REAL data (honest number)", ["tests/eval_manip_real.py"], True),
    ("few-shot concept extension (adaptive learning)",   ["tests/eval_fewshot.py"], True),
    ("accessibility profiles (per-disability alerts)",   ["tests/eval_accessibility.py"], True),
    ("output reliability (determinism/consistency/etc.)", ["tests/eval_reliability.py"], True),
    ("multilingual coverage (no language barrier)",      ["tests/eval_multilingual.py"], True),
    ("accessibility contract",                          ["tests/eval_access.py"], True),
    ("speech-input wiring",                             ["tests/eval_speech.py"], True),
    ("deployment API contract",                         ["tests/eval_server.py"], True),
    ("security hardening (auth/limit/caps/metrics)",    ["tests/eval_hardening.py"], True),
]
LOAD = ("load & latency benchmark",
        ["tests/loadtest.py", "--requests", "800", "--concurrency", "30"], False)


def run(label, argv):
    env = {"PYTHONUTF8": "1"}
    import os
    env = dict(os.environ, **env)
    t0 = time.perf_counter()
    p = subprocess.run([sys.executable, *argv], cwd=str(ROOT), env=env,
                       capture_output=True, text=True, encoding="utf-8")
    dt = time.perf_counter() - t0
    return p.returncode, dt, p.stdout, p.stderr


def main():
    suites = list(GATE)
    if "--load" in sys.argv:
        suites.append(LOAD)

    print("DhvaniShield — full verification\n" + "=" * 60)
    results = []
    for label, argv, is_gate in suites:
        code, dt, out, err = run(label, argv)
        ok = code == 0
        results.append((label, ok, dt, is_gate, out, err))
        print(f"[{'PASS' if ok else 'FAIL'}] {label:52} {dt:5.1f}s")

    failed_gates = [r for r in results if r[3] and not r[1]]
    print("=" * 60)
    print(f"{sum(1 for r in results if r[1])}/{len(results)} suites passed"
          f"  ({len(failed_gates)} gate failures)")

    if failed_gates:
        print("\n--- output from failed gate suites ---")
        for label, ok, dt, is_gate, out, err in failed_gates:
            print(f"\n### {label}\n{out[-1500:]}\n{err[-800:]}")

    sys.exit(1 if failed_gates else 0)


if __name__ == "__main__":
    main()
