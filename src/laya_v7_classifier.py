"""LAYA v7.1 multi-head Stage 0/1 classifier (V71-P1-3, plan docs/10x_plane.md §1.2).

Unified multi-head teacher over a permissive-licensed encoder backbone.
CODE ONLY — no training runs on this VM (no GPU / no torch here).

Backbones (FALLBACK-2 + GPT-RERUN, 2026-11-27; Lane B amendment — the
Lane 04 ModernBERT-large / DeBERTa-v3-large defaults are SUPERSEDED, not
silently dropped: see docs/impl_laneB_classifier_changes.md §5):
    - "jhu-clsp/mmBERT-base"        (MIT)         [DEFAULT, primary candidate]
    - "google/muril-base-cased"     (Apache-2.0)  [serious Kanglish challenger]
    - "FacebookAI/xlm-roberta-base" (MIT)
No backbone is the predetermined winner — the A4 smoke benchmark decides.
Licences verified 2026-11-27 from the published model cards (mmBERT MIT,
MuRIL Apache-2.0 per its card metadata, XLM-R MIT) and recorded in
docs/impl_laneB_classifier_changes.md §5. build_model() refuses any
backbone not in BACKBONES.

Encoding (FALLBACK-2 item 1, GPT-RERUN claim 1 adopted with correction):
    1-PASS (default, ``pooling="one_pass"``): encode ``[CLS] full_question
    [SEP]`` ONCE (max_seq_len 320, bf16); clause vectors come from
    token-span attention pooling over the contextualised token embeddings
    inside each clause's character offsets. Every clause keeps full-question
    context (coreference / Kannada pro-drop survive); clause-splitter errors
    are non-fatal.
    9-PASS (audit only, ``pooling="nine_pass"``): the old Lane 03/04 path —
    the full question plus each clause encoded separately. Kept so the old
    behaviour stays reproducible for audit, NOT as a training default.
    VRAM CLAIM — UNVERIFIED (GPT-RERUN): 1-pass cuts MAXIMUM PADDED TOKEN
    positions ~8.1x (9x288/320 at max padding), NOT a proven ~8x VRAM saving.
    Parameter weights and optimizer states are not replicated 9x, and dynamic
    padding changes the real token ratio. Micro-batch 8 is a TARGET, not a
    guaranteed fit; the training script fails loudly on OOM and suggests the
    micro-batch 4 / grad-accum 4 fallback instead of silently shrinking.

Heads:
    issue_head  [11, 4]  softmax over (requested, incidental, denied, uncertain)
    fact_head   [28, 4]  softmax over (supported, denied, unknown, conflicting)
    enum_heads  claimant_sex   [F, M, U]
                claimant_role  [spouse, parent, child, other]
                modality_time  [present, past, future, hypothetical, quoted]
    span_attn_pool: token-level evidence spans aligned with clause max-pooling.

Loss (FALLBACK-2 item 2, GPT-RERUN claim 2 — ASL REPLACED, see §Loss below):
    weighted cross-entropy over the 4 mutually exclusive states per head is
    the BASELINE (``loss="weighted_ce"``, default); class-balanced focal CE
    is the CHALLENGER (``loss="focal_ce"``). Unknown stays a semantic state;
    the 3-binary-logits variant is REJECTED (it conflates "not established"
    with "uncertain").

Clause-vs-full fusion (plan §1.2):
    requested uses calibrated max(full_p, cmax_p), gated by sentence-local
    denied gate logits only (Lane B2, 2026-11-27: the hypothetical and
    third_party gate columns were dropped from the model head — no
    clause-local source for either in the corpus; see encode_labels,
    which keeps all-zero placeholder columns in the label tensor only
    so the frozen A3 checker can index them). A gate score >= tau_neg
    vetoes ONLY that clause (it is excluded from the clause max-pool); sibling
    clauses are unaffected. Other intents come from the full-question encoding.
    GPT-RERUN amendment: hypothetical / third-party language is NOT
    automatically out-of-scope — soft relevance weighting first, hard vetoes
    only where independently validated; never copy question-level labels onto
    clauses as clause-level supervision (spans or MIL only).

Thresholds (FALLBACK-2 item 3, GPT-RERUN claim 3): calibrated by
scripts/calibrate_thresholds.py against Stage 2 section-set exact match on
OOF predictions from TRAIN-7500 ONLY (never Val-500), temperature scaling
first, Empirical Bayes shrinkage comparing kappa in {50, 150, 300} with
separate priors per head family, up to 3 coordinate passes, precision floor
0.91 (Pareto measured at 0.88/0.90/0.91/0.93/0.95). The calibration writes
thresholds.json next to the checkpoint; decode applies it via
decode_with_thresholds(). predict_text() itself still returns argmax
labels + full probs, so the thresholds stay a decode-time policy, not a
model property.

Fact binding (GPT-RERUN P0, minimal version — see bind_evidence()):
    evidence spans carry subject / event / polarity / time / span, derived
    from the corpus spans (text/key/kind/offsets) + the record's enums and
    fact states. Full subject/event resolution (which span belongs to which
    proceeding/claimant when several co-occur) needs a schema change and is
    OPEN — see docs/impl_laneB_classifier_changes.md §6. Do not hack the
    schema to fake it.

Checkpoint dir layout (contract C2, docs/impl_swarm_state.md):
    models/<name>/best/model.pt        (state_dict + config, via save_checkpoint)
    models/<name>/best/config.json     (ClassifierConfig, written with the checkpoint)
    models/<name>/best/thresholds.json (written by scripts/calibrate_thresholds.py)
    models/<name>/best/label_maps.json (label vocabularies, written by training)
    models/<name>/last/...             (final-epoch checkpoint, same layout minus
                                        thresholds.json — thresholds are calibrated
                                        on the BEST checkpoint only)
    Default checkpoint the integrated runtime looks for:
    models/v71-classifier/best/model.pt (overridable with --checkpoint).

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
RuntimeError telling the operator to run on Google Colab (T4) — Colab is the
user's compute rule; the RTX 5050 is the equivalent local path, not a
comparison. See docs/rtx-recall-training-commands.md.
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

# Backbones the code accepts, with the licence verified 2026-11-27 (Lane B).
# FALLBACK-2 + GPT-RERUN 3-backbone benchmark: NO predetermined winner —
# the A4 smoke benchmark (scripts/smoke_backbones.py, Lane A) decides.
# Default is mmBERT-base as the PRIMARY CANDIDATE; MuRIL is a serious
# Kanglish challenger (natively pretrained on Indian scripts + Romanised
# transliterations), XLM-R the third equal. The Lane 04 defaults
# (answerdotai/ModernBERT-large, microsoft/deberta-v3-large) are SUPERSEDED
# by this amendment — documented in docs/impl_laneB_classifier_changes.md §5,
# not silently dropped. PIXMELT/laya stays refused (no verified licence).
# Licence check, 2026-11-27, Lane B: mmBERT MIT (HF model card
# jhu-clsp/mmBERT-base, "license: mit"); MuRIL Apache-2.0 (HF card metadata
# google/muril-base-cased, "license: apache-2.0"); XLM-R MIT (HF card
# FacebookAI/xlm-roberta-base; corroborated by GPT-RERUN §7, which verified
# all three from the published model cards). Re-verify on the card before
# any training run if the checkpoint revision changes.
BACKBONES = {
    "jhu-clsp/mmBERT-base": "MIT",
    "google/muril-base-cased": "Apache-2.0",
    "FacebookAI/xlm-roberta-base": "MIT",
}

DEFAULT_BACKBONE = "jhu-clsp/mmBERT-base"

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
    max_seq_len: int = 320
    max_clauses: int = 8
    dropout: float = 0.1
    freeze_backbone: bool = False
    use_lora: bool = False
    # Encoding (FALLBACK-2 item 1): "one_pass" (default) encodes the full
    # question once and pools clause vectors from its token embeddings;
    # "nine_pass" is the old Lane 03/04 audit path (full + each clause
    # encoded separately). See module docstring — the "~9x VRAM saving"
    # claim is UNVERIFIED (8.1x padded tokens, not proven VRAM).
    pooling: str = "one_pass"
    pool_mode: str = "mean_ln"
    # Loss (FALLBACK-2 item 2, GPT-RERUN claim 2): "weighted_ce" is the
    # BASELINE (default), "focal_ce" the CHALLENGER. ASL is NOT an option:
    # it is a binary multi-label loss and does not fit 4 mutually exclusive
    # states (see docs/impl_laneB_classifier_changes.md §2). Unknown stays a
    # semantic state; the 3-binary-logits variant is rejected.
    loss: str = "weighted_ce"
    focal_gamma: float = 2.0       # focal CE challenger only (gamma grid {0,1,2})
    loss_beta: float = 0.999       # effective-number weighting (beta grid {0.99,0.999})
    loss_unknown_weight: float = 0.25  # relative weight of the unknown state (grid {0.25,0.5,1.0})
    loss_max_weight: float = 8.0   # cap on effective-number class weights (grid {4x,8x})
    # Optimiser (FALLBACK-2): separate encoder / head learning rates.
    lr_encoder: float = 2e-5
    lr_head: float = 1e-4
    # Fusion / calibration (fit on held-out dev by Lane 10, defaults = neutral).
    tau_neg: float = 0.5      # per-clause gate score >= tau_neg vetoes that clause
    temperature_issue: float = 1.0
    temperature_fact: float = 1.0
    # Loss weights for scripts/train_v71_classifier.py (must sum to ~1.0).
    # Lane B2 (2026-11-27, A3/C4): "clause" 0.10 added for the
    # span-anchored clause issue/fact CE; issue/fact each 0.35 -> 0.30 so
    # the weights still sum to 1.0. Old weights (issue/fact 0.35, no
    # clause term) are recorded here, not silently rewritten.
    loss_weights: dict[str, float] = field(
        default_factory=lambda: {
            "issue": 0.30,
            "fact": 0.30,
            "enum": 0.15,
            "gate": 0.10,
            "span": 0.05,
            "clause": 0.10,
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
            "Run scripts/train_v71_classifier.py in Google Colab (T4) — see "
            "docs/rtx-recall-training-commands.md (Colab-first commands) or the "
            "Colab notebook notebooks/laya_v71_train_backtest.ipynb. The RTX 5050 "
            "is the equivalent local path, not a comparison. "
            f"Original import error: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# FALLBACK-2 helpers (pure python — no torch needed)
# ---------------------------------------------------------------------------

def clause_token_spans(offsets: list[tuple[int, int]],
                       clauses: list[dict[str, Any]]) -> list[tuple[int, int]]:
    """Map each clause's char offsets to a [start_token, end_token) span.

    ``offsets`` is the tokenizer offset mapping for the single full-question
    encoding (one (char_start, char_end) pair per token, (0, 0) for special
    tokens). A token belongs to a clause iff its char range overlaps the
    clause's char range. A clause with no overlapping token (e.g. a
    whitespace-only fragment after truncation) falls back to the [CLS]
    token span (0, 1) so pooling never receives an empty range.
    """
    spans: list[tuple[int, int]] = []
    for c in clauses:
        idx = [t for t, (s, e) in enumerate(offsets)
               if e > s and s < c["end"] and e > c["start"]]
        if idx:
            spans.append((idx[0], idx[-1] + 1))
        else:
            spans.append((0, 1))
    return spans


def effective_number_weights(counts: list[int], *, beta: float = 0.999,
                             unknown_weight: float = 0.25,
                             max_weight: float = 8.0,
                             unknown_index: int = 2) -> list[float]:
    """Class-balanced weights by effective number of samples (Cui et al.).

    w_c = (1 - beta) / (1 - beta ** n_c), then the ``unknown`` state
    (index ``unknown_index`` — 2 for both heads: issue "uncertain" is index
    3, fact "unknown" is index 2; callers pass the right index) is scaled
    to ``unknown_weight`` relative to the mean active-state weight, and all
    weights are capped at ``max_weight`` and renormalised to mean 1.0 so
    head-loss magnitudes stay comparable. Pure python — the training script
    computes counts from the train split and passes the result to the loss.
    GPT-RERUN: beta in {0.99, 0.999}, unknown weight in {0.25, 0.5, 1.0},
    cap in {4x, 8x} are search grids, not established optima — the defaults
    here (0.999 / 0.25 / 8x) are the FALLBACK-2 starting point.
    """
    raw = [(1.0 - beta) / (1.0 - beta ** max(1, n)) for n in counts]
    active = [w for i, w in enumerate(raw) if i != unknown_index]
    mean_active = sum(active) / len(active) if active else 1.0
    weights = [min(max_weight, w) for w in raw]
    weights[unknown_index] = min(max_weight, unknown_weight * mean_active)
    mean_w = sum(weights) / len(weights) if weights else 1.0
    return [w / mean_w for w in weights]


def bind_evidence(spans: list[dict[str, Any]], facts: dict[str, str],
                  enums: dict[str, str],
                  issues: dict[str, str] | None = None) -> list[dict[str, Any]]:
    """MINIMAL fact binding (GPT-RERUN P0) from the spans the corpus has.

    Each span already carries text/key/kind/offsets; this attaches a
    ``binding`` with the five fields the re-run requires:
      subject  — the claimant role/sex from the record's enums (the only
                 subject signal the corpus carries; per-span subjects do
                 NOT exist in the schema — see OPEN below).
      event    — the span's ``key`` (fact/issue name).
      polarity — the corpus state of that key: supported -> "asserted",
                 denied -> "negated", unknown -> "unknown",
                 conflicting -> "conflicting"; issue spans use the issue
                 intent (requested/incidental -> "asserted", denied ->
                 "negated", uncertain -> "unknown").
      time     — the record's modality_time enum.
      span     — {start, end, text} (the evidence span itself).
    Returns NEW span dicts (input untouched). Spans with no key get
    event=None / polarity="unknown" — they are attention spans, not
    labelled evidence, and must not be presented as bound facts.
    OPEN (schema change needed, NOT hacked here): when two proceedings,
    demands or properties co-occur, the corpus cannot say WHICH span
    belongs to WHICH event/claimant — spans carry one key and no
    subject/event id. Full binding needs a span-level subject + event-id
    field in the schema; the design is filed in
    docs/impl_laneB_classifier_changes.md §6.
    """
    issues = issues or {}
    bound: list[dict[str, Any]] = []
    for sp in spans or []:
        key = sp.get("key")
        if key in FACTS:
            state = facts.get(key, "unknown")
            polarity = {"supported": "asserted", "denied": "negated",
                        "unknown": "unknown",
                        "conflicting": "conflicting"}.get(state, "unknown")
        elif key in ISSUES:
            intent = issues.get(key, "uncertain")
            polarity = {"requested": "asserted", "denied": "negated",
                        "incidental": "asserted",
                        "uncertain": "unknown"}.get(intent, "unknown")
        else:
            polarity = "unknown"
        bound.append({
            **sp,
            "binding": {
                "subject": enums.get("claimant_role", "other"),
                "subject_sex": enums.get("claimant_sex", "U"),
                "event": key,
                "polarity": polarity,
                "time": enums.get("modality_time", "present"),
                "span": {"start": sp.get("start"), "end": sp.get("end"),
                         "text": sp.get("text")},
            },
        })
    return bound


def decode_with_thresholds(issue_probs: dict[str, dict[str, float]],
                           fact_probs: dict[str, dict[str, float]],
                           thresholds: dict[str, Any]) -> dict[str, Any]:
    """Decode per-head probs to labels using a calibrated thresholds dict.

    ``thresholds`` is the thresholds.json written by
    scripts/calibrate_thresholds.py: {"tau_0_issue", "tau_0_fact",
    "tau_issue": {issue: tau}, "tau_fact": {fact: tau}, ...}. Rule: the
    argmax state wins, BUT if its probability is below the head's threshold
    the label falls back to the neutral state ("uncertain" for issues,
    "unknown" for facts) instead of emitting a low-confidence active label.
    This is the decode-time policy the integrated runtime applies; it is
    deliberately separate from predict_text(), which returns argmax labels
    + full probs and never hides the model's raw output.
    """
    tau_issue = thresholds.get("tau_issue") or {}
    tau_fact = thresholds.get("tau_fact") or {}
    tau0_i = float(thresholds.get("tau_0_issue", 0.5))
    tau0_f = float(thresholds.get("tau_0_fact", 0.5))
    issues: dict[str, str] = {}
    for name, probs in (issue_probs or {}).items():
        best = max(probs, key=lambda k: probs[k])
        tau = float(tau_issue.get(name, tau0_i))
        issues[name] = best if probs[best] >= tau else "uncertain"
    facts: dict[str, str] = {}
    for name, probs in (fact_probs or {}).items():
        best = max(probs, key=lambda k: probs[k])
        tau = float(tau_fact.get(name, tau0_f))
        facts[name] = best if probs[best] >= tau else "unknown"
    return {"issues": issues, "facts": facts}


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
         clauses: [{text, start, end}],
         meta: {cluster, blocks, split} as carried in the raw record
         ({} when absent — preserved, not re-derived, so callers that
         group by meta.blocks, e.g. scripts/smoke_backbones.py part (b),
         do not crash with KeyError 'meta')}

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
                "meta": raw.get("meta") if isinstance(raw.get("meta"), dict)
                else {},
            })
            report["n_ok"] += 1
    return records, report


def encode_labels(record: dict[str, Any]) -> dict[str, Any]:
    """Map a normalised record to integer label tensors (as plain lists).

    Returns {issue: [11], fact: [28], enums: {head: int},
             gate: [n_clauses, 3], span_mask: per-clause 0/1,
             clause_issue: [n_clauses, 11], clause_fact: [n_clauses, 28],
             clause_issue_mask / clause_fact_mask: per-(clause, head) 0/1}.
    Gate labels (Lane B2, 2026-11-27 — A3 fix): ONLY column 0 (denied)
    carries supervision — a clause is labelled denied=1 iff a span in it
    names a fact/issue the corpus marks "denied". That is the only
    clause-local gate signal the corpus actually carries.
    Columns 1 (hypothetical) and 2 (third_party) are ALWAYS 0 and are
    NEVER consumed by the model: the gate head is denied-only
    (``clause_gate_head`` outputs 1 logit), the train collate slices
    column 0 only, and fusion vetoes on denied only. They are retained
    in this label tensor SOLELY because the frozen A3 checker
    (``scripts/check_clause_supervision.py``, Lane A — the test, not the
    code under test) indexes row[1] and row[2] when counting corpus
    positives; dropping them from the tensor would crash the checker
    rather than change its verdict. They are placeholders, not heads:
    no hypothetical/third-party head exists, no loss trains them, and
    no veto can fire from them. (The checker therefore still prints its
    C2 VACUOUS lines for these columns — those lines describe the
    unconsumed placeholder columns, not any trained head.)
    REMOVED (do not re-add without a clause-local source):
      * the ``hypothetical`` broadcast (Lane 04): if question-level
        ``modality_time`` was hypothetical/quoted, EVERY clause got
        hypothetical=1 — including requested clauses in mixed-modality
        questions. No span in the corpus carries a modality label
        (all 5,829 train span labels are None; 176/253 hyp/quoted train
        records have no spans at all), so there is no clause-local source
        for a hypothetical column. Hypothetical/quoted stays supervised
        at question level only, by the modality_time enum head.
      * the ``third_party`` column as a trained head (Lane 04): 0
        positive rows in all 8,000 records — the corpus schema has no
        third-party span label. A head trained on all-zero targets can
        never fire, so the head (and its fusion veto) is dropped, not
        kept as a dead head; only the placeholder column above remains.
    Clause issue/fact supervision (Lane B2, C4 fix): for each span, the
    clause it falls in is anchored to the span's key — clause_issue[ci]
    for an issue key / clause_fact[ci] for a fact key takes the record's
    intent/state for that key, and the matching mask entry is 1. This is
    span-anchored supervision (the span is clause-local evidence that
    the clause expresses that issue/fact), NOT a broadcast: unanchored
    (clause, head) pairs stay masked out of the clause loss. A span
    naming a denied fact/issue also marks its clause gate denied=1.
    Without any span in a clause the gate label is 0 for that clause.
    """
    issue = [ISSUE_INTENT_INDEX[record["issues"][n]] for n in ISSUES]
    fact = [FACT_STATE_INDEX[record["facts"][n]] for n in FACTS]
    enums = {
        head: ENUM_INDEX[head][record["enums"][head]] for head in ENUMS
    }
    n_clauses = max(1, len(record.get("clauses") or [None]))
    gate = [[0, 0, 0] for _ in range(n_clauses)]
    span_mask = [0] * n_clauses
    # Span-anchored clause targets (C4): placeholder 0 is never used —
    # the loss only reads entries whose mask is 1.
    clause_issue = [[0] * len(ISSUES) for _ in range(n_clauses)]
    clause_fact = [[0] * len(FACTS) for _ in range(n_clauses)]
    clause_issue_mask = [[0] * len(ISSUES) for _ in range(n_clauses)]
    clause_fact_mask = [[0] * len(FACTS) for _ in range(n_clauses)]
    for sp in record.get("spans") or []:
        ci = sp.get("clause_idx")
        if isinstance(ci, int) and 0 <= ci < n_clauses:
            span_mask[ci] = 1
            key = sp.get("key")
            # Schema spans carry key (fact/issue name) + kind, not a label:
            # a span naming a denied fact/issue marks its clause denied,
            # and anchors that (clause, head) pair to the record's label
            # for that head — the clause-local supervision source for C4.
            if key in FACTS:
                clause_fact[ci][FACTS.index(key)] = fact[FACTS.index(key)]
                clause_fact_mask[ci][FACTS.index(key)] = 1
                if record["facts"].get(key) == "denied":
                    gate[ci][0] = 1
            if key in ISSUES:
                # Independent `if`, not `elif`: "violence" is both an issue
                # and a fact name, so one span can anchor both heads.
                clause_issue[ci][ISSUES.index(key)] = issue[ISSUES.index(key)]
                clause_issue_mask[ci][ISSUES.index(key)] = 1
                if record["issues"].get(key) == "denied":
                    gate[ci][0] = 1
            if (sp.get("label") or "") == "denied":
                gate[ci][0] = 1
    return {"issue": issue, "fact": fact, "enums": enums,
            "gate": gate, "span_mask": span_mask,
            "clause_issue": clause_issue, "clause_fact": clause_fact,
            "clause_issue_mask": clause_issue_mask,
            "clause_fact_mask": clause_fact_mask}


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

    CPU-runnable (slow on CPU — the intended run is Colab T4 / the RTX 5050
    GPU box; see docs/rtx-recall-training-commands.md §4). Loads the checkpoint with
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
    if cfg.pooling not in ("one_pass", "nine_pass"):
        raise ValueError(
            f"Unknown pooling {cfg.pooling!r}. Allowed: 'one_pass', 'nine_pass'."
        )
    if cfg.loss not in ("weighted_ce", "focal_ce"):
        raise ValueError(
            f"Unknown loss {cfg.loss!r}. Allowed: 'weighted_ce', 'focal_ce'. "
            "ASL is not an option (binary loss on 4 mutually exclusive states)."
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
            self.pool_norm = nn.LayerNorm(hidden)
            if cfg.freeze_backbone:
                for p in self.encoder.parameters():
                    p.requires_grad = False
            # Heads (all on the pooled [CLS] representation unless noted).
            self.issue_head = nn.Linear(hidden, len(ISSUES) * len(ISSUE_INTENTS))
            self.fact_head = nn.Linear(hidden, len(FACTS) * len(FACT_STATES))
            self.enum_heads = nn.ModuleDict({
                head: nn.Linear(hidden, len(vals)) for head, vals in ENUMS.items()
            })
            # Per-clause gate: [denied] logits only (Lane B2, 2026-11-27:
            # A3/C2 — the hypothetical broadcast and the vacuous
            # third_party column were removed from the model head; denied
            # is the only gate column with a clause-local source in the
            # corpus. The label tensor keeps all-zero placeholder columns
            # 1-2 solely for the frozen A3 checker — see encode_labels.)
            # A score >= tau_neg vetoes ONLY that clause in fusion.
            self.clause_gate_head = nn.Linear(hidden, 1)
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
            if getattr(self.cfg, "pool_mode", "cls") == "mean_ln":
                mask = attention_mask.unsqueeze(-1).to(hidden.dtype)
                mean_vec = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp_min(1.0)
                return self.dropout(self.pool_norm(mean_vec))
            # [CLS] pooling (position 0) — legacy fallback.
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

        def span_pool_clauses(self, hidden, attention_mask, clause_token_spans):
            """1-pass contextual clause vectors (FALLBACK-2 item 1).

            ``hidden``: [B, T, H] from the SINGLE full-question encoding.
            ``clause_token_spans``: [B, C, 2] (start, end) token indices per
            clause, from clause_token_spans() on the offset mapping. Each
            clause vector is an attention-weighted sum of the contextualised
            token embeddings inside its span, with the attention softmax
            restricted to that span (the same span_attn scorer as the
            full-question pooling, so evidence mass stays comparable).
            Padded clause slots have span (0, 0) and return a zero vector;
            callers must mask them out with clause_counts. Empty spans
            fall back to the [CLS] embedding so no clause is a zero vector
            by accident.
            """
            b, _, h = hidden.shape
            c = clause_token_spans.shape[1]
            scores = self.span_attn(hidden).squeeze(-1)  # [B, T]
            scores = scores.masked_fill(attention_mask == 0, float("-inf"))
            device = hidden.device
            arange_t = torch.arange(hidden.shape[1], device=device)
            starts = clause_token_spans[:, :, 0]  # [B, C]
            ends = clause_token_spans[:, :, 1]    # [B, C]
            in_span = (arange_t.unsqueeze(0).unsqueeze(0) >= starts.unsqueeze(-1)) \
                & (arange_t.unsqueeze(0).unsqueeze(0) < ends.unsqueeze(-1))
            masked = scores.unsqueeze(1).masked_fill(~in_span, float("-inf"))
            weights = torch.softmax(masked, dim=-1)  # [B, C, T]
            # Where a span was empty (all -inf), softmax is NaN: replace
            # those rows with a one-hot on [CLS] (token 0).
            bad = ~torch.isfinite(weights).any(dim=-1)  # [B, C]
            if bool(bad.any()):
                cls_onehot = torch.zeros_like(weights)
                cls_onehot[:, :, 0] = 1.0
                weights = torch.where(bad.unsqueeze(-1), cls_onehot, weights)
            clause_vecs = torch.einsum("bct,bth->bch", weights, hidden)
            if getattr(self.cfg, "pool_mode", "cls") == "mean_ln":
                clause_vecs = self.pool_norm(clause_vecs)
            # Zero out padded slots (span (0,0)) so they carry no signal.
            padded = (ends <= starts)
            clause_vecs = clause_vecs.masked_fill(padded.unsqueeze(-1), 0.0)
            return self.dropout(clause_vecs)

        def forward(self, full_input_ids, full_attention_mask,
                    clause_input_ids=None, clause_attention_mask=None,
                    clause_counts=None, clause_token_spans=None):
            """full_*: [B, T]; clause_*: [B, C, T] (C = max_clauses, padded).

            One-pass (default, cfg.pooling == "one_pass"): the full question
            is encoded ONCE; clause vectors come from span_pool_clauses()
            over that single encoding, using clause_token_spans [B, C, 2].
            clause_input_ids / clause_attention_mask are ignored in this
            mode (callers may pass None).
            Nine-pass (audit only, cfg.pooling == "nine_pass"): the old
            Lane 03/04 path — each clause is encoded separately from
            clause_input_ids / clause_attention_mask. clause_token_spans is
            ignored in this mode.

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
            if self.cfg.pooling == "one_pass":
                if clause_token_spans is not None and clause_counts is not None:
                    clause_pooled = self.span_pool_clauses(
                        full_hidden, full_attention_mask, clause_token_spans)
                    b, c, _ = clause_pooled.shape
                    out["clause_issue_logits"] = self.issue_head(clause_pooled).view(
                        b, c, len(ISSUES), len(ISSUE_INTENTS))
                    out["clause_fact_logits"] = self.fact_head(clause_pooled).view(
                        b, c, len(FACTS), len(FACT_STATES))
                    out["clause_gate_logits"] = self.clause_gate_head(clause_pooled)
                    out["clause_span_logits"] = self.span_head(clause_pooled).squeeze(-1)
                    out["clause_counts"] = clause_counts
            else:  # nine_pass — audit path only, kept for reproducibility
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
    clause_gate_logits: [B, C, 1] (denied only — Lane B2, 2026-11-27).
    clause_counts: [B] real clause counts (padded slots ignored).
    Returns fused [B, 11, 4] probs (renormalised). Rule (plan §1.2):
      requested_fused = max(full_requested, max over NON-VETOED clauses
                            of clause_requested); a clause is vetoed iff
      its denied gate sigmoid >= tau_neg. Other intents keep the full
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
    cmax_req = masked.amax(dim=1)  # [B, 11]; -inf where no clause kept
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

    Returns plain-JSON-able {issues, facts, enums, spans, clauses, pooling}
    where issues/facts carry {label, confidence, probs} and spans carry the
    top attention-mass token ranges mapped back to char offsets via the
    tokenizer's offset mapping, each with a minimal ``binding``
    (subject/event/polarity/time/span — see bind_evidence(); attention spans
    carry no key, so event is None and polarity "unknown" for them: they are
    evidence pointers, not bound facts). Clause fusion (fuse_issue_probs)
    is applied to the issue head; fact/enum heads use the full encoding.

    Encoding: ``pooling="one_pass"`` (default) tokenizes the full question
    ONCE and derives clause token spans from the offset mapping — no
    separate clause encoding. ``pooling="nine_pass"`` keeps the old audit
    path (full + each clause encoded separately).
    """
    require_torch()
    import torch

    cfg = config or ClassifierConfig()
    model.eval()
    clauses = split_clauses(text, cfg.max_clauses)
    if not clauses:
        return {"issues": {}, "facts": {}, "enums": {}, "spans": [],
                "clauses": [], "pooling": cfg.pooling}
    full = tokenizer(text, return_tensors="pt", truncation=True,
                     max_length=cfg.max_seq_len, return_offsets_mapping=True)
    offsets = full.pop("offset_mapping")[0].tolist()
    c = len(clauses)
    if cfg.pooling == "one_pass":
        spans_idx = clause_token_spans(offsets, clauses)
        clause_token_tensor = torch.tensor([spans_idx], dtype=torch.long)
        clause_ids = clause_mask = None
    else:  # nine_pass — audit path only
        clause_batch = tokenizer(
            [c["text"] for c in clauses], return_tensors="pt", truncation=True,
            max_length=cfg.max_seq_len, padding=True,
        )
        pad_to = cfg.max_clauses
        clause_ids = torch.zeros(1, pad_to, clause_batch["input_ids"].shape[1],
                                 dtype=torch.long)
        clause_mask = torch.zeros_like(clause_ids)
        clause_ids[0, :c] = clause_batch["input_ids"]
        clause_mask[0, :c] = clause_batch["attention_mask"]
        clause_token_tensor = None
    with torch.no_grad():
        try:
            dev = next(model.parameters()).device
        except (StopIteration, AttributeError):
            dev = torch.device("cpu")
        input_ids = full["input_ids"].to(dev)
        attention_mask = full["attention_mask"].to(dev)
        c_ids = clause_ids.to(dev) if clause_ids is not None else None
        c_mask = clause_mask.to(dev) if clause_mask is not None else None
        c_counts = torch.tensor([c], device=dev)
        c_spans = clause_token_tensor.to(dev) if clause_token_tensor is not None else None
        out = model(input_ids, attention_mask,
                    c_ids, c_mask,
                    clause_counts=c_counts,
                    clause_token_spans=c_spans)
        issue_p = torch.softmax(
            out["issue_logits"] / max(cfg.temperature_issue, 1e-6), dim=-1)
        clause_p = torch.softmax(
            out["clause_issue_logits"] / max(cfg.temperature_issue, 1e-6), dim=-1)
        fused = fuse_issue_probs(
            issue_p, clause_p, out["clause_gate_logits"],
            c_counts, tau_neg=cfg.tau_neg,
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
            "probs": {FACT_STATES[j]: round(float(probs[j]), 4)
                      for j in range(len(FACT_STATES))},
        }
    enums: dict[str, Any] = {}
    for head, logits in out["enum_logits"].items():
        probs = torch.softmax(logits[0], dim=-1)
        k = int(torch.argmax(probs))
        enums[head] = {"value": ENUMS[head][k],
                       "confidence": round(float(probs[k]), 4),
                       "probs": {ENUMS[head][j]: round(float(probs[j]), 4)
                                 for j in range(len(ENUMS[head]))}}
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
    # Minimal fact binding (GPT-RERUN P0): attention spans carry no key, so
    # event is None / polarity "unknown" — they are evidence pointers, not
    # bound facts. Subject/time come from the predicted enums. Full binding
    # (which span proves which fact for which claimant/event) needs the
    # schema change filed as OPEN in docs/impl_laneB_classifier_changes.md §6.
    spans = bind_evidence(
        spans,
        {n: facts[n]["state"] for n in FACTS},
        {h: enums[h]["value"] for h in ENUMS},
        issues={n: issues[n]["intent"] for n in ISSUES},
    )
    return {"issues": issues, "facts": facts, "enums": enums,
            "spans": spans, "clauses": clauses, "pooling": cfg.pooling}


def save_checkpoint(model, config: ClassifierConfig, path: str | Path) -> Path:
    """Save {state_dict, config} + config.json next to it — torch required.

    Contract C2 checkpoint layout: models/<name>/best/model.pt +
    config.json (+ thresholds.json, written separately by
    scripts/calibrate_thresholds.py). Writing config.json here (not only in
    the training script) keeps every checkpoint self-describing no matter
    which caller saved it.
    """
    require_torch()
    import torch

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": model.state_dict(),
                "config": config.to_dict()}, path)
    (path.parent / "config.json").write_text(
        json.dumps(config.to_dict(), indent=2), encoding="utf-8")
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
