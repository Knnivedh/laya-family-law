"""Pre-push / CI gate runner for LAYA v7.1 (V71-P7-4, 10x plan §7.4).

Runs the frozen gates and reports each as pass / fail / blocked — never a
silent pass. A gate that cannot run here (no torch, no student ONNX artifact,
Lane 02's leakage script not yet landed) is BLOCKED, not passed, and the
overall exit code is 2 unless --allow-blocked is given (local CPU triage
only; CI must run without it).

Gates
-----
frozen_sha            python -m tests.test_graph_v4
                      (7/7 frozen SHA-256 intact, 0 dangling edges, v4 counts)
unit                  python -m unittest discover -s tests -p "test_*.py" -v
                      (incl. test_v7_rules batch-permutation invariance and
                      test_laya_family maintenance tests; needs torch)
prose                 python -m tests.test_prose_renderer_v2
                      (EN + KN templates, adversarial mutants, Fp=0)
leakage               python -m scripts.check_ngram_leakage --strict
                      (Lane 02's script; 0 8-gram overlap vs all test banks)
license               Default runtime model config contains zero CC-BY-NC
                      model IDs (blocks facebook/nllb-200-distilled-600M).
latency-determinism   CPU latency + determinism (G14-CPU + G15): deterministic
                      16-Q smoke via student_int8.onnx on CI CPU
                      (mean < 0.5s/Q, max <= 1.0s/Q, Run 1 == Run 2
                      byte-identical outcome SHA-256).

CPU-runnable here (no torch, no GPU): frozen_sha, prose, license.
Blocked here: unit (torch missing), leakage (Lane 02 script not landed),
latency-determinism (no student_int8.onnx, no torch/onnxruntime).

Usage (repo root):
  python scripts/ci_gate.py --all
  python scripts/ci_gate.py --gate frozen_sha --gate prose --gate license
  python scripts/ci_gate.py --all --allow-blocked --json-out results/ci-gate-local.json

Exact RTX / CI commands for the blocked gates:
  python -m unittest discover -s tests -p "test_*.py" -v
  python -m scripts.check_ngram_leakage --strict
  python -m tests.v7_backtest --suite 16q --mode student_onnx --device cpu --misses 0   # x2, compare outcome SHA
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent

# CC-BY-NC model IDs that must never appear in the DEFAULT runtime config.
# (Lane 06 retires NLLB-200; until then this gate correctly FAILS.)
CC_BY_NC_MODEL_IDS: tuple[str, ...] = (
    "facebook/nllb-200-distilled-600M",
    "facebook/nllb-200-distilled-1.3B",
    "facebook/nllb-200-3.3B",
    "facebook/nllb-200",
)
LICENSE_SCAN_FILES: tuple[str, ...] = (
    "src/laya_v7_extractor.py",
    "src/laya_v7_student.py",  # Lane 08; absent until then (noted, not failed).
)
STUDENT_ONNX_PATH = REPO_ROOT / "models" / "student_int8.onnx"

ALL_GATES: tuple[str, ...] = (
    "frozen_sha",
    "unit",
    "prose",
    "leakage",
    "license",
    "latency-determinism",
)


def _run(cmd: list[str], *, timeout: int = 1200) -> tuple[int, str]:
    proc = subprocess.run(
        cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=timeout
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def _gate(name: str, status: str, detail: str, command: str = "") -> dict[str, Any]:
    return {"gate": name, "status": status, "detail": detail, "command": command}


def gate_frozen_sha() -> dict[str, Any]:
    cmd = [sys.executable, "-m", "tests.test_graph_v4"]
    code, out = _run(cmd)
    tail = "\n".join(out.strip().splitlines()[-3:])
    if code == 0:
        return _gate("frozen_sha", "pass", tail, " ".join(cmd))
    return _gate("frozen_sha", "fail", tail or f"exit {code}", " ".join(cmd))


def gate_unit() -> dict[str, Any]:
    cmd = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"]
    code, out = _run(cmd)
    tail = "\n".join(out.strip().splitlines()[-5:])
    if code == 0:
        return _gate("unit", "pass", tail, " ".join(cmd))
    if "No module named 'torch'" in out or "ModuleNotFoundError: No module named 'torch'" in out:
        return _gate(
            "unit", "blocked",
            "torch is not installed on this VM; unit tests needing torch "
            "(test_v7_rules, test_laya_family) cannot run here. "
            "Run on the RTX machine / CI with torch. " + tail,
            " ".join(cmd),
        )
    return _gate("unit", "fail", tail or f"exit {code}", " ".join(cmd))


def gate_prose() -> dict[str, Any]:
    cmd = [sys.executable, "-m", "tests.test_prose_renderer_v2"]
    code, out = _run(cmd)
    tail = "\n".join(out.strip().splitlines()[-3:])
    if code == 0:
        return _gate("prose", "pass", tail, " ".join(cmd))
    return _gate("prose", "fail", tail or f"exit {code}", " ".join(cmd))


def gate_leakage() -> dict[str, Any]:
    script = REPO_ROOT / "scripts" / "check_ngram_leakage.py"
    cmd = [sys.executable, "-m", "scripts.check_ngram_leakage", "--strict"]
    if not script.exists():
        return _gate(
            "leakage", "blocked",
            "scripts/check_ngram_leakage.py not present (Lane 02, V71-P1-2, "
            "not yet landed). Cannot verify 0 8-gram overlap; gate is "
            "BLOCKED, not passed.",
            " ".join(cmd),
        )
    code, out = _run(cmd)
    tail = "\n".join(out.strip().splitlines()[-5:])
    if code == 0:
        return _gate("leakage", "pass", tail, " ".join(cmd))
    return _gate("leakage", "fail", tail or f"exit {code}", " ".join(cmd))


def _strip_comments(line: str) -> str:
    # Remove a trailing # comment (naive but sufficient for model-ID scans;
    # blocklisted IDs never legitimately appear inside a string literal
    # containing '#').
    if "#" in line:
        line = line.split("#", 1)[0]
    return line


def gate_license() -> dict[str, Any]:
    """Zero CC-BY-NC model IDs in the default runtime model config."""
    hits: list[str] = []
    scanned: list[str] = []
    missing: list[str] = []
    for rel in LICENSE_SCAN_FILES:
        path = REPO_ROOT / rel
        if not path.exists():
            missing.append(rel)
            continue
        scanned.append(rel)
        for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            code_line = _strip_comments(raw)
            # Keep only maximal matches per line: "facebook/nllb-200" is a
            # substring of "facebook/nllb-200-distilled-600M" and must not
            # double-count the same occurrence.
            line_hits = [m for m in CC_BY_NC_MODEL_IDS if m in code_line]
            line_hits = [m for m in line_hits
                         if not any(m != other and m in other for other in line_hits)]
            for model_id in line_hits:
                hits.append(f"{rel}:{lineno}: {model_id}")
    detail = f"scanned={scanned or ['(none)']} missing={missing} hits={hits or ['none']}"
    if hits:
        return _gate(
            "license", "fail",
            "CC-BY-NC model ID(s) in default runtime config: " + "; ".join(hits)
            + ". Retire from the default path (Lane 06, V71-P3-1) before this gate can pass. "
            + detail,
            "python scripts/ci_gate.py --gate license",
        )
    return _gate("license", "pass", detail, "python scripts/ci_gate.py --gate license")


def _extract_16q_json(stdout: str) -> dict[str, Any] | None:
    """Extract the printed 16-Q JSON block from v7_backtest stdout."""
    start = stdout.find('{\n  "n":')
    if start < 0:
        return None
    try:
        return json.loads(stdout[start:])
    except json.JSONDecodeError:
        return None


def gate_latency_determinism() -> dict[str, Any]:
    """G14-CPU + G15: student_int8.onnx 16-Q smoke, mean < 0.5s/Q, max <= 1.0s/Q,
    Run 1 == Run 2 byte-identical outcome SHA-256 (latency/wall excluded)."""
    cmd_str = (
        "python -m tests.v7_backtest --suite 16q --mode student_onnx --device cpu --misses 0"
    )
    if not STUDENT_ONNX_PATH.exists():
        return _gate(
            "latency-determinism", "blocked",
            "models/student_int8.onnx absent (Lane 08, V71-P5-2, not yet "
            "landed). No CPU latency / determinism measurement is possible "
            "here. Run on RTX/CI once the artifact exists: " + cmd_str + " (x2).",
            cmd_str,
        )
    try:
        import onnxruntime  # noqa: F401
    except Exception:
        return _gate(
            "latency-determinism", "blocked",
            "onnxruntime is not installed on this VM. Install it on the "
            "RTX/CI runner and re-run: " + cmd_str + " (x2).",
            cmd_str,
        )
    cmd = [sys.executable, "-m", "tests.v7_backtest", "--suite", "16q",
           "--mode", "student_onnx", "--device", "cpu", "--misses", "0"]
    results: list[dict[str, Any]] = []
    for run_no in (1, 2):
        code, out = _run(cmd, timeout=1800)
        if code != 0:
            if "invalid choice" in out and "student_onnx" in out:
                return _gate(
                    "latency-determinism", "blocked",
                    "tests/v7_backtest.py has no student_onnx mode yet "
                    "(Lane 08). Artifact exists but the runner cannot use it.",
                    cmd_str,
                )
            tail = "\n".join(out.strip().splitlines()[-5:])
            return _gate("latency-determinism", "fail", f"run {run_no} exit {code}: {tail}", cmd_str)
        parsed = _extract_16q_json(out)
        if parsed is None:
            return _gate("latency-determinism", "fail", f"run {run_no}: could not parse 16-Q JSON.", cmd_str)
        results.append(parsed)
    mean_s = float(results[0]["latency_mean_s"])
    max_s = float(results[0]["latency_max_s"])
    normalised = []
    for res in results:
        slim = {k: v for k, v in res.items()
                if k not in {"latency_mean_s", "latency_max_s", "total_wall_s"}}
        normalised.append(hashlib.sha256(json.dumps(slim, sort_keys=True).encode()).hexdigest())
    deterministic = normalised[0] == normalised[1]
    detail = (f"mean={mean_s}s/Q max={max_s}s/Q "
              f"outcome_sha_run1={normalised[0][:12]} run2={normalised[1][:12]} "
              f"deterministic={deterministic}")
    if mean_s < 0.5 and max_s <= 1.0 and deterministic:
        return _gate("latency-determinism", "pass", detail, cmd_str)
    return _gate(
        "latency-determinism", "fail",
        detail + " (need mean < 0.5s/Q, max <= 1.0s/Q, Run 1 == Run 2).",
        cmd_str,
    )


GATE_FUNCS = {
    "frozen_sha": gate_frozen_sha,
    "unit": gate_unit,
    "prose": gate_prose,
    "leakage": gate_leakage,
    "license": gate_license,
    "latency-determinism": gate_latency_determinism,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="LAYA v7.1 CI gate runner (V71-P7-4).")
    parser.add_argument("--gate", action="append", default=[], choices=ALL_GATES,
                        help="Run one gate (repeatable). Default with no --gate is --all.")
    parser.add_argument("--all", action="store_true", help="Run every gate.")
    parser.add_argument("--allow-blocked", action="store_true",
                        help="Local CPU triage only: exit 0 despite blocked gates. Never use in CI.")
    parser.add_argument("--json-out", default=None, help="Write the gate summary JSON here.")
    args = parser.parse_args(argv)

    names = list(args.gate) or (list(ALL_GATES) if (args.all or not args.gate) else [])
    results = [GATE_FUNCS[name]() for name in names]
    summary = {"gates": results}
    for res in results:
        print(f"[{res['status'].upper():7}] {res['gate']}: {res['detail']}")
    n_pass = sum(1 for r in results if r["status"] == "pass")
    n_fail = sum(1 for r in results if r["status"] == "fail")
    n_blocked = sum(1 for r in results if r["status"] == "blocked")
    print(f"SUMMARY: {n_pass} pass / {n_fail} fail / {n_blocked} blocked (of {len(results)})")
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"Wrote {args.json_out}")
    if n_fail:
        return 1
    if n_blocked and not args.allow_blocked:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
