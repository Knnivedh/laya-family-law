# Test report — Laya CrPC/BNS section decision tree, 2026-11-26 test case

File tested: `laya-crpc-bns-section-decision-tree.json` (valid JSON, `python json.load` passes)

## Test case (fresh English retest, 2026-11-26)
35yo Hindu woman, Bengaluru, Hindu marriage 2012, husband separated 2 years,
Rs 40,000/month, paying **no** maintenance, 8yo daughter, Stridhan Rs 5 lakh gold
+ Rs 2 lakh cash held by husband's family, eviction threats from house in
husband's name. Asked: maintenance, custody, Stridhan return, residence,
court, documents, timeline.

## Walk through the tree (by hand)
1. **Root choice** `root:issue-classification` — one Laya forward pass.
   Picks ALL of: maintenance, custody, stridhan, residence, procedure.
   Divorce is **not** picked (not asked). No free-text generation is used
   for section selection.
2. **Maintenance** → `maintenance:maintenance-section-set`:
   BNSS s.144 + HMA s.24 + HMA s.25 + PWDVA s.20.
   BNSS s.144 is the live immediate remedy (wife + daughter as separate
   heads); HMA s.24 is interim/pendente lite (conditional — needs a pending
   HMA proceeding), HMA s.25 is permanent alimony at/after decree.
   Quantum escalated, not invented: husband's income unknown.
3. **Custody** → `custody:custody_section_set`:
   HMA s.26 + Guardians and Wards Act 1890 + HMGA 1956 s.6 +
   welfare-of-the-child principle (paramount, overrides the natural-guardian
   default — father is natural guardian for an 8yo above five, so the claim
   rests on welfare, not on denying his status).
4. **Stridhan** → `stridhan:stridhan-section-set`:
   HMA s.27 (Family Court, return in specie or Rs 7 lakh value) +
   BNS s.316 (criminal breach of trust, IPC s.406 equivalent).
   Civil and criminal routes together; neither replaces the other.
   Open fact: whether a demand for return was made (fallback:
   `entrusted_no_demand_yet` — demand first, then re-evaluate).
5. **Residence** → `residence:residence_section_set`:
   PWDVA s.17 + s.18 + s.19 + s.20 as a set. Default s.19 direction:
   restraint on dispossession (stay in the house); removal of respondent /
   alternative accommodation is fact-dependent.
6. **Procedure** → `procedure:court-selection`: graph picks the court —
   Family Court, Bengaluru for HMA matters; Magistrate for BNSS s.144 and
   PWDVA matters. Then `procedure:clarifying-questions` asks the 3 missing
   facts (husband's income, school-fee amount, where the husband lives now)
   and `procedure:documents-checklist` lists the documents. Salary slips
   are **not** demanded.

## Forbidden mappings — verified NOT firing
- Rajnesh v. Neha: cited for maintenance quantum ONLY; never for Stridhan,
  custody, residence or divorce. No Stridhan node references it as authority.
- Satish Chander Ahuja: cited for residence/shared household ONLY
  (PWDVA ss.17/19); never for custody.
- Residence is never called 'tenancy rights' except in exclusion fields.
- HMA s.13/s.13B: divorce set is EMPTY for this case (see
  `section_sets_for_test_case.divorce: []`).
- Birth certificate: Registration of Births and Deaths Act 1969, not HMA.
- Court: picked by the graph, never asked of the user.

## Counts (verified from the merged file, not from lane claims)
- Sections (unique): **29** — 13 statutory/principle + 16 procedure items
  (PWDVA s.20 deduplicated: it appeared in both the maintenance and
  residence lanes and is one canonical section here)
- Nodes: **38** (1 root + 37 lane nodes, all unique)
- Edges: **66** (57 lane edges + 5 root edges + 4 section-set → procedure edges)
- Dangling edge endpoints: **0**; unresolved section references: **0**

## Excluded as unverified (in `unverified_excluded`)
Any BNS section other than s.316; any CrPC/BNSS section other than
BNSS s.144; HMA s.13/s.13B as a default citation; any maintenance amount;
timeline durations (estimates only); Lane 3's Stridhan precedents
(Pratibha Rani / Rashmi Kumar — correct issue, but not retest-verified,
so check against the judgment text before live citation).

## Open questions carried from the lanes
1. Was a demand for Stridhan return made? 2. Is a matrimonial proceeding
already pending (gates HMA s.24/s.27)? 3. s.19 direction — ask the woman's
preference first? 4. Husband's whereabouts (BNSS s.144 jurisdiction) and
income/school fees (quantum).
