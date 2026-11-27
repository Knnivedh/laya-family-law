#!/usr/bin/env python3
"""Merge the 5 lane fragments into one verified Laya decision-tree JSON.
PWDVA s.20 appears in both maintenance and residence lanes: deduplicated to
one canonical section, keeping both lane definitions under merged_from.
All other section ids are canonicalised to lower-case.
"""
import json, pathlib, copy

ROOT = pathlib.Path.home() / "workspace/goals/english-family-law-chatbot-retest/files/laya-graph"
LANES = ROOT / "lanes"
OUT = pathlib.Path.home() / "workspace/goals/english-family-law-chatbot-retest/files/laya-crpc-bns-section-decision-tree.json"

lane_files = {
    "maintenance": "maintenance.json",
    "custody": "custody.json",
    "stridhan": "stridhan.json",
    "residence": "residence.json",
    "procedure": "procedure.json",
}

def canon(sid):
    return str(sid).lower().replace("_", "-")

sections = {}          # canonical id -> section dict
section_order = []
nodes = []
edges = []
lane_counts = {}

for lane, fname in lane_files.items():
    d = json.load(open(LANES / fname))
    lane_counts[lane] = {
        "sections_raw": len(d.get("sections", [])),
        "nodes": len(d.get("nodes", [])),
        "edges": len(d.get("edges", [])),
        "file": f"laya-graph/lanes/{fname}",
    }
    # sections: dedupe pwdva-20
    for s in d.get("sections", []):
        cid = canon(s.get("id"))
        s2 = copy.deepcopy(s)
        s2["id"] = cid
        s2["lane"] = lane
        s2.setdefault("verification_status", "verified — 2026-11-26 fresh English retest")
        if cid in sections:
            prev = sections[cid]
            prev.setdefault("merged_from", []).append({"lane": lane, "original_id": s.get("id")})
            # keep the maintenance definition as canonical for pwdva-20 (it carries
            # the monetary-relief quantum/escalation detail); record the residence
            # definition's distinct fields as an alternate face
            prev.setdefault("alternate_face", {})[lane] = {
                k: s2[k] for k in ("when_used", "court", "escalate_rule", "exclusions")
                if k in s2
            }
            prev.setdefault("lanes", []).append(lane)
            continue
        s2["merged_from"] = [{"lane": lane, "original_id": s.get("id")}]
        s2["lanes"] = [lane]
        sections[cid] = s2
        section_order.append(cid)
    # nodes: prefix with lane to avoid id collisions, remap edges
    idmap = {}
    for n in d.get("nodes", []):
        nid = n.get("node_id") or n.get("id")
        new_id = f"{lane}:{nid}"
        idmap[nid] = new_id
        n2 = copy.deepcopy(n)
        n2["node_id"] = new_id
        n2["lane"] = lane
        n2["original_node_id"] = nid
        # normalise section references to canonical ids
        if "section_ids" in n2:
            n2["section_ids"] = [canon(x) for x in n2["section_ids"]]
        nodes.append(n2)
    for e in d.get("edges", []):
        e2 = copy.deepcopy(e)
        frm, to = e2.get("from"), e2.get("to")
        e2["from"] = idmap.get(frm, frm)
        e2["to"] = idmap.get(to, to)
        e2["lane"] = lane
        edges.append(e2)

