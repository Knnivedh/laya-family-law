"""Single unified runtime entrypoint for LAYA v7.1 (10x plan §2, V71-P2-1).

``assess_turn(state, question, *, confirmations=None,
vocab_profile="v4_legacy_18", ...) -> (result, new_state)`` merges the two
split runtimes — the maintenance intake (``laya_family.assess`` /
``guided_assessment``) and the full family-law pipeline (``laya_v7.assess_v7``)
— behind one SessionState-carrying entrypoint with three vocabulary profiles:

* ``v4_legacy_18`` — bnss-144-3 / bnss-146 fold into bnss-144 (16-Q /
  Sealed / v7 backward comparability; custody vocab ``v3_bundled``).
* ``brutal_primary`` — statutory-primary custody (``gwa-1890`` | ``hma-26``
  only in kept_ids; ``hmga-1956-s6`` + ``welfare-principle`` in
  applied_principles; custody vocab ``statutory_primary``).
* ``maintenance_sub_routes`` — exposes bnss-144, bnss-144-3, bnss-146,
  hma-24, hma-25 cleanly via the maintenance intake for maintenance
  questions, with the full pipeline as fallback for multi-issue questions.

Delegation (guarded — this VM has no torch/CUDA, so neural extraction must
degrade, never crash):
* Stage 0/1 extraction delegates to ``laya_v7.extract_v7``; on this VM
  ``mode="auto"`` resolves to evidence-only extraction. If the import itself
  fails, extraction falls back to ``laya_v7_evidence.extract_grounded_v7``
  and, failing that, to an empty-facts result that asks clarifying questions
  instead of guessing.
* Stage 2 delegates to ``laya_graph_engine.execute`` (Graph v4.1 + Layer A);
  if the v4.1 JSON is absent it falls back to ``evaluate_stage2_v7`` and
  records the fallback in the result.
* Prose delegates to ``laya_prose_v2.render_prose`` / ``prose_forbidden_check``
  with the REAL ``gated_out`` (fixing the ``laya_v7.py`` ``[]`` bug).
* Maintenance sub-routes delegate to ``laya_family.assess`` with an
  evidence-only extractor shim (no model) when the profile asks for it.

State handling (declared per docs/laya-10-10-exact-plan.md §4.4): the runtime
passes an ACCUMULATED FACTS OBJECT forward (``SessionState.active_facts`` /
``active_issues``), not the full raw conversation history, and recomputes
``kept_ids`` fresh from the merged facts every turn — prior turns' kept_ids
are NEVER unioned forward, so stale sections cannot persist (MT2/MT3).

This module does NOT refactor ``laya_v7.py`` / ``laya_family.py`` into thin
wrappers (contract C4 — Lane 01 owns those files). The precise patch spec
for that refactor lives in ``docs/10x_swarm_state/lane-05-p2.md``.
"""

from __future__ import annotations

import uuid
from time import perf_counter
from typing import Any, Literal

from .laya_clarifier import rank_clarifications
from .laya_graph_engine import (
    PROFILE_CUSTODY_VOCAB,
    VOCAB_PROFILES,
    apply_vocab_profile,
    load_graph_v41,
)
from .laya_schema_v71 import (
    FACT_KEY_TO_ISSUE,
    FactEvidence,
    IssueEvidence,
    SessionState,
    TurnRecord,
    canonical_provenance,
    new_session,
    provenance_rank,
)
from .laya_v7_schema import proved_true

# ---------------------------------------------------------------------------
# Guarded delegation imports (torch is NOT installed on this VM).
# ---------------------------------------------------------------------------

try:  # noqa: SIM105 — guarded import, fallback handled below
    from .laya_v7_extractor import extract_v7 as _extract_v7
except Exception:  # pragma: no cover - import-time degradation
    _extract_v7 = None  # type: ignore[assignment]

try:
    from .laya_v7_evidence import extract_grounded_v7 as _extract_grounded_v7
    from .laya_v7_evidence import judicial_separation_intent as _judicial_separation_intent
except Exception:  # pragma: no cover
    _extract_grounded_v7 = None  # type: ignore[assignment]
    _judicial_separation_intent = None  # type: ignore[assignment]

try:
    from .laya_v7_graph import evaluate_stage2_v7 as _evaluate_stage2_v7
