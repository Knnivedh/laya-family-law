# v5 PRECISION — merged report (round 2 of the overnight 10/10 run)

**Status: PLAN + BUILD SPEC. No live Colab run yet.** This merges Lanes A (aux audit), B (custody), C (single-issue guard), D (notebook skeleton). Lane D Phase 2 applies this spec to the v5 notebook; the parent runs Colab next.

**Starting point — v4r LIVE (verified, Colab 2026-11-27 ~00:19 IST):** exact 10/16, mean P/R 0.833/1.000, micro P/R 0.826/1.000, micro-F1 0.905, TP/FP/FN 57/12/0 out of 57 GT. Recall 1.000 — zero sections missed. Court 13/16, escalates 14/16, forbidden 0, model errors 0/16. Rating by the frozen formula (0.4·exact + 0.3·micro-F1 + 0.15·court + 0.15·escalates): **7.7/10**. Exact: K0, H2, H4, H5, H8, H9, H10, H11, H12, H13.

**The gap:** 6 questions not exact, ALL precision-only, recall 1.000 on every one. 12 FP total, 0 FN.

## 1. Per-FP diagnosis (which mechanism fired each of the 12 FPs)

All values from the v4r JSON `raw_live_runs` (full = full-question score; clause-max / aux-max / final / fired_source as recorded). Firing rule (Cell 7): `final = max(clause_max, full, aux_max)`, fires iff `final >= THRESHOLDS[issue]`.

| Q | FP sections | FP issue | Full | Clause-max | Aux-max | Final | Fired via | Guilty mechanism |
|---|---|---|---|---|---|---|---|---|
| H1 | BNS 316, HMA 27 | stridhan | 0.4948 | **0.7545** | — (no stridhan aux) | 0.7545 | clause | Clause "My husband has not given me any money for three months." on the stridhan prompt — "not given money" read as "cash held". Full 0.4948 was correctly just under 0.50; clause-max lifted it over. Court wrong (HMA 27 adds Family Court). |
| H3 | BNSS 144, PWDVA 20 | maintenance | 0.0001 | 0.0433 | **0.1218** | 0.1218 | aux | Aux "he gives no money for me and my child" (L185) 0.1218 on a gold-only question. NOT one bad prompt: 3 maintenance aux prompts independently clear 0.10 (L183 0.1114, L185 0.1218, L186 0.1205) — the pool has a background floor. Deleting L185 leaves L186 at 0.1205. |
| H7 | BNSS 144, PWDVA 20 | maintenance | 0.0 | **0.1971** | 0.0335 | 0.1971 | clause | Clause "The hospital did not give us one." — "did not give" bleeds into "gives no money". Court wrong (Magistrate added, GT Registrar). |
| H15 | BNSS 144, PWDVA 20 | maintenance | 0.0001 | 0.0298 | **0.1269** | 0.1269 | aux | Same L185 prompt as H3 (0.1269); again 3 prompts independently clear 0.10 (L181 0.1007, L185 0.1269, L186 0.1108). |
| H6 | GWA 1890, HMGA s.6, WELFARE | custody | 0.1602 | 0.1712 | **0.3669** | 0.3669 | aux | Aux "I want my daughter to stay with me" scored 0.3669 against the FULL question — cannot distinguish "stay *with me*" (custody) from "stay *in the house* with my daughter" (residence). Residence already fires correctly via its own aux (0.7318). Court wrong (Family Court added). |
| H14 | GWA 1890 | custody route | — (custody legitimately fires, final 0.7895) | — | — | — | Stage 2 | `stage2()` adds the GWA set unconditionally on custody firing, then adds HMA 26 on top when proceeding_pending — keeping BOTH primaries. Custody firing is correct; routing is wrong. |

**Lane A headline correction:** only 4 of the 8 financial FPs are aux-driven (H3, H15); the other 4 are clause-max-driven (H1 stridhan, H7 maintenance). Any fix touching only aux prompts can remove at most 4 FPs. The common root cause is the max-pool itself: full-question scores on H3/H7/H15 separate perfectly (0.0001/0.0/0.0001); the clause/aux max-pool manufactures the fires.

**Lane B headline correction:** H6's custody fire does NOT come from the full-question score — it is solely aux-driven (0.3669). The same aux prompt is the ONLY thing keeping H5's custody alive (final 0.2189, entirely aux-driven, margin 0.0189 over threshold) — so aux prompts must not be weakened or reworded.

## 2. Merged fix (v5 ships all four — they are all vetoes, so they compose)

