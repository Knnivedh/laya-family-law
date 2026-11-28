"""Deterministic Template-Locked Prose Renderer + Automated Fp=0 Verifier (Lane 4 v2).

Zero model calls, zero question-text input, Fp = 0 by construction.
Covers:
  - All original 16-set & sealed sections + brutal-230 Graph v3/v4 sections
    (bnss-144, pwdva-20, hma-24, hma-25, gwa-1890, hmga-1956-s6, welfare-principle,
     hma-26, hma-27, bns-316, pwdva-17, pwdva-18, pwdva-19, pwdva-22,
     hma-13, hma-13b, hma-9, births-deaths-act-1969)
  - D1-A / D2 HMA-27 rule: NEVER cites HMA s.27 unless 'hma-27' is in kept_ids
  - C8 role reversals (claimant_sex='male' vs 'female')
  - All 9 typed escalation kinds (quantum, court, demand, recovery, custody,
    residence, safety, procedure, fact)
  - Strict automated verifier checking frozen Forbidden Items 1-9 + Additions A-F.
"""
import re
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

TEMPLATE_VERSION = "v2.0-d1a-brutal"

KNOWN_SECTIONS = frozenset({
    "bnss-144", "pwdva-20", "hma-24", "hma-25",
    "gwa-1890", "hmga-1956-s6", "welfare-principle", "hma-26",
    "hma-27", "bns-316",
    "pwdva-17", "pwdva-18", "pwdva-19", "pwdva-22",
    "hma-13", "hma-13b", "hma-9", "hma-10", "sma-23",
    "births-deaths-act-1969",
})

COURT_FRAGMENTS = {
    "Family Court": "the Family Court",
    "Magistrate": "the Magistrate",
    "Judicial Magistrate First Class": "the Magistrate",
    "Registrar": "the Registrar of Births and Deaths",
    "Registrar of Births and Deaths": "the Registrar of Births and Deaths",
    "District Registrar": "the District Registrar",
}

INTRO_LINE = (
    "Based on what you have said, the following applies to your question. "
    "This is general information, not legal advice, and a lawyer or the court "
    "will look at your full facts before deciding anything."
)

CLOSING_LINE = (
    "This answer is general information based only on the sections identified "
    "for your question. It is not legal advice for your full situation."
)

OUT_OF_SCOPE_LINE = (
    "This question is outside the family-law matters this system covers. "
    "It does not say anything about your rights in this matter. "
    "A human adviser will need to look at it."
)


def _join_clauses(parts: Sequence[str]) -> str:
    return " ".join(p.strip() for p in parts if p and p.strip())


def _format_court_line(court_live: Sequence[str], court_source: Optional[str]) -> str:
    if court_source in ("fallback-escalate", "out-of-scope"):
        return ""
    frags: List[str] = []
    for c in court_live or []:
        if c.startswith("ESCALATE") or c == "none":
            continue
        frag = COURT_FRAGMENTS.get(c)
        if frag and frag not in frags:
            frags.append(frag)
    if not frags:
        return ""
    if len(frags) == 1:
        joined = frags[0]
    elif len(frags) == 2:
        joined = f"{frags[0]} and {frags[1]}"
    else:
        joined = ", ".join(frags[:-1]) + f", and {frags[-1]}"
    return f"You would approach {joined}."


