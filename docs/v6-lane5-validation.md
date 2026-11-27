# Lane 5 — Validation readiness (v6 deep-dive)

**Lane:** 5 (validation readiness). **Date:** 2026-11-27. **Mode:** offline only — no browser, no Colab.
**Scope respected:** no ground truth changed, no notebook touched, no sealed question wording read.
All sealed-set checks below use metadata only (counts, checksums, tags, facts, script fractions, dates).
No sealed wording is copied anywhere in this file.

**Headline findings**
1. The sealed sets are properly frozen in substance (hashes verified, blind writer, GT fixed before any sealed run, zero 8-gram overlap) — but the freeze record has gaps (no rater name, no Kannada-fluency evidence, `frozen_date` one day off the file mtime, no checksum on the freeze note itself).
2. **Fresh-16 vs fresh-20 is a real discrepancy** that must be resolved by amending the gate doc *before* any fresh run (recommendation in §2). The sealed 20 is stricter than the gate's 16; do not silently run 20 against a gate that says 16, and do not silently trim 20 to 16.
3. **The rating formula discrepancy is real and material.** The gate (§2) freezes one formula; the "working formula" used for the v3 5.9 and v4r 7.7 ratings is a different formula. Under the gate formula v3 is **5.0** (not 5.9) and v4r is **7.3** (not 7.7). The gate formula governs (§6 rule 9). The brief's "v1 3.3 under the working formula" is also wrong: 3.3 is the *gate*-formula value; the working formula gives v1 **4.8**.
4. **v5-predicted cannot reach 9/10 as a claim yet, and cannot exceed a capped 9.0 even with 16/16.** Under the gate formula v5-predicted is 9.8 raw, but four independent caps (prose not measured, fresh not run, Kannada not run, no confirmation) each cap it at 9.0. The user's 9/10 minimum target is therefore reachable only as a *capped* 9.0, and only after a live 16/16 current-set pass — it is not 10/10.
5. **G14 latency is currently FAILING on v4r too** (mean 57.6 s, max 133.3 s, total 921.6 s vs ≤15/≤30/≤240 s) — not just on v3. The filed v4r MD does not even surface latency. G14 blocks any 10/10 claim regardless of rating, and v5's fixes do nothing for it.
6. **Run filing is incomplete:** v4 and v4.1 notebooks exist but were never run live; v5 has no live run filed (prediction only); no sealed, prose, or confirmation run exists; the coordinator log's run table is stale (no v4r row).

---

## 1. Freeze check (metadata only)

### 1.1 Checksums — VERIFIED

Recomputed 2026-11-27 from the files on disk; both match the freeze note exactly.

| File | SHA-256 (freeze note) | SHA-256 (recomputed now) | Match |
|---|---|---|---|
| `sealed/sealed-fresh-20.json` | `1d8b5dc376e711c3ac6ead4424bb2d8ce52b07552b9a533ad86e0616dbcf8837` | `1d8b5dc376e711c3ac6ead4424bb2d8ce52b07552b9a533ad86e0616dbcf8837` | ✅ |
| `sealed/sealed-kannada-8.json` | `2f652af1123a22441cc4158ddf480ef0981aa923858bbcb9dc3622f5e5c25853` | `2f652af1123a22441cc4158ddf480ef0981aa923858bbcb9dc3622f5e5c25853` | ✅ |

Any future change to either JSON invalidates the freeze; re-hash and re-note (per the freeze note itself).

### 1.2 Freeze-check table

| Check (gate §4.1 / §6) | Finding | Verdict |
|---|---|---|
| Files exist, counts as named | fresh-20: 20 questions, IDs F1–F20, no gaps/dupes. Kannada-8: 8 questions, IDs KN1–KN8. | ✅ PASS |
| Checksums recorded + matching | Both SHA-256 recorded in freeze note and verified by coordinator + re-verified by this lane (see §1.1). | ✅ PASS |
| GT frozen before tuning | Freeze note: "Ground truth was fixed before any system run on these questions." Files written 2026-11-26 23:51 IST; v5 has never run live; no sealed run has ever happened. v4r (live ~00:19 IST 27 Nov) ran *after* the freeze but never saw the sealed sets. | ✅ PASS |
| Written by a rater who is not the tuning lane (gate §4.1) | Author role recorded as "blind sealed-test-set writer (subagent, depth 2)"; blindness statement lists exactly one file read (`backtest-laya-vs-llama8b.md`, for GT rules + no-overlap check only) and an explicit did-not-read list (no live results, no plan, no notebook, no builder, no `browser_downloads`). No tuning-lane member wrote the sets. | ⚠️ PASS IN SUBSTANCE, GAP IN RECORD — **no rater name/ID is recorded anywhere** (only a role + "blind_writer": true in the JSON). Recommend recording the writer subagent's session/label in a freeze-note addendum (no JSON change). |
| No-overlap vs current 16 | Mechanical check: zero shared word 8-grams across all 28 sealed questions vs all 16 current questions. Three near-collisions (F3, F15, F18) caught and reworded *before* freezing. | ✅ PASS |
| Kannada script recorded | JSON `language: "kn"`; measured Kannada-script character fraction 0.831–0.868 on **all 8** questions (KN1 0.831 … KN5 0.868). This is Kannada script, not Latin transliteration. Gate §4: transliterated Kannada would be a separate variant — not the case here. | ✅ PASS |
| Kannada composition (gate §4) | KN1 maintenance, KN2 custody (child under 5), KN3 Stridhan (demand not made), KN4 residence, KN5 divorce-asked multi-issue (7 GT sections), KN6 divorce-not-asked (5 GT sections), KN7 birth certificate, KN8 out-of-scope. Matches the gate's 8-element composition exactly. | ✅ PASS |
| Fresh composition vs gate §4 (16) | See §2 — the sealed set was built to a **different, 20-question composition table** (its own requirements), not the gate's 16-question table. Counts verified: maintenance 4, custody 3, Stridhan 3, residence 2, violence 2, divorce 2, birth cert 2, OOS 2; multi-issue (≥3 GT sections) 10 by section count, 5 tagged `multi-issue` (F10, F14, F15, F16, F18); five-issue F15 (10 GT sections); ≥5 GT sections on 6 questions (F10, F12, F14, F15, F16, F18); negation 3 (F7, F12, F13); divorce-not-asked 4 (F6, F12, F13, F18); decree-passed HMA-25-keep F4; mutual-consent 13B F16; judicial separation F18. **Two gate-§4 elements are NOT verifiably present from metadata:** (a) salary-slips-missing — no such difficulty tag exists in the set; (b) no-proceeding interim money — the only `interim-money` question (F3) is case-pending. Also the gate's "violence + residence + school fees" multi-issue question is not matched: `school-fees` appears only on F4 (a maintenance question). | ⚠️ DISCREPANCY — see §2 |
| F20 escalate conflict | Documented in freeze note item 11 and coordinator log: F20 has empty GT/court but `escalates: true` (human-lawyer handoff). Scorer must apply the F20-specific human-lawyer rule, not mark it a failure. Metadata confirms: `expected_escalations` includes type `human-lawyer`; F19 is the only `escalates: false` fresh question. | ✅ DOCUMENTED — scorer rule must be enforced in the v6 runner (see §6) |
| GT judgement calls documented | 14 numbered judgement calls in the freeze note (F3/HMA 13, F4 post-decree exclusions, F6 undecided, F7 visitation-only, F12 PWDVA 20 via rent, F13 violence-only, F15 five-issue routing, F16 13B-only, F18 judicial separation, F19/F20 OOS, court mapping, F10 no-proof, KN parallels). Re-derivable from the note + JSON metadata. | ✅ PASS |
| Dates | File mtimes 2026-11-26 18:21:29 UTC (= 23:51 IST). JSON `frozen_date: "2026-11-27"`. Freeze note: "Date frozen: 2026-11-27 (task issued 2026-11-26 ~23:48 IST)". | ⚠️ MINOR INCONSISTENCY — files were written 26 Nov 23:51 IST but dated 27 Nov (likely UTC-date vs IST-date slip). Not a freeze break; record a one-line addendum noting the mtime, do not touch the JSONs. |