Every v5 fix is a **veto**: it can only force a final score to 0.0, never fire an issue. No new issue can fire in v5 that did not fire in v4r, so no new sub-choice runs and no new FN can be created by a fix *except* through a wrongly-applied veto on a true issue — which is exactly what the guardrail checks below rule out per fix. Vetoes are independent (each reads scores/clauses/facts, not another veto's output) except for the dominance computation, which MUST use raw full-question scores before any veto (Lane C pseudocode does this — preserve it). If the live run regresses, the `gated_out` reason string names the culprit veto — attribution is preserved by construction despite bundling.

Apply in Cell 7, after final scores are computed and after the existing residence fact gate, before the firing loop, in this order (each veto: force `final[name] = 0.0`, update `rec['stage1_final'][name]`, append a distinct `gated_out_a` entry — never merge reason strings):

### Fix 1 — Evidence gates (Lane A, mechanism (c); kills H1/H3/H7/H15 financial FPs, 8/8)
New Cell 6 fact fields, same frozen-annotation style as `residence_claim`:
- `money_fact` (bool) — True iff the question states money not given / asks for periodic money / states a need for money for self or child / asks how much money per month / **explicitly asks for "maintenance" by name** (H8 rests on this — a narrower "money-not-given only" rule would wrongly gate H8 out).
- `gold_fact` (bool) — True iff the question states gold / cash / gifts given at marriage held by the husband's side, or sold / not returned. Holding, not demanding, is the grounding fact (H10's gold fact holds although demand has not yet been made; `demand_made` stays separate).

Gate as veto, score threshold still applies on top: maintenance fires only if `money_fact` is True AND final ≥ 0.10; stridhan fires only if `gold_fact` is True AND final ≥ 0.50.

Verified separation on the 16 (checked question by question): `money_fact` True exactly on the GT-maintenance set {K0, H1, H5, H6, H8, H9, H10, H11, H13, H14}; `gold_fact` True exactly on the GT-stridhan set {K0, H3, H10, H15}. Full table for Cell 6 (False = complement):

| Q | money_fact | gold_fact |
|---|---|---|
| K0 | True | True |
| H1 | True | **False** (blocks stridhan FP; true maintenance kept) |
| H2 | False | False |
| H3 | **False** (blocks maintenance FP) | True |
| H4 | False | False |
| H5 | True | False |
| H6 | True | False |
| H7 | **False** (blocks maintenance FP) | False |
| H8 | True (explicit "maintenance" ask) | False |
| H9 | True | False |
| H10 | True | True |
| H11 | True | False |
| H12 | False | False |
| H13 | True (school fees count as money) | False |
| H14 | True | False |
| H15 | **False** (blocks maintenance FP) | True |

### Fix 2 — Custody gate (Lane B, option (c); kills H6 custody FPs, 3/3)
Deterministic per-clause veto after scoring (modelled on the v4 residence gate). Custody fires only if some clause matches a who-gets-the-child pattern AND is not itself a residence co-location clause. Patterns (verbatim from Lane B §2.2):
- `who will get my` (K0, H2)
- `(want|wish|need) … my (son|daughter|child) to stay with me` within 30 chars (H5, H14)
- `custody|guardianship|guardian` (explicit term; none in the 16 — future-proofing)
- `take (him|her|them) away` (H2 backup)
- Residence co-location exclusion: `stay in the (house|home) … with my (son|daughter|child)` — such a clause cannot carry a custody claim.

If no clause qualifies, force `final['custody'] = 0.0`, record `rec['custody_claim']` (bool) and `rec['custody_gated']`, append `gated_out` entry. Record the pre-gate final too (as the residence gate does for fired_clause/fired_source).

Rejected: (a) split-trigger extension — aux is scored on the full question, so splitting cannot change the 0.3669 aux score; (b) residence aux prompt — already exists and already scores 0.7318 on H6. Threshold rise rejected: H5's true 0.2189 < H6's false 0.3669 — ranges inverted, no threshold separates them.