def _render_maintenance(kept: set, facts: Dict[str, Any]) -> str:
    if not (kept & {"bnss-144", "pwdva-20", "hma-24", "hma-25"}):
        return ""
    male = facts.get("claimant_sex") == "male"
    is_parent = facts.get("claimant_role") == "parent"
    child = bool(facts.get("child_fact"))
    school_fees = bool(facts.get("school_fees_fact"))
    parts: List[str] = []

    if kept & {"bnss-144", "pwdva-20"}:
        if is_parent:
            if "bnss-144" in kept:
                parts.append(
                    "A parent who is unable to maintain themselves can seek monthly maintenance "
                    "from an adult child who has sufficient means under "
                    "Section 144 of the Bharatiya Nagarik Suraksha Sanhita, 2023."
                )
        elif male:
            # Under BNSS s.144, a husband cannot claim for himself, only for a dependent child.
            if child:
                parts.append("You can ask for monthly maintenance for your child.")
            else:
                parts.append("Monthly maintenance under general statutory rules depends on dependency and the applicable matrimonial proceeding.")
            if "bnss-144" in kept:
                parts.append(
                    "Under Section 144 of the Bharatiya Nagarik Suraksha Sanhita, 2023, "
                    "maintenance can be claimed from a parent who has sufficient means for a child's support."
                )
        else:
            if child:
                parts.append("You can ask for monthly maintenance for yourself and for your child.")
            else:
                parts.append("You can ask for monthly maintenance for yourself.")
            if "bnss-144" in kept:
                parts.append(
                    "The law allows a wife to claim maintenance from her husband under "
                    "Section 144 of the Bharatiya Nagarik Suraksha Sanhita, 2023."
                )
            if "pwdva-20" in kept:
                parts.append(
                    "You can also claim monetary relief under Section 20 of the "
                    "Protection of Women from Domestic Violence Act, 2005."
                )

    if "hma-24" in kept:
        if male:
            parts.append(
                "Because your case under the Hindu Marriage Act, 1955 is already going on, "
                "either spouse with insufficient independent income can ask the Family Court for "
                "interim maintenance while that case is pending, under Section 24 of the Hindu Marriage Act, 1955."
            )
        else:
            parts.append(
                "Because your case under the Hindu Marriage Act, 1955 is already going on, "
                "you can also ask the Family Court for interim maintenance while that case is pending, "
                "under Section 24 of the Hindu Marriage Act, 1955."
            )
    if "hma-25" in kept:
        parts.append(
            "At the time of passing a decree or at any time subsequent thereto, permanent alimony "
            "or lump-sum maintenance can be sought by either spouse under Section 25 of the Hindu Marriage Act, 1955."
        )

    payer = "the respondent's income" if is_parent else ("your spouse's income" if male else "your husband's income")
    school_clause = " and your child's school fees" if (child and school_fees) else ""
    parts.append(
        f"The monthly amount cannot be fixed from the information given. "
        f"It will depend on {payer} and your needs{school_clause}, and it will be decided by the court. "
        f"No amount is stated here because the amount is not decided by this system."
    )
    return _join_clauses(parts)


def _render_custody(kept: set, facts: Dict[str, Any]) -> str:
    if not (kept & {"gwa-1890", "hmga-1956-s6", "welfare-principle", "hma-26"}):
        return ""
    parts = [
        "The question of who your child stays with will be decided keeping the welfare of the child first."
    ]
    if "gwa-1890" in kept:
        parts.append("The Guardians and Wards Act, 1890 is the law that applies to guardianship.")
    if "hmga-1956-s6" in kept:
        parts.append("Section 6 of the Hindu Minority and Guardianship Act, 1956 is also relevant to guardianship of a Hindu child.")
    if "hma-26" in kept:
        is_pending = bool(facts.get("proceeding_pending_hma", facts.get("proceeding_pending")))
        if is_pending:
            parts.append(
                "Because your case under the Hindu Marriage Act, 1955 is already going on, "
                "the Family Court can also pass orders about the child under Section 26 of the Hindu Marriage Act, 1955 "
                "while that case is pending."
            )
        else:
            parts.append(
                "Where a proceeding under the Hindu Marriage Act, 1955 is being filed alongside this claim, "
                "the Family Court can pass orders about the child under Section 26 of the Hindu Marriage Act, 1955."
            )
    return _join_clauses(parts)