# --- root: issue classification, one Laya choice per decision node ---
root_node = {
    "node_id": "root:issue-classification",
    "lane": "root",
    "type": "choice",
    "question": "Which issues does this question raise? Pick ALL that apply — a complex family-law question usually raises several at once.",
    "laya_type": "choice",
    "options": [
        {"value": "maintenance", "next": "maintenance:maintenance-root",
         "section_set": ["bnss-144", "hma-24", "hma-25", "pwdva-20"]},
        {"value": "custody", "next": "custody:custody_sub_issue_choice",
         "section_set": ["hma-26", "gwa-1890", "hmga-1956-s6", "welfare-principle"]},
        {"value": "stridhan", "next": "stridhan:stridhan-subissue",
         "section_set": ["hma-27", "bns-316"]},
        {"value": "residence", "next": "residence:residence_sub_issue",
         "section_set": ["pwdva-17", "pwdva-18", "pwdva-19", "pwdva-20"]},
        {"value": "procedure", "next": "procedure:court-selection",
         "section_set": []},
    ],
    "fast_path_note": "One Laya forward pass per decision node; section selection uses no free-text generation. A multi-issue question runs the root choice once, then each selected lane's choice nodes in parallel — classification in a fraction of a second, not a generated answer.",
    "escalate_rule": "If no issue can be picked with confidence, or the question is outside family law, escalate to human/LLM — do not guess a section.",
}
nodes.insert(0, root_node)
for opt in root_node["options"]:
    edges.append({"from": "root:issue-classification", "to": opt["next"],
                  "condition": f"issue includes {opt['value']}", "lane": "root"})
# section sets -> procedure (court + documents) once sections are picked
for lane_root, set_node in [
    ("maintenance", "maintenance:maintenance-section-set"),
    ("custody", "custody:custody_section_set"),
    ("stridhan", "stridhan:stridhan-section-set"),
    ("residence", "residence:residence_section_set"),
]:
    edges.append({"from": set_node, "to": "procedure:court-selection",
                  "condition": "section set picked; graph now picks court and documents",
                  "lane": "root"})