### Fix 3 — Single-issue guard (Lane C; kills H3/H7/H15 maintenance FPs, 6/6 — redundant with Fix 1, kept as defence-in-depth)
Arm iff exactly **one** issue clears its **own** per-issue threshold on the full question alone (divorce judged on its asked signal only, ≥ 0.45). Then, for any other issue with full-question score **≤ 0.01**, require lift = max(clause_max, aux_max) ≥ **0.80** to fire, else block. Dominant issue never guarded. Constants: `GUARD_LIFT_BAR = 0.80`, `GUARD_FULL_CEILING = 0.01`. Residence uses the R0 full score. Record `rec['single_issue_guard']` {armed, dominant, dominant_full, blocked} + one `gated_out` entry per blocked issue.
- Bar 0.80: 0.60 above the highest target lift (H7, 0.1971), just below the genuine aux-rescue cluster (0.8495–0.9018). Ceiling 0.01: 100× above the worst FP full (0.0001), 7.7× below the lowest true fired full (K0 maintenance 0.0773).
- Why both layers: the per-issue dominance test disarms K0/H5/H6/H10/H13 by construction (their second issues already clear their own low thresholds on full alone); the ceiling is the second layer. A guard without the dominance test would kill H4 (residence aux 0.6474 < 0.80, no issue clears its threshold on full alone — guard does not arm). A ceiling of ≤ 0.50 would break H14 custody (full 0.1321, lift 0.7895 < 0.80) — tested and rejected.
- **in_scope gate: REJECTED.** H13's in_scope final (0.0985) is *below* H7's (0.113) — no final-score cutoff separates them; a full-score cutoff rests on a 0.0205 gap; in_scope is False on 5 exact questions. Keep in_scope as court-fallback input only.

### Fix 4 — H14 exclusive primary route (Lane B; kills H14 GWA FP, 1/1)
In `stage2()` (Cell 7 lines 262–265), replace the unconditional GWA-set add with an exclusive branch: if `proceeding_pending` → keep `{hma-26, hmga-1956-s6, welfare-principle}`; else → `{gwa-1890, hmga-1956-s6, welfare-principle}`. HMGA s.6 + WELFARE ride with either primary. Keep the existing recheck (lines 298–300) as Layer-B defence-in-depth. H14 is the only question with proceeding_pending=true, so every other custody question takes the unchanged else-branch by construction.

### NOT shipped in v5 (recorded, with reasons)
- **(a) Maintenance per-source bar 0.30** (Lane A safety-net): verified 13/16 alone, zero recall risk, but subsumed by Fix 1 and it leaves H1 OPEN (stridhan clause bar 0.77 rejected as knife-edge: margins 0.016/0.017). Keep as the v5 offline diagnostic cross-check (expect 13/16) and v6 fallback. Do NOT apply the 0.30 bar in the v5 notebook — redundant with the gates. Any bar must be maintenance-specific, never global: a global 0.30 aux bar would kill H5 custody (true, aux 0.2189) and create the run's first FNs.
- **(b) Gemini's 4-option financial-claim choice** (maintenance_only / stridhan_only / both / neither): v6 fallback, NOT v5. Reasons: option definitions were never transmitted verbatim (consultation file has only the four labels; planning-note definitions are flagged drafts — Lane A drafted wordings are in its §5, marked as drafts, not Gemini quotes); `both` collapsing to a single label on K0/H10 is an untested recall risk (a single-label collapse creates the first FN); its cutoff is unknown (must be fitted live in the 0.35–0.85 range). Same projected numbers as (c) if perfect (14/16 alone) but contingent on untested model behaviour.
- **Keyword token guards** (maintenance fires only with a money token, etc.): rejected as primary — violates the Cell 7 hard rule against keyword picks, fails on paraphrase, cannot run on the sealed set. (The custody gate in Fix 2 is a veto on explicit-claim patterns, not a pick — same shape as the shipped residence gate; every pick still comes from `agent.predict()`.)
- **H6 split-trigger extension** (split on "and to stay/live"): recorded as a possible companion, not the fix — aux is scored on the full question, so it cannot change the 0.3669 score. Do not bundle.
- **Residence 2-option choice gate** (planning note §5): not in v5 — after money/custody, before the sealed run. The frozen `residence_claim` annotation's generalisation gap stands (see §5).

## 3. Mechanism decision (why (c) is v5 primary)

Lane A recommends (c) evidence gates; the merger adopts it, with Lane C's guard as defence-in-depth (it fixes the same H3/H7/H15 FPs by an independent mechanism, so a failure in either mechanism still leaves the other) and Lane B's fixes for the non-financial FPs.
1. (c) is the only mechanism fixing all 8 financial FPs with no knife-edge and no recall risk on the 16 (verified by offline re-score that first reproduces the v4r baseline exactly: 10/16, 57/12/0, F1 0.905, court 13/16, escalates 14/16).
2. It has a built precedent in this codebase (v4.1 residence evidence gate; v4r `residence_claim`).
3. It fixes H1 structurally — H1's stridhan FP cannot be fixed by any score bar without overfitting (0.032 gap to H3's true clause 0.7868) and stridhan has no aux prompts.
4. Its weakness is shared and stated: hand-annotated facts restate ground truth on the 16 and do not generalise; the sealed fresh-20 needs model-extracted facts (planned, unbuilt, error rate unmeasured). Same limitation already applies to the shipped residence gate — it is the round's established methodology, not a new deviation.

