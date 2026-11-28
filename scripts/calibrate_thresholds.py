"""Graph-aware OOF threshold calibration for the LAYA v7.1 classifier.

FALLBACK-2 item 3 + GPT-RERUN claim 3 (binding corrections applied).

What it does, in order:
  1. Loads OOF per-record probs (written by
     ``scripts/train_v71_classifier.py --eval-checkpoint ... --val-file
     data/synthetic_v7_1/train.jsonl --dump-predictions ...``) and the gold
     labels from ``--train-file`` (Train-7500).
  2. Temperature scaling FIRST: one temperature per head family
     (issue / fact), grid-searched on OOF NLL.
  3. Global thresholds tau_0_issue / tau_0_fact: grid-searched on OOF
     Stage 2 section-set exact match (via tests/recall_eval.py
     predict_sections_from_stage1 — the frozen Graph v4 mapping).
  4. Per-head thresholds tau_h: each maximises F1.2 (recall-weighted F1)
     for its ACTIVE state on OOF (requested for issues, supported for
     facts), then Empirical Bayes shrinkage toward the family prior:
     tau_h = [N+/(N+ + kappa)] * tau_h^OOF + [kappa/(N+ + kappa)] * tau_0.
     kappa is COMPARED in {50, 150, 300} on OOF Stage 2 exact — kappa=150
     is an unproven hyperparameter, NOT a hard-coded default — with
     SEPARATE priors per family (tau_0_issue vs tau_0_fact).
  5. Up to 3 coordinate passes (default 3) on OOF Stage 2 exact, subject
     to micro-precision >= the floor (default 0.91). Each pass tries
     tau_h +/- 0.05 per head, then PAIRED +/- 0.05 moves on graph-coupled
     (issue, fact) pairs (a single-coordinate optimiser misses
     improvements that need two thresholds to move together). The Pareto
     table in thresholds.json reports where the FINAL calibrated point
     sits relative to each floor in 0.88 / 0.90 / 0.91 / 0.93 / 0.95
     (pass/fail per floor) — it is NOT a re-optimisation under each
     floor; a per-floor re-optimisation is a possible follow-up, not
     done here.
  6. Writes thresholds.json next to the checkpoint (contract C2):
     models/<name>/best/thresholds.json. The integrated runtime applies it
     at decode time via src/laya_v7_classifier.decode_with_thresholds().

HARD GUARDS (GPT-RERUN):
  - OOF on TRAIN-7500 ONLY. The script REFUSES any file whose sha256
    equals the frozen validation split
    (7640d067c28abf539131dbcc891e4bdffedf62bbef4a7d66c1659bb96d07e58e)
    or whose name contains "validation". The frozen split must stay
    untouched by calibration.
  - The OOF dump must cover exactly the Train-7500 records (same count,
    same id set) — a partial dump is an error, not a warning.

Pure python, no torch. Runs on CPU (minutes for 7,500 records; use
--limit for a fast smoke check of the script itself — a --limit run must
NOT be used as real thresholds).

Usage (after the 5-fold OOF predictions exist — see
docs/rtx-recall-training-commands.md §5):

    python3 scripts/calibrate_thresholds.py \\
        --oof-predictions models/v71-classifier/oof-preds.jsonl \\
        --train-file data/synthetic_v7_1/train.jsonl \\
        --checkpoint-dir models/v71-classifier/best
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from laya_v7_classifier import FACTS, FACT_STATES, ISSUES, ISSUE_INTENTS, load_corpus_jsonl  # noqa: E402

FROZEN_VAL_SHA256 = (
    "7640d067c28abf539131dbcc891e4bdffedf62bbef4a7d66c1659bb96d07e58e"
)
FROZEN_VAL_PATH = "data/synthetic_v7_1/validation.jsonl"

ISSUE_ACTIVE = "requested"
FACT_ACTIVE = "supported"
TAU_MIN, TAU_MAX = 0.22, 0.75
TEMP_GRID = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0)
TAU_GRID = tuple(round(0.25 + 0.05 * i, 2) for i in range(9))  # 0.25..0.65

# Graph-coupled (issue, fact) pairs for the PAIRED coordinate moves: the
# fact gates the issue's section in Graph v4, so moving both thresholds
# together can unlock a section neither move unlocks alone. (Pairs are
# the plan's high-fan-out facts + their parent issues.)
COUPLED_PAIRS = [
    ("residence", "coercive_eviction_or_lockout"),
    ("divorce", "divorce_asked"),
    ("custody", "custody_claim"),
    ("joint_property", "joint_property_claim"),
    ("stridhan", "stridhan_claim"),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_harness():
    """Import Lane 07's Stage 2 mapping (read-only use)."""
    spec = importlib.util.spec_from_file_location(
        "recall_eval", REPO_ROOT / "tests" / "recall_eval.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("tests/recall_eval.py not found — cannot score "
                           "Stage 2 exact match.")
    harness = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(harness)
    return harness