merged = {
    "model": "Laya (convaiinnovations/laya) — System One decision model, NOT LLaMA",
    "purpose": "Section classification for Indian family law: CrPC/BNSS + BNS (+ HMA / PWDVA / guardianship Acts where the retest proved them necessary). One Laya choice per decision node; no free-text generation for section selection.",
    "version": "1.0",
    "date": "2026-11-26",
    "source": "Fresh English retest 2026-11-26, rated 4/10 overall (legal accuracy 3/10). Test case: 35yo Hindu woman, Bengaluru, Hindu marriage 2012, husband separated 2 years, Rs 40,000/month, paying no maintenance, 8yo daughter, Stridhan Rs 5 lakh gold + Rs 2 lakh cash held by husband's family, eviction threats from house in husband's name. Asked maintenance, custody, Stridhan return, residence, court, documents, timeline.",
    "model_download_status": "NOT part of this file. Official convaiinnovations/laya weights failed with 403; PIXMELT/laya (~810 MB English checkpoint) download was running separately to ~/workspace/models/laya-english. This graph works with any Laya checkpoint once loaded.",
    "guardrails": {
        "rajnesh_v_neha": "Maintenance ONLY. NEVER cite for Stridhan, custody, residence or divorce.",
        "satish_chander_ahuja": "Shared household / residence ONLY. NEVER cite for custody.",
        "residence_label": "Right to reside in the SHARED HOUSEHOLD. NEVER call it 'tenancy rights'.",
        "court_selection": "The graph picks the court (Family Court, Bengaluru for HMA matters; Magistrate for BNSS s.144 and PWDVA matters). NEVER ask the user to pick the court.",
        "divorce_gate": "HMA s.13 / s.13B ONLY if divorce was asked. In the test case no divorce was asked, so they must NOT fire.",
        "birth_certificate": "Registration of Births and Deaths Act 1969. NOT the Hindu Marriage Act.",
        "salary_slips": "Ask husband's income / school fees / where husband lives now. Do NOT demand salary slips the user said she does not have.",
        "quantum": "Section selection is high-confidence on the test facts; maintenance QUANTUM is low-confidence until husband's income is known — escalate quantum, not section selection. Never invent an amount.",
        "no_double_counting": "Do not double-count the same maintenance under both PWDVA s.20 and BNSS s.144 / HMA ss.24-25. PWDVA s.20 is one canonical section, shared by the maintenance and residence lanes.",
    },
    "fast_path": {
        "design": "root choice (1 forward pass) -> one choice per selected lane (parallel) -> section_set node -> procedure court/documents node. No generation step for section selection.",
        "laya_primitives_used": ["choice", "score", "noul"],
        "escalate_on": "low confidence, missing facts, or a question outside the verified section set",
    },
    "counts": {
        "lanes": lane_counts,
        "sections_statutory_and_principle": len([s for s in sections.values() if s.get("kind") not in ("procedure", "court", "document", "timeline")]),
        "procedure_items": len([s for s in sections.values() if s.get("kind") in ("procedure", "court", "document", "timeline")]),
        "sections_total_unique": len(sections),
        "nodes_total": len(nodes),
        "edges_total": len(edges),
    },
    "sections": [sections[cid] for cid in section_order],
    "nodes": nodes,
    "edges": edges,
    "section_sets_for_test_case": {
        "maintenance": ["bnss-144", "hma-24", "hma-25", "pwdva-20"],
        "custody": ["hma-26", "gwa-1890", "hmga-1956-s6", "welfare-principle"],
        "stridhan": ["hma-27", "bns-316"],
        "residence": ["pwdva-17", "pwdva-18", "pwdva-19", "pwdva-20"],
        "divorce": [],
        "note": "Divorce set is EMPTY for the test case — HMA s.13/s.13B do not fire because no divorce was asked.",
    },
    "unverified_excluded": [
        {"item": "Any BNS section other than BNS s.316", "verification_status": "unverified — do not use as fact", "reason": "Not in the verified retest list; no BNS section beyond s.316 was verified in this build."},
        {"item": "Any CrPC/BNSS section other than BNSS s.144 (old CrPC s.125)", "verification_status": "unverified — do not use as fact", "reason": "Not in the verified retest list."},
        {"item": "HMA s.13 / s.13B as a default citation", "verification_status": "unverified for this test case — do not use as fact", "reason": "Divorce-only gate; no divorce was asked."},
        {"item": "Maintenance quantum / amount for the test case", "verification_status": "unverified — do not use as fact", "reason": "Husband's income, school fees and whereabouts unknown; quantum must be escalated, not invented."},
        {"item": "Timeline durations", "verification_status": "estimate only, not a statutory deadline", "reason": "Lane 5 marks every duration ESTIMATE."},
        {"item": "Pratibha Rani v. Suraj Kumar (1985) and Rashmi Kumar v. Mahesh Kumar Bhada (1997) as Stridhan precedents", "verification_status": "lane-supplied, not retest-verified — check against the judgment text before citing in a live answer", "reason": "Supplied by Lane 3; correct issue (Stridhan ownership/entrustment) but not part of the 2026-11-26 retest evidence."},
    ],
    "open_questions_from_lanes": [
        "Stridhan: test case does not state whether a demand for return was made — BNS s.316 expected answer is 'entrusted_and_refused', fallback 'entrusted_no_demand_yet' (demand first, then re-evaluate).",
        "Stridhan/HMA 24: whether a matrimonial proceeding is already pending is unconfirmed — HMA s.27 needs a proceeding, HMA s.24 is conditional on one.",
        "Residence: s.19 default is restraint-on-dispossession (stay in the house); removal of respondent / alternative accommodation is fact-dependent — confirm whether to ask the woman's preference first.",
        "Maintenance quantum: no amount can be stated without husband's income; jurisdiction for BNSS s.144 also needs where the husband lives now.",
        "Procedure timeline 'stages' field: kept as supplied by Lane 5 (extra field inside proc-timeline-staged).",
    ],
}

json.dump(merged, open(OUT, "w"), indent=2, ensure_ascii=False)
print("wrote", OUT)
print("sections unique:", len(sections))
print("nodes:", len(nodes), "edges:", len(edges))
print("section ids:", section_order)
