"""LAYA v7.1 single-pass multi-head student model (V71-P5-1).

Lane 08 (Pillar 5) — scripts + design only. No training, export, or
neural inference is run from this module on this VM (no GPU, no torch
here); the model class below is the execution contract for the user's
RTX 5050 machine / Colab T4.

Design (plan docs/10x_plane.md §5.2, V71-P5-1)
-----------------------------------------------
Teacher: Lane 03's fine-tuned multi-head large encoder
(``src/laya_v7_classifier.py``, V71-P1-3 — NOT yet delivered at the
time this file was written; see DEPENDENCY note below). The teacher
generates soft logit targets over Lane 02's 5,000-example synthetic
bilingual corpus (contract C2: JSONL ``{id, lang, text, issues, facts,
enums, spans}``).

Student: one shared forward pass over ``[full_q] + filtered_clauses``
(batch_size <= 8, max_seq_len <= 192) producing, simultaneously:

* ``issue_logits``  — [11, 4]  (requested / incidental / denied / uncertain)
* ``fact_logits``   — [28, 4]  (supported / denied / unknown / conflicting)
* ``sex_logits``    — [3]      (F / M / U)
* ``role_logits``   — [4]      (spouse / parent / child / other)
* ``time_logits``   — [5]      (present / past / future / hypothetical / quoted)
* ``safety_logits`` — [3]      (none / threat_or_harassment /
  imminent_physical_or_child_danger; Pillar 4, V71-P4-3)

Backbone: <= 120M-150M params, permissive weights only
(Apache-2.0 / MIT / BSD-3-Clause). Candidate backbones are listed in
``BACKBONE_CANDIDATES``; the exact checkpoint + its licence must be
verified at execution time against Lane 06's licence audit (V71-P3-1)
— no backbone is hard-pinned here, because none has been licence-checked
yet. The 120M-150M cap is enforced by :func:`check_param_budget`.

Vocabulary provenance (read this before changing a label)
---------------------------------------------------------
The plan (§1.2) fixes the *counts* — 11 issues, 28 facts — but does
not enumerate them. The lists below are Lane 08's canonicalisation,
derived from the repo at baseline bc7f40f:

* Issues: the 7 extractor ``noul`` issues (``src/laya_v7_extractor.py``
  ``LAYA_NOUL_PROMPTS``: maintenance, custody, stridhan, residence,
  violence, divorce, birth_certificate) + ``joint_property`` (the
  ``jp_p`` probe / HMA s.27 lane) + ``restitution`` (HMA s.9) +
  ``dv_injury_compensation`` (PWDVA s.22) + ``procedure`` (the graph
  root's fifth option). The last two close the exact gap the plan
  §1.1 names: hma-9 and pwdva-22 had zero neural probes.
* Facts: the 28 keys below include all 8 dead graph keys the plan
  §1.1 lists (``interim_asked``, ``money_fact_child_or_parallel``,
  ``stay_in_house_under_eviction_pressure``,
  ``stridhan_held_by_inlaws_refused``,
  ``stridhan_safe_in_own_possession``,
  ``stridhan_abandoned_or_undisputed``, ``urgent_safety_risk``,
  ``hypothetical_or_joint_prop_fact_only``) plus the grounded keys
  used by ``src/laya_v7_evidence.py`` / ``src/laya_v7_graph.py``.
* ``time_logits`` uses the plan's 5 modality labels. Note:
  ``src/laya_v7_schema.py`` adds a sixth, ``"general"``; the student
  emits 5 and the runtime maps ``general -> present`` at decode time
  (see :func:`decode_logits`). If Lane 03's teacher emits 6, the
  coordinator reconciles at merge — do NOT silently widen the head.

If Lane 02's corpus schema or Lane 03's teacher head order differs
from the lists here, the distill script (``scripts/distill_student.py``)
fails loudly instead of silently reordering labels. ``VOCAB_VERSION``
must be bumped on any change.

Tiered serving — mode="auto" (V71-P5-4)
----------------------------------------
Priority (fastest first; exact run commands are in
``docs/10x_swarm_state/lane-08-p5.md`` and in the v7 Colab notebook):

1. ``student_onnx_gpu``      — student INT8/FP16 ONNX on CUDA,  < 50 ms/Q
2. ``student_onnx_int8_cpu`` — student INT8 ONNX on CPU,       < 0.5 s/Q
3. ``laya_teacher_cuda``     — teacher / PIXMELT laya on CUDA, ~0.13 s/Q
4. ``evidence``              — zero-model evidence fallback,   < 1 ms/Q,
                               EN-only emergency fallback

All four latency figures are the plan §5.2/§5.3 *targets*, not measured
results. Nothing in this file claims a measured latency.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from typing import Any

# ---------------------------------------------------------------------------
# Vocabulary (canonical — see module docstring; VOCAB_VERSION bumps on change)
# ---------------------------------------------------------------------------

VOCAB_VERSION = "v71-p5-1"

ISSUES: tuple[str, ...] = (
    "maintenance",
    "custody",
    "stridhan",
    "residence",
    "violence",
    "divorce",
    "joint_property",
    "restitution",
    "dv_injury_compensation",
    "birth_certificate",
    "procedure",
)
assert len(ISSUES) == 11

ISSUE_INTENTS: tuple[str, ...] = ("requested", "incidental", "denied", "uncertain")

FACTS: tuple[str, ...] = (
    "divorce_asked",
    "mutual_consent",
    "contested_divorce_asked",
    "proceeding_pending_hma",
    "being_filed",
    "decree",
    "interim_asked",
    "lump_sum_settlement",
    "custody_claim",
    "residence_claim",
    "violence",
    "coercive_eviction_or_lockout",
    "urgent_safety_risk",
    "child_safety_risk",
    "stridhan_claim",
    "stridhan_safe_in_own_possession",
    "stridhan_held_by_inlaws_refused",
    "stridhan_abandoned_or_undisputed",
    "joint_property_claim",
    "restitution_asked",
    "dv_injury_comp_asked",
    "demand_made",
    "minor_child",
    "birth_cert_asked",
    "in_scope",
    "money_fact_child_or_parallel",
    "stay_in_house_under_eviction_pressure",
    "hypothetical_or_joint_prop_fact_only",
)
assert len(FACTS) == 28

FACT_STATES: tuple[str, ...] = ("supported", "denied", "unknown", "conflicting")

SEX_LABELS: tuple[str, ...] = ("F", "M", "U")
ROLE_LABELS: tuple[str, ...] = ("spouse", "parent", "child", "other")
TIME_LABELS: tuple[str, ...] = ("present", "past", "future", "hypothetical", "quoted")
SAFETY_LABELS: tuple[str, ...] = (
    "none",
    "threat_or_harassment",
    "imminent_physical_or_child_danger",
)

# Head output shapes: name -> (rows, cols). safety/sex/role/time are [1, n].
HEAD_SHAPES: dict[str, tuple[int, int]] = {
    "issue_logits": (len(ISSUES), len(ISSUE_INTENTS)),   # [11, 4]
    "fact_logits": (len(FACTS), len(FACT_STATES)),       # [28, 4]
    "sex_logits": (1, len(SEX_LABELS)),                  # [1, 3]
    "role_logits": (1, len(ROLE_LABELS)),                # [1, 4]
    "time_logits": (1, len(TIME_LABELS)),                # [1, 5]
    "safety_logits": (1, len(SAFETY_LABELS)),            # [1, 3]
}

# ---------------------------------------------------------------------------
# Serving / distillation constants (plan §5.2)
# ---------------------------------------------------------------------------

MAX_SEQ_LEN = 192
BATCH_SIZE = 8
SHAPE_BUCKETS: tuple[int, ...] = (64, 128, 192)
PARAM_BUDGET_MAX = 150_000_000  # <= 120M-150M params (plan §5.2)

# Permissive-licence candidate backbones (plan §5.2 examples). Licences
# are NOT asserted here — Lane 06 (V71-P3-1) must verify the exact
# Hugging Face licence metadata of the chosen checkpoint at execution
# time, and only Apache-2.0 / MIT / BSD-3-Clause weights may ship.
BACKBONE_CANDIDATES: tuple[dict[str, str], ...] = (
    {"id": "6-layer distilled mmBERT (jhu-clsp/mmBERT family)",
     "notes": "plan §5.2 example; verify licence + multilingual coverage at execution"},
    {"id": "answerdotai/ModernBERT-small (ModernBERT-small family)",
     "notes": "plan §5.2 example; verify licence + multilingual coverage at execution"},
    {"id": "MiniLM-L12 multilingual (paraphrase-multilingual-MiniLM-L12-v2 family)",
     "notes": "plan §5.2 example; verify licence + multilingual coverage at execution"},
)
DEFAULT_BACKBONE = BACKBONE_CANDIDATES[0]["id"]

# mode="auto" tier table (V71-P5-4). Latencies are plan TARGETS.
TIER_PRIORITY: tuple[dict[str, str], ...] = (
    {"tier": "1", "mode": "student_onnx_gpu",
     "target_latency": "< 50 ms/Q", "device": "CUDA",
     "artifact": "models/student_int8.onnx (ORT CUDA EP)"},
    {"tier": "2", "mode": "student_onnx_int8_cpu",
     "target_latency": "< 0.5 s/Q", "device": "CPU",
     "artifact": "models/student_int8.onnx (ORT CPU EP)"},
    {"tier": "3", "mode": "laya_teacher_cuda",
     "target_latency": "~0.13 s/Q", "device": "CUDA",
     "artifact": "Lane 03 teacher / PIXMELT laya (v7 baseline 0.133 s/Q mean)"},
    {"tier": "4", "mode": "evidence",
     "target_latency": "< 1 ms/Q", "device": "CPU (no model)",
     "artifact": "zero-model evidence fallback, EN-only emergency"},
)

# ONNX export contract (V71-P5-2).
ONNX_OPSET = 17
ONNX_INPUTS: tuple[str, ...] = ("input_ids", "attention_mask")
ONNX_OUTPUTS: tuple[str, ...] = (
    "issue_logits", "fact_logits", "sex_logits",
    "role_logits", "time_logits", "safety_logits",
)


# ---------------------------------------------------------------------------
# Pure-python helpers (importable and testable WITHOUT torch)
# ---------------------------------------------------------------------------

def pad_to_bucket(seq_len: int) -> int:
    """Deterministic shape-bucket padding (V71-P5-2).

    Rounds ``seq_len`` up to the next bucket in (64, 128, 192).
    Raises on ``seq_len > 192`` — over-long inputs must be truncated
    by the caller (clause filtering), never silently re-bucketed.
    """
    if seq_len <= 0:
        raise ValueError(f"seq_len must be positive, got {seq_len}")
    for bucket in SHAPE_BUCKETS:
        if seq_len <= bucket:
            return bucket
    raise ValueError(
        f"seq_len {seq_len} exceeds MAX_SEQ_LEN={MAX_SEQ_LEN}; "
        "truncate / filter clauses before padding"
    )


def build_student_inputs(text: str, clauses: list[str] | None = None) -> list[str]:
    """One batched student input list: [full_q] + filtered clauses.

    The caller (distill / runtime) tokenizes and pads each entry to its
    shape bucket. The list is capped at ``BATCH_SIZE`` (8); extra
    clauses are dropped deterministically (longest-first is NOT used —
    order is input order, so results are reproducible).
    """
    items = [text] + [c for c in (clauses or []) if c and c.strip()]
    if len(items) > BATCH_SIZE:
        items = items[:BATCH_SIZE]
    return items


def check_param_budget(num_params: int) -> None:
    """Enforce the <= 150M student param budget (plan §5.2)."""
    if num_params > PARAM_BUDGET_MAX:
        raise ValueError(
            f"student has {num_params:,} params, over the "
            f"{PARAM_BUDGET_MAX:,} budget — pick a smaller backbone"
        )


def vocab_fingerprint() -> str:
    """SHA-256 of the canonical vocab — recorded in every run manifest."""
    payload = json.dumps(
        {"version": VOCAB_VERSION, "issues": ISSUES, "facts": FACTS,
         "sex": SEX_LABELS, "role": ROLE_LABELS, "time": TIME_LABELS,
         "safety": SAFETY_LABELS, "heads": HEAD_SHAPES},
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _softmax(logits: list[float]) -> list[float]:
    m = max(logits)
    exps = [math.exp(x - m) for x in logits]
    s = sum(exps)
    return [e / s for e in exps]


def decode_logits(logits: dict[str, Any]) -> dict[str, Any]:
    """Decode raw head logits into IssueEvidence/FactEvidence dicts.

    Pure-python (lists of floats in, dicts out) so the decode contract
    can be unit-tested without torch. ``logits`` values are rows:
    ``issue_logits`` is 11 rows x 4, ``fact_logits`` 28 rows x 4, the
    enum/safety heads are a single row each. ``time`` maps the schema's
    sixth ``"general"`` modality to ``"present"`` (see module docstring).

    Returns ``{"issues": {...}, "facts": {...}, "enums": {...},
    "safety": {...}}`` with per-label probabilities and argmax labels.
    """
    for head, (rows, cols) in HEAD_SHAPES.items():
        if head not in logits:
            raise KeyError(f"missing head output: {head}")
        got = logits[head]
        if len(got) != rows:
            raise ValueError(f"{head}: expected {rows} rows, got {len(got)}")
        for r in got:
            if len(r) != cols:
                raise ValueError(f"{head}: expected {cols} cols, got {len(r)}")

    issues: dict[str, Any] = {}
    for name, row in zip(ISSUES, logits["issue_logits"]):
        probs = _softmax([float(x) for x in row])
        best = max(range(len(probs)), key=lambda i: probs[i])
        issues[name] = {
            "intent": ISSUE_INTENTS[best],
            "confidence": round(probs[best], 4),
            "probs": {k: round(v, 4) for k, v in zip(ISSUE_INTENTS, probs)},
        }
    facts: dict[str, Any] = {}
    for name, row in zip(FACTS, logits["fact_logits"]):
        probs = _softmax([float(x) for x in row])
        best = max(range(len(probs)), key=lambda i: probs[i])
        facts[name] = {
            "status": FACT_STATES[best],
            "confidence": round(probs[best], 4),
            "probs": {k: round(v, 4) for k, v in zip(FACT_STATES, probs)},
        }

    def _enum(head: str, labels: tuple[str, ...]) -> dict[str, Any]:
        probs = _softmax([float(x) for x in logits[head][0]])
        best = max(range(len(probs)), key=lambda i: probs[i])
        return {"label": labels[best], "confidence": round(probs[best], 4),
                "probs": {k: round(v, 4) for k, v in zip(labels, probs)}}

    enums = {
        "claimant_sex": _enum("sex_logits", SEX_LABELS),
        "claimant_role": _enum("role_logits", ROLE_LABELS),
        "modality_time": _enum("time_logits", TIME_LABELS),
    }
    safety = _enum("safety_logits", SAFETY_LABELS)
    return {"issues": issues, "facts": facts, "enums": enums, "safety": safety}


# ---------------------------------------------------------------------------
# PyTorch student model (torch imported lazily — this module must import
# cleanly on machines WITHOUT torch, e.g. this VM)
# ---------------------------------------------------------------------------

def load_student_model(backbone: str = DEFAULT_BACKBONE, device: str = "cpu"):
    """Build the multi-head student. Requires torch + transformers.

    Raises RuntimeError with a clear message (not an ImportError
    traceback) when torch is absent — this VM has no torch by design.
    """
    try:
        import torch
        from torch import nn
        from transformers import AutoConfig, AutoModel
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise RuntimeError(
            "torch + transformers are required to build the student "
            "model. This VM has neither (no GPU, no torch by design). "
            "Run on the RTX 5050 machine or Colab T4. Original error: "
            f"{exc}"
        ) from exc

    class LayaV7Student(nn.Module):
        """Single shared encoder + 6 linear heads (see module docstring)."""

        def __init__(self, backbone_id: str):
            super().__init__()
            self.backbone_id = backbone_id
            self.config = AutoConfig.from_pretrained(backbone_id)
            self.encoder = AutoModel.from_pretrained(backbone_id)
            hidden = self.config.hidden_size
            self.issue_head = nn.Linear(hidden, 11 * 4)
            self.fact_head = nn.Linear(hidden, 28 * 4)
            self.sex_head = nn.Linear(hidden, 3)
            self.role_head = nn.Linear(hidden, 4)
            self.time_head = nn.Linear(hidden, 5)
            self.safety_head = nn.Linear(hidden, 3)

        def forward(self, input_ids, attention_mask=None):
            out = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
            # CLS pooling (index 0); backbone-agnostic and deterministic.
            pooled = out.last_hidden_state[:, 0, :]
            return {
                "issue_logits": self.issue_head(pooled).view(-1, 11, 4),
                "fact_logits": self.fact_head(pooled).view(-1, 28, 4),
                "sex_logits": self.sex_head(pooled),
                "role_logits": self.role_head(pooled),
                "time_logits": self.time_head(pooled),
                "safety_logits": self.safety_head(pooled),
            }

        def num_params(self) -> int:
            return sum(p.numel() for p in self.parameters())

    model = LayaV7Student(backbone)
    check_param_budget(model.num_params())
    return model.to(device)


def select_tier(*, cuda_available: bool, onnx_path: str | None,
                teacher_available: bool) -> dict[str, str]:
    """mode="auto" tier selection (V71-P5-4) — pure decision logic.

    Order: student_onnx_gpu -> student_onnx_int8_cpu -> laya_teacher_cuda
    -> evidence. No model is loaded here; the caller loads the selected
    tier's artifact and falls through on load failure.
    """
    onnx_exists = bool(onnx_path) and os.path.exists(onnx_path)
    if cuda_available and onnx_exists:
        return dict(TIER_PRIORITY[0])
    if onnx_exists:
        return dict(TIER_PRIORITY[1])
    if cuda_available and teacher_available:
        return dict(TIER_PRIORITY[2])
    return dict(TIER_PRIORITY[3])