def _render_stridhan_and_property(kept: set, facts: Dict[str, Any]) -> str:
    """D1-A / D2 safe Stridhan and joint matrimonial property renderer.
    NEVER cites Section 27 of HMA unless 'hma-27' is explicitly in kept!
    """
    has_27 = "hma-27" in kept
    has_316 = "bns-316" in kept
    if not (has_27 or has_316):
        return ""
    parts: List[str] = []
    joint_only = has_27 and not has_316 and bool(facts.get("joint_property_claim", facts.get("joint_property_fact")))
    sold = bool(facts.get("stridhan_sold_or_mortgaged", facts.get("stridhan_sold")))

    if joint_only:
        parts.append(
            "Property jointly owned by both spouses in connection with the marriage can be addressed "
            "inside the pending or being-filed matrimonial proceeding under Section 27 of the Hindu Marriage Act, 1955."
        )
        return _join_clauses(parts)

    parts.append("The gold, cash, and gifts given to you at your marriage belong to you.")
    if has_27:
        if sold:
            parts.append(
                "Because a Hindu Marriage Act proceeding is pending or being filed, you can ask for their value back "
                "under Section 27 of the Hindu Marriage Act, 1955, since they have been sold."
            )
        else:
            parts.append(
                "Because a Hindu Marriage Act proceeding is pending or being filed, you can ask for their return "
                "under Section 27 of the Hindu Marriage Act, 1955."
            )
    else:
        # D1-A / D2: hma-27 not kept (no HMA proceeding pending or being filed).
        # Never cite HMA s.27 here; describe civil recovery in Family Court without an unkept statute number.
        if sold:
            parts.append(
                "When no Hindu Marriage Act case is pending or being filed, you can seek civil recovery of their value "
                "through a property claim before the Family Court."
            )
        else:
            parts.append(
                "When no Hindu Marriage Act case is pending or being filed, you can seek civil return of your property "
                "through a property claim before the Family Court."
            )
    if has_316:
        parts.append(
            "Keeping back or misappropriating a wife's property can also be an offence under "
            "Section 316 of the Bharatiya Nyaya Sanhita, 2023."
        )
    return _join_clauses(parts)


def _render_residence_and_dv(kept: set, facts: Dict[str, Any]) -> str:
    if not (kept & {"pwdva-17", "pwdva-18", "pwdva-19", "pwdva-22"}):
        return ""
    parts: List[str] = []
    if kept & {"pwdva-17", "pwdva-19"}:
        parts.append("You have the right to stay in the shared household.")
    if "pwdva-17" in kept:
        parts.append(
            "Under Section 17 of the Protection of Women from Domestic Violence Act, 2005, "
            "you have the right to reside in the shared household."
        )
    if "pwdva-19" in kept:
        parts.append(
            "Under Section 19 of the Protection of Women from Domestic Violence Act, 2005, "
            "the court can pass a residence order about the shared household."
        )
    if "pwdva-18" in kept:
        parts.append(
            "Under Section 18 of the Protection of Women from Domestic Violence Act, 2005, "
            "the court can pass a protection order stopping violence, threats, and harassment at home."
        )
    if "pwdva-22" in kept:
        parts.append(
            "Under Section 22 of the Protection of Women from Domestic Violence Act, 2005, "
            "the court can order compensation for injuries, including mental torture and emotional distress, "
            "caused by acts of domestic violence."
        )
    return _join_clauses(parts)


def _render_judicial_separation(kept: set) -> str:
    if "hma-10" in kept:
        section = "Section 10 of the Hindu Marriage Act, 1955"
    elif "sma-23" in kept:
        section = "Section 23 of the Special Marriage Act, 1954"
    else:
        return ""
    return (
        f"{section} provides for judicial separation on specified statutory grounds. "
        "If the court grants a decree, you can live apart while remaining married. "
        "A family-law lawyer can check which grounds may apply to your facts and "
        "whether the petition belongs in the local Family Court or District Court."
    )


