"""LAYA v7.1 unified integration runtime (Lane C, contract C1).

ONE entry point for the whole system::

    from src.laya_integrated import run_question
    run_question("My husband ...", mode="auto")

    python3 src/laya_integrated.py --mode auto "question"
    python3 src/laya_integrated.py --mode rule-based --json "question"
    python3 src/laya_integrated.py --self-test

Pipeline (new wiring only — no pipeline module is edited here)::

    question
      -> laya_lang_normalizer.detect_script_locale   (en / kn / kn_roman)
      -> extractor
           * classifier: laya_v7_classifier.predict_text, ONLY when a real
             trained checkpoint exists (models/v71-classifier/best/model.pt
             by default, or --checkpoint PATH)
           * rule-based: laya_v7_extractor.extract_v7(mode="evidence",
             device="cpu") — the zero-model grounded evidence extractor
      -> laya_v7_graph.evaluate_stage2_v7   (Graph v4, frozen — called, not edited)
      -> laya_prose_v2.render_prose        (frozen — called, not edited)

Why a NEW file instead of extending ``src/laya_v7.py``: ``laya_v7.py`` is the
frozen v7 entry point whose ``assess_v7`` hard-codes the old extractor modes
(``auto``/``laya``/``structured``/``evidence`` — the neural ones need
PIXMELT/laya or Qwen weights and CUDA) and the old output shape. The v7.1
contract needs different mode semantics (``classifier``/``rule-based``/
``auto`` keyed on a *trained v7.1 checkpoint*), the exact C1 output keys, and
clean fallback semantics (say when the classifier did NOT run). Extending
``laya_v7.py`` would have changed a frozen file's behaviour for existing
callers (``tests/v7_backtest.py``, ``tests/recall_eval.py``); a new module
leaves every existing caller untouched.

Mode semantics
--------------
* ``auto`` (default): classifier if a checkpoint file exists at the default
  path (or ``--checkpoint``), else rule-based with ``fallback_reason`` set.
  If a checkpoint exists but cannot be loaded (e.g. no torch on this VM),
  ``auto`` also falls back to rule-based and says so — ``auto`` never fails
  just because the neural path is unavailable.
* ``classifier``: hard requirement. No checkpoint file -> exit 2 (CLI) /
  ``FileNotFoundError`` (API) with "no trained checkpoint found; run the
  Colab notebook first or use --mode rule-based". A checkpoint that exists
  but cannot be loaded (no torch) is likewise exit 2 with a clear message.
* ``rule-based``: always works on CPU today. ``extractor="rule_based"``,
  ``checkpoint=None``, ``fallback_reason=None`` (no fallback happened — the
  rule-based path was explicitly requested).

The classifier path NEVER fakes a run: ``extractor="classifier"`` appears
only when ``predict_text`` actually executed on a loaded checkpoint. The
rule-based baseline this path reproduces is the frozen-split evidence-mode
number, 261/500 (52.2%) — see docs/recall_status.md §2–§3; this module
introduces no new extraction behaviour.

Checkpoint layout (contract C2, owned by Lane B)
-------------------------------------------------
``models/v71-classifier/best/model.pt`` + ``config.json`` + ``thresholds.json``
in the same directory. ``load_checkpoint`` reads the config from inside
``model.pt``. When present, ``thresholds.json`` supplies temperatures and
the classifier's per-head neutral fallback policy. ``--checkpoint``
accepts a ``model.pt`` file or a directory (``.../best`` or
``.../v71-classifier`` — ``best/model.pt`` is appended as needed).

This VM has NO GPU and NO torch: the classifier path raises a clear
``RuntimeError`` here instead of a fake score. Train on Colab (see
``notebooks/laya_v71_train_backtest.ipynb``, Lane D) and the same code
activates the classifier path unchanged.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
import math
import sys
from pathlib import Path
from time import perf_counter
from typing import Any

# This file is run as ``python3 src/laya_integrated.py`` (script dir = src/,
# so plain ``import laya_v7`` would fail) and as ``python -m
# src.laya_integrated`` from the repo root. Resolve the repo root from this
# file's location and import the pipeline as the ``src`` package either way.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.laya_lang_normalizer import detect_script_locale  # noqa: E402
from src.laya_prose_v2 import prose_forbidden_check, render_prose  # noqa: E402
from src.laya_v7_extractor import extract_v7  # noqa: E402
from src.laya_v7_graph import evaluate_stage2_v7  # noqa: E402
from src.laya_v7_schema import FactEvidence, IssueEvidence  # noqa: E402

DEFAULT_CHECKPOINT = REPO_ROOT / "models" / "v71-classifier" / "best" / "model.pt"

MODES = ("auto", "classifier", "rule-based")

# Classifier enum vocab -> the plain strings Graph v4 compares against
# (recall_eval.py coordinator fix: corpus "M"/"F"/"U" map to male/female/
# unknown; the live extractor already produces female/male/unknown).
_SEX_MAP = {"F": "female", "M": "male", "U": "unknown"}

# Cache of loaded classifiers, keyed by resolved checkpoint path, so the
# harness (Lane E) calling run_question() per question does not reload the
# model every time. Values are (model, tokenizer, config).
_CLASSIFIER_CACHE: dict[str, tuple[Any, Any, Any]] = {}


# ---------------------------------------------------------------------------
# Checkpoint resolution
# ---------------------------------------------------------------------------

def resolve_checkpoint(checkpoint: str | Path | None) -> Path:
    """Resolve a --checkpoint value to a model.pt file path.

    Accepts a ``model.pt`` file, a ``.../best`` directory, or a
    ``.../v71-classifier`` directory (``best/model.pt`` appended).
    ``None`` -> the C2 default, ``models/v71-classifier/best/model.pt``.
    """
    if checkpoint is None:
        return DEFAULT_CHECKPOINT
    p = Path(checkpoint)
    if p.is_file():
        return p
    if p.suffix == ".pt":
        return p  # does not exist yet — caller reports it as missing
    if (p / "model.pt").is_file() or p.name == "best":
        return p / "model.pt"
    return p / "best" / "model.pt"


def checkpoint_exists(checkpoint: str | Path | None = None) -> bool:
    """True iff a trained checkpoint file exists at the resolved path."""
    return resolve_checkpoint(checkpoint).is_file()


# ---------------------------------------------------------------------------
# Classifier path (lazy imports: the rule-based path must work even if the
# classifier module is mid-edit by Lane B, and must not import torch)
# ---------------------------------------------------------------------------

def _select_device() -> str:
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def _load_classifier(checkpoint_path: Path) -> tuple[Any, Any, Any]:
    """Load (model, tokenizer, config) for a checkpoint, cached per path.

    Raises RuntimeError with an actionable message when torch/transformers
    are unavailable or the checkpoint cannot be loaded. Never returns a fake model.
    """
    key = str(checkpoint_path)
    if key in _CLASSIFIER_CACHE:
        return _CLASSIFIER_CACHE[key]
    try:
        from src.laya_v7_classifier import load_checkpoint
    except ImportError as exc:
        raise RuntimeError(
            "Could not import src.laya_v7_classifier "
            f"(Lane B may be mid-edit): {exc}"
        ) from exc
    model, cfg = load_checkpoint(checkpoint_path, device=_select_device())
    try:
        from transformers import AutoTokenizer
    except ImportError as exc:
        raise RuntimeError(
            "transformers is not installed; cannot load the classifier "
            "tokenizer. Train/run on Colab instead."
        ) from exc
    tokenizer = AutoTokenizer.from_pretrained(cfg.backbone)
    _CLASSIFIER_CACHE[key] = (model, tokenizer, cfg)
    return model, tokenizer, cfg


def _predict_classifier(text: str, checkpoint_path: Path) -> dict[str, Any]:
    from src.laya_v7_classifier import decode_with_thresholds, predict_text

    model, tokenizer, cfg = _load_classifier(checkpoint_path)
    calibration_path = checkpoint_path.with_name("thresholds.json")
    if not calibration_path.is_file():
        return predict_text(model, tokenizer, text, cfg)

    calibration = json.loads(calibration_path.read_text(encoding="utf-8"))
    temperatures = {
        key: float(calibration.get(key, getattr(cfg, key)))
        for key in ("temperature_issue", "temperature_fact")
    }
    if any(not math.isfinite(value) or value <= 0 for value in temperatures.values()):
        raise ValueError("Calibration temperatures must be finite and positive.")
    pred = predict_text(model, tokenizer, text, replace(cfg, **temperatures))
    decoded = decode_with_thresholds(
        {name: item["probs"] for name, item in pred["issues"].items()},
        {name: item["probs"] for name, item in pred["facts"].items()},
        calibration,
    )
    for group, key in (("issues", "intent"), ("facts", "state")):
        for name, label in decoded[group].items():
            item = pred[group][name]
            item[key] = label
            item["confidence"] = item["probs"].get(label, 0.0)
    return pred


BRIDGE_DERIVED_KEYS = frozenset({
    "arrears_recovery_asked",
    "custody_negated",
    "first_demand_never_made",
    "forum_question_asked",
    "hypothetical_or_joint_prop_fact_only",
    "interim_only_asked",
    "interim_unpaid_with_joint_or_parallel",
    "judicial_separation_act",
    "maintenance_negated",
    "maintenance_variation_asked",
    "money_fact_child_or_parallel",
    "no_dispute_empty",
    "post_decree_lump_sum_enforcement",
    "procedure_how_to_asked",
    "pwdva_monetary_basis_blocked",
    "residence_negated",
    "stay_in_house_under_eviction_pressure",
    "stridhan_abandoned_or_undisputed",
    "stridhan_held_by_inlaws_refused",
    "stridhan_negated",
    "stridhan_safe_in_own_possession",
    "urgent_safety_risk",
    "violence_negated",
})


def _attach_bridge_facts(
    issues: dict[str, Any],
    facts: dict[str, Any],
    enums_plain: dict[str, Any],
    question_text: str = "",
) -> None:
    """Derive all graph-consumed keys uncovered by the 28 classifier fact heads."""
    def _is_sup(k: str) -> bool:
        ev = facts.get(k)
        return isinstance(ev, FactEvidence) and ev.status == "supported"

    def _is_den(k: str) -> bool:
        ev = facts.get(k)
        return isinstance(ev, FactEvidence) and ev.status == "denied"

    def _req(k: str) -> bool:
        ev = issues.get(k)
        return isinstance(ev, IssueEvidence) and ev.intent == "requested"

    def _set(k: str, val: Any, *, source: str = "classifier_bridge") -> None:
        if k in facts:
            return
        if isinstance(val, bool):
            status = "supported" if val else "denied"
        elif val is None or val == "":
            status = "unknown"
        else:
            status = "supported"
        facts[k] = FactEvidence(key=k, status=status, value=val, source=source, confidence=1.0 if status != "unknown" else 0.0)

    negated_issues = facts.get("negated_issues") or set()

    # Semantic derivations from classifier predictions
    urgent = _is_sup("violence") or _is_sup("child_safety_risk")
    _set("urgent_safety_risk", urgent)
    _set("interim_only_asked", _is_sup("interim_asked") and _is_sup("proceeding_pending_hma") and not _is_sup("money_fact"))
    _set("money_fact_child_or_parallel", _is_sup("money_fact") and (_is_sup("child_maintenance_only") or not _is_sup("existing_order_enforcement")))
    _set("stay_in_house_under_eviction_pressure", _is_sup("residence_claim") and (_is_sup("coercive_eviction_or_lockout") or _is_sup("violence")))
    _set("stridhan_held_by_inlaws_refused", _is_sup("stridhan_claim") and (_is_sup("demand_made") or _is_sup("stridhan_sold_or_mortgaged")))
    _set("stridhan_safe_in_own_possession", _is_den("stridhan_claim"))
    _set("stridhan_abandoned_or_undisputed", _is_den("stridhan_claim"))
    _set("first_demand_never_made", _is_sup("stridhan_claim") and _is_den("demand_made"))

    for issue_key, fact_key, neg_key in (
        ("custody", "custody_claim", "custody_negated"),
        ("maintenance", "money_fact", "maintenance_negated"),
        ("residence", "residence_claim", "residence_negated"),
        ("stridhan", "stridhan_claim", "stridhan_negated"),
        ("violence", "violence", "violence_negated"),
    ):
        _set(neg_key, (issue_key in negated_issues) or _is_den(fact_key))

    proc_ev = issues.get("procedure")
    proc_req = isinstance(proc_ev, IssueEvidence) and proc_ev.intent == "requested"
    proc_any = isinstance(proc_ev, IssueEvidence) and proc_ev.intent in ("requested", "incidental")
    _set("forum_question_asked", proc_any)
    _set("procedure_how_to_asked", proc_req)
    any_requested = any(_req(name) for name in issues)
    _set("no_dispute_empty", _is_sup("in_scope") and not any_requested and _is_den("stridhan_claim"))
    modality = enums_plain.get("modality_time", {}).get("value", "present")
    _set(
        "hypothetical_or_joint_prop_fact_only",
        modality == "hypothetical"
        or (_is_sup("joint_property_claim") and not _is_sup("proceeding_pending_hma") and not _is_sup("being_filed") and not _req("divorce")),
    )

    # Deterministic grounded extraction for post-order / Act / strict PWDVA keys
    if question_text:
        try:
            from src.laya_v7_evidence import extract_grounded_v7
            grounded = extract_grounded_v7(question_text, strict_pwdva=True).get("facts") or {}
            for gkey in (
                "arrears_recovery_asked",
                "maintenance_variation_asked",
                "interim_unpaid_with_joint_or_parallel",
                "post_decree_lump_sum_enforcement",
                "pwdva_monetary_basis_blocked",
            ):
                if gkey in grounded and isinstance(grounded[gkey], FactEvidence):
                    facts[gkey] = grounded[gkey]
        except Exception:
            pass
    for fallback_key in (
        "arrears_recovery_asked",
        "maintenance_variation_asked",
        "interim_unpaid_with_joint_or_parallel",
        "post_decree_lump_sum_enforcement",
        "pwdva_monetary_basis_blocked",
    ):
        _set(fallback_key, False, source="classifier_bridge_default")
    if "judicial_separation_act" not in facts:
        facts["judicial_separation_act"] = FactEvidence(
            key="judicial_separation_act", status="unknown", value=None,
            source="classifier_bridge_default", confidence=0.0,
        )


_COUPLED_ISSUE_FACT: tuple[tuple[str, str], ...] = (
    ("maintenance", "money_fact"),
    ("divorce", "divorce_asked"),
    ("custody", "custody_claim"),
    ("violence", "violence"),
    ("residence", "residence_claim"),
    ("stridhan", "stridhan_claim"),
    ("joint_property", "joint_property_claim"),
    ("restitution", "restitution_asked"),
    ("birth_certificate", "birth_cert_asked"),
    ("dv_compensation", "dv_injury_comp_asked"),
)


def _sync_coupled_pairs(
    pred: dict[str, Any],
    issues: dict[str, Any],
    facts: dict[str, Any],
) -> None:
    """Keep strongly predicted issues and primary facts mutually consistent."""
    raw_issues = pred.get("issues") or {}
    raw_facts = pred.get("facts") or {}

    for iss_key, fac_key in _COUPLED_ISSUE_FACT:
        iss_ev = issues.get(iss_key)
        fac_ev = facts.get(fac_key)
        if (
            isinstance(iss_ev, IssueEvidence)
            and iss_ev.intent == "requested"
            and iss_ev.confidence >= 0.50
            and isinstance(fac_ev, FactEvidence)
            and fac_ev.status == "unknown"
        ):
            p_sup = float((raw_facts.get(fac_key) or {}).get("probs", {}).get("supported", 0.0))
            if p_sup >= 0.20:
                facts[fac_key] = FactEvidence(
                    key=fac_key,
                    status="supported",
                    value=True,
                    source="classifier_coupled",
                    confidence=iss_ev.confidence,
                )

    for iss_key, fac_key in _COUPLED_ISSUE_FACT + (("residence", "coercive_eviction_or_lockout"),):
        iss_ev = issues.get(iss_key)
        fac_ev = facts.get(fac_key)
        if (
            isinstance(fac_ev, FactEvidence)
            and fac_ev.status == "supported"
            and fac_ev.confidence >= 0.70
            and isinstance(iss_ev, IssueEvidence)
            and iss_ev.intent == "uncertain"
        ):
            p_req = float((raw_issues.get(iss_key) or {}).get("probs", {}).get("requested", 0.0))
            if p_req >= 0.20:
                issues[iss_key] = IssueEvidence(
                    issue=iss_key,
                    intent="requested",
                    source="classifier_coupled",
                    confidence=fac_ev.confidence,
                )
                if fac_key == "coercive_eviction_or_lockout":
                    res_ev = facts.get("residence_claim")
                    if isinstance(res_ev, FactEvidence) and res_ev.status == "unknown":
                        facts["residence_claim"] = FactEvidence(
                            key="residence_claim",
                            status="supported",
                            value=True,
                            source="classifier_coupled",
                            confidence=fac_ev.confidence,
                        )


def _classifier_to_stage1(pred: dict[str, Any], question_text: str = "") -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Convert a predict_text() result to (issues, facts, enums) for Graph v4.

    Mirrors tests/recall_eval.py::predict_sections_from_stage1: issue
    intents become IssueEvidence, fact states become FactEvidence, denied
    issues become the negated_issues set, and claimant_sex F/M/U maps to
    female/male/unknown (the strings evaluate_stage2_v7 compares against).
    ``in_scope`` is one of the classifier's 28 facts and flows through
    untouched, so an out-of-scope prediction still takes the OOS branch.
    """
    issues: dict[str, Any] = {}
    for name, val in (pred.get("issues") or {}).items():
        intent = val.get("intent", "uncertain") if isinstance(val, dict) else str(val)
        if intent not in ("requested", "incidental", "denied", "uncertain"):
            intent = "uncertain"
        conf = float(val.get("confidence", 0.0)) if isinstance(val, dict) else 0.0
        issues[name] = IssueEvidence(
            issue=name, intent=intent, source="classifier", confidence=conf
        )
    facts: dict[str, Any] = {}
    for name, val in (pred.get("facts") or {}).items():
        state = val.get("state", "unknown") if isinstance(val, dict) else str(val)
        if state not in ("supported", "denied", "unknown", "conflicting"):
            state = "unknown"
        conf = float(val.get("confidence", 0.0)) if isinstance(val, dict) else 0.0
        value: Any = True if state == "supported" else (False if state == "denied" else None)
        facts[name] = FactEvidence(
            key=name, status=state, value=value, source="classifier", confidence=conf
        )
    _sync_coupled_pairs(pred, issues, facts)
    enums_plain: dict[str, Any] = {}
    for head, val in (pred.get("enums") or {}).items():
        value = val.get("value") if isinstance(val, dict) else val
        conf = float(val.get("confidence", 0.0)) if isinstance(val, dict) else 0.0
        enums_plain[head] = {"value": value, "confidence": round(conf, 4)}
    # Enum heads live in the facts dict for Graph v4 (sex/role gating).
    sex = enums_plain.get("claimant_sex", {}).get("value", "U")
    sex_str = _SEX_MAP.get(str(sex), "unknown")
    facts["claimant_sex"] = FactEvidence(
        key="claimant_sex",
        status="supported" if sex_str != "unknown" else "unknown",
        value=sex_str, source="classifier",
        confidence=enums_plain.get("claimant_sex", {}).get("confidence", 0.0),
    )
    role = enums_plain.get("claimant_role", {}).get("value", "other")
    facts["claimant_role"] = FactEvidence(
        key="claimant_role",
        status="supported" if str(role) in ("spouse", "parent", "child") else "unknown",
        value=str(role), source="classifier",
        confidence=enums_plain.get("claimant_role", {}).get("confidence", 0.0),
    )
    facts["negated_issues"] = {
        name for name, ev in issues.items() if ev.intent == "denied"
    }
    facts["open_fact_markers"] = set()
    _attach_bridge_facts(issues, facts, enums_plain, question_text)
    return issues, facts, enums_plain