def temper_probs(probs: dict[str, float], temp: float) -> dict[str, float]:
    """Apply temperature T to a prob dict (log-space, renormalised)."""
    if temp == 1.0:
        return dict(probs)
    logits = {k: math.log(max(v, 1e-12)) / temp for k, v in probs.items()}
    m = max(logits.values())
    exps = {k: math.exp(v - m) for k, v in logits.items()}
    s = sum(exps.values())
    return {k: v / s for k, v in exps.items()}


def nll_for_family(oof, family: str, temp: float) -> float:
    """Mean NLL of the gold label under temperature-scaled OOF probs."""
    total, n = 0.0, 0
    key = "pred_issues" if family == "issue" else "pred_facts"
    gold_key = "gold_issues" if family == "issue" else "gold_facts"
    for row in oof:
        for name, probs in row[key].items():
            gold = row[gold_key][name]
            scaled = temper_probs(probs, temp)
            total += -math.log(max(scaled.get(gold, 1e-12), 1e-12))
            n += 1
    return total / max(1, n)


def decode_labels(pred_issues, pred_facts, temp_issue, temp_fact,
                  tau_issue, tau_fact, tau0_issue, tau0_fact):
    """Decode probs to predict_text-style dicts (argmax, neutral fallback).

    Same rule as src/laya_v7_classifier.decode_with_thresholds(): the
    argmax state wins, but if its probability is below the head's
    threshold the label falls back to the neutral state ("uncertain" for
    issues, "unknown" for facts) instead of emitting a low-confidence
    active label.
    """
    issues: dict[str, dict[str, str]] = {}
    for name, probs in pred_issues.items():
        scaled = temper_probs(probs, temp_issue)
        best = max(scaled, key=lambda k: scaled[k])
        tau = tau_issue.get(name, tau0_issue)
        issues[name] = {"intent": best if scaled[best] >= tau else "uncertain"}
    facts: dict[str, dict[str, str]] = {}
    for name, probs in pred_facts.items():
        scaled = temper_probs(probs, temp_fact)
        best = max(scaled, key=lambda k: scaled[k])
        tau = tau_fact.get(name, tau0_fact)
        facts[name] = {"state": best if scaled[best] >= tau else "unknown"}
    return issues, facts


def decode_enums(pred_enums: dict[str, Any] | None) -> dict[str, dict[str, str]]:
    """Decode {head: prob_dict} or {head: {'value': ...}} for Stage 2."""
    out: dict[str, dict[str, str]] = {}
    for head, val in (pred_enums or {}).items():
        if isinstance(val, dict):
            if "value" in val:
                out[head] = {"value": str(val["value"])}
            elif val:
                out[head] = {"value": max(val, key=lambda k: float(val[k]))}
        else:
            out[head] = {"value": str(val)}
    return out


def f_beta(prec: float, rec: float, beta: float = 1.2) -> float:
    b2 = beta * beta
    if prec + rec == 0:
        return 0.0
    return (1 + b2) * prec * rec / (b2 * prec + rec)