### 1.3 What is missing from the freeze

1. **Rater name/ID** — only a role ("blind sealed-test-set writer") is recorded. Gate §4.1 requires the rater to be someone other than the tuning lane; the substance is satisfied but the identity is not on file.
2. **Kannada-fluency evidence** — gate §4 requires Kannada GT "frozen by a Kannada-fluent rater". Nothing on file evidences the writer's Kannada fluency. Recommend one independent Kannada-fluent check of the KN GT *before* the Kannada gate run (read-only; any GT error found goes through gate §6 rule 1 — independent rater, and a GT change invalidates prior runs on that set).
3. **No checksum on the freeze note itself** — only the two JSONs are hashed. If the note is edited later (e.g. to add the rater name), there is no hash to detect it. Recommend: hash the note as it stands now, file the hash in the coordinator log, and make any addendum a *separate* dated file, never an edit to the note.
4. **No backup location recorded** — no note of where else the sealed files live. Recommend one read-only copy filed outside the working tree (e.g. with the filed run results) with hashes re-verified.
5. **HMA 27 GT dispute is open and interacts with the freeze.** The legal lane (`legal-decisions-v4.md`) verdicts that HMA 27's graph prereq is correct and the *current-16 GT is wrong* on H3/H10/H15. That dispute is about the current 16, not the sealed sets — but the sealed sets also contain HMA 27 in GT (it is in the fresh-20 section union and the Kannada-8 union). If the HMA 27 GT is ever changed, gate §6 rule 1 invalidates **all** prior runs on every affected set and requires re-runs. Decision required from the parent/coordinator *before* the fresh run; do not let it surface mid-gate. This is not a freeze defect, it is an open decision that the freeze does not protect against.

---

## 2. Fresh-16 vs fresh-20 discrepancy — with recommendation

### 2.1 The discrepancy, stated plainly

| Source | Fresh set size | Gate target | Composition table |
|---|---|---|---|
| Gate doc §1 G2 + §4 | **16** | 16/16 | 16-question composition (single maintenance ×2, custody ×1, Stridhan ×1, residence ×1, birth cert ×1; multi ×4 incl. divorce-asked / proceeding-pending / demand-not-made / violence+residence+school-fees; divorce-not-asked ×1; salary-slips-missing ×1; income-unknown/quantum ×1; no-proceeding interim money ×1; OOS ×2; ≥2 with ≥5 GT sections; ≥1 negated) |
| Sealed files (frozen) | **20** | — (task brief says 20/20) | 20-question composition in the freeze note (maintenance 4, custody 3, Stridhan 3, residence 2, violence 2, divorce 2, birth cert 2, OOS 2; 5 tagged multi-issue incl. 1 five-issue; 5 missing-facts; 5 no-case-filed; 2 case-pending; 1 decree-passed; ≥3 divorce-not-asked; ≥2 negation; judicial separation ×1) |
| Task brief for this lane | 20 | "sealed fresh-20 20/20" | — |

The sealed 20 is **stricter in size and harder in composition** than the gate's 16 in most dimensions (more questions, 6 questions with ≥5 GT sections vs the gate's ≥2, 3 negations vs ≥1, 4 divorce-not-asked vs 1, plus a first-ever 13B GT and a judicial-separation case). It is **weaker in exactly two gate elements** (§1.2): no salary-slips-missing element and no no-proceeding interim-money element verifiable from metadata. The gate's 16-composition was written *before* the sealed set was commissioned; the overnight task commissioned 20 and the blind writer built 20. Neither document was updated to match the other. The coordinator log already flags this ("gate file says fresh 16; the overnight task says fresh 20 … record the discrepancy, do not silently edit the gate").

### 2.2 Recommendation — amend the gate, do not touch the sealed sets

**Adopt the sealed 20 as the gate set: G2 becomes "fresh held-out 20, 20/20".** Rationale:

