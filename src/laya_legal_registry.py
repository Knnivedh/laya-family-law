"""Laya legal registry — deterministic statutory crosswalk + citation gate.

V71-P4-1 / V71-P4-2 (docs/10x_plane.md §4). Lane 07 deliverable.

Pure Python, no torch, no GPU, no network. The unified runtime
(Lane 05, src/laya_runtime.py) calls this module; this module never
imports the graph, the extractor, or prose.

Two hard rules, enforced here and nowhere else by convention:
  1. NEVER silently emit bnss-144-3 / bnss-146 on an unverified
     CrPC 125 or pre-1-July-2024 order. Pre-2024 orders stay under
     their old statute via the BNSS s.531 savings clause until a
     fact proves otherwise.
  2. NEVER cite a case in consumer prose unless
     legal/verified_authorities.json says status == "verified_primary"
     AND the section is in kept_ids AND the use is inside an
     allowed_scope. Everything else is unverified, full stop.

Run the CPU self-test with:  python3 src/laya_legal_registry.py
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import date

# ---------------------------------------------------------------------------
# Commencement boundary
# ---------------------------------------------------------------------------
# BNS 2023, BNSS 2023 and BSA 2023 commenced on 1 July 2024.
# BNSS commencement is verified in-repo via S.O. 848(E) at
# src/laya_family_evidence.py:117-122. The exact Gazette notifications
# for BNS & BSA are to be verified during implementation (plan §4.1);
# the shared 1 July 2024 date is the plan's stated boundary and is
# NOT re-derived here from a Gazette this lane read.
COMMENCEMENT_DATE = date(2024, 7, 1)
COMMENCEMENT_NOTE = (
    "BNS/BNSS/BSA commenced 1 July 2024 (BNSS via S.O. 848(E); "
    "verify exact Gazette notifications for BNS & BSA during "
    "implementation — plan §4.1)."
)
SAVINGS_CLAUSE = "BNSS s.531 (savings clause)"

# ---------------------------------------------------------------------------
# Statutory crosswalk (deterministic table)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CrosswalkEntry:
    """One old-statute <-> new-statute pair."""
    old_code: str          # e.g. "crpc_125"
    old_label: str         # e.g. "CrPC s.125"
    new_code: str          # e.g. "bnss_144"
    new_label: str         # e.g. "BNSS s.144"
    # "verified" = pair stated in plan §4.1; "provisional" = derived
    # sub-route, needs a BNSS-text check before production use.
    status: str = "verified"
    # Governing rule for orders/applications straddling the boundary.
    transition_rule: str = ""
    # Sub-route codes that must NEVER be emitted on an old-statute
    # or pre-commencement order (enforcement / variation routes).
    never_emit_on_old_order: tuple[str, ...] = ()

# Plan §4.1 pairs (verbatim scope — nothing added as "verified").
CROSSWALK: tuple[CrosswalkEntry, ...] = (
    CrosswalkEntry(
        old_code="crpc_125",
        old_label="CrPC s.125",
        new_code="bnss_144",
        new_label="BNSS s.144",
        status="verified",
        transition_rule=(
            "New maintenance applications filed on/after 1 July 2024 use "
            "BNSS s.144. Pre-1-July-2024 pending applications/orders retain "
            "CrPC s.125/127 governance under BNSS s.531 savings clause."
        ),
        never_emit_on_old_order=("bnss_144_3", "bnss_146"),
    ),
    CrosswalkEntry(
        old_code="ipc_406",
        old_label="IPC s.406",
        new_code="bns_316_2",
        new_label="BNS s.316(2)",
        status="verified",
        transition_rule=(
            "Use BNS s.316 for post-1-July-2024 retention/sale of Stridhan. "
            "Flag an IPC s.406 transition note if entrustment/FIR predates "
            "1 July 2024."
        ),
    ),
    CrosswalkEntry(
        old_code="iea_65b",
        old_label="Indian Evidence Act s.65B",
        new_code="bsa_63",
        new_label="BSA s.63",
        status="verified",
        transition_rule=(
            "Electronic-evidence certificate route for WhatsApp messages, "
            "bank transfers, audio/video threats, or UPI proofs in "
            "doc-evidence / doc-stridhan-list-proof checklists."
        ),
    ),
)

# IPC s.498A <-> BNS s.85 is EXCLUDED, not mapped. It is currently
# excluded from the frozen 34-section graph per
# docs/test-report-v2-layman.md:37. It stays in
# unverified_excluded / human-lawyer criminal escalation until
# explicitly verified AND added to a v5 graph. Never hallucinate
# BNS s.85 into kept_ids.
EXCLUDED_TRANSITIONS: tuple[dict[str, str], ...] = (
    {
        "old_code": "ipc_498a",
        "old_label": "IPC s.498A",
        "new_code": "bns_85",
        "new_label": "BNS s.85 (cruelty by husband or relatives)",
        "status": "unverified_excluded",
        "reason": (
            "Excluded from the frozen 34-section graph "
            "(docs/test-report-v2-layman.md:37). Keep in human-lawyer "
            "criminal escalation until explicitly verified and added "
            "to a v5 graph; never emit into kept_ids."
        ),
    },
)

# Sub-route notes: BNSS s.144(3) (enforcement) and s.146 (alteration/
# variation) are the maintenance sub-routes exposed by the unified
# runtime (plan §2.2, maintenance_sub_routes). Their old-statute
# counterparts are CrPC s.125(3) and s.127. These two rows are
# PROVISIONAL — the plan does not list them as verified pairs, so
# they carry a verification step and must not be treated as verified
# until checked against the BNSS text.
SUB_ROUTE_NOTES: tuple[CrosswalkEntry, ...] = (
    CrosswalkEntry(
        old_code="crpc_125_3",
        old_label="CrPC s.125(3) (enforcement)",
        new_code="bnss_144_3",
        new_label="BNSS s.144(3) (enforcement)",
        status="provisional",
        transition_rule=(
            "PROVISIONAL — verify against BNSS text before production "
            "use. Enforcement of a pre-1-July-2024 CrPC s.125 order "
            "stays under CrPC s.125(3) / BNSS s.531; never emit "
            "bnss-144-3 on an unverified CrPC 125 order."
        ),
        never_emit_on_old_order=("bnss_144_3",),
    ),
    CrosswalkEntry(
        old_code="crpc_127",
        old_label="CrPC s.127 (alteration)",
        new_code="bnss_146",
        new_label="BNSS s.146 (alteration/variation)",
        status="provisional",
        transition_rule=(
            "PROVISIONAL — verify against BNSS text before production "
            "use. Variation of a pre-1-July-2024 order stays under "
            "CrPC s.127 / BNSS s.531; never emit bnss-146 on an "
            "unverified CrPC 125 order."
        ),
        never_emit_on_old_order=("bnss_146",),
    ),
)

_BY_CODE: dict[str, CrosswalkEntry] = {}
for _e in list(CROSSWALK) + list(SUB_ROUTE_NOTES):
    _BY_CODE[_e.old_code] = _e
    _BY_CODE[_e.new_code] = _e
_BY_EXCLUDED: dict[str, dict[str, str]] = {}
for _x in EXCLUDED_TRANSITIONS:
    _BY_EXCLUDED[_x["old_code"]] = _x
    _BY_EXCLUDED[_x["new_code"]] = _x


def lookup_crosswalk(code: str) -> CrosswalkEntry | dict[str, str] | None:
    """Resolve either side of a crosswalk pair (old or new code).

    Returns the CrosswalkEntry, the excluded-transition dict for
    IPC 498A / BNS 85, or None when the code is not in the table.
    Never raises on unknown input — unknown means 'not mapped'.
    """
    code = (code or "").strip().lower()
    if code in _BY_CODE:
        return _BY_CODE[code]
    return _BY_EXCLUDED.get(code)


def is_pre_bnss(d: date | None) -> bool | None:
    """True if `d` is before the 1 July 2024 commencement boundary.

    Returns None when no date is given — unknown is unknown, and
    must never be coerced to post-commencement.
    """
    if d is None:
        return None
    return d < COMMENCEMENT_DATE


# ---------------------------------------------------------------------------
# existing_order_statute fact
# ---------------------------------------------------------------------------
# Canonical fact values (plan §4.1). The unified Stage 0/1 verifier
# must set exactly one of these; "unknown" is a legitimate value.

EXISTING_ORDER_STATUTES = (
    "bnss_144",
    "crpc_125",
    "hma_24",
    "hma_25",
    "unknown",
)

# Fact keys the verifier may set (names follow the existing codebase:
# pre_bnss_order / bnss_order in laya_family_evidence.py; decree /
# proceeding_pending_hma in laya_v7_graph.py). The registry reads
# them; it does not invent them.
_ORDER_FACT_KEYS = (
    "existing_order_statute",  # pass-through when already set + valid
    "pre_bnss_order",
    "bnss_order",
    "existing_order_enforcement",
)


def _is_true(facts: dict, key: str) -> bool:
    v = facts.get(key)
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.strip().lower() in ("true", "yes", "1")
    return bool(v) if v is not None else False


def derive_existing_order_statute(facts: dict | None) -> str:
    """Derive the canonical existing_order_statute fact from Stage 0/1 facts.

    Precedence (first match wins):
      1. facts["existing_order_statute"] if already set to a valid value.
      2. pre_bnss_order True  -> "crpc_125" (old order, s.531 savings).
      3. bnss_order True      -> "bnss_144" (post-commencement order).
      4. HMA decree/order signals are NOT inferred here: an HMA 24
         (interim) vs HMA 25 (permanent) order needs decree +
         proceeding facts the caller must resolve explicitly — see
         resolve_maintenance_section(). Without them: "unknown".
      5. Otherwise -> "unknown". Unknown is never coerced to bnss_144.

    A date alone never decides the statute: a pre-2024 *filing* date
    with no order-type fact still yields "unknown" (the caller must
    ask, not guess). Use is_pre_bnss() for date checks separately.
    """
    facts = facts or {}
    direct = facts.get("existing_order_statute")
    if isinstance(direct, str) and direct.strip().lower() in EXISTING_ORDER_STATUTES:
        return direct.strip().lower()
    if _is_true(facts, "pre_bnss_order"):
        return "crpc_125"
    if _is_true(facts, "bnss_order"):
        return "bnss_144"
    return "unknown"


def resolve_maintenance_section(
    facts: dict | None,
    *,
    order_date: date | None = None,
    existing_order_statute: str | None = None,
) -> dict[str, str | None]:
    """Resolve which maintenance section governs, given order facts.

    Returns {"section": <kept section id or None>, "statute": <fact>,
    "rule": <why>}. Section is None (not a guessed bnss-144) whenever
    the statute is unknown or the order is a pre-BNSS CrPC 125 order
    being enforced/varied — the caller must then ask, or route to the
    human-lawyer / clarification path, instead of emitting
    bnss-144-3 / bnss-146.

    Rules:
      - existing order under crpc_125 + enforcement/variation asked
        -> section None, rule "s531_savings" (stays CrPC 125/127).
      - existing order under crpc_125 + fresh support asked
        -> "bnss_144" for the NEW application only (old order untouched).
      - existing order under bnss_144 -> "bnss_144" (and sub-routes
        bnss-144-3 / bnss-146 only when the caller explicitly asks
        enforcement/variation — this function never emits them alone).
      - existing order under hma_24 / hma_25 -> that HMA section.
      - unknown statute -> section None, rule "unknown_statute_ask".
    """
    facts = facts or {}
    statute = (existing_order_statute or derive_existing_order_statute(facts)).lower()
    enforcement = _is_true(facts, "existing_order_enforcement")
    fresh = _is_true(facts, "new_support") or _is_true(facts, "maintenance_asked")

    if statute == "crpc_125":
        if enforcement and not fresh:
            return {
                "section": None,
                "statute": statute,
                "rule": "s531_savings: pre-BNSS CrPC 125 order stays under "
                "CrPC 125/127 (BNSS s.531); do not emit bnss-144-3/bnss-146.",
            }
        return {
            "section": "bnss_144",
            "statute": statute,
            "rule": "fresh application under BNSS s.144; pre-existing "
            "CrPC 125 order itself stays under s.531.",
        }
    if statute == "bnss_144":
        return {
            "section": "bnss_144",
            "statute": statute,
            "rule": "post-commencement BNSS s.144 order governs; "
            "bnss-144-3/bnss-146 only on explicit enforcement/variation ask.",
        }
    if statute in ("hma_24", "hma_25"):
        return {
            "section": statute,
            "statute": statute,
            "rule": "HMA order governs (interim s.24 / permanent s.25).",
        }
    # unknown — plus a date check that can only narrow, never decide.
    if order_date is not None and is_pre_bnss(order_date):
        return {
            "section": None,
            "statute": "unknown",
            "rule": "unknown_statute_ask: order predates 1 July 2024 but "
            "order type is unproven — ask, do not assume CrPC 125.",
        }
    return {
        "section": None,
        "statute": "unknown",
        "rule": "unknown_statute_ask: no order-statute fact proven — "
        "ask, do not emit bnss-144-3/bnss-146.",
    }


# ---------------------------------------------------------------------------
# Citation gate (reads legal/verified_authorities.json)
# ---------------------------------------------------------------------------

_DEFAULT_REGISTRY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "legal",
    "verified_authorities.json",
)

_registry_cache: dict[str, dict] = {}


def load_authorities(path: str | None = None) -> dict:
    """Load the verified-authorities registry (cached per path)."""
    p = path or _DEFAULT_REGISTRY_PATH
    if p not in _registry_cache:
        with open(p, "r", encoding="utf-8") as fh:
            _registry_cache[p] = json.load(fh)
    return _registry_cache[p]


def check_citation_allowed(
    authority_id: str,
    section_id: str,
    scope: str,
    path: str | None = None,
) -> dict[str, bool | str]:
    """Gate for any case citation the runtime/prose wants to emit.

    Allowed ONLY when all three hold:
      status == "verified_primary",
      section_id is listed in the authority's graph_sections, and
      scope is in allowed_scopes.
    Anything else -> {"allowed": False, ...} with the reason. There
    is no partial-credit path: unverified stays unverified.
    """
    try:
        data = load_authorities(path)
    except (OSError, json.JSONDecodeError) as exc:
        return {"allowed": False, "reason": f"registry unreadable: {exc}"}
    for auth in data.get("authorities", []):
        if auth.get("id") == authority_id:
            if auth.get("status") != "verified_primary":
                return {
                    "allowed": False,
                    "reason": f"status is {auth.get('status')!r}, not "
                    "'verified_primary'",
                }
            if section_id not in (auth.get("graph_sections") or []):
                return {
                    "allowed": False,
                    "reason": f"section {section_id!r} not in "
                    "graph_sections for this authority",
                }
            if scope not in (auth.get("allowed_scopes") or []):
                return {
                    "allowed": False,
                    "reason": f"scope {scope!r} not in allowed_scopes",
                }
            return {"allowed": True, "reason": "verified_primary + scope match"}
    return {"allowed": False, "reason": f"unknown authority id {authority_id!r}"}


def verified_citations_for_sections(
    kept_ids: list[str] | set[str],
    scope: str,
    path: str | None = None,
) -> list[dict[str, str]]:
    """All verified-primary citations usable for these kept sections + scope.

    Today this returns at most Sukhdev Singh (hma-24/hma-25, nullity
    scopes). An empty list is the normal, correct answer for every
    other section — prose must then cite nothing.
    """
    data = load_authorities(path)
    kept = set(kept_ids or [])
    out: list[dict[str, str]] = []
    for auth in data.get("authorities", []):
        if auth.get("status") != "verified_primary":
            continue
        if not (kept & set(auth.get("graph_sections") or [])):
            continue
        if scope not in (auth.get("allowed_scopes") or []):
            continue
        out.append(
            {
                "id": auth["id"],
                "case": auth["case"],
                "citation": (auth.get("citations") or [""])[0],
                "scope": scope,
            }
        )
    return out


# ---------------------------------------------------------------------------
# CPU self-test (no torch, no network, no test banks)
# ---------------------------------------------------------------------------

def _self_test() -> int:
    checks: list[tuple[str, bool]] = []

    def check(name: str, cond: bool) -> None:
        checks.append((name, bool(cond)))

    # Crosswalk round-trips (both directions).
    for code, want in (
        ("crpc_125", "bnss_144"), ("bnss_144", "crpc_125"),
        ("ipc_406", "bns_316_2"), ("bns_316_2", "ipc_406"),
        ("iea_65b", "bsa_63"), ("bsa_63", "iea_65b"),
    ):
        e = lookup_crosswalk(code)
        other = want
        got = e.new_code if getattr(e, "old_code", None) == code else getattr(e, "old_code", None)
        check(f"crosswalk {code} -> {want}", got == other)

    # IPC 498A / BNS 85 is excluded, never mapped.
    x = lookup_crosswalk("ipc_498a")
    check("ipc_498a excluded", isinstance(x, dict) and x.get("status") == "unverified_excluded")
    check("bns_85 excluded", isinstance(lookup_crosswalk("bns_85"), dict))
    check("unknown code -> None", lookup_crosswalk("ipc_999") is None)

    # Commencement boundary.
    check("30 Jun 2024 is pre-BNSS", is_pre_bnss(date(2024, 6, 30)) is True)
    check("1 Jul 2024 is NOT pre-BNSS", is_pre_bnss(date(2024, 7, 1)) is False)
    check("no date -> None", is_pre_bnss(None) is None)

    # existing_order_statute derivation.
    check("pre_bnss_order -> crpc_125",
          derive_existing_order_statute({"pre_bnss_order": True}) == "crpc_125")
    check("bnss_order -> bnss_144",
          derive_existing_order_statute({"bnss_order": True}) == "bnss_144")
    check("empty facts -> unknown",
          derive_existing_order_statute({}) == "unknown")
    check("date alone never decides statute",
          derive_existing_order_statute({"order_date": "2023-05-01"}) == "unknown")
    check("direct valid pass-through",
          derive_existing_order_statute({"existing_order_statute": "hma_25"}) == "hma_25")
    check("direct invalid -> unknown",
          derive_existing_order_statute({"existing_order_statute": "bns_85"}) == "unknown")
    check("pre_bnss beats bnss_order (savings wins)",
          derive_existing_order_statute(
              {"pre_bnss_order": True, "bnss_order": True}) == "crpc_125")

    # Maintenance resolution: never emit 144-3/146 on an old order.
    r = resolve_maintenance_section({"pre_bnss_order": True,
                                     "existing_order_enforcement": True})
    check("old-order enforcement -> section None, s531",
          r["section"] is None and "s531" in r["rule"])
    r = resolve_maintenance_section({"bnss_order": True})
    check("bnss order -> bnss_144", r["section"] == "bnss_144")
    r = resolve_maintenance_section({})
    check("unknown statute -> section None",
          r["section"] is None and r["statute"] == "unknown")
    r = resolve_maintenance_section({}, order_date=date(2023, 5, 1))
    check("pre-2024 date + unknown type -> still None",
          r["section"] is None)

    # Citation gate (reads the real registry file).
    g = check_citation_allowed("sukhdev-singh-v-sukhbir-kaur-2025",
                               "hma-25", "hma-25_nullity_decree")
    check("Sukhdev allowed for hma-25 nullity decree", g["allowed"] is True)
    g = check_citation_allowed("sukhdev-singh-v-sukhbir-kaur-2025",
                               "hma-25", "stridhan")
    check("Sukhdev blocked for stridhan scope", g["allowed"] is False)
    g = check_citation_allowed("sukhdev-singh-v-sukhbir-kaur-2025",
                               "bns-316", "hma-25_nullity_decree")
    check("Sukhdev blocked for wrong section", g["allowed"] is False)
    g = check_citation_allowed("rajnesh-v-neha-2020",
                               "bnss-144", "maintenance-quantum-only")
    check("Rajnesh blocked (unverified)", g["allowed"] is False)
    g = check_citation_allowed("balkrishna-ramchandra-kadam-v-sangeeta-balkrishna-kadam-1997",
                               "hma-27", "hma-27-ancillary")
    check("Balkrishna blocked (unverified)", g["allowed"] is False)
    g = check_citation_allowed("no-such-authority", "hma-25", "x")
    check("unknown authority blocked", g["allowed"] is False)
    c = verified_citations_for_sections(["hma-25", "bnss-144"], "hma-25_nullity_decree")
    check("verified list returns Sukhdev only for hma-25",
          len(c) == 1 and c[0]["id"] == "sukhdev-singh-v-sukhbir-kaur-2025")
    c = verified_citations_for_sections(["bns-316"], "hma-25_nullity_decree")
    check("verified list empty for bns-316", c == [])

    failed = [n for n, ok in checks if not ok]
    print(f"laya_legal_registry self-test: {len(checks) - len(failed)}/{len(checks)} passed")
    for name, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'} {name}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_self_test())