## 4. Guardrail check (merged — which exact questions each fix risks)

| Fix | Risks | Proof it does not break them (v4r numbers) |
|---|---|---|
| Fix 1 gates | K0/H10 `both` must stay; H8/H9/H11 maintenance; H3/H15 stridhan | money_fact True exactly on GT-maintenance set, gold_fact True exactly on GT-stridhan set (verified question by question). K0: money True ("gives no money", "not enough") + gold True ("gold … will not return it"). H10: money True + gold True (holding, not demanding). H8: explicit "maintenance" ask counts. H13: school fees count as money. H5 custody aux 0.2189 untouched (gates touch only maintenance/stridhan). |
| Fix 2 custody gate | H5 custody (aux 0.2189, margin 0.0189); H2/K0/H14 custody | Gate is score-neutral (veto only, never changes a score) — H5 passes via its stay-with-me clause; H2/K0 via "who will get"; H14 via stay-with-me clause. H10/H13/H12 have no matching clause and were already unfired. |
| Fix 3 guard | K0/H5/H10/H13 true second issues with low fulls (0.0773–0.4212) and lifts < 0.80 (H5 custody 0.2189, H10 maintenance 0.6772, H14 custody 0.7895); H4 residence aux 0.6474 | Guard never arms on K0/H5/H6/H10/H13 (≥2 issues clear their own thresholds on full alone); H4 never arms (no issue clears its threshold on full alone). Full per-question table in Lane C §5 — all 10 exact questions unchanged. |
| Fix 4 H14 route | H2/H5/K0 GWA route | H14 is the only proceeding_pending=true question; all others take the unchanged else-branch. |
| All fixes | H12 must stay empty | No fix can fire anything (all vetoes/drops); H12 kept stays `[]`. Divorce firing on H12 stays section-neutral (Stage 2 drops HMA 13). |

## 5. Predicted v5 outcome (offline, from v4r numbers — NOT a live result)

| Metric | v4r live | v5 predicted (merged) |
|---|---|---|
| Exact | 10/16 | **16/16** (H1, H3, H6, H7, H14, H15 all fixed) |
| TP / FP / FN | 57 / 12 / 0 | **57 / 0 / 0** |
| Micro P / R / F1 | 0.826 / 1.000 / 0.905 | **1.000 / 1.000 / 1.000** |
| Court correct | 13/16 | **16/16** (H1, H6, H7 fixed) |
| Escalates correct | 14/16 | **12/16** — see §6, NOT a section regression |
| Rating (frozen formula) | 7.7/10 | **9.6/10** (0.4·1.0 + 0.3·1.0 + 0.15·1.0 + 0.15·0.75) |

Per-question prediction: every question exact. K0, H2, H4, H5, H8, H9, H10, H11, H12, H13 unchanged; H1 exact (stridhan gated, court fixed); H3 exact (maintenance gated + guard); H6 exact (custody gated, court fixed); H7 exact (maintenance gated + guard, court → Registrar only); H14 exact (GWA dropped); H15 exact (maintenance gated + guard).

Why this prediction is stronger than a projection: **all v5 fixes are vetoes/drops** — no new issue fires, so no unrun sub-choice outcome is involved. The predicted kept sets follow deterministically from the v4r fired set minus the vetoed issues (H6's custody sub-choice simply does not run; H14's GWA removal is a deterministic Stage 2 branch). The live run still must confirm the v4r scores reproduce — especially H5 custody aux 0.2189 (margin 0.0189).

## 6. Escalates 12/16 — what it is and what it is not (OPEN decisions for the parent)

Fixing H7+H15's sections removes their only escalation reason under current Cell 8 typed scoring, and the escalate expectations (True on both) are unchanged because ground truth is not to be changed:
- **H7:** kept = {births-deaths-act-1969} only → no quantum/demand/court escalation → False vs expected True. H7's expectation was already OPEN (fully answerable, no named reason).
- **H15:** kept = stridhan only, demand_made=True → no demand escalation → False vs expected True. Same shape as H7.
- H3 keeps escalates True via demand (demand_made=False). H1 keeps True via quantum. H2 and H4 were already wrong in v4r and no v5 fix touches them (H2: custody+residence fired, no quantum/court/demand; H4: residence-only, no quantum/court/demand — the typed-escalation kinds do not cover custody/residence-only questions at all).

