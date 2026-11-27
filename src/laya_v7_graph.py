"""Executable Decision Graph v4 / Stage 2 legal router for LAYA v7.

Consumes strictly typed Stage 1 evidence (issues + facts). Never reads raw
question strings, item IDs, dataset names, or ground-truth annotations.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .laya_v7_schema import (
    ESCALATION_KINDS,
    FactEvidence,
    IssueEvidence,
    RemedyDisposition,
    fact_value,
    is_denied,
    proved_true,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
GRAPH_V4_PATH = REPO_ROOT / "graph" / "laya-crpc-bns-section-decision-tree-v4.json"
DECLARED_ENTRY_NODES = (
    "root:issue-classification",
    "stage1:confidence-gate",
    "stage1:conversation-context",
    "stage1:kannada-mapping",
)

FAMILY_COURT_SECTIONS = frozenset({
    "hma-9",
    "hma-13",
    "hma-13b",
    "hma-24",
    "hma-25",
    "hma-26",
    "hma-27",
    "gwa-1890",
    "hmga-1956-s6",
    "welfare-principle",
})
MAGISTRATE_SECTIONS = frozenset({
    "bnss-144",
    "pwdva-17",
    "pwdva-18",
    "pwdva-19",
    "pwdva-20",
    "pwdva-22",
    "bns-316",
})
REGISTRAR_SECTIONS = frozenset({"births-deaths-act-1969"})

SECTION_FORUM_AUTHORITY = {
    **{s: ("Family Court", "FCA s.7(1)") for s in FAMILY_COURT_SECTIONS},
    "bnss-144": ("Magistrate", "BNSS s.144 / JMFC (note: FCA s.7(2)(a) where Family Court established)"),
    "bns-316": ("Magistrate", "BNSS Sch. I / BNS s.316 (civil property claim in Family Court FCA s.7 Expl.(c))"),
    **{s: ("Magistrate", "PWDVA s.27 / JMFC") for s in ("pwdva-17", "pwdva-18", "pwdva-19", "pwdva-20", "pwdva-22")},
    "births-deaths-act-1969": ("Registrar", "RBD Act 1969 ss.7-13"),
}


def load_graph_v4() -> dict[str, Any]:
    return json.loads(GRAPH_V4_PATH.read_text(encoding="utf-8"))


def audit_graph_reachability(graph: dict[str, Any] | None = None) -> dict[str, Any]:
    g = graph or load_graph_v4()
    adj: dict[str, list[str]] = {}
    for edge in g["edges"]:
        adj.setdefault(edge["from"], []).append(edge["to"])
    visited: set[str] = set()
    queue = [n for n in DECLARED_ENTRY_NODES if any(node["node_id"] == n for node in g["nodes"])]
    visited.update(queue)
    while queue:
        cur = queue.pop(0)
        for nxt in adj.get(cur, ()):
            if nxt not in visited:
                visited.add(nxt)
                queue.append(nxt)
    all_ids = {n["node_id"] for n in g["nodes"]}
    return {
        "entry_nodes": list(DECLARED_ENTRY_NODES),
        "total_nodes": len(all_ids),
        "reachable_nodes": len(visited),
        "unreachable_nodes": sorted(all_ids - visited),
    }


def layer_a_filter_options(node_id: str, options: list[str], facts: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Zero-Fb pre-generation Layer A filter matching Graph v4 §4.1."""
    kept: list[str] = []
    removed: list[str] = []
    pending_hma = proved_true(facts, "proceeding_pending_hma") or proved_true(facts, "proceeding_pending")
    being_filed = proved_true(facts, "being_filed")
    decree = proved_true(facts, "decree")
    lump_sum = proved_true(facts, "lump_sum_settlement")
    sex = facts.get("claimant_sex", "unknown")
    if isinstance(sex, FactEvidence):
        sex = sex.value or "unknown"
    role = facts.get("claimant_role", "unknown")
    if isinstance(role, FactEvidence):
        role = role.value or "unknown"
    child_only = proved_true(facts, "child_maintenance_only")
    divorce_asked = proved_true(facts, "divorce_asked") and not proved_true(facts, "judicial_separation_only")
    mutual = proved_true(facts, "mutual_consent")
    dom_rel = proved_true(facts, "domestic_relationship", default=True)

    for opt in options:
        low = opt.lower()
        drop_reason = None
        if node_id == "maintenance:maintenance-root":
            if "interim maintenance" in low and not (pending_hma or being_filed):
                drop_reason = "no_pending_or_being_filed_hma"
            elif "permanent alimony" in low and not (decree or (lump_sum and (divorce_asked or pending_hma or being_filed))):
                drop_reason = "no_decree_or_settlement"
            elif sex == "male" and not child_only and (
                "immediate maintenance" in low or "pwdva" in low or "full maintenance" in low
            ):
                drop_reason = "male_self_maintenance_excluded"
            elif (sex == "male" or role == "parent") and "pwdva" in low:
                drop_reason = "pwdva_woman_only_s2a"
        elif node_id == "procedure:divorce-gate":
            if not divorce_asked or "divorce" in (facts.get("negated_issues") or set()):
                if "13" in low:
                    drop_reason = "divorce_not_asked"
            elif mutual and "contested" in low:
                drop_reason = "mutual_consent_exclusive"
            elif not mutual and "mutual" in low:
                drop_reason = "no_mutual_consent"
        elif node_id == "custody:custody_sub_issue_choice":
            if "hma s.26" in low and not (pending_hma or being_filed):
                drop_reason = "no_pending_hma_for_hma26"
            elif "guardians and wards" in low and (pending_hma or being_filed):
                drop_reason = "hma_pending_uses_hma26"
        elif node_id == "matrimonial:hma-9-choice":
            if divorce_asked and "yes" in low:
                drop_reason = "divorce_asked_excludes_restitution"
        elif node_id == "violence:pwdva-22-choice":
            if (sex == "male" or not dom_rel) and "yes" in low:
                drop_reason = "pwdva_22_eligibility_failed"

        if drop_reason:
            removed.append(f"{opt} [{drop_reason}]")
        else:
            kept.append(opt)
    return kept, removed


