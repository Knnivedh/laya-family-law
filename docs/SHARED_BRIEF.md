# Shared brief — Laya family-law section decision graph
Coordinator: this subagent (sole merger). Finish contract: each lane writes ONE JSON fragment to files/laya-graph/lanes/<lane>.json, valid JSON, with its sections/nodes/edges counted in its report back.
Test case (2026-11-26 retest): 35yo Hindu woman, Bengaluru, Hindu marriage 2012, husband separated 2 years, Rs 40,000/month, paying no maintenance, 8yo daughter, Stridhan Rs 5 lakh gold + Rs 2 lakh cash held by husband's family, eviction threats from house in husband's name. Asked maintenance, custody, Stridhan return, residence, court, documents, timeline.
VERIFIED sections ONLY (do not invent others; anything else = verification_status "unverified — do not use as fact", out of main tree):
Maintenance: BNSS s.144 (old CrPC s.125), HMA s.24 interim pendente lite, HMA s.25 permanent alimony, PWDVA s.20 monetary reliefs
Custody: HMA s.26, Guardians and Wards Act 1890, Hindu Minority and Guardianship Act 1956 s.6, welfare-of-the-child principle (paramount)
Stridhan: HMA s.27 disposal of property / Stridhan return, BNS s.316 criminal breach of trust (IPC s.406 equivalent)
Residence: PWDVA s.17 right to reside in shared household, PWDVA s.18 protection order, PWDVA s.19 residence order, PWDVA s.20 monetary reliefs
Divorce ONLY if asked: HMA s.13, s.13B — never by default
Birth certificate: Registration of Births and Deaths Act 1969 — NOT HMA
FORBIDDEN: Rajnesh v Neha = maintenance ONLY never Stridhan; Satish Chander Ahuja = shared household/residence never custody; never call residence 'tenancy rights'; never ask user to pick court — graph picks it; never cite HMA 13/13B when no divorce asked.
Each section must have: id, act, section, title, when_used (exact triggering facts), triggers/keywords, prerequisites, exclusions/not_for, related_sections, court, relief, precedent (correct issue only), laya_question (choice/score/noul, options, expected answer for test case), escalate_rule (low confidence / missing facts -> human/LLM).
Each lane fragment JSON shape: {"lane": "...", "sections": [...], "nodes": [{"node_id","type":"choice|section_set|leaf","question","options","next","section_ids"}], "edges": [{"from","to","condition"}]}