except Exception:  # pragma: no cover
    _evaluate_stage2_v7 = None  # type: ignore[assignment]

try:
    from .laya_graph_engine import execute as _graph_execute
except Exception:  # pragma: no cover
    _graph_execute = None  # type: ignore[assignment]

try:
    from .laya_prose_v2 import prose_forbidden_check as _prose_forbidden_check
    from .laya_prose_v2 import render_prose as _render_prose
except Exception:  # pragma: no cover
    _prose_forbidden_check = None  # type: ignore[assignment]
    _render_prose = None  # type: ignore[assignment]

try:
    from . import laya_family as _laya_family
except Exception:  # pragma: no cover
    _laya_family = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Superseding state transitions (plan §2.3, MT1–MT3).
# Each rule: trigger fact becoming supported this turn retires `from_section`
# in favour of `to_section` and logs the transition in override_log.
# ---------------------------------------------------------------------------

SUPERSEDING_TRANSITIONS: tuple[dict[str, Any], ...] = (
    {
        "id": "MT3-custody-route",
        "trigger_fact": "proceeding_pending_hma",
        "trigger_value": True,
        "from_section": "gwa-1890",
        "to_section": "hma-26",
        "note": "Proceeding starts: standalone guardianship route retires, HMA s.26 becomes the custody route.",
    },
    {
        "id": "MT2-divorce-mutual-consent",
        "trigger_fact": "mutual_consent",
        "trigger_value": True,
        "from_section": "hma-13",
        "to_section": "hma-13b",
        "note": "Mutual consent added: contested-divorce framing must not persist.",
    },
    {
        "id": "MT3-decree-passes",
        "trigger_fact": "decree",
        "trigger_value": True,
        "from_section": "hma-24",
        "to_section": "hma-25",
        "note": "Decree passes: interim HMA s.24 framing must not persist as the live route; HMA s.25 keeps.",
    },
    {
        "id": "MT1-demand-to-recovery",
        "trigger_fact": "demand_made",
        "trigger_value": True,
        "from_section": "demand-first-escalation",
        "to_section": "bns-316",
        "note": "Written demand made and refused: BNS s.316 flips from demand-first escalation to live recovery; HMA s.27 stays.",
    },
)


def _evidence_for(
    key: str,
    status: str,
    value: Any,
    source: str,
    confidence: float,
    turn: int,
) -> FactEvidence:
    return FactEvidence(
        key=key,
        status=status,  # type: ignore[arg-type]
        value=value,
        source=canonical_provenance(source),
        confidence=float(confidence),
        turn=turn,
    )


def _issue_for(issue: str, intent: str, source: str, confidence: float, turn: int) -> IssueEvidence:
    return IssueEvidence(
        issue=issue,
        intent=intent,  # type: ignore[arg-type]
        source=canonical_provenance(source),
        confidence=float(confidence),
        turn=turn,
    )


def _flag_conflict(
    state: SessionState,
    key: str,
    prior: FactEvidence,
    new: FactEvidence,
    turn_id: int,
) -> None:
    """Flag a genuine span-vs-span contradiction; enqueue disambiguation."""
    flagged = FactEvidence(
        key=key,
        status="conflicting",
        value=new.value,
        source=canonical_provenance(new.source),
        confidence=float(new.confidence or 0.0),
        turn=turn_id,
    )
    state.active_facts[key] = flagged
    state.pending_clarifications.append({
        "fact_key": key,
        "question": (
            f"Earlier turns indicated {key} was {prior.status}, but the latest "
            f"message suggests {new.status}. Which is correct?"
        ),
        "reason": f"conflicting extraction: prior={prior.status} vs new={new.status}",
        "information_gain": "conflict",
        "flips_if_yes": "",
        "flips_if_no": "",
    })
    state.override_log.append({
        "turn": turn_id,
        "kind": "conflict_flagged",
        "fact_key": key,
        "prior_status": prior.status,
        "new_status": new.status,
        "prior_source": prior.source,
        "new_source": new.source,
    })


