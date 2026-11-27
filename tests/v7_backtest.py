"""Scorer-isolated full-system backtest runner for LAYA v7.

Strictly enforces separation: assess_v7() receives ONLY raw question text (+
optional production confirmations). Dataset IDs, expected facts, and gold labels
are joined strictly AFTER inference inside score_predictions().

V71-P7-1 (LAYA v7.1 / 10x plan §7.1) — honest scoring:
  * Fb is measured genuinely from pre-gate candidates (see ``compute_fb`` and
    the Fb definition below), never 0-by-construction from post-Stage-2 kept_ids.
  * Both ``raw_formula_rating`` and ``capped_rating`` are computed and printed,
    applying every Gate §2 cap (docs/laya-10-10-gate-definition.md §2).
    ``rating`` is the CAPPED rating. An uncapped 10.0 is never printed when any
    cap binds.
  * Strict 16-Q esc_bool / esc_kinds_strict are reported alongside the legacy
    compat values; the H12 safety-delta masking is surfaced, never hidden.
  * Sealed suites carry aggregate-only diagnostic telemetry (hma-27 note-ID
    sensitivity + F1/F2/KN1 court sensitivity) with blind_text=True: item IDs
    and counts only, zero sealed question text.

Fb definition (frozen for this scorer; see docs/10x_swarm_state/lane-10-p7.md)
---------------------------------------------------------------------------
Fb = number of (question, section) pairs where a section in
``candidates_before_gate`` was proposed pre-gate but Stage 2 gated it out for
a statutory-prerequisite reason. Per contract C1 (docs/10x_swarm_state.md)
Lane 01 produces ``rec["candidates_before_gate"]`` = the disposition keys
(eligible + conditional + inapplicable). The scorer reads, in order:

  1. ``rec["candidates_before_gate"]`` (primary; contract C1), else
  2. ``rec["dispositions"]`` keys (the same disposition set, present in every
     current assess_v7 record), else
  3. ``rec["kept_ids"]`` only — with ``fb_measured=False``. A 0 from this
     fallback is NOT a measured 0 and is flagged as unmeasured.

A pre-gate candidate counts toward Fb iff it is NOT in ``kept_ids`` AND either
(a) it matches one of the 6 frozen forbidden mappings below, or (b) Stage 2
gated it out for a statutory-prerequisite reason (a disposition with status
conditional / needs_fact / inapplicable whose reason code is a statutory-gate
reason, or an entry in ``rec["gated_out"]`` naming that section).

The 6 frozen forbidden mappings (Gate §5, Fp items 1-6, applied here at the
pre-gate candidate level):

  1. rajnesh_for_stridhan — Rajnesh v. Neha cited for Stridhan return.
  2. satish_for_custody — Satish Chander Ahuja cited for custody.
  3. hma_13_13b_divorce_not_asked — HMA ss. 13/13B proposed when divorce was
     not asked (13B additionally requires mutual consent).
  4. residence_as_tenancy — residence labelled "tenancy rights".
  5. ask_user_to_pick_court — user asked to pick the court.
  6. birth_certificate_under_hma — birth certificate placed under HMA.

Candidate-level detectability: only mapping 3 has a section-candidate
signature (candidate hma-13 / hma-13b, not kept, gated with reason
``divorce_not_expressly_asked`` / gated_out "divorce not asked"). Mappings 1,
2, 4, 5, 6 are citation / label / prose errors with NO section-candidate
signature: they cannot be detected from pre-gate section IDs and are NOT
double-counted here. They are enforced where they are observable — in prose,
via ``prose_forbidden_check`` Fp items 1, 2, 4, 5, 6, counted in ``fp_prose``.
The operative, measurable part of Fb is therefore clause (b): any candidate
gated out for a statutory-prerequisite reason. That clause subsumes the
canonical Gate §5 Fb examples (HMA 25 with no decree, HMA 24 with no
proceeding, HMA 13/13B with divorce not asked, HMA 26 with no proceeding,
HMA 27 with no HMA proceeding — D2 — PWDVA s.2(a) eligibility failure,
male self-maintenance outside HMA, adult-child BNSS 144 ineligibility).

Deliberately NOT counted: dispositions with reason ``superseded_*`` (e.g.
hma-13 inapplicable because hma-13b is eligible on mutual consent, gwa-1890
inapplicable because hma-26 governs inside a pending HMA proceeding).
Supersession is correct routing, not a forbidden proposal.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys
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

# --- V71-P7-1: genuine Fb measurement -------------------------------------
# The 6 frozen forbidden mappings (Gate §5 Fp items 1-6). Only mapping 3 is
# detectable from pre-gate section candidates; the rest are prose-level and
# are enforced via Fp (prose_forbidden_check), not double-counted in Fb.
FORBIDDEN_FB_MAPPINGS: tuple[dict[str, Any], ...] = (
    {"key": "rajnesh_for_stridhan", "gate_fp_item": 1, "detectable_in_candidates": False,
     "note": "Citation error; prose-level only, enforced via Fp item 1."},
    {"key": "satish_for_custody", "gate_fp_item": 2, "detectable_in_candidates": False,
     "note": "Citation error; prose-level only, enforced via Fp item 2."},
    {"key": "hma_13_13b_divorce_not_asked", "gate_fp_item": 3, "detectable_in_candidates": True,
     "note": "Candidate hma-13/hma-13b, not kept, gated with divorce_not_expressly_asked / 'divorce not asked'."},
    {"key": "residence_as_tenancy", "gate_fp_item": 4, "detectable_in_candidates": False,
     "note": "Wrong legal label; prose-level only, enforced via Fp item 4."},
    {"key": "ask_user_to_pick_court", "gate_fp_item": 5, "detectable_in_candidates": False,
     "note": "Prose asks user to pick court; prose-level only, enforced via Fp item 5."},
    {"key": "birth_certificate_under_hma", "gate_fp_item": 6, "detectable_in_candidates": False,
     "note": "Wrong Act for birth certificate; prose-level only, enforced via Fp item 6."},
)

# Disposition reason-code substrings (lowercased) that denote a
# statutory-prerequisite gate. Checked ONLY for non-kept candidates whose
# disposition status is conditional / needs_fact / inapplicable. Reason codes
# containing "superseded" are excluded upstream (correct routing, not a
# forbidden proposal). Eligible dispositions are never counted (they are kept).
STATUTORY_GATE_REASON_SUBSTRINGS: tuple[str, ...] = (
    "no_decree", "pre_decree", "without_decree", "no_pending", "no_hma",
    "d2_", "divorce_not", "not_expressly_asked", "s2a",
    "eligibility_failed", "excluded_bnss144", "husband_self_claim_excluded",
    "adult_child", "adult_able_child", "no_domestic_entrustment",
    "stridhan_safe_or_no_domestic", "gated",
)

# Sealed diagnostic note IDs (plan §4.4 / §7.1; IDs only, never question text).
HMA27_NOTE_IDS: frozenset[str] = frozenset({"F8", "F9", "F10", "F16", "KN3"})
COURT_NOTE_IDS: frozenset[str] = frozenset({"F1", "F2", "KN1"})

# Brutal-230 pass bar (docs/brutal-test-200-plan.md §3.2): strict typed
# escalations >= 200/230 and every category >= 0.75 exact.
STRICT_ESC_KINDS_BAR_NUM = 200
STRICT_ESC_KINDS_BAR_DEN = 230
STRICT_PER_CAT_MIN = 0.75


def _is_statutory_gate_reason(reason_codes: list[str]) -> bool:
    """True iff any reason code denotes a statutory-prerequisite gate."""
    for code in reason_codes or []:
        low = str(code).lower()
        if "superseded" in low:
            continue
        if any(sub in low for sub in STATUTORY_GATE_REASON_SUBSTRINGS):
            return True
    return False


def _parse_gated_out_sections(gated_out: Any) -> dict[str, str]:
    """Map section id -> gated_out entry text, from rec["gated_out"] strings.

    Entries look like "hma-25: gated (pre_decree_without_hma)",
    "hma-27: gated (D2) — no HMA proceeding pending or being filed",
    "pwdva-17/19: gated (PWDVA s.2(a) claimant/domestic check)".
    Entries with no section id ("all: out_of_scope",
    "maintenance: gated (male spouse self-maintenance outside HMA)") are
    skipped here; their sections are still caught via dispositions.
    """
    out: dict[str, str] = {}
    for entry in gated_out or []:
        text = str(entry)
        head = text.split(":", 1)[0].strip()
        for token in head.split("/"):
            token = token.strip()
            # A section id contains "-" and is not a bare word like "all".
            if "-" in token and token not in {"out_of_scope"}:
                out[token] = text
    return out


def compute_fb(rec: dict[str, Any]) -> dict[str, Any]:
    """Genuinely measure forbidden-before-recheck (Fb) for one record.

    Pure function (no torch, no I/O): safe to unit-test on synthetic records.
    Returns {"fb_count", "fb_details", "fb_by_mapping", "fb_measured",
    "fb_source"}. ``fb_count`` counts distinct (question, section) pairs.
    """
    kept = set(rec.get("kept_ids") or [])
    dispositions = rec.get("dispositions") or {}
    gated_out = rec.get("gated_out") or []

    candidates: list[str] | None = None
    fb_source = ""
    fb_measured = False
    if isinstance(rec.get("candidates_before_gate"), list) and rec.get("candidates_before_gate"):
        candidates = list(rec["candidates_before_gate"])
        fb_source = "candidates_before_gate"
        fb_measured = True
    elif isinstance(dispositions, dict) and dispositions:
        # Same disposition set contract C1 defines as candidates_before_gate.
        candidates = list(dispositions.keys())
        fb_source = "dispositions_keys"
        fb_measured = True
    elif isinstance(rec.get("candidates_before_stage2"), list) and rec.get("candidates_before_stage2"):
        candidates = list(rec["candidates_before_stage2"])
        fb_source = "candidates_before_stage2 (known clone of kept_ids pre-Lane-01; Fb NOT measurable)"
        fb_measured = False
    else:
        candidates = list(kept)
        fb_source = "kept_ids fallback (no pre-gate data in record; Fb NOT measurable)"
        fb_measured = False

    gated_sections = _parse_gated_out_sections(gated_out)
    details: list[dict[str, Any]] = []
    if fb_measured:
        for sec in candidates:
            if sec in kept:
                continue
            disp = dispositions.get(sec) or {}
            status = str(disp.get("status") or "")
            reasons = [str(r) for r in (disp.get("reason_codes") or [])]
            reason_text = ";".join(reasons) if reasons else status
            mapping: str | None = None
            if sec in {"hma-13", "hma-13b"} and (
                any("divorce_not" in r.lower() or "not_expressly_asked" in r.lower() for r in reasons)
                or sec in gated_sections
            ):
                mapping = "hma_13_13b_divorce_not_asked"
            elif sec in gated_sections:
                mapping = "statutory_prerequisite_gate"
                reason_text = gated_sections[sec]
            elif status in {"conditional", "needs_fact", "inapplicable"} and _is_statutory_gate_reason(reasons):
                mapping = "statutory_prerequisite_gate"
            if mapping is not None:
                details.append({"section": sec, "mapping": mapping, "reason": reason_text})
    by_mapping = dict(Counter(d["mapping"] for d in details))
    return {
        "fb_count": len(details),
        "fb_details": details,
        "fb_by_mapping": by_mapping,
        "fb_measured": fb_measured,
        "fb_source": fb_source,
    }


def apply_gate_caps(
    raw_rating: float,
    *,
    fp_prose_n: int = 0,
    fb_count: int = 0,
    g12_verified: bool = False,
    sealed_passed: bool = False,
    confirmation_done: bool = False,
    prose_measured: bool = True,
    errors: int = 0,
) -> tuple[float, list[str]]:
    """Apply Gate §2 caps (frozen, docs/laya-10-10-gate-definition.md §2).

    Returns (capped_rating, caps_applied). ``capped_rating`` is the lower of
    the formula rating and every binding cap. Flags default to the honest
    (unverified) state, so a bare run can never print an uncapped 10.0:
    G12 unverified, sealed not passed and no confirmation re-run each cap at
    9.0; Fp >= 1 caps at 5.0; errors >= 3 caps at 5.0; Fb >= 1 caps at 9.0.
    """
    caps: list[str] = []
    cap_value = 10.0
    if fp_prose_n >= 1:
        caps.append("Fp>=1 -> <=5.0")
        cap_value = min(cap_value, 5.0)
    if fb_count >= 1:
        caps.append("Fb>=1 -> <=9.0")
        cap_value = min(cap_value, 9.0)
    if not g12_verified:
        caps.append("G12_unverified -> <=9.0")
        cap_value = min(cap_value, 9.0)
    if not prose_measured:
        caps.append("prose_not_measured -> <=9.0")
        cap_value = min(cap_value, 9.0)
    if not sealed_passed:
        caps.append("sealed_not_passed -> <=9.0")
        cap_value = min(cap_value, 9.0)
    if not confirmation_done:
        caps.append("confirmation_missing -> <=9.0")
        cap_value = min(cap_value, 9.0)
    if errors >= 3:
        caps.append("errors>=3 -> <=5.0")
        cap_value = min(cap_value, 5.0)
    capped = max(0.0, min(10.0, round(min(float(raw_rating), cap_value), 1)))
    return capped, caps


def strict_check(suite_name: str, n: int, kinds_strict_n: int, per_cat_min: float) -> list[str]:
    """--strict failures for one suite. The 200/230 esc_kinds bar is a
    Brutal-230 bar (n == 230); other suites are checked on per_cat_min only
    and their strict kinds count is reported, not asserted against 200/230."""
    failures: list[str] = []
    if n == STRICT_ESC_KINDS_BAR_DEN:
        if kinds_strict_n < STRICT_ESC_KINDS_BAR_NUM:
            failures.append(
                f"{suite_name}: esc_kinds_strict {kinds_strict_n}/{n} < "
                f"{STRICT_ESC_KINDS_BAR_NUM}/{STRICT_ESC_KINDS_BAR_DEN} (FAIL)"
            )
    if per_cat_min < STRICT_PER_CAT_MIN:
        failures.append(
            f"{suite_name}: per_cat_min {per_cat_min:.4f} < {STRICT_PER_CAT_MIN} (FAIL)"
        )
    return failures


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
    g12_verified: bool = False,
    sealed_passed: bool = False,
    confirmation_done: bool = False,
    sealed_note_ids: bool = False,
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

        # V71-P7-1: strict esc_bool — no safety removal, no H12 special case.
        # Reported alongside the legacy-compat value, never instead of it.
        esc_ok_strict = (bool(kinds) == bool(item["gt_escalates"]))

        kinds_ok_strict = (kinds == gt_kinds)
        kinds_ok_fe = ((kinds - {"fact"}) == (gt_kinds - {"fact"}))
        silent = bool(gt) and not pred
        exact = (pred == gt)
        per_cat[item.get("category", "all")].append(exact)

        fb = compute_fb(rec)

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
            "esc_ok_strict": esc_ok_strict,
            "kinds": sorted(kinds),
            "gt_kinds": sorted(gt_kinds),
            "kinds_ok": kinds_ok_strict,
            "kinds_ok_fe": kinds_ok_fe,
            "silent": silent,
            "fp_prose": len(rec.get("prose_fp_hits") or []),
            "q_flags": len(rec.get("prose_quality_flags") or []),
            "fb": fb["fb_count"],
            "fb_details": fb["fb_details"],
            "fb_measured": fb["fb_measured"],
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
    esc_bool_strict_n = sum(1 for r in rows if r["esc_ok_strict"])
    kinds_n = sum(1 for r in rows if r["kinds_ok"])
    kinds_fe_n = sum(1 for r in rows if r["kinds_ok_fe"])
    silent_n = sum(1 for r in rows if r["silent"])
    fp_prose_n = sum(1 for r in rows if r["fp_prose"] > 0)
    err_n = sum(1 for r in rows if r["error"])
    fb_count = sum(r["fb"] for r in rows)
    fb_by_mapping = dict(Counter(m for r in rows for d in r["fb_details"] for m in [d["mapping"]]))
    fb_measured_all = all(r["fb_measured"] for r in rows)
    lats = [r["latency_s"] for r in rows]
    cat_exact = {c: f"{sum(v)}/{len(v)}" for c, v in sorted(per_cat.items())}
    cat_min = min((sum(v) / len(v)) for v in per_cat.values()) if per_cat else 0.0

    # H12 strict-vs-legacy surfacing (V71-P7-1: stop H12 masking).
    h12_row = next((r for r in rows if r["id"] == "H12"), None)
    h12 = None
    if h12_row is not None:
        h12 = {
            "strict_esc_ok": h12_row["esc_ok_strict"],
            "legacy_esc_ok": h12_row["esc_ok"],
            "strict_kinds_ok": h12_row["kinds_ok"],
            "kinds": h12_row["kinds"],
            "gt_kinds": h12_row["gt_kinds"],
            "gt_escalates": bool(h12_row["gt_kinds"]),
            "note": "Strict esc_bool counts the H12 safety/procedure delta as a "
                    "mismatch; legacy_16q_compat does not. Both are reported.",
        }

    # Gate / Brutal rating formula (Gate §2, frozen): -0.5 * Fb - 1.0 * Fp.
    E = n_exact / n
    C = court_n / n
    S = esc_bool_n / n
    raw_rating = max(0.0, min(10.0, round(
        10.0 * (0.60 * E + 0.15 * mean_r + 0.10 * mean_p + 0.075 * C + 0.075 * S)
        - 0.5 * fb_count - 1.0 * fp_prose_n, 1)))
    prose_measured = all("prose_fp_hits" in rec for rec in recs)
    capped_rating, caps_applied = apply_gate_caps(
        raw_rating,
        fp_prose_n=fp_prose_n,
        fb_count=fb_count,
        g12_verified=g12_verified,
        sealed_passed=sealed_passed,
        confirmation_done=confirmation_done,
        prose_measured=prose_measured,
        errors=err_n,
    )

    out: dict[str, Any] = {
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
        "esc_bool_strict": f"{esc_bool_strict_n}/{n}",
        "esc_bool_legacy_compat": f"{esc_bool_n}/{n}",
        "legacy_16q_compat": bool(legacy_16q_compat),
        "h12": h12,
        "esc_kinds_strict": f"{kinds_n}/{n}",
        "esc_kinds_fe": f"{kinds_fe_n}/{n}",
        "silent": silent_n,
        "fp_prose": fp_prose_n,
        "fb_count": fb_count,
        "fb_by_mapping": fb_by_mapping,
        "fb_measured": fb_measured_all,
        "fb_warning": None if fb_measured_all else (
            "Fb UNMEASURED on at least one record: no candidates_before_gate / "
            "dispositions in the record; fb_count=0 is NOT a measured 0."
        ),
        "errors": err_n,
        "per_cat_exact": cat_exact,
        "per_cat_min": round(cat_min, 4),
        "latency_mean_s": round(sum(lats) / len(lats), 3),
        "latency_max_s": round(max(lats), 3),
        "raw_formula_rating": raw_rating,
        "capped_rating": capped_rating,
        "rating": capped_rating,
        "caps_applied": caps_applied,
        "top_fp_sections": dict(sec_fp.most_common(12)),
        "top_fn_sections": dict(sec_fn.most_common(12)),
    }

    # V71-P7-1: sealed diagnostic telemetry — aggregates + item IDs only,
    # zero sealed question text (blind_text=True is preserved by the caller).
    if sealed_note_ids:
        out["sealed_diagnostics"] = _sealed_diagnostics(rows)
    else:
        out["sealed_diagnostics"] = None

    if print_misses and not blind_text:
        shown = 0
        for r in rows:
            if not r["exact"]:
                print(f"  MISS {r['id']} ({r['category']}): pred={r['pred']} gt={r['gt']} court={r['court_live']}/{r['court_expected']} kinds={r['kinds']}/{r['gt_kinds']} fb={r['fb']} model={r.get('model_slots')}", flush=True)
                shown += 1
                if shown >= print_misses:
                    break
    out["total_wall_s"] = total_wall_s
    return out


def _sealed_diagnostics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate-only sealed sensitivity telemetry (IDs + counts, no text).

    * hma-27 note IDs (F8, F9, F10, F16, KN3 — plan §4.4): per-ID exact and
      hma-27 TP/FN/FP, plus a suite-wide counterfactual exact count with
      hma-27 stripped from both pred and gt (sensitivity to the D1-A call).
    * Court note IDs (F1, F2, KN1 — Bengaluru FCA s.7(2)(a) Family Court vs
      Magistrate delta): per-ID expected vs predicted court, plus whether the
      predicted court would pass if the expected forum were the other one.
    """
    by_id = {r["id"]: r for r in rows}
    hma27_notes: dict[str, Any] = {}
    for note_id in sorted(HMA27_NOTE_IDS):
        r = by_id.get(note_id)
        if r is None:
            hma27_notes[note_id] = {"present": False}
            continue
        in_gt = "hma-27" in r["gt"]
        in_pred = "hma-27" in r["pred"]
        hma27_notes[note_id] = {
            "present": True,
            "exact": r["exact"],
            "hma27_in_gt": in_gt,
            "hma27_in_pred": in_pred,
            "hma27_tp": bool(in_gt and in_pred),
            "hma27_fn": bool(in_gt and not in_pred),
            "hma27_fp": bool(in_pred and not in_gt),
        }
    exact_ignoring_hma27 = sum(
        1 for r in rows
        if (set(r["pred"]) - {"hma-27"}) == (set(r["gt"]) - {"hma-27"})
    )
    court_notes: dict[str, Any] = {}
    for note_id in sorted(COURT_NOTE_IDS):
        r = by_id.get(note_id)
        if r is None:
            court_notes[note_id] = {"present": False}
            continue
        expected = list(r["court_expected"])
        predicted = list(r["court_live"])
        alt_ok: bool | None = None
        if len(expected) == 1 and expected[0] in ("Family Court", "Magistrate"):
            alt = "Magistrate" if expected[0] == "Family Court" else "Family Court"
            alt_ok = alt in predicted
        court_notes[note_id] = {
            "present": True,
            "expected_court": expected,
            "predicted_court": predicted,
            "court_ok": r["court_ok"],
            "alt_forum_ok": alt_ok,
        }
    return {
        "hma27_note_ids": hma27_notes,
        "hma27_sensitivity": {
            "note_ids_exact": f"{sum(1 for v in hma27_notes.values() if v.get('exact'))}/{sum(1 for v in hma27_notes.values() if v.get('present'))}",
            "exact_count": sum(1 for r in rows if r["exact"]),
            "exact_count_ignoring_hma27": exact_ignoring_hma27,
            "hma27_tp": sum(1 for r in rows if "hma-27" in r["pred"] and "hma-27" in r["gt"]),
            "hma27_fn": sum(1 for r in rows if "hma-27" in r["gt"] and "hma-27" not in r["pred"]),
            "hma27_fp": sum(1 for r in rows if "hma-27" in r["pred"] and "hma-27" not in r["gt"]),
        },
        "court_note_ids": court_notes,
        "court_sensitivity": {
            "note_ids_court_ok": f"{sum(1 for v in court_notes.values() if v.get('court_ok'))}/{sum(1 for v in court_notes.values() if v.get('present'))}",
            "note_ids_alt_forum_ok": f"{sum(1 for v in court_notes.values() if v.get('alt_forum_ok'))}/{sum(1 for v in court_notes.values() if v.get('present'))}",
        },
    }


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


