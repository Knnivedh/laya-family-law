"""Targeted clarifying-question engine for LAYA v7.1 (10x plan §2.3, V71-P2-4).

Interface note (2026-11-27, Lane 05): Lane 04's
``docs/clarification-fallback-spec.md`` did not exist when this module was
written, so this implements the plan §2.3 spec directly. If Lane 04's spec
lands later, the coordinator should reconcile the two; the public entry
points below are the seam to reconcile against:

    rank_clarifications(state, facts, issues, *, max_questions=2)
    clarifying_questions_for_turn(state, facts, issues, *, max_questions=2)

Ranking rule: remedy-flip information gain. Each candidate fact carries a
base priority (safety first, then scope, then gates that flip whole sections)
plus one point per section whose disposition flips depending on the answer.
At most 2 questions per turn. A question is only asked when the fact is
unknown / conflicting / in the model gray band — never to re-ask a fact the
user already confirmed (provenance rank 1) or a verified span (rank 2).

This module is deliberately dependency-light: it reads FactEvidence /
IssueEvidence dicts and SessionState, and imports nothing from the runtime
(no import cycle). It never calls a model.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .laya_v7_schema import FactEvidence, IssueEvidence, proved_true
from .laya_schema_v71 import SessionState, provenance_rank

MAX_QUESTIONS_PER_TURN = 2

# Gray-band bounds for model confidence. A model-sourced fact whose
# confidence falls inside [TAU_LOW, TAU_HIGH) is "uncertain" and becomes a
# clarification candidate instead of a silent guess. Calibrated values are
# Lane 10's job (V71-P7-3); these defaults are the plan's gray band only.
TAU_LOW = 0.30
TAU_HIGH = 0.70


@dataclass(frozen=True)
class ClarificationTarget:
    """One askable fact: question text + what flips on each answer."""

    fact_key: str
    question: str
    base_priority: float
    flips_if_yes: tuple[str, ...] = ()
    flips_if_no: tuple[str, ...] = ()
    reason: str = ""

    @property
    def flip_count(self) -> int:
        return len(set(self.flips_if_yes) | set(self.flips_if_no))

    def information_gain(self) -> float:
        """Remedy-flip information gain: base priority + sections flipped."""
        return self.base_priority + float(self.flip_count)


# Ordered by plan §2.3 V71-P2-4. Base priorities encode the plan's order:
# (1) safety, (2) scope, (3) proceeding gates, (4) order statute/date,
# (5) demand, (6) minor-child age. Flip lists name the sections whose
# eligible/inapplicable disposition changes on the answer.
CLARIFICATION_TARGETS: tuple[ClarificationTarget, ...] = (
    ClarificationTarget(
        fact_key="violence",
        question=(
            "Are you, or a child in the house, facing threats, hitting, or any "
            "immediate physical danger right now?"
        ),
        base_priority=100.0,
        flips_if_yes=("pwdva-18", "safety"),
        flips_if_no=("pwdva-18",),
        reason="safety check if violence cues uncertain",
    ),
    ClarificationTarget(
        fact_key="urgent_safety_risk",
        question=(
            "Is there an urgent safety risk — for example, is someone in immediate "
            "danger, or is a child at risk of being taken away?"
        ),
        base_priority=99.0,
        flips_if_yes=("safety",),
        flips_if_no=("safety",),
        reason="safety check if urgency cues uncertain",
    ),
    ClarificationTarget(
        fact_key="in_scope",
        question=(
            "Is your question about Indian family law — marriage, divorce, "
            "maintenance, custody, residence, or Stridhan — or is it about a "
            "different matter such as rent, employment, or a loan?"
        ),
        base_priority=90.0,
        flips_if_yes=(),
        flips_if_no=("all",),
        reason="scope disambiguation if kept == [] and in_scope uncertain",
    ),
    ClarificationTarget(
        fact_key="proceeding_pending_hma",
        question=(
            "Is a case about your marriage under the Hindu Marriage Act currently "
            "pending in court?"
        ),
        base_priority=80.0,
        flips_if_yes=("hma-24", "hma-26", "hma-27"),
        flips_if_no=("hma-24", "hma-26", "hma-27"),
        reason="proceeding gate for hma-24/26/27",
    ),
    ClarificationTarget(
        fact_key="being_filed",
        question=(
            "Are you definitely going to file a case about your marriage under the "
            "Hindu Marriage Act, even if no case is pending yet?"
        ),
        base_priority=79.0,
        flips_if_yes=("hma-24", "hma-26", "hma-27"),
        flips_if_no=("hma-24", "hma-26", "hma-27"),
        reason="proceeding gate for hma-24/26/27 (being-filed branch)",
    ),
    ClarificationTarget(
        fact_key="bnss_order",
        question=(
            "Does the existing maintenance order cite section 144 of the BNSS, 2023?"
        ),
        base_priority=70.0,
        flips_if_yes=("bnss-144-3", "bnss-146"),
        flips_if_no=("bnss-144-3", "bnss-146"),
        reason="bnss_order / pre-BNSS 2024 date for enforcement/variation",
    ),
    ClarificationTarget(
        fact_key="demand_made",
        question=(
            "Have you made a written demand for the return of your Stridhan "
            "(gold/jewellery), and was it refused?"
        ),
        base_priority=60.0,
        flips_if_yes=("bns-316",),
        flips_if_no=("bns-316",),
        reason="demand_made for bns-316",
    ),
    ClarificationTarget(
        fact_key="minor_child",
        question="Is the child under 18 years of age?",
        base_priority=50.0,
        flips_if_yes=("bnss-144", "gwa-1890", "hma-26"),
        flips_if_no=("bnss-144", "gwa-1890", "hma-26"),
        reason="minor_child age under 18",
    ),
    ClarificationTarget(
        fact_key="mutual_consent",
        question=(
            "Have both you and your spouse agreed to end the marriage by mutual "
            "consent?"
        ),
        base_priority=45.0,
        flips_if_yes=("hma-13b", "hma-13"),
        flips_if_no=("hma-13b", "hma-13"),
        reason="mutual-consent fork for hma-13 vs hma-13b",
    ),
    ClarificationTarget(
        fact_key="decree",
        question="Has a court already passed a decree in your marriage case?",
        base_priority=40.0,
        flips_if_yes=("hma-25",),
        flips_if_no=("hma-25",),
        reason="decree / lump-sum gate for hma-25",
    ),
    ClarificationTarget(
        fact_key="domestic_relationship",
        question=(
            "Do you live, or did you live, in a shared household with the person "
            "your question is about (husband or in-laws)?"
        ),
        base_priority=35.0,
        flips_if_yes=("pwdva-17", "pwdva-18", "pwdva-19", "pwdva-20"),
        flips_if_no=("pwdva-17", "pwdva-18", "pwdva-19", "pwdva-20"),
        reason="PWDVA s.2(a) domestic-relationship eligibility",
    ),
    ClarificationTarget(
        fact_key="custody_claim",
        question="Are you asking for custody of your child, or for guardianship?",
        base_priority=30.0,
        flips_if_yes=("gwa-1890", "hma-26"),
        flips_if_no=("gwa-1890", "hma-26"),
        reason="custody claim disambiguation",
    ),
)

_TARGET_BY_KEY = {t.fact_key: t for t in CLARIFICATION_TARGETS}

_TARGET_ISSUES = {
    "violence": {"violence", "residence", "dv_compensation"},
    "urgent_safety_risk": {"violence", "residence", "custody"},
    "proceeding_pending_hma": {"maintenance", "custody", "stridhan", "joint_property"},
    "being_filed": {"maintenance", "custody", "stridhan", "joint_property"},
    "demand_made": {"stridhan"},
    "minor_child": {"maintenance", "custody"},
    "mutual_consent": {"divorce"},
    "decree": {"maintenance"},
    "domestic_relationship": {"violence", "residence", "dv_compensation"},
    "custody_claim": {"custody"},
}


def _fact_evidence(facts: dict[str, Any], key: str) -> FactEvidence | None:
    val = facts.get(key)
    if isinstance(val, FactEvidence):
        return val
    return None


def _needs_clarification(
    facts: dict[str, Any], key: str, *, kept_ids: list[str] | None = None
) -> tuple[bool, str]:
    """Decide whether ``key`` is askable this turn, and why.

    Returns (askable, reason). Never askable: user-confirmed facts
    (provenance rank 1), verified user/translated spans (ranks 2-3), or a
    fact already supported/denied with high confidence. Askable: unknown,
    conflicting, or model output inside the gray band.
    """
    ev = _fact_evidence(facts, key)
    if ev is None:
        # No evidence object at all: the fact was never extracted.
        # Askable only for the two plan-mandated gates (safety, scope);
        # other missing facts mean "not raised", not "uncertain".
        if key in ("violence", "urgent_safety_risk", "in_scope"):
            return True, "not_extracted"
        return False, "not_raised"
    if ev.status == "conflicting":
        return True, "conflicting"
    if provenance_rank(ev.source) == 1 or ev.span is not None:
        return False, "already_verified"
    if ev.status == "unknown":
        return True, "unknown"
    if ev.source in ("model_uncertain", "model", "model_suggestion"):
        if TAU_LOW <= float(ev.confidence or 0.0) < TAU_HIGH:
            return True, "gray_band"
    return False, "settled"


def rank_clarifications(
    state: SessionState | None,
    facts: dict[str, Any],
    issues: dict[str, Any] | None = None,
    *,
    max_questions: int = MAX_QUESTIONS_PER_TURN,
    kept_ids: list[str] | None = None,
) -> list[dict[str, str]]:
    """Rank missing/uncertain/conflicting facts by remedy-flip gain.

    Returns at most ``max_questions`` dicts, highest gain first, each with
    ``fact_key``, ``question``, ``reason`` and ``information_gain`` (as a
    string, matching the SessionState.pending_clarifications shape).
    Safety questions always outrank everything else; already-asked questions
    still pending in ``state`` are not repeated.
    """
    kept = list(kept_ids or [])
    already_pending = set()
    if state is not None:
        already_pending = {q.get("fact_key") for q in state.pending_clarifications}

    # Plan rule: scope disambiguation fires only when nothing was kept and
    # scope itself is uncertain.
    scope_candidate = kept == [] and not proved_true(facts, "in_scope", default=False)
    requested = {name for name, item in (issues or {}).items()
                 if isinstance(item, IssueEvidence) and item.intent == "requested"}

    scored: list[tuple[float, ClarificationTarget, str]] = []
    for target in CLARIFICATION_TARGETS:
        if target.fact_key in already_pending:
            continue
        if target.fact_key == "in_scope" and not scope_candidate:
            # in_scope is only asked when kept == [] (plan §2.3 rule 2);
            # a kept section already proves scope.
            continue
        relevant_to = _TARGET_ISSUES.get(target.fact_key)
        if relevant_to is not None and relevant_to.isdisjoint(requested):
            continue
        if target.fact_key == "bnss_order" and not proved_true(facts, "existing_order_enforcement"):
            continue
        if target.fact_key == "minor_child" and not proved_true(facts, "child_fact"):
            continue
        askable, why = _needs_clarification(facts, target.fact_key, kept_ids=kept)
        if not askable:
            continue
        # Conflicting extractions outrank gray-band ones at the same base.
        gain = target.information_gain()
        if why == "conflicting":
            gain += 5.0
        scored.append((gain, target, why))

    scored.sort(key=lambda item: (-item[0], item[1].fact_key))
    out: list[dict[str, str]] = []
    for gain, target, why in scored[:max_questions]:
        out.append({
            "fact_key": target.fact_key,
            "question": target.question,
            "reason": f"{target.reason} ({why})",
            "information_gain": f"{gain:.1f}",
            "flips_if_yes": ", ".join(target.flips_if_yes),
            "flips_if_no": ", ".join(target.flips_if_no),
        })
    return out


def clarifying_questions_for_turn(
    state: SessionState | None,
    facts: dict[str, Any],
    issues: dict[str, Any] | None = None,
    *,
    max_questions: int = MAX_QUESTIONS_PER_TURN,
    kept_ids: list[str] | None = None,
) -> list[dict[str, str]]:
    """Alias for rank_clarifications (Lane 04 spec seam name)."""
    return rank_clarifications(
        state, facts, issues, max_questions=max_questions, kept_ids=kept_ids
    )


def disambiguation_prompt(fact_key: str, prior_status: str, new_status: str) -> dict[str, str]:
    """Build the targeted disambiguation prompt for a conflicting fact."""
    target = _TARGET_BY_KEY.get(fact_key)
    question = target.question if target else (
        f"Earlier you indicated {fact_key} was {prior_status}, but the latest "
        f"message suggests {new_status}. Which is correct?"
    )
    return {
        "fact_key": fact_key,
        "question": question,
        "reason": f"conflicting extraction: prior={prior_status} vs new={new_status}",
        "information_gain": "conflict",
        "flips_if_yes": ", ".join(target.flips_if_yes) if target else "",
        "flips_if_no": ", ".join(target.flips_if_no) if target else "",
    }