def resolve_turn_state(
    state: SessionState,
    new_turn: TurnRecord,
    confirmations: dict[str, Any] | None = None,
) -> SessionState:
    """Merge one new turn into session state (replaces apply_confirmations_v7).

    Rules (plan §2.3 V71-P2-3):
    * Generic bi-directional override for EVERY fact key: True removes any
      prior negated_issues entry and upgrades the mapped issue intent to
      "requested"; False adds to negated_issues and sets intent "denied".
      Non-bool confirmations (e.g. claimant_sex="female") set the value with
      status "supported". Unknown keys are stored as facts without an issue
      mapping — never dropped, never crash.
    * Provenance lattice: a new fact only replaces the active fact when its
      provenance rank is stronger (lower number), or on equal rank when it is
      from a newer turn. A model guess NEVER overrides a user confirmation
      or a verified span. Additionally, because the grounded extractor emits
      a closed-world per-turn assignment (absence in this turn's text =
      "denied", span=None), supported facts are STICKY against later-turn
      absence-denials — see the accretion block for the verified finding.
    * MT4 accretion: non-contradictory facts/issues from turns 1..t-1 persist.
    * MT2/MT3 superseding transitions: logged in override_log; stale
      sections are retired (kept_ids are recomputed fresh each turn, so the
      retired section cannot be carried forward — see assess_turn).
    * Conflicting extraction flagging: when BOTH sides are grounded in text
      spans with opposite statuses, set FactEvidence.status = "conflicting"
      and enqueue a targeted disambiguation prompt in
      pending_clarifications instead of silently guessing.
    """
    turn_id = new_turn.turn_id

    # 1. Accrete extracted facts/issues (MT4) under the provenance lattice.
    #
    # DESIGN FINDING (verified 2026-11-27 against extract_v7 evidence mode):
    # the grounded extractor emits a COMPLETE closed-world assignment per
    # turn — every fact gets supported/denied with source "user_text",
    # confidence 1.0, and span=None on every denial. A "denied" therefore
    # means "not mentioned in THIS turn's text", not "explicitly denied by
    # the user", and it carries no span to distinguish the two cases. So:
    #   * supported facts are STICKY: a later turn's absence-denial NEVER
    #     retracts a prior supported fact (otherwise MT4 accretion is
    #     impossible — turn 2 would erase turn 1's residence claim).
    #   * a later supported fact DOES overwrite a prior denied one (the
    #     fact is newly asserted — this is MT4 accretion itself).
    #   * "unknown" never overwrites anything.
    #   * explicit issue retractions use the separate denied intent below.
    #   * a genuine conflict is flagged ONLY when both sides are grounded in
    #     text spans (prior.span and new.span both present) with opposite
    #     statuses — otherwise the "contradiction" is just absence.
    for key, ev in new_turn.extracted_facts.items():
        ev.turn = turn_id
        prior = state.active_facts.get(key)
        if prior is None:
            state.active_facts[key] = ev
        elif ev.status == "unknown" or provenance_rank(ev.source) > provenance_rank(prior.source):
            pass  # lower provenance and absent evidence cannot displace a decision
        elif ev.status == prior.status:
            state.active_facts[key] = ev  # newer turn refreshes
        elif prior.status == "supported" and ev.status == "denied":
            if prior.span is not None and ev.span is not None:
                _flag_conflict(state, key, prior, ev, turn_id)
            elif provenance_rank(ev.source) == 1:
                state.active_facts[key] = ev
            else:
                state.override_log.append({
                    "turn": turn_id,
                    "kind": "accretion_retained",
                    "fact_key": key,
                    "prior_status": prior.status,
                    "new_status": ev.status,
                    "note": "later-turn absence-denial does not retract a prior supported fact",
                })
        elif prior.status == "denied" and ev.status == "supported":
            if prior.span is not None and ev.span is not None:
                _flag_conflict(state, key, prior, ev, turn_id)
            else:
                state.active_facts[key] = ev  # newly asserted fact accretes
        elif prior.status == "conflicting":
            if ev.span is not None and provenance_rank(ev.source) <= 2:
                state.active_facts[key] = ev  # verified span resolves conflict
            # else: keep conflicting; clarification already pending
        else:
            # prior unknown + new decided, or any other combination: take new.
            state.active_facts[key] = ev
        state.fact_history.setdefault(key, []).append(state.active_facts[key])

    for name, ev in new_turn.extracted_issues.items():
        ev.turn = turn_id
        prior = state.active_issues.get(name)
        if prior is None:
            state.active_issues[name] = ev
        elif ev.intent != "uncertain" and (
            prior.intent == "uncertain" or provenance_rank(ev.source) <= provenance_rank(prior.source)
        ):
            # Grounded denials explicitly retract an issue. Omission is uncertain.
            state.active_issues[name] = ev

    # 2. Explicit user confirmations (provenance rank 1 — always win).
    if confirmations:
        for key, value in confirmations.items():
            if isinstance(value, bool):
                status = "supported" if value else "denied"
                state.active_facts[key] = _evidence_for(
                    key, status, value, "user_confirmation", 1.0, turn_id
                )
                issue = FACT_KEY_TO_ISSUE.get(key)
                if issue is not None:
                    if value:
                        state.active_issues[issue] = _issue_for(
                            issue, "requested", "user_confirmation", 1.0, turn_id
                        )
                    else:
                        state.active_issues[issue] = _issue_for(
                            issue, "denied", "user_confirmation", 1.0, turn_id
                        )
                state.override_log.append({
                    "turn": turn_id,
                    "kind": "confirmation_override",
                    "fact_key": key,
                    "value": value,
                    "issue": FACT_KEY_TO_ISSUE.get(key),
                })
            else:
                # Non-bool confirmation (enum / string value, e.g. claimant_sex).
                state.active_facts[key] = _evidence_for(
                    key, "supported", value, "user_confirmation", 1.0, turn_id
                )
                state.override_log.append({
                    "turn": turn_id,
                    "kind": "confirmation_override",
                    "fact_key": key,
                    "value": value,
                    "issue": FACT_KEY_TO_ISSUE.get(key),
                })
            state.fact_history.setdefault(key, []).append(state.active_facts[key])
        # in_scope=False confirmation is a scope override, not an issue.
        if confirmations.get("in_scope") is False:
            state.active_facts["in_scope"] = _evidence_for(
                "in_scope", "denied", False, "user_confirmation", 1.0, turn_id
            )

    _apply_superseding_transitions(state, turn_id)

    state.turns.append(new_turn)
    return state


