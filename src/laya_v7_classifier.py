"""LAYA v7.1 multi-head Stage 0/1 classifier (V71-P1-3, plan docs/10x_plane.md §1.2).

Unified multi-head teacher over a permissive-licensed encoder backbone.
CODE ONLY — no training runs on this VM (no GPU / no torch here).

Backbone (config choice, default is the permissive-licensed one):
    - "answerdotai/ModernBERT-large"  (Apache-2.0)  [DEFAULT]
    - "microsoft/deberta-v3-large"     (MIT)
    - "PIXMELT/laya"                   (license MUST be verified at training time;
                                        do not train on it until Lane 06 / the
                                        license audit confirms it is permissive)

Inputs (no regex anchor vetoes for recall — plan §1.2):
    [CLS] <full_question> [SEP]  +  batched [CLS] <clause_i> [SEP]

Heads:
    issue_head  [11, 4]  softmax over (requested, incidental, denied, uncertain)
    fact_head   [28, 4]  softmax over (supported, denied, unknown, conflicting)
    enum_heads  claimant_sex   [F, M, U]
                claimant_role  [spouse, parent, child, other]
                modality_time  [present, past, future, hypothetical, quoted]
    span_attn_pool: token-level evidence spans aligned with clause max-pooling.

Clause-vs-full fusion (plan §1.2):
    requested uses calibrated max(full_p, cmax_p), gated by sentence-local
    denied / hypothetical / third_party gate logits. A gate score >= tau_neg
    vetoes ONLY that clause (it is excluded from the clause max-pool); sibling
    clauses are unaffected. Other intents come from the full-question encoding.

Corpus contract C2 (docs/10x_swarm_state.md) + schema R2
(data/synthetic_v7_1/schema.json): JSONL, one record per example:
    {id, lang, text, issues: {issue: intent}, facts: {fact: state},
     enums: {claimant_sex, claimant_role, modality_time},
     spans: [{start, end, text, key, kind}]}
where a span's ``key`` is a fact-or-issue name and ``kind`` is "fact" |
"issue" (schema.json "span"). The loader derives each span's clause_idx
from its char offsets against split_clauses() (the corpus carries no
clause_idx), and keeps key/kind so the gate/span heads get real
supervision. Legacy Lane 03 sample corpora using {clause_idx, label}
are still accepted. See ASSUMPTIONS in docs/10x_swarm_state/lane-03-p1-3.md
as amended by docs/recall_swarm_state/lane-04-classifier.md (PC-2 fix).

Torch / transformers are imported lazily and guarded: importing this module,
splitting clauses, loading a corpus and computing fusion defaults all work
with NO torch installed. Anything that builds the model raises a clear
RuntimeError telling the operator to run on the RTX 5050 machine instead.
"""

from __future__ import annotations

import json
import math
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

# ---------------------------------------------------------------------------
# Label vocabularies (canonical v7.1 sets — see ASSUMPTIONS in status file)
# ---------------------------------------------------------------------------

ISSUE_INTENTS = ("requested", "incidental", "denied", "uncertain")
FACT_STATES = ("supported", "denied", "unknown", "conflicting")

# 11 issues: exactly the schema order in data/synthetic_v7_1/schema.json
# (contract R2). The plan says 11 issues but never enumerates them; the
# evidence module's 10 triggers + "procedure" (forum / how-to questions)
# is the set, reconciled against the schema by Lane 04 (PC-2 fix,
# 2026-11-27): set-identical to the schema, order now matches it too, so
# label indices line up with the corpus schema by construction.
ISSUES = (
    "maintenance",
    "custody",
    "residence",
    "divorce",
    "stridhan",
    "joint_property",
    "violence",
    "dv_compensation",
    "restitution",
    "birth_certificate",
    "procedure",
)