**Do NOT "fix" this by re-attaching the quantum boilerplate** — the boilerplate was content-wrong on a birth-certificate question and a stridhan-sold question. The section score is v5's deliverable; the escalate expectation is a separate open decision. Consequences: even with 16/16 sections and 16/16 courts, the frozen rating caps at **9.6/10** while escalates reads 12/16. If the parent resolves H7/H15 expectations to False (fully answerable, no named reason), escalates reads 14/16 and the rating is 9.8/10; H2/H4 would still need a typed-escalation design for custody/residence-only questions (v6 work). The 10/10 gate requires escalates 16/16 too — v5 cannot reach 10/10 on the frozen rating without those decisions. **Do not change Cell 6 escalate_expected in v5.**

## 7. OPEN items (not resolved, not hidden)

1. **H7/H15 escalate expectations** — see §6. Parent decision.
2. **H2/H4 escalates wrong** — typed-escalation kinds do not cover custody/residence-only questions. v6 design question.
3. **Hand-annotation generalisation** — money_fact/gold_fact (Fix 1), residence_claim (v4r), and the custody-gate patterns (Fix 2) all restate ground truth on the 16 and do not generalise to unseen phrasings. The sealed fresh-20 needs model-extracted facts / pattern extension from rater-approved paraphrases only. Until then, any claim that v5 generalises is capped. Lane B's specific gap: an unseen custody paraphrase ("I want my child to live with me", "who gets the kids") matches no pattern and would be gated out — v5 must report `custody_claim`/`custody_gated` per question so it is visible.
4. **H1 under mechanism (a) only** — OPEN if v5 had shipped (a) instead of (c); moot under (c), recorded for the record.
5. **H5 sub-choice contradiction** (custody sub-choice A "HMA s.26" with no proceeding pending, silently ignored by Stage 2) — untouched; belongs to a Stage 2 lane / later run. No score impact.
6. **H5 custody aux margin 0.0189** — the run's tightest margin; the live v5 run must report H5 custody final and confirm it is still ≥ 0.20.
7. **Guard bar/ceiling validation** — 0.80/0.01 are in-sample on n=16. Validate on sealed fresh F1–F20: report how many fresh single-issue questions arm the guard, whether any fresh true second issue with full ≤ 0.01 and lift < 0.80 is blocked (recall loss → bar must drop or guard becomes flag-and-escalate), whether any fresh FP with full ≤ 0.01 and lift in [0.20, 0.80) survives. Do not tune the bar on the fresh set.

## 8. What Lane D must do (Phase 2 spec — sent separately, summarised here)

Apply Fixes 1–4 in Cell 7 (Cell 8 only for: FP-by-issue metric, `v4r_baseline_reference`, gated-out summary surfacing), using the builder's `apply_merged_fixes(nb)` with assert-before-edit on every anchor; flag back on any mismatch, never improvise. Cell 6: add `money_fact`/`gold_fact` per the §2 table (values verified above). Also fix the two doc-only defects from Lane D's build note: Cell 7 header stale divorce thresholds (0.40/0.13 → 0.45/0.12) and Cell 8 header stale v3 baseline. Keep: HMA 25 gate, court fallback, typed escalations, esc_live incl. 'demand', graph assert 32/46/77, no-keyword-fallback rule, GT/facts/expectations unchanged (except the two added fact fields). Validate: nbformat.validate PASS, compile Cells 7–8 PASS, Cells 0–6 diff vs v4r is exactly the two added fact fields (plus nothing else), TEST_SET ids and GT ids unchanged, builder re-run byte-identical. Record per-question in the live run: `money_fact`, `gold_fact`, `custody_claim`/`custody_gated` (pre-gate final too), `single_issue_guard` {armed, dominant, blocked}, `gated_out` with distinct reasons per veto, `fired_source`/`fired_clause` as computed.

## 9. Colab steps to run v5 next (for the parent)

1. Lane D Phase 2 finishes the notebook; verify its sha256 and build-note change log.
2. Upload `live-laya-colab-test-v5-precision.ipynb` to Drive (nivedhbhat15@gmail.com), open in Colab; CPU works (~16 min, Cell 7 ~15 min), T4 optional.
3. Run cells 0–8 in order. Cell 5 prompts for `laya-crpc-bns-section-decision-tree-v2.json` (from `files/laya-crpc-bns-section-decision-tree-v2.json` or `colab_bundle/`); asserts 32/46/77. Cell 7's HMA 25 shadow test must print PASS before the live loop.
4. Cell 8 downloads `live-laya-colab-results-v5-precision.json/.md` — file both, log exact/micro-F1/court/escalates against the §5 prediction (16/16, 1.000, 16/16, 12/16). Any deviation: report which veto's `gated_out` entry explains it before merging anything further.
5. Do NOT run the sealed fresh-20 in this round — v5 is validated on the 16 only; the fresh set is the final gate, not a tuning set.