def _render_divorce_and_restitution(kept: set, facts: Dict[str, Any]) -> Tuple[str, bool]:
    """Returns (paragraph, needs_failsafe_escalation)."""
    parts: List[str] = []
    failsafe = False

    if "hma-13" in kept:
        pend = bool(facts.get("proceeding_pending_hma", facts.get("proceeding_pending")))
        if facts.get("divorce_asked") or pend:
            if pend:
                parts.append(
                    "Your divorce case is already going on. It will be decided under "
                    "Section 13 of the Hindu Marriage Act, 1955, and the Family Court will decide it "
                    "on the facts and evidence in your case."
                )
            else:
                parts.append(
                    "You have asked for a divorce. A divorce can be sought under "
                    "Section 13 of the Hindu Marriage Act, 1955, and the Family Court will decide it "
                    "on the facts and evidence in your case."
                )
        else:
            failsafe = True

    if "hma-13b" in kept:
        # Forbidden #3 guard: 13B strictly requires BOTH divorce_asked AND mutual_consent
        if facts.get("divorce_asked") and facts.get("mutual_consent"):
            parts.append(
                "Because both spouses agree to end the marriage, a mutual-consent divorce petition "
                "can be filed before the Family Court under Section 13B of the Hindu Marriage Act, 1955."
            )
        else:
            failsafe = True

    if "hma-9" in kept:
        parts.append(
            "Where a spouse has withdrawn from the society of the other without reasonable excuse, "
            "a petition for restitution of conjugal rights can be filed before the Family Court under "
            "Section 9 of the Hindu Marriage Act, 1955."
        )

    return _join_clauses(parts), failsafe


def _render_birth_certificate(kept: set) -> str:
    if "births-deaths-act-1969" not in kept:
        return ""
    return (
        "You can get your child's birth certificate from the Registrar of Births and Deaths. "
        "Birth registration is done under the Registration of Births and Deaths Act, 1969. "
        "If the hospital did not give a certificate, you can apply to the Registrar with the "
        "hospital record or other proof of birth, and delayed registration procedures depend on "
        "how long ago the birth occurred."
    )


def _render_escalation_lines(kinds: Sequence[str], kept: set, facts: Dict[str, Any]) -> List[str]:
    male = facts.get("claimant_sex") == "male"
    is_parent = facts.get("claimant_role") == "parent"
    payer = "the respondent's income" if is_parent else ("your spouse's income" if male else "your husband's income")
    whereabouts = "where the respondent lives now" if is_parent else ("where your spouse lives now" if male else "where your husband lives now")
    child = bool(facts.get("child_fact"))
    school_fees = bool(facts.get("school_fees_fact"))
    res_claim = bool(facts.get("residence_claim"))

    kind_set = set(kinds or [])
    order = ["quantum", "court", "demand", "recovery", "custody", "residence", "safety", "procedure", "fact"]
    lines: List[str] = []

    for k in order:
        if k not in kind_set:
            continue
        if k == "quantum":
            sf_part = " and your child's school fees" if (child and school_fees) else ""
            lines.append(
                f"The monthly amount is not fixed here. It will be decided after {payer} "
                f"and your needs{sf_part} are known."
            )
        elif k == "court":
            lines.append(
                "The court cannot be named from the information given. "
                "This question needs to be looked at by a human adviser, who will say which court applies."
            )
        elif k == "demand":
            lines.append(
                "Before going to court, make a written demand for the return of your property and keep a copy of it."
            )
        elif k == "recovery":
            # D1-A / item 7 safe: cite BNS s.316 ONLY if 'bns-316' in kept, HMA s.27 ONLY if 'hma-27' in kept!
            has_316 = "bns-316" in kept
            has_27 = "hma-27" in kept
            if has_316 and has_27:
                lines.append(
                    "Recovering or valuing sold or withheld property requires a human lawyer to assist with "
                    "valuation, a police complaint under Section 316 of the Bharatiya Nyaya Sanhita, 2023, "
                    "and civil recovery under Section 27 of the Hindu Marriage Act, 1955."
                )
            elif has_316:
                lines.append(
                    "Recovering or valuing sold or withheld property requires a human lawyer to assist with "
                    "valuation, a police complaint under Section 316 of the Bharatiya Nyaya Sanhita, 2023, "
                    "and civil recovery before the Family Court."
                )
            elif has_27:
                lines.append(
                    "Recovering or valuing sold or withheld property requires a human lawyer to assist with "
                    "valuation and civil recovery under Section 27 of the Hindu Marriage Act, 1955."
                )
            else:
                lines.append(
                    "Recovering or valuing sold or withheld property requires a human lawyer to assist with "
                    "valuation and civil property recovery."
                )
        elif k == "custody":
            lines.append(
                "Custody depends on the child's welfare and must be decided by the Family Court; "
                "a human lawyer can assist with filing for interim custody and urgent protection if removal is threatened."
            )
        elif k == "residence":
            lines.append(
                "Restoring entry to the shared household requires a Magistrate's residence order; "
                "escalate to a human adviser or lawyer to help file the residence application."
            )
        elif k == "safety":
            lines.append(
                "Because domestic violence or threats are indicated, seek urgent help from a protection officer, "
                "helpline, or lawyer to obtain an immediate protection order."
            )
        elif k == "procedure":
            lines.append(
                "The exact filing steps and timelines depend on case-specific details not stated here; "
                "a human adviser or the relevant authority can guide the formal application."
            )
        elif k == "fact":
            extra = []
            if child and school_fees:
                extra.append("the school-fee amount")
            if res_claim:
                extra.append(whereabouts)
            extra_str = (", " + ", ".join(extra)) if extra else ""
            lines.append(
                f"Some facts are still needed: {payer}, in an estimate or a range{extra_str}. "
                f"Give whatever records you have. If a record is missing, say that it is missing."
            )
    return lines


