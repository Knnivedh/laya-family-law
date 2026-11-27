# SHARED BRIEF — v2 Layman-proof Laya decision graph (2026-11-26)

## Coordinator
I am the coordinator. I own the merged v2 file. Lanes write ONLY their own file under `v2-lanes/`; never edit v1 or another lane's file. A lane is finished only when its file is on disk and its claimed counts can be read back from that file with `python3 -c "import json; json.load(open(...))"`.

## v1 source of truth (DO NOT EDIT)
- Main v1: `~/workspace/goals/english-family-law-chatbot-retest/files/laya-crpc-bns-section-decision-tree.json` (182 KB, valid JSON, 29 unique sections, 38 nodes, 66 edges, 0 dangling endpoints)
- Lane fragments: `.../laya-graph/lanes/` (maintenance, custody, stridhan, residence, procedure)
- Test report: `.../laya-graph/test-report.md`
- Model (already downloaded, DO NOT retry download): PIXMELT/laya English, 808 MB, `~/workspace/models/laya-english/model.safetensors` (804 MB). Laya = Convai Innovations System One decision model, 421M ModernBERT-large, NOT LLaMA.

## Test case (all lanes use this)
35yo Hindu woman, Bengaluru, Hindu marriage 2012, husband separated 2 years, ₹40,000/month, paying no maintenance, 8yo daughter, Stridhan ₹5 lakh gold + ₹2 lakh cash held by husband's family, eviction threats from house in husband's name. Asked maintenance, custody, Stridhan return, residence, court, documents, timeline.

## Verified sections ONLY — do not invent new BNS/CrPC sections
BNSS s.144 (old CrPC s.125); HMA ss.24, 25, 26, 27; PWDVA ss.17, 18, 19, 20; Guardians and Wards Act 1890; Hindu Minority and Guardianship Act 1956 s.6; welfare-of-the-child principle; BNS s.316 (IPC s.406 equivalent); HMA ss.13/13B ONLY if divorce asked; Registration of Births and Deaths Act 1969 (birth certificate, NOT HMA). Anything else goes in `unverified_excluded` with that label.

## Forbidden mappings (hard guardrails, v2 must enforce them in Stage 2)
- Rajnesh v. Neha = maintenance ONLY, never Stridhan/custody/residence/divorce.
- Satish Chander Ahuja = shared household / residence ONLY, never custody.
- Residence is NOT 'tenancy rights'.
- Never ask the user to pick the court — graph picks Family Court Bengaluru (HMA) / Magistrate (BNSS 144, PWDVA).
- Never demand salary slips she said she does not have; ask husband's income, school fees, where husband lives now.
- Maintenance quantum: escalate, never invent an amount.

## v2 two-stage design — confirm this understanding in every lane file's header
STAGE 1 — Layman → article/section: pick ALL layman words/phrases, fetch them into article-section format. Convert every layman expression into legal terms, then map legal terms to section(s) via Laya choice questions. User asks in layman format, e.g. "my husband is not giving me money", "he took my gold and cash and won't return it", "they are throwing me out of the house", "who will get my daughter", "I need money for my child", "he beats me / threatens me".
STAGE 2 — Recheck inside the article section: after Stage 1 picks sections, RECHECK each picked section against ALL its relations — prerequisites, exclusions/not_for, related_sections, guardrails, court, co-firing sections. Only after recheck is the answer final. A section failing recheck (wrong issue, missing prerequisite, divorce not asked, etc.) must be DROPPED with a reason, not kept. Examples: BNSS 144 firing must recheck HMA 24 vs 25 and PWDVA 20; Stridhan must recheck HMA 27 + BNS 316 together; custody must recheck welfare-of-child overriding natural-guardian default; residence must recheck PWDVA 17+18+19+20 as a set.

## Lane output files (all under .../laya-graph/v2-lanes/)
1. `lane1-phrasebook.json` — layman phrasebook
2. `lane2-stage1-mapping.json` — Stage-1 mapping
3. `lane3-stage2-recheck.json` — Stage-2 recheck rules
4. `lane4-adversarial-tests.json` — 30-question test suite + results
5. `lane5-website-content.md` — website content/spec (DO NOT build an artifact yourself; the coordinator builds the web artifact)

## Finish contract (every lane)
Report: file path, claimed counts (recomputable from the file), pass/fail, open questions. Validate JSON with python json.load before finishing. No invented sections. No claim of "never fails" — report honest pass rate and every failure with a fix.