def per_head_tau_oof(oof, names, *, family: str, temp: float) -> dict[str, float]:
    """Per-head threshold maximising F1.2 for the ACTIVE state on OOF."""
    active = ISSUE_ACTIVE if family == "issue" else FACT_ACTIVE
    key = "pred_issues" if family == "issue" else "pred_facts"
    gold_key = "gold_issues" if family == "issue" else "gold_facts"
    out: dict[str, float] = {}
    for name in names:
        best_tau, best_f = 0.5, -1.0
        for tau in TAU_GRID:
            tp = fp = fn = 0
            for row in oof:
                p = temper_probs(row[key][name], temp)[active]
                pred_active = p >= tau
                gold_active = row[gold_key][name] == active
                if pred_active and gold_active:
                    tp += 1
                elif pred_active:
                    fp += 1
                elif gold_active:
                    fn += 1
            prec = tp / (tp + fp) if tp + fp else 1.0
            rec = tp / (tp + fn) if tp + fn else 1.0
            score = f_beta(prec, rec, 1.2)
            if score > best_f:
                best_f, best_tau = score, tau
        out[name] = best_tau
    return out


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        description="Graph-aware OOF threshold calibration (Train-7500 only).")
    p.add_argument("--oof-predictions", required=True,
                   help="JSONL from --dump-predictions on the TRAIN split.")
    p.add_argument("--train-file", required=True,
                   help="Train JSONL (Train-7500). Validation files refused.")
    p.add_argument("--checkpoint-dir", required=True,
                   help="Dir containing model.pt; thresholds.json is written here.")
    p.add_argument("--out", default=None,
                   help="Override output path for thresholds.json.")
    p.add_argument("--kappas", default="50,150,300",
                   help="EB shrinkage kappas to compare (default 50,150,300).")
    p.add_argument("--precision-floors", default="0.88,0.90,0.91,0.93,0.95",
                   help="Pareto floors to measure (default 0.88..0.95).")
    p.add_argument("--precision-floor", type=float, default=0.91,
                   help="Floor enforced during coordinate passes (default 0.91).")
    p.add_argument("--max-passes", type=int, default=3,
                   help="Coordinate passes, max 3 (GPT-RERUN).")
    p.add_argument("--limit", type=int, default=None,
                   help="SMOKE ONLY: calibrate on the first N OOF records. "
                        "A --limit run must NOT be used as real thresholds.")
    args = p.parse_args(argv)

    train_path = Path(args.train_file)
    oof_path = Path(args.oof_predictions)
    ckpt_dir = Path(args.checkpoint_dir)
    if not train_path.exists():
        print(f"ERROR: train file not found: {train_path}", file=sys.stderr)
        return 2
    if not oof_path.exists():
        print(f"ERROR: OOF file not found: {oof_path}", file=sys.stderr)
        return 2
    if not (ckpt_dir / "model.pt").exists():
        print(f"ERROR: no model.pt in checkpoint dir {ckpt_dir} — calibrate "
              "the BEST checkpoint only.", file=sys.stderr)
        return 2

    # --- HARD GUARD: never calibrate on (or with) the frozen validation split.
    train_sha = sha256_file(train_path)
    if train_sha == FROZEN_VAL_SHA256 or "validation" in train_path.name:
        print("ERROR: REFUSED — --train-file is the frozen validation split "
              f"({FROZEN_VAL_PATH}, sha256 {FROZEN_VAL_SHA256[:12]}...). "
              "OOF calibration runs on Train-7500 ONLY; the frozen split "
              "must stay untouched by calibration.", file=sys.stderr)
        return 2

    gold_recs, _ = load_corpus_jsonl(train_path)
    oof = [json.loads(line) for line in oof_path.read_text(encoding="utf-8").splitlines()
           if line.strip()]
    if args.limit is not None:
        print(f"WARNING: --limit {args.limit} — SMOKE ONLY, not real thresholds.")
        oof = oof[: args.limit]
        gold_recs = gold_recs[: args.limit]
    gold_by_id = {r["id"]: r for r in gold_recs}
    oof_ids = [row["id"] for row in oof]
    if len(oof) != len(gold_recs) or set(oof_ids) != set(gold_by_id):
        print(f"ERROR: OOF dump does not cover Train-7500 exactly "
              f"(oof={len(oof)} train={len(gold_recs)}). The dump must cover "
              "all 7,500 training records once (5-fold grouped OOF).",
              file=sys.stderr)
        return 2
    # Align OOF rows to gold order.
    oof_by_id = {row["id"]: row for row in oof}
    oof = [oof_by_id[g["id"]] for g in gold_recs]

    harness = load_harness()
    # Expected sections per gold record, computed ONCE (not per candidate).
    expected = [
        harness.predict_sections_from_stage1(g["issues"], g["facts"], g["enums"])
        for g in gold_recs
    ]

    def score_stage2(temp_issue, temp_fact, tau_issue, tau_fact,
                     tau0_issue, tau0_fact):
        """Stage 2 exact + micro-P/R for a threshold set (fast path)."""
        tp = fp = fn = exact = 0
        for row, exp in zip(oof, expected):
            issues, facts = decode_labels(
                row["pred_issues"], row["pred_facts"],
                temp_issue, temp_fact, tau_issue, tau_fact,
                tau0_issue, tau0_fact)
            pred = harness.predict_sections_from_stage1(
                issues, facts, decode_enums(row["pred_enums"]))
            if pred == exp:
                exact += 1
            tp += len(pred & exp)
            fp += len(pred - exp)
            fn += len(exp - pred)
        n = len(oof)
        micro_p = tp / (tp + fp) if tp + fp else 0.0
        micro_r = tp / (tp + fn) if tp + fn else 0.0
        return {"exact": exact, "exact_rate": round(exact / n, 4) if n else 0.0,
                "micro_p": round(micro_p, 4), "micro_r": round(micro_r, 4)}

    # --- 1. Temperature scaling first (per family, OOF NLL).
    temp_issue = min(TEMP_GRID, key=lambda t: nll_for_family(oof, "issue", t))
    temp_fact = min(TEMP_GRID, key=lambda t: nll_for_family(oof, "fact", t))
    print(f"temperature: issue T={temp_issue} "
          f"(NLL {nll_for_family(oof, 'issue', temp_issue):.4f}), "
          f"fact T={temp_fact} "
          f"(NLL {nll_for_family(oof, 'fact', temp_fact):.4f})")

    # --- 2. Global thresholds tau_0 per family (OOF Stage 2 exact).
    def tau0_score(family, tau0):
        if family == "issue":
            return score_stage2(temp_issue, temp_fact, {}, {},
                                tau0, 0.5)["exact_rate"]
        return score_stage2(temp_issue, temp_fact, {}, {},
                            0.5, tau0)["exact_rate"]

    tau0_issue = max(TAU_GRID, key=lambda t: tau0_score("issue", t))
    tau0_fact = max(TAU_GRID, key=lambda t: tau0_score("fact", t))
    print(f"tau_0: issue={tau0_issue} fact={tau0_fact} "
          f"(OOF exact at tau_0-only decode: "
          f"{score_stage2(temp_issue, temp_fact, {}, {}, tau0_issue, tau0_fact)})")

    # --- 3. Per-head OOF thresholds (F1.2) + EB shrinkage, kappa compared.
    tau_issue_oof = per_head_tau_oof(oof, ISSUES, family="issue", temp=temp_issue)
    tau_fact_oof = per_head_tau_oof(oof, FACTS, family="fact", temp=temp_fact)

    def n_pos(family, name):
        active = ISSUE_ACTIVE if family == "issue" else FACT_ACTIVE
        gold_key = "gold_issues" if family == "issue" else "gold_facts"
        return sum(1 for row in oof if row[gold_key][name] == active)

    kappas = [int(k) for k in args.kappas.split(",") if k.strip()]
    kappa_results = {}
    for kappa in kappas:
        tau_i = {n: (n_pos("issue", n) / (n_pos("issue", n) + kappa)) * tau_issue_oof[n]
                 + (kappa / (n_pos("issue", n) + kappa)) * tau0_issue
                 for n in ISSUES}
        tau_f = {n: (n_pos("fact", n) / (n_pos("fact", n) + kappa)) * tau_fact_oof[n]
                 + (kappa / (n_pos("fact", n) + kappa)) * tau0_fact
                 for n in FACTS}
        s = score_stage2(temp_issue, temp_fact, tau_i, tau_f,
                         tau0_issue, tau0_fact)
        kappa_results[kappa] = (tau_i, tau_f, s)
        print(f"kappa={kappa}: OOF exact {s['exact_rate']} micro-P {s['micro_p']} "
              f"micro-R {s['micro_r']}")
    # Best kappa by OOF exact; ties break to 150 (FALLBACK-2 middle value).
    best_kappa = max(kappas, key=lambda k: (
        kappa_results[k][2]["exact_rate"], -abs(k - 150)))
    tau_issue, tau_fact, best_score = kappa_results[best_kappa]
    print(f"selected kappa={best_kappa} (exact {best_score['exact_rate']}, "
          f"micro-P {best_score['micro_p']})")

    # --- 4. Coordinate passes (up to --max-passes, default 3).
    floor = args.precision_floor
    current = best_score

    def try_move(tau_i, tau_f):
        s = score_stage2(temp_issue, temp_fact, tau_i, tau_f,
                         tau0_issue, tau0_fact)
        return s if (s["exact_rate"] > current["exact_rate"]
                     and s["micro_p"] >= floor) else None

    for pass_no in range(1, max(1, min(args.max_passes, 3)) + 1):
        improved = False
        for name in ISSUES:
            for delta in (0.05, -0.05):
                cand = dict(tau_issue)
                cand[name] = round(min(TAU_MAX, max(TAU_MIN, cand[name] + delta)), 2)
                s = try_move(cand, tau_fact)
                if s is not None:
                    tau_issue, current, improved = cand, s, True
        for name in FACTS:
            for delta in (0.05, -0.05):
                cand = dict(tau_fact)
                cand[name] = round(min(TAU_MAX, max(TAU_MIN, cand[name] + delta)), 2)
                s = try_move(tau_issue, cand)
                if s is not None:
                    tau_fact, current, improved = cand, s, True
        # Paired moves on graph-coupled (issue, fact) pairs.
        for issue_name, fact_name in COUPLED_PAIRS:
            for delta in (0.05, -0.05):
                cand_i = dict(tau_issue)
                cand_f = dict(tau_fact)
                cand_i[issue_name] = round(min(TAU_MAX, max(TAU_MIN, cand_i[issue_name] + delta)), 2)
                cand_f[fact_name] = round(min(TAU_MAX, max(TAU_MIN, cand_f[fact_name] + delta)), 2)
                s = try_move(cand_i, cand_f)
                if s is not None:
                    tau_issue, tau_fact, current, improved = cand_i, cand_f, s, True
        print(f"coordinate pass {pass_no}: exact {current['exact_rate']} "
              f"micro-P {current['micro_p']} improved={improved}")
        if not improved:
            break

    # --- 5. Pareto frontier: re-run the final thresholds against each floor.
    # (The thresholds were refined under the main floor; the Pareto reports
    # the exact/micro-P the SAME thresholds achieve — floors only gate
    # acceptance during refinement, so this table shows where the final
    # point sits relative to each floor, not a re-optimisation per floor.)
    pareto = {}
    for f in [float(x) for x in args.precision_floors.split(",") if x.strip()]:
        pareto[str(f)] = {"exact_rate": current["exact_rate"],
                          "micro_p": current["micro_p"],
                          "passes_floor": current["micro_p"] >= f}

    # Cross-check the fast-path scoring against the harness once, on the
    # final thresholds, so a scoring bug cannot silently pass.
    final_preds = []
    for row in oof:
        issues, facts = decode_labels(
            row["pred_issues"], row["pred_facts"],
            temp_issue, temp_fact, tau_issue, tau_fact, tau0_issue, tau0_fact)
        final_preds.append(harness.predict_sections_from_stage1(
            issues, facts, decode_enums(row["pred_enums"])))
    check = harness.score_predictions(gold_recs, final_preds)
    check.pop("rows", None)
    if (check["exact_count"] != current["exact"]
            or abs(check["micro_p"] - current["micro_p"]) > 0.001):
        print(f"WARNING: fast-path score disagrees with harness "
              f"(fast exact={current['exact']} micro-P={current['micro_p']} vs "
              f"harness exact={check['exact_count']} "
              f"micro-P={check['micro_p']}). Using harness numbers.",
              file=sys.stderr)
        current = {"exact": check["exact_count"],
                   "exact_rate": check["exact_rate"],
                   "micro_p": check["micro_p"], "micro_r": check["micro_r"]}

    thresholds = {
        "temperature_issue": temp_issue,
        "temperature_fact": temp_fact,
        "tau_0_issue": tau0_issue,
        "tau_0_fact": tau0_fact,
        "tau_issue": {n: round(v, 2) for n, v in tau_issue.items()},
        "tau_fact": {n: round(v, 2) for n, v in tau_fact.items()},
        "kappa": best_kappa,
        "kappas_compared": {str(k): v[2] for k, v in kappa_results.items()},
        "precision_floor": floor,
        "oof": {"n": len(oof), "exact": current["exact"],
                "exact_rate": current["exact_rate"],
                "micro_p": current["micro_p"], "micro_r": current["micro_r"],
                "pareto": pareto},
        "oof_source": str(oof_path),
        "train_file": str(train_path),
        "train_file_sha256": train_sha,
        "val_500_untouched": True,
        "frozen_val_sha256_refused": FROZEN_VAL_SHA256,
        "decode_rule": ("argmax, neutral fallback (uncertain/unknown) if "
                        "argmax prob < head threshold; see "
                        "src/laya_v7_classifier.decode_with_thresholds"),
        "smoke_only": args.limit is not None,
    }
    out_path = Path(args.out) if args.out else ckpt_dir / "thresholds.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(thresholds, indent=2), encoding="utf-8")
    print(f"Wrote thresholds.json -> {out_path}")
    print(f"OOF (Train-7500, n={len(oof)}): exact {current['exact_rate']} "
          f"micro-P {current['micro_p']} micro-R {current['micro_r']} "
          f"kappa={best_kappa} floor={floor}")
    print("Val-500 was NOT touched by this calibration "
          "(guard: sha256 + filename check).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
