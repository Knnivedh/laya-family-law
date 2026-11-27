"""Confidence calibration for LAYA v7.1 (V71-P7-3, 10x plan §7.3).

Per-head temperature scaling (+ isotonic-regression sanity check), fit
STRICTLY on a held-out clean synthetic/dev calibration split (n >= 500,
zero overlap with 16-Q / Brutal-230 / Sealed Fresh-20 / Sealed Kannada-8).
Calibration is never fit on any test bank.

Gates (logged per eval run):
  * ECE (Expected Calibration Error)            <= 0.03
  * Brier score (multi-class)                   <= 0.04
  * Risk-coverage AURC                          <= 0.02
  * Precision on auto-accepted predictions
    (confidence >= tau_high)                    >= 0.99
  * Predictions with confidence in [tau_low, tau_high) are routed ONLY to
    targeted clarifying questions (V71-P2-4), never auto-accepted.

Implementation notes
--------------------
* Pure-Python core (``math`` only): temperature fitting is a 1-D search
  (coarse log-grid + golden-section refinement of the NLL), isotonic
  regression is PAVA, and ECE / Brier / risk-coverage are direct formulas.
  The module imports and runs on CPU with NO torch installed.
* ``torch`` is imported lazily and guarded (``torch is None`` when absent).
  :func:`fit_temperature_torch` is a thin parity wrapper for the RTX run; it
  raises a clear error here instead of silently pretending to fit.
* This file is CODE ONLY. No fitting is done here: there is no GPU/torch on
  this VM and no calibration split exists yet (Lane 02 owns the corpus,
  Lane 03 owns the classifier). ``--self-test`` runs a deterministic
  synthetic smoke check only, labelled as such — it is not a result.

Exact RTX 5050 run commands (run from the repo root on the RTX machine,
after Lane 02's calibration split exists at data/synthetic_v7_1/calibration.jsonl
with records {"head": str, "logits": [float, ...], "label": int}):
  # 1. Fit per-head temperatures on the held-out calibration split:
  python -m src.laya_calibration --calibration-file data/synthetic_v7_1/calibration.jsonl \\
      --out results/calibration-v71.json
  # 2. Evaluate the fitted temperatures on a FRESH dev slice (never the fit split):
  python -m src.laya_calibration --calibration-file data/synthetic_v7_1/dev.jsonl \\
      --temperatures results/calibration-v71.json --report-only
  # 3. Torch parity check (same data, torch optimiser; must match within 1e-3):
  python -m src.laya_calibration --calibration-file data/synthetic_v7_1/calibration.jsonl \\
      --torch --out results/calibration-v71-torch.json
  # 4. Re-run the backtest with calibrated confidences and check the gates:
  python -m tests.v7_backtest --suite all_with_sealed --mode laya --device cuda --misses 0
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path
from typing import Any

try:  # Guarded: torch is NOT installed on the CPU-only dev VM.
    import torch  # type: ignore
except Exception:  # pragma: no cover - import guard
    torch = None  # type: ignore[assignment]

# Frozen calibration gates (10x plan §7.3).
ECE_MAX = 0.03
BRIER_MAX = 0.04
AURC_MAX = 0.02
AUTO_ACCEPT_PRECISION_MIN = 0.99
CALIBRATION_SPLIT_MIN_N = 500


# ---------------------------------------------------------------------------
# Core numerics (pure Python, no torch / numpy)
# ---------------------------------------------------------------------------

def _softmax(logits: list[float]) -> list[float]:
    m = max(logits)
    exps = [math.exp(x - m) for x in logits]
    total = sum(exps)
    return [e / total for e in exps]


def _log_softmax(logits: list[float]) -> list[float]:
    m = max(logits)
    denom = math.log(sum(math.exp(x - m) for x in logits)) + m
    return [x - denom for x in logits]


def nll_for_temperature(
    logits_list: list[list[float]], labels: list[int], temperature: float
) -> float:
    """Mean negative log-likelihood of the labels under temperature scaling."""
    if temperature <= 0:
        raise ValueError("temperature must be > 0")
    total = 0.0
    for logits, label in zip(logits_list, labels):
        scaled = [x / temperature for x in logits]
        total -= _log_softmax(scaled)[label]
    return total / max(len(labels), 1)


def fit_temperature(
    logits_list: list[list[float]],
    labels: list[int],
    *,
    t_min: float = 0.05,
    t_max: float = 10.0,
    grid_points: int = 60,
) -> dict[str, Any]:
    """Fit a single scalar temperature T minimising NLL (grid + golden section).

    Returns {"temperature", "nll_before", "nll_after"}. T == 1.0 means the
    head was already calibrated; T > 1 softens overconfident logits.
    """
    if not logits_list or len(logits_list) != len(labels):
        raise ValueError("logits_list and labels must be non-empty and aligned")
    nll_before = nll_for_temperature(logits_list, labels, 1.0)
    # Coarse search on a log grid, then golden-section refinement.
    best_t, best_nll = 1.0, nll_before
    lo_log, hi_log = math.log(t_min), math.log(t_max)
    for i in range(grid_points + 1):
        t = math.exp(lo_log + (hi_log - lo_log) * i / grid_points)
        nll = nll_for_temperature(logits_list, labels, t)
        if nll < best_nll:
            best_t, best_nll = t, nll
    # Golden-section around the grid best (+/- one grid step in log space).
    step = (hi_log - lo_log) / grid_points
    a = max(lo_log, math.log(best_t) - step)
    b = min(hi_log, math.log(best_t) + step)
    inv_phi = (math.sqrt(5.0) - 1.0) / 2.0
    c = b - inv_phi * (b - a)
    d = a + inv_phi * (b - a)
    fc = nll_for_temperature(logits_list, labels, math.exp(c))
    fd = nll_for_temperature(logits_list, labels, math.exp(d))
    for _ in range(60):
        if abs(b - a) < 1e-6:
            break
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - inv_phi * (b - a)
            fc = nll_for_temperature(logits_list, labels, math.exp(c))
        else:
            a, c, fc = c, d, fd
            d = a + inv_phi * (b - a)
            fd = nll_for_temperature(logits_list, labels, math.exp(d))
    t_refined = math.exp((a + b) / 2.0)
    nll_refined = nll_for_temperature(logits_list, labels, t_refined)
    if nll_refined < best_nll:
        best_t, best_nll = t_refined, nll_refined
    return {
        "temperature": round(float(best_t), 4),
        "nll_before": round(float(nll_before), 4),
        "nll_after": round(float(best_nll), 4),
    }


def fit_temperature_per_head(
    records_by_head: dict[str, dict[str, list[Any]]],
) -> dict[str, dict[str, Any]]:
    """Fit one temperature per head. Input: {head: {"logits": [...], "labels": [...]}}."""
    out: dict[str, dict[str, Any]] = {}
    for head, data in sorted(records_by_head.items()):
        logits_list = [list(map(float, row)) for row in data["logits"]]
        labels = [int(y) for y in data["labels"]]
        result = fit_temperature(logits_list, labels)
        result["n"] = len(labels)
        out[head] = result
    return out


def apply_temperature(logits: list[float], temperature: float) -> list[float]:
    """Calibrated probabilities for one prediction."""
    if temperature <= 0:
        raise ValueError("temperature must be > 0")
    return _softmax([x / temperature for x in logits])


# ---------------------------------------------------------------------------
# Isotonic regression (PAVA) — sanity check against temperature scaling
# ---------------------------------------------------------------------------

def fit_isotonic(confidences: list[float], correct: list[int]) -> dict[str, Any]:
    """Pool-Adjacent-Violators isotonic fit of P(correct | confidence).

    Returns {"bin_edges": [...], "bin_values": [...]} — a stepwise mapping
    from raw confidence to calibrated probability. If the isotonic curve
    disagrees with the temperature-scaled curve by more than ~0.05 in any
    populated bin, the temperature fit must be investigated, not shipped.
    """
    if len(confidences) != len(correct) or not confidences:
        raise ValueError("confidences and correct must be non-empty and aligned")
    order = sorted(range(len(confidences)), key=lambda i: confidences[i])
    xs = [confidences[i] for i in order]
    ys = [float(correct[i]) for i in order]
    # PAVA blocks: [sum_y, count, x_min, x_max]
    blocks: list[list[float]] = []
    for x, y in zip(xs, ys):
        blocks.append([y, 1.0, x, x])
        while len(blocks) >= 2 and (blocks[-2][0] / blocks[-2][1]) > (blocks[-1][0] / blocks[-1][1]):
            b2 = blocks.pop()
            b1 = blocks.pop()
            blocks.append([b1[0] + b2[0], b1[1] + b2[1], b1[2], b2[3]])
    edges = [b[2] for b in blocks] + [blocks[-1][3]]
    values = [b[0] / b[1] for b in blocks]
    return {"bin_edges": [round(e, 4) for e in edges], "bin_values": [round(v, 4) for v in values]}


def isotonic_predict(mapping: dict[str, Any], confidence: float) -> float:
    edges, values = mapping["bin_edges"], mapping["bin_values"]
    for i, edge in enumerate(edges[1:], start=0):
        if confidence <= edge:
            return float(values[i])
    return float(values[-1])


# ---------------------------------------------------------------------------
# Metrics: ECE, Brier, risk-coverage / AURC, auto-accept precision
# ---------------------------------------------------------------------------

def compute_ece(
    probs_list: list[list[float]], labels: list[int], n_bins: int = 15
) -> dict[str, Any]:
    """Expected Calibration Error on the predicted class (confidence = max prob)."""
    if not probs_list or len(probs_list) != len(labels):
        raise ValueError("probs_list and labels must be non-empty and aligned")
    bins: list[dict[str, Any]] = [
        {"count": 0, "conf_sum": 0.0, "correct": 0} for _ in range(n_bins)
    ]
    for probs, label in zip(probs_list, labels):
        conf = max(probs)
        pred = probs.index(conf)
        b = min(n_bins - 1, int(conf * n_bins))
        bins[b]["count"] += 1
        bins[b]["conf_sum"] += conf
        bins[b]["correct"] += 1 if pred == label else 0
    ece = 0.0
    n = len(labels)
    for b in bins:
        if b["count"]:
            ece += (b["count"] / n) * abs(b["conf_sum"] / b["count"] - b["correct"] / b["count"])
    return {
        "ece": round(float(ece), 4),
        "n_bins": n_bins,
        "n": n,
        "gate_ece_max": ECE_MAX,
        "pass": bool(ece <= ECE_MAX),
    }


def compute_brier(probs_list: list[list[float]], labels: list[int]) -> dict[str, Any]:
    """Multi-class Brier score: mean over items of sum_c (p_c - onehot_c)^2."""
    if not probs_list or len(probs_list) != len(labels):
        raise ValueError("probs_list and labels must be non-empty and aligned")
    total = 0.0
    for probs, label in zip(probs_list, labels):
        total += sum((p - (1.0 if c == label else 0.0)) ** 2 for c, p in enumerate(probs))
    brier = total / len(labels)
    return {
        "brier": round(float(brier), 4),
        "n": len(labels),
        "gate_brier_max": BRIER_MAX,
        "pass": bool(brier <= BRIER_MAX),
    }


def compute_risk_coverage(
    confidences: list[float],
    correct: list[int],
    *,
    tau_low: float = 0.5,
    tau_high: float = 0.9,
) -> dict[str, Any]:
    """Selective-prediction curve: risk vs coverage + AURC + auto-accept precision.

    Coverage sweeps thresholds from high to low confidence; risk at a
    coverage is the error rate among accepted predictions. AURC is the
    trapezoidal area under the risk-coverage curve (lower is better).
    Auto-accepted = confidence >= tau_high; gray band [tau_low, tau_high)
    must go to clarification (V71-P2-4), never to auto-accept.
    """
    if len(confidences) != len(correct) or not confidences:
        raise ValueError("confidences and correct must be non-empty and aligned")
    order = sorted(range(len(confidences)), key=lambda i: -confidences[i])
    n = len(confidences)
    curve: list[dict[str, float]] = []
    errors = 0
    for k, idx in enumerate(order, start=1):
        errors += 0 if correct[idx] else 1
        curve.append({"coverage": round(k / n, 4), "risk": round(errors / k, 4)})
    aurc = 0.0
    prev_cov, prev_risk = 0.0, 0.0
    for point in curve:
        aurc += (point["coverage"] - prev_cov) * (point["risk"] + prev_risk) / 2.0
        prev_cov, prev_risk = point["coverage"], point["risk"]
    accepted = [i for i, c in enumerate(confidences) if c >= tau_high]
    gray = [i for i, c in enumerate(confidences) if tau_low <= c < tau_high]
    auto_prec = (
        sum(correct[i] for i in accepted) / len(accepted) if accepted else 0.0
    )
    return {
        "aurc": round(float(aurc), 4),
        "gate_aurc_max": AURC_MAX,
        "aurc_pass": bool(aurc <= AURC_MAX),
        "tau_low": tau_low,
        "tau_high": tau_high,
        "auto_accepted_n": len(accepted),
        "auto_accept_precision": round(float(auto_prec), 4),
        "gate_auto_precision_min": AUTO_ACCEPT_PRECISION_MIN,
        "auto_precision_pass": bool(auto_prec >= AUTO_ACCEPT_PRECISION_MIN),
        "gray_band_n": len(gray),
        "risk_coverage_curve": curve,
    }


def evaluate_calibration(
    probs_list: list[list[float]],
    labels: list[int],
    *,
    tau_low: float = 0.5,
    tau_high: float = 0.9,
) -> dict[str, Any]:
    """All §7.3 gates in one call. Returns metrics + per-gate pass flags."""
    ece = compute_ece(probs_list, labels)
    brier = compute_brier(probs_list, labels)
    confidences = [max(p) for p in probs_list]
    correct = [1 if probs.index(max(probs)) == y else 0 for probs, y in zip(probs_list, labels)]
    rc = compute_risk_coverage(confidences, correct, tau_low=tau_low, tau_high=tau_high)
    passes = {
        "ece": ece["pass"],
        "brier": brier["pass"],
        "aurc": rc["aurc_pass"],
        "auto_accept_precision": rc["auto_precision_pass"],
    }
    return {
        "ece": ece["ece"],
        "brier": brier["brier"],
        "aurc": rc["aurc"],
        "auto_accept_precision": rc["auto_accept_precision"],
        "auto_accepted_n": rc["auto_accepted_n"],
        "gray_band_n": rc["gray_band_n"],
        "gates": passes,
        "all_gates_pass": bool(all(passes.values())),
    }


# ---------------------------------------------------------------------------
# Torch parity wrapper (RTX only; raises clearly without torch)
# ---------------------------------------------------------------------------

def fit_temperature_torch(
    logits_list: list[list[float]], labels: list[int]
) -> dict[str, Any]:
    """Same fit via torch (LBFGS on a scalar log-T). RTX parity check only.

    Raises RuntimeError on this VM (no torch) — never silently fakes a fit.
    Must agree with :func:`fit_temperature` within 1e-3 on the same data.
    """
    if torch is None:
        raise RuntimeError(
            "torch is not installed on this VM. Run fit_temperature_torch on "
            "the RTX 5050 machine (or Colab T4) with torch installed."
        )
    import torch as _torch

    logits_t = _torch.tensor(logits_list, dtype=_torch.float32)
    labels_t = _torch.tensor(labels, dtype=_torch.long)
    log_t = _torch.zeros((), dtype=_torch.float32, requires_grad=True)
    opt = _torch.optim.LBFGS([log_t], lr=0.1, max_iter=100)

    def closure() -> Any:
        opt.zero_grad()
        scaled = logits_t / _torch.exp(log_t)
        loss = _torch.nn.functional.cross_entropy(scaled, labels_t)
        loss.backward()
        return loss

    opt.step(closure)
    temperature = float(_torch.exp(log_t).item())
    return {
        "temperature": round(temperature, 4),
        "nll_before": round(float(nll_for_temperature(logits_list, labels, 1.0)), 4),
        "nll_after": round(float(nll_for_temperature(logits_list, labels, temperature)), 4),
        "backend": "torch-lbfgs",
    }


# ---------------------------------------------------------------------------
# File I/O + CLI
# ---------------------------------------------------------------------------

def load_calibration_file(path: str | Path) -> dict[str, dict[str, list[Any]]]:
    """Load JSONL calibration records {"head", "logits", "label"} grouped by head.

    Enforces the §7.3 split rule at load time: n >= 500 total, and refuses
    files whose records carry a test-bank provenance marker.
    """
    by_head: dict[str, dict[str, list[Any]]] = {}
    total = 0
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        provenance = str(rec.get("provenance", "synthetic_dev"))
        if provenance in {"16q", "brutal-230", "sealed-fresh-20", "sealed-kannada-8", "test-bank"}:
            raise ValueError(
                f"Calibration file {path} contains test-bank provenance "
                f"'{provenance}': calibration must never be fit on a test bank."
            )
        head = str(rec["head"])
        slot = by_head.setdefault(head, {"logits": [], "labels": []})
        slot["logits"].append([float(x) for x in rec["logits"]])
        slot["labels"].append(int(rec["label"]))
        total += 1
    if total < CALIBRATION_SPLIT_MIN_N:
        raise ValueError(
            f"Calibration split has n={total}, below the §7.3 minimum "
            f"n={CALIBRATION_SPLIT_MIN_N}."
        )
    return by_head


def _self_test() -> int:
    """Deterministic synthetic smoke check (NOT a result).

    Generates seeded synthetic logits with known temperature distortion and
    checks the fitter recovers it, ECE/Brier/AURC compute, and the gates
    evaluate. No torch, no data files, no test banks.
    """
    rng = random.Random(0)
    failures: list[str] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        print(f"  {'PASS' if cond else 'FAIL'} {name} {detail}")
        if not cond:
            failures.append(name)

    # Synthetic 3-class head: true probs from a fixed distribution, logits
    # distorted by T_true = 2.0 (overconfident). Fitter should recover ~2.0.
    logits_list: list[list[float]] = []
    labels: list[int] = []
    for _ in range(600):
        true_p = [rng.random() + 0.1 for _ in range(3)]
        s = sum(true_p)
        true_p = [p / s for p in true_p]
        label = rng.choices(range(3), weights=true_p)[0]
        distorted = [2.0 * math.log(p) for p in true_p]
        logits_list.append(distorted)
        labels.append(label)
    fit = fit_temperature(logits_list, labels)
    check("fit_recovers_temperature", 1.5 <= fit["temperature"] <= 2.5, str(fit))
    check("fit_reduces_nll", fit["nll_after"] <= fit["nll_before"], str(fit))
    calibrated = [apply_temperature(row, fit["temperature"]) for row in logits_list]
    ev = evaluate_calibration(calibrated, labels)
    check("metrics_compute", all(k in ev for k in ("ece", "brier", "aurc", "auto_accept_precision")), str(ev))
    check("brier_sane", 0.0 <= ev["brier"] <= 1.0, str(ev["brier"]))
    # Isotonic sanity check runs and is monotone.
    confs = [max(p) for p in calibrated]
    corr = [1 if p.index(max(p)) == y else 0 for p, y in zip(calibrated, labels)]
    iso = fit_isotonic(confs, corr)
    vals = iso["bin_values"]
    check("isotonic_monotone", all(vals[i] <= vals[i + 1] + 1e-9 for i in range(len(vals) - 1)), str(vals))
    # Torch wrapper raises clearly without torch.
    if torch is None:
        try:
            fit_temperature_torch(logits_list[:10], labels[:10])
            check("torch_guard_raises", False, "expected RuntimeError")
        except RuntimeError as exc:
            check("torch_guard_raises", "torch is not installed" in str(exc), str(exc))
    else:
        tf = fit_temperature_torch(logits_list, labels)
        check("torch_parity", abs(tf["temperature"] - fit["temperature"]) <= 0.05, str(tf))
    print(f"SELF-TEST: {'PASS' if not failures else 'FAIL'} ({len(failures)} failures)")
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="LAYA v7.1 per-head temperature calibration (V71-P7-3).")
    parser.add_argument("--calibration-file", default=None,
                        help="JSONL calibration split: {head, logits, label}. n >= 500; never a test bank.")
    parser.add_argument("--temperatures", default=None,
                        help="JSON file of fitted {head: {temperature}} for --report-only evaluation.")
    parser.add_argument("--out", default=None, help="Write fitted temperatures + metrics as JSON.")
    parser.add_argument("--report-only", action="store_true",
                        help="Evaluate (do not fit) using --temperatures on the given file.")
    parser.add_argument("--torch", action="store_true", help="Fit with the torch LBFGS wrapper (RTX only).")
    parser.add_argument("--tau-low", type=float, default=0.5)
    parser.add_argument("--tau-high", type=float, default=0.9)
    parser.add_argument("--self-test", action="store_true",
                        help="Deterministic synthetic smoke check (no torch, no data files).")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()
    if not args.calibration_file:
        parser.error("--calibration-file is required (or use --self-test).")
    by_head = load_calibration_file(args.calibration_file)

    if args.report_only:
        if not args.temperatures:
            parser.error("--report-only requires --temperatures.")
        temps = json.loads(Path(args.temperatures).read_text(encoding="utf-8"))
        report: dict[str, Any] = {}
        for head, data in sorted(by_head.items()):
            temperature = float(temps[head]["temperature"]) if head in temps else 1.0
            probs = [apply_temperature(row, temperature) for row in data["logits"]]
            report[head] = evaluate_calibration(
                probs, [int(y) for y in data["labels"]],
                tau_low=args.tau_low, tau_high=args.tau_high,
            )
            report[head]["temperature"] = temperature
        print(json.dumps(report, indent=2))
        return 0 if all(v["all_gates_pass"] for v in report.values()) else 1

    fitted: dict[str, Any] = {}
    for head, data in sorted(by_head.items()):
        if args.torch:
            result = fit_temperature_torch(data["logits"], [int(y) for y in data["labels"]])
        else:
            result = fit_temperature(data["logits"], [int(y) for y in data["labels"]])
        probs = [apply_temperature(row, result["temperature"]) for row in data["logits"]]
        result["metrics"] = evaluate_calibration(
            probs, [int(y) for y in data["labels"]],
            tau_low=args.tau_low, tau_high=args.tau_high,
        )
        # Isotonic sanity check on the same split (diagnostic, not shipped).
        confs = [max(p) for p in probs]
        corr = [1 if p.index(max(p)) == y else 0 for p, y in zip(probs, data["labels"])]
        result["isotonic_sanity"] = fit_isotonic(confs, corr)
        fitted[head] = result
    print(json.dumps(fitted, indent=2))
    if args.out:
        Path(args.out).write_text(json.dumps(fitted, indent=2), encoding="utf-8")
        print(f"Wrote {args.out}")
    return 0 if all(v["metrics"]["all_gates_pass"] for v in fitted.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
