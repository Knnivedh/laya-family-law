"""Held-out validation harness for the LAYA v7.1 recall swarm (LANE 07).

README — how to run it
----------------------
From the repo root (``~/workspace/laya-v71-work``)::

    python3 tests/recall_eval.py
    python3 tests/recall_eval.py --misses 10 --failures-out results/recall_eval_failures.jsonl
    python3 tests/recall_eval.py --json-out results/recall_eval_summary.json
    python3 tests/recall_eval.py --suite kaanoon
    python3 tests/recall_eval.py --self-test        # CPU-only unit checks, no data

Kaanoon real-phrasing eval — CONTRACT R6 (2026-11-27 ~19:24 IST)
----------------------------------------------------------------
``--suite kaanoon`` scores the same evidence-mode pipeline on
``data/kaanoon_eval/heldout.jsonl`` — a FRESH held-out set built by Lane 11
from real Kaanoon family-law questions (target ~25–35 items, source URL
per item, annotated issues/facts + expected sections). R6: it is
EVALUATION ONLY. Lane 07 is the only lane that scores it, read-only
measurement, and NO lane (including Lane 07) may tune anything against it.
The Kaanoon number is reported as a SEPARATE number, labelled "Kaanoon
real-phrasing eval (n=..., never tuned against)" — never merged with the
synthetic validation-split number. The loader is schema-tolerant (accepts
``text`` or ``question``; expected sections from an explicit
``expected_sections`` / ``gt_sections`` / ``gt_ids`` / ``expected`` field
when present, else derived via Stage 2 from issues/facts; category from
``category`` / ``primary_issue`` / ``meta.cluster``; source URL kept per
row for audit). If Lane 11's file has not landed yet, ``--suite kaanoon``
exits with a loud "pending" message (exit 3) and no number.

What it measures
----------------
The pipeline is scored on ``data/synthetic_v7_1/validation.jsonl`` ONLY —
the held-out split named by ``data/synthetic_v7_1/manifest.json``. The split
size is read from the manifest (``n_validation``), never hardcoded; Lane 02
owns the corpus and the manifest, so a manifest/file count mismatch is
reported loudly in the summary rather than silently trusted.

* Predicted sections come from the real pipeline end to end:
  ``assess_v7_batch(..., mode="evidence", device="cpu")`` — the zero-model
  regex evidence path. CPU-only on this VM: no torch, no model weights.
* Expected sections are DERIVED, not read from the text: each record's
  ``issues`` / ``facts`` / ``enums`` are fed through the Stage 2 graph
  rules (``evaluate_stage2_v7``) exactly as the pipeline's own Stage 2
  would route them. Exact match means predicted section set == expected
  section set. Both sides use the same ``custody_vocab`` (default
  ``v3_bundled``, the ``assess_v7`` default), so a custody-vocab difference
  can never manufacture or hide a mismatch.

How to interpret the number
----------------------------
The validation-split exact rate is a PROXY, not the sealed number. It
measures recall on synthetic paraphrases generated from the same statutory
grammars as the training data — it says how well the pipeline generalises
across paraphrase templates, not how it does on independently authored
unseen questions. The user target (2026-11-27 ~19:19 IST) is MINIMUM 70%
exact on unseen law-related questions, measured on Sealed Fresh-20
(current 7/20 = 35%) and Sealed Kannada-8 (current 4/8 = 50%). The sealed
re-run happens ONLY on the RTX machine, never here, and no validation-split
number may ever be presented as a sealed number. A validation exact of
70%+ is necessary evidence toward the target, never proof of it.

Sealed guard
------------
This harness REFUSES to score anything from ``test-bank/sealed/``: any
input path containing ``sealed`` or ``test-bank`` (case-insensitive) exits
with an error before any data is read. Do not open ``test-bank/sealed/*.json``
beyond aggregates already logged in ``results/``.

Cross-lane contract (Lane 04 — model-side scoring)
--------------------------------------------------
Lane 04 owns the scoring function for the trained classifier; this file
owns the harness. The agreed shared signature (proposed here; Lane 04 to
confirm in the shared state file) is::

    predict_sections_from_stage1(issues, facts, enums, *, custody_vocab="v3_bundled") -> set[str]

where ``issues`` / ``facts`` / ``enums`` are the ``predict_text()`` outputs
from ``src/laya_v7_classifier.py`` (``{issue: {"intent": ...}}``,
``{fact: {"state": ...}}``, ``{head: {"value": ...}}`` — plain
intent/state/value strings are accepted too). It runs Stage 2 on the
predicted Stage 1 labels and returns the predicted section set. The pure
scorer both paths share is::

    score_predictions(records, predicted_sections, *, failure_tagger=None) -> dict

``records`` are normalised records from ``load_corpus_jsonl`` (Lane 04's
loader, reused here — not duplicated); ``predicted_sections`` is a list of
section sets aligned with ``records``. Lane 04 calls ``score_predictions``
with the sets from ``predict_sections_from_stage1``; this CLI calls it with
the sets from the evidence-mode pipeline. One scorer, one number.

Per-cause failure tags (Lane 01 hook)
-------------------------------------
``score_predictions`` tags every non-exact row with a failure cause. The
built-in tagger is deliberately coarse (``silent``, ``missing_only``,
``extra_only``, ``missing_and_extra``, ``empty_expected_nonempty_pred``);
Lane 01's taxonomy plugs in via ``register_failure_tagger(fn)`` or the
``--tagger module:function`` CLI option, where ``fn(record, expected,
predicted) -> str``. ``--failures-out`` writes one JSONL row per non-exact
record (id, lang, cluster, expected, predicted, tag) for Lane 01's
breakdown. Tags never change the score — they only classify misses.

Conventions reused (not duplicated) from ``tests/v7_backtest.py``:
``wilson_ci`` is imported from that module; exact / micro-P/R/F1 follow its
``_pr`` convention (TP = pred & gt, FP = pred - gt, FN = gt - pred).
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.laya_v7 import assess_v7_batch  # noqa: E402
from src.laya_v7_classifier import (  # noqa: E402
    ENUMS,
    FACT_STATES,
    FACTS,
    ISSUE_INTENTS,
    ISSUES,
    load_corpus_jsonl,
)
from src.laya_v7_graph import evaluate_stage2_v7  # noqa: E402
from src.laya_v7_schema import IssueEvidence  # noqa: E402

# Reuse the honest scorer's Wilson CI (convention, not a copy).
_spec = importlib.util.spec_from_file_location(
    "_v7_backtest_wilson", REPO_ROOT / "tests" / "v7_backtest.py"
)
_v7_backtest = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_v7_backtest)  # type: ignore[union-attr]
wilson_ci = _v7_backtest.wilson_ci

DEFAULT_MANIFEST = REPO_ROOT / "data" / "synthetic_v7_1" / "manifest.json"
DEFAULT_VALIDATION = REPO_ROOT / "data" / "synthetic_v7_1" / "validation.jsonl"
DEFAULT_KAANOON = REPO_ROOT / "data" / "kaanoon_eval" / "heldout.jsonl"
CUSTODY_VOCAB_DEFAULT = "v3_bundled"

# ---------------------------------------------------------------------------
# Sealed guard
# ---------------------------------------------------------------------------

FORBIDDEN_PATH_SUBSTRINGS = ("sealed", "test-bank")


def guard_path(path: str | Path, *, what: str = "input") -> Path:
    """Refuse any path that could touch the sealed test banks.

    Hard rule: if the resolved path contains "sealed" or "test-bank"
    (case-insensitive), exit with an error before any data is read.
    """
    p = Path(path)
    lowered = str(p.resolve()).lower() if p.exists() else str(p).lower()
    for bad in FORBIDDEN_PATH_SUBSTRINGS:
        if bad in lowered:
            print(
                f"ERROR: refusing to score {what} path containing "
                f"'{bad}': {path}\n"
                f"  Sealed banks (test-bank/sealed/) are never scored by this "
                f"harness; the sealed re-run happens only on the RTX machine.",
                file=sys.stderr,
            )
            raise SystemExit(2)
    return p


# ---------------------------------------------------------------------------
# Stage 1 -> Stage 2 bridge (shared with Lane 04)
# ---------------------------------------------------------------------------

def _normalise_stage1_value(value: Any) -> str:
    """Accept a predict_text()-style dict, a plain string, or a bool."""
    if isinstance(value, dict):
        for key in ("intent", "state", "value"):
            if key in value:
                return str(value[key])
        return "uncertain"
    if isinstance(value, bool):
        return "supported" if value else "denied"
    return str(value)


def predict_sections_from_stage1(
    issues: dict[str, Any],
    facts: dict[str, Any],
    enums: dict[str, Any] | None = None,
    *,
    custody_vocab: str = CUSTODY_VOCAB_DEFAULT,
) -> set[str]:
    """Run Stage 2 graph rules on Stage 1 labels; return predicted sections.

    Shared signature with Lane 04 (see module docstring): Lane 04 passes
    ``predict_text()`` outputs; this harness passes the same function the
    record's own issues/facts/enums to derive the EXPECTED sections. Both
    sides route through the identical Stage 2 code, so the comparison is
    Stage 1 extraction quality only — never a Stage 2 difference.
    """
    issue_evs: dict[str, IssueEvidence] = {}
    for name, val in (issues or {}).items():
        intent = _normalise_stage1_value(val)
        if intent not in ("requested", "incidental", "denied", "uncertain"):
            intent = "uncertain"
        issue_evs[name] = IssueEvidence(
            issue=name, intent=intent, source="recall_eval", confidence=1.0
        )
    stage2_facts: dict[str, Any] = {}
    for name, val in (facts or {}).items():
        stage2_facts[name] = _normalise_stage1_value(val)
    for head, val in (enums or {}).items():
        norm = _normalise_stage1_value(val)
        # COORD-FIX (Lane 09 verifier finding, confirmed in code): the corpus
        # schema stores claimant_sex as "M"/"F"/"U", but evaluate_stage2_v7
        # compares against "male"/"female" (the values the live extractor
        # produces, src/laya_v7_evidence.py). Passing "M" raw made
        # sex == "male" False and sex != "male" True, so male records got
        # female-gated sections in the EXPECTED set that the predicted side
        # (correctly male-gated) never emits — systematic false misses.
        # Map exactly as data/kaanoon_eval/build_heldout.py::validate_expected.
        if head == "claimant_sex":
            norm = {"M": "male", "F": "female", "U": "unknown"}.get(
                norm, norm
            )
        stage2_facts[head] = norm
    # Stage 2 reads negated/denied issue sets from the facts dict; derive
    # them from the issue intents exactly as the extractor does for
    # grounded negations (evidence.py builds negated_issues the same way).
    denied = {name for name, ev in issue_evs.items() if ev.intent == "denied"}
    stage2_facts["negated_issues"] = set(denied)
    stage2_facts["denied_issues"] = set(denied)
    decision = evaluate_stage2_v7(issue_evs, stage2_facts, custody_vocab=custody_vocab)
    return set(decision["kept_ids"])


def expected_sections(
    record: dict[str, Any], *, custody_vocab: str = CUSTODY_VOCAB_DEFAULT
) -> set[str]:
    """Derive a record's expected sections from its issues/facts/enums.

    The record's own labels are the ground truth for Stage 1; Stage 2 is
    applied mechanically. A record whose labels route to no section expects
    the empty set (e.g. out-of-scope / no-dispute records).
    """
    return predict_sections_from_stage1(
        record.get("issues") or {},
        record.get("facts") or {},
        record.get("enums") or {},
        custody_vocab=custody_vocab,
    )


# ---------------------------------------------------------------------------
# Failure tagging (Lane 01 hook)
# ---------------------------------------------------------------------------

def default_failure_tagger(
    record: dict[str, Any], expected: set[str], predicted: set[str]
) -> str:
    """Coarse built-in cause tag. Lane 01 replaces this via the hook."""
    if expected and not predicted:
        return "silent"
    if not expected and predicted:
        return "empty_expected_nonempty_pred"
    if not expected and not predicted:
        return "exact_empty"
    missing = expected - predicted
    extra = predicted - expected
    if missing and extra:
        return "missing_and_extra"
    if missing:
        return "missing_only"
    return "extra_only"


_FAILURE_TAGGER: Callable[[dict[str, Any], set[str], set[str]], str] = (
    default_failure_tagger
)


def register_failure_tagger(
    fn: Callable[[dict[str, Any], set[str], set[str]], str]
) -> None:
    """Plug in Lane 01's per-cause taxonomy. ``fn(record, expected,
    predicted) -> str``. The tag classifies a miss; it never changes the
    score."""
    global _FAILURE_TAGGER
    _FAILURE_TAGGER = fn


def load_tagger(dotted: str) -> Callable[[dict[str, Any], set[str], set[str]], str]:
    """Load a tagger as ``module:function`` (importable from the repo root)."""
    if ":" not in dotted:
        raise ValueError("--tagger must be 'module:function'")
    mod_name, fn_name = dotted.rsplit(":", 1)
    module = importlib.import_module(mod_name)
    fn = getattr(module, fn_name)
    if not callable(fn):
        raise ValueError(f"--tagger {dotted!r} is not callable")
    return fn


# ---------------------------------------------------------------------------
# Pure scorer (shared by the evidence CLI path and Lane 04's model path)
# ---------------------------------------------------------------------------

ISSUE_NAMES = (
    "maintenance", "custody", "residence", "divorce", "stridhan",
    "joint_property", "violence", "dv_compensation", "restitution",
    "birth_certificate", "procedure",
)


def score_predictions(
    records: list[dict[str, Any]],
    predicted_sections: list[set[str]],
    *,
    failure_tagger: Callable[[dict[str, Any], set[str], set[str]], str] | None = None,
) -> dict[str, Any]:
    """Score predicted section sets against Stage 2-derived expected sets.

    Pure function: no I/O, no torch. Returns the summary dict plus per-row
    detail under ``rows``. Exact = predicted set == expected set. A record
    carrying ``_expected_sections`` (set/list, set by the Kaanoon loader
    when the item has an explicit human-annotated expected set) uses that
    instead of the Stage 2 derivation; every other record derives its
    expected set via ``expected_sections``.
    """
    if len(records) != len(predicted_sections):
        raise ValueError(
            f"records ({len(records)}) and predicted_sections "
            f"({len(predicted_sections)}) differ in length"
        )
    tagger = failure_tagger or _FAILURE_TAGGER
    rows: list[dict[str, Any]] = []
    tot_tp = tot_fp = tot_fn = 0
    sec_fp: Counter[str] = Counter()
    sec_fn: Counter[str] = Counter()
    lang_stats: dict[str, list[bool]] = defaultdict(list)
    issue_stats: dict[str, list[bool]] = defaultdict(list)
    cluster_stats: dict[str, list[bool]] = defaultdict(list)
    tag_counts: Counter[str] = Counter()

    for record, predicted in zip(records, predicted_sections):
        if record.get("_expected_sections") is not None:
            expected = set(record["_expected_sections"])
        else:
            expected = expected_sections(record)
        predicted = set(predicted)
        exact = predicted == expected
        tp = len(predicted & expected)
        fp = len(predicted - expected)
        fn = len(expected - predicted)
        tot_tp += tp
        tot_fp += fp
        tot_fn += fn
        for s in predicted - expected:
            sec_fp[s] += 1
        for s in expected - predicted:
            sec_fn[s] += 1
        lang = str(record.get("lang") or "unknown")
        lang_stats[lang].append(exact)
        for issue in ISSUE_NAMES:
            if (record.get("issues") or {}).get(issue) == "requested":
                issue_stats[issue].append(exact)
        cluster = str((record.get("meta") or {}).get("cluster") or "unknown")
        cluster_stats[cluster].append(exact)
        tag = "exact" if exact else tagger(record, expected, predicted)
        tag_counts[tag] += 1
        rows.append({
            "id": record.get("id"),
            "lang": lang,
            "cluster": cluster,
            "source_url": (record.get("meta") or {}).get("source_url") or "",
            "exact": exact,
            "expected": sorted(expected),
            "predicted": sorted(predicted),
            "missing": sorted(expected - predicted),
            "extra": sorted(predicted - expected),
            "tag": tag,
        })

    n = len(rows)
    n_exact = sum(1 for r in rows if r["exact"])
    silent = sum(1 for r in rows if r["expected"] and not r["predicted"])
    micro_p = tot_tp / (tot_tp + tot_fp) if (tot_tp + tot_fp) else 0.0
    micro_r = tot_tp / (tot_tp + tot_fn) if (tot_tp + tot_fn) else 0.0
    micro_f1 = (2 * micro_p * micro_r / (micro_p + micro_r)) if (micro_p + micro_r) else 0.0

    def _rate(stats: dict[str, list[bool]]) -> dict[str, str]:
        return {
            k: f"{sum(v)}/{len(v)} ({sum(v) / len(v):.3f})"
            for k, v in sorted(stats.items())
        }

    return {
        "n": n,
        "exact_count": n_exact,
        "exact_rate": round(n_exact / n, 4) if n else 0.0,
        "wilson_95": list(wilson_ci(n_exact, n)),
        "micro_p": round(micro_p, 4),
        "micro_r": round(micro_r, 4),
        "micro_f1": round(micro_f1, 4),
        "tp_fp_fn": [tot_tp, tot_fp, tot_fn],
        "silent": silent,
        "per_language_exact": _rate(lang_stats),
        "per_issue_exact_requested": _rate(issue_stats),
        "per_cluster_exact": _rate(cluster_stats),
        "failure_tags": dict(tag_counts),
        "top_missing_sections": dict(sec_fn.most_common(12)),
        "top_extra_sections": dict(sec_fp.most_common(12)),
        "rows": rows,
    }


# ---------------------------------------------------------------------------
# Evidence-mode run
# ---------------------------------------------------------------------------

def load_split(
    manifest_path: str | Path, validation_path: str | Path
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    """Load the manifest + validation split. Split size comes from the
    manifest (``n_validation``), never hardcoded. Returns
    (records, manifest, loader_report)."""
    manifest_path = guard_path(manifest_path, what="manifest")
    validation_path = guard_path(validation_path, what="validation split")
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    records, report = load_corpus_jsonl(validation_path)
    # load_corpus_jsonl normalises to the Lane 02 schema and drops the
    # builder's "meta" block; re-attach it (cluster etc.) by id so the
    # per-cluster breakdown and Lane 01's failure file carry it.
    meta_by_id: dict[str, dict[str, Any]] = {}
    with Path(validation_path).open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(raw.get("id"), str):
                meta_by_id[raw["id"]] = raw.get("meta") or {}
    for rec in records:
        rec["meta"] = meta_by_id.get(rec["id"], {})
    return records, manifest, report


def run_evidence_eval(
    *,
    manifest_path: str | Path = DEFAULT_MANIFEST,
    validation_path: str | Path = DEFAULT_VALIDATION,
    custody_vocab: str = CUSTODY_VOCAB_DEFAULT,
    limit: int | None = None,
    failure_tagger: Callable[[dict[str, Any], set[str], set[str]], str] | None = None,
) -> dict[str, Any]:
    """Score the evidence-mode pipeline on the validation split (CPU-only).

    Returns the summary dict (``score_predictions`` output plus run
    metadata). Raises SystemExit(2) on a sealed/test-bank path.
    """
    records, manifest, report = load_split(manifest_path, validation_path)
    manifest_n = int(manifest.get("n_validation") or 0)
    if limit is not None:
        records = records[:limit]
    if manifest_n and len(records) != manifest_n and limit is None:
        print(
            f"WARNING: manifest n_validation={manifest_n} but validation file "
            f"has {len(records)} records (loader skipped "
            f"{report.get('n_skipped', 0)} lines). Lane 02 may be mid-expansion; "
            f"scoring the {len(records)} records actually present. Re-run the "
            f"leakage gate after any corpus change.",
            file=sys.stderr,
        )
    predicted_recs, wall_s = assess_v7_batch(
        [r["text"] for r in records],
        mode="evidence",
        device="cpu",
        custody_vocab=custody_vocab,
        with_prose=False,
        batch_size=16,
    )
    extractor_modes = Counter(r.get("extractor_mode") for r in predicted_recs)
    if set(extractor_modes) != {"evidence"}:
        print(
            f"WARNING: expected every record in mode=evidence, got "
            f"extractor modes {dict(extractor_modes)} — the method label "
            f"below is NOT a pure evidence-mode number.",
            file=sys.stderr,
        )
    predicted = [set(r["kept_ids"]) for r in predicted_recs]
    summary = score_predictions(records, predicted, failure_tagger=failure_tagger)
    summary["split"] = {
        "validation_path": str(validation_path),
        "n_manifest": manifest_n,
        "n_scored": len(records),
        "manifest_seed": manifest.get("seed"),
        "manifest_method": manifest.get("method"),
        "loader_skipped_lines": report.get("n_skipped", 0),
    }
    summary["method"] = {
        "pipeline": "assess_v7_batch",
        "mode": "evidence",
        "device": "cpu",
        "torch": False,
        "custody_vocab": custody_vocab,
        "extractor_modes": dict(extractor_modes),
        "total_wall_s": round(wall_s, 3),
        "mean_latency_s": round(wall_s / max(len(records), 1), 4),
    }
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(REPO_ROOT), capture_output=True, text=True, check=True,
        ).stdout.strip()
    except Exception:
        commit = "unknown (git rev-parse failed)"
    summary["commit"] = commit
    return summary


# ---------------------------------------------------------------------------
# Kaanoon real-phrasing eval — CONTRACT R6 (evaluation only, never tuned)
# ---------------------------------------------------------------------------

KAANOON_EXPECTED_KEYS = ("expected_sections", "gt_sections", "gt_ids", "expected")


def _kaanoon_label(mapping: dict[str, Any], key: str, allowed: tuple[str, ...], default: str) -> str:
    """Normalise one label against the Lane 02 schema; unknown -> default."""
    raw = (mapping or {}).get(key)
    if raw is None:
        return default
    value = _normalise_stage1_value(raw)
    return value if value in allowed else default


def load_kaanoon_split(path: str | Path) -> list[dict[str, Any]]:
    """Load Lane 11's Kaanoon held-out set (tolerant of its exact schema).

    Accepts JSONL (one record per line) or a top-level JSON array. Per
    record accepts ``text`` or ``question``; issues/facts/enums normalised
    against the Lane 02 schema (missing -> "uncertain" / "unknown" /
    U-other-present); category from ``category`` / ``primary_issue`` /
    ``meta.cluster``; source URL from ``source_url`` / ``source`` /
    ``meta.source_url``. Expected sections: an explicit
    ``expected_sections`` / ``gt_sections`` / ``gt_ids`` / ``expected``
    list is honoured as-is (stored as ``_expected_sections``); when no
    explicit field is present, the expected set is derived via Stage 2
    from the record's issues/facts, exactly like the synthetic split.

    Raises FileNotFoundError when Lane 11's file has not landed yet.
    The sealed/test-bank guard applies here too.
    """
    path = guard_path(path, what="kaanoon held-out set")
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"Kaanoon held-out set not found: {p} "
            f"(Lane 11 has not landed data/kaanoon_eval/heldout.jsonl yet)"
        )
    raw_text = p.read_text(encoding="utf-8").strip()
    raw_items: list[dict[str, Any]] = []
    if raw_text.startswith("["):
        data = json.loads(raw_text)
        raw_items = data if isinstance(data, list) else [data]
    else:
        for line in raw_text.splitlines():
            line = line.strip()
            if line:
                raw_items.append(json.loads(line))
    records: list[dict[str, Any]] = []
    for idx, raw in enumerate(raw_items):
        if not isinstance(raw, dict):
            continue
        text = (raw.get("text") or raw.get("question") or "").strip()
        if not text:
            continue
        raw_issues = raw.get("issues") or {}
        raw_facts = raw.get("facts") or {}
        raw_enums = raw.get("enums") or {}
        issues = {
            name: _kaanoon_label(raw_issues, name, ISSUE_INTENTS, "uncertain")
            for name in ISSUES
        }
        facts = {
            name: _kaanoon_label(raw_facts, name, FACT_STATES, "unknown")
            for name in FACTS
        }
        enums = {
            head: _kaanoon_label(raw_enums, head, tuple(values), default)
            for head, values, default in (
                ("claimant_sex", tuple(ENUMS["claimant_sex"]), "U"),
                ("claimant_role", tuple(ENUMS["claimant_role"]), "other"),
                ("modality_time", tuple(ENUMS["modality_time"]), "present"),
            )
        }
        meta = raw.get("meta") or {}
        category = (
            raw.get("category") or raw.get("primary_issue")
            or meta.get("cluster") or "kaanoon"
        )
        source_url = (
            raw.get("source_url") or raw.get("source")
            or meta.get("source_url") or ""
        )
        expected: set[str] | None = None
        for key in KAANOON_EXPECTED_KEYS:
            if key in raw and isinstance(raw[key], list):
                expected = {str(s) for s in raw[key]}
                break
        records.append({
            "id": str(raw.get("id") or f"kaanoon-{idx + 1}"),
            "lang": str(raw.get("lang") or "en").lower(),
            "text": text,
            "issues": issues,
            "facts": facts,
            "enums": enums,
            "spans": raw.get("spans") or [],
            "clauses": [],
            "meta": {"cluster": str(category), "source_url": str(source_url)},
            "_expected_sections": expected,
        })
    return records


def run_kaanoon_eval(
    *,
    kaanoon_path: str | Path = DEFAULT_KAANOON,
    custody_vocab: str = CUSTODY_VOCAB_DEFAULT,
    failure_tagger: Callable[[dict[str, Any], set[str], set[str]], str] | None = None,
) -> dict[str, Any]:
    """Score the evidence-mode pipeline on the Kaanoon held-out set.

    Same pipeline and Stage 2 rules as the synthetic split; the number is
    reported separately and must never be merged with the synthetic
    validation number. CONTRACT R6: read-only measurement — this function
    never writes to the Kaanoon set and nothing is tuned against it.
    Raises FileNotFoundError when Lane 11's file has not landed yet.
    """
    records = load_kaanoon_split(kaanoon_path)
    if not records:
        raise ValueError(f"No scorable records in Kaanoon set: {kaanoon_path}")
    predicted_recs, wall_s = assess_v7_batch(
        [r["text"] for r in records],
        mode="evidence",
        device="cpu",
        custody_vocab=custody_vocab,
        with_prose=False,
        batch_size=16,
    )
    extractor_modes = Counter(r.get("extractor_mode") for r in predicted_recs)
    if set(extractor_modes) != {"evidence"}:
        print(
            f"WARNING: expected every record in mode=evidence, got "
            f"extractor modes {dict(extractor_modes)} — the method label "
            f"below is NOT a pure evidence-mode number.",
            file=sys.stderr,
        )
    predicted = [set(r["kept_ids"]) for r in predicted_recs]
    summary = score_predictions(records, predicted, failure_tagger=failure_tagger)
    summary["split"] = {
        "kaanoon_path": str(kaanoon_path),
        "n_scored": len(records),
        "n_with_source_url": sum(
            1 for r in records if (r.get("meta") or {}).get("source_url")
        ),
        "n_expected_explicit": sum(
            1 for r in records if r.get("_expected_sections") is not None
        ),
        "n_expected_derived": sum(
            1 for r in records if r.get("_expected_sections") is None
        ),
    }
    summary["method"] = {
        "pipeline": "assess_v7_batch",
        "mode": "evidence",
        "device": "cpu",
        "torch": False,
        "custody_vocab": custody_vocab,
        "extractor_modes": dict(extractor_modes),
        "total_wall_s": round(wall_s, 3),
        "mean_latency_s": round(wall_s / max(len(records), 1), 4),
    }
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(REPO_ROOT), capture_output=True, text=True, check=True,
        ).stdout.strip()
    except Exception:
        commit = "unknown (git rev-parse failed)"
    summary["commit"] = commit
    summary["contract"] = (
        "R6 evaluation-only: read-only measurement, never tuned against"
    )
    return summary


def print_kaanoon_summary(summary: dict[str, Any]) -> None:
    """Print the Kaanoon summary block — a SEPARATE number from synthetic."""
    split = summary["split"]
    method = summary["method"]
    lo, hi = summary["wilson_95"]
    print("=== KAANOON REAL-PHRASING EVAL (never tuned against) ===")
    print(f"source:       {split['kaanoon_path']} "
          f"(n={split['n_scored']}, source_url on "
          f"{split['n_with_source_url']}/{split['n_scored']}, expected "
          f"explicit {split['n_expected_explicit']} / derived "
          f"{split['n_expected_derived']})")
    print(f"method:       mode={method['mode']} (zero-model regex evidence, "
          f"CPU-only, no torch) + Stage 2 graph rules "
          f"(custody_vocab={method['custody_vocab']}); "
          f"extractor_modes={method['extractor_modes']}; "
          f"wall {method['total_wall_s']}s, mean {method['mean_latency_s']}s/Q")
    print(f"commit:       {summary['commit']}")
    print(f"exact:        {summary['exact_count']}/{summary['n']} "
          f"({summary['exact_rate']:.1%})  Wilson 95% CI [{lo:.4f}, {hi:.4f}]")
    print(f"micro P/R/F1: {summary['micro_p']:.4f} / {summary['micro_r']:.4f} / "
          f"{summary['micro_f1']:.4f}  (TP/FP/FN {summary['tp_fp_fn']})")
    print(f"silent:       {summary['silent']} "
          f"(expected non-empty, predicted empty)")
    print(f"per-language: " + "; ".join(
        f"{k} {v}" for k, v in summary["per_language_exact"].items()))
    print(f"per-category: " + "; ".join(
        f"{k} {v}" for k, v in summary["per_cluster_exact"].items()))
    print(f"failure tags: {summary['failure_tags']}")
    print(f"top missing:  {summary['top_missing_sections']}")
    print(f"top extra:    {summary['top_extra_sections']}")
    print("CONTRACT R6: Kaanoon real-phrasing eval — evaluation only, "
          "read-only measurement, never tuned against. This number is "
          "SEPARATE from the synthetic validation-split number; do not "
          "merge them, and do not present either as the sealed Fresh-20 / "
          "Kannada-8 number (sealed re-runs happen only on the RTX machine).")


def print_summary(summary: dict[str, Any]) -> None:
    """Print the one honest summary block."""
    split = summary["split"]
    method = summary["method"]
    lo, hi = summary["wilson_95"]
    print("=== RECALL EVAL — LAYA v7.1 validation split (PROXY, not sealed) ===")
    print(f"split:        {split['validation_path']} "
          f"(n_scored={split['n_scored']}, manifest n_validation={split['n_manifest']}, "
          f"seed {split['manifest_seed']})")
    print(f"method:       mode={method['mode']} (zero-model regex evidence, "
          f"CPU-only, no torch) + Stage 2 graph rules "
          f"(custody_vocab={method['custody_vocab']}); "
          f"extractor_modes={method['extractor_modes']}; "
          f"wall {method['total_wall_s']}s, mean {method['mean_latency_s']}s/Q")
    print(f"commit:       {summary['commit']}")
    print(f"exact:        {summary['exact_count']}/{summary['n']} "
          f"({summary['exact_rate']:.1%})  Wilson 95% CI [{lo:.4f}, {hi:.4f}]")
    print(f"micro P/R/F1: {summary['micro_p']:.4f} / {summary['micro_r']:.4f} / "
          f"{summary['micro_f1']:.4f}  (TP/FP/FN {summary['tp_fp_fn']})")
    print(f"silent:       {summary['silent']} "
          f"(expected non-empty, predicted empty)")
    print(f"per-language: " + "; ".join(
        f"{k} {v}" for k, v in summary["per_language_exact"].items()))
    print("per-issue exact (issue requested):")
    for issue, rate in summary["per_issue_exact_requested"].items():
        print(f"  {issue}: {rate}")
    print(f"per-cluster:  " + "; ".join(
        f"{k} {v}" for k, v in summary["per_cluster_exact"].items()))
    print(f"failure tags: {summary['failure_tags']}")
    print(f"top missing:  {summary['top_missing_sections']}")
    print(f"top extra:    {summary['top_extra_sections']}")
    print("WARNING: validation-split exact is a PROXY for unseen-question "
          "recall, not the sealed number. The user target is >=70% exact on "
          "unseen law questions (Sealed Fresh-20 7/20, Kannada-8 4/8); the "
          "sealed re-run happens only on the RTX machine. Do not present "
          "this number as a sealed result.")


def _self_test() -> int:
    """CPU-only unit checks of the harness math (no data files, no torch)."""
    failures: list[str] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        print(f"  {'PASS' if cond else 'FAIL'} {name} {detail}")
        if not cond:
            failures.append(name)

    # 1. Expected sections: maintenance requested + money supported -> bnss-144.
    rec_maint = {
        "id": "T1", "lang": "en", "text": "x",
        "issues": {"maintenance": "requested"},
        "facts": {"money_fact": "supported", "in_scope": "supported"},
        "enums": {"claimant_sex": "F", "claimant_role": "spouse", "modality_time": "present"},
    }
    exp = expected_sections(rec_maint)
    check("expected_maint_bnss144", "bnss-144" in exp, str(sorted(exp)))

    # 2. Out-of-scope record expects the empty set.
    rec_oos = {
        "id": "T2", "lang": "en", "text": "x",
        "issues": {"maintenance": "uncertain"},
        "facts": {"in_scope": "denied"},
        "enums": {"claimant_sex": "F", "claimant_role": "spouse", "modality_time": "present"},
    }
    check("expected_oos_empty", expected_sections(rec_oos) == set(),
          str(sorted(expected_sections(rec_oos))))

    # 3. predict_text()-style dicts work through the shared signature.
    exp3 = predict_sections_from_stage1(
        {"maintenance": {"intent": "requested"}},
        {"money_fact": {"state": "supported"}, "in_scope": {"state": "supported"}},
        {"claimant_sex": {"value": "F"}},
    )
    check("shared_sig_predict_text_style", "bnss-144" in exp3, str(sorted(exp3)))

    # 4. Scorer math on toy rows: 1 exact / 2, micro P/R/F1, silent count.
    toy = [
        {"id": "A", "lang": "en", "text": "x",
         "issues": {"maintenance": "requested"}, "facts": {"money_fact": "supported", "in_scope": "supported"},
         "enums": {"claimant_sex": "F", "claimant_role": "spouse", "modality_time": "present"}, "meta": {"cluster": "core"}},
        {"id": "B", "lang": "kn", "text": "x",
         "issues": {"maintenance": "requested"}, "facts": {"money_fact": "supported", "in_scope": "supported"},
         "enums": {"claimant_sex": "F", "claimant_role": "spouse", "modality_time": "present"}, "meta": {"cluster": "core"}},
    ]
    # A: exact (bnss-144 + pwdva-20 predicted — money_fact supported with a
    # female spouse claimant routes to both under Stage 2). B: silent.
    s = score_predictions(toy, [{"bnss-144", "pwdva-20"}, set()])
    check("scorer_exact_1_of_2", s["exact_count"] == 1 and s["n"] == 2, str(s["exact_count"]))
    check("scorer_silent_1", s["silent"] == 1, str(s["silent"]))
    check("scorer_tags", s["failure_tags"] == {"exact": 1, "silent": 1}, str(s["failure_tags"]))
    check("scorer_per_lang", s["per_language_exact"]["en"].startswith("1/1") and s["per_language_exact"]["kn"].startswith("0/1"),
          str(s["per_language_exact"]))

    # 5. Custom tagger hook is honoured.
    register_failure_tagger(lambda rec, e, p: "lane01-taxonomy")
    s2 = score_predictions(toy, [{"bnss-144", "pwdva-20"}, set()])
    check("tagger_hook", s2["failure_tags"] == {"exact": 1, "lane01-taxonomy": 1},
          str(s2["failure_tags"]))
    register_failure_tagger(default_failure_tagger)

    # 6. Sealed guard refuses sealed / test-bank paths.
    for bad in ("test-bank/sealed/fresh-20.json", "data/sealed/x.jsonl", "TEST-BANK/sealed/kannada-8.json"):
        try:
            guard_path(bad)
            check(f"guard_refuses_{bad}", False, "no error raised")
        except SystemExit as exc:
            check(f"guard_refuses_{bad}", exc.code == 2, f"exit={exc.code}")

    # 7. Length mismatch raises instead of silently misaligning.
    try:
        score_predictions(toy, [{"bnss-144"}])
        check("length_mismatch_raises", False, "no error raised")
    except ValueError:
        check("length_mismatch_raises", True)

    # 8. Kaanoon loader: tolerant schema (question field, explicit expected,
    # category, source_url) + Stage 2 derivation fallback.
    import tempfile
    k_records = [
        {"id": "K1", "question": "My husband does not pay maintenance.",
         "issues": {"maintenance": "requested"},
         "facts": {"money_fact": "supported", "in_scope": "supported"},
         "enums": {"claimant_sex": "F", "claimant_role": "spouse"},
         "category": "maintenance",
         "source_url": "https://example.invalid/kaanoon/k1",
         "expected_sections": ["bnss-144", "pwdva-20"]},
        {"id": "K2", "text": "I want a divorce by mutual consent.",
         "issues": {"divorce": "requested"},
         "facts": {"divorce_asked": "supported", "mutual_consent": "supported",
                   "in_scope": "supported"},
         "enums": {"claimant_sex": "F", "claimant_role": "spouse"},
         "category": "divorce"},
    ]
    with tempfile.NamedTemporaryFile(
        "w", suffix=".jsonl", delete=False, encoding="utf-8"
    ) as tf:
        for r in k_records:
            tf.write(json.dumps(r) + "\n")
        k_path = tf.name
    loaded = load_kaanoon_split(k_path)
    check("kaanoon_loads_2", len(loaded) == 2, f"n={len(loaded)}")
    check("kaanoon_question_field", loaded[0]["text"].startswith("My husband"),
          loaded[0]["text"][:20])
    check("kaanoon_explicit_expected",
          loaded[0].get("_expected_sections") == {"bnss-144", "pwdva-20"},
          str(loaded[0].get("_expected_sections")))
    check("kaanoon_derived_expected_is_none",
          loaded[1].get("_expected_sections") is None, "")
    check("kaanoon_category_and_url",
          loaded[0]["meta"]["cluster"] == "maintenance"
          and loaded[0]["meta"]["source_url"] == "https://example.invalid/kaanoon/k1",
          str(loaded[0]["meta"]))
    # Explicit expected is honoured by the scorer (K1 exact on match).
    ks = score_predictions(loaded, [{"bnss-144", "pwdva-20"}, {"hma-13b"}])
    check("kaanoon_explicit_scored", ks["exact_count"] == 2, str(ks["exact_count"]))
    check("kaanoon_per_category",
          ks["per_cluster_exact"].get("maintenance", "").startswith("1/1")
          and ks["per_cluster_exact"].get("divorce", "").startswith("1/1"),
          str(ks["per_cluster_exact"]))
    # Missing file -> FileNotFoundError (CLI turns this into PENDING, exit 3).
    try:
        load_kaanoon_split("/tmp/definitely-not-here-kaanoon-heldout.jsonl")
        check("kaanoon_missing_raises", False, "no error raised")
    except FileNotFoundError:
        check("kaanoon_missing_raises", True)
    # Guard applies to the kaanoon path too.
    try:
        load_kaanoon_split("test-bank/sealed/heldout.jsonl")
        check("kaanoon_guard_refuses_sealed", False, "no error raised")
    except SystemExit as exc:
        check("kaanoon_guard_refuses_sealed", exc.code == 2, f"exit={exc.code}")

    print(f"SELF-TEST: {'PASS' if not failures else 'FAIL'} ({len(failures)} failures)")
    if failures:
        print("FAILED CHECKS: " + ", ".join(failures))
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="LAYA v7.1 recall harness: score the evidence-mode pipeline "
                    "on a held-out set ONLY (synthetic validation split by default; "
                    "Lane 11's Kaanoon real-phrasing set with --suite kaanoon). "
                    "Never sealed.",
        epilog="The validation-split exact rate is a PROXY for unseen-question "
               "recall, not the sealed Fresh-20 / Kannada-8 number. The Kaanoon "
               "number is a separate real-phrasing number under CONTRACT R6 "
               "(evaluation only, never tuned against). Sealed re-runs happen "
               "only on the RTX machine.",
    )
    parser.add_argument("--suite", default="synthetic",
                        choices=("synthetic", "kaanoon"),
                        help="Which held-out set to score (default: synthetic). "
                             "'kaanoon' scores Lane 11's real-phrasing set at "
                             "--kaanoon-path as a SEPARATE number under CONTRACT R6 "
                             "(evaluation only, never tuned against).")
    parser.add_argument("--kaanoon-path", default=str(DEFAULT_KAANOON),
                        help="Kaanoon held-out JSONL (default: "
                             "data/kaanoon_eval/heldout.jsonl). Any path containing "
                             "'sealed' or 'test-bank' is refused.")
    parser.add_argument("--validation-path", default=str(DEFAULT_VALIDATION),
                        help="Validation JSONL (default: data/synthetic_v7_1/validation.jsonl). "
                             "Any path containing 'sealed' or 'test-bank' is refused.")
    parser.add_argument("--manifest-path", default=str(DEFAULT_MANIFEST),
                        help="Corpus manifest JSON (default: data/synthetic_v7_1/manifest.json). "
                             "Split size (n_validation) is read from here, never hardcoded.")
    parser.add_argument("--custody-vocab", default=CUSTODY_VOCAB_DEFAULT,
                        choices=("v3_bundled", "statutory_primary"),
                        help="Custody vocabulary used identically for expected and "
                             "predicted sections (default: v3_bundled, the assess_v7 default).")
    parser.add_argument("--limit", type=int, default=None,
                        help="Score only the first N validation records (debugging; "
                             "the reported number is then NOT the split number).")
    parser.add_argument("--misses", type=int, default=10,
                        help="Print the first N non-exact rows (default 10; 0 to suppress).")
    parser.add_argument("--failures-out", default=None,
                        help="Write one JSONL row per non-exact record "
                             "(id, lang, cluster, expected, predicted, tag) for Lane 01.")
    parser.add_argument("--json-out", default=None,
                        help="Write the full summary dict (incl. rows) as JSON.")
    parser.add_argument("--tagger", default=None,
                        help="Lane 01 taxonomy hook as 'module:function' "
                             "(fn(record, expected, predicted) -> str).")
    parser.add_argument("--self-test", action="store_true",
                        help="CPU-only unit checks of harness math (no data files, no torch).")
    args = parser.parse_args()

    if args.self_test:
        return _self_test()

    tagger = load_tagger(args.tagger) if args.tagger else None
    if tagger is not None:
        register_failure_tagger(tagger)

    if args.suite == "kaanoon":
        try:
            summary = run_kaanoon_eval(
                kaanoon_path=args.kaanoon_path,
                custody_vocab=args.custody_vocab,
                failure_tagger=tagger,
            )
        except FileNotFoundError as exc:
            print(f"KAANOON BASELINE PENDING — {exc}", file=sys.stderr)
            print("  Lane 11's data/kaanoon_eval/heldout.jsonl has not landed "
                  "yet; no Kaanoon number exists to report. Re-run "
                  "`python3 tests/recall_eval.py --suite kaanoon` once it lands.",
                  file=sys.stderr)
            return 3
        print_kaanoon_summary(summary)
    else:
        summary = run_evidence_eval(
            manifest_path=args.manifest_path,
            validation_path=args.validation_path,
            custody_vocab=args.custody_vocab,
            limit=args.limit,
            failure_tagger=tagger,
        )
        print_summary(summary)

    misses = [r for r in summary["rows"] if not r["exact"]]
    if args.misses and misses:
        print(f"--- first {min(args.misses, len(misses))} misses "
              f"({len(misses)} total) ---")
        for r in misses[: args.misses]:
            print(f"  MISS {r['id']} [{r['lang']}/{r['cluster']}] tag={r['tag']}: "
                  f"pred={r['predicted']} expected={r['expected']}")

    if args.failures_out:
        out_path = Path(args.failures_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as fh:
            for r in misses:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"failures written: {out_path} ({len(misses)} rows)")

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False),
                            encoding="utf-8")
        print(f"summary JSON written: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