def _auto_stage1(
    question: str,
    language: str,
    checkpoint_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Hybrid grounded-evidence + multilingual MuRIL extraction for mode='auto'.

    Grounded English rules anchor active English claims (preserving high
    precision on hard-negative gates and third-person hypotheticals), while
    calibrated MuRIL handles Kannada, Kanglish, and paraphrased English
    queries where English patterns are silent.
    """
    ev_issues, ev_facts, ev_enums = _rule_based_stage1(question, language)
    ev_active = any(
        isinstance(v, IssueEvidence) and v.intent in ("requested", "denied")
        for v in ev_issues.values()
    ) or any(
        isinstance(v, FactEvidence)
        and v.status == "supported"
        and v.key not in ("in_scope", "domestic_relationship")
        for v in ev_facts.values()
    )

    ev_in_scope = ev_facts.get("in_scope")
    ev_oos = isinstance(ev_in_scope, FactEvidence) and ev_in_scope.status == "denied"
    if language == "en" and (ev_active or ev_oos):
        return ev_issues, ev_facts, ev_enums

    pred = _predict_classifier(question, checkpoint_path)
    clf_issues, clf_facts, clf_enums = _classifier_to_stage1(pred, question)

    pending_ev = clf_facts.get("proceeding_pending_hma")
    if isinstance(pending_ev, FactEvidence) and pending_ev.status == "supported" and pending_ev.confidence < 0.65:
        clf_facts["proceeding_pending_hma"] = FactEvidence(
            key="proceeding_pending_hma", status="unknown", value=None,
            source="auto_guard", confidence=0.0,
        )

    if ev_active:
        for name, e_ev in ev_issues.items():
            c_ev = clf_issues.get(name)
            if (
                isinstance(e_ev, IssueEvidence)
                and e_ev.intent == "requested"
                and (not isinstance(c_ev, IssueEvidence) or c_ev.intent == "uncertain")
            ):
                clf_issues[name] = e_ev
        for iss_key, fac_key in _COUPLED_ISSUE_FACT:
            e_fac = ev_facts.get(fac_key)
            c_fac = clf_facts.get(fac_key)
            if (
                isinstance(e_fac, FactEvidence)
                and e_fac.status == "supported"
                and (not isinstance(c_fac, FactEvidence) or c_fac.status == "unknown")
            ):
                clf_facts[fac_key] = e_fac
    return clf_issues, clf_facts, clf_enums


# ---------------------------------------------------------------------------
# Rule-based path
# ---------------------------------------------------------------------------

def _rule_based_stage1(text: str, language: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Zero-model grounded extraction (evidence mode, CPU).

    ``extract_v7(mode="evidence")`` — the exact path behind the frozen-split
    baseline 261/500 (52.2%). ``locale="kn"`` is passed for Kannada-script
    and Kanglish input so the extractor records lang "kn"; in evidence mode
    no translation model is invoked, so this changes no extraction behaviour.
    """
    extracted = extract_v7(
        text,
        locale="kn" if language in ("kn", "kn_roman") else None,
        mode="evidence",
        device="cpu",
    )
    facts = dict(extracted["facts"])
    enums_plain = _enums_from_facts(facts)
    return extracted["issues"], facts, enums_plain


def _enums_from_facts(facts: dict[str, Any]) -> dict[str, Any]:
    """Derive the classifier-shaped enum dict from grounded facts.

    The rule-based extractor does not predict modality_time, so it defaults
    to "present" with confidence 0.0 (explicitly "not detected", not a
    measured prediction). Sex/role come from the grounded facts; unknown
    maps to the classifier defaults U / other.
    """
    def _fact_value(key: str) -> Any:
        val = facts.get(key)
        if isinstance(val, FactEvidence):
            return val.value
        return val

    def _fact_conf(key: str) -> float:
        val = facts.get(key)
        if isinstance(val, FactEvidence):
            return round(float(val.confidence), 4)
        return 0.0

    sex = _fact_value("claimant_sex") or "unknown"
    sex_code = {"female": "F", "male": "M"}.get(str(sex), "U")
    role = _fact_value("claimant_role") or "unknown"
    role_val = str(role) if str(role) in ("spouse", "parent", "child", "other") else "other"
    return {
        "claimant_sex": {"value": sex_code, "confidence": _fact_conf("claimant_sex")},
        "claimant_role": {"value": role_val, "confidence": _fact_conf("claimant_role")},
        "modality_time": {"value": "present", "confidence": 0.0},
    }


# ---------------------------------------------------------------------------
# Plain-JSON projections (contract C1 output shape)
# ---------------------------------------------------------------------------

def _plain_issues(issues: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name in sorted(issues):
        ev = issues[name]
        if isinstance(ev, IssueEvidence):
            out[name] = {
                "intent": ev.intent,
                "confidence": round(float(ev.confidence), 4),
                "source": ev.source,
            }
        elif isinstance(ev, dict):
            out[name] = {
                "intent": ev.get("intent", "uncertain"),
                "confidence": round(float(ev.get("confidence", 0.0)), 4),
                "source": ev.get("source", "unknown"),
            }
        else:
            out[name] = {"intent": str(ev), "confidence": 0.0, "source": "unknown"}
    return out


def _plain_facts(facts: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name in sorted(facts):
        if name in ("negated_issues", "open_fact_markers") or name.startswith("_"):
            continue
        val = facts[name]
        if isinstance(val, FactEvidence):
            value: Any = val.value
            if isinstance(value, set):
                value = sorted(value)
            out[name] = {
                "status": val.status,
                "value": value,
                "confidence": round(float(val.confidence), 4),
                "source": val.source,
            }
        elif isinstance(val, dict) and "status" in val:
            out[name] = {
                "status": val.get("status"),
                "value": val.get("value"),
                "confidence": round(float(val.get("confidence", 0.0)), 4),
                "source": val.get("source", "unknown"),
            }
        elif isinstance(val, set):
            out[name] = {"status": "unknown", "value": sorted(val), "confidence": 0.0, "source": "unknown"}
        else:
            out[name] = {"status": "unknown", "value": val, "confidence": 0.0, "source": "unknown"}
    return out


# ---------------------------------------------------------------------------
# Public API (contract C1)
# ---------------------------------------------------------------------------

def run_question(
    text: str,
    mode: str = "auto",
    checkpoint: str | Path | None = None,
) -> dict[str, Any]:
    """Run one question end to end. Returns the exact C1 output dict.

    Keys: question, language, extractor ("classifier" | "rule_based"),
    checkpoint (path or None), fallback_reason (None or str), issues, facts,
    enums, sections (sorted list), court, escalations (list of kind strings,
    in Graph v4's canonical order), prose (str or None), latency_ms, plus
    route_trace and error for evaluation.

    Raises FileNotFoundError in mode="classifier" when no checkpoint exists,
    and RuntimeError when a checkpoint exists but cannot be loaded (e.g. no
    torch on this VM). In mode="auto" those conditions fall back to the
    rule-based extractor instead, with fallback_reason saying so.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("run_question requires a non-empty question string")
    mode_norm = mode.replace("_", "-").lower()
    if mode_norm not in MODES:
        raise ValueError(f"mode must be one of {MODES}, got {mode!r}")

    t0 = perf_counter()
    question = text.strip()
    language = str(detect_script_locale(question).get("lang", "en"))

    extractor = "rule_based"
    checkpoint_str: str | None = None
    fallback_reason: str | None = None
    issues: dict[str, Any]
    facts: dict[str, Any]
    enums: dict[str, Any]

    resolved = resolve_checkpoint(checkpoint)
    if mode_norm == "classifier":
        if not resolved.is_file():
            raise FileNotFoundError(
                f"no trained checkpoint found at {resolved}; "
                "run the Colab notebook first or use --mode rule-based"
            )
        try:
            pred = _predict_classifier(question, resolved)
        except (RuntimeError, OSError, ValueError, TypeError, AttributeError) as exc:
            raise RuntimeError(
                f"classifier checkpoint exists at {resolved} but cannot run "
                f"here: {exc}"
            ) from exc
        issues, facts, enums = _classifier_to_stage1(pred, question)
        extractor = "classifier"
        checkpoint_str = str(resolved)
    elif mode_norm == "auto" and resolved.is_file():
        try:
            issues, facts, enums = _auto_stage1(question, language, resolved)
            extractor = "classifier"
            checkpoint_str = str(resolved)
        except Exception as exc:  # auto never fails on the neural path
            fallback_reason = (
                f"classifier checkpoint found at {resolved} but could not "
                f"run ({exc}); using rule-based evidence extractor"
            )
            issues, facts, enums = _rule_based_stage1(question, language)
    else:
        if mode_norm == "auto":
            fallback_reason = (
                f"no trained checkpoint found at {resolved}; using "
                "rule-based evidence extractor — run the Colab notebook "
                "first to train one"
            )
        issues, facts, enums = _rule_based_stage1(question, language)

    # Graph v4 (frozen) + prose renderer (frozen) — called, never edited.
    decision = evaluate_stage2_v7(issues, facts)
    prose_rec = {
        "in_scope": decision["in_scope"],
        "kept_ids": decision["kept_ids"],
        "court_live": decision["court_live"],
        "court_source": decision["court_source"],
        "escalations_typed": decision["escalations_typed"],
        "escalation_kinds": decision["escalation_kinds"],
    }
    route_trace = {
        "kept_ids": decision["kept_ids"],
        "candidates_before_gate": decision["candidates_before_gate"],
        "dispositions": decision["dispositions"],
        "gated_out": decision["gated_out"],
    }
    error = None
    try:
        prose_out = render_prose(prose_rec, decision["facts"])
        prose: str | None = prose_out["prose"]
        hits, flags = prose_forbidden_check(
            prose, decision["kept_ids"], decision["gated_out"], decision["facts"],
        )
        route_trace.update(prose_fp_hits=hits, prose_quality_flags=flags)
        if prose_out.get("status") != "ok" or hits:
            prose = None
            error = "prose_validation_error"
    except Exception:
        prose = None
        error = "prose_validation_error"

    latency_ms = round((perf_counter() - t0) * 1000.0, 1)
    return {
        "question": question,
        "language": language,
        "extractor": extractor,
        "checkpoint": checkpoint_str,
        "fallback_reason": fallback_reason,
        "issues": _plain_issues(issues),
        "facts": _plain_facts(facts),
        "enums": enums,
        "sections": sorted(decision["kept_ids"]),
        "court": list(decision["court_live"]),
        "escalations": list(decision["escalation_kinds"]),
        "prose": prose,
        "route_trace": route_trace,
        "error": error,
        "latency_ms": latency_ms,
    }


# ---------------------------------------------------------------------------
# Self-test (hand-written questions — NOT copied from any test bank, the
# sealed sets, or the 16-Q set)
# ---------------------------------------------------------------------------

SELF_TEST_QUESTIONS = [
    # English: maintenance + child costs, no case filed.
    "I am a mother of a ten-year-old boy. My husband moved out of our home "
    "last year and sends no money at all. I work part-time and struggle to "
    "pay the rent and my son's school costs. What can I ask the court for?",
    # Kannada script (own wording): husband pays no maintenance, daughter
    # lives with the speaker, can she go to court?
    "ನನ್ನ ಗಂಡ ನನಗೆ ಜೀವನಾಂಶ ಕೊಡುತ್ತಿಲ್ಲ. ನನ್ನ ಮಗಳು ನನ್ನ ಜೊತೆಯಲ್ಲೇ ಇದ್ದಾಳೆ. "
    "ನಾನು ಕೋರ್ಟಿಗೆ ಹೋಗಬಹುದೇ?",
    # Kanglish (own wording): same situation in Romanized Kannada.
    "Nanna ganda nange maintenance koduttilla, nanna magu nanna jothe ide, "
    "nanu court ge hogabahude?",
]


def self_test() -> list[dict[str, Any]]:
    """Run the 3 hand-written sample questions end to end (rule-based)."""
    return [run_question(q, mode="rule-based") for q in SELF_TEST_QUESTIONS]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="LAYA v7.1 unified runtime: one entry point for the "
        "family-law decision graph (classifier when a trained checkpoint "
        "exists, else the rule-based evidence extractor)."
    )
    parser.add_argument("question", nargs="?", default=None,
                        help="family-law question (or omit to read from stdin)")
    parser.add_argument("--mode", choices=MODES, default="auto",
                        help="classifier | rule-based | auto (default)")
    parser.add_argument("--checkpoint", default=None,
                        help="path to model.pt, or to its .../best or "
                        "models/<name> directory (default: "
                        "models/v71-classifier/best/model.pt)")
    parser.add_argument("--json", action="store_true",
                        help="print the full C1 output dict as JSON")
    parser.add_argument("--self-test", action="store_true",
                        help="run 3 hand-written sample questions end to end "
                        "and print each JSON output")
    args = parser.parse_args(argv)

    if args.self_test:
        print(json.dumps(self_test(), indent=2, ensure_ascii=False))
        return 0

    question = args.question
    if question is None:
        if sys.stdin.isatty():
            parser.error("a question is required (positional arg or stdin)")
            return 2
        question = sys.stdin.read().strip()
    if not question or not question.strip():
        print("error: empty question", file=sys.stderr)
        return 2

    try:
        result = run_question(question, mode=args.mode, checkpoint=args.checkpoint)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    print(f"language:   {result['language']}")
    print(f"extractor:  {result['extractor']}"
          + (f" (checkpoint: {result['checkpoint']})" if result["checkpoint"] else ""))
    if result["fallback_reason"]:
        print(f"fallback:   {result['fallback_reason']}")
    print(f"sections:   {', '.join(result['sections']) or '(none)'}")
    print(f"court:      {', '.join(result['court']) or '(none)'}")
    print(f"escalations:{', '.join(result['escalations']) or '(none)'}")
    print(f"latency:    {result['latency_ms']} ms")
    print()
    print(result["prose"] or "(no prose rendered)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