# 28 atomic facts: exactly the schema order in data/synthetic_v7_1/schema.json
# (contract R2). PC-2 fix (Lane 04, 2026-11-27): Lane 03's list had
# "stridhan_held_or_disposed" (a DERIVED downstream fact — graph L210
# derives it from stridhan_claim; it appears in NO corpus record) and was
# missing "in_scope" (present in all 5,000 records: supported 4,712 /
# denied 288 — the out-of-scope signal, 5.8% denied). Training the old list
# would have left one head permanently unsupervised (all-"unknown") and
# silently dropped in_scope as an "unknown key" on every record. in_scope
# is a real 4-state fact head here: supported = in scope, denied = out of
# scope; it drives the graph's in_scope=False OOS escalation (graph L400)
# and the V71-P1-5 clarification fallback. Enum-valued keys (claimant_sex /
# claimant_role — separate enum heads) stay out, as do derived/meta keys
# (no_dispute_empty, first_demand_never_made, forum_question_asked,
# procedure_how_to_asked, interim_only_asked,
# interim_unpaid_with_joint_or_parallel). "interim_asked" is the canonical
# name for the graph's dead key (graph L453/L468); the evidence module's
# "interim_only_asked" is a narrower variant and maps to it only when the
# corpus uses that spelling (see _FACT_ALIASES). The stridhan disposition
# signal the corpus DOES carry is "stridhan_sold_or_mortgaged".
FACTS = (
    "divorce_asked",
    "mutual_consent",
    "judicial_separation_only",
    "restitution_asked",
    "proceeding_pending_hma",
    "being_filed",
    "decree",
    "money_fact",
    "lump_sum_settlement",
    "existing_order_enforcement",
    "interim_asked",
    "custody_claim",
    "child_fact",
    "minor_child",
    "child_maintenance_only",
    "school_fees_fact",
    "child_safety_risk",
    "residence_claim",
    "coercive_eviction_or_lockout",
    "explicit_residence_order_only",
    "violence",
    "dv_injury_comp_asked",
    "stridhan_claim",
    "stridhan_sold_or_mortgaged",
    "demand_made",
    "joint_property_claim",
    "birth_cert_asked",
    "in_scope",
)

ENUMS = {
    "claimant_sex": ("F", "M", "U"),
    "claimant_role": ("spouse", "parent", "child", "other"),
    "modality_time": ("present", "past", "future", "hypothetical", "quoted"),
}

# Spelling variants the loader accepts (corpus may use the evidence-module
# spellings). Anything else unknown is ignored with a warning, not an error.
_FACT_ALIASES = {
    "interim_only_asked": "interim_asked",
    "dv_injury_comp": "dv_injury_comp_asked",
    "birth_cert": "birth_cert_asked",
    "stridhan_sold": "stridhan_sold_or_mortgaged",
}
_ISSUE_ALIASES = {
    "dv_comp": "dv_compensation",
    "birth_cert": "birth_certificate",
}

# Backbones the code accepts, with the license the plan requires us to check.
# Default is the permissive-licensed one. PIXMELT/laya stays available as a
# config choice only — its license must be verified before any training run.
BACKBONES = {
    "answerdotai/ModernBERT-large": "Apache-2.0",
    "microsoft/deberta-v3-large": "MIT",
    "PIXMELT/laya": "VERIFY-BEFORE-TRAINING",
}

DEFAULT_BACKBONE = "answerdotai/ModernBERT-large"

ISSUE_INDEX = {name: i for i, name in enumerate(ISSUES)}
FACT_INDEX = {name: i for i, name in enumerate(FACTS)}
ISSUE_INTENT_INDEX = {name: i for i, name in enumerate(ISSUE_INTENTS)}
FACT_STATE_INDEX = {name: i for i, name in enumerate(FACT_STATES)}
ENUM_INDEX = {head: {v: i for i, v in enumerate(vals)} for head, vals in ENUMS.items()}


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass
class ClassifierConfig:
    backbone: str = DEFAULT_BACKBONE
    max_seq_len: int = 192
    max_clauses: int = 8
    dropout: float = 0.1
    freeze_backbone: bool = False
    use_lora: bool = False
    # Fusion / calibration (fit on held-out dev by Lane 10, defaults = neutral).
    tau_neg: float = 0.5      # per-clause gate score >= tau_neg vetoes that clause
    temperature_issue: float = 1.0
    temperature_fact: float = 1.0
    # Loss weights for scripts/train_v71_classifier.py (must sum to ~1.0).
    loss_weights: dict[str, float] = field(
        default_factory=lambda: {
            "issue": 0.35,
            "fact": 0.35,
            "enum": 0.15,
            "gate": 0.10,
            "span": 0.05,
        }
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ClassifierConfig":
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in d.items() if k in known})


# ---------------------------------------------------------------------------
# Torch-guarded imports (module must import cleanly with NO torch installed)
# ---------------------------------------------------------------------------

