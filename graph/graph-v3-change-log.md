# Graph v3 change log — Lane A (labels + graph v3)

**Date:** 2026-11-27. **Mode:** offline only. **File built:**
`workspace/goals/english-family-law-chatbot-retest/files/laya-crpc-bns-section-decision-tree-v3.json`
**SHA-256:** `67bf2b04ca946f7c7fa3062068e01ce051fbce8f4d740c281afe6fff841c34a5`

**Sources:** D1-A settlement (`hma27-settlement-report.md` §2–§3), D2 patch
(`hma27-D2-gate.patch`), D2 validation log (`hma27-D2-gate-validation.md`),
brutal-bank freeze note (`brutal-bank-freeze-note.md` §1, §6), frozen bank
(`brutal-bank-v1-frozen.json`, B-018/B-019).

**Untouched (verified by SHA after the build):** graph v2
(`c7e095ad185242e9360d8b9f180fefff894f5677b52d188174413a32a2704255`),
frozen bank v1 (`934a2b2265ac137c96939e1fbeca3682a037010e42f972bfd459c2fcac4ec717`),
sealed sets (never opened).

## 1. D2 gate patch applied (to a copy of v2, never to v2 itself)

- Patch: `laya-graph/hma27-D2-gate.patch` (363 lines, unified diff, paths
  relative to `files/`), **SHA-256
  `6349c922944275d26bdc38f6c725daee12ddcd25f86f39ae1485f104e507fc04`**.
- Applied with `patch -p1` in a `/tmp` mirror of the `files/` layout (graph +
  notebook, exactly as the D2 validation did it). The patched intermediate
  graph hashes to
  `d8d75663589673e359f8d24da914db42604c5b2dfe48535a55bcaac7a42a6352` —
  **identical to the patched-graph SHA in `hma27-D2-gate-validation.md` §1**,
  and the patched notebook intermediate matches that log's
  `842609ae…` too. (The patched notebook copy is a throwaway intermediate in
  `/tmp/v3work/`; no notebook was written by this lane.)