KNOWN_ESCALATION_KINDS = frozenset({
    "quantum",
    "court",
    "demand",
    "recovery",
    "custody",
    "residence",
    "safety",
    "procedure",
    "fact",
})

INVALID_RECORD_HANDOFF = (
    "This system could not validate the automated classification record cleanly, so no statutory "
    "provisions or court routing are stated here. Please have a human adviser or lawyer review your question."
)


def _normalize_prose_facts(raw_facts: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Project typed FactEvidence/tri-state strings to plain native bool/str values.

    Guarantees strings like 'unknown' or FactEvidence(status='unknown') NEVER act truthy.
    """
    out: Dict[str, Any] = {}
    for k, v in (raw_facts or {}).items():
        if hasattr(v, "status") and hasattr(v, "value"):
            st = getattr(v, "status")
            inner = getattr(v, "value")
            if st == "supported":
                out[k] = True if inner is None else inner
            elif st == "denied":
                out[k] = False if inner in (None, True) else inner
            else:
                out[k] = False if k not in {"claimant_sex", "claimant_role"} else "unknown"
        elif isinstance(v, dict) and "status" in v:
            st = v.get("status")
            inner = v.get("value")
            if st == "supported":
                out[k] = True if inner is None else inner
            elif st == "denied":
                out[k] = False if inner in (None, True) else inner
            else:
                out[k] = False if k not in {"claimant_sex", "claimant_role"} else "unknown"
        elif isinstance(v, str) and k not in {"claimant_sex", "claimant_role"}:
            low = v.strip().lower()
            if low in {"true", "yes", "1", "supported"}:
                out[k] = True
            elif low in {"false", "no", "0", "denied", "unknown", "none", "null", "unclear", "conflicting", ""}:
                out[k] = False
            else:
                out[k] = v
        else:
            out[k] = v
    return out


def render_prose(rec: Dict[str, Any], facts: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Render deterministic user-facing prose strictly from kept_ids, court_live,
    escalation_kinds, and structured facts. NEVER reads question text.
    """
    t0 = time.perf_counter()
    facts = _normalize_prose_facts(facts if facts is not None else (rec.get("facts") or {}))
    kept_list = list(rec.get("kept_ids") or [])
    kept = set(kept_list)
    in_scope = bool(rec.get("in_scope", True))
    court_live = list(rec.get("court_live") or [])
    court_source = rec.get("court_source")

    # Derive kinds from escalations_typed (never verbatim internal texts!)
    raw_typed = rec.get("escalations_typed") or []
    kinds = [e["kind"] for e in raw_typed if isinstance(e, dict) and "kind" in e]
    if rec.get("escalation_kinds"):
        for k in rec["escalation_kinds"]:
            if k not in kinds:
                kinds.append(k)

    # Check for unknown section IDs or unknown escalation enums -> fail-safe handoff
    unknown_ids = sorted(kept - KNOWN_SECTIONS)
    unknown_kinds = sorted(k for k in kinds if k not in KNOWN_ESCALATION_KINDS)
    if unknown_ids or unknown_kinds:
        ms = round((time.perf_counter() - t0) * 1000.0, 3)
        return {
            "prose": INVALID_RECORD_HANDOFF,
            "prose_render_ms": ms,
            "prose_template_version": TEMPLATE_VERSION,
            "unknown_ids": unknown_ids,
            "unknown_kinds": unknown_kinds,
            "status": "error",
        }

    # Out-of-scope branch (checked BEFORE kept so stale sections never render on OOS)
    if not in_scope:
        prose = OUT_OF_SCOPE_LINE
        ms = round((time.perf_counter() - t0) * 1000.0, 3)
        return {"prose": prose, "prose_render_ms": ms, "prose_template_version": TEMPLATE_VERSION, "unknown_ids": unknown_ids, "status": "ok"}

    # Empty kept but in scope -> no-dispute informational line OR escalation + closing
    if not kept and in_scope:
        if facts.get("no_dispute_empty") and not kinds:
            prose = (
                "Based on the facts stated, no actionable dispute requiring court intervention is indicated, "
                "so no statutory section is triggered here. If any dispute arises later, consult a lawyer."
            )
            ms = round((time.perf_counter() - t0) * 1000.0, 3)
            return {"prose": prose, "prose_render_ms": ms, "prose_template_version": TEMPLATE_VERSION, "unknown_ids": unknown_ids, "status": "ok"}
        if "court" not in kinds and "procedure" not in kinds:
            kinds.append("court")
        paras = _render_escalation_lines(kinds, kept, facts) + [CLOSING_LINE]
        prose = "\n\n".join(p for p in paras if p)
        ms = round((time.perf_counter() - t0) * 1000.0, 3)
        return {"prose": prose, "prose_render_ms": ms, "prose_template_version": TEMPLATE_VERSION, "unknown_ids": unknown_ids, "status": "ok"}

    separation = _render_judicial_separation(kept)
    paras: List[str] = [(
        "These are potential legal routes. A court decides whether the statutory "
        "requirements are met based on the facts and evidence."
        if separation else INTRO_LINE
    )]

    p_maint = _render_maintenance(kept, facts)
    if p_maint:
        paras.append(p_maint)

    p_cust = _render_custody(kept, facts)
    if p_cust:
        paras.append(p_cust)

    p_strid = _render_stridhan_and_property(kept, facts)
    if p_strid:
        paras.append(p_strid)

    p_res = _render_residence_and_dv(kept, facts)
    if p_res:
        paras.append(p_res)

    if separation:
        paras.append(separation)
    p_div, div_failsafe = _render_divorce_and_restitution(kept, facts)
    if p_div:
        paras.append(p_div)
    if div_failsafe and "court" not in kinds:
        kinds.append("court")

    p_birth = _render_birth_certificate(kept)
    if p_birth:
        paras.append(p_birth)

    c_line = _format_court_line(court_live, court_source)
    if c_line:
        paras.append(c_line)

    paras.extend(_render_escalation_lines(kinds, kept, facts))
    paras.append(CLOSING_LINE)

    prose = "\n\n".join(p for p in paras if p)
    ms = round((time.perf_counter() - t0) * 1000.0, 3)
    return {"prose": prose, "prose_render_ms": ms, "prose_template_version": TEMPLATE_VERSION, "unknown_ids": unknown_ids, "status": "ok"}


# ---------------------------------------------------------------------------
# Automated Verifier: Frozen Forbidden Items 1-9 + Additions A-F
# ---------------------------------------------------------------------------
SECTION_PATTERNS = [
    (r"\bSection 144\b.{0,40}Bharatiya Nagarik Suraksha Sanhita", "bnss-144"),
    (r"\bBNSS\b.{0,10}s\.?\s*144\b", "bnss-144"),
    (r"\bSection 20\b.{0,45}Protection of Women from Domestic Violence Act", "pwdva-20"),
    (r"\bSection 17\b.{0,45}Protection of Women from Domestic Violence Act", "pwdva-17"),
    (r"\bSection 18\b.{0,45}Protection of Women from Domestic Violence Act", "pwdva-18"),
    (r"\bSection 19\b.{0,45}Protection of Women from Domestic Violence Act", "pwdva-19"),
    (r"\bSection 22\b.{0,45}Protection of Women from Domestic Violence Act", "pwdva-22"),
    (r"\bSection 24\b.{0,40}Hindu Marriage Act", "hma-24"),
    (r"\bSection 25\b.{0,40}Hindu Marriage Act", "hma-25"),
    (r"\bSection 26\b.{0,40}Hindu Marriage Act", "hma-26"),
    (r"\bSection 27\b.{0,40}Hindu Marriage Act", "hma-27"),
    (r"\bSection 13\b(?!B).{0,40}Hindu Marriage Act", "hma-13"),
    (r"\bSection 13B\b.{0,40}Hindu Marriage Act", "hma-13b"),
    (r"\bSection 9\b.{0,40}Hindu Marriage Act", "hma-9"),
    (r"\bSection 10\b.{0,40}Hindu Marriage Act", "hma-10"),
    (r"\bSection 23\b.{0,40}Special Marriage Act", "sma-23"),
    (r"\bSection 316\b.{0,40}Bharatiya Nyaya Sanhita", "bns-316"),
    (r"\bBNS\b.{0,10}s\.?\s*316\b", "bns-316"),
    (r"\bSection 6\b.{0,40}Hindu Minority and Guardianship Act", "hmga-1956-s6"),
    (r"\bGuardians and Wards Act, 1890\b", "gwa-1890"),
    (r"\bRegistration of Births and Deaths Act, 1969\b", "births-deaths-act-1969"),
]

AMOUNT_WORDS = (
    r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|"
    r"twelve|fifteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|"
    r"ninety|hundred)\s+(?:thousand|lakh|lakhs|crore|crores)\b"
)


def prose_forbidden_check(
    prose: str,
    kept_ids: Sequence[str],
    dropped_ids: Sequence[Any],
    facts: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Returns (fp_hits, quality_flags).
    fp_hits map strictly to the 9 frozen Fp items (gate §5).
    quality_flags catch structural/template bugs (Additions A-E).
    """
    facts = _normalize_prose_facts(facts)
    hits: List[Dict[str, Any]] = []
    flags: List[Dict[str, Any]] = []
    kept = set(kept_ids or [])
    dropped = {d[0] if isinstance(d, (list, tuple)) else d for d in (dropped_ids or [])}

    # 1+2. Any precedent / case citation
    for pat in (
        r"\b[A-Z][a-z]+ v\. [A-Z][a-z]+\b",
        r"\bRajnesh\b",
        r"\bSatish Chander Ahuja\b",
        r"\bAIR \d{4}\b",
        r"\bSCC\b",
        r"\(\d{4}\) \d+ SCC",
    ):
        if re.search(pat, prose):
            item = 2 if "Satish" in pat else 1
            hits.append({"item": item, "detail": f"precedent/case citation matched {pat!r}"})
            break

    # 3. HMA 13 / 13B in prose without divorce_asked (or pending for 13) / mutual_consent for 13B.
    # Canonical fact is proceeding_pending_hma (legacy proceeding_pending
    # kept as a fallback so old fact dicts still check out).
    if re.search(r"\bSection 13\b(?!B).{0,40}Hindu Marriage Act", prose):
        if (not (facts.get("divorce_asked") or facts.get("proceeding_pending_hma") or facts.get("proceeding_pending"))) or ("hma-13" not in kept):
            hits.append({"item": 3, "detail": "HMA 13 in prose without divorce_asked/pending or not kept"})
    if re.search(r"\bSection 13B\b", prose):
        if not (facts.get("divorce_asked") and facts.get("mutual_consent") and "hma-13b" in kept):
            hits.append({"item": 3, "detail": "HMA 13B in prose without mutual_consent + divorce_asked + kept"})

    # 4. Tenancy / tenant rights label for residence
    if re.search(r"tenancy rights?|tenant rights?", prose, re.I):
        hits.append({"item": 4, "detail": '"tenancy rights" / "tenant rights" in prose'})

    # 5. User asked to pick the court (any '?' or pick-a-court phrasing)
    if "?" in prose:
        hits.append({"item": 5, "detail": "question mark in generated prose"})
    if re.search(
        r"which court (do you|should you|will you|do I)|choose (a|the) court|"
        r"pick (a|the) court|decide which court",
        prose,
        re.I,
    ):
        hits.append({"item": 5, "detail": "prose asks user to pick the court"})

    # 6. Birth certificate under HMA or missing 1969 Act
    if re.search(r"birth certificate", prose, re.I):
        if re.search(
            r"birth certificate.{0,100}Hindu Marriage Act|Hindu Marriage Act.{0,100}birth certificate",
            prose,
            re.I,
        ):
            hits.append({"item": 6, "detail": "birth certificate linked to HMA"})
        if "births-deaths-act-1969" in kept and "Registration of Births and Deaths Act, 1969" not in prose:
            hits.append({"item": 6, "detail": "birth-certificate paragraph missing the 1969 Act"})

    # 7. Cited section not in kept_ids (or explicitly dropped / gated by D2!)
    cited = set()
    for pat, sid in SECTION_PATTERNS:
        if re.search(pat, prose):
            cited.add(sid)
    for sid in sorted(cited - kept):
        hits.append({"item": 7, "detail": f"prose cites {sid} which is not in kept_ids"})
    for sid in sorted(cited & dropped):
        hits.append({"item": 7, "detail": f"prose cites {sid} which Stage 2 dropped"})

    # 8. Maintenance amount stated as a number
    # NOTE (coordinator, Lane 09 flag): [\d,]+ matches a bare comma, so a
    # stray "," false-fired item 8. All four numeric patterns use
    # [\d][\d,]* (must start with a digit), matching Lane 09's fix in
    # laya_prose_kn.py. AMOUNT_WORDS untouched.
    for pat in (
        r"₹\s?[\d][\d,]*",
        r"\bRs\.?\s?[\d][\d,]*",
        r"\brupees\s+[\d][\d,]*",
        r"\b[\d][\d,]*\s*(?:per month|a month|/month|monthly)\b",
        AMOUNT_WORDS,
    ):
        if re.search(pat, prose, re.I):
            hits.append({"item": 8, "detail": f"maintenance amount pattern matched {pat!r}"})
            break

    # 9. Salary slips demanded
    if re.search(r"salary slips?|pay slips?|payslips?", prose, re.I):
        hits.append({"item": 9, "detail": '"salary slips" / "pay slips" appears in prose'})
    if re.search(
        r"(must|need to|have to|should|required|bring|provide|submit|give|produce|attach)"
        r".{0,40}(salary|income proof|income document)",
        prose,
        re.I,
    ):
        hits.append({"item": 9, "detail": "prose demands income proof as an obligation"})

    # --- Structural Quality Additions (A-E) ---
    if "right to stay in the shared household" in prose and not (kept & {"pwdva-17", "pwdva-19"}):
        flags.append({"check": "A-residence-base-without-section", "detail": "residence-right sentence without pwdva-17/19"})
    if not facts.get("child_fact") and re.search(r"\byour child\b", prose):
        flags.append({"check": "B-child-without-fact", "detail": '"your child" in prose with child_fact=False'})
    if not facts.get("school_fees_fact") and re.search(r"school fee", prose):
        flags.append({"check": "B-school-fees-without-fact", "detail": '"school fees" in prose with school_fees_fact=False'})
    if "hma-27" not in kept and re.search(r"Section 27\b|HMA s\.?\s*27\b", prose):
        flags.append({"check": "C-pre-d1a-hma27-leak", "detail": "HMA 27 cited in prose without hma-27 in kept_ids"})
    if facts.get("claimant_sex") == "male" and re.search(r"\ba wife to claim\b|\byour husband's\b", prose, re.I):
        flags.append({"check": "E-claimant-sex-mismatch", "detail": "wife/husband wording used for male claimant"})
    if facts.get("claimant_role") == "parent" and re.search(r"\ba wife to claim\b|\byour husband's\b", prose, re.I):
        flags.append({"check": "E-claimant-role-mismatch", "detail": "wife/husband wording used for parent claimant"})

    return hits, flags
