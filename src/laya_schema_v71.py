"""Unified v7.1 data contracts for the LAYA multi-turn runtime (10x plan §2.2).

This module is the single source of truth for provenance, turn records and
session state. It re-exports the v7 evidence types (FactEvidence,
IssueEvidence, TextSpan, RemedyDisposition) from ``laya_v7_schema`` so the
unified runtime and the legacy runtimes share one type identity — no parallel
``FactEvidence`` copy is introduced here.

Provenance precedence (lowest number wins; ties break by newer turn):
    1 user_confirmation        explicit answer to a clarification / --confirm
    2 user_text_verified_span  literal current/recent user span (non-hypothetical)
    3 translated_verified_span span grounded after permissive translation
    4 model_calibrated_high    P >= tau_high(key)
    5 model_uncertain          tau_low <= P < tau_high -> asks clarification
    6 default                  unresolved / unknown
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

# Re-export / compat: one shared identity with src/laya_v7_schema.py.
from .laya_v7_schema import (  # noqa: F401  (re-exported for runtime consumers)
    DISPOSITION_STATUSES,
    ESCALATION_KINDS,
    FACT_STATUSES,
    ISSUE_INTENTS,
    FactEvidence,
    FactStatus,
    IssueEvidence,
    IssueIntent,
    RemedyDisposition,
    TextSpan,
    fact_value,
    is_denied,
    proved_true,
)

ProvenanceSource = Literal[
    "user_confirmation",           # Precedence 1: explicit answer to clarification or --confirm
    "user_text_verified_span",     # Precedence 2: literal current/recent user span (non-hypothetical)
    "translated_verified_span",    # Precedence 3: span grounded after permissive translation
    "model_calibrated_high",       # Precedence 4: P >= tau_high(key)
    "model_uncertain",             # Precedence 5: tau_low <= P < tau_high -> asks clarification
    "default",                     # Precedence 6: unresolved / unknown
]

PROVENANCE_SOURCES: tuple[str, ...] = (
    "user_confirmation",
    "user_text_verified_span",
    "translated_verified_span",
    "model_calibrated_high",
    "model_uncertain",
    "default",
)

#: Lower number = stronger provenance. Ties are broken by recency (newer turn wins).
PROVENANCE_PRECEDENCE: dict[str, int] = {
    "user_confirmation": 1,
    "user_text_verified_span": 2,
    "translated_verified_span": 3,
    "model_calibrated_high": 4,
    "model_uncertain": 5,
    "default": 6,
}

#: Legacy / free-form source strings mapped onto the v7.1 provenance lattice.
#: Anything unrecognised falls back to "model_uncertain" (never silently
#: promoted to a verified span).
LEGACY_SOURCE_MAP: dict[str, ProvenanceSource] = {
    "user_confirmation": "user_confirmation",
    "user_text": "user_text_verified_span",
    "user_text_verified_span": "user_text_verified_span",
    "translated": "translated_verified_span",
    "translated_text": "translated_verified_span",
    "translated_verified_span": "translated_verified_span",
    "model": "model_calibrated_high",
    "model_calibrated_high": "model_calibrated_high",
    "model_suggestion": "model_uncertain",
    "model_uncertain": "model_uncertain",
    "default": "default",
    "unresolved": "default",
}


def provenance_rank(source: str | None) -> int:
    """Precedence rank for a provenance source string (1 strongest, 6 weakest)."""
    if source is None:
        return PROVENANCE_PRECEDENCE["default"]
    mapped = LEGACY_SOURCE_MAP.get(str(source), None)
    if mapped is not None:
        return PROVENANCE_PRECEDENCE[mapped]
    # Unknown source strings are treated as uncertain model output, never as
    # verified user text.
    return PROVENANCE_PRECEDENCE["model_uncertain"]


def canonical_provenance(source: str | None) -> ProvenanceSource:
    """Normalise any legacy source string onto the 6-level lattice."""
    if source is None:
        return "default"
    return LEGACY_SOURCE_MAP.get(str(source), "model_uncertain")


@dataclass
class TurnRecord:
    turn_id: int
    raw_text: str
    lang: str
    script: str
    extracted_facts: dict[str, FactEvidence] = field(default_factory=dict)
    extracted_issues: dict[str, IssueEvidence] = field(default_factory=dict)
    confirmations: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "raw_text": self.raw_text,
            "lang": self.lang,
            "script": self.script,
            "extracted_facts": {k: v.to_dict() for k, v in self.extracted_facts.items()},
            "extracted_issues": {k: v.to_dict() for k, v in self.extracted_issues.items()},
            "confirmations": dict(self.confirmations),
        }


@dataclass
class SessionState:
    session_id: str
    turns: list[TurnRecord] = field(default_factory=list)
    fact_history: dict[str, list[FactEvidence]] = field(default_factory=dict)
    active_facts: dict[str, FactEvidence] = field(default_factory=dict)
    active_issues: dict[str, IssueEvidence] = field(default_factory=dict)
    override_log: list[dict[str, Any]] = field(default_factory=list)
    pending_clarifications: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "turns": [t.to_dict() for t in self.turns],
            "fact_history": {k: [e.to_dict() for e in v] for k, v in self.fact_history.items()},
            "active_facts": {k: v.to_dict() for k, v in self.active_facts.items()},
            "active_issues": {k: v.to_dict() for k, v in self.active_issues.items()},
            "override_log": [dict(e) for e in self.override_log],
            "pending_clarifications": [dict(q) for q in self.pending_clarifications],
        }


def new_session(session_id: str) -> SessionState:
    """Create an empty session. Session ids are caller-supplied (UUID or test id)."""
    return SessionState(session_id=session_id)


#: Fact keys the v7.1 runtime recognises for generic bi-directional override.
#: Kept deliberately broad: every key Stage 0/1 can emit plus the procedural
#: keys Stage 2 gates on. Unknown confirmation keys are still accepted by
#: resolve_turn_state (stored as facts) but are not mapped to an issue.
KNOWN_FACT_KEYS: tuple[str, ...] = (
    "divorce_asked",
    "mutual_consent",
    "judicial_separation_only",
    "restitution_asked",
    "money_fact",
    "custody_claim",
    "residence_claim",
    "violence",
    "stridhan_claim",
    "stridhan_held_or_disposed",
    "stridhan_sold_or_mortgaged",
    "stridhan_held_by_inlaws_refused",
    "stridhan_safe_in_own_possession",
    "joint_property_claim",
    "proceeding_pending_hma",
    "being_filed",
    "decree",
    "demand_made",
    "first_demand_never_made",
    "bnss_order",
    "pre_bnss_order",
    "existing_order_enforcement",
    "lump_sum_settlement",
    "interim_asked",
    "interim_only_asked",
    "child_fact",
    "minor_child",
    "child_maintenance_only",
    "child_safety_risk",
    "urgent_safety_risk",
    "coercive_eviction_or_lockout",
    "explicit_residence_order_only",
    "dv_injury_comp_asked",
    "birth_cert_asked",
    "domestic_relationship",
    "in_scope",
    "no_dispute_empty",
    "claimant_sex",
    "claimant_role",
    "hypothetical_or_joint_prop_fact_only",
)

#: Fact key -> issue name for the bi-directional override sync in
#: resolve_turn_state. Keys absent here (procedural / gating-only keys such
#: as proceeding_pending_hma, decree, demand_made) update the fact only.
FACT_KEY_TO_ISSUE: dict[str, str] = {
    "divorce_asked": "divorce",
    "restitution_asked": "restitution",
    "money_fact": "maintenance",
    "custody_claim": "custody",
    "residence_claim": "residence",
    "violence": "violence",
    "stridhan_claim": "stridhan",
    "joint_property_claim": "joint_property",
    "dv_injury_comp_asked": "dv_compensation",
    "birth_cert_asked": "birth_certificate",
}