- All 17 graph edits (G1–G17) from the validation log §2 are in v3:
  R-HMA27-04 `if_fail` is now **`drop`** with the lane-3 §1.4 `drop_reason`
  verbatim ("No HMA proceeding pending or being filed — HMA s.27 cannot be
  invoked standalone; route Stridhan return to the Family Court under Family
  Courts Act s.7(1) Expl. (c) / CPC s.151, and keep BNS s.316 as the criminal
  route."); the "alternatively…" limb is gone — **0 occurrences of
  "alternatively"** in the file; the co-fire rule and every BNS 316
  exclusion/court/relief sentence now name the civil return route as "HMA 27
  where an HMA proceeding is pending/being filed, otherwise the Family Court
  property suit under Family Courts Act s.7(1) Expl. (c) / CPC s.151".
- Counts after the patch alone were still **32 sections / 46 nodes / 77
  edges** (verified before the new sections were added).

## 2. New sections (the label-coverage gap from freeze note §6.1)

### `hma-9` — HMA s.9, restitution of conjugal rights
- **Needed by bank question B-018** (C1): "My husband left our home six
  months ago and refuses to return. I want him to come back, and until then I
  need money to run the house." GT `[hma-9, bnss-144, pwdva-20]`, Family
  Court, escalates `quantum`. Second rater verified the use as legitimate.
- **Statute (verified against the HMA 1955 text, India Code, not memory
  alone):** "When either the husband or the wife has, without reasonable
  excuse, withdrawn from the society of the other, the aggrieved party may
  apply, by petition to the district court, for restitution of conjugal
  rights… Explanation — …the burden of proving reasonable excuse shall be on
  the person who has withdrawn from the society."
- Entry follows the hma-27/pwdva-20 schema: `id, act, section ("9"), title,
  when_used, triggers (10), prerequisites (5), court (Family Court),
  relief` (decree directing resumption of cohabitation; no forced
  cohabitation; no restitution for 1 year+ grounds divorce under
  s.13(1A)(ii), cited only if divorce is then asked; maintenance meanwhile is
  BNSS s.144 / PWDVA s.20), `laya_question` (choice-type, 3 options, expected
  answer grounded on B-018), `related_sections` (bnss-144, pwdva-20, hma-24,
  hma-13, proc-filing-hma), `keywords (7), escalate_rule` (condition +
  missing_facts + on_missing), `exclusions (5), precedent` ("No case-law
  precedent relied on… Do NOT cite a case for HMA s.9 until verified"),
  `lane: matrimonial`, `verification_status` noting v3 addition + B-018.
- **Node added:** `stage2:hma-9-leaf` (type `section_set`, lane `stage2`,
  `section_set: ["hma-9"]`), following the `stage2:divorce-leaf` /
  `stage2:birth-certificate-leaf` pattern.
- **Edge added:** `root:issue-classification` →
  `stage2:hma-9-leaf` (lane `stage2`; condition: spouse has left home /
  withdrawn from society and user wants them to return).

### `pwdva-22` — PWDVA s.22, compensation orders
- **Needed by bank question B-019** (C1): "My husband broke my arm and I
  spent 60,000 rupees on hospital treatment. I want him to pay my medical
  costs and monthly support." GT `[pwdva-18, pwdva-22, pwdva-20, bnss-144]`,
  Magistrate, escalates `[safety, quantum]`. Second rater verified the use as
  legitimate.
- **Statute (verified against the PWDVA 2005 text, India Code, not memory
  alone):** "In addition to other reliefs as may be granted under this Act,
  the Magistrate may on an application being made by the aggrieved person,
  pass an order directing the respondent to pay compensation and damages for
  the injuries, including mental torture and emotional distress, caused by the
  acts of domestic violence committed by that respondent."
- Entry in the same schema: `id, act, section ("22"), title, when_used,
  triggers (9), prerequisites (4 — incl. PWDVA s.2(a) "aggrieved person" is a
  woman), court (Judicial Magistrate First Class, PWDVA s.12), relief`
  (compensation/damages for injuries incl. mental torture and emotional
  distress, in addition to every other relief; no statutory tariff — quantum
  judicially assessed; B-019's Rs 60,000 hospital bill is compensable as
  injury costs; monthly support is s.20 / BNSS s.144, NOT s.22),
  `laya_question` (choice-type, 3 options, expected answer grounded on
  B-019), `related_sections` (pwdva-18, pwdva-20, pwdva-19, bnss-144,
  proc-filing-magistrate), `keywords (8), escalate_rule, exclusions (6 —
  incl. not available to a male claimant, cf. bank B-148; no double recovery
  across s.20/s.22 or a civil decree), precedent` (same no-case-law line),
  `lane: residence`, `lanes: [residence, maintenance]`,
  `verification_status` noting v3 addition + B-019.
- **Node added:** `stage2:pwdva-22-leaf` (type `section_set`, lane `stage2`,
  `section_set: ["pwdva-22"]`).
- **Edge added:** `root:issue-classification` →
  `stage2:pwdva-22-leaf` (lane `stage2`; condition: injuries from domestic
  violence and compensation/damages asked).

### Counts added by §2
- Sections **+2** (hma-9, pwdva-22), nodes **+2** (the two stage2 leaves),
  edges **+2** (the two root → leaf edges).
- Note on "edges for their related_sections links": in v2, cross-section
  links live inside each section's `related_sections` array (that is the
  graph's convention — no v2 edge connects section ids to each other; edges
  connect node ids). Both new sections carry full `related_sections` arrays
  (5 links each, all resolving). The new *edges* connect the new leaf nodes
  into the root traversal, which is what makes the sections reachable; no
  per-related-section edge pattern exists in v2 to follow.

## 3. Old vs new counts

| | v2 | v3 (D2 patch + §2) |
|---|---|---|
| Sections | 32 | **34** |
| Nodes | 46 | **48** |
| Edges | 77 | **79** |
| `counts.sections_total_unique` | 32 | 34 |
| `counts.sections_statutory_and_principle_v2` | 16 | 18 (both new sections are statutory) |
| `counts.sections_new_in_v3` | — (new key) | 2 |
| `version` / `date` | 2.0 / 2026-11-26 | **3.0 / 2026-11-27** |

### Exact expected counts for the notebook's Cell 5 assert
Cell 5 of `live-laya-colab-test-v5-precision.ipynb` currently asserts
`(n_sections, n_nodes, n_edges) == (32, 46, 77)`. For the v6 notebook built
on graph v3 the assert must become:

```python
assert (n_sections, n_nodes, n_edges) == (34, 48, 79), (
    f'Graph counts do not match v3 (expected 34/48/79, got {n_sections}/{n_nodes}/{n_edges}). '
    'You may have uploaded the v2 graph — upload the v3 file and re-run.')
```

and the `GRAPH_FILE` becomes
`laya-crpc-bns-section-decision-tree-v3.json`. (Build lane's change — this
lane wrote no notebook.)

## 4. Verification results (v3 file)

All checks run on the written v3 file; full list:

- Valid JSON; **34 sections / 48 nodes / 79 edges**; `version 3.0`,
  `date 2026-11-27`; `counts` object 34/48/79 — PASS.
- No duplicate section ids or node ids — PASS.
- **New sections:** hma-9 and pwdva-22 each present once, all 14 required
  fields present and non-empty (`id, act, section, title, when_used,
  triggers, prerequisites, court, relief, laya_question, related_sections,
  keywords, escalate_rule, exclusions`); `laya_question.type == "choice"`;
  all their `related_sections` resolve; each has a node — PASS.
- **New nodes/edges:** `stage2:hma-9-leaf`, `stage2:pwdva-22-leaf` present;
  both root → leaf edges present with existing endpoints — PASS.
- **Every node section reference exists** (`section_ids`, `section_set`,
  option `section_set`) — PASS.
- **D2 changes present:** R-HMA27-04 `if_fail == "drop"` with the §1.4
  `drop_reason`; hma-27 prerequisites carry the corrected §1.4 wording;
  "alternatively" = 0 occurrences; co-fire wording present — PASS.
- **Equivalence check:** v3 minus the §2 additions (2 sections, 2 nodes,
  2 edges, version/date/counts) is **byte-identical in content to the
  D2-patched v2** (SHA `d8d75663…`, matching the D2 validation log) — PASS.
  The build therefore contains exactly the D2 patch plus the §2 additions,
  nothing else.
- **Pre-existing v2 defects inherited unchanged (NOT introduced by this
  lane, NOT fixed — out of scope; flagged for the coordinator/build lane):**
  1. Three v2 edges point at non-node targets: `stage1:confidence-gate` →
     `escalate_clarify`; `stage2:demand-gate` → `bns-316`;
     `stage2:demand-gate` → `escalate_demand_first`. Identical in v2.
  2. `related_sections` across v2 uses several free-text forms, not only
     resolvable ids: plain display strings ("HMA s.24", "PWDVA s.17", …),
     UPPER_SNAKE constants ("HMA_26", "WELFARE_PRINCIPLE", "GWA_1890",
     "HMGA_1956_s6"), and one wrong id — bnss-144's related entry
     `section_id: "hmga-6"` (the real id is `hmga-1956-s6`). All of these
     are byte-identical in v2. The two new sections use only the resolvable
     `{section_id, relationship}` form.
  3. Consequence: a strict whole-file "every related_sections id exists /
     no dangling references" check FAILS on the file as a whole because of
     (1) and (2) above. Every reference **added by this lane** resolves.
     Deciding whether to normalise the pre-existing forms is a coordinator
     call — it would touch many untouched v2 sections.

## 5. Lane 2 `recovery` escalation text — exact location + replacement

**The operative text lives in ONE file, in TWO places** (same wording):
- `laya-graph/v6-lane2-escalates.md` **line 98** (§1.2 table, `recovery` row):
  > "Stridhan recovery: sold or withheld gold cannot be recovered or valued
  > by the bot — escalate to a lawyer for valuation, a police complaint under
  > BNS s.316 and civil recovery under HMA s.27."
- `laya-graph/v6-lane2-escalates.md` **line 367** (§3 code snippet, the
  `esc_typed.append({'kind': 'recovery', ...})` block, lines 364–368):
  > "Stridhan recovery: sold or withheld gold cannot be recovered or valued
  > by the bot -- escalate to a lawyer for valuation, a police complaint
  > under BNS s.316 and civil recovery under HMA s.27."

**Summaries only (not operative text, same correction applies if reworded):**
- `laya-graph/v6-deep-dive-report.md` **line 147** (§3.1 table):
  "…BNS 316 complaint, HMA 27 recovery."
- `laya-graph/v6-deep-dive-report.md` **line 171** (§3.2, H15 bullet):
  "…a BNS 316 complaint, HMA 27 recovery; …"

**Checked and clean:** `v5-laneB-custody.md` (no occurrence) and the v5
notebook `live-laya-colab-test-v5-precision.ipynb` (0 occurrences of "civil
recovery under HMA" — the `recovery` kind does not exist in the v5 notebook;
it is a v6 Lane 2 design). No other `.ipynb` / `.json` / `.py` under
`files/` contains the phrase (outside the freeze-note / settlement-report
mentions, which are reports, not system text).

**Proposed D1-A-correct replacement wording** (for the build lane to apply
at both v6-lane2-escalates.md locations; no notebook edited by this lane):
> "Stridhan recovery: sold or withheld gold cannot be recovered or valued
> by the bot — escalate to a lawyer for valuation, a police complaint under
> BNS s.316 and civil recovery through the Family Court under FCA s.7(1)
> Expl. (c) / CPC s.151 (or under HMA s.27 where an HMA proceeding is
> pending or being filed)."

The civil route is the Family Court under FCA s.7(1) Expl. (c) / CPC s.151
unless an HMA proceeding is pending/being filed, in which case HMA 27; BNS
s.316 is never cited alone as the civil route. Note for the build lane: the
`recovery` trigger (`kept ∩ {hma-27, bns-316} ≠ ∅` AND `demand_made is
True`) fires on either section, so a conditional variant is also valid —
emit "civil recovery under HMA s.27" only when `hma-27` is in `kept`, else
the FCA s.7(1) Expl. (c) / CPC s.151 route. Under the D2 gate, `hma-27` is
only kept when a proceeding exists, so the conditional variant is exact on
every question; the single-string replacement above is the safe
unconditional form.

## 6. Out of scope / open for the build lane (not done here)
- Notebook changes: Cell 5 assert + `GRAPH_FILE` → v3 (see §3); Stage 1
  candidate generation must be able to produce `hma-9` / `pwdva-22`
  (stage1 phrasebook/mappings in the graph only reference external lane
  files — no stage1 entries were added by this lane); the D2 gate
  (`being_filed`, `gated_out`) is a notebook change from the D2 patch, not
  re-applied here.
- The pre-existing dangling references in §4 (coordinator decision).
- No live run was performed and none is claimed.