def require_torch():
    """Import torch/transformers or raise an actionable error (no fake run)."""
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise RuntimeError(
            "torch/transformers are not installed on this VM. Do not train here. "
            "Run scripts/train_v71_classifier.py on the user's RTX 5050 machine "
            "(see the EXACT command in that script's docstring). "
            f"Original import error: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Clause splitting (pure python — no tokenizer / torch needed)
# ---------------------------------------------------------------------------

# Split on sentence-terminal punctuation or clause separators, keeping the
# delimiter attached to the preceding clause. Handles Kannada danda (।/॥)
# and the common Latin-script separators in Kanglish text.
_CLAUSE_SPLIT_RE = re.compile(
    r"(?<=[.!?।॥;])\s+|(?<=[,،])\s+(?=[A-Z\u0c80-\u0cff])|\n+"
)


def split_clauses(text: str, max_clauses: int = 8) -> list[dict[str, Any]]:
    """Split a question into clauses with char offsets.

    Returns [{text, start, end}] in order, at most ``max_clauses`` items
    (overflow clauses are merged into the last one so no text is lost).
    A single-clause question returns one clause == the full text.
    """
    text = (text or "").strip()
    if not text:
        return []
    parts = [p for p in _CLAUSE_SPLIT_RE.split(text) if p.strip()]
    if not parts:
        parts = [text]
    clauses: list[dict[str, Any]] = []
    cursor = 0
    for part in parts:
        start = text.find(part.strip(), cursor)
        if start < 0:  # fallback: sequential scan failed, append at cursor
            start = cursor
        end = start + len(part.strip())
        clauses.append({"text": part.strip(), "start": start, "end": end})
        cursor = end
    if len(clauses) > max_clauses:
        merged = clauses[: max_clauses - 1]
        tail_text = " ".join(c["text"] for c in clauses[max_clauses - 1 :])
        merged.append(
            {"text": tail_text, "start": clauses[max_clauses - 1]["start"],
             "end": clauses[-1]["end"]}
        )
        clauses = merged
    return clauses


# ---------------------------------------------------------------------------
# Corpus loading against contract C2 (pure python — no torch needed)
# ---------------------------------------------------------------------------

def _normalise_label(value: Any, allowed: tuple[str, ...], default: str) -> str:
    if isinstance(value, str) and value.strip().lower() in allowed:
        return value.strip().lower()
    return default


def _clause_index_for_offset(clauses: list[dict[str, Any]],
                             start: int, end: int) -> int | None:
    """Clause index containing a span's midpoint (None if no clauses)."""
    if not clauses:
        return None
    mid = (start + end) // 2
    for i, c in enumerate(clauses):
        if c["start"] <= mid < c["end"] or (mid == c["end"] and i == len(clauses) - 1):
            return i
    return len(clauses) - 1


def load_corpus_jsonl(
    path: str | Path, *, strict: bool = False
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Load + normalise a Lane 02 corpus JSONL file (contract C2).

    Returns (records, report). Each record is normalised to:
        {id, lang, text, issues: {issue: intent}, facts: {fact: state},
         enums: {claimant_sex, claimant_role, modality_time},
         spans: [{start, end, text, key, kind, clause_idx}],
         clauses: [{text, start, end}]}

    Missing issues default to "uncertain", missing facts to "unknown",
    missing enums to the "unknown" member (U / other / present).
    Unknown keys are counted in the report and (unless strict) ignored.
    Span clause_idx is DERIVED from char offsets (schema spans carry no
    clause_idx); key/kind are kept verbatim from the corpus.
    """
    path = Path(path)
    records: list[dict[str, Any]] = []
    report: dict[str, Any] = {
        "path": str(path), "n_lines": 0, "n_ok": 0, "n_skipped": 0,
        "unknown_issue_keys": {}, "unknown_fact_keys": {},
        "unknown_enum_values": {}, "langs": {}, "n_spans": 0,
        "issues_seen": {}, "facts_seen": {},
    }
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            report["n_lines"] += 1
            try:
                raw = json.loads(line)
            except json.JSONDecodeError:
                report["n_skipped"] += 1
                if strict:
                    raise
                continue
            text = (raw.get("text") or "").strip()
            if not text:
                report["n_skipped"] += 1
                continue
            rec_id = str(raw.get("id") or f"line-{report['n_lines']}")
            lang = str(raw.get("lang") or "en").lower()
            report["langs"][lang] = report["langs"].get(lang, 0) + 1

            issues: dict[str, str] = {}
            for key, val in (raw.get("issues") or {}).items():
                canon = _ISSUE_ALIASES.get(key, key)
                if canon not in ISSUE_INDEX:
                    report["unknown_issue_keys"][key] = (
                        report["unknown_issue_keys"].get(key, 0) + 1
                    )
                    continue
                intent = _normalise_label(val, ISSUE_INTENTS, "uncertain")
                issues[canon] = intent
                report["issues_seen"][canon] = report["issues_seen"].get(canon, 0) + 1
            for name in ISSUES:
                issues.setdefault(name, "uncertain")

            facts: dict[str, str] = {}
            for key, val in (raw.get("facts") or {}).items():
                canon = _FACT_ALIASES.get(key, key)
                if canon not in FACT_INDEX:
                    report["unknown_fact_keys"][key] = (
                        report["unknown_fact_keys"].get(key, 0) + 1
                    )
                    continue
                state = _normalise_label(val, FACT_STATES, "unknown")
                facts[canon] = state
                report["facts_seen"][canon] = report["facts_seen"].get(canon, 0) + 1
            for name in FACTS:
                facts.setdefault(name, "unknown")

            enums: dict[str, str] = {}
            for head, values in ENUMS.items():
                raw_val = (raw.get("enums") or {}).get(head)
                if isinstance(raw_val, str) and raw_val in values:
                    enums[head] = raw_val
                else:
                    if raw_val is not None:
                        report["unknown_enum_values"][f"{head}={raw_val!r}"] = (
                            report["unknown_enum_values"].get(f"{head}={raw_val!r}", 0) + 1
                        )
                    # "general" (laya_v7_schema ModalityTime) maps to present.
                    enums[head] = (
                        "present" if head == "modality_time"
                        else ("U" if head == "claimant_sex" else "other")
                    )

            clauses = split_clauses(text)
            spans: list[dict[str, Any]] = []
            for sp in raw.get("spans") or []:
                if not isinstance(sp, dict):
                    continue
                try:
                    start, end = int(sp["start"]), int(sp["end"])
                except (KeyError, TypeError, ValueError):
                    continue
                # Schema shape: {start, end, text, key, kind} where key is a
                # fact-or-issue name and kind is "fact" | "issue". Legacy
                # Lane 03 samples used {clause_idx, label} instead.
                ci = sp.get("clause_idx")
                if not isinstance(ci, int):
                    ci = _clause_index_for_offset(clauses, start, end)
                spans.append({
                    "start": start, "end": end,
                    "text": str(sp.get("text") or text[start:end]),
                    "key": sp.get("key"),
                    "kind": sp.get("kind"),
                    "clause_idx": ci,
                    "label": sp.get("label"),
                })
            report["n_spans"] += len(spans)

            records.append({
                "id": rec_id, "lang": lang, "text": text,
                "issues": issues, "facts": facts, "enums": enums,
                "spans": spans,
                "clauses": clauses,
            })
            report["n_ok"] += 1
    return records, report


def encode_labels(record: dict[str, Any]) -> dict[str, Any]:
    """Map a normalised record to integer label tensors (as plain lists).

    Returns {issue: [11], fact: [28], enums: {head: int},
             gate: [n_clauses, 3], span_mask: per-clause 0/1}.
    Gate labels (Lane 04: now REAL supervision, not all-zero): a clause is
    labelled denied=1 if a span in it names a fact the corpus marks
    "denied" (or an issue marked "denied"); hypothetical=1 if modality_time
    is hypothetical/quoted; third_party=1 only if a span is explicitly
    labelled "third_party" (the corpus schema has no third-party span
    label, so this stays 0 unless Lane 02 adds one — the gate head still
    learns its signal from clause text at training time). Without any span
    in a clause the gate labels are 0 for that clause.
    """
    issue = [ISSUE_INTENT_INDEX[record["issues"][n]] for n in ISSUES]
    fact = [FACT_STATE_INDEX[record["facts"][n]] for n in FACTS]
    enums = {
        head: ENUM_INDEX[head][record["enums"][head]] for head in ENUMS
    }
    n_clauses = max(1, len(record.get("clauses") or [None]))
    gate = [[0, 0, 0] for _ in range(n_clauses)]
    if record["enums"].get("modality_time") in ("hypothetical", "quoted"):
        for row in gate:
            row[1] = 1
    span_mask = [0] * n_clauses
    for sp in record.get("spans") or []:
        ci = sp.get("clause_idx")
        if isinstance(ci, int) and 0 <= ci < n_clauses:
            span_mask[ci] = 1
            key = sp.get("key")
            # Schema spans carry key (fact/issue name) + kind, not a label:
            # a span naming a denied fact/issue marks its clause denied.
            if key in FACTS and record["facts"].get(key) == "denied":
                gate[ci][0] = 1
            elif key in ISSUES and record["issues"].get(key) == "denied":
                gate[ci][0] = 1
            if (sp.get("label") or "") == "third_party":
                gate[ci][2] = 1
            if (sp.get("label") or "") == "denied":
                gate[ci][0] = 1
    return {"issue": issue, "fact": fact, "enums": enums,
            "gate": gate, "span_mask": span_mask}


# ---------------------------------------------------------------------------
# Model-side scoring hook (Lane 04 — for Lane 07's tests/recall_eval.py)
# ---------------------------------------------------------------------------

def _f1_from_counts(tp: int, fp: int, fn: int) -> float:
    if tp == 0:
        return 0.0
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    return 2 * prec * rec / (prec + rec) if prec + rec else 0.0


def _head_scores(gold: list[int], pred: list[int], n_classes: int) -> dict[str, Any]:
    """Macro/micro-F1 + accuracy for one single-label head (pure python)."""
    per_class = []
    tp_tot = fp_tot = fn_tot = 0
    for c in range(n_classes):
        tp = sum(1 for g, p in zip(gold, pred) if g == c and p == c)
        fp = sum(1 for g, p in zip(gold, pred) if g != c and p == c)
        fn = sum(1 for g, p in zip(gold, pred) if g == c and p != c)
        per_class.append(round(_f1_from_counts(tp, fp, fn), 4))
        tp_tot += tp
        fp_tot += fp
        fn_tot += fn
    micro = _f1_from_counts(tp_tot, fp_tot, fn_tot)
    return {"macro_f1": round(sum(per_class) / len(per_class), 4) if per_class else 0.0,
            "micro_f1": round(micro, 4),
            "accuracy": round(tp_tot / len(gold), 4) if gold else 0.0,
            "per_class_f1": per_class}


def score_label_predictions(gold_records: list[dict[str, Any]],
                            pred_records: list[dict[str, Any]]) -> dict[str, Any]:
    """Score predict_text()-style predictions against normalised gold records.

    Pure python (no torch) — this is the MODEL-SIDE per-head scoring
    function. NOTE ON NAMES (Lane 04 + Lane 07 coordination, 2026-11-27):
    tests/recall_eval.py has its own ``score_predictions(records,
    predicted_sections)`` which scores SECTION-SET exact — a different
    function with the same name. This one is deliberately named
    ``score_label_predictions`` to avoid the collision: it scores per-head
    label F1 (issue/fact/enum), NOT sections. The two scorers compose:
    predict_text() -> recall_eval.predict_sections_from_stage1() ->
    recall_eval.score_predictions() gives the section-exact R1 number;
    this function gives the per-head diagnostics behind it. Lane 04
    confirms Lane 07's proposed shared signature
    ``predict_sections_from_stage1(issues, facts, enums, *,
    custody_vocab="v3_bundled") -> set[str]`` as written in
    tests/recall_eval.py; it accepts predict_text()-style dicts AND plain
    intent/state/value strings.

    Returns {"n", "issue", "fact", "claimant_sex", "claimant_role",
             "modality_time", "issue_requested_recall",
             "mean_macro_f1_issue_fact", "in_scope": {...}}.
    """
    gold_issue: list[int] = []
    pred_issue: list[int] = []
    gold_fact: list[int] = []
    pred_fact: list[int] = []
    gold_enum: dict[str, list[int]] = {h: [] for h in ENUMS}
    pred_enum: dict[str, list[int]] = {h: [] for h in ENUMS}
    for gold, pred in zip(gold_records, pred_records):
        for name in ISSUES:
            gold_issue.append(ISSUE_INTENT_INDEX[gold["issues"][name]])
            pred_issue.append(ISSUE_INTENT_INDEX[
                pred["issues"][name]["intent"]])
        for name in FACTS:
            gold_fact.append(FACT_STATE_INDEX[gold["facts"][name]])
            pred_fact.append(FACT_STATE_INDEX[
                pred["facts"][name]["state"]])
        for head, vals in ENUMS.items():
            gold_enum[head].append(ENUM_INDEX[head][gold["enums"][head]])
            pred_enum[head].append(ENUM_INDEX[head][
                pred["enums"][head]["value"]])
    req = ISSUE_INTENT_INDEX["requested"]
    tp = sum(1 for g, p in zip(gold_issue, pred_issue) if g == req and p == req)
    fn = sum(1 for g, p in zip(gold_issue, pred_issue) if g == req and p != req)
    issue_m = _head_scores(gold_issue, pred_issue, len(ISSUE_INTENTS))
    fact_m = _head_scores(gold_fact, pred_fact, len(FACT_STATES))
    in_gold = [gold["facts"]["in_scope"] for gold in gold_records]
    in_pred = [pred["facts"]["in_scope"]["state"] for pred in pred_records]
    in_acc = (sum(1 for g, p in zip(in_gold, in_pred) if g == p)
              / len(in_gold)) if in_gold else 0.0
    denied_tp = sum(1 for g, p in zip(in_gold, in_pred)
                    if g == "denied" and p == "denied")
    denied_n = sum(1 for g in in_gold if g == "denied")
    metrics: dict[str, Any] = {
        "n": len(gold_records),
        "issue": issue_m,
        "fact": fact_m,
        "issue_requested_recall": round(tp / (tp + fn), 4) if tp + fn else 1.0,
        "mean_macro_f1_issue_fact": round(
            (issue_m["macro_f1"] + fact_m["macro_f1"]) / 2, 4),
        "in_scope": {
            "accuracy": round(in_acc, 4),
            "denied_recall": round(denied_tp / denied_n, 4) if denied_n else 1.0,
            "n_denied_gold": denied_n,
        },
    }
    for head in ENUMS:
        metrics[head] = _head_scores(gold_enum[head], pred_enum[head],
                                     len(ENUMS[head]))
    return metrics


def evaluate_checkpoint(checkpoint_path: str | Path, val_path: str | Path, *,
                        device: str = "cpu", limit: int | None = None,
                        config: ClassifierConfig | None = None,
                        return_predictions: bool = False):
    """Score a saved checkpoint on a held-out validation JSONL (torch needed).

    CPU-runnable (slow on CPU — the intended run is the RTX 5050 GPU box;
    see docs/rtx-recall-training-commands.md §4). Loads the checkpoint with
    load_checkpoint(), runs predict_text() per validation record, and scores
    with score_label_predictions(). With return_predictions=True it also
    returns (metrics, gold_records, pred_records) so a caller (e.g. the
    --eval-checkpoint mode of scripts/train_v71_classifier.py) can feed the
    predictions through Lane 07's predict_sections_from_stage1() +
    recall_eval.score_predictions() for the section-exact R1 number — the
    classifier module itself never imports the harness (the harness imports
    this module, so the dependency runs one way only). Returns the
    score_label_predictions() dict plus {"checkpoint": str, "val_file": str}.
    """
    model, cfg = load_checkpoint(checkpoint_path, device=device)
    cfg = config or cfg
    from transformers import AutoTokenizer  # noqa: PLC0415 - torch-only path
    tokenizer = AutoTokenizer.from_pretrained(cfg.backbone)
    gold, _ = load_corpus_jsonl(val_path)
    if limit is not None:
        gold = gold[:limit]
    preds = [predict_text(model, tokenizer, rec["text"], cfg) for rec in gold]
    metrics = score_label_predictions(gold, preds)
    metrics["checkpoint"] = str(checkpoint_path)
    metrics["val_file"] = str(val_path)
    if return_predictions:
        return metrics, gold, preds
    return metrics


# ---------------------------------------------------------------------------
# Model (torch required — everything below raises without it)
# ---------------------------------------------------------------------------

def build_model(config: ClassifierConfig | None = None):
    """Build the multi-head classifier. Raises RuntimeError without torch."""
    require_torch()
    import torch
    from torch import nn
    from transformers import AutoConfig, AutoModel

    cfg = config or ClassifierConfig()
    if cfg.backbone not in BACKBONES:
        raise ValueError(
            f"Unknown backbone {cfg.backbone!r}. Allowed: {sorted(BACKBONES)}"
        )
    if BACKBONES[cfg.backbone] == "VERIFY-BEFORE-TRAINING":
        raise ValueError(
            f"Backbone {cfg.backbone!r} has no verified permissive license yet. "
            "Verify its license (Lane 06 audit) before training, or use the "
            f"default {DEFAULT_BACKBONE!r}."
        )

    class LayaMultiHeadClassifier(nn.Module):
        """One shared encoder, five head groups, clause-vs-full fusion."""

        def __init__(self, cfg: ClassifierConfig):
            super().__init__()
            self.cfg = cfg
            hf_cfg = AutoConfig.from_pretrained(cfg.backbone)
            self.encoder = AutoModel.from_pretrained(cfg.backbone, config=hf_cfg)
            hidden = hf_cfg.hidden_size
            self.dropout = nn.Dropout(cfg.dropout)
            if cfg.freeze_backbone:
                for p in self.encoder.parameters():
                    p.requires_grad = False
            # Heads (all on the pooled [CLS] representation unless noted).
            self.issue_head = nn.Linear(hidden, len(ISSUES) * len(ISSUE_INTENTS))
            self.fact_head = nn.Linear(hidden, len(FACTS) * len(FACT_STATES))
            self.enum_heads = nn.ModuleDict({
                head: nn.Linear(hidden, len(vals)) for head, vals in ENUMS.items()
            })
            # Per-clause gate: [denied, hypothetical, third_party] logits.
            # A score >= tau_neg vetoes ONLY that clause in fusion.
            self.clause_gate_head = nn.Linear(hidden, 3)
            # Per-clause span-presence head: 1 logit per clause, trained
            # against the corpus span_mask (does this clause carry evidence?).
            self.span_head = nn.Linear(hidden, 1)
            # Token-level span attention: scores every token so evidence-span
            # mass can be read off and aligned with clause max-pooling.
            self.span_attn = nn.Linear(hidden, 1)

        def _encode(self, input_ids, attention_mask):
            out = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
            return out.last_hidden_state  # [B, T, H]

        def _pooled(self, hidden, attention_mask):
            # [CLS] pooling (position 0) — encoder is BERT-style.
            return self.dropout(hidden[:, 0, :])

        def span_attention(self, hidden, attention_mask):
            """Return (pooled_vector, token_attention_weights).

            Attention is a softmax over non-pad tokens only, so the weights
            sum to 1 per sequence and can be read as span evidence mass.
            """
            scores = self.span_attn(hidden).squeeze(-1)  # [B, T]
            scores = scores.masked_fill(attention_mask == 0, float("-inf"))
            weights = torch.softmax(scores, dim=-1)
            pooled = torch.sum(hidden * weights.unsqueeze(-1), dim=1)
            return self.dropout(pooled), weights

        def forward(self, full_input_ids, full_attention_mask,
                    clause_input_ids=None, clause_attention_mask=None,
                    clause_counts=None):
            """full_*: [B, T]; clause_*: [B, C, T] (C = max_clauses, padded).

            Returns dict of logits; fusion is applied by the caller /
            ``predict`` via :func:`fuse_issue_probs` so the raw clause
            logits stay available for inspection and calibration.
            """
            full_hidden = self._encode(full_input_ids, full_attention_mask)
            full_pooled = self._pooled(full_hidden, full_attention_mask)
            _, span_weights = self.span_attention(full_hidden, full_attention_mask)

            out: dict[str, Any] = {
                "issue_logits": self.issue_head(full_pooled).view(
                    -1, len(ISSUES), len(ISSUE_INTENTS)),
                "fact_logits": self.fact_head(full_pooled).view(
                    -1, len(FACTS), len(FACT_STATES)),
                "enum_logits": {
                    head: layer(full_pooled)
                    for head, layer in self.enum_heads.items()
                },
                "span_weights": span_weights,
            }
            if clause_input_ids is not None:
                b, c, t = clause_input_ids.shape
                flat_ids = clause_input_ids.reshape(b * c, t)
                flat_mask = clause_attention_mask.reshape(b * c, t)
                clause_hidden = self._encode(flat_ids, flat_mask)
                clause_pooled = self._pooled(clause_hidden, flat_mask).view(b, c, -1)
                clause_pooled = self.dropout(clause_pooled)
                out["clause_issue_logits"] = self.issue_head(clause_pooled).view(
                    b, c, len(ISSUES), len(ISSUE_INTENTS))
                out["clause_fact_logits"] = self.fact_head(clause_pooled).view(
                    b, c, len(FACTS), len(FACT_STATES))
                out["clause_gate_logits"] = self.clause_gate_head(clause_pooled)
                out["clause_span_logits"] = self.span_head(clause_pooled).squeeze(-1)
                out["clause_counts"] = clause_counts
            return out

    return LayaMultiHeadClassifier(cfg)


def fuse_issue_probs(full_probs, clause_probs, clause_gate_logits,
                     clause_counts, *, tau_neg: float = 0.5,
                     temperature: float = 1.0):
    """Calibrated clause-vs-full fusion for the issue head (torch required).

    full_probs:   [B, 11, 4] softmax probs from the full question.
    clause_probs: [B, C, 11, 4] softmax probs per clause.
    clause_gate_logits: [B, C, 3] (denied, hypothetical, third_party).
    clause_counts: [B] real clause counts (padded slots ignored).
    Returns fused [B, 11, 4] probs (renormalised). Rule (plan §1.2):
      requested_fused = max(full_requested, max over NON-VETOED clauses
                            of clause_requested); a clause is vetoed iff any
      of its three gate sigmoids >= tau_neg. Other intents keep the full
      encoding's probabilities; the row is then renormalised.
    """
    require_torch()
    import torch

    req = ISSUE_INTENT_INDEX["requested"]
    gate_sig = torch.sigmoid(clause_gate_logits)
    vetoed = gate_sig.amax(dim=-1) >= tau_neg  # [B, C] True = veto this clause
    b, c, _, _ = clause_probs.shape
    arange_c = torch.arange(c, device=clause_probs.device).unsqueeze(0)
    valid = arange_c < clause_counts.unsqueeze(1)  # [B, C] real clauses only
    keep = valid & (~vetoed)
    clause_req = clause_probs[:, :, :, req]  # [B, C, 11]
    masked = clause_req.masked_fill(~keep.unsqueeze(-1), float("-inf"))
    cmax_req, _ = masked.amax(dim=1)  # [B, 11]; -inf where no clause kept
    cmax_req = torch.where(
        torch.isfinite(cmax_req), cmax_req,
        torch.zeros_like(cmax_req),
    )
    fused = full_probs.clone()
    fused[:, :, req] = torch.maximum(full_probs[:, :, req], cmax_req)
    fused = fused / fused.sum(dim=-1, keepdim=True).clamp_min(1e-9)
    return fused


def predict_text(model, tokenizer, text: str,
                 config: ClassifierConfig | None = None) -> dict[str, Any]:
    """Run one question through the model (torch required).

    Returns plain-JSON-able {issues, facts, enums, spans, clauses} where
    issues/facts carry {label, confidence, clause_idx?} and spans carry the
    top attention-mass token ranges mapped back to char offsets via the
    tokenizer's offset mapping. Clause fusion (fuse_issue_probs) is applied
    to the issue head; fact/enum heads use the full encoding.
    """
    require_torch()
    import torch

    cfg = config or ClassifierConfig()
    model.eval()
    clauses = split_clauses(text, cfg.max_clauses)
    if not clauses:
        return {"issues": {}, "facts": {}, "enums": {}, "spans": [],
                "clauses": []}
    full = tokenizer(text, return_tensors="pt", truncation=True,
                     max_length=cfg.max_seq_len, return_offsets_mapping=True)
    offsets = full.pop("offset_mapping")[0].tolist()
    clause_batch = tokenizer(
        [c["text"] for c in clauses], return_tensors="pt", truncation=True,
        max_length=cfg.max_seq_len, padding=True,
    )
    b, c = 1, len(clauses)
    pad_to = cfg.max_clauses
    clause_ids = torch.zeros(1, pad_to, clause_batch["input_ids"].shape[1],
                             dtype=torch.long)
    clause_mask = torch.zeros_like(clause_ids)
    clause_ids[0, :c] = clause_batch["input_ids"]
    clause_mask[0, :c] = clause_batch["attention_mask"]
    with torch.no_grad():
        out = model(full["input_ids"], full["attention_mask"],
                    clause_ids, clause_mask,
                    clause_counts=torch.tensor([c]))
        issue_p = torch.softmax(
            out["issue_logits"] / max(cfg.temperature_issue, 1e-6), dim=-1)
        clause_p = torch.softmax(
            out["clause_issue_logits"] / max(cfg.temperature_issue, 1e-6), dim=-1)
        fused = fuse_issue_probs(
            issue_p, clause_p, out["clause_gate_logits"],
            torch.tensor([c]), tau_neg=cfg.tau_neg,
            temperature=cfg.temperature_issue)
        fact_p = torch.softmax(
            out["fact_logits"] / max(cfg.temperature_fact, 1e-6), dim=-1)

    issues: dict[str, Any] = {}
    for i, name in enumerate(ISSUES):
        probs = fused[0, i]
        k = int(torch.argmax(probs))
        issues[name] = {
            "intent": ISSUE_INTENTS[k],
            "confidence": round(float(probs[k]), 4),
            "probs": {ISSUE_INTENTS[j]: round(float(probs[j]), 4)
                      for j in range(len(ISSUE_INTENTS))},
        }
    facts: dict[str, Any] = {}
    for i, name in enumerate(FACTS):
        probs = fact_p[0, i]
        k = int(torch.argmax(probs))
        facts[name] = {
            "state": FACT_STATES[k],
            "confidence": round(float(probs[k]), 4),
        }
    enums: dict[str, Any] = {}
    for head, logits in out["enum_logits"].items():
        probs = torch.softmax(logits[0], dim=-1)
        k = int(torch.argmax(probs))
        enums[head] = {"value": ENUMS[head][k],
                       "confidence": round(float(probs[k]), 4)}
    # Top attention-mass spans: take the 3 highest-weight non-special tokens
    # and expand each to its char range via offset mapping.
    weights = out["span_weights"][0].tolist()
    order = sorted(range(len(weights)), key=lambda t: weights[t], reverse=True)
    spans: list[dict[str, Any]] = []
    for tok_idx in order[:3]:
        if tok_idx >= len(offsets):
            continue
        s, e = offsets[tok_idx]
        if e <= s:
            continue
        spans.append({"start": s, "end": e, "text": text[s:e],
                      "attention": round(float(weights[tok_idx]), 4)})
    return {"issues": issues, "facts": facts, "enums": enums,
            "spans": spans, "clauses": clauses}


def save_checkpoint(model, config: ClassifierConfig, path: str | Path) -> Path:
    """Save {state_dict, config} — torch required."""
    require_torch()
    import torch

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": model.state_dict(),
                "config": config.to_dict()}, path)
    return path


def load_checkpoint(path: str | Path, *, device: str = "cpu"):
    """Load a checkpoint and rebuild the model — torch required."""
    require_torch()
    import torch

    ckpt = torch.load(path, map_location=device, weights_only=False)
    cfg = ClassifierConfig.from_dict(ckpt["config"])
    model = build_model(cfg)
    model.load_state_dict(ckpt["state_dict"])
    model.to(device)
    model.eval()
    return model, cfg


# ---------------------------------------------------------------------------
# CLI smoke entry (torch-free paths only)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--check-corpus":
        recs, rep = load_corpus_jsonl(sys.argv[2])
        print(json.dumps(rep, indent=2, ensure_ascii=False)[:4000])
        print(f"OK: {rep['n_ok']} records loaded, "
              f"{rep['n_skipped']} skipped.")
    elif len(sys.argv) >= 3 and sys.argv[1] == "--split":
        print(json.dumps(split_clauses(sys.argv[2]), indent=2,
                         ensure_ascii=False))
    else:
        print("usage: python -m src.laya_v7_classifier --check-corpus <file.jsonl>")
        print("       python -m src.laya_v7_classifier --split '<question>'")
        print("Model build/train needs torch — see scripts/train_v71_classifier.py")