def _negated_issues(state: SessionState) -> set[str]:
    """Negated-issue set, derived from active_issues (single source of truth).

    Deliberately NOT stored as a FactEvidence inside active_facts:
    ``evaluate_stage2_v7`` / ``_normalize_legacy_facts`` expect
    ``facts["negated_issues"]`` to be a plain set, and a FactEvidence value
    there raises ``TypeError: 'FactEvidence' object is not iterable``.
    """
    return {name for name, ie in state.active_issues.items() if ie.intent == "denied"}


def stage2_facts(
    state: SessionState,
    *,
    extra_negated: set[str] | None = None,
    open_fact_markers: set[str] | None = None,
) -> dict[str, Any]:
    """Build the facts dict Stage 2 consumes from session state.

    FactEvidence values pass through untouched; ``negated_issues`` and
    ``open_fact_markers`` are attached as plain sets, matching the contract
    ``evaluate_stage2_v7`` expects.
    """
    facts: dict[str, Any] = {
        k: v for k, v in state.active_facts.items() if isinstance(v, FactEvidence)
    }
    negated = _negated_issues(state) | (extra_negated or set())
    facts["negated_issues"] = negated
    facts["open_fact_markers"] = set(open_fact_markers or set())
    return facts


def _apply_superseding_transitions(state: SessionState, turn_id: int) -> None:
    """Log MT1–MT3 transitions whose trigger newly became supported."""
    facts = state.active_facts
    for rule in SUPERSEDING_TRANSITIONS:
        trigger = facts.get(rule["trigger_fact"])
        if trigger is None or trigger.status != "supported" or trigger.value is not True:
            continue
        # Only log when the trigger fired on THIS turn (not a stale re-log).
        if trigger.turn != turn_id:
            continue
        # MT1 demand->recovery additionally needs an active stridhan claim.
        if rule["id"] == "MT1-demand-to-recovery":
            sc = facts.get("stridhan_claim")
            if sc is None or sc.status != "supported":
                continue
        # MT2 additionally needs divorce_asked (mutual consent alone is not a divorce).
        if rule["id"] == "MT2-divorce-mutual-consent":
            da = facts.get("divorce_asked")
            if da is None or da.status != "supported":
                continue
        already = any(
            e.get("kind") == "superseding_transition"
            and e.get("transition_id") == rule["id"]
            and e.get("turn") == turn_id
            for e in state.override_log
        )
        if already:
            continue
        state.override_log.append({
            "turn": turn_id,
            "kind": "superseding_transition",
            "transition_id": rule["id"],
            "trigger_fact": rule["trigger_fact"],
            "from_section": rule["from_section"],
            "to_section": rule["to_section"],
            "retired_section": rule["from_section"],
            "note": rule["note"],
        })