- The 20 is frozen, hashed, blind-written, and already delivered. Re-cutting it to 16 would require *choosing which 4 questions to drop* — that choice would be made by the tuning side after seeing the composition, which is itself a selection-bias risk, and dropping F17/F18 (birth cert) or F19/F20 (OOS) would gut coverage the gate explicitly wants.
- The 20 is stricter (20/20 is harder than 16/16), so passing it is a stronger claim, not a weaker one. Nothing already measured is flattered by the change: no fresh run has happened yet, so no run needs re-scoring.
- The two missing gate elements (salary-slips-missing, no-proceeding interim money) are *not* lost silently: record them explicitly as accepted composition deviations in the amendment, with the reason (the sealed set was commissioned to a different table before the gate's table was reconciled). Salary-slips behaviour is still partially covered: the prose forbidden list (§5 item 9, "salary slips demanded when the user said they do not have them") is scored through prose, and F2/F10 carry missing-facts/proof escalations.

**Exact procedure (do this before any fresh run, and before v6 tuning finishes):**

1. Coordinator (parent) approves the amendment in writing; record the approval with date/time in the coordinator log.
2. Edit `laya-10-10-gate-definition.md` only: G2 row → "Exact section-set match, fresh held-out **20** (§4) — **20/20**"; §4 "Fresh held-out set (n = 16)" → "(n = 20)" with the freeze note's composition table pasted in verbatim as the governing table; §4 step 6 and §8 checklist fresh row updated to 20/20; §3 tier table row 10 updated to "16/16 + fresh 20/20 + Kannada 8/8". Add an "Amendments" footer to the gate doc: amendment date, what changed, why, approved by whom.
3. Do **not** edit the sealed JSONs, the freeze note, or any GT. Hashes must still verify after the amendment.
4. Gate §6 rule 9 says amending the gate "invalidates the '10/10' label until the full gate is re-passed under the amended version". Nothing has passed yet, so the cost is zero — but state it in the amendment footer so the rule is honoured in form.
5. Rejected alternatives, for the record: (a) trimming 20→16 — selection bias + coverage loss, see above; (b) running all 20 but scoring only the first 16 — same problem, plus an arbitrary cut; (c) keeping the gate at 16 and treating F17–F20 as "extra, unscored" — unscored questions in a gate run invite cherry-picking and violate §6 rule 5's spirit; (d) re-commissioning a fresh 16 — destroys a valid blind freeze for no gain.

**Until the amendment is made, the fresh gate is ambiguous and no fresh run may be scored against it.** The v6 notebook's sealed runner must read the set size from the JSON (20) and report "20/20", not hardcode 16.

---

## 3. Rating formula discrepancy — both formulas computed

### 3.1 The two formulas

- **Gate formula (§2, frozen):** `Rating = 10 × [0.60·E + 0.15·Rm + 0.10·Pm + 0.075·C + 0.075·S] − 0.5·Fb − 1.0·Fp`, clamp [0,10], round to 1 decimal, then apply the §2 caps (lower of formula and cap wins). Uses **mean** precision/recall; exact match weighted 0.60; forbidden-before-recheck costs 0.5 each; prose-forbidden costs 1.0 each and caps at 5.0 if ≥1.
- **Working formula** (used for the v3 5.9 and v4r 7.7 numbers quoted in reports/memory): `Rating = 10 × [0.40·E + 0.30·micro-F1 + 0.15·C + 0.15·S]`. Uses **micro-F1** instead of mean P/R; no forbidden penalty; **no caps defined at all**. It is not in the gate doc anywhere.

### 3.2 Both-formula table (all inputs from filed live JSONs, except v5-predicted which is offline)

| Run | Exact E | Mean P / Mean R | Micro P / Micro R | Micro-F1 | Court C | Escalates S | Fb | Fp | **Gate formula** | **Working formula** |
|---|---|---|---|---|---|---|---|---|---|---|
| v1 (live 26 Nov 22:28) | 5/16 = 0.3125 | 0.656 / 0.492 | 0.875 / 0.368 | 0.518 | 10/16 = 0.625 | 11/16 = 0.6875 | 2 | not measured | **3.3** (3.2534; matches gate §2 worked example) | **4.8** (4.7731) |
| v3 (live 26 Nov 23:38) | 5/16 = 0.3125 | 0.673 / 0.866 | 0.671 / 0.895 | 0.767 | 11/16 = 0.6875 | 14/16 = 0.875 | 0 | not measured | **5.0** (5.0189) | **5.9** (5.8947) |
| v4r (live 27 Nov ~00:19) | 10/16 = 0.625 | 0.833 / 1.000 | 0.826 / 1.000 | 0.905 | 13/16 = 0.8125 | 14/16 = 0.875 | 0 | not measured | **7.3** (7.3486) | **7.7** (7.7454) |
| v5-predicted (NOT live) | 16/16 = 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 | 16/16 = 1.000 | 12/16 = 0.750 | 0 | not measured | **9.8 raw → capped 9.0** (9.8125) | **9.6** (9.625; no caps in this formula) |
| v5-pred, esc 14/16 (if H7/H15 expectations resolved to False) | 16/16 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 | 16/16 | 14/16 = 0.875 | 0 | not measured | **9.9 raw → capped 9.0** (9.9062) | **9.8** (9.8125) |
| v5-pred, esc 16/16 (hypothetical) | 16/16 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 | 16/16 | 16/16 | 0 | not measured | **10.0 raw → capped 9.0** | **10.0** (no caps) |

Worked arithmetic (gate formula):
- v1: 10×[0.60×0.3125 + 0.15×0.492 + 0.10×0.656 + 0.075×0.625 + 0.075×0.6875] − 0.5×2 = 10×0.4253 − 1.0 = 3.2534 → **3.3**.
- v3: 10×[0.1875 + 0.1299 + 0.0673 + 0.0516 + 0.0656] − 0 = 5.0189 → **5.0**.
- v4r: 10×[0.3750 + 0.1500 + 0.0833 + 0.0609 + 0.0656] − 0 = 7.3486 → **7.3**.
- v5-pred: 10×[0.6000 + 0.1500 + 0.1000 + 0.0750 + 0.0563] = 9.8125 → **9.8 raw**.

Caps applying to every row above (gate §2, each independently caps at 9.0): prose not measured (Fp NOT MEASURED on all live runs — classification only, no answer prose generated); fresh set not run; Kannada set not run; no confirmation re-run. Fb ≥ 1 cap (≤9.0) does not bind on v3/v4r (Fb = 0); the Fp ≥ 1 cap (≤5.0) does not bind (Fp unmeasured, not ≥1). **So every live run to date is capped at 9.0 regardless of formula output** — v1's 3.3 and v3's 5.0 and v4r's 7.3 are all below the cap, so the caps only bite on the v5 prediction.

### 3.3 Errors in the numbers currently in circulation

1. **v1 "3.3" was attributed to the working formula in the task brief — that is wrong.** 3.3 is the *gate*-formula value (it is the gate doc's own worked example). The working formula gives v1 **4.8**. The working formula appears to have been applied only from v3 onward, while v1's 3.3 was carried over from the gate doc. Anywhere memory/reports say "working formula: v1 3.3 / v3 5.9 / v4r 7.7", the v1 entry is misattributed.
2. **v3 and v4r are overstated by 0.9 and 0.4 respectively** under the frozen formula (5.9→5.0, 7.7→7.3). The overstatement comes from the working formula's heavier micro-F1 weight (0.30) and its lack of a forbidden penalty — v3's recall-heavy profile (mean R 0.866, micro-F1 0.767) scores better under micro-F1 than under the gate's mean-recall/mean-precision split.
3. **The v5 "9.6" prediction is uncapped.** The v5 report's 9.6 is a working-formula number with no caps applied. Under the gate formula the same prediction is 9.8 raw and **9.0 after caps**. Quoting 9.6 without the cap misstates what the system could claim even if the live run matches the prediction exactly.

### 3.4 Recommendation — the gate formula governs, the working formula is retired

- **The gate formula (§2) is the only rating from now on.** It is frozen; gate §6 rule 9 forbids changing the metric definitions, formula, or targets mid-tuning; gate §2 itself says "The formula is frozen; no run may be re-scored under a different formula." The working formula has no standing in any frozen document and no caps, which lets it report 9.6/10.0 for a system with unmeasured prose, unrun fresh/Kannada sets, and no confirmation — exactly the over-claim the caps exist to prevent.
- **Re-score all past runs under the gate formula and correct the record:** v1 **3.3** (unchanged), v3 **5.0** (was 5.9), v4r **7.3** (was 7.7). Memory and the coordinator log should be corrected; the filed JSONs need no change (they record metrics, not ratings — but any MD that states a rating must be annotated, not silently edited; add a dated correction note).
- **Cell 8 of the v6 notebook must compute the gate formula** (it currently does not compute any §2 rating — see §6). The working formula must not appear in any v6 artefact except in this lane file as a historical note.
- **What this does to the "reach 9/10" target (set 2026-11-27 ~07:05 IST, minimum 9/10):** under the gate formula + caps, **9.0 is the ceiling until prose is measured, fresh + Kannada pass, and the confirmation re-run passes**. A live v5 run matching its prediction (16/16, 16/16 court, 12/16 escalates) would rate **9.0 (capped)**, which *meets* the 9/10 minimum — but it must be reported as "9.0, capped — not 10/10", with the four unmet conditions listed. It is not 10/10, and the 9.8 raw formula output must never be quoted without the cap. Conversely, a v5 live run that falls short of 16/16 (e.g. H5 custody aux 0.2189 flipping — see §4.4) drops below 9.0 fast: at 15/16 exact with otherwise identical metrics the gate formula gives 10×[0.5625+0.15+0.10+0.075+0.0563] = 9.44 raw, still capped 9.0; at 14/16 it gives 9.06 raw, still capped 9.0; at 13/16 it gives 8.69 raw — below the 9/10 target. So the 9/10 target tolerates at most ~2 non-exact questions on the current set, *provided* court stays 16/16 and escalates ≥12/16.
- **Separate problem the formula change exposes:** G14 latency fails on v4r (see §5.4). The rating formula does not include latency, so a 9.0 capped rating can coexist with a failed G14 row — but the 10/10 *claim* requires every gate row including G14. The 9/10 target and the 10/10 claim must be tracked separately: rating 9.0 (capped) ≠ gate passed.

---

## 4. Confirmation re-run protocol (G15)

Gate §4 step 9: "After G1–G14 pass on all three sets in one run, re-run all three sets in a second independent live Colab run with zero code changes between runs. Both runs must pass every row. Only then may 10/10 be claimed."

### 4.1 Preconditions — the confirmation run may not start until ALL of these hold

1. Run 1 (the gate pass) is filed complete per §4.10 (JSON + MD, run number, date, notebook link + SHA-256, code version, §2 rating with arithmetic, §8 checklist ticked).
2. Run 1 passed **every** gate row G1–G14 on **all three sets** (current 16, fresh 20 as amended per §2, Kannada 8) **and** prose Fp = 0 measured (G12) — a run with Fp NOT MEASURED cannot be a gate pass, because the prose cap would already hold it at 9.0.
3. The H7/H15 escalate-expectation decisions and the HMA 27 GT decision (§1.3 item 5) are resolved and recorded *before* run 1 — they cannot be resolved between run 1 and run 2, because that would be a GT/scorer change.
4. G14 latency passes on run 1 (currently failing — see §5.4). If run 1 passes sections but fails latency, it is not a gate pass and there is nothing to confirm.

### 4.2 What "zero code changes" means — the frozen artefact list

Between run 1 and run 2, **all** of the following must be byte-identical (SHA-256 recorded for each in both run files):

| Artefact | How verified |
|---|---|
| Notebook `.ipynb` actually uploaded to Colab | SHA-256 of the uploaded file, printed in both run MDs. Must match exactly. A re-exported notebook with identical cells but different metadata is a *different file* — re-verify, do not assume. |
| Builder script that produced the notebook (e.g. `build_laya_v6_*.py`) | SHA-256 in both run MDs. |
| Graph JSON (`laya-crpc-bns-section-decision-tree-v2.json`) | SHA-256 + the in-notebook assert (32/46/77) passing in both runs. |
| Phrasebook / prompts / thresholds / fact annotations / gate constants (GUARD_LIFT_BAR, GUARD_FULL_CEILING, THRESHOLDS, aux prompts, clause patterns) | All embedded in the notebook — covered by the notebook SHA-256. Any of these living in a separate file must be hashed separately. |
| Test-set files (current-16 Cell 6 GT/facts/expectations; sealed JSONs) | Sealed JSON SHA-256 re-verified immediately before run 2 and printed in the run MD; must match §1.1. Current-16 GT is frozen — any Cell 6 change is a code change. |
| Prose renderer + forbidden self-checker (Cell 9, once it exists) | Covered by notebook SHA-256; version string printed in both runs. |
| Model + snapshot | Same Laya checkpoint (PIXMELT snapshot dir / version string) and same `laya` package version, printed by Cell 0/5 in both runs. |
| Colab runtime | Fresh Colab process for run 2 (new runtime, not a re-run in the same session). Same hardware class as run 1 (CPU vs T4) — record which; if the class differs, record it as a deviation and justify why it does not invalidate the comparison (see §4.5). |

**What is NOT a code change:** the calendar date; the Colab session/machine identity; the run number and output filenames (these differ by definition). **What IS a code change (any one resets confirmation):** any notebook edit, re-export, builder edit, graph edit, threshold/prompt/phrasebook edit, GT or fact-annotation edit, prose-template edit, dependency version change, or re-running with a different sealed-set file.

### 4.3 Step-by-step protocol

1. **Freeze.** After run 1 is filed and verified as a full gate pass, the coordinator declares the freeze in the coordinator log: run-1 number, date, notebook SHA-256, builder SHA-256, graph SHA-256, sealed SHAs. No edits to any frozen artefact from this point.
2. **Re-verify before run 2.** Immediately before uploading, recompute all SHA-256s and confirm they match the run-1 record. Re-verify sealed JSON SHAs. If any hash differs, STOP — the confirmation is void before it starts; diagnose what changed.
3. **Fresh Colab process.** Upload the *same* `.ipynb` file (same SHA-256) to Drive, open in Colab, start a fresh runtime. Run cells 0–9 in order. Do not edit any cell in the browser. If a cell errors, do not patch it in place — stop, file the failed attempt as a run (see §4.6), and diagnose offline.
4. **Run all three sets in the same run, same order as run 1** (current 16, then fresh 20, then Kannada 8), plus prose generation + scoring for every question. Record per-question latency for every set.
5. **Download and file run 2** as `live-laya-colab-results-v6-confirmation.json/.md` (or the next versioned name — see §5.3 on numbering), with the full filing set in §4.7. The MD must state "ZERO CHANGES — confirmation re-run of run N" and list every frozen hash.
6. **Compare (see §4.4).** Both runs must pass every gate row independently. Then produce the comparison table (exact counts, per-question exact flags, TP/FP/FN, court, escalates, Fb, Fp, latency, and the full per-question score table diff).
7. **Decide.** Only if both runs pass every row AND the comparison shows no unexplained divergence (see §4.4) may 10/10 be claimed. File the claim with both run numbers cited.

### 4.4 How the two runs are compared — and what happens if run 2 differs

**Comparison table (mandatory in the run-2 MD):** for each set, run-1 vs run-2 exact count, mean P/R, micro P/R, TP/FP/FN, court, escalates, Fb, Fp, latency mean/max/total, §2 rating; plus a per-question diff of `stage1_final` scores and exact flags.

**Cases:**

| Case | Verdict | Action |
|---|---|---|
| Run 2 passes every row; per-question scores identical (or differing by ≤ 0.005 on every score, no exact-flag flips, no FP/FN changes) | **Confirmation PASSES.** 10/10 may be claimed (with both run numbers cited). | File the comparison table; claim 10/10. |
| Run 2 passes every row, but some per-question scores differ by > 0.005 (no exact-flag flips, same FP/FN/court/escalates) | **Confirmation PASSES with a reproducibility note.** The gate requires both runs to pass every row — they do. But the divergence must be explained in the run-2 MD (candidate causes: Colab hardware, torch nondeterminism, model-load variance) and the differing scores listed. If the divergence touches a margin question (see below), escalate to the coordinator before claiming. | File with the note; coordinator decides whether to claim or to run a third confirmation. |
| Run 2 fails any row (any set) | **Confirmation FAILS.** No 10/10 claim. The run-2 failure is filed as a run (never deleted, never re-run silently). | Diagnose from the run-2 JSON only. A fix (one change, gate §4 step 3) resets confirmation entirely: a new gate-pass run becomes the new run 1, and a fresh confirmation run 2 is required. The failed confirmation does not count as run 1 for any later pair. |
| Run 2 differs because of model nondeterminism (same code, different scores, exact flags flip) | **Treat as a reproducibility failure, not bad luck.** Do not average the two runs, do not pick the better run (gate §6 rule 8), do not re-run until a pass appears. | Investigate: torch determinism settings, `laya` version, Colab hardware class, snapshot identity. If nondeterminism cannot be eliminated, the system cannot be confirmed at 10/10 — report that honestly. The tightest margin is the prime suspect (see below). |
| Run 2 cannot run (Colab/login failure, cell error, timeout) | **Not a confirmation result.** File the attempt with the error and the frozen hashes. | Fix the infrastructure cause only (no system change), re-verify hashes, and attempt the confirmation again. An infrastructure fix is not a code change, but record it. |

**Margin watch — the scores that could flip run 2 (from v4r/v5 numbers):**

- **H5 custody aux 0.2189 vs threshold 0.20 — margin 0.0189.** The tightest margin in the system. The v5 report §7 item 6 already flags it: the live v5 run must report H5 custody final and confirm it is still ≥ 0.20. In the confirmation comparison, H5 custody final must be reported in *both* runs to 4 decimals. A flip here costs exact on H5 (16/16 → 15/16) and breaks the gate pass.
- **H1 stridhan clause-max 0.7545 (FP) vs H3 true stridhan clause 0.7868 — gap 0.032.** Any score-bar fix in this range is knife-edge; v5's evidence gate avoids the bar, but the underlying scores still sit 0.03 apart — report both in each run.
- **Single-issue guard bar 0.80 vs genuine aux-rescue cluster 0.8495–0.9018 — gap 0.0495.** The guard's headroom is small; the fresh-set validation in v5 §7 item 7 must be reported as a read-only diagnostic in the confirmation run (see §6.4).
- **Any per-question score within 0.05 of its firing threshold** must be listed in a "margin table" in every run MD from v6 onward, so a run-2 flip is never a surprise.

**No cherry-picking, ever:** the rating is the latest run's rating, not the best run's (gate §6 rule 8). If run 2 is worse than run 1, run 2 is the rating. Two passing runs are required; two *filed* runs are required even if the second fails.

### 4.5 Hardware / environment notes

- v1–v4r were all CPU runs (Colab CPU, ~29 s load, 36–133 s/question). The latency analysis recommends a T4 GPU run for G14 (mean ~8–12 s/question projected). **If run 1 is CPU and run 2 is T4 (or vice versa), that is an environment change, not a code change — but it must be declared as a deviation** in the run-2 MD with the reason, because latency (G14) and possibly scores could differ by hardware. Cleanest practice: run 1 and run 2 on the **same hardware class**. Decide the class before run 1 and record it in the freeze declaration (§4.3 step 1).
- Model nondeterminism on CPU vs GPU is a known risk for confirmation; if run 1 must be CPU (as all runs so far) and G14 can only pass on T4, the G14 problem must be solved *before* run 1 (call-count cuts or a T4 run-1 decision), not papered over between runs.

### 4.6 Filing requirements per run (gate §4.10 / §8)

Every run — pass or fail, gate-pass or confirmation — files **both** of these, next to the 2026-11-26 baseline files:

| File | Required contents |
|---|---|
| `live-laya-colab-results-<version>.json` | Full per-question records (see §6.2 for the field list), aggregate metrics, latency per question, `stage1_final` scores, `gated_out` reasons, sealed-set SHAs, frozen artefact hashes, run number, date/time IST, notebook link + SHA-256, builder SHA-256, graph SHA-256, model/package versions, hardware class. Sealed-question *wording* must never appear in the JSON (IDs + scores only — see §6.3). |
| `live-laya-colab-results-<version>.md` | Human-readable report: run number, date, change since previous run (or "ZERO CHANGES — confirmation re-run of run N"), §2 rating with full arithmetic shown, §8 checklist ticked per row (with actuals), margin table (§4.4), latency table, per-question table, comparison table (for run 2), and the frozen-hash list. A run that is not filed does not count. Failed runs are filed too. |

Additionally: append one row per run to the coordinator log's run table (§5.3), and record the §2 rating under the gate formula only.

### 4.7 Confirmation-specific filing

- Run 2's MD must contain the sentence "ZERO CHANGES — confirmation re-run of run <N>" and the complete frozen-hash list, with each hash marked match/mismatch against run 1.
- The comparison table (§4.4) is mandatory in run 2's MD, even if the runs are identical (state "identical" explicitly — do not omit the table).
- If confirmation passes, the 10/10 claim cites **both** run numbers, both dates, and both notebook SHAs.

---

## 5. Run filing audit (against gate §4.10 / §8)

### 5.1 Run-log table (corrected — see §5.3 for corrections to existing records)

| Run | Version | Date/time IST | Notebook (SHA-256) | Live? | Filed files | Exact | Micro-F1 | Court | Escalates | TP/FP/FN | Rating (gate formula) | Rating (working, historic) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | v1 (baseline) | 2026-11-26 22:28 | `live-laya-colab-test.ipynb` (SHA not recorded) | ✅ live, Colab CPU | JSON+MD in `browser_downloads/sess-2896751965/` | 5/16 | 0.518 | 10/16 | 11/16 | 21/3/36 | **3.3** | 4.8 |
| 1 | v3 (empty5) | 2026-11-26 23:38 | `live-laya-colab-test-v3-empty5.ipynb` — `548f9cfe…c51c0db` | ✅ live, Colab CPU | JSON+MD in `browser_downloads/sess-2896751965/` | 5/16 | 0.767 | 11/16 | 14/16 | 51/25/6 | **5.0** | 5.9 |
| 2 | v4r (residence-only) | 2026-11-27 ~00:19 | `live-laya-colab-test-v4r-residence-only.ipynb` — `7d67bd53…82f5` | ✅ live, Colab CPU | JSON+MD in `browser_downloads/sess-2184034649/` | 10/16 | 0.905 | 13/16 | 14/16 | 57/12/0 | **7.3** | 7.7 |
| — | v4 (residence + PRIMARY thresholds) | — | `live-laya-colab-test-v4-residence.ipynb` — `af1d6a5d…1a45b` | ❌ never run live | Notebook + `v4-change-log.md` only (build filed, no run) | — | — | — | — | — | — | — (predicted 6/16, ~6.4) |
| — | v4.1 (evidence-first) | — | `live-laya-colab-test-v4-1-evidence-first.ipynb` — `7453647c…b5baf` | ❌ never run live | Notebook + `v4-1-change-log.md` only | — | — | — | — | — | — | — |
| — | v5 (precision) | — | `live-laya-colab-test-v5-precision.ipynb` — `3121f742…979d7` | ❌ never run live | Notebook + builder + `v5-precision-report.md` (+ lanes A–D) only | — (predicted 16/16) | — (pred. 1.000) | — (pred. 16/16) | — (pred. 12/16) | — (pred. 57/0/0) | — (pred. 9.8 raw → 9.0 capped) | — (pred. 9.6) |
| — | Sealed fresh-20 | — | — | ❌ never run | — | — | — | — | — | — | — | — |
| — | Sealed Kannada-8 | — | — | ❌ never run | — | — | — | — | — | — | — | — |
| — | Prose (Fp) | — | — | ❌ never run | Renderer is a design doc only (`prose-renderer-design.md`); no Cell 9 exists | — | — | — | — | — | — | — |
| — | Confirmation (G15) | — | — | ❌ never run | — | — | — | — | — | — | — | — |

Full notebook/builder hashes verified by this lane (2026-11-27): v3 `548f9cfe30517270070197997e5ecfe475086dd720c1a31fbf103fb26c51c0db`; v4 `af1d6a5d4749bd1e72389885081cadcc13171ea0e28e16977776f69a56e1a45b`; v4r `7d67bd53033bb96b0c5a1f99b4c637975fdbdc91911a49c4c3ccd64432e382f5`; v4.1 `7453647c332a44062f72766474b3194ef1a24b218af2d2efa449d11f62c5b5af`; v5 `3121f742f24ac59d73924328a7c4ff685261351b65cab1eddf3e01df328979d7`; builders v3 `cc84192f…`, v4 `0d6706fb…`, v4.1 `381f0031…`, v5 `49149f1d…`.

### 5.2 What is missing

1. **v5 has no live run filed.** The v5-precision-report §5 numbers (16/16, 9.6) are offline predictions from v4r numbers, not results. Nothing in v5 may be quoted as measured until the live run is filed.
2. **No v4 live run.** v4 was built and validated, then superseded by the coordinator's v4r variant (thresholds reverted). The coordinator's plan was "v4r first, v4 second only as a falsification test of the threshold vector". That falsification run has never happened. It is optional — but if it is never run, the record should say "v4 falsification run: not run (superseded by v4r)" rather than leaving it as a pending row.
3. **No v4.1 live run.** Built, change-logged, never run. Same treatment: either schedule it or mark it superseded in the log.
4. **No sealed runs, no prose run, no confirmation run.** G2, G3, G12, G15 are all "not run".
5. **Coordinator log run table is stale.** Its last row is "Run 2 — v4 — pending build + live run". It has no row for the v4r live run (the actual run 2, 2026-11-27 ~00:19, 10/16, 7.3 gate / 7.7 working). Correct it: renumber so v4r is run 2, and add a row per future run.
6. **v1 notebook SHA not recorded.** The baseline notebook's hash was never filed. It cannot be re-verified now; note it as unrecoverable and ensure every notebook from v3 onward carries a hash (they do).
7. **v4r MD omits latency and the §2 rating computation.** The JSON has per-question `latency_s` (mean 57.6 s, max 133.3 s, total 921.6 s — see §5.4) but the filed MD has no latency row and no §8 checklist. Cell 8 does not compute the §2 rating (noted in the latency analysis). Every run MD from v6 onward must include both (see §6).

### 5.3 Run numbering rule (for v6 and beyond)

Run numbers are **global and sequential across versions, never reused, never per-version**: run 0 = v1, run 1 = v3, run 2 = v4r. The next live run (v5) is **run 3**; the v6 live run is **run 4**; the confirmation re-run takes the next number after the gate-pass run. Version labels (v5, v6) and run numbers are different things — a version may have zero live runs (v4, v4.1, v5 so far) and a run number belongs to exactly one live execution. The v6 notebook must print its run number in Cell 8 output and in the output filenames.

### 5.4 G14 latency — a failing gate row hiding in the filed JSONs

Computed by this lane from the filed per-question `latency_s` values:

| Run | Mean/question | Max/question | Full-run total (excl. load) | Model load | G14 (≤15 s / ≤30 s / ≤240 s / ≤60 s) |
|---|---|---|---|---|---|
| v1 | 11.77 s | 24.17 s | 188.4 s | 25.8 s | ✅ PASS |
| v3 | 56.09 s | 122.92 s | 897.5 s | 28.9 s | ❌ FAIL (all three) |
| v4r | 57.6 s | 133.32 s | 921.6 s | 29.0 s | ❌ FAIL (all three) |

v4r's latency is *worse* than v3's despite the precision fixes (the residence gate did not reduce call count). The latency analysis says zero-risk trims recover only ~25–35% and G14 cannot be restored on CPU; its realistic target is a recorded T4 GPU runtime (mean ~8–12 s/question) or reporting CPU as a G14 failure. **Consequence for validation:** G14 is a gate row (G1–G14 must all pass for the gate pass that precedes confirmation). Until G14 is addressed — T4 run, call-count cuts, or a documented decision — **no run can be a gate pass, and the confirmation protocol in §4 cannot start**, whatever the section scores are. This must be decided before run 1 of the confirmation pair, not between run 1 and run 2. The v6 notebook must surface latency aggregates in Cell 8 output (mean/max/total/load) so the failure is visible in the MD, not buried in per-question JSON.

### 5.5 Current blocker (not a validation finding, but it gates all live work)

As of 2026-11-27 ~07:08 IST, live Colab runs are blocked on the Google password for nivedhbhat15 (Google rejected the saved password twice; the only other option offered was a passkey, which the cloud browser cannot use). The same block affects the Gemini consultation. No live run — v5, v6, sealed, or confirmation — can be executed until the parent resolves Colab access. This lane's work is unaffected (offline), but the run-log gaps in §5.2 cannot close until access is restored.

---

## 6. What the v6 notebook must contain for validation

### 6.1 Run numbering and hash recording

- **Run number:** a `RUN_NUMBER` constant (next sequential global number — see §5.3) and a `VERSION` string, printed in Cell 0 output and embedded in the output filenames (`live-laya-colab-results-v6-run<N>.json/.md`). Never reuse a run number; a re-executed notebook is a new run number, not an overwrite.
- **Hash recording:** Cell 0/5 must print: notebook version string, builder script SHA-256 (recorded at build time — a notebook cannot reliably hash itself in Colab, so the builder writes its own SHA and the notebook file's SHA into a `BUILD_INFO` cell at build time), graph JSON SHA-256 + the 32/46/77 assert result, `laya` package version, torch version, model snapshot identifier, hardware class (CPU/T4), and Colab runtime start time. Cell 8 must copy all of these into the output JSON's `run_info` block and the MD header.
- **Change log line:** Cell 8 output must include one line: the single change since the previous run (gate §4 step 3 — one change per cycle), or "ZERO CHANGES — confirmation re-run of run N".

### 6.2 Per-question fields (every set, every run)

Each per-question record must contain: `id`, `exact`, `precision`, `recall`, `tp`, `fp`, `fn`, `pred_labels`, `gt_labels`, `forbidden_before_recheck`, `forbidden_after_recheck`, `forbidden_proposed_before_gate`, `gated_out` (list of distinct reason strings, one per veto — never merged), `court_live`, `court_expected`, `court_correct`, `escalates_live`, `escalates_expected`, `escalates_correct` (+ the typed-escalation kinds that fired), `fired_issues`, `fired_clause`, `fired_source`, `stage1_final` (full per-issue score map — needed to re-derive any threshold decision and to diff run 1 vs run 2), `money_fact`, `gold_fact`, `custody_claim` / `custody_gated` (with pre-gate final), `single_issue_guard` (`{armed, dominant, dominant_full, blocked}`), `residence_claim` / `residence_gated`, `latency_s`, `error` (null or the error string; model errors score 0 on every component per §2).

Aggregate block must contain: exact, mean P/R, micro P/R, micro-F1, TP/FP/FN, court, escalates, silent count, Fb, Fp (or the literal string `NOT MEASURED` with the reason), model-error count, **latency aggregates (mean/max/total/load)**, the **§2 gate-formula rating with full arithmetic shown** (not the working formula), the §8 checklist with actuals, the margin table (§4.4), and the frozen-hash list.

### 6.3 Sealed-set runner (must not leak sealed wording into tuning artefacts)

- **Separate runner section** (new cells after Cell 8, or a clearly delimited Cell 10–11 block) that loads the sealed JSONs **by path only**, verifies both SHA-256s against §1.1 **before** running, and aborts with a printed error if either hash mismatches. It must run the *same* Cell 7 pipeline (same thresholds, same gates, same Stage 2) — no sealed-specific code paths, no sealed-specific thresholds.
- **No leakage rules (hard):**
  - The runner's output JSON/MD must contain **question IDs and scores only — never question text**. Do not print, log, or embed any sealed `question` string, paraphrase, or distinctive phrase in any output, notebook cell output, or tuning artefact.
  - Sealed questions must never be added to `TEST_SET`, the phrasebook, prompts, aux prompts, examples, or tests. The runner must load them into a separate variable (`SEALED_FRESH`, `SEALED_KANNADA`) that no tuning code reads.
  - The guard-bar validation (v5 §7 item 7) runs as a **read-only diagnostic** inside the sealed runner: report (a) how many fresh single-issue questions arm the guard, (b) whether any fresh true second issue with full ≤ 0.01 and lift < 0.80 is blocked (recall loss → bar must drop or guard becomes flag-and-escalate), (c) whether any fresh FP with full ≤ 0.01 and lift in [0.20, 0.80) survives. **Do not tune the bar on the fresh set** — any change goes through the general-cause procedure (gate §4 step 7) and both sets are re-run.
  - The F20 human-lawyer rule (§1.2) must be implemented in the scorer: F20 `escalates: true` with empty GT/court scores as correct when the system escalates to a human lawyer without inventing a section. The same rule must not be generalised to F19 (`escalates: false`).
  - The runner must report the set size it read from the JSON (20) and score G2 as 20/20 per the §2 amendment — never hardcode 16.
- **Sealed-run gating:** the sealed runner must refuse to run until the current-16 gate passes (gate §4 step 6) — enforce with an explicit guard: the notebook must not execute the sealed block unless a flag is set by the operator *after* the current-16 pass is filed. Log the flag and the operator's confirmation in the run MD. (Kannada baseline measurement is the exception per §4 step 8 — a Kannada *baseline* may run at any time to establish a number; tuning on Kannada begins only after English current + fresh pass.)

### 6.4 Other v6 notebook requirements

- **Compute the §2 gate-formula rating in Cell 8** (currently not computed). Print the full arithmetic (each term) and the caps applied, and the final capped rating. Do not compute or print the working formula.
- **§8 checklist output:** Cell 8 must print the full gate checklist table with actuals and pass/fail per row, so the MD can be generated from cell output without hand-computation.
- **Margin table:** Cell 8 must print every per-question issue score within 0.05 of its firing threshold, with the margin — H5 custody (0.2189 vs 0.20) must appear here in every run.
- **Prose:** if Cell 9 (prose renderer + forbidden self-checker) is not yet built, Cell 8 must print `prose_forbidden_mappings: NOT MEASURED` and the MD must carry the ≤9.0 cap. Do not leave Fp blank or zero by default — an unmeasured Fp is not Fp = 0.
- **Latency:** Cell 8 must print latency mean/max/total/load and a G14 pass/fail line (§5.4).
- **No silent changes:** the builder must assert before editing (as Lane D did for v5) and the build note must record the exact cell diff vs the previous version.

---

## 7. Decisions needed from the parent/coordinator (before the v6 live run)

1. **Approve the gate amendment** (G2 fresh 16 → fresh 20, §2) and record it per the procedure in §2.2. Until then the fresh gate is ambiguous.
2. **Confirm the rating-formula correction** (gate formula governs; v3 = 5.0, v4r = 7.3; working formula retired) and correct memory/coordinator-log entries.
3. **Resolve H7/H15 escalate expectations** (v5 §6) and the **HMA 27 GT dispute** (legal-decisions-v4.md) before the gate-pass run — both affect scoring and neither may change between run 1 and run 2.
4. **Decide the G14 latency route** (T4 GPU run vs call-count cuts vs documented CPU failure) — no gate pass is possible while G14 fails (§5.4).
5. **Resolve Colab access** (Google password for nivedhbhat15 rejected; passkey unusable in the cloud browser) — all live runs are blocked until then (§5.5).
6. **Record the sealed-set rater identity** (freeze-note addendum) and arrange the independent Kannada-fluency GT check (§1.3 items 1–2).

---

## 8. Sources used (offline)

- `laya-10-10-gate-definition.md` (§0 baseline, §1 gate rows, §2 formula + caps, §4 validation loop, §5 definitions, §6 anti-overfitting, §8 checklist)
- `sealed/sealed-sets-freeze-note.md` + recomputed SHA-256s + metadata-only structural reads of `sealed-fresh-20.json` / `sealed-kannada-8.json` (counts, tags, facts, script fractions — no question wording read or copied)
- `v5-precision-report.md` (§5 prediction, §6 escalates, §7 item 7 guard-bar validation)
- `overnight-coordinator-log.md` (run history, sealed delivery, legal decisions, prose/latency findings, v4/v4r provenance)
- Filed live results: `browser_downloads/sess-2896751965/` (v1, v3 JSON+MD), `browser_downloads/sess-2184034649/` (v4r JSON+MD) — aggregates and per-question `latency_s` recomputed by this lane
- Notebook/builder SHA-256s computed by this lane for v3, v4, v4r, v4.1, v5