def court_for_v7(kept_ids: list[str], in_scope: bool) -> tuple[list[str], str]:
    """Deterministic forum derivation from final eligible sections ONLY."""
    kept = set(kept_ids)
    if kept:
        courts: set[str] = set()
        if kept & FAMILY_COURT_SECTIONS:
            courts.add("Family Court")
        if kept & MAGISTRATE_SECTIONS:
            courts.add("Magistrate")
        if kept & REGISTRAR_SECTIONS:
            courts.add("Registrar")
        order = ["Family Court", "Magistrate", "Registrar"]
        return [c for c in order if c in courts], "kept"
    if not in_scope:
        return [], "out-of-scope"
    return [], "fallback-escalate"


def _issue_map(issues: list[IssueEvidence] | dict[str, Any] | set[str]) -> dict[str, IssueEvidence]:
    if isinstance(issues, (set, list, tuple)):
        if issues and isinstance(next(iter(issues)), IssueEvidence):
            return {ie.issue: ie for ie in issues}  # type: ignore[union-attr]
        return {str(name): IssueEvidence(issue=str(name), intent="requested", confidence=1.0) for name in issues}
    out: dict[str, IssueEvidence] = {}
    for k, v in issues.items():
        if isinstance(v, IssueEvidence):
            out[k] = v
        elif isinstance(v, bool):
            out[k] = IssueEvidence(issue=k, intent="requested" if v else "denied", confidence=1.0 if v else 0.0)
        elif isinstance(v, dict):
            out[k] = IssueEvidence(
                issue=k,
                intent=v.get("intent", "requested"),
                source=v.get("source", "input"),
                confidence=float(v.get("confidence", 0.0)),
            )
    return out


def _as_str(facts: dict[str, Any], key: str, default: str = "unknown") -> str:
    val = facts.get(key, default)
    if isinstance(val, FactEvidence):
        return str(val.value or default)
    if isinstance(val, dict) and "value" in val:
        return str(val.get("value") or default)
    return str(val or default)


