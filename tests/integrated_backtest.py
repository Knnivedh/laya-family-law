"""Integrated backtest harness for LAYA v7.1 (Lane E — contract C3).

One command scores the integrated runtime (contract C1, ``src/laya_integrated.py``)
on every non-sealed set::

    python3 tests/integrated_backtest.py [--mode auto|rule-based|classifier] \\
        [--suite all|validation|kaanoon|16q|brutal] [--checkpoint PATH] \\
        --json-out <path>

HONEST CLAIM RULE (printed in every run header and recorded in every JSON):
    "No claim of >=70% until a real sealed re-run measures it."
The validation-split, Kaanoon, 16-Q and Brutal numbers below are PROXIES /
regression numbers, never sealed numbers. Sealed Fresh-20 / Kannada-8 run
ONLY on Colab/RTX — this harness REFUSES any sealed suite or sealed path
and never loads a sealed file.

How it scores
-------------
* The harness IMPORTS the integrated runtime in-process and calls
  ``run_question(text, mode=..., checkpoint=...)`` (contract C1) once per
  question. It NEVER subprocesses the runtime for scoring.
* Section scoring reuses Lane 07's pure scorer (``tests/recall_eval.py``:
  ``score_predictions``) for the validation + Kaanoon suites, and mirrors
  ``tests/v7_backtest.py::score_dataset`` row-for-row for the 16-Q +
  Brutal suites (same ``_pr`` convention, same legacy-16Q-compat esc_bool,
  same frozen gate-rating formula via ``apply_gate_caps``). Loaders are
  reused, not duplicated: ``load_split`` / ``load_kaanoon_split`` from
  ``recall_eval``; ``_load_16q`` / ``_load_brutal`` from ``v7_backtest``.
  ``score_dataset`` itself is NOT reused — it calls ``assess_v7_batch``
  directly and would bypass the integrated runtime.
* The frozen validation split SHA is verified BEFORE any scoring; a
  mismatch aborts with exit 2. The Brutal bank SHA is recorded and
  warned on, not aborted (the task requires the abort only for the
  validation split).

Runtime status (2026-11-27, Lane E write-up)
--------------------------------------------
Lane C's ``src/laya_integrated.py`` had NOT landed when this harness was
written, so the harness ships with a DOCUMENTED STAND-IN adapter: when
``src/laya_integrated.py`` is absent it maps each question through the
frozen rule-based pipeline (``assess_v7_batch``, mode="evidence", CPU) and
shapes the result into the exact C1 dict. The stand-in is labelled in
every printout and in the JSON (``runtime.source == "stand-in"``), so a
stand-in number can never be mistaken for an integrated-runtime number.
The moment Lane C lands, the harness imports the real module instead —
no harness change needed — and the stand-in path goes dead. The stand-in
cannot do classifier mode (no torch, no checkpoint on this VM): it exits 2
and points at Colab/RTX.

Current C1 results include ``route_trace`` with pre-gate candidates,
dispositions, dropped routes and prose check results. This supports the
same Fb/Fp measurements as the stand-in. Older C1 records without this
trace have unmeasured Fb and a partial Fp check.

Modes
-----
* ``rule-based`` — rule-based extractor only (stand-in: evidence mode).
* ``classifier`` — classifier extractor only; exit 2 without a checkpoint
  (C1) and exit 2 from the stand-in (no torch on this VM — Colab/RTX only).
* ``auto`` — classifier preferred, rule-based fallback; the stand-in
  records the fallback reason on every question.

Suites
------
* ``validation`` — ``data/synthetic_v7_1/validation.jsonl`` (frozen 500,
  sha256 ``7640d067…``), expected sections derived via Stage 2 from the
  record's own issues/facts/enums (``recall_eval`` method).
* ``kaanoon`` — ``data/kaanoon_eval/heldout.jsonl`` (28 real-phrasing
  items; CONTRACT R6: evaluation only, never tuned against, reported as
  a SEPARATE number).
* ``16q`` — the frozen 16-Q regression set
  (``ground-truth/ground-truth-v2-hma27-A.json``) with the frozen gate
  rating (Gate §2 formula + caps).
* ``brutal`` — ``test-bank/brutal-bank-v1-frozen.json`` (230, read-only),
  scored with the ``v7_backtest`` brutal convention (custody
  ``statutory_primary`` + custody-companion projection). NO 10-point gate
  rating is computed for brutal: the rating formula is a 16-question
  instrument and its -0.5 x Fb term is not calibrated for a 230-question
  gating-probe set. Brutal is judged by the §3.2 bar instead (exact
  >= 200/230, micro-F1 >= 0.95, court/esc >= 200, silent 0, per-cat
  >= 0.75), reported per row.

Mode-qualified baselines (what a rule-based run must reproduce)
--------------------------------------------------------------
* validation (evidence, CPU): 261/500 = 52.2%, micro-P 0.8905 /
  micro-R 0.4623 / micro-F1 0.6086, TP/FP/FN 423/52/492, silent 212
  (``docs/recall_status.md`` §3, HEAD ``f92a9e5``).
* kaanoon (evidence, CPU): 14/28 = 50.0%, 0.7500 / 0.6000 / 0.6667,
  TP/FP/FN 27/9/18, silent 6 (``docs/recall_status.md`` §3).
* 16-Q (evidence, CPU): 14/16, TP/FP/FN 51/0/2, court 13/16, esc 16/16,
  esc_kinds_strict 10/16, Fb 3, Fp 0, rating 7.6
  (``docs/recall_status.md`` §2; re-verified with the frozen scorer on
  this VM at Lane E write-up).
* brutal (evidence, CPU): RECORDED 215/230, TP/FP/FN 387/0/28, court
  215/230, esc 230/230, esc_kinds_strict 184/230, silent 15
  (``results/live-laya-v7-results.md`` §2, pre-recall-swarm code). The
  headline "Brutal 230/230" is the NEURAL ``laya``/CUDA number, NOT a
  rule-based number — a rule-based run must NOT be expected to hit it.
  Current-code re-measurement with the frozen scorer on this VM gives
  210/230 (see the Lane E doc for the delta analysis).

Exit codes: 0 success; 2 refusal / contract error (sealed request, SHA
mismatch, classifier mode without a checkpoint, C1 key drift, missing
runtime in a mode the stand-in cannot serve); 1 unexpected failure.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.laya_prose_v2 import prose_forbidden_check  # noqa: E402  (frozen, read-only use)

# --- Reuse Lane 07 + v7_backtest (loaders + pure scorers; read-only) -------
_spec_re = importlib.util.spec_from_file_location(
    "_laneE_recall_eval", REPO_ROOT / "tests" / "recall_eval.py"
)
recall_eval = importlib.util.module_from_spec(_spec_re)  # type: ignore[arg-type]
_spec_re.loader.exec_module(recall_eval)  # type: ignore[union-attr]

_spec_v7 = importlib.util.spec_from_file_location(
    "_laneE_v7_backtest", REPO_ROOT / "tests" / "v7_backtest.py"
)
v7b = importlib.util.module_from_spec(_spec_v7)  # type: ignore[arg-type]
_spec_v7.loader.exec_module(v7b)  # type: ignore[union-attr]

# ---------------------------------------------------------------------------
# Frozen constants
# ---------------------------------------------------------------------------

CLAIM_RULE = "No claim of >=70% until a real sealed re-run measures it."
FROZEN_VALIDATION_SHA256 = (
    "7640d067c28abf539131dbcc891e4bdffedf62bbef4a7d66c1659bb96d07e58e"
)
FROZEN_BRUTAL_SHA256 = (
    "934a2b2265ac137c96939e1fbeca3682a037010e42f972bfd459c2fcac4ec717"
)
DEFAULT_MANIFEST = REPO_ROOT / "data" / "synthetic_v7_1" / "manifest.json"
DEFAULT_VALIDATION = REPO_ROOT / "data" / "synthetic_v7_1" / "validation.jsonl"
DEFAULT_KAANOON = REPO_ROOT / "data" / "kaanoon_eval" / "heldout.jsonl"
GT_16_PATH = REPO_ROOT / "ground-truth" / "ground-truth-v2-hma27-A.json"
BANK_PATH = REPO_ROOT / "test-bank" / "brutal-bank-v1-frozen.json"
INTEGRATED_PATH = REPO_ROOT / "src" / "laya_integrated.py"

# Contract C1 output keys (impl_swarm_state.md). The harness validates the
# first real-runtime result against exactly this set.
C1_REQUIRED_KEYS = (
    "question", "language", "extractor", "checkpoint", "fallback_reason",
    "issues", "facts", "enums", "sections", "court", "escalations",
    "prose", "latency_ms",
)

# Mode-qualified baselines a rule-based run must reproduce (see module
# docstring for sources). Used only for the printed/JSON delta table.
KNOWN_BASELINES: dict[str, dict[str, Any]] = {
    "validation": {
        "mode": "rule-based (evidence, cpu)",
        "exact_count": 261, "n": 500, "exact_rate": 0.522,
        "micro_p": 0.8905, "micro_r": 0.4623, "micro_f1": 0.6086,
        "tp_fp_fn": [423, 52, 492], "silent": 212,
        "source": "docs/recall_status.md §3 (HEAD f92a9e5)",
    },
    "kaanoon": {
        "mode": "rule-based (evidence, cpu)",
        "exact_count": 14, "n": 28, "exact_rate": 0.5,
        "micro_p": 0.75, "micro_r": 0.6, "micro_f1": 0.6667,
        "tp_fp_fn": [27, 9, 18], "silent": 6,
        "source": "docs/recall_status.md §3 (HEAD f92a9e5)",
    },
    "16q": {
        "mode": "rule-based (evidence, cpu)",
        "exact_count": 14, "n": 16, "exact_rate": 0.875,
        "micro_p": 1.0, "micro_r": 0.9623, "micro_f1": 0.9808,
        "tp_fp_fn": [51, 0, 2], "silent": 0,
        "court": "13/16", "esc_bool": "16/16",
        "esc_kinds_strict": "10/16", "fb_count": 3, "fp_prose": 0,
        "rating": 7.6,
        "source": "docs/recall_status.md §2; frozen scorer re-run, this VM",
    },
    "brutal": {
        "mode": "rule-based (evidence, cpu)",
        # Recorded pre-recall-swarm evidence baseline (results file §2).
        "exact_count": 215, "n": 230, "exact_rate": 0.9348,
        "micro_p": 1.0, "micro_r": 0.9325, "micro_f1": 0.9651,
        "tp_fp_fn": [387, 0, 28], "silent": 15,
        "court": "215/230", "esc_bool": "230/230",
        "esc_kinds_strict": "184/230",
        "source": "results/live-laya-v7-results.md §2 (pre-recall-swarm code)",
        # Current-code re-measurement with the frozen scorer on this VM
        # (Lane E reference run before writing this harness).
        "current_code_reference": {
            "exact_count": 210, "n": 230, "exact_rate": 0.913,
            "micro_p": 0.9974, "micro_r": 0.9205, "micro_f1": 0.9574,
            "tp_fp_fn": [382, 1, 33], "silent": 15,
            "court": "215/230", "esc_bool": "213/230",
            "esc_kinds_strict": "152/230", "fb_count": 58,
            "source": "frozen tests/v7_backtest.py --suite brutal "
                      "--mode evidence --device cpu, this VM, Lane E",
        },
    },
}


# ---------------------------------------------------------------------------
# Small utilities
# ---------------------------------------------------------------------------

def _sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_head() -> tuple[str, bool]:
    """(HEAD sha, dirty?) — 'unknown' when git is unavailable."""
    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT),
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except Exception:
        return "unknown (git rev-parse failed)", False
    try:
        dirty = bool(subprocess.run(
            ["git", "status", "--porcelain"], cwd=str(REPO_ROOT),
            capture_output=True, text=True, check=True,
        ).stdout.strip())
    except Exception:
        dirty = False
    return head, dirty


def refuse_sealed(what: str) -> "SystemExit":
    """The sealed refusal: sealed sets run only on Colab/RTX, never here."""
    print(
        f"ERROR: refusing {what}: sealed test banks "
        f"(test-bank/sealed/sealed-fresh-20.json, "
        f"test-bank/sealed/sealed-kannada-8.json) are NEVER scored by this "
        f"harness.\n"
        f"  Sealed re-runs happen ONLY on Colab/RTX with the trained "
        f"classifier. No sealed file is loaded, no sealed question text "
        f"is read, no sealed number is produced here.\n"
        f"  {CLAIM_RULE}",
        file=sys.stderr,
    )
    return SystemExit(2)


def validate_suite(value: str) -> str:
    """Validate --suite, refusing sealed values with the proper message."""
    lowered = value.strip().lower()
    if "sealed" in lowered:
        raise refuse_sealed(f"--suite {value!r}")
    if lowered not in ("all", "validation", "kaanoon", "16q", "brutal"):
        print(
            f"ERROR: unknown --suite {value!r} (expected one of "
            f"all|validation|kaanoon|16q|brutal). "
            f"'sealed' suites are refused outright — sealed re-runs happen "
            f"only on Colab/RTX.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return lowered


def verify_validation_sha() -> dict[str, Any]:
    """Verify the frozen validation split SHA before any scoring.

    Aborts (exit 2) unless BOTH the file hash and the manifest's
    ``frozen_validation_sha256`` equal the frozen constant.
    """
    actual = _sha256(DEFAULT_VALIDATION)
    try:
        manifest = json.loads(Path(DEFAULT_MANIFEST).read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - manifest unreadable
        print(f"ERROR: cannot read validation manifest: {exc}", file=sys.stderr)
        raise SystemExit(2)
    manifest_sha = manifest.get("frozen_validation_sha256")
    info = {
        "path": str(DEFAULT_VALIDATION),
        "expected": FROZEN_VALIDATION_SHA256,
        "actual": actual,
        "manifest_sha": manifest_sha,
        "manifest_n_validation": manifest.get("n_validation"),
        "ok": actual == FROZEN_VALIDATION_SHA256
        and manifest_sha == FROZEN_VALIDATION_SHA256,
    }
    if not info["ok"]:
        print(
            "ERROR: frozen validation split SHA MISMATCH — aborting before "
            "scoring.\n"
            f"  file:     {actual}\n"
            f"  manifest: {manifest_sha}\n"
            f"  expected: {FROZEN_VALIDATION_SHA256}\n"
            "  The validation split is FROZEN; a mismatch means the corpus "
            "moved under the harness. Re-freeze deliberately (Lane 02) or "
            "restore the frozen file — do not score against a moved split.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return info


# ---------------------------------------------------------------------------
# Integrated runtime loading (contract C1) + documented stand-in
# ---------------------------------------------------------------------------

class RuntimeHandle:
    """What the harness calls per question: a C1-shaped ``run_question``.

    ``source`` is "src/laya_integrated.py" for Lane C's real runtime or
    "stand-in" for the documented fallback (see module docstring).
    ``batch_fn`` is set only for the stand-in (batched evidence run).
    """

    def __init__(self, source: str, note: str, run_fn=None, batch_fn=None):
        self.source = source
        self.note = note
        self.run_fn = run_fn
        self.batch_fn = batch_fn

    @property
    def is_standin(self) -> bool:
        return self.source == "stand-in"


def load_runtime() -> RuntimeHandle:
    """Load Lane C's runtime if it has landed; else the stand-in.

    If ``src/laya_integrated.py`` EXISTS, it is imported and any import
    error propagates loudly (exit, no silent fallback — a broken real
    runtime must never be masked by the stand-in). Only a MISSING file
    selects the stand-in.
    """
    if INTEGRATED_PATH.exists():
        try:
            mod = importlib.import_module("src.laya_integrated")
        except Exception:
            print(
                "ERROR: src/laya_integrated.py exists but failed to import. "
                "Not falling back to the stand-in — fix Lane C's module "
                "(contract C1) instead.",
                file=sys.stderr,
            )
            raise
        fn = getattr(mod, "run_question", None)
        if not callable(fn):
            print(
                "ERROR: src/laya_integrated.py has no callable run_question "
                "(contract C1: run_question(text, mode='auto', "
                "checkpoint=None) -> dict). Interface drift — adapt at "
                "merge time; refusing to score against a drifted runtime.",
                file=sys.stderr,
            )
            raise SystemExit(2)
        return RuntimeHandle(
            "src/laya_integrated.py",
            "Lane C integrated runtime (contract C1)",
            run_fn=fn,
        )
    return RuntimeHandle(
        "stand-in",
        "STAND-IN: src/laya_integrated.py has not landed yet — frozen "
        "rule-based pipeline (assess_v7_batch, mode='evidence', CPU) "
        "shaped into the C1 dict. These are stand-in numbers, NOT "
        "integrated-runtime numbers.",
        batch_fn=_standin_run_batch,
    )


def _validate_c1_result(result: Any, question: str) -> dict[str, Any]:
    """Strict-check the FIRST real-runtime result against contract C1.

    A missing key or a wrongly-typed ``sections`` is interface drift:
    abort (exit 2) with the drift spelled out. Later per-question
    failures are recorded as error rows, not aborts (see _run_questions).
    """
    if not isinstance(result, dict):
        print(
            "ERROR: contract C1 drift — run_question did not return a dict "
            f"for question {question[:60]!r} (got {type(result).__name__}).",
            file=sys.stderr,
        )
        raise SystemExit(2)
    missing = [k for k in C1_REQUIRED_KEYS if k not in result]
    if missing:
        print(
            "ERROR: contract C1 drift — run_question result is missing keys "
            f"{missing} (present: {sorted(result.keys())}). The harness "
            "scores only the C1 dict; adapt the runtime or the harness at "
            "merge time.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    sections = result.get("sections")
    if not isinstance(sections, (list, tuple, set)):
        print(
            "ERROR: contract C1 drift — run_question 'sections' is not a "
            f"list/set (got {type(sections).__name__}).",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return result


def _standin_run_batch(
    questions: list[str],
    *,
    mode: str,
    custody_vocab: str,
    with_prose: bool,
) -> tuple[list[dict[str, Any]], float]:
    """Stand-in batch run: frozen evidence pipeline -> C1-shaped dicts.

    One in-process ``assess_v7_batch`` call (mode="evidence", CPU); each
    record is mapped to the exact C1 key set. The raw assess record rides
    along as ``_assess_record`` (stand-in only) so Fb/Fp can be measured
    genuinely via ``compute_fb`` / ``prose_fp_hits``; it is stripped
    before any JSON is written. ``issues``/``facts``/``enums`` are empty
    here — ``assess_v7_batch`` does not expose them — and are flagged as
    such; scoring never reads them.
    """
    from src.laya_v7 import assess_v7_batch

    recs, wall_s = assess_v7_batch(
        questions,
        mode="evidence",
        device="cpu",
        custody_vocab=custody_vocab,
        with_prose=with_prose,
        batch_size=16,
    )
    out: list[dict[str, Any]] = []
    for q, rec in zip(questions, recs):
        out.append({
            "question": q,
            "language": rec.get("lang"),
            "extractor": "rule_based",
            "checkpoint": None,
            "fallback_reason": (
                "classifier unavailable on this VM (no torch); "
                "rule-based fallback" if mode == "auto" else None
            ),
            "issues": {},
            "facts": {},
            "enums": {},
            "sections": sorted(rec.get("kept_ids") or []),
            "court": list(rec.get("court_live") or []),
            "escalations": sorted(rec.get("escalation_kinds") or []),
            "prose": rec.get("prose"),
            "latency_ms": round(float(rec.get("latency_s") or 0.0) * 1000.0, 1),
            "error": rec.get("error"),
            "_assess_record": rec,
            "_standin_note": (
                "issues/facts/enums not exposed by assess_v7_batch; "
                "scoring uses sections/court/escalations/prose only"
            ),
        })
    return out, wall_s


def _run_questions(
    texts: list[str],
    *,
    mode: str,
    checkpoint: str | None,
    custody_vocab: str,
    with_prose: bool,
    runtime: RuntimeHandle,
) -> tuple[list[dict[str, Any]], float]:
    """Run every question through the C1 runtime; return C1 dicts + wall s.

    Real runtime: one ``run_question`` call per question (in-process, never
    a subprocess). The FIRST call is strictly validated against C1 and any
    failure there aborts; later per-question exceptions become error rows
    (empty sections, ``error`` set) so one bad question cannot sink a suite.
    Stand-in: one batched evidence call (see ``_standin_run_batch``).
    """
    import time

    t0 = time.perf_counter()
    if runtime.is_standin:
        if mode == "classifier":
            print(
                "ERROR: --mode classifier with the STAND-IN runtime: the "
                "stand-in is rule-based only. This VM has no torch and no "
                "classifier checkpoint, so classifier mode cannot run here.\n"
                "  Classifier-mode backtest needs the Colab GPU run "
                "(Lane D notebook, contract C4) with Lane C's runtime + a "
                "trained checkpoint. Rule-based mode is the only mode that "
                "runs on this VM today.",
                file=sys.stderr,
            )
            raise SystemExit(2)
        assert runtime.batch_fn is not None
        outputs, _wall = runtime.batch_fn(
            texts, mode=mode,
            custody_vocab=custody_vocab, with_prose=with_prose,
        )
        return outputs, round(time.perf_counter() - t0, 3)

    assert runtime.run_fn is not None
    outputs: list[dict[str, Any]] = []
    for idx, text in enumerate(texts):
        try:
            result = runtime.run_fn(text, mode=mode, checkpoint=checkpoint)
        except SystemExit:
            raise
        except Exception as exc:
            if idx == 0:
                print(
                    "ERROR: run_question failed on the FIRST question "
                    f"({type(exc).__name__}: {exc}) — aborting instead of "
                    "scoring a suite of error rows. If this is a missing "
                    "checkpoint, C1 requires exit 2 from the runtime.",
                    file=sys.stderr,
                )
                raise SystemExit(2)
            outputs.append({
                "question": text, "language": None, "extractor": "error",
                "checkpoint": checkpoint, "fallback_reason": None,
                "issues": {}, "facts": {}, "enums": {}, "sections": [],
                "court": [], "escalations": [], "prose": None,
                "latency_ms": None, "error": f"{type(exc).__name__}: {exc}",
            })
            continue
        if idx == 0:
            result = _validate_c1_result(result, text)
        outputs.append(result)
    return outputs, round(time.perf_counter() - t0, 3)


# ---------------------------------------------------------------------------
# Fb / Fp per row (genuine via stand-in record; partial via C1 output)
# ---------------------------------------------------------------------------

def _fb_fp_for_row(out: dict[str, Any]) -> tuple[int | None, bool, list, int | None, bool]:
    """Return (fb_count, fb_measured, fb_details, fp_count, fp_measured).

    Trace path (``route_trace`` or stand-in ``_assess_record``): Fb from
    ``compute_fb`` and Fp from the pipeline's own ``prose_fp_hits``
    (computed with real facts + gated_out). Older results without a trace
    have unmeasured Fb, and Fp is checked
    from the prose text + kept sections + the C1 ``facts`` dict (which
    ``_normalize_prose_facts`` accepts as-is — dicts with a "status"
    key). That covers Fp items 1-6, 8, 9 and item 7's cited-not-kept
    half; only item 7's dropped half (prose cites a section Stage 2
    dropped) is unmeasurable without ``gated_out``, so the real-runtime
    Fp is a LOWER BOUND. Passing empty facts here would be WRONG:
    item 3 fires spuriously whenever the prose mentions HMA 13/13B
    (verified on H5: facts={} gave a false item-3 hit; real facts
    give none). A row with no prose at all has Fp unmeasured.
    """
    rec = out.get("route_trace", out.get("_assess_record"))
    if isinstance(rec, dict):
        fb = v7b.compute_fb(rec)
        fp = len(rec.get("prose_fp_hits") or []) if "prose_fp_hits" in rec else None
        return (
            fb["fb_count"], bool(fb["fb_measured"]), fb["fb_details"],
            fp, fp is not None,
        )
    # Older results with no pre-gate data. Fp is checked from
    # the prose + kept sections + the C1 facts dict (NOT empty facts —
    # see docstring: empty facts false-fire item 3 on any HMA 13/13B
    # mention). Item 7's dropped half is unmeasurable (no gated_out),
    # so this Fp is a lower bound.
    fp: int | None = None
    fp_measured = False
    prose = out.get("prose")
    if isinstance(prose, str) and prose:
        try:
            hits, _flags = prose_forbidden_check(
                prose, list(out.get("sections") or []), [],
                out.get("facts") or {},
            )
            fp = len(hits)
            fp_measured = True  # lower bound: item 7 dropped-half not coverable
        except Exception:
            fp, fp_measured = None, False
    return None, False, [], fp, fp_measured


# ---------------------------------------------------------------------------
# 16-Q / Brutal scorer — mirrors tests/v7_backtest.py::score_dataset
# (same _pr, same legacy-16Q-compat esc_bool, same rating formula)
# ---------------------------------------------------------------------------

def _score_typed_suite(
    items: list[dict[str, Any]],
    outputs: list[dict[str, Any]],
    *,
    legacy_16q_compat: bool,
    project_custody: bool,
    suite_name: str,
) -> dict[str, Any]:
    """Score 16-Q / Brutal items against C1 runtime outputs.

    ``suite_name`` is "16q" or "brutal". Only "16q" gets the frozen
    10-point gate rating; "brutal" gets the §3.2 bar verdict instead
    (the rating formula is a 16-question instrument).
    """
    if len(items) != len(outputs):
        raise ValueError(
            f"{suite_name}: items ({len(items)}) and runtime outputs "
            f"({len(outputs)}) differ in length"
        )
    rows: list[dict[str, Any]] = []
    tot_tp = tot_fp = tot_fn = 0
    sec_fp: Counter[str] = Counter()
    sec_fn: Counter[str] = Counter()
    per_cat: dict[str, list[bool]] = defaultdict(list)

    for item, out in zip(items, outputs):
        pred = set(out.get("sections") or [])
        if project_custody:
            pred = pred - v7b.CUSTODY_COMPANIONS
        gt = set(item["gt_ids"])
        tp, fp, fn, prec, rec_v = v7b._pr(pred, gt)
        tot_tp += tp
        tot_fp += fp
        tot_fn += fn
        for s in pred & gt:
            pass
        for s in pred - gt:
            sec_fp[s] += 1
        for s in gt - pred:
            sec_fn[s] += 1

        court = list(out.get("court") or [])
        exp_court = list(item["gt_court"])
        if not exp_court:
            court_ok = (court == [])
        else:
            court_ok = set(exp_court) <= set(court)

        kinds = set(out.get("escalations") or []) & v7b.SCORING_KINDS_V7
        gt_kinds = set(item.get("gt_kinds", []))
        if legacy_16q_compat and "safety" not in gt_kinds:
            kinds_cmp = kinds - {"safety"}
        else:
            kinds_cmp = kinds
        if item.get("f20_rule"):
            esc_ok = (not pred and court == [])
        elif legacy_16q_compat and item["id"] == "H12":
            esc_ok = (bool(kinds_cmp - {"procedure"}) == bool(item["gt_escalates"]))
        else:
            esc_ok = (bool(kinds_cmp) == bool(item["gt_escalates"]))
        esc_ok_strict = (bool(kinds) == bool(item["gt_escalates"]))
        kinds_ok_strict = (kinds == gt_kinds)
        kinds_ok_fe = ((kinds - {"fact"}) == (gt_kinds - {"fact"}))
        silent = bool(gt) and not pred
        exact = (pred == gt)
        per_cat[item.get("category", "all")].append(exact)

        fb_count, fb_measured, fb_details, fp_prose, fp_measured = _fb_fp_for_row(out)
        rec = out.get("route_trace", out.get("_assess_record"))
        q_flags = (
            len(rec.get("prose_quality_flags") or [])
            if isinstance(rec, dict) and "prose_quality_flags" in rec
            else None
        )
        lat_ms = out.get("latency_ms")
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
            "court_live": court,
            "court_expected": exp_court,
            "court_ok": court_ok,
            "esc_ok": esc_ok,
            "esc_ok_strict": esc_ok_strict,
            "kinds": sorted(kinds),
            "gt_kinds": sorted(gt_kinds),
            "kinds_ok": kinds_ok_strict,
            "kinds_ok_fe": kinds_ok_fe,
            "silent": silent,
            "fp_prose": fp_prose,
            "fp_prose_measured": fp_measured,
            "q_flags": q_flags,
            "fb": fb_count,
            "fb_details": fb_details,
            "fb_measured": fb_measured,
            "error": out.get("error"),
            "latency_s": (round(lat_ms / 1000.0, 4) if isinstance(lat_ms, (int, float)) else None),
            "extractor": out.get("extractor"),
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
    fp_rows = [r for r in rows if r["fp_prose"] is not None]
    fp_prose_n = sum(1 for r in fp_rows if (r["fp_prose"] or 0) > 0)
    fp_unmeasured = n - len(fp_rows)
    err_n = sum(1 for r in rows if r["error"])
    fb_total = sum(r["fb"] for r in rows if r["fb"] is not None)
    fb_measured_all = all(r["fb_measured"] for r in rows)
    fb_unmeasured_rows = sum(1 for r in rows if not r["fb_measured"])
    fb_by_mapping = dict(Counter(
        d["mapping"] for r in rows for d in (r["fb_details"] or [])
    ))
    lats = [r["latency_s"] for r in rows if r["latency_s"] is not None]
    cat_exact = {c: f"{sum(v)}/{len(v)}" for c, v in sorted(per_cat.items())}
    cat_min = min((sum(v) / len(v)) for v in per_cat.values()) if per_cat else 0.0

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
            "note": "Strict esc_bool counts the H12 safety/procedure "
                    "delta as a mismatch; legacy_16q_compat does not. "
                    "Both are reported.",
        }

    out: dict[str, Any] = {
        "n": n,
        "exact": f"{n_exact}/{n}",
        "exact_count": n_exact,
        "exact_rate": round(n_exact / n, 4) if n else 0.0,
        "wilson_95": list(v7b.wilson_ci(n_exact, n)),
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
        "fp_prose_unmeasured_rows": fp_unmeasured,
        "fb_count": fb_total,
        "fb_by_mapping": fb_by_mapping,
        "fb_measured": fb_measured_all,
        "fb_unmeasured_rows": fb_unmeasured_rows,
        "fb_warning": None if fb_measured_all else (
            "Fb UNMEASURED on at least one record: no candidates_before_gate "
            "/ dispositions in the C1 output; fb_count counts only the "
            "measured rows and is a LOWER BOUND, never a measured total."
        ),
        "errors": err_n,
        "per_cat_exact": cat_exact,
        "per_cat_min": round(cat_min, 4),
        "latency_mean_s": round(sum(lats) / len(lats), 3) if lats else None,
        "latency_max_s": round(max(lats), 3) if lats else None,
        "top_fp_sections": dict(sec_fp.most_common(12)),
        "top_fn_sections": dict(sec_fn.most_common(12)),
        "rows": rows,
    }

    if suite_name == "16q":
        # Frozen gate rating (Gate §2): raw formula, then every cap.
        # Fb unmeasured rows contribute 0 to the formula — flagged below.
        e = n_exact / n
        c = court_n / n
        s = esc_bool_n / n
        raw_rating = max(0.0, min(10.0, round(
            10.0 * (0.60 * e + 0.15 * mean_r + 0.10 * mean_p
                    + 0.075 * c + 0.075 * s)
            - 0.5 * fb_total - 1.0 * fp_prose_n, 1)))
        prose_measured = fp_unmeasured == 0
        capped_rating, caps_applied = v7b.apply_gate_caps(
            raw_rating,
            fp_prose_n=fp_prose_n,
            fb_count=fb_total,
            g12_verified=False,
            sealed_passed=False,
            confirmation_done=False,
            prose_measured=prose_measured,
            errors=err_n,
        )
        out["raw_formula_rating"] = raw_rating
        out["capped_rating"] = capped_rating
        out["rating"] = capped_rating
        out["caps_applied"] = caps_applied
        out["rating_components"] = {
            "E": round(e, 4), "mean_r": round(mean_r, 4),
            "mean_p": round(mean_p, 4), "C": round(c, 4), "S": round(s, 4),
            "fb_count": fb_total, "fp_prose_n": fp_prose_n,
        }
        out["rating_note"] = (
            "Gate §2 formula + caps (frozen). Caps default to the honest "
            "unverified state (G12 unverified, sealed not passed, no "
            "confirmation re-run), so the capped rating can never exceed "
            "9.0 from this harness."
            + ("" if fb_measured_all else
               " Fb UNMEASURED on some rows: the rating EXCLUDES the "
               "-0.5 x Fb term for those rows and is a provisional UPPER "
               "BOUND, not a measured rating.")
            + ("" if prose_measured else
               " Fp UNMEASURED on some rows (no prose): the Fp term is "
               "undercounted.")
        )
    else:
        # Brutal: no 10-point rating (see module docstring). §3.2 bar.
        out["raw_formula_rating"] = None
        out["capped_rating"] = None
        out["rating"] = None
        out["rating_note"] = (
            "No 10-point gate rating for Brutal-230: the Gate §2 formula "
            "is a 16-question instrument and its -0.5 x Fb term is not "
            "calibrated for a 230-question gating-probe set (Fb counts "
            "every gated candidate the bank deliberately probes). Brutal "
            "is judged by the §3.2 bar below."
        )
        bar = {
            "exact_ge_200": n_exact >= 200,
            "micro_f1_ge_0.95": mf1 >= 0.95,
            "court_ge_200": court_n >= 200,
            "esc_bool_ge_200": esc_bool_n >= 200,
            "silent_0": silent_n == 0,
            "per_cat_min_ge_0.75": cat_min >= 0.75,
            "errors_0": err_n == 0,
            "fp_prose_0": fp_prose_n == 0,
        }
        bar["pass"] = all(bar.values())
        out["section_3_2_bar"] = bar
    return out


# ---------------------------------------------------------------------------
# Suite runners (loaders + scorer reused; runtime is the only scorer input)
# ---------------------------------------------------------------------------

def _strip_private(outputs: list[dict[str, Any]]) -> None:
    """Drop stand-in-private keys before JSON serialisation."""
    for o in outputs:
        o.pop("_assess_record", None)
        o.pop("_standin_note", None)


def run_validation_suite(runtime: RuntimeHandle, mode: str, checkpoint: str | None) -> dict[str, Any]:
    records, manifest, report = recall_eval.load_split(
        DEFAULT_MANIFEST, DEFAULT_VALIDATION
    )
    outputs, wall_s = _run_questions(
        [r["text"] for r in records], mode=mode, checkpoint=checkpoint,
        custody_vocab="v3_bundled", with_prose=False, runtime=runtime,
    )
    summary = recall_eval.score_predictions(
        records, [set(o.get("sections") or []) for o in outputs]
    )
    summary["split"] = {
        "validation_path": str(DEFAULT_VALIDATION),
        "n_manifest": int(manifest.get("n_validation") or 0),
        "n_scored": len(records),
        "manifest_seed": manifest.get("seed"),
        "loader_skipped_lines": report.get("n_skipped", 0),
    }
    summary["method"] = {
        "runtime": runtime.source,
        "mode": mode,
        "checkpoint": checkpoint,
        "extractor": Counter(o.get("extractor") for o in outputs),
        "custody_vocab": "v3_bundled",
        "with_prose": False,
        "total_wall_s": wall_s,
        "mean_latency_s": round(wall_s / max(len(records), 1), 4),
        "errors": sum(1 for o in outputs if o.get("error")),
    }
    _strip_private(outputs)
    return summary


def run_kaanoon_suite(runtime: RuntimeHandle, mode: str, checkpoint: str | None) -> dict[str, Any]:
    records = recall_eval.load_kaanoon_split(DEFAULT_KAANOON)
    if not records:
        raise ValueError(f"No scorable records in Kaanoon set: {DEFAULT_KAANOON}")
    outputs, wall_s = _run_questions(
        [r["text"] for r in records], mode=mode, checkpoint=checkpoint,
        custody_vocab="v3_bundled", with_prose=False, runtime=runtime,
    )
    summary = recall_eval.score_predictions(
        records, [set(o.get("sections") or []) for o in outputs]
    )
    summary["split"] = {
        "kaanoon_path": str(DEFAULT_KAANOON),
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
        "runtime": runtime.source,
        "mode": mode,
        "checkpoint": checkpoint,
        "extractor": Counter(o.get("extractor") for o in outputs),
        "custody_vocab": "v3_bundled",
        "with_prose": False,
        "total_wall_s": wall_s,
        "mean_latency_s": round(wall_s / max(len(records), 1), 4),
        "errors": sum(1 for o in outputs if o.get("error")),
    }
    summary["contract"] = (
        "R6 evaluation-only: read-only measurement, never tuned against"
    )
    _strip_private(outputs)
    return summary


def run_16q_suite(runtime: RuntimeHandle, mode: str, checkpoint: str | None) -> dict[str, Any]:
    items = v7b._load_16q()
    outputs, wall_s = _run_questions(
        [it["question"] for it in items], mode=mode, checkpoint=checkpoint,
        custody_vocab="v3_bundled", with_prose=True, runtime=runtime,
    )
    summary = _score_typed_suite(
        items, outputs, legacy_16q_compat=True, project_custody=False,
        suite_name="16q",
    )
    summary["method"] = {
        "runtime": runtime.source,
        "mode": mode,
        "checkpoint": checkpoint,
        "extractor": Counter(o.get("extractor") for o in outputs),
        "custody_vocab": "v3_bundled",
        "with_prose": True,
        "total_wall_s": wall_s,
        "errors": sum(1 for o in outputs if o.get("error")),
    }
    _strip_private(outputs)
    return summary


def run_brutal_suite(runtime: RuntimeHandle, mode: str, checkpoint: str | None) -> dict[str, Any]:
    items = v7b._load_brutal()
    outputs, wall_s = _run_questions(
        [it["question"] for it in items], mode=mode, checkpoint=checkpoint,
        custody_vocab="statutory_primary", with_prose=True, runtime=runtime,
    )
    summary = _score_typed_suite(
        items, outputs, legacy_16q_compat=False, project_custody=True,
        suite_name="brutal",
    )
    summary["method"] = {
        "runtime": runtime.source,
        "mode": mode,
        "checkpoint": checkpoint,
        "extractor": Counter(o.get("extractor") for o in outputs),
        "custody_vocab": "statutory_primary (ignored by the real C1 "
                        "runtime — it chooses its own vocab; the parameter "
                        "only applies to the stand-in assess path — see doc)",
        "with_prose": True,
        "total_wall_s": wall_s,
        "errors": sum(1 for o in outputs if o.get("error")),
    }
    _strip_private(outputs)
    return summary


# ---------------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------------

def _print_header(mode: str, suite: str, runtime: RuntimeHandle, sha_info: dict[str, Any]) -> None:
    print("=== LAYA v7.1 INTEGRATED BACKTEST (Lane E, contract C3) ===")
    print(f"HONEST CLAIM RULE: {CLAIM_RULE}")
    print("  Validation / Kaanoon / 16-Q / Brutal numbers are proxies and")
    print("  regression numbers. They are NOT sealed numbers and never")
    print("  prove >=70% on unseen questions.")
    print(f"mode:    {mode}")
    print(f"suite:   {suite}")
    print(f"runtime: {runtime.source} — {runtime.note}")
    print(f"validation sha256: {sha_info['actual'][:12]}… "
          f"(expected {sha_info['expected'][:12]}…, "
          f"manifest {str(sha_info['manifest_sha'])[:12]}… — "
          f"{'VERIFIED' if sha_info['ok'] else 'MISMATCH'})")


def _print_section_summary(name: str, summary: dict[str, Any]) -> None:
    lo, hi = summary["wilson_95"]
    print(f"--- {name} ---")
    print(f"exact:        {summary['exact_count']}/{summary['n']} "
          f"({summary['exact_rate']:.1%})  Wilson 95% CI [{lo:.4f}, {hi:.4f}]")
    print(f"micro P/R/F1: {summary['micro_p']:.4f} / {summary['micro_r']:.4f} / "
          f"{summary['micro_f1']:.4f}  (TP/FP/FN {summary['tp_fp_fn']})")
    print(f"silent:       {summary['silent']} "
          f"(expected non-empty, predicted empty)")
    if "mean_p" in summary:
        print(f"mean P/R:     {summary['mean_p']:.4f} / {summary['mean_r']:.4f}")
    if "court_correct" in summary:
        print(f"court:        {summary['court_correct']}  "
              f"esc_bool: {summary['esc_bool']} "
              f"(strict {summary['esc_bool_strict']})  "
              f"esc_kinds_strict: {summary['esc_kinds_strict']} "
              f"(FE {summary['esc_kinds_fe']})")
    if "fb_count" in summary:
        fb_note = "" if summary.get("fb_measured") else " (UNMEASURED rows — lower bound)"
        print(f"Fb:           {summary['fb_count']}{fb_note}  "
              f"by mapping {summary.get('fb_by_mapping', {})}  "
              f"Fp prose: {summary.get('fp_prose')}  "
              f"errors: {summary.get('errors')}")
    if summary.get("per_cat_min") is not None:
        print(f"per_cat_min:  {summary['per_cat_min']:.4f}  "
              f"per_cat: {summary.get('per_cat_exact', {})}")
    if "rating" in summary and summary["rating"] is not None:
        rc = summary["rating_components"]
        fb_qual = ("" if summary.get("fb_measured") else
                   " [Fb UNMEASURED — provisional UPPER BOUND; "
                   "rule-based baseline measured 7.6 (Fb=3) under the "
                   "frozen scorer]")
        print(f"gate rating:  raw {summary['raw_formula_rating']} -> "
              f"capped {summary['capped_rating']} "
              f"(E {rc['E']}, Rm {rc['mean_r']}, Pm {rc['mean_p']}, "
              f"C {rc['C']}, S {rc['S']}, Fb {rc['fb_count']}, "
              f"Fp {rc['fp_prose_n']}; caps: {summary['caps_applied']})"
              f"{fb_qual}")
        print(f"  note: {summary['rating_note']}")
    if "section_3_2_bar" in summary:
        bar = summary["section_3_2_bar"]
        print(f"§3.2 bar:     {'PASS' if bar['pass'] else 'FAIL'} — " +
              ", ".join(f"{k}={'Y' if v else 'N'}"
                        for k, v in bar.items() if k != "pass"))
        print(f"  note: {summary['rating_note']}")
    print(f"latency:      mean {summary['method'].get('mean_latency_s', summary.get('latency_mean_s'))}s/Q "
          f"(wall {summary['method'].get('total_wall_s')}s)")


def _print_baseline_delta(name: str, summary: dict[str, Any]) -> None:
    base = KNOWN_BASELINES.get(name)
    if base is None:
        return
    got = summary["exact_count"]
    want = base["exact_count"]
    delta = got - want
    verdict = "MATCH" if delta == 0 else ("ABOVE" if delta > 0 else "BELOW")
    print(f"baseline [{base['mode']}; {base['source']}]: "
          f"expected {want}/{base['n']}, measured {got}/{summary['n']} "
          f"({verdict} by {delta:+d})")
    for key in ("micro_p", "micro_r", "micro_f1", "silent"):
        if key in base and key in summary:
            print(f"  {key}: baseline {base[key]} vs measured {summary[key]}")
    if "tp_fp_fn" in base:
        print(f"  tp_fp_fn: baseline {base['tp_fp_fn']} vs measured {summary['tp_fp_fn']}")
    if name == "16q" and "rating" in base:
        print(f"  rating: baseline {base['rating']} vs measured {summary.get('rating')} "
              f"(Fb baseline {base.get('fb_count')} vs measured {summary.get('fb_count')})"
              + ("" if summary.get("fb_measured") else
                 " — measured is a provisional UPPER BOUND (Fb unmeasured); "
                 "the measured rating for this rule-based baseline is 7.6"))
    if name == "brutal" and "current_code_reference" in base:
        ref = base["current_code_reference"]
        print(f"  current-code reference [{ref['source']}]: "
              f"expected {ref['exact_count']}/{ref['n']}, measured "
              f"{got}/{summary['n']} "
              f"({'MATCH' if got == ref['exact_count'] else 'DELTA ' + str(got - ref['exact_count'])})")
        print(f"    esc_bool: reference {ref['esc_bool']} vs measured {summary.get('esc_bool')}; "
              f"esc_kinds_strict: reference {ref['esc_kinds_strict']} vs measured {summary.get('esc_kinds_strict')}; "
              f"Fb: reference {ref['fb_count']} vs measured {summary.get('fb_count')}")


# ---------------------------------------------------------------------------
# Self-test (CPU-only harness checks; no scoring runs)
# ---------------------------------------------------------------------------

def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        print(f"  {'PASS' if cond else 'FAIL'} {name} {detail}")
        if not cond:
            failures.append(name)

    # 1. Sealed guard refuses sealed / test-bank paths (Lane 07 guard).
    for bad in ("test-bank/sealed/fresh-20.json", "data/sealed/x.jsonl"):
        try:
            recall_eval.guard_path(bad)
            check(f"guard_refuses_{bad}", False, "no error raised")
        except SystemExit as exc:
            check(f"guard_refuses_{bad}", exc.code == 2, f"exit={exc.code}")

    # 2. --suite sealed is refused with the sealed message.
    try:
        validate_suite("sealed")
        check("suite_sealed_refused", False, "no error raised")
    except SystemExit as exc:
        check("suite_sealed_refused", exc.code == 2, f"exit={exc.code}")
    check("suite_all_ok", validate_suite("all") == "all")
    try:
        validate_suite("bogus")
        check("suite_bogus_refused", False, "no error raised")
    except SystemExit as exc:
        check("suite_bogus_refused", exc.code == 2, f"exit={exc.code}")

    # 3. Frozen validation SHA verifies on disk.
    info = verify_validation_sha()
    check("validation_sha_verified", info["ok"], info["actual"][:12])

    # 4. C1 key validation: full dict passes, missing key aborts.
    full = {k: [] if k in ("sections", "court", "escalations") else None
            for k in C1_REQUIRED_KEYS}
    full["question"] = "q"
    full["latency_ms"] = 1.0
    check("c1_keys_ok", _validate_c1_result(dict(full), "q") is not None)
    try:
        bad = dict(full)
        del bad["sections"]
        _validate_c1_result(bad, "q")
        check("c1_missing_key_aborts", False, "no error raised")
    except SystemExit as exc:
        check("c1_missing_key_aborts", exc.code == 2, f"exit={exc.code}")

    # 5. Toy 16-Q-style scoring: 2 exact rows -> raw 10.0, capped 9.0
    # (caps bind: G12/sealed/confirmation unverified).
    toy_items = [
        {"id": "T1", "category": "16Q", "question": "q1",
         "gt_ids": ["bnss-144"], "gt_court": ["Magistrate"],
         "gt_escalates": True, "gt_kinds": ["quantum"]},
        {"id": "T2", "category": "16Q", "question": "q2",
         "gt_ids": [], "gt_court": [],
         "gt_escalates": False, "gt_kinds": []},
    ]
    toy_outs = [
        {"sections": ["bnss-144"], "court": ["Magistrate"],
         "escalations": ["quantum"], "prose": "x", "latency_ms": 5.0,
         "extractor": "rule_based", "error": None,
         "_assess_record": {"kept_ids": ["bnss-144"],
                            "candidates_before_gate": ["bnss-144"],
                            "dispositions": {"bnss-144": {"status": "eligible", "reason_codes": []}},
                            "gated_out": [], "prose_fp_hits": []}},
        {"sections": [], "court": [], "escalations": [], "prose": "y",
         "latency_ms": 4.0, "extractor": "rule_based", "error": None,
         "_assess_record": {"kept_ids": [], "candidates_before_gate": [],
                            "dispositions": {}, "gated_out": [],
                            "prose_fp_hits": []}},
    ]
    s = _score_typed_suite(toy_items, toy_outs, legacy_16q_compat=True,
                           project_custody=False, suite_name="16q")
    check("toy_16q_exact_2", s["exact_count"] == 2 and s["n"] == 2,
          str(s["exact"]))
    check("toy_16q_rating", s["raw_formula_rating"] == 10.0
          and s["capped_rating"] == 9.0,
          f"raw={s['raw_formula_rating']} capped={s['capped_rating']}")
    check("toy_16q_fb0_measured", s["fb_count"] == 0
          and s["rows"][0]["fb_measured"] is True
          and s["fb_measured"] is True,
          f"fb={s['fb_count']} suite_measured={s['fb_measured']}")

    # 6. compute_fb passthrough: hma-25 gated for no decree -> Fb 1.
    fb = v7b.compute_fb({
        "kept_ids": ["bnss-144"],
        "candidates_before_gate": ["hma-25", "bnss-144"],
        "dispositions": {
            "hma-25": {"status": "conditional",
                       "reason_codes": ["lump_sum_without_decree_or_hma_proceeding"]},
            "bnss-144": {"status": "eligible", "reason_codes": []},
        },
        "gated_out": ["hma-25: gated (pre_decree_without_hma)"],
    })
    check("fb_hma25_no_decree", fb["fb_count"] == 1 and fb["fb_measured"] is True,
          str(fb))

    # 7. Fp via C1 facts (real-runtime path): HMA 13 prose + divorce_asked
    # supported -> no hit; the SAME prose with empty facts false-fires
    # item 3 (the bug found on H5 during the first verification run).
    _prose = ("You can seek divorce under Section 13 of the Hindu "
              "Marriage Act, 1955.")
    _facts = {"divorce_asked": {"status": "supported", "value": True,
                                "confidence": 1.0, "source": "test"}}
    _out = {"sections": ["hma-13"], "prose": _prose, "facts": _facts}
    _fb, _fbm, _fbd, _fp, _fpm = _fb_fp_for_row(_out)
    check("fp_c1_facts_no_false_hit", _fp == 0 and _fpm is True,
          f"fp={_fp}")
    _out_empty = {"sections": ["hma-13"], "prose": _prose, "facts": {}}
    _fb2, _fbm2, _fbd2, _fp2, _fpm2 = _fb_fp_for_row(_out_empty)
    check("fp_empty_facts_false_fires_item3", _fp2 == 1,
          f"fp={_fp2} (documents why empty facts must never be passed)")

    print(f"SELF-TEST: {'PASS' if not failures else 'FAIL'} ({len(failures)} failures)")
    if failures:
        print("FAILED CHECKS: " + ", ".join(failures))
        return 1
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

SUITE_RUNNERS = {
    "validation": ("validation", run_validation_suite),
    "kaanoon": ("kaanoon", run_kaanoon_suite),
    "16q": ("16q", run_16q_suite),
    "brutal": ("brutal", run_brutal_suite),
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="LAYA v7.1 integrated backtest (Lane E, contract C3): "
                    "score the integrated runtime (C1 run_question) on all "
                    "non-sealed sets with one command. Sealed suites are "
                    "refused — sealed re-runs happen only on Colab/RTX.",
        epilog=f"{CLAIM_RULE} Validation / Kaanoon / 16-Q / Brutal numbers "
               "are proxies and regression numbers, never sealed numbers.",
    )
    parser.add_argument("--mode", default="auto",
                        choices=("auto", "rule-based", "classifier"),
                        help="Runtime mode (default: auto). rule-based is "
                             "the only mode that runs on this VM today.")
    parser.add_argument("--suite", default="all",
                        help="all|validation|kaanoon|16q|brutal (default: "
                             "all). 'sealed' is refused outright.")
    parser.add_argument("--checkpoint", default=None,
                        help="Classifier checkpoint path (passed through to "
                             "run_question; C1 default "
                             "models/v71-classifier/best/model.pt).")
    parser.add_argument("--json-out", default=None,
                        help="Write per-set results + exact command + git "
                             "HEAD as JSON (required unless --self-test).")
    parser.add_argument("--misses", type=int, default=10,
                        help="Print the first N non-exact rows per suite "
                             "(default 10; 0 to suppress).")
    parser.add_argument("--self-test", action="store_true",
                        help="CPU-only harness checks (no scoring runs).")
    args = parser.parse_args()

    if args.self_test:
        return _self_test()
    if not args.json_out:
        parser.error("--json-out is required (unless --self-test)")

    suite = validate_suite(args.suite)
    mode = args.mode
    if mode == "classifier" and args.checkpoint:
        recall_eval.guard_path(args.checkpoint, what="checkpoint")

    sha_info = verify_validation_sha()
    brutal_sha = _sha256(BANK_PATH)
    gt16_sha = _sha256(GT_16_PATH)
    if brutal_sha != FROZEN_BRUTAL_SHA256:
        print(
            f"WARNING: brutal bank SHA differs from the frozen value "
            f"({brutal_sha[:12]}… vs {FROZEN_BRUTAL_SHA256[:12]}…). The "
            f"bank is FROZEN — investigate before trusting the brutal "
            f"number.",
            file=sys.stderr,
        )
    head, dirty = _git_head()

    runtime = load_runtime()
    _print_header(mode, suite, runtime, sha_info)

    wanted = (
        ["validation", "kaanoon", "16q", "brutal"]
        if suite == "all" else [suite]
    )
    results: dict[str, Any] = {}
    for name in wanted:
        _label, runner = SUITE_RUNNERS[name]
        summary = runner(runtime, mode, args.checkpoint)
        results[name] = summary
        _print_section_summary(name, summary)
        _print_baseline_delta(name, summary)
        misses = [r for r in summary["rows"] if not r["exact"]]
        if args.misses and misses:
            print(f"--- first {min(args.misses, len(misses))} misses "
                  f"({len(misses)} total) ---")
            for r in misses[: args.misses]:
                print(f"  MISS {r['id']}: pred={r['predicted'] if 'predicted' in r else r.get('pred')} "
                      f"expected={r['expected'] if 'expected' in r else r.get('gt')} "
                      f"tag={r.get('tag', '')}")
        print()

    report = {
        "harness": "tests/integrated_backtest.py (Lane E, contract C3)",
        "claim_rule": CLAIM_RULE,
        "command": " ".join(sys.argv),
        "mode": mode,
        "suite": suite,
        "checkpoint": args.checkpoint,
        "git_head": head,
        "git_dirty": dirty,
        "runtime": {"source": runtime.source, "note": runtime.note},
        "validation_sha256": sha_info,
        "brutal_sha256": {
            "path": str(BANK_PATH), "actual": brutal_sha,
            "expected": FROZEN_BRUTAL_SHA256,
            "ok": brutal_sha == FROZEN_BRUTAL_SHA256,
        },
        "gt16_sha256": {"path": str(GT_16_PATH), "actual": gt16_sha},
        "results": results,
        "baselines": KNOWN_BASELINES,
    }
    out_path = Path(args.json_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(f"summary JSON written: {out_path}")
    print(f"{CLAIM_RULE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