# ---------------------------------------------------------------------------
# Extraction + maintenance delegation
# ---------------------------------------------------------------------------

def _extract(question: str, *, locale: str | None, mode: str, device: str,
              kannada_strategy: str, strict_pwdva: bool = False) -> dict[str, Any]:
    """Stage 0/1 extraction with graceful degradation (never raises).

    When ``mode`` is ``"auto"`` or ``"classifier"`` and a trained v7.1
    checkpoint (``models/v71-classifier/best/model.pt``) is available, runs the
    trained multilingual classifier bridged via ``laya_integrated`` and merges
    deterministic English strict-PWDVA/grounded safety checks without letting
    English-only regex vetoes silence Kannada or Kanglish questions.
    """
    options = {"strict_pwdva": True} if strict_pwdva else {}
    if mode in ("auto", "classifier"):
        try:
            from . import laya_integrated as _integrated
            if _integrated.checkpoint_exists():
                resolved_ckpt = _integrated.resolve_checkpoint(None)
                from .laya_lang_normalizer import detect_script_locale
                lang_info = detect_script_locale(question)
                lang_code = str(lang_info.get("lang", "en"))
                if mode == "auto":
                    issues, facts, _ = _integrated._auto_stage1(question, lang_code, resolved_ckpt)
                else:
                    pred = _integrated._predict_classifier(question, resolved_ckpt)
                    issues, facts, _ = _integrated._classifier_to_stage1(pred, question)
                if strict_pwdva and _extract_grounded_v7 is not None:
                    grounded = _extract_grounded_v7(question, strict_pwdva=True)
                    gfacts = grounded.get("facts") or {}
                    if "pwdva_monetary_basis_blocked" in gfacts:
                        facts["pwdva_monetary_basis_blocked"] = gfacts["pwdva_monetary_basis_blocked"]
                    gneg = set(grounded.get("negated_issues") or set())
                    for n in gneg:
                        if n not in issues or issues[n].intent != "requested":
                            issues[n] = IssueEvidence(issue=n, intent="denied", source="grounded_guard", confidence=1.0)
                    facts["negated_issues"] = set(facts.get("negated_issues") or set()) | gneg
                return {
                    "lang": lang_code,
                    "script": str(lang_info.get("script", "latin")),
                    "translated_text": None,
                    "extractor_mode": "classifier",
                    "facts": facts,
                    "issues": issues,
                    "negated_issues": set(facts.get("negated_issues") or set()),
                }
            elif mode == "classifier":
                return {"error": "v71 classifier checkpoint missing", "facts": {}, "issues": {},
                        "negated_issues": set(), "lang": "en", "script": "latin",
                        "extractor_mode": "failed", "translated_text": None}
        except Exception as exc:
            if mode == "classifier":
                return {"error": f"v71 classifier failed: {exc}", "facts": {}, "issues": {},
                        "negated_issues": set(), "lang": "en", "script": "latin",
                        "extractor_mode": "failed", "translated_text": None}
    if _extract_v7 is not None:
        try:
            return _extract_v7(
                question, locale=locale, mode=mode, device=device,
                kannada_strategy=kannada_strategy, **options,
            )
        except Exception as exc:  # neural path unavailable on this VM
            return {"error": f"extract_v7 failed: {exc}", "facts": {}, "issues": {},
                    "negated_issues": set(), "lang": "en", "script": "latin",
                    "extractor_mode": "failed", "translated_text": None}
    if _extract_grounded_v7 is not None:
        try:
            grounded = _extract_grounded_v7(question, **options)
            return {
                "lang": "en", "script": "latin", "translated_text": None,
                "extractor_mode": "evidence",
                "facts": dict(grounded.get("facts", {})),
                "issues": dict(grounded.get("issues", {})),
                "negated_issues": set(grounded.get("negated_issues", set())),
            }
        except Exception as exc:
            return {"error": f"extract_grounded_v7 failed: {exc}", "facts": {},
                    "issues": {}, "negated_issues": set(), "lang": "en",
                    "script": "latin", "extractor_mode": "failed",
                    "translated_text": None}
    return {"error": "no extractor available", "facts": {}, "issues": {},
            "negated_issues": set(), "lang": "en", "script": "latin",
            "extractor_mode": "unavailable", "translated_text": None}


