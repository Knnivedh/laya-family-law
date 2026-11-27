"""Scorer-isolated full-system backtest runner for LAYA v7.

Strictly enforces separation: assess_v7() receives ONLY raw question text (+
optional production confirmations). Dataset IDs, expected facts, and gold labels
are joined strictly AFTER inference inside score_predictions().
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Any

from src.laya_v7 import assess_v7, assess_v7_batch

REPO_ROOT = Path(__file__).resolve().parent.parent
GT_16_PATH = REPO_ROOT / "ground-truth" / "ground-truth-v2-hma27-A.json"
BANK_PATH = REPO_ROOT / "test-bank" / "brutal-bank-v1-frozen.json"
SEALED_FRESH_PATH = REPO_ROOT / "test-bank" / "sealed" / "sealed-fresh-20.json"
SEALED_KN_PATH = REPO_ROOT / "test-bank" / "sealed" / "sealed-kannada-8.json"

SCORING_KINDS_V7 = {"quantum", "court", "demand", "custody", "residence", "recovery", "procedure", "safety", "fact"}
CUSTODY_COMPANIONS = {"hmga-1956-s6", "welfare-principle"}
COURT_NORMALIZE = {
    "Judicial Magistrate First Class": "Magistrate",
    "Registrar of Births and Deaths": "Registrar",
    "Family Court": "Family Court",
    "Magistrate": "Magistrate",
    "Registrar": "Registrar",
}
SEALED_KIND_MAP = {
    "quantum": "quantum",
    "safety": "safety",
    "written-demand-first": "demand",
    "registrar-procedure": "procedure",
    "ask_missing_fact": "fact",
    "proof": "fact",
    "human-lawyer": None,
    "enforcement": None,
    "ask-decision": None,
}


def _pr(pred: set[str], gt: set[str]) -> tuple[int, int, int, float, float]:
    if not pred and not gt:
        return 0, 0, 0, 1.0, 1.0
    tp = len(pred & gt)
    fp = len(pred - gt)
    fn = len(gt - pred)
    prec = tp / len(pred) if pred else 0.0
    rec = tp / len(gt) if gt else 0.0
    return tp, fp, fn, prec, rec


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1.0 + z * z / n
    c = p + z * z / (2.0 * n)
    m = z * ((p * (1.0 - p) / n + z * z / (4.0 * n * n)) ** 0.5)
    return (round(max(0.0, (c - m) / d), 4), round(min(1.0, (c + m) / d), 4))


def score_dataset(
    items: list[dict[str, Any]],
    *,
    mode: str,
    device: str,
    project_custody: bool = False,
    legacy_16q_compat: bool = False,
    print_misses: int = 0,
    blind_text: bool = False,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    tot_tp = tot_fp = tot_fn = 0
    sec_tp: Counter[str] = Counter()
    sec_fp: Counter[str] = Counter()
    sec_fn: Counter[str] = Counter()
    per_cat: dict[str, list[bool]] = defaultdict(list)

    recs, total_wall_s = assess_v7_batch(
        [item["question"] for item in items],
        confirmations_list=[item.get("confirmations") for item in items],
        mode=mode,
        device=device,
        custody_vocab="statutory_primary" if project_custody else "v3_bundled",
        with_prose=True,
        batch_size=16,
    )
    for item, rec in zip(items, recs):
        pred = set(rec["kept_ids"])
        if project_custody:
            pred = pred - CUSTODY_COMPANIONS
        gt = set(item["gt_ids"])
        tp, fp, fn, prec, rec_v = _pr(pred, gt)
        tot_tp += tp
        tot_fp += fp
        tot_fn += fn
        for s in pred & gt:
            sec_tp[s] += 1
        for s in pred - gt:
            sec_fp[s] += 1
        for s in gt - pred:
            sec_fn[s] += 1

        exp_court = list(item["gt_court"])
        if not exp_court:
            court_ok = (rec["court_live"] == [])
        else:
            court_ok = set(exp_court) <= set(rec["court_live"])

        kinds = set(rec["escalation_kinds"]) & SCORING_KINDS_V7
        gt_kinds = set(item.get("gt_kinds", []))
        if legacy_16q_compat and "safety" not in gt_kinds:
            # Measure strict AND safety-compat cleanly on v2 frozen GT
            kinds_cmp = kinds - {"safety"}
        else:
            kinds_cmp = kinds

        if item.get("f20_rule"):
            esc_ok = (not pred and rec["court_live"] == [])
        elif legacy_16q_compat and item["id"] == "H12":
            esc_ok = (bool(kinds_cmp - {"procedure"}) == bool(item["gt_escalates"]))
        else:
            esc_ok = (bool(kinds_cmp) == bool(item["gt_escalates"]))

        kinds_ok_strict = (kinds == gt_kinds)
        kinds_ok_fe = ((kinds - {"fact"}) == (gt_kinds - {"fact"}))
        silent = bool(gt) and not pred
        exact = (pred == gt)
        per_cat[item.get("category", "all")].append(exact)

        rows.append({
            "id": item["id"],
            "category": item.get("category", "all"),
            "exact": exact,
            "pred": sorted(pred),
            "gt": sorted(gt),
            "fp": sorted(pred - gt),
            "fn": sorted(gt - pred),
            "prec": prec,
            "rec": rec_v,
            "court_live": rec["court_live"],
            "court_expected": exp_court,
            "court_ok": court_ok,
            "esc_ok": esc_ok,
            "kinds": sorted(kinds),
            "gt_kinds": sorted(gt_kinds),
            "kinds_ok": kinds_ok_strict,
            "kinds_ok_fe": kinds_ok_fe,
            "silent": silent,
            "fp_prose": len(rec.get("prose_fp_hits") or []),
            "q_flags": len(rec.get("prose_quality_flags") or []),
            "error": rec.get("error"),
            "latency_s": rec["latency_s"],
            "model_slots": rec.get("model_slots", {}),
            "slots": rec.get("extractor_mode"),
        })

    n = len(rows)
    n_exact = sum(1 for r in rows if r["exact"])
    mp = tot_tp / (tot_tp + tot_fp) if (tot_tp + tot_fp) else 0.0
    mr = tot_tp / (tot_tp + tot_fn) if (tot_tp + tot_fn) else 0.0
    mf1 = (2 * mp * mr / (mp + mr)) if (mp + mr) else 0.0
    mean_p = sum(r["prec"] for r in rows) / n
    mean_r = sum(r["rec"] for r in rows) / n
    court_n = sum(1 for r in rows if r["court_ok"])
    esc_bool_n = sum(1 for r in rows if r["esc_ok"])
    kinds_n = sum(1 for r in rows if r["kinds_ok"])
    kinds_fe_n = sum(1 for r in rows if r["kinds_ok_fe"])
    silent_n = sum(1 for r in rows if r["silent"])
    fp_prose_n = sum(1 for r in rows if r["fp_prose"] > 0)
    err_n = sum(1 for r in rows if r["error"])
    lats = [r["latency_s"] for r in rows]
    cat_exact = {c: f"{sum(v)}/{len(v)}" for c, v in sorted(per_cat.items())}
    cat_min = min((sum(v) / len(v)) for v in per_cat.values()) if per_cat else 0.0

    # Gate / Brutal rating formula
    E = n_exact / n
    C = court_n / n
    S = esc_bool_n / n
    rating = max(0.0, min(10.0, round(10.0 * (0.60 * E + 0.15 * mean_r + 0.10 * mean_p + 0.075 * C + 0.075 * S) - 1.0 * fp_prose_n, 1)))

    out = {
        "n": n,
        "exact": f"{n_exact}/{n}",
        "exact_count": n_exact,
        "wilson_95": list(wilson_ci(n_exact, n)),
        "micro_p": round(mp, 4),
        "micro_r": round(mr, 4),
        "micro_f1": round(mf1, 4),
        "tp_fp_fn": [tot_tp, tot_fp, tot_fn],
        "mean_p": round(mean_p, 4),
        "mean_r": round(mean_r, 4),
        "court_correct": f"{court_n}/{n}",
        "esc_bool": f"{esc_bool_n}/{n}",
        "esc_kinds_strict": f"{kinds_n}/{n}",
        "esc_kinds_fe": f"{kinds_fe_n}/{n}",
        "silent": silent_n,
        "fp_prose": fp_prose_n,
        "errors": err_n,
        "per_cat_exact": cat_exact,
        "per_cat_min": round(cat_min, 4),
        "latency_mean_s": round(sum(lats) / len(lats), 3),
        "latency_max_s": round(max(lats), 3),
        "rating": rating,
        "top_fp_sections": dict(sec_fp.most_common(12)),
        "top_fn_sections": dict(sec_fn.most_common(12)),
    }

    if print_misses and not blind_text:
        shown = 0
        for r in rows:
            if not r["exact"]:
                print(f"  MISS {r['id']} ({r['category']}): pred={r['pred']} gt={r['gt']} court={r['court_live']}/{r['court_expected']} kinds={r['kinds']}/{r['gt_kinds']} model={r.get('model_slots')}", flush=True)
                shown += 1
                if shown >= print_misses:
                    break
    out["total_wall_s"] = total_wall_s
    return out


def _load_16q() -> list[dict[str, Any]]:
    qs = json.loads(GT_16_PATH.read_text(encoding="utf-8"))["questions"]
    items = []
    for q in qs:
        items.append({
            "id": q["id"],
            "category": "16Q",
            "question": q["question"],
            "gt_ids": q["gt_ids"],
            "gt_court": q["gt_court"],
            "gt_escalates": q["gt_escalates"],
            "gt_kinds": q.get("gt_escalation_kinds", []),
        })
    return items


def _load_brutal() -> list[dict[str, Any]]:
    qs = json.loads(BANK_PATH.read_text(encoding="utf-8"))["questions"]
    items = []
    for q in qs:
        items.append({
            "id": q["id"],
            "category": q["category"],
            "question": q["question"],
            "gt_ids": q["gt_sections"],
            "gt_court": [] if q["gt_court"] == "none" else [q["gt_court"]],
            "gt_escalates": q["gt_escalates"],
            "gt_kinds": q.get("gt_escalation_kinds", []),
        })
    return items


def _load_sealed(path: Path) -> list[dict[str, Any]]:
    qs = json.loads(path.read_text(encoding="utf-8"))["questions"]
    items = []
    for q in qs:
        mapped = {SEALED_KIND_MAP[e["type"]] for e in q.get("expected_escalations", []) if SEALED_KIND_MAP.get(e.get("type"))}
        items.append({
            "id": q["id"],
            "category": q.get("primary_issue", "sealed"),
            "question": q["question"],
            "gt_ids": q["gt_sections"],
            "gt_court": [COURT_NORMALIZE[c] for c in q.get("expected_court", [])],
            "gt_escalates": q["escalates"],
            "gt_kinds": sorted(mapped),
            "f20_rule": q["id"] == "F20",
        })
    return items


def main() -> None:
    parser = argparse.ArgumentParser(description="Scorer-isolated backtest for LAYA v7.")
    parser.add_argument("--suite", choices=("16q", "brutal", "both", "all_with_sealed"), default="both")
    parser.add_argument("--mode", choices=("auto", "laya", "structured", "evidence"), default="laya")
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--misses", type=int, default=20)
    args = parser.parse_args()

    out: dict[str, Any] = {}
    if args.suite in ("16q", "both", "all_with_sealed"):
        print("=== 16-Q ===")
        out["16q"] = score_dataset(
            _load_16q(),
            mode=args.mode,
            device=args.device,
            project_custody=False,
            legacy_16q_compat=True,
            print_misses=args.misses,
        )
        print(json.dumps(out["16q"], indent=2))
    if args.suite in ("brutal", "both", "all_with_sealed"):
        print("=== BRUTAL-230 (custody statutory_primary) ===")
        out["brutal_projected"] = score_dataset(
            _load_brutal(),
            mode=args.mode,
            device=args.device,
            project_custody=True,
            print_misses=args.misses,
        )
        print(json.dumps(out["brutal_projected"], indent=2))
    if args.suite == "all_with_sealed":
        print("=== SEALED FRESH-20 (aggregate only) ===")
        out["sealed_fresh_20"] = score_dataset(
            _load_sealed(SEALED_FRESH_PATH),
            mode=args.mode,
            device=args.device,
            project_custody=False,
            print_misses=0,
            blind_text=True,
        )
        print(json.dumps(out["sealed_fresh_20"], indent=2))
        print("=== SEALED KANNADA-8 (aggregate only) ===")
        out["sealed_kannada_8"] = score_dataset(
            _load_sealed(SEALED_KN_PATH),
            mode=args.mode,
            device=args.device,
            project_custody=False,
            print_misses=0,
            blind_text=True,
        )
        print(json.dumps(out["sealed_kannada_8"], indent=2))


if __name__ == "__main__":
    main()