def _self_test() -> int:
    """CPU-only unit check of the V71-P7-1 scorer math on synthetic records.

    No torch, no model, no dataset I/O. Run:
    ``python -m tests.v7_backtest --self-test``
    Returns 0 on pass, 1 on any failure (prints each check).
    """
    failures: list[str] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        print(f"  {'PASS' if cond else 'FAIL'} {name} {detail}")
        if not cond:
            failures.append(name)

    # 1. hma-25 gated for no decree -> Fb 1, statutory gate, measured.
    r1 = compute_fb({
        "kept_ids": ["bnss-144"],
        "candidates_before_gate": ["hma-25", "bnss-144"],
        "dispositions": {
            "hma-25": {"status": "conditional", "reason_codes": ["lump_sum_without_decree_or_hma_proceeding"]},
            "bnss-144": {"status": "eligible", "reason_codes": ["subsistence_maintenance_bnss144"]},
        },
        "gated_out": ["hma-25: gated (pre_decree_without_hma)"],
    })
    check("fb_hma25_no_decree", r1["fb_count"] == 1 and r1["fb_measured"] is True, str(r1))

    # 2. hma-13 gated, divorce not asked -> Fb 1, mapping 3.
    r2 = compute_fb({
        "kept_ids": [],
        "candidates_before_gate": ["hma-13"],
        "dispositions": {"hma-13": {"status": "conditional", "reason_codes": ["divorce_not_expressly_asked"]}},
        "gated_out": ["hma-13: gated (divorce not asked)"],
    })
    check("fb_hma13_mapping3", r2["fb_count"] == 1 and r2["fb_by_mapping"] == {"hma_13_13b_divorce_not_asked": 1}, str(r2))

    # 3. Superseded hma-13 (13b eligible) is correct routing, NOT Fb.
    r3 = compute_fb({
        "kept_ids": ["hma-13b"],
        "candidates_before_gate": ["hma-13", "hma-13b"],
        "dispositions": {
            "hma-13": {"status": "inapplicable", "reason_codes": ["superseded_by_mutual_consent_13b"]},
            "hma-13b": {"status": "eligible", "reason_codes": ["mutual_consent_divorce"]},
        },
        "gated_out": [],
    })
    check("fb_superseded_not_counted", r3["fb_count"] == 0, str(r3))

    # 4. hma-27 D2 conditional (no HMA proceeding) -> Fb 1.
    r4 = compute_fb({
        "kept_ids": [],
        "dispositions": {"hma-27": {"status": "conditional", "reason_codes": ["d2_no_hma_pending_or_being_filed"]}},
        "gated_out": ["hma-27: gated (D2) — no HMA proceeding pending or being filed"],
    })
    check("fb_hma27_d2_via_dispositions", r4["fb_count"] == 1 and r4["fb_source"] == "dispositions_keys", str(r4))

    # 5. Old-format record (kept_ids only) -> Fb unmeasured, never a fake 0.
    r5 = compute_fb({"kept_ids": ["bnss-144"]})
    check("fb_unmeasured_old_format", r5["fb_count"] == 0 and r5["fb_measured"] is False, str(r5))

    # 6. Caps: raw 10.0 is capped by every binding condition.
    capped, caps = apply_gate_caps(10.0, fp_prose_n=1)
    check("cap_fp5", capped == 5.0 and "Fp>=1 -> <=5.0" in caps, f"{capped} {caps}")
    capped, _ = apply_gate_caps(10.0, fb_count=1, g12_verified=True, sealed_passed=True, confirmation_done=True)
    check("cap_fb9", capped == 9.0, f"{capped}")
    capped, _ = apply_gate_caps(10.0)  # defaults: G12/sealed/confirmation unverified
    check("cap_defaults9", capped == 9.0, f"{capped}")
    capped, _ = apply_gate_caps(10.0, errors=3, g12_verified=True, sealed_passed=True, confirmation_done=True)
    check("cap_errors5", capped == 5.0, f"{capped}")
    capped, caps = apply_gate_caps(10.0, g12_verified=True, sealed_passed=True, confirmation_done=True)
    check("cap_all_clear10", capped == 10.0 and caps == [], f"{capped} {caps}")
    capped, _ = apply_gate_caps(9.1, g12_verified=True, sealed_passed=True, confirmation_done=True)
    check("cap_raw_below_cap_kept", capped == 9.1, f"{capped}")

    # 7. Rating formula includes -0.5 * Fb: raw 10.0 with Fb=2 -> 9.0.
    raw = max(0.0, min(10.0, round(10.0 * 1.0 - 0.5 * 2 - 1.0 * 0, 1)))
    check("formula_minus_half_fb", raw == 9.0, f"{raw}")

    # 8. --strict: 191/230 strict kinds FAILS; 200/230 passes; per_cat_min fails.
    check("strict_191_fails", bool(strict_check("brutal", 230, 191, 1.0)), str(strict_check("brutal", 230, 191, 1.0)))
    check("strict_200_passes", strict_check("brutal", 230, 200, 1.0) == [], "")
    check("strict_percat_fails", bool(strict_check("brutal", 230, 230, 0.5)), "")

    # 9. Sealed diagnostics are aggregates only (IDs + counts, no text).
    diag = _sealed_diagnostics([
        {"id": "F8", "exact": True, "pred": ["hma-27"], "gt": ["hma-27"], "court_live": ["Family Court"], "court_expected": ["Family Court"], "court_ok": True},
        {"id": "F1", "exact": False, "pred": ["bnss-144"], "gt": ["bnss-144"], "court_live": ["Magistrate"], "court_expected": ["Family Court"], "court_ok": False},
    ])
    check("sealed_diag_hma27", diag["hma27_sensitivity"]["hma27_tp"] == 1, str(diag["hma27_sensitivity"]))
    check("sealed_diag_court_alt", diag["court_note_ids"]["F1"]["alt_forum_ok"] is True, str(diag["court_note_ids"]["F1"]))
    check("sealed_diag_no_text", "question" not in json.dumps(diag), "")

    print(f"SELF-TEST: {'PASS' if not failures else 'FAIL'} ({len(failures)} failures)")
    if failures:
        print("FAILED CHECKS: " + ", ".join(failures))
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Scorer-isolated backtest for LAYA v7.")
    parser.add_argument("--suite", choices=("16q", "brutal", "both", "all_with_sealed"), default="both")
    parser.add_argument("--mode", choices=("auto", "laya", "structured", "evidence"), default="laya")
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--misses", type=int, default=20)
    parser.add_argument("--strict", action="store_true",
                        help="Fail loudly unless Brutal-230 esc_kinds_strict >= 200/230 and per_cat_min >= 0.75.")
    parser.add_argument("--g12-verified", action="store_true",
                        help="Blind human legal rater (G12) has signed off Fp=0; otherwise the <=9.0 cap binds.")
    parser.add_argument("--sealed-passed", action="store_true",
                        help="Sealed Fresh-20 + Kannada-8 passed; otherwise the <=9.0 cap binds.")
    parser.add_argument("--confirmation-run", action="store_true",
                        help="This is the second independent confirmation re-run (G15); otherwise the <=9.0 cap binds.")
    parser.add_argument("--self-test", action="store_true",
                        help="CPU-only unit check of Fb / caps / strict math on synthetic records (no model, no datasets).")
    args = parser.parse_args()

    if args.self_test:
        return _self_test()

    out: dict[str, Any] = {}
    strict_failures: list[str] = []
    scored: list[tuple[str, dict[str, Any]]] = []

    def _score(name: str, result: dict[str, Any]) -> None:
        scored.append((name, result))
        if args.strict:
            n = result["n"]
            kinds_n = int(str(result["esc_kinds_strict"]).split("/")[0])
            strict_failures.extend(strict_check(name, n, kinds_n, float(result["per_cat_min"])))
            result["strict_pass"] = not strict_check(name, n, kinds_n, float(result["per_cat_min"]))
        else:
            result["strict_pass"] = None

    if args.suite in ("16q", "both", "all_with_sealed"):
        print("=== 16-Q ===")
        out["16q"] = score_dataset(
            _load_16q(),
            mode=args.mode,
            device=args.device,
            project_custody=False,
            legacy_16q_compat=True,
            print_misses=args.misses,
            g12_verified=args.g12_verified,
            sealed_passed=args.sealed_passed,
            confirmation_done=args.confirmation_run,
        )
        _score("16q", out["16q"])
        print(json.dumps(out["16q"], indent=2))
    if args.suite in ("brutal", "both", "all_with_sealed"):
        print("=== BRUTAL-230 (custody statutory_primary) ===")
        out["brutal_projected"] = score_dataset(
            _load_brutal(),
            mode=args.mode,
            device=args.device,
            project_custody=True,
            print_misses=args.misses,
            g12_verified=args.g12_verified,
            sealed_passed=args.sealed_passed,
            confirmation_done=args.confirmation_run,
        )
        _score("brutal", out["brutal_projected"])
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
            g12_verified=args.g12_verified,
            sealed_passed=args.sealed_passed,
            confirmation_done=args.confirmation_run,
            sealed_note_ids=True,
        )
        _score("sealed_fresh_20", out["sealed_fresh_20"])
        print(json.dumps(out["sealed_fresh_20"], indent=2))
        print("=== SEALED KANNADA-8 (aggregate only) ===")
        out["sealed_kannada_8"] = score_dataset(
            _load_sealed(SEALED_KN_PATH),
            mode=args.mode,
            device=args.device,
            project_custody=False,
            print_misses=0,
            blind_text=True,
            g12_verified=args.g12_verified,
            sealed_passed=args.sealed_passed,
            confirmation_done=args.confirmation_run,
            sealed_note_ids=True,
        )
        _score("sealed_kannada_8", out["sealed_kannada_8"])
        print(json.dumps(out["sealed_kannada_8"], indent=2))

    if args.strict and strict_failures:
        print("STRICT FAIL:")
        for failure in strict_failures:
            print(f"  {failure}")
        return 2
    if args.strict:
        print("STRICT PASS: esc_kinds_strict and per_cat_min bars met on every scored suite.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
