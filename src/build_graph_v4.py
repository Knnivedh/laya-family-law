"""Deterministic builder for LAYA Decision Graph v4 from frozen Graph v3.

Preserves all 34 section IDs cleanly while fixing all v2/v3 structural defects,
normalizing related_sections & laya_question metadata, and adding the 18 new
Stage 1 / Stage 2 routing nodes and +20 net edges specified in
docs/v4-decision-graph-architecture.md.

Expected output counts: 34 sections / 66 nodes / 99 edges.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parent.parent
V3_PATH = REPO_ROOT / "graph" / "laya-crpc-bns-section-decision-tree-v3.json"
V4_PATH = REPO_ROOT / "graph" / "laya-crpc-bns-section-decision-tree-v4.json"
V3_EXPECTED_LF_SHA256 = "67bf2b04ca946f7c7fa3062068e01ce051fbce8f4d740c281afe6fff841c34a5"

LABEL_TO_ID = {
    "HMA_26": "hma-26",
    "GWA_1890": "gwa-1890",
    "HMGA_1956_s6": "hmga-1956-s6",
    "WELFARE_PRINCIPLE": "welfare-principle",
    "HMGA-6": "hmga-1956-s6",
    "hmga-6": "hmga-1956-s6",
    "BNSS S.144": "bnss-144",
    "BNS S.316": "bns-316",
    "HMA S.24": "hma-24",
    "HMA S.25": "hma-25",
    "HMA S.26": "hma-26",
    "HMA S.27": "hma-27",
    "HMA S.13": "hma-13",
    "HMA S.13B": "hma-13b",
    "HMA S.9": "hma-9",
    "PWDVA S.17": "pwdva-17",
    "PWDVA S.18": "pwdva-18",
    "PWDVA S.19": "pwdva-19",
    "PWDVA S.20": "pwdva-20",
    "PWDVA S.22": "pwdva-22",
    "GUARDIANS AND WARDS ACT 1890": "gwa-1890",
}


def canonical_lf_sha256(path: Path) -> str:
    raw = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(raw).hexdigest()


def map_label_to_ids(label: str, valid_ids: set[str]) -> list[str]:
    clean = label.strip()
    if clean in valid_ids:
        return [clean]
    if clean in LABEL_TO_ID:
        return [LABEL_TO_ID[clean]]
    upper = clean.upper().replace("  ", " ")
    if upper in LABEL_TO_ID:
        return [LABEL_TO_ID[upper]]

    # Match prefixes like "HMA s.24 / HMA s.25 (...)" or "PWDVA s.18 — description"
    head = re.split(r"\s*(?:\(|—|–)\s*", clean, maxsplit=1)[0].strip()
    parts = [p.strip() for p in head.split("/") if p.strip()]
    out: list[str] = []
    for part in parts:
        u = part.upper().replace("  ", " ")
        if part in valid_ids:
            out.append(part)
        elif part in LABEL_TO_ID:
            out.append(LABEL_TO_ID[part])
        elif u in LABEL_TO_ID:
            out.append(LABEL_TO_ID[u])
        else:
            # Regex fallbacks for Statute s.N
            m = re.match(r"^(HMA|PWDVA|BNSS|BNS)\s*s\.?\s*(13B|13|24|25|26|27|17|18|19|20|22|9|144|316)\b", part, re.I)
            if m:
                cand = f"{m.group(1).lower()}-{m.group(2).lower()}"
                if cand in valid_ids:
                    out.append(cand)
                    continue
            raise ValueError(f"Unmapped related_sections label: {label!r} (part={part!r})")
    return out


def normalize_related_sections(sections: list[dict], valid_ids: set[str]) -> None:
    for sec in sections:
        new_rel: list[dict[str, str]] = []
        for item in sec.get("related_sections", []):
            if isinstance(item, dict):
                raw_sid = item.get("section_id") or item.get("section")
                if not raw_sid:
                    raise ValueError(f"Section {sec['id']} has empty dict in related_sections: {item!r}")
                ids = map_label_to_ids(raw_sid, valid_ids)
                rel_desc = item.get("relationship", f"Related provision: {raw_sid}")
                for sid in ids:
                    new_rel.append({"section_id": sid, "relationship": rel_desc})
            elif isinstance(item, str):
                parts = re.split(r"\s*(?:\(|—|–)\s*", item.strip(), maxsplit=1)
                head = parts[0].strip()
                if len(parts) > 1:
                    rel_desc = parts[1].rstrip(")").strip()
                else:
                    rel_desc = f"Related provision ({item.strip()})"
                for sid in map_label_to_ids(head, valid_ids):
                    new_rel.append({"section_id": sid, "relationship": rel_desc})
            else:
                raise TypeError(f"Unexpected related_sections element type in {sec['id']}: {type(item)}")
        sec["related_sections"] = new_rel


def normalize_laya_questions(sections: list[dict]) -> None:
    upgrades = {
        "hma-13": {
            "type": "choice",
            "question": "Has the user expressly asked for contested divorce (without mutual consent)?",
            "options": [
                "Contested divorce expressly asked (HMA s.13)",
                "Mutual-consent divorce agreed by both spouses (route to HMA s.13B)",
                "No divorce asked / judicial separation or restitution only (gate closed)",
            ],
        },
        "hma-13b": {
            "type": "choice",
            "question": "Have both spouses agreed to end the marriage by mutual consent?",
            "options": [
                "Mutual-consent divorce asked and both spouses agree (HMA s.13B)",
                "Contested divorce only (route to HMA s.13)",
                "No divorce asked (gate closed)",
            ],
        },
        "births-deaths-act-1969": {
            "type": "choice",
            "question": "Is the user asking how to obtain, register, or correct a birth certificate?",
            "options": [
                "Yes — birth certificate registration or correction before the Registrar of Births and Deaths",
                "No — unrelated issue",
            ],
        },
    }
    for sec in sections:
        if isinstance(sec.get("laya_question"), str):
            sid = sec["id"]
            if sid in upgrades:
                sec["laya_question"] = upgrades[sid]
            else:
                sec["laya_question"] = {
                    "type": "choice",
                    "question": sec["laya_question"],
                    "options": ["Yes", "No"],
                }


def update_section_descriptions(sections: list[dict]) -> None:
    by_id = {s["id"]: s for s in sections}
    by_id["bnss-144"]["exclusions"] = (
        str(by_id["bnss-144"].get("exclusions", ""))
        + " [v4 rule]: A husband cannot claim self-maintenance from his wife under BNSS s.144 "
        "(use HMA s.24 pendente lite if HMA proceeding pending), though a father may claim on behalf of a dependent child."
    ).strip()
    for pid in ("pwdva-17", "pwdva-18", "pwdva-19", "pwdva-20", "pwdva-22"):
        if pid in by_id:
            by_id[pid]["exclusions"] = (
                str(by_id[pid].get("exclusions", ""))
                + " [v4 statutory eligibility]: Applies strictly to an 'aggrieved person' (woman) "
                "in a domestic relationship under PWDVA s.2(a) — never to male adult claimants or non-domestic disputes."
            ).strip()
    by_id["hma-27"]["when_used"] = (
        "Strictly when an HMA proceeding is pending or definitely being filed: covers disposal of jointly owned "
        "matrimonial property (flat, house, plot, car) as well as wedding-time Stridhan presented jointly at/about marriage. "
        "Dropped under D1-A/D2 when no HMA proceeding is pending or being filed."
    )
    by_id["hma-25"]["when_used"] = (
        "At or after passing of an HMA decree, or when one-time / lump-sum permanent alimony settlement "
        "is sought in connection with dissolution/decree."
    )


def build_v4_graph() -> dict:
    v3_sha = canonical_lf_sha256(V3_PATH)
    assert v3_sha == V3_EXPECTED_LF_SHA256, (
        f"Graph v3 LF SHA-256 mismatch: expected {V3_EXPECTED_LF_SHA256}, got {v3_sha}"
    )
    g = copy.deepcopy(json.loads(V3_PATH.read_text(encoding="utf-8")))
    valid_ids = {s["id"] for s in g["sections"]}

    # Section normalizations (DEF-4..DEF-8)
    normalize_related_sections(g["sections"], valid_ids)
    normalize_laya_questions(g["sections"])
    update_section_descriptions(g["sections"])

    # Update procedure:divorce-gate node to 4-way v4 fork
    for n in g["nodes"]:
        if n["node_id"] == "procedure:divorce-gate":
            n["options"] = [
                "No divorce asked (gate closed; check restitution HMA s.9 if spouse separated)",
                "Contested divorce expressly asked -> HMA s.13",
                "Mutual-consent divorce asked and both spouses agree -> HMA s.13B",
                "Judicial separation only / ambiguous -> clarify before opening divorce gate",
            ]

    # Add the +18 new v4 nodes (48 + 18 = 66)
    new_nodes = [
        {
            "node_id": "stage1:escalate-clarify",
            "lane": "stage1",
            "type": "leaf",
            "section_set": [],
            "question": "No family-law issue can be picked with confidence — clarify facts with the user before classifying.",
            "options": ["Clarify missing facts"],
        },
        {
            "node_id": "stage2:escalate-demand-first",
            "lane": "stage2",
            "type": "leaf",
            "section_set": ["bns-316"],
            "question": "Stridhan held but no demand yet made — keep BNS s.316 provisionally with demand-first escalation (make written demand first, then re-evaluate).",
            "options": ["Make written demand first"],
        },
        {
            "node_id": "matrimonial:hma-9-choice",
            "lane": "matrimonial",
            "type": "choice",
            "section_set": ["hma-9"],
            "question": "Has spouse withdrawn without reasonable excuse and claimant seeks restitution rather than divorce?",
            "options": [
                "yes — spouse left / refuses to return, and I want them back (HMA s.9)",
                "no — divorce or separation wanted instead",
            ],
        },
        {
            "node_id": "violence:pwdva-22-choice",
            "lane": "violence",
            "type": "choice",
            "section_set": ["pwdva-22"],
            "question": "Are injuries, medical costs, or emotional torture compensation claimed from domestic violence?",
            "options": [
                "yes — injuries / medical costs / mental torture from domestic violence, compensation wanted (PWDVA s.22)",
                "no — protection/residence order only",
            ],
        },
        {
            "node_id": "stage2:hma-13-leaf",
            "lane": "stage2",
            "type": "section_set",
            "section_set": ["hma-13"],
            "question": "Contested dissolution of Hindu marriage under HMA s.13.",
            "options": [],
        },
        {
            "node_id": "stage2:hma-13b-leaf",
            "lane": "stage2",
            "type": "section_set",
            "section_set": ["hma-13b"],
            "question": "Mutual-consent dissolution of Hindu marriage under HMA s.13B (both spouses agree).",
            "options": [],
        },
        {
            "node_id": "stridhan:joint-property-check",
            "lane": "stridhan",
            "type": "choice",
            "section_set": ["hma-27"],
            "question": "Is division of jointly acquired matrimonial property (flat/house/plot/car) claimed in a pending or definitely being-filed HMA proceeding?",
            "options": [
                "yes — pending/being-filed HMA proceeding with joint property division (HMA s.27)",
                "no — no pending HMA proceeding or not joint property",
            ],
        },
        {
            "node_id": "stage2:hma-27-leaf",
            "lane": "stage2",
            "type": "section_set",
            "section_set": ["hma-27"],
            "question": "HMA s.27 joint matrimonial property / Stridhan disposal inside pending/being-filed HMA proceeding.",
            "options": [],
        },
        {
            "node_id": "stage2:not-joint-property-leaf",
            "lane": "stage2",
            "type": "leaf",
            "section_set": [],
            "question": "No pending/being-filed HMA proceeding or sole property — civil handoff outside HMA s.27.",
            "options": [],
        },
        {
            "node_id": "maintenance:claimant-applicability-gate",
            "lane": "maintenance",
            "type": "choice",
            "section_set": ["bnss-144", "pwdva-20", "hma-24", "hma-25"],
            "question": "Check claimant statutory standing (wife, dependent child, aged parent, or husband in HMA proceeding).",
            "options": [
                "female spouse or minor child subsistence (standard route)",
                "husband claiming self-maintenance (HMA s.24/25 only if HMA pending)",
                "aged parent or child-only father claim (BNSS s.144 only, no PWDVA s.20)",
                "outside family-law maintenance scope",
            ],
        },
        {
            "node_id": "maintenance:post-order-enforcement",
            "lane": "maintenance",
            "type": "choice",
            "section_set": ["bnss-144", "hma-24", "hma-25"],
            "question": "Is the query about arrears, variation, or lump-sum settlement of a maintenance order?",
            "options": [
                "Magistrate order arrears / shortfall / schedule / payer reduction (BNSS s.144 only)",
                "Pending HMA s.24 interim order duration/query (HMA s.24 only)",
                "Lump-sum settlement / post-decree permanent alimony (HMA s.25)",
            ],
        },
        {
            "node_id": "stage2:hma-24-only-leaf",
            "lane": "stage2",
            "type": "section_set",
            "section_set": ["hma-24"],
            "question": "HMA s.24 interim maintenance only (male spouse or pure pending-HMA interim request).",
            "options": [],
        },
        {
            "node_id": "stage2:hma-25-settlement-leaf",
            "lane": "stage2",
            "type": "section_set",
            "section_set": ["hma-25"],
            "question": "HMA s.25 permanent alimony or lump-sum settlement.",
            "options": [],
        },
        {
            "node_id": "stage2:pwdva-17-19-residence-leaf",
            "lane": "stage2",
            "type": "section_set",
            "section_set": ["pwdva-17", "pwdva-19"],
            "question": "Shared-household residence right and residence order (PWDVA ss.17 & 19) without s.18 protection order.",
            "options": [],
        },
        {
            "node_id": "stage2:pwdva-18-protection-leaf",
            "lane": "stage2",
            "type": "section_set",
            "section_set": ["pwdva-18"],
            "question": "Protection order against domestic violence, threats, or coercive harm (PWDVA s.18) independently of residence.",
            "options": [],
        },
        {
            "node_id": "stage2:male-claimant-dv-handoff",
            "lane": "stage2",
            "type": "leaf",
            "section_set": [],
            "question": "Male DV complainant: PWDVA s.2(a) does not cover adult male claimants; escalate to general criminal/legal advice.",
            "options": [],
        },
        {
            "node_id": "stage2:out-of-scope-handoff",
            "lane": "stage2",
            "type": "leaf",
            "section_set": [],
            "question": "Out-of-scope civil/landlord/workplace/property dispute — empty sections, human lawyer handoff.",
            "options": [],
        },
        {
            "node_id": "stage2:no-dispute-empty",
            "lane": "stage2",
            "type": "leaf",
            "section_set": [],
            "question": "Undisputed / no actionable court relief needed — empty sections, no escalation.",
            "options": [],
        },
    ]
    existing_ids = {n["node_id"] for n in g["nodes"]}
    for nn in new_nodes:
        assert nn["node_id"] not in existing_ids, f"Duplicate node_id: {nn['node_id']}"
        g["nodes"].append(nn)

    # Fix v3 dangling/legacy edges: indices 57, 67, 74, 75, 77, 78
    edges = g["edges"]
    # Replace edge 57 (root -> maintenance-root) with root -> claimant-applicability-gate
    assert edges[57]["to"] == "maintenance:maintenance-root"
    edges[57]["to"] = "maintenance:claimant-applicability-gate"
    # Fix DEF-1..DEF-3 dangling edges
    assert edges[67]["to"] == "escalate_clarify"
    edges[67]["to"] = "stage1:escalate-clarify"
    assert edges[74]["to"] == "bns-316"
    edges[74]["to"] = "stridhan:bns-316-leaf"
    assert edges[75]["to"] == "escalate_demand_first"
    edges[75]["to"] = "stage2:escalate-demand-first"
    # Redirect 77 and 78 through interactive choice nodes
    assert edges[77]["to"] == "stage2:hma-9-leaf"
    edges[77]["to"] = "matrimonial:hma-9-choice"
    assert edges[78]["to"] == "stage2:pwdva-22-leaf"
    edges[78]["to"] = "violence:pwdva-22-choice"

    # Add +20 net edges (79 + 20 = 99)
    new_edges = [
        {"from": "matrimonial:hma-9-choice", "to": "stage2:hma-9-leaf", "condition": "restitution sought and divorce_asked=False", "lane": "matrimonial"},
        {"from": "violence:pwdva-22-choice", "to": "stage2:pwdva-22-leaf", "condition": "female DV injury/compensation asked (claimant_sex != male)", "lane": "violence"},
        {"from": "procedure:divorce-gate", "to": "stage2:hma-13-leaf", "condition": "divorce_asked and not mutual_consent", "lane": "stage2"},
        {"from": "procedure:divorce-gate", "to": "stage2:hma-13b-leaf", "condition": "divorce_asked and mutual_consent", "lane": "stage2"},
        {"from": "root:issue-classification", "to": "stridhan:joint-property-check", "condition": "joint matrimonial property division asked", "lane": "stridhan"},
        {"from": "stridhan:joint-property-check", "to": "stage2:hma-27-leaf", "condition": "proceeding_pending_hma or being_filed", "lane": "stage2"},
        {"from": "stridhan:joint-property-check", "to": "stage2:not-joint-property-leaf", "condition": "no pending/being-filed HMA proceeding", "lane": "stage2"},
        {"from": "maintenance:claimant-applicability-gate", "to": "maintenance:maintenance-root", "condition": "eligible female claimant or minor-child maintenance", "lane": "maintenance"},
        {"from": "maintenance:claimant-applicability-gate", "to": "stage2:hma-24-only-leaf", "condition": "male spouse in pending/being-filed HMA or pure HMA 24 interim", "lane": "maintenance"},
        {"from": "maintenance:claimant-applicability-gate", "to": "maintenance:bnss-144-leaf", "condition": "parent claimant or father claiming child-only maintenance", "lane": "maintenance"},
        {"from": "maintenance:claimant-applicability-gate", "to": "stage2:out-of-scope-handoff", "condition": "male self-maintenance with no HMA proceeding / non-family", "lane": "maintenance"},
        {"from": "maintenance:maintenance-root", "to": "maintenance:post-order-enforcement", "condition": "existing order arrears, variation, or lump-sum settlement", "lane": "maintenance"},
        {"from": "maintenance:post-order-enforcement", "to": "maintenance:bnss-144-leaf", "condition": "Magistrate order arrears / shortfall / fixed-date / reduction", "lane": "stage2"},
        {"from": "maintenance:post-order-enforcement", "to": "stage2:hma-24-only-leaf", "condition": "existing HMA s.24 interim order duration query", "lane": "stage2"},
        {"from": "maintenance:post-order-enforcement", "to": "stage2:hma-25-settlement-leaf", "condition": "HMA s.25 post-decree or lump-sum permanent alimony", "lane": "stage2"},
        {"from": "stage2:pwdva-per-section-gate", "to": "stage2:pwdva-17-19-residence-leaf", "condition": "residence_claim and not coercive eviction/violence", "lane": "stage2"},
        {"from": "stage2:pwdva-per-section-gate", "to": "stage2:pwdva-18-protection-leaf", "condition": "violence/coercive eviction without residence order ask", "lane": "stage2"},
        {"from": "stage2:pwdva-per-section-gate", "to": "stage2:male-claimant-dv-handoff", "condition": "claimant_sex == male or not domestic_relationship", "lane": "stage2"},
        {"from": "stage1:confidence-gate", "to": "stage2:out-of-scope-handoff", "condition": "out-of-scope civil/property/employer matter", "lane": "stage2"},
        {"from": "stage1:confidence-gate", "to": "stage2:no-dispute-empty", "condition": "no actionable dispute (no_dispute_empty=True)", "lane": "stage2"},
    ]
    edges.extend(new_edges)

    g["version"] = "v4"
    g["date"] = "2026-11-27"
    g["purpose"] = (
        "LAYA Indian family-law decision graph v4: repairs all v2/v3 dangling edges and "
        "non-canonical references, canonicalizes laya_question objects, and adds complete "
        "Stage 2 routing for HMA 9, PWDVA 22, HMA 13B, HMA 25 settlements, HMA 27 joint property, "
        "claimant-sex/role gates, post-order enforcement, and independent PWDVA 17/18/19 routing."
    )
    g["counts"] = {
        "sections": len(g["sections"]),
        "nodes": len(g["nodes"]),
        "edges": len(g["edges"]),
    }

    assert (len(g["sections"]), len(g["nodes"]), len(g["edges"])) == (34, 66, 99), g["counts"]
    node_ids = {n["node_id"] for n in g["nodes"]}
    assert all(e["from"] in node_ids and e["to"] in node_ids for e in g["edges"])
    assert all(
        rs["section_id"] in valid_ids
        for s in g["sections"]
        for rs in s.get("related_sections", [])
    )
    assert all(set(n.get("section_set", [])) <= valid_ids for n in g["nodes"])
    return g


def main() -> None:
    g = build_v4_graph()
    text = json.dumps(g, indent=2, ensure_ascii=False) + "\n"
    V4_PATH.write_bytes(text.encode("utf-8"))
    sha = hashlib.sha256(V4_PATH.read_bytes()).hexdigest()
    print(
        f"Built {V4_PATH}: {len(g['sections'])} sections / "
        f"{len(g['nodes'])} nodes / {len(g['edges'])} edges | LF SHA-256={sha}"
    )


if __name__ == "__main__":
    main()