def _maintenance_sub_routes(question: str) -> dict[str, Any] | None:
    """Maintenance-profile delegation to laya_family.assess (evidence-only).

    Uses an evidence-only extractor shim (no model) so the call works on a
    CPU-only VM. Returns None when the maintenance intake is unavailable or
    the question is outside maintenance (caller falls back to the full pipeline).
    """
    if _laya_family is None:
        return None
    try:
        def _evidence_only_extractor(text: str) -> dict[str, float | str]:
            # laya_family.assess only needs a scores mapping; evidence-only
            # means "unknown" everywhere except what the regex evidence proves
            # via procedural_evidence inside assess() itself.
            return {field: "unknown" for field in _laya_family.QUESTIONS}

        result = _laya_family.assess(question, _evidence_only_extractor, {})
        if result.get("status") in ("outside_maintenance", "unsupported_language"):
            return None
        return result
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Unified entrypoint
# ---------------------------------------------------------------------------

def assess_turn(
    state: SessionState | None,
    question: str,
    *,
    confirmations: dict[str, Any] | None = None,
    vocab_profile: str = "v4_legacy_18",
    locale: str | None = None,
    mode: str = "auto",
    device: str = "cuda",
    kannada_strategy: str = "native_laya",
    with_prose: bool = True,
    session_id: str | None = None,
    judicial_separation_act: Literal["hma", "sma"] | None = None,
    strict_pwdva: bool = False,
) -> tuple[dict[str, Any], SessionState]:
    """Run one unified turn. Returns (result, new_state).

    Result keys are a superset of ``assess_v7``'s (lang, script, in_scope,
    kept_ids, kept_statutory_ids, applied_principles, court_live,
    escalation_kinds, gated_out, dispositions, prose, ...) plus the v7.1
    additions: ``candidates_before_gate`` (genuine pre-gate set),
    ``gated_out_layer_a`` / ``gated_out_stage2``, ``turn_id``,
    ``pending_clarifications``, ``override_log`` (this turn's entries) and
    ``vocab_profile``.

    A host may opt into a potential judicial-separation route for the
    selected marriage statute. The host confirms applicability before
    presenting provisions and prose to the user.
    Strict PWDVA intake uses explicit, turn-scoped monetary-relief blockers.
    """
    if vocab_profile not in VOCAB_PROFILES:
        raise ValueError(f"Unknown vocab_profile {vocab_profile!r}; expected one of {VOCAB_PROFILES}")
    if judicial_separation_act not in (None, "hma", "sma"):
        raise ValueError("judicial_separation_act must be hma, sma, or None")
    t0 = perf_counter()
    if state is None:
        state = new_session(session_id or f"laya-v71-{uuid.uuid4().hex[:12]}")
    turn_id = len(state.turns) + 1
    override_log_before = len(state.override_log)

    extracted = _extract(
        question, locale=locale, mode=mode, device=device,
        kannada_strategy=kannada_strategy, strict_pwdva=strict_pwdva,
    )
    turn = TurnRecord(
        turn_id=turn_id,
        raw_text=question,
        lang=str(extracted.get("lang", "en")),
        script=str(extracted.get("script", "latin")),
        extracted_facts={
            k: v for k, v in (extracted.get("facts") or {}).items()
            if isinstance(v, FactEvidence)
        },
        extracted_issues={
            k: v for k, v in (extracted.get("issues") or {}).items()
            if isinstance(v, IssueEvidence)
        },
        confirmations=dict(confirmations or {}),
    )
    # Carry the extractor's negated_issues into the session store as denied
    # IssueEvidence (active_issues is the single source of truth; the plain
    # set itself is re-attached only in the Stage 2 facts dict, below).
    negated_seed = set(extracted.get("negated_issues") or set())
    for name in negated_seed:
        if name not in turn.extracted_issues:
            turn.extracted_issues[name] = IssueEvidence(
                issue=name, intent="denied", source="model", confidence=1.0,
                turn=turn_id,
            )
    open_markers = set((extracted.get("facts") or {}).get("open_fact_markers") or set())

    pwdva_basis = turn.extracted_facts.pop("pwdva_monetary_basis_blocked", None)
    state = resolve_turn_state(state, turn, confirmations)
    if strict_pwdva and pwdva_basis is not None:
        # Only qualified affirmative or negative evidence emits this key.
        # The latest such turn revises the gate. Silence leaves it untouched.
        pwdva_basis.turn = turn_id
        turn.extracted_facts[pwdva_basis.key] = pwdva_basis
        state.active_facts[pwdva_basis.key] = pwdva_basis
        state.fact_history.setdefault(pwdva_basis.key, []).append(pwdva_basis)

    separation = None
    if judicial_separation_act is not None and _judicial_separation_intent is not None:
        separation = state.active_issues.get("judicial_separation")
        amended_intent = _judicial_separation_intent(question)
        divorce = turn.extracted_issues.get("divorce")
        divorce_requested = divorce is not None and divorce.intent == "requested"
        if amended_intent == "requested" and divorce_requested:
            amended_intent = "uncertain"
        elif amended_intent is None and divorce_requested and separation is not None:
            amended_intent = "denied"
        source = "user_text"
        declared = turn.confirmations.get("judicial_separation_requested")
        if amended_intent is None and separation is not None and separation.intent == "uncertain":
            if isinstance(declared, bool):
                amended_intent = "requested" if declared else "denied"
                source = "user_confirmation"
        if amended_intent is not None:
            # Petition preference can change. A new express choice supersedes
            # a previously confirmed preference for the same matter.
            separation = _issue_for("judicial_separation", amended_intent, source, 1.0, turn_id)
            turn.extracted_issues["judicial_separation"] = separation
            state.active_issues["judicial_separation"] = separation

    facts = stage2_facts(state, open_fact_markers=open_markers)
    if not strict_pwdva:
        facts.pop("pwdva_monetary_basis_blocked", None)
    issues = dict(state.active_issues)
    if separation is not None:
        facts["judicial_separation_act"] = judicial_separation_act
        facts["judicial_separation_only"] = separation.intent != "denied"

    # Maintenance sub-routes profile: maintenance-only intake first.
    maintenance_routes: dict[str, Any] | None = None
    if vocab_profile == "maintenance_sub_routes":
        maintenance_routes = _maintenance_sub_routes(question)
        if maintenance_routes is not None and not issues:
            # Pure maintenance intake answered it; still record the turn.
            result: dict[str, Any] = {
                "lang": turn.lang,
                "script": turn.script,
                "extractor_mode": str(extracted.get("extractor_mode", "evidence")),
                "in_scope": True,
                "kept_ids": [r["id"] for r in maintenance_routes.get("routes", [])],
                "kept_statutory_ids": [r["id"] for r in maintenance_routes.get("routes", [])],
                "applied_principles": [],
                "custody_companions": [],
                "court_live": [],
                "court_source": "maintenance-intake",
                "escalations_typed": [],
                "escalation_kinds": [],
                "gated_out": [],
                "gated_out_layer_a": [],
                "gated_out_stage2": [],
                "candidates_before_gate": [r["id"] for r in maintenance_routes.get("routes", [])],
                "dispositions": {},
                "maintenance_routes": maintenance_routes.get("routes", []),
                "maintenance_questions": maintenance_routes.get("questions", []),
                "vocab_profile": vocab_profile,
                "turn_id": turn_id,
                "pending_clarifications": list(state.pending_clarifications),
                "override_log": list(state.override_log[override_log_before:]),
                "error": extracted.get("error"),
            }
            result["latency_s"] = round(perf_counter() - t0, 4)
            return result, state

    # Full pipeline: Graph v4.1 engine, else Stage 2 fallback.
    engine_used = "graph_engine_v41"
    try:
        graph = load_graph_v41()
        decision = _graph_execute(graph, issues, facts, vocab_profile=vocab_profile)  # type: ignore[misc]
    except Exception as exc:
        engine_used = f"stage2_fallback ({exc})"
        if _evaluate_stage2_v7 is None:
            raise RuntimeError("No Stage 2 available: graph engine and evaluate_stage2_v7 both failed") from exc
        decision = _evaluate_stage2_v7(
            issues, facts, custody_vocab=PROFILE_CUSTODY_VOCAB[vocab_profile]
        )
        decision = dict(decision)
        decision["candidates_before_gate"] = sorted((decision.get("dispositions") or {}).keys())
        decision["gated_out_layer_a"] = []
        decision["gated_out_stage2"] = list(decision.get("gated_out", []) or [])
        decision["vocab_profile"] = vocab_profile

    kept_ids = apply_vocab_profile(list(decision.get("kept_ids", []) or []), vocab_profile)

    result = {
        "lang": turn.lang,
        "script": turn.script,
        "extractor_mode": str(extracted.get("extractor_mode", "evidence")),
        "in_scope": bool(decision.get("in_scope", True)),
        "kept_ids": kept_ids,
        "kept_statutory_ids": list(decision.get("kept_statutory_ids", []) or []),
        "applied_principles": list(decision.get("applied_principles", []) or []),
        "custody_companions": list(decision.get("custody_companions", []) or []),
        "court_live": list(decision.get("court_live", []) or []),
        "court_source": str(decision.get("court_source", "")),
        "escalations_typed": list(decision.get("escalations_typed", []) or []),
        "escalation_kinds": list(decision.get("escalation_kinds", []) or []),
        "gated_out": list(decision.get("gated_out", []) or []),
        "gated_out_layer_a": list(decision.get("gated_out_layer_a", []) or []),
        "gated_out_stage2": list(decision.get("gated_out_stage2", []) or []),
        "candidates_before_gate": list(decision.get("candidates_before_gate", kept_ids)),
        "dispositions": dict(decision.get("dispositions", {}) or {}),
        "vocab_profile": vocab_profile,
        "engine": engine_used,
        "turn_id": turn_id,
        "pending_clarifications": list(state.pending_clarifications),
        "override_log": list(state.override_log[override_log_before:]),
        "error": extracted.get("error"),
    }

    # Recompute pending questions so confirmed or no-longer-relevant facts drop
    # off the list. Keep conflict prompts only while the conflict is active.
    state.pending_clarifications = [
        q for q in state.pending_clarifications
        if (ev := state.active_facts.get(q["fact_key"])) is not None
        and ev.status == "conflicting"
    ][:2] if result["in_scope"] else []
    clarifications = []
    if result["in_scope"] and len(state.pending_clarifications) < 2:
        if separation is not None and separation.intent == "uncertain":
            clarifications.append({
                "fact_key": "judicial_separation_requested",
                "question": "Are you asking for a court-ordered separation while staying married?",
            })
        state.pending_clarifications.extend(clarifications)
        ranked = rank_clarifications(
            state, facts, issues,
            max_questions=2 - len(state.pending_clarifications), kept_ids=kept_ids,
        )
        state.pending_clarifications.extend(ranked)
        clarifications.extend(ranked)
    result["pending_clarifications"] = list(state.pending_clarifications)
    result["clarifying_questions"] = clarifications

    if with_prose and _render_prose is not None and _prose_forbidden_check is not None:
        prose_out = _render_prose(result, decision.get("facts", facts))
        fp_hits, q_flags = _prose_forbidden_check(
            prose_out["prose"], result["kept_ids"], result["gated_out"],
            decision.get("facts", facts),
        )
        result["prose"] = prose_out["prose"]
        result["prose_fp_hits"] = fp_hits
        result["prose_quality_flags"] = q_flags
        result["prose_render_ms"] = prose_out.get("prose_render_ms")
        if prose_out.get("status") == "error":
            result["error"] = "prose_validation_error"

    result["latency_s"] = round(perf_counter() - t0, 4)
    return result, state


def assess_turns(
    questions: list[str],
    *,
    confirmations_list: list[dict[str, Any] | None] | None = None,
    vocab_profile: str = "v4_legacy_18",
    session_id: str | None = None,
    **kwargs: Any,
) -> tuple[list[dict[str, Any]], SessionState]:
    """Run a multi-turn dialogue through one shared SessionState."""
    state: SessionState | None = None
    if session_id is not None:
        state = new_session(session_id)
    results: list[dict[str, Any]] = []
    for idx, question in enumerate(questions):
        confs = confirmations_list[idx] if confirmations_list else None
        result, state = assess_turn(
            state, question, confirmations=confs,
            vocab_profile=vocab_profile, **kwargs,
        )
        results.append(result)
    return results, state
