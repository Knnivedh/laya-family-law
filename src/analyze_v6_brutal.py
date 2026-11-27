"""Diagnostic analyzer for live-laya-colab-results-v6-brutal JSON outputs.

Reports per-category accuracy, custody vocabulary mismatch separation,
per-section TP/FP/FN, language split, and latency without printing any sealed text.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
import statistics


REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO_ROOT / "results"
BANK_PATH = REPO_ROOT / "test-bank" / "brutal-bank-v1-frozen.json"
V5_REF_PATH = RESULTS_DIR / "live-laya-colab-results-v5.json"

CUSTODY_VOCAB_EXTRA = {"hmga-1956-s6", "welfare-principle"}


def _f1(p: float, r: float) -> float:
    return round(2 * p * r / (p + r), 4) if (p + r) > 0 else 0.0


def main() -> None:
    final = json.loads((RESULTS_DIR / "live-laya-colab-results-v6-brutal-final.json").read_text(encoding="utf-8"))
    reg = json.loads((RESULTS_DIR / "live-laya-colab-results-v6-brutal-regression.json").read_text(encoding="utf-8"))
    bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))
    bank_by_id = {q["id"]: q for q in bank["questions"]}
    raw_by_id = {r["id"]: r for r in final["raw_live_runs_brutal"]}
    rows = final["per_question_brutal"]

    if V5_REF_PATH.exists():
        v5 = {r["id"]: r for r in json.loads(V5_REF_PATH.read_text(encoding="utf-8"))["raw_live_runs"]}
        diffs = [
            abs(float(run["stage1_raw"][k]) - float(v5[run["id"]]["stage1_raw"][k]))
            for run in reg["raw_live_runs"]
            for k in (v5[run["id"]].get("stage1_raw") or {})
            if k in (run.get("stage1_raw") or {}) and run["stage1_raw"][k] is not None and v5[run["id"]]["stage1_raw"][k] is not None
        ]
        print(f"Parity vs v5 CPU ({len(diffs)} prompts): mean_abs_diff={sum(diffs)/len(diffs):.6f}, max_abs_diff={max(diffs):.6f}")

    agg = final["brutal_230"]
    print(f"Brutal-230: exact={agg['exact']} uP/R/F1={agg['micro_precision']}/{agg['micro_recall']}/{agg['micro_f1']} court={agg['court_correct']} esc_bool={agg['escalates_bool_correct']} silent={agg['silent_count']} Fb={agg['forbidden_before_recheck_total']} rating={final['brutal_rating_capped_9.0']}")

    by_cat: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_cat[bank_by_id[r["id"]]["category"]].append(r)
    for cat in sorted(by_cat, key=lambda c: int(c[1:])):
        crows = by_cat[cat]
        tp = sum(r["tp"] for r in crows); fp = sum(r["fp"] for r in crows); fn = sum(r["fn"] for r in crows)
        up = tp / (tp + fp) if (tp + fp) else 0.0
        ur = tp / (tp + fn) if (tp + fn) else 0.0
        print(f"  {cat:4s}: exact={sum(1 for r in crows if r['exact']):2d}/{len(crows):<2d} uF1={_f1(up, ur):.3f} court={sum(1 for r in crows if r['court_correct']):2d}/{len(crows):<2d} silent={sum(1 for r in crows if r['silent']):2d}")

    tp_nv = fp_nv = fn_nv = ex_nv = 0
    for r in rows:
        q = bank_by_id[r["id"]]
        pred_nv = set(raw_by_id[r["id"]]["kept_ids"]) - CUSTODY_VOCAB_EXTRA
        gt = set(q["gt_sections"])
        if pred_nv == gt:
            ex_nv += 1
        tp_nv += len(pred_nv & gt); fp_nv += len(pred_nv - gt); fn_nv += len(gt - pred_nv)
    up_nv = tp_nv / (tp_nv + fp_nv); ur_nv = tp_nv / (tp_nv + fn_nv)
    print(f"Excluding custody vocab extras: exact={ex_nv}/230 uF1={_f1(up_nv, ur_nv):.4f}")

    lats = [r["latency_s"] for r in final["raw_live_runs_brutal"] if r.get("latency_s") is not None]
    print(f"Latency: total={sum(lats):.2f}s mean={statistics.mean(lats):.3f}s median={statistics.median(lats):.3f}s max={max(lats):.3f}s")


if __name__ == "__main__":
    main()