def _normalize_legacy_facts(raw_facts: dict[str, Any]) -> dict[str, Any]:
    """Accept canonical Graph v4 facts OR legacy 9-key 16-Q facts without leaking strings."""
    f = dict(raw_facts)
    if "proceeding_pending_hma" not in f:
        mag_only = proved_true(f, "magistrate_case_only")
        if mag_only:
            f["proceeding_pending_hma"] = False
        elif "proceeding_pending" in f:
            f["proceeding_pending_hma"] = proved_true(f, "proceeding_pending")
    if "stridhan_claim" not in f and "gold_fact" in f:
        f["stridhan_claim"] = proved_true(f, "gold_fact")
    if "stridhan_held_or_disposed" not in f and proved_true(f, "stridhan_claim"):
        # Unless explicitly safe/undisposed, gold held/sold by husband/in-laws is active
        if proved_true(f, "stridhan_safe_in_own_possession") or proved_true(f, "stridhan_abandoned_or_undisputed"):
            f["stridhan_held_or_disposed"] = False
        else:
            f["stridhan_held_or_disposed"] = True
    if "in_scope" not in f:
        f["in_scope"] = True
    if "domestic_relationship" not in f:
        f["domestic_relationship"] = True
    if "negated_issues" not in f or f["negated_issues"] is None:
        f["negated_issues"] = set()
    else:
        f["negated_issues"] = set(f["negated_issues"])
    if "open_fact_markers" not in f or f["open_fact_markers"] is None:
        f["open_fact_markers"] = set()
    else:
        f["open_fact_markers"] = set(f["open_fact_markers"])
    return f


def _derive_escalations_v7(
    kept: set[str],
    facts: dict[str, Any],
    court_source: str,
    urgent_safety: bool,
) -> list[dict[str, str]]:
    esc: list[dict[str, str]] = []
    lump_sum = proved_true(facts, "lump_sum_settlement")
    custody_risk = proved_true(facts, "child_safety_risk")
    stridhan_sold = proved_true(facts, "stridhan_sold_or_mortgaged") or proved_true(facts, "stridhan_sold")
    stridhan_refused = proved_true(facts, "stridhan_held_by_inlaws_refused")
    demand_made = fact_value(facts, "demand_made", default=None)
    first_demand_never = proved_true(facts, "first_demand_never_made")
    forum_asked = proved_true(facts, "forum_question_asked")
    proc_asked = proved_true(facts, "procedure_how_to_asked")
    existing_order = proved_true(facts, "existing_order_enforcement")
    no_dispute = proved_true(facts, "no_dispute_empty")
    open_markers = set(facts.get("open_fact_markers") or set())

    # Also auto-mark open_fact_markers when canonical facts clearly require fact-specific determination
    if proved_true(facts, "joint_property_claim"):
        open_markers.add("joint_property_claim")
    if stridhan_sold:
        open_markers.add("stridhan_sold_or_mortgaged")

    if (kept & {"bnss-144", "pwdva-20", "hma-24", "hma-25"}) or (
        lump_sum and (proved_true(facts, "divorce_asked") or proved_true(facts, "proceeding_pending_hma"))
    ):
        esc.append({"kind": "quantum", "text": "Monthly or lump-sum maintenance quantum must be fixed by the court."})

    if kept & {"gwa-1890", "hma-26"}:
        esc.append({"kind": "custody", "text": "Custody and child welfare must be decided by the Family Court."})

    if kept & {"pwdva-17", "pwdva-19"}:
        esc.append({"kind": "residence", "text": "Shared-household residence relief requires a Magistrate order under PWDVA."})

    # Safety is ALWAYS independent of statute eligibility and kept counts
    if ("pwdva-18" in kept) or custody_risk or urgent_safety:
        esc.append({"kind": "safety", "text": "Safety risk indicated — escalate urgently for protection and safety help."})

    if "bns-316" in kept:
        esc.append({"kind": "recovery", "text": "Stridhan recovery requires formal valuation and legal assistance."})
        if demand_made is False or first_demand_never:
            esc.append({"kind": "demand", "text": "Make a documented written demand for return of Stridhan before filing."})
    elif first_demand_never and (kept & {"bnss-144", "pwdva-20", "pwdva-17", "pwdva-19"}):
        esc.append({"kind": "demand", "text": "Formal demand / notice has not yet been made."})

    # Procedure escalation
    is_divorce_only = bool(kept) and kept <= {"hma-13", "hma-13b"}
    hyp_or_prop_only = proved_true(facts, "hypothetical_or_joint_prop_fact_only")
    if (
        ("births-deaths-act-1969" in kept)
        or (not kept and not no_dispute)
        or (is_divorce_only and not forum_asked and not hyp_or_prop_only)
        or ("hma-13b" in kept and forum_asked)
        or proc_asked
    ):
        esc.append({"kind": "procedure", "text": "Formal filing or procedural steps require human adviser guidance."})

    # Court escalation (only for forum questions on court remedies, or ambiguous in-scope fallback)
    is_civil_handoff = (
        is_denied(facts, "in_scope")
        or not proved_true(facts, "domestic_relationship", default=True)
        or proved_true(facts, "joint_property_claim")
        or (str(facts.get("claimant_sex") and getattr(facts.get("claimant_sex"), "value", facts.get("claimant_sex")) or "").lower() == "male" and ("pwdva-18" not in kept))
        or proved_true(facts, "stridhan_safe_in_own_possession")
    )
    if (forum_asked and ("births-deaths-act-1969" not in kept) and not existing_order) or (
        court_source == "fallback-escalate" and not no_dispute and not is_civil_handoff and not proved_true(facts, "joint_property_claim")
    ):
        esc.append({"kind": "court", "text": "Confirm the competent forum jurisdiction before filing."})

    if open_markers and not (no_dispute and not kept):
        esc.append({"kind": "fact", "text": "Additional case-specific facts materially affect valuation, proof, or forum."})

    # Deduplicate by kind preserving deterministic order
    seen: set[str] = set()
    ordered_esc: list[dict[str, str]] = []
    by_kind = {item["kind"]: item for item in esc}
    for k in ESCALATION_KINDS:
        if k in by_kind and k not in seen:
            seen.add(k)
            ordered_esc.append(by_kind[k])
    return ordered_esc


def evaluate_stage2_v7(
    issues: list[IssueEvidence] | dict[str, Any] | set[str],
    raw_facts: dict[str, Any],
    *,
    custody_vocab: str = "v3_bundled",
) -> dict[str, Any]:
    """Execute Graph v4 Stage 2 legal routing across all family-law slices.

    Args:
        issues: Detected Stage 1 issues (name -> IssueEvidence / bool).
        raw_facts: Canonical facts dict (strings like 'unknown' are never coerced to True).
        custody_vocab: 'v3_bundled' adds ['hmga-1956-s6', 'welfare-principle'] for Hindu minor custody;
            'statutory_primary' keeps only 'gwa-1890'/'hma-26' in kept_ids while recording companions
            in applied_principles.
    """
    facts = _normalize_legacy_facts(raw_facts)
    imap = _issue_map(issues)

    def _wanted(name: str) -> bool:
        ev = imap.get(name)
        return ev is not None and ev.intent == "requested"

    negated = facts["negated_issues"]
    in_scope = not is_denied(facts, "in_scope")
    dom_rel = proved_true(facts, "domestic_relationship", default=True)
    sex = _as_str(facts, "claimant_sex", "unknown").lower()
    role = _as_str(facts, "claimant_role", "unknown").lower()

    pending_hma = proved_true(facts, "proceeding_pending_hma")
    being_filed = proved_true(facts, "being_filed")
    hma_active = pending_hma or being_filed
    decree = proved_true(facts, "decree")
    lump_sum = proved_true(facts, "lump_sum_settlement")
    divorce_asked = proved_true(facts, "divorce_asked") and not proved_true(facts, "judicial_separation_only")
    mutual_consent = proved_true(facts, "mutual_consent")
    js_only = proved_true(facts, "judicial_separation_only")
    restitution_asked = proved_true(facts, "restitution_asked")
    money_fact = proved_true(facts, "money_fact")
    child_only = proved_true(facts, "child_maintenance_only")
    existing_order = proved_true(facts, "existing_order_enforcement")
    interim_only = proved_true(facts, "interim_only_asked")
    interim_parallel = proved_true(facts, "interim_unpaid_with_joint_or_parallel")
    post_decree_lump = proved_true(facts, "post_decree_lump_sum_enforcement")

    violence = proved_true(facts, "violence")
    urgent_safety = proved_true(facts, "urgent_safety_risk") or violence
    coercive_lockout = proved_true(facts, "coercive_eviction_or_lockout")
    stay_eviction_press = proved_true(facts, "stay_in_house_under_eviction_pressure")
    explicit_res_only = proved_true(facts, "explicit_residence_order_only")
    res_claim = proved_true(facts, "residence_claim")
    dv_comp = proved_true(facts, "dv_injury_comp_asked")

    custody_claim = proved_true(facts, "custody_claim")
    stridhan_claim = proved_true(facts, "stridhan_claim")
    stridhan_held = proved_true(facts, "stridhan_held_or_disposed")
    joint_prop_claim = proved_true(facts, "joint_property_claim")
    birth_cert = proved_true(facts, "birth_cert_asked")
    child_fact = proved_true(facts, "child_fact") or custody_claim or birth_cert or child_only
    minor_child_verified = proved_true(facts, "minor_child", default=True)
    if is_denied(facts, "minor_child"):
        minor_child_verified = False

    dispositions: dict[str, RemedyDisposition] = {}
    kept_stat: list[str] = []
    gated_out: list[str] = []
    applied_principles: list[str] = []

    def _add_disp(sec_id: str, status: str, reason: str, missing: list[str] | None = None, principles: list[str] | None = None) -> None:
        forum, auth = SECTION_FORUM_AUTHORITY.get(sec_id, (None, None))
        dispositions[sec_id] = RemedyDisposition(
            section_id=sec_id,
            status=status,  # type: ignore[arg-type]
            reason_codes=[reason],
            missing_facts=missing or [],
            forum=forum if status == "eligible" else None,
            forum_authority=auth if status == "eligible" else None,
            applied_principles=principles or [],
        )
        if status == "eligible" and sec_id not in kept_stat:
            kept_stat.append(sec_id)

    if not in_scope:
        court_live, court_source = court_for_v7([], False)
        escalations = _derive_escalations_v7(set(), facts, court_source, urgent_safety=urgent_safety)
        return {
            "in_scope": False,
            "kept_ids": [],
            "kept_statutory_ids": [],
            "applied_principles": [],
            "custody_companions": [],
            "gated_out": ["all: out_of_scope"],
            "dispositions": {},
            "court_live": court_live,
            "court_source": court_source,
            "escalations_typed": escalations,
            "escalation_kinds": [e["kind"] for e in escalations],
            "facts": facts,
        }

    # --- 1. Maintenance slice ---
    maint_requested = (
        (_wanted("maintenance") or money_fact or lump_sum or existing_order or proved_true(facts, "interim_asked"))
        and ("maintenance" not in negated)
        and ("maintenance" not in facts.get("denied_issues", set()))
        and not proved_true(facts, "maintenance_negated")
    )
    if maint_requested:
        # Check decree / lump-sum HMA 25 first
        handled_maint = False
        if decree or (lump_sum and (divorce_asked or hma_active)):
            _add_disp("hma-25", "eligible", "decree_or_lump_sum_settlement")
            if lump_sum or post_decree_lump:
                handled_maint = True
            elif decree and money_fact and sex != "male" and minor_child_verified:
                _add_disp("bnss-144", "eligible", "post_decree_ongoing_maintenance")
                handled_maint = True
            elif decree:
                handled_maint = True
        elif lump_sum:
            _add_disp("hma-25", "conditional", "lump_sum_without_decree_or_hma_proceeding", ["hma_decree_or_pending"])
            gated_out.append("hma-25: gated (pre_decree_without_hma)")

        if not handled_maint:
            if role == "parent":
                _add_disp("bnss-144", "eligible", "dependent_parent_bnss144")
                _add_disp("pwdva-20", "inapplicable", "parent_routed_bnss144_only")
            elif sex == "male" and not child_only:
                if hma_active:
                    _add_disp("hma-24", "eligible", "male_spouse_pending_hma_interim")
                else:
                    _add_disp("bnss-144", "inapplicable", "husband_self_claim_excluded_bnss144")
                    _add_disp("pwdva-20", "inapplicable", "pwdva_s2a_woman_only")
                    gated_out.append("maintenance: gated (male spouse self-maintenance outside HMA)")
            elif sex == "male" and child_only:
                if minor_child_verified:
                    _add_disp("bnss-144", "eligible", "father_child_only_bnss144")
                    if pending_hma and proved_true(facts, "interim_asked"):
                        _add_disp("hma-24", "eligible", "pending_hma_interim")
                _add_disp("pwdva-20", "inapplicable", "pwdva_s2a_woman_only")
            elif existing_order:
                if pending_hma and not proved_true(facts, "money_fact_child_or_parallel"):
                    _add_disp("hma-24", "eligible", "existing_hma24_order_duration")
                    if interim_parallel:
                        _add_disp("bnss-144", "eligible", "parallel_bnss144_support")
                else:
                    _add_disp("bnss-144", "eligible", "existing_magistrate_order_enforcement_or_vary")
            else:
                if not minor_child_verified and child_only:
                    _add_disp("bnss-144", "inapplicable", "adult_able_child_ineligible")
                    gated_out.append("bnss-144: gated (adult child)")
                else:
                    if pending_hma or (being_filed and proved_true(facts, "interim_asked")):
                        _add_disp("hma-24", "eligible", "pending_hma_interim")
                        if interim_only:
                            handled_maint = True
                    if not handled_maint and money_fact:
                        _add_disp("bnss-144", "eligible", "subsistence_maintenance_bnss144")
                        if sex != "male" and dom_rel and not child_only:
                            _add_disp("pwdva-20", "eligible", "pwdva_s20_monetary_relief")

    # --- 2. Matrimonial slice (HMA 13, 13B, 9) ---
    if (_wanted("divorce") or divorce_asked) and ("divorce" not in negated) and not js_only:
        if divorce_asked:
            if mutual_consent:
                _add_disp("hma-13b", "eligible", "mutual_consent_divorce")
                _add_disp("hma-13", "inapplicable", "superseded_by_mutual_consent_13b")
            else:
                _add_disp("hma-13", "eligible", "contested_divorce_asked")
                _add_disp("hma-13b", "inapplicable", "no_mutual_consent")
        else:
            _add_disp("hma-13", "conditional", "divorce_not_expressly_asked", ["divorce_asked"])
            gated_out.append("hma-13: gated (divorce not asked)")

    if (_wanted("restitution") or restitution_asked) and not divorce_asked and ("restitution" not in negated):
        _add_disp("hma-9", "eligible", "restitution_of_conjugal_rights")

    # --- 3. Custody slice (HMA 26 vs GWA 1890 + principles) ---
    custody_companions: list[str] = []
    if (_wanted("custody") or custody_claim) and custody_claim and ("custody" not in negated) and not proved_true(facts, "custody_negated"):
        applied_principles.extend(["hmga-1956-s6", "welfare-principle"])
        custody_companions = ["hmga-1956-s6", "welfare-principle"]
        if hma_active:
            _add_disp("hma-26", "eligible", "custody_inside_hma_proceeding", principles=custody_companions)
            _add_disp("gwa-1890", "inapplicable", "superseded_by_hma26_pending")
        else:
            _add_disp("gwa-1890", "eligible", "standalone_guardianship_custody", principles=custody_companions)
            _add_disp("hma-26", "conditional", "no_pending_or_being_filed_hma", ["proceeding_pending_hma"])

    # --- 4. Property & Stridhan slice (BNS 316 vs HMA 27) ---
    if (_wanted("stridhan") or stridhan_claim) and stridhan_claim and ("stridhan" not in negated) and not proved_true(facts, "stridhan_negated"):
        if stridhan_held and dom_rel:
            _add_disp("bns-316", "eligible", "stridhan_withheld_or_disposed_criminal_trust")
        else:
            _add_disp("bns-316", "inapplicable", "stridhan_safe_or_no_domestic_entrustment")

    if (_wanted("joint_property") or joint_prop_claim) and joint_prop_claim and ("stridhan" not in negated):
        if hma_active:
            _add_disp("hma-27", "eligible", "d2_joint_property_in_hma_proceeding")
        else:
            _add_disp("hma-27", "conditional", "d2_no_hma_pending_or_being_filed", ["proceeding_pending_hma"])
            gated_out.append("hma-27: gated (D2) — no HMA proceeding pending or being filed")

    # --- 5. PWDVA Residence, Protection & Compensation (strictly independent!) ---
    pwdva_eligible = (sex != "male") and dom_rel
    if (_wanted("residence") or res_claim) and res_claim and ("residence" not in negated) and not proved_true(facts, "residence_negated"):
        if pwdva_eligible:
            _add_disp("pwdva-17", "eligible", "shared_household_right_pwdva17")
            _add_disp("pwdva-19", "eligible", "residence_order_pwdva19")
        else:
            _add_disp("pwdva-17", "inapplicable", "pwdva_s2a_eligibility_failed")
            _add_disp("pwdva-19", "inapplicable", "pwdva_s2a_eligibility_failed")
            gated_out.append("pwdva-17/19: gated (PWDVA s.2(a) claimant/domestic check)")

    protection_trigger = (violence or coercive_lockout or stay_eviction_press) and not explicit_res_only
    if (_wanted("violence") or protection_trigger) and protection_trigger and ("violence" not in negated) and not proved_true(facts, "violence_negated"):
        if pwdva_eligible:
            _add_disp("pwdva-18", "eligible", "protection_order_independent_pwdva18")
        else:
            _add_disp("pwdva-18", "inapplicable", "pwdva_s2a_eligibility_failed")
            gated_out.append("pwdva-18: gated (PWDVA s.2(a) claimant/domestic check)")

    if (_wanted("dv_compensation") or dv_comp) and violence and dv_comp and ("violence" not in negated):
        if pwdva_eligible:
            _add_disp("pwdva-22", "eligible", "dv_injury_compensation_pwdva22")
        else:
            _add_disp("pwdva-22", "inapplicable", "pwdva_s2a_eligibility_failed")

    # --- 6. Birth Registration ---
    if (_wanted("birth_certificate") or birth_cert) and birth_cert and ("birth_certificate" not in negated):
        _add_disp("births-deaths-act-1969", "eligible", "birth_registration_act_1969")

    # Build final kept_ids respecting custody_vocab policy
    kept_ids = list(kept_stat)
    if custody_vocab == "v3_bundled" and custody_companions:
        for comp in custody_companions:
            if comp not in kept_ids:
                kept_ids.append(comp)
                _add_disp(comp, "eligible", "v3_bundled_custody_companion")

    # Include child_fact projection for Prose v2
    facts["child_fact"] = bool(child_fact)

    court_live, court_source = court_for_v7(kept_ids, in_scope=in_scope)
    escalations = _derive_escalations_v7(set(kept_ids), facts, court_source, urgent_safety=urgent_safety)

    return {
        "in_scope": True,
        "kept_ids": kept_ids,
        "kept_statutory_ids": kept_stat,
        "applied_principles": sorted(set(applied_principles)),
        "custody_companions": custody_companions,
        "gated_out": gated_out,
        "dispositions": {k: v.to_dict() for k, v in dispositions.items()},
        "court_live": court_live,
        "court_source": court_source,
        "escalations_typed": escalations,
        "escalation_kinds": [e["kind"] for e in escalations],
        "facts": facts,
    }
