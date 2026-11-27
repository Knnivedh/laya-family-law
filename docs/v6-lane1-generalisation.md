# v6 Lane 1 — Per-FP generalisation audit of the v5 vetoes

**Lane:** 1 (per-FP generalisation) · **Round:** v6 deep-dive, round 3 of the overnight 10/10 run ·
**Method:** offline only. No browser, no Colab, no notebook touched, no ground truth changed.
**Sources:** `v5-precision-report.md` §1–§4, `v5-laneA-aux-audit.md`, `v5-laneB-custody.md`,
`v5-laneC-single-issue-guard.md`, the v4r live JSON
(`browser-download-20261126T185447.300061282Z-0-live-laya-colab-results-v4r-residence-only.json`,
`raw_live_runs`), `laya-10-10-gate-definition.md` §6, Cell 7 of
`live-laya-colab-test-v4r-residence-only.ipynb` (line numbers below refer to that Cell 7),
`lanes/custody.json` (sub-choice node definition).

**Starting point (verified live, v4r 2026-11-27 ~00:19 IST):** exact 10/16, micro P/R 0.826/1.000,
micro-F1 0.905, TP/FP/FN 57/12/0, recall 1.000, court 13/16, escalates 14/16. All 12 FP are
precision-only, on 6 questions: H1 ×2 (stridhan), H3 ×2, H7 ×2, H15 ×2 (maintenance), H6 ×3
(custody), H14 ×1 (GWA route). v5 (built, NOT live-measured) predicts 16/16 via four vetoes.

**Headline verdict, blunt:** v5's *mechanisms* mostly generalise; v5's *shipped implementations*
mostly do not. The maintenance vetoes (Fix 1 money gate, Fix 3 guard) are genuine mechanisms
whose score evidence separates widely on the 16 — but they currently run on hand-annotated facts,
which restate ground truth and are overfit by construction. The custody veto (Fix 2) is overfit
as shipped: its four regex patterns cover exactly the phrasings in the 16 and fail 0/3 of the
must-not-gate paraphrases in §1.4. The H14 route fix (Fix 4) is a general legal rule riding on a
hand-annotated boolean fact. The guard's 0.80 bar looks safe (0.60 margin) but its real margin
is 0.0105, because genuine rescues below the bar survive only via the dominance test and the
ceiling. And the tightest number in the whole run is not a v5 constant at all — it is H5's
custody aux score, 0.0189 above threshold, which no v5 fix touches.

**Scope note on the paraphrases in §1:** every paraphrase below is written by this lane as a
*test item*, not a tuning input. Per gate §6 rules 2 and 4, none of them may be added to the
phrasebook, prompts, or pattern lists, and none may be used to tune a threshold. Before any
use, a non-tuning rater must re-write (or approve) the paraphrase set. "Predicted correct" in
§1 means "the mechanism as specified implies this outcome" — it is reasoning, not a measured
result. No paraphrase below has a live Laya score.

---

## 0. Per-FP verdict table (the 12 FPs)

| # | FP | v5 veto | Mechanism general? | Shipped implementation general? | Verdict |
|---|---|---|---|---|---|
| 1–2 | H1 stridhan ×2 (BNS 316, HMA 27) | Fix 1 `gold_fact` gate | Yes — "no gold-held fact, no stridhan" is a legal grounding rule, not a fitted number | **No** — hand annotation restates GT; the score pattern it replaces (full 0.4948 vs 0.50 threshold) is knife-edge (0.0052) | **OVERFIT as shipped; generalises only via model extraction (§2.2)** |
| 3–4 | H3 maintenance ×2 (BNSS 144, PWDVA 20) | Fix 1 `money_fact` gate + Fix 3 guard (redundant) | Yes, both — full-question score separates 0.0001 vs ≥0.0773; aux pool background floor (~0.12) is a property of the pool, not the question | **No** — money gate runs on a hand fact | **GENERALISES as mechanism; needs model extraction (§2.1)** |
| 5–6 | H7 maintenance ×2 | Fix 1 `money_fact` gate + Fix 3 guard (redundant) | Yes, both — "did not give" clause bleed is a general max-pool failure mode, and the full score is exactly 0.0 | **No** — money gate runs on a hand fact | **GENERALISES as mechanism; needs model extraction (§2.1)** |
| 7–8 | H15 maintenance ×2 | Fix 1 `money_fact` gate + Fix 3 guard (redundant) | Yes, both — same aux-floor mechanism as H3 | **No** — money gate runs on a hand fact | **GENERALISES as mechanism; needs model extraction (§2.1)** |
| 9–11 | H6 custody ×3 (GWA 1890, HMGA s.6, WELFARE) | Fix 2 regex custody gate | **No** — the gate *is* four literal patterns fitted to the 16's phrasings; no existing score separates H5 (true, 0.2189) from H6 (false, 0.3669) — all three score channels are inverted (§2.3) | **No** | **OVERFIT — needs model extraction via a new choice prompt; do not ship the regex as the long-term gate** |
| 12 | H14 GWA 1890 ×1 | Fix 4 exclusive primary route in `stage2()` | Yes — "exactly one primary route" is a legal rule from the exact plan §3.2, not a fitted threshold | Partially — the branch is general; its input `proceeding_pending` is hand-annotated | **GENERALISES as a rule; fact source must be model-extracted (§2.4) or rater-verified** |

Net: **7 of 12 FPs are killed by general mechanisms running on overfit inputs** (Fix 1 money/gold
gates); **3 of 12 by an overfit mechanism** (Fix 2 regex); **1 of 12 by a general rule on an
overfit input** (Fix 4); **1 FP family (H3/H7/H15) is additionally covered by a general mechanism
with thin real margins** (Fix 3 guard — see §3). Nothing in this table changes the v5 prediction
of 16/16 on the 16. It changes what that prediction is *worth* on the 17th question.

---

## 1. Paraphrase stress tests (3 should-gate + 3 must-not-gate per FP family)

Reading guide: **SHOULD-GATE** = the veto must block the FP (the paraphrase carries no true
claim for that issue). **MUST-NOT-GATE** = the veto must let a true claim through (blocking it
creates a new FN — worse than the FP it was built to kill, because it breaks recall 1.000).
"Veto handles it?" is judged against the mechanism *as specified in the v5 report*, including
its known gaps. All outcomes below are predictions, not measurements.

### 1.1 Family H1 — stridhan FP, Fix 1 `gold_fact` gate (clause 0.7545 on a money-only clause)

The FP mechanism: the clause *"My husband has not given me any money for three months."*
scores 0.7545 on the stridhan prompt ("gold, cash or gifts … held by the husband"), because
"not given money" reads as "cash held". Full-question stridhan is 0.4948 — 0.0052 under threshold.

**SHOULD-GATE (money-only, no gold — veto must block stridhan):**

| # | Paraphrase | Veto handles it? |
|---|---|---|
| S1 | "My husband stopped sending money for the children last month." | **Yes, predicted correct** — no gold/cash/gift-held claim; hand `gold_fact`=False; model extraction (§2.2) should also return False (stridhan full would be low; no held-asset clause). |
| S2 | "I earn very little and he gives nothing for the house." | **Yes** — money-need only. Same shape as H1's own clause, one paraphrase step further from "not given money". |
| S3 | "He has not paid a rupee for our daughter's expenses in a year." | **Yes, but note the trap** — "rupee" is a money token; a *keyword* gold guard would misread "paid a rupee" as cash-held. The fact gate (money vs gold-held) handles it; a token guard would not. This is why Lane A rejected token guards. |

**MUST-NOT-GATE (true stridhan — veto must let it fire):**

| # | Paraphrase | Veto handles it? |
|---|---|---|
| N1 | "My mother gave me ornaments at my wedding and my in-laws kept them." | **RISKY — predicted failure mode.** "Ornaments" is the ordinary layman word for gold jewellery, but neither the hand rule ("gold / cash / gifts") nor the main stridhan prompt names it. A rater hand-annotating would mark `gold_fact`=True; a model extraction whose prompt lists only gold/cash/gifts may return False → new FN (2 sections lost). The extraction prompt must cover ornaments/jewellery explicitly (§2.2). |
| N2 | "He sold the jewellery my parents gave me at my marriage." | **Probably yes, with the same caveat as N1.** "Sold" + "given at marriage" matches the H15 shape ("sold my gold") with "jewellery" substituted for "gold". Passes iff the extraction prompt covers jewellery/sold. |
| N3 | "My streedhan is with my husband's family and they will not return it." | **RISKY.** Uses only the legal term "streedhan" (transliteration) with no gold/cash/gift noun. The main stridhan prompt contains none of the words "stridhan/streedhan" — a question phrased purely in the legal term may score low on every existing prompt. Hand annotation handles it; model extraction may not. This is the mirror image of the H8 lesson (explicit term "maintenance" had to be counted as grounding for money). |

Family verdict: the gate's *logic* generalises (money-only ≠ gold-held is a real distinction in
any phrasing). Its *implementation* generalises only as far as the fact extraction's vocabulary
covers layman synonyms (ornaments, jewellery, streedhan). The stridhan full-question score
itself does NOT generalise as a separator: H1's 0.4948 sits 0.0052 under a 0.50 threshold, so
any fresh money-only question scoring 0.51 on stridhan-full fires on score alone.

### 1.2 Family H3/H15 — maintenance FP, Fix 1 `money_fact` gate + Fix 3 guard (aux-max 0.1218/0.1269)

The FP mechanism: three maintenance aux prompts independently clear the 0.10 threshold on
gold-only questions (H3: L183 0.1114, L185 0.1218, L186 0.1205; H15: L181 0.1007, L185 0.1269,
L186 0.1108). The aux pool has a background floor of ~0.08–0.13 on non-money questions. The
full-question scores (0.0001/0.0001) separate perfectly.

**SHOULD-GATE (no money ask — veto must block maintenance):**

| # | Paraphrase | Veto handles it? |
|---|---|---|
| S1 | "My mother gave me a necklace at my wedding and my in-laws kept it." | **Yes, both vetoes agree.** Money gate: no money fact. Guard: stridhan dominant, maintenance full ~0.0001, lift ~0.12 < 0.80 → blocked. Double coverage. |
| S2 | "How do I get my son's school admission certificate?" | **Yes.** Non-money admin question (H7 shape, different document). Money gate False; guard blocks (single dominant, full ~0, lift < 0.80). |
| S3 | "He took my wedding bangles and sold them without telling me." | **Yes.** Gold-only (H15 shape, "bangles" for "gold"). Money gate False; guard blocks. Note "bangles" is another jewellery synonym the *stridhan* side must still recognise (cf. §1.1 N1) — the two gates pull in opposite directions on vocabulary. |

**MUST-NOT-GATE (true maintenance — veto must let it fire):**

| # | Paraphrase | Veto handles it? |
|---|---|---|
| N1 | "He gives nothing for our children's books and uniforms each month." | **RISKY — the sharpest test in this family.** Money need expressed as books/uniforms, with no word "money/maintenance/fees". Hand rule ("states a need for money for self or child") — a rater would likely mark True, but it is one paraphrase step past H13 ("school fees count as money"). Model extraction from the maintenance full score is unmeasured here; the school-fees aux (L183) may match "books/uniforms" only weakly. If extraction returns False → 2-section FN. |
| N2 | "What am I owed every month for myself and my child?" | **Probably yes.** "Owed every month" paraphrases "ask for monthly money" (the main maintenance prompt) without any money token. Full-score extraction (§2.1) should catch it; a keyword extraction would miss it. This paraphrase discriminates extraction designs. |
| N3 | "I need maintenance but I don't have his salary slips." | **Yes.** In-set shape (H8 verbatim family); explicit term "maintenance" is grounding by the v5 rule. |

Family verdict: **generalises, with one known vocabulary edge (N1).** The full-question
separation (max false 0.0001 vs min true 0.0773) is the widest in the run, and the guard agrees
independently. The risk concentrates in money-needs expressed without money words (N1).

### 1.3 Family H7 — maintenance FP, Fix 1 `money_fact` gate + Fix 3 guard (clause 0.1971)

The FP mechanism: the clause *"The hospital did not give us one."* scores 0.1971 on the
maintenance prompt — "did not give" bleeds into "gives no money". Full-question maintenance is
exactly 0.0. This is the purest demonstration that the clause-max pool manufactures fires: a
2-word overlap ("did not give") on a birth-certificate question clears a 0.10 threshold.

**SHOULD-GATE (no money — veto must block maintenance):**

| # | Paraphrase | Veto handles it? |
|---|---|---|
| S1 | "The school did not give us the transfer certificate." | **Yes, both vetoes agree.** Same "did not give" bleed, different institution/document. Money gate False; guard blocks (single dominant, full ~0, lift ~0.20 < 0.80). |
| S2 | "The hospital did not give us the discharge summary." | **Yes.** Same shape as H7 verbatim, different document. |
| S3 | "My husband's office did not give him his relieving letter." | **Yes.** "Did not give" bleed with no money and no birth certificate at all — tests whether the vetoes depend on the birth-certificate dominant (they don't; the money gate is dominant-independent). |

**MUST-NOT-GATE (true maintenance mixed with a "did not give" clause — veto must let it fire):**

| # | Paraphrase | Veto handles it? |
|---|---|---|
| N1 | "The hospital did not give us the bill, and my husband gives no money for the baby's medicines." | **Money gate: yes. Guard: RISKY.** Money fact is True ("gives no money for medicines"), so Fix 1 passes it. But the guard is the danger: if birth/hospital is single-dominant and the maintenance *full* score lands ≤ 0.01 (the money mention lives in a short clause, exactly the H1/H5 pattern where full under-scores a true issue), the guard blocks maintenance unless its lift clears 0.80. A clause lift of ~0.35 would be blocked → FN. This is the guard's known failure shape (§3.1), now with a concrete instance. |
| N2 | "He did not give me money for three months." | **Yes.** In-set (H1 clause verbatim family); money fact True. |
| N3 | "I need money every month and the hospital did not give the certificate." | **Yes.** Money fact True; maintenance full should clear 0.01 (money is in the main clause, not a subordinate one), so the guard never engages. |

Family verdict: **generalises.** The "did not give" bleed is a property of the clause-max
mechanism, not of H7's wording, so S1–S3 are safe. The residual risk is N1's shape — a true
second issue hiding behind a ≤0.01 full score — which is a guard-scope risk, not a money-gate
risk (see §3.1).

### 1.4 Family H6 — custody FP, Fix 2 regex custody gate (aux 0.3669)

The FP mechanism: the custody aux *"I want my daughter to stay with me"* scores 0.3669 against
the full H6 question (*"…to stay in the house with my daughter"*), because Laya cannot
distinguish "stay *with me*" (custody) from "stay *in the house* with my daughter" (residence).
The gate blocks custody unless some clause matches a who-gets-the-child pattern and is not a
residence co-location clause. Patterns (Lane B §2.2): `who will get my`; `(want|wish|need) … my
(son|daughter|child) to stay with me` (≤30 chars); `custody|guardianship|guardian`;
`take (him|her|them) away`; exclusion `stay in the (house|home) … with my (son|daughter|child)`.

**SHOULD-GATE (residence co-location only — veto must block custody):**

| # | Paraphrase | Veto handles it? |
|---|---|---|
| S1 | "I just want to live in the house with my son." | **Yes — but for the wrong reason.** "Live in the house" matches neither the exclusion regex (needs "stay in the house/home") nor any custody pattern, so the gate blocks by *absence of a pattern*, not by recognising co-location. Correct outcome, fragile mechanism: the gate's "block" here is indistinguishable from its "block" on a true claim phrased differently (see N1–N3). |
| S2 | "I want to stay in our home with my children." | **Yes — same fragility, plus a concrete bug.** The exclusion regex requires singular `son|daughter|child`; "children" (plural) does not match it, so the exclusion never fires. The gate still blocks (no custody pattern matches "stay in our home with my children"), but only by absence. **Plural gap:** the same plural breaks the stay-with-me pattern — "I want my children to stay with me" matches NO custody pattern (see N1). |
| S3 | "I don't want a divorce, I only want money and to remain in the house with my daughter." | **Yes — by absence again.** "Remain in the house" matches neither the exclusion ("stay") nor any custody pattern. Correct outcome; the gate recognised nothing. |

**MUST-NOT-GATE (true custody — veto must let it fire):**

| # | Paraphrase | Veto handles it? |
|---|---|---|
| N1 | "I want my child to live with me." | **NO — predicted FN.** "Live with me" ≠ "stay with me" (the pattern's verb is fixed); "my child to live" does not match `(want\|wish\|need) … my (son\|daughter\|child) to stay with me`. No other pattern matches. The gate blocks a true custody claim → 3-section FN (GWA 1890, HMGA s.6, WELFARE). This is the most ordinary custody phrasing in layman English, and it fails. |
| N2 | "Who gets the kids after a divorce?" | **NO — predicted FN.** Pattern needs "who will get my" + singular child noun. "Who gets the kids" fails on the verb ("gets" vs "will get"), the possessive ("the" vs "my"), and the plural ("kids"). Three independent mismatches on one short question. |
| N3 | "Can I keep my son with me?" | **NO — predicted FN.** "Keep my son" is a natural custody ask; no pattern contains "keep". Gate blocks. |

Family verdict: **OVERFIT — 3/3 should-gate correct (all by absence, none by recognition),
0/3 must-not-gate correct.** The gate's should-gate "successes" are vacuous: it blocks S1–S3
because it recognises nothing in them, which is the same behaviour that blocks N1–N3. A veto
that cannot distinguish the two classes is not a discriminator; it is a whitelist of four
phrasings. The plural gap (S2/N1: "children/kids") is a fixable morphology bug *within* the
regex approach — adding `(children|kids)` is general layman language, not test-question
wording — but patching plurals and verbs ("live", "keep", "gets") one at a time is exactly how
a whitelist becomes a second phrasebook. The fix is model extraction (§2.3), not more patterns.

### 1.5 Family H14 — GWA route FP, Fix 4 exclusive primary route

The FP mechanism is not a firing error: custody legitimately fires (final 0.7895), and Stage 2
adds the GWA set unconditionally and then HMA 26 on top when a proceeding is pending, keeping
both primaries. Fix 4 branches on `proceeding_pending`: pending → HMA 26 (+ HMGA s.6, WELFARE);
not pending → GWA 1890 (+ HMGA s.6, WELFARE).

**SHOULD-KEEP-GWA (no proceeding — must route GWA, not HMA 26):**

| # | Paraphrase | Veto handles it? |
|---|---|---|
| S1 | "We never filed any case. Who will get my daughter?" | **Yes.** `proceeding_pending`=False → else-branch, GWA kept. Correct by construction. |
| S2 | "I want a divorce and custody of my son, no case filed yet." | **Yes.** Divorce asked, no proceeding — the H5 shape. Else-branch, GWA kept. This is the case Fix 4 exists to protect against the H5 sub-choice error (§4). |
| S3 | "My husband and I are separated, no court case, I want my child to stay with me." | **Yes.** No proceeding → GWA. (Custody firing itself depends on Fix 2/§2.3 for the "stay with me" phrasing; routing is correct conditional on firing.) |

**MUST-KEEP-HMA-26 (proceeding pending — must route HMA 26, not GWA):**

| # | Paraphrase | Veto handles it? |
|---|---|---|
| N1 | "My divorce case is going on and I want my son to stay with me." | **Yes.** In-set (H14 verbatim family); proceeding True → HMA 26 branch. |
| N2 | "The Family Court case is pending and I need interim custody of my daughter." | **Yes, conditional on the fact.** "Case is pending" paraphrases "case is already going on". Hand annotation: True. Model extraction (§2.4) must recognise "pending" as proceeding-pending — untested. |
| N3 | "My HMA case is already in court; who gets my child till it ends?" | **Yes, conditional on the fact.** "HMA case … in court" is a proceeding-pending paraphrase using the Act abbreviation. Hand annotation: True. Model extraction must not require the word "divorce" — the proceeding fact is about a case existing, not about divorce being asked. |

Family verdict: **generalises as a rule.** The branch encodes a legal exclusivity (exactly one
primary), and every paraphrase above routes correctly *given a correct fact*. The entire risk
is in the fact: `proceeding_pending` is currently hand-annotated, and §4 shows the model
actively conflates "divorce asked" with "proceeding pending" (custody sub-choice A on H5/H6).
Fix 4's correctness on unseen questions is therefore exactly the correctness of the
proceeding-pending extraction (§2.4) — the branch contributes no additional generalisation risk
of its own.

---

## 2. Model-extracted facts — design to replace hand annotation

**Design constraint (from the task):** use only mechanisms already in the notebook —
`agent.predict` on the full question, on clauses, and on aux prompts (`noul` and `choice` nodes).
No new model, no keyword fallback for *picks* (Cell 7 hard rule); the regex custody gate is a
veto, not a pick, and §2.3 proposes replacing it with a model choice for exactly that reason.

**Governing principle for all four facts — fail open, flag, never silently veto on uncertainty:**
whenever extraction lands in its uncertain band, the fact defaults to **True** (the veto does
not fire; the score decides) **and** the question is flagged (`extraction_uncertain=True`,
`escalate=True`). Rationale: (i) every v5 fix was designed not to break recall 1.000 — a wrong
veto creates the run's first FN, which is strictly worse than leaving the FP it was built to
kill, because the FP is a known, bounded, already-measured quantity (12) while a wrong veto is
a new failure class; (ii) the system's history is under-firing (baseline 36 FN vs 3 FP), and
the gate weights recall (0.15) above precision (0.10); (iii) the flag makes the uncertainty
visible and reviewable instead of silent — a flagged question does not count as a clean exact
in the run report (report exact-clean and exact-with-flags separately). If the flagged rate on
any set exceeds ~10%, the extraction is not fit and the gate must not ship as a hard veto.

**Calibration rule (applies to every threshold below):** the numeric bands below are set from
the current-16 *distribution* (max false vs min true on each signal), never from a single
question (gate §6 rule 3). They are **provisional** — each must be confirmed by a live dry run
that runs the extraction on the 16 and reports model-vs-hand agreement per fact before the
extraction is wired as a veto. A dry-run disagreement is a finding to report, not a threshold
to quietly re-fit: re-fitting a band to absorb a dry-run miss on one question is threshold
fitting on n=16 and is forbidden. If the dry run shows a band does not separate, the answer is
a better prompt, not a moved number.

### 2.1 `money_fact` — primary signal: maintenance FULL-question score (the clean channel)

Evidence from v4r `raw_live_runs` (maintenance `stage1_probs`):

| | Value |
|---|---|
| True money set (GT-maintenance: K0, H1, H5, H6, H8, H9, H10, H11, H13, H14) — full scores | 0.0773 (K0) … 0.898 (H6); **min 0.0773** |
| False money set (H2, H3, H4, H7, H12, H15) — full scores | 0.0000 … 0.0001; **max 0.0001** |
| Separation | **773×** (0.0001 → 0.0773); absolute gap 0.0772 |

The full-question maintenance prompt separates perfectly on the 16 — the FP mechanism is the
clause/aux max-pool, not the full prompt. Cross-checks that do NOT separate as cleanly (record
for audit, do not use as primary): maintenance aux-max — true min 0.2861 (H5) vs false max
0.1269 (H15), gap 0.1592, margins 0.073/0.086 at a 0.20 midpoint (too thin for a primary);
maintenance clause-max — true min 0.1432 (H11) vs false max 0.1971 (H7), **inverted** (a false
clause out-scores a true clause), so clause-max must never feed extraction.

**Procedure:**
1. Read `full_maint = stage1_probs['maintenance']` (already computed; zero new model calls).
2. **Certain-True band:** `full_maint ≥ 0.05` → `money_fact=True`. (0.05 sits 500× above the
   false max 0.0001 and 1.5× below the true min 0.0773. All 10 true in-set are ≥ 0.05.)
3. **Certain-False band:** `full_maint ≤ 0.002` → `money_fact=False`. (0.002 sits 20× above
   the false max and 38× below the true min. All 6 false in-set are ≤ 0.002.)
4. **Uncertain band** `(0.002, 0.05)`: run a NEW dedicated 2-option Laya `choice` node on the
   **full question** (not clauses — the clause channel is the leaky one):
   - Option Y: "The question asks for periodic money or maintenance for the wife or a child,
     or states that money is not given / needed for the wife or a child, or asks how much
     money per month — including an explicit ask for 'maintenance' by name, and including
     school fees, medicines, books or uniforms as money needs."
   - Option N: "The question asks for no periodic money or maintenance and states no need
     for money for the wife or a child."
   - Choice-Y score ≥ 0.60 → True; ≤ 0.40 → False; in (0.40, 0.60) → **uncertain → default
     True + flag** (governing principle above).
5. **Honest limitation (state it, don't hide it):** this extraction is *not* independent
   evidence — it re-thresholds the same full-question prompt that fires maintenance. It
   removes the hand annotation and it kills the max-pool leak (which is the actual FP
   mechanism), but a fresh question that the full prompt mis-scores breaks the fire and the
   fact together (correlated failure). The choice node in step 4 is the only independent leg,
   and it is untested: its 0.35–0.85 separable range is Gemini's claim (Lane A §5), not a
   measurement. The dry run must report the choice distribution on all 16, and N1/N2 of
   §1.2 ("books and uniforms", "what am I owed") are the discriminating test items for it.

### 2.2 `gold_fact` — primary signal: stridhan FULL-question score, with a choice leg in the gap

Evidence (stridhan `stage1_probs`):

| | Value |
|---|---|
| True gold set (K0, H3, H10, H15) — full scores | 0.8929 (H10) … 0.9332 (H3); **min 0.8929** |
| False gold set (all others) — full scores | **max 0.4948 (H1)**, next 0.2546 (H9), then 0.1146 (H12) |
| Separation | gap 0.4948 → 0.8929, absolute 0.3981; midpoint ≈ 0.69 |

Unlike money, the stridhan full prompt is NOT clean: H1's money-only question scores 0.4948,
0.0052 under the firing threshold. The full score alone cannot be trusted as the fact — a fresh
money-only question at 0.51 would both fire stridhan and pass a full-score fact gate.

**Procedure:**
1. Read `full_strid = stage1_probs['stridhan']` (already computed).
2. **Certain-True band:** `full_strid ≥ 0.70` → `gold_fact=True`. (Margins: 0.19 below the
   true min 0.8929, 0.21 above the false max 0.4948.)
3. **Certain-False band:** `full_strid ≤ 0.60` → `gold_fact=False`. (Margin 0.11 above H1's
   0.4948 — the thin side; H1 is the binding constraint, and it is a single question, so
   this band edge must be confirmed by the dry run, not asserted as safe.)
4. **Uncertain band** `(0.60, 0.70)`: run a NEW dedicated 2-option `choice` node on the full
   question:
   - Option Y: "The question states that gold, cash, jewellery, ornaments or gifts given to
     the wife at marriage are held by the husband or his family, or were sold, or have not
     been returned — including where the question uses only the word 'stridhan'/'streedhan'
     for them."
   - Option N: "The question states no gold, cash, jewellery, ornaments or gifts given at
     marriage held by the husband or his family, and none sold or not returned."
   - Choice-Y ≥ 0.60 → True; ≤ 0.40 → False; in (0.40, 0.60) → **uncertain → default True
     + flag** (governing principle; the flag, not the default, is the safety).
   - The vocabulary in option Y (jewellery/ornaments/streedhan) is general layman language
     for the gold concept, added because §1.1 N1/N3 show the shipped vocabulary misses it.
     It is a prompt-design decision to be validated on the rater-written paraphrase set, not
     a tuning input from any test question.
5. **Why the choice leg matters more here than for money:** for money the full score already
   separates 773×; for gold the full score's false side reaches 0.4948, so the fact gate's
   safety on unseen money-only questions depends on the choice node, not on the full score.
   If the dry run shows the choice node cannot separate H1 (0.4948-shape) from H3/H10/H15
   with margin ≥ 0.10, `gold_fact` extraction is not fit and v6 must keep the hand fact
   (with the overfit disclosed) rather than ship a broken extraction.

### 2.3 `custody_claim` — NO existing score separates; new per-clause choice node required

This is the strongest negative finding in this lane. From v4r `raw_live_runs` (custody):

| Channel | True custody that must pass (H5) | False custody that must block (H6) | Separates? |
|---|---|---|---|
| Full-question | 0.1098 | 0.1602 | **No — inverted** (false > true) |
| Clause-max | 0.0957 | 0.1712 | **No — inverted** |
| Aux-max ("I want my daughter to stay with me") | 0.2189 | 0.3669 | **No — inverted** (false exceeds true by 0.148) |

The inversion is structural: H6's residence co-location sentence matches the custody aux
*better* than H5's genuine custody sentence does. No threshold, band, or combination of the
three existing channels can extract `custody_claim` — any cutoff that blocks H6 also blocks
H5, and vice versa. (This is the same inversion Lane B used to reject a threshold rise.)
Therefore the regex gate cannot be replaced by re-thresholding; it can only be replaced by a
**new signal**.

**Procedure (new mechanism, to be dry-run before wiring as a veto):**
1. Add a NEW 2-option Laya `choice` node, run **per clause** (not on the full question —
   full-question scoring is precisely what conflates the residence sentence with the custody
   claim; the clause is the unit that separates them, cf. Lane B §2.4):
   - Option A (custody claim): "This clause asks who will get or look after the child, or
     asks for custody / guardianship of the child, or asks for the child to stay or live
     with the speaker."
   - Option B (not a custody claim): "This clause only mentions where the child lives or
     stays (for example staying in the house with the child), or asks for no custody or
     guardianship of the child."
   - Per clause, record `choice_A` score. A clause counts as a custody claim iff
     `choice_A ≥ 0.60` on that clause.
2. `custody_claim=True` iff **any** clause counts, **excluding** clauses the residence
   co-location pattern matches (keep the Lane B exclusion regex as a *secondary* check on
   the choice's output, not as the gate itself — it catches the known H6 shape while the
   choice is being validated).
3. **Uncertain:** if the best clause's `choice_A` is in (0.40, 0.60) on every clause →
   **uncertain → default True + flag** (governing principle). If no clause reaches 0.40 →
   `custody_claim=False` (certain).
4. **Dry-run gate before wiring:** run the new choice node on the 16 in a live Colab dry-run
   cell (no veto wired). Required to pass before the choice replaces the regex as the gate:
   H5/H14/K0/H2 must return claim=True with best-clause `choice_A ≥ 0.70`; H6/H10/H13/H12
   must return claim=False with best-clause `choice_A ≤ 0.50` (margin ≥ 0.10 on both sides
   of the 0.60 cutoff). If it fails, keep the regex gate for v6 (disclosed as overfit) and
   do not pretend the choice works.
5. **Interim regex repair (if the regex is retained for v6):** fix the plural morphology bug
   (§1.4 S2): extend both the stay-with-me pattern and the residence exclusion to
   `(son|daughter|child|children|kids)`. This is a morphology fix in general layman language,
   not a test-question wording. It does NOT fix N1–N3 ("live with me", "who gets the kids",
   "keep my son") — say so explicitly; do not present the plural fix as a generalisation fix.
6. **What must NOT be done:** do not weaken, reword, or delete the custody aux prompts to
   "fix" H6 — H5's custody lives entirely on the daughter aux (0.2189, margin 0.0189); any
   aux change risks the run's first FN (Lane A §3, Lane B §4).

### 2.4 `residence_claim` and `proceeding_pending` — the two facts Fix 4 and the v4 gate depend on

**`residence_claim`** (v4r shipped gate; same overfit class as money/gold, predates v5).
Evidence — residence R0 full does NOT separate: true (K0 0.265, H4 0.1267, H6 0.2173, H13
0.4212) vs false max **0.8247 (H2)** and 0.4882 (H5) — inverted. Residence clause-max also
inverted (false H2 0.8464 > true max 0.7674). But residence **aux-max DOES separate** on the 16:

| | Value |
|---|---|
| True residence set — aux-max | 0.6474 (H4) … 0.8905 (K0); **min 0.6474** |
| False residence set — aux-max | **max 0.3813 (H2)**, next 0.2143 (H5) |
| Separation | gap 0.3813 → 0.6474, absolute 0.2661; midpoint 0.51 |

Procedure: `residence_claim=True` iff residence aux-max ≥ 0.50 (margins 0.147 above the true
min, 0.119 above the false max — the false side is thin, H2 at 0.3813). Uncertain band
(0.40, 0.60) → dedicated residence choice node ("does this question ask to stay/live in the
shared house, or complain of being thrown out / locked out?" vs "no residence claim"), same
0.60/0.40 cutoffs, uncertain → default True + flag. Note the aux-max signal is scored on the
full question, so it shares the full-question conflation risk — the choice leg is the
independent check. The v6 dry run must report residence aux-max on all 16 against the hand
fact; any disagreement is a finding.

**`proceeding_pending`** (Fix 4's input; also gates HMA 24/26 rechecks). Evidence — the
existing `divorce_pending` noul score does NOT separate: true (H14 only) 0.9202 vs false max
**0.6445 (H2)**, then 0.4490 (H12), 0.4095 (H5). A 0.78 cutoff would separate on the 16, but
H2 at 0.6445 is 0.136 below it — thin, and it is a single aux phrase doing the work of a fact.
Worse, §4 shows the model conflates "divorce asked" with "proceeding pending" in the
sub-choice node (A picked on H5/H6, both proceeding=False). Procedure: NEW dedicated 2-option
`choice` node on the full question:
- Option Y: "A case is already going on / pending in a court or the Family Court (for example
  'my divorce case is already going on', 'the case is pending')."
- Option N: "No case has been filed or is going on; the user is asking for something, or
  thinking about filing, but no proceeding is pending."
- Choice-Y ≥ 0.65 → True; ≤ 0.35 → False; in between → **uncertain → default False + flag
  and escalate**. Note the deliberate asymmetry here (default False, unlike the other facts):
  a wrong proceeding_pending=True routes custody to HMA 26 — a forbidden-before-recheck-class
  error (HMA 26 with no proceeding, gate G11) — while a wrong False routes to GWA, which is
  the standalone route and is never a forbidden fire. The flag + escalation still applies, so
  the uncertainty is visible either way. This asymmetry must be recorded as a decision, not
  buried: it trades a possible GWA-side error (wrong route, both sections still custody-family)
  against a forbidden-side error.
- Dry-run requirement: the choice must return True only on H14 and False on all other 15,
  with margin ≥ 0.10; H5 (divorce asked, no proceeding) and H6 (no divorce, no proceeding)
  are the discriminating items — if the choice returns True on either, the model is still
  conflating asked with pending and the extraction is not fit.

**`demand_made`** (feeds the stridhan demand escalation, not a veto — recorded for completeness):
same pattern — dedicated choice node ("has she already asked for the gold back?" vs "has not
asked yet"), 0.60/0.40 cutoffs, uncertain → default False (demand-not-made → escalate to make
a demand, which is the safe direction: it asks the user to do something true rather than
assuming a demand happened) + flag. H3 (False) vs H15 (True) are the in-set discriminators.

### 2.5 Exact per-question fields the v6 notebook must record

Add to every `rec` in the live run (Cell 7/Cell 8 output JSON). The hand fact is kept **for
comparison only** — it must never feed a gate in v6 (if any gate reads a `_hand` field, the run
is not a v6 extraction test):

```
# Per fact F in {money, gold, custody, residence, proceeding, demand}:
rec['fact_<F>_model']       # bool — the model-extracted value actually used by the gate
rec['fact_<F>_method']      # 'full' | 'choice' | 'clause_choice' | 'aux' | 'regex_audit'
rec['fact_<F>_score']       # float — the deciding score (full score, or winning choice score)
rec['fact_<F>_band']        # 'certain_true' | 'certain_false' | 'uncertain'
rec['fact_<F>_uncertain']   # bool
rec['fact_<F>_hand']        # bool — frozen Cell 6 annotation, comparison only, NEVER a gate input
rec['fact_<F>_agree']       # bool — model == hand (a False here is a finding, file it)
# Custody per-clause detail (choice node):
rec['custody_clause_choices']  # [{clause, choice_A, counts}] for every clause
rec['custody_regex_audit']     # {regex_claim, choice_claim, agree} — regex kept as audit only
# Guard / gate audit (already in v5 spec, keep):
rec['single_issue_guard']   # {armed, dominant, dominant_full, blocked:[(issue, full, lift)]}
rec['gated_out']            # one distinct reason string per veto, never merged
rec['stage1_final_pre_gate']# final scores BEFORE any veto (so a veto's effect is auditable)
rec['fired_source'] / rec['fired_clause']  # as computed (what WOULD have fired)
# Flag-and-escalate (§3):
rec['extraction_flags']     # [{fact, reason, band}] — every uncertain extraction
rec['flagged_issues']       # [{issue, flag_reason}] — every flag-and-escalate outcome
rec['escalate']             # bool — True if any flag exists on this question
rec['thin_margin']          # [{issue, final, threshold, margin}] — any fired issue within 0.05 of threshold
# Sub-choice audit (§4):
rec['sub_choice_fact_check'] # {node, chosen, fact_required, fact_value, contradiction: bool}
```

The run report must print, verbatim, a **fact-agreement table** (model vs hand per fact per
question, 16 × 6) and a **flag table** (every flagged question with its reason). A run that
does not print these has not tested extraction, whatever its exact score says.

---

## 3. Margin analysis — how wide the safety margins really are, and what breaks each constant

All numbers from v4r `raw_live_runs` unless stated. "Margin" is measured against the nearest
in-set score on the dangerous side, not against the target the constant was designed to kill.

### 3.1 Fix 3 guard — lift bar 0.80, ceiling 0.01

| Constant | Advertised margin | Real margin | What it means |
|---|---|---|---|
| Lift bar 0.80 vs highest target lift (H7 0.1971) | 0.6029 | — | Genuine: no target FP comes within 0.60 of the bar. |
| Lift bar 0.80 vs nearest genuine rescue **below** the bar | — | **0.0105** (H14 custody aux 0.7895) | H14's true custody lift sits 0.0105 under the bar. It survives **only** because its full (0.1321) exceeds the 0.01 ceiling and H14 arms the guard (single dominant) — i.e. it survives via the ceiling leg, not the bar. If H14's custody full had been 0.009 instead of 0.1321, the guard would have blocked a true issue. The bar's safety is entirely conditional on the scope conditions holding. |
| Lift bar 0.80 vs other genuine rescues below the bar | — | 0.1228 (H10 maintenance aux 0.6772); 0.1526 (H4 residence aux 0.6474) | Same point, wider: three genuine rescues in-sample sit below 0.80. The bar does not separate true from false lifts — the *scope* does. |
| Ceiling 0.01 vs worst FP full (0.0001) | 100× | — | Genuine: no FP full comes within 100× of the ceiling. |
| Ceiling 0.01 vs lowest true **fired** full (K0 maintenance 0.0773) | 7.7× | absolute gap **0.0673** | Thin in absolute terms. K0's maintenance full is itself an aux-rescued issue — the full prompt nearly missed a true issue. The ceiling assumes true-issue fulls stay ≥ 0.077; that is a property of this prompt on these 16, not a law. A fresh true second issue with full 0.005 breaks the ceiling leg. |

**Unseen-question pattern that breaks Fix 3:** a single-dominant question whose true second
issue has `full ≤ 0.01` and `lift in [0.20, 0.80)`. Concrete instance (§1.3 N1): *"The hospital
did not give us the bill, and my husband gives no money for the baby's medicines."* — if the
maintenance full lands at ~0.005 (money lives in a short subordinate clause, the H1/H5 pattern
where full under-scores true issues) with a clause lift of ~0.35, the guard blocks a true
maintenance issue → 2-section FN. This is not an exotic construction; it is an ordinary
multi-issue phrasing with the money ask in the second clause. The guard has **no true-positive
calibrator inside its own scope** (Lane C §2: no genuine rescue with full ≤ 0.01 exists
in-sample) — the bar was set from the FP side only. That is the precise sense in which 0.80 is
fitted, not measured.

**Second break pattern:** a fresh single-issue question where the dominant issue's own full is
low and a *second* true issue's full is also low — e.g. a violence + residence question where
violence full is 0.42 (dominant) and residence full is 0.008 with aux lift 0.70. Guard arms
(single dominant), residence full ≤ 0.01, lift 0.70 < 0.80 → blocked → residence FN. H13's
shape (violence 0.8892 + residence 0.4212) with both scores scaled down by shorter phrasing.

### 3.2 Fix 1 thresholds — maintenance 0.10, stridhan 0.50

| Threshold | Nearest false score | Nearest true score | Verdict |
|---|---|---|---|
| Maintenance 0.10 (final) | FP aux finals 0.1218 (H3), 0.1269 (H15) — **0.022–0.027 above** | True finals min 0.6772 (H10) | The threshold alone does NOT save H3/H15: the FPs clear it by 0.02. If the money gate fails (extraction error), the threshold is no defence. The threshold's only job is the full-score leg (true min full 0.0773 is *below* 0.10 — the threshold is cleared by aux/clause, not by full, on K0/H8/H10/H11/H13). |
| Stridhan 0.50 (final) | H1 full 0.4948 — **0.0052 below**; H1 clause 0.7545 — above | True finals min 0.9032 (H15) | The threshold is effectively non-functional as a separator on the false side: a money-only question sits 0.0052 under it. Any fresh money-only question scoring stridhan-full 0.51 fires on score alone, and then only the gold gate stands between it and 2 FPs. The stridhan threshold is a 0.0052 coin flip, not a boundary. |

### 3.3 The margin no v5 fix touches — H5 custody aux 0.2189 vs threshold 0.20

Margin **0.0189** — the tightest number in the run. H5's custody (true positive: GWA 1890, HMGA
s.6, WELFARE) fires *entirely* on the daughter aux prompt (full 0.1098, clause-max 0.0957, both
below 0.20). Consequences:
- A live-run score shift of > 0.019 in the custody aux flips H5 custody off → 3 new FN, recall
  1.000 → 0.947, exact 10/16 → 9/16 (before any v5 fix is even evaluated). The v5 prediction
  of 16/16 is conditional on this score reproducing.
- The FP it is measured against (H6 aux 0.3669) is **higher** than the true score — the
  ranges are inverted by 0.148. No threshold separates them; this is why Fix 2 exists, and
  why Fix 2's failure modes (§1.4) matter more than its in-sample success.
- Laya inference *should* be deterministic given identical weights and process, but the v5
  live run re-computes every score in a fresh Colab process. The run report must print H5's
  custody aux explicitly and confirm it is still ≥ 0.20 (v5 report §5 already requires this;
  this lane adds: confirm it is still ≥ 0.21, i.e. the margin has not narrowed further, and
  record it in `thin_margin` per §2.5).

### 3.4 Flag-and-escalate fallback (replaces hard veto where the margin is thin)

Replace the hard veto with a 3-state outcome per gated issue — **FIRE / VETO-certain /
FLAG** — in exactly these cases (all others keep the hard veto):

| Case | Trigger | Outcome instead of hard veto |
|---|---|---|
| Any fact extraction in its uncertain band (§2) | `fact_<F>_uncertain=True` for a fact a veto would rely on | **FLAG**: fact defaults True (fail open, §2 governing principle), issue fires or not on its score, `escalate=True`, reason recorded. The question is routed to human/LLM review; it does not count as clean-exact. |
| Guard would block a lift in the "plausible rescue" band | Guard armed, `full ≤ 0.01`, lift in **[0.50, 0.80)** | **FLAG, do not block**: let the issue fire on its score, record `flag_reason='guard_lift_plausible_rescue'`, escalate. Rationale: H14's genuine 0.7895 and H10's 0.6772 both live in this band — a lift here is evidence, not noise. Lifts < 0.50 keep the hard block (all three target FPs are ≤ 0.1971; the 0.50 floor sits 0.30 above the highest target). |
| Any fired issue within 0.05 of its threshold | `final − threshold < 0.05` (H5 custody 0.0189 is the in-set instance) | **FLAG (informational, does not change firing)**: record in `thin_margin`, escalate for review. The firing stands; the flag says "this exact-match depends on a 0.02 margin — re-verify before trusting it." |
| Custody gate on a clause whose choice score is uncertain (§2.3) | Best clause `choice_A` in (0.40, 0.60) | **FLAG**: `custody_claim` defaults True (fail open), escalate. Never silently gate custody on an uncertain choice — custody is the issue whose false side out-scores its true side. |

Cost of flag-and-escalate: flagged questions need review, so the run's headline exact must be
reported as **exact-clean** (no flags) alongside **exact-with-flags**. A run that reports only
the with-flags number is inflating. Benefit: no silent FN is ever created by a veto whose
input was uncertain — which is the only failure mode that can take the run below v4r's recall.

---

## 4. The H5 sub-choice contradiction — diagnosis and fix

### 4.1 What happened (verified from the v4r JSON)

- **Question (H5):** *"I want a divorce from my husband. He beats me, I need money every month
  and I want my daughter to stay with me."*
- **Facts (Cell 6):** `divorce_asked=True`, `proceeding_pending=False`, `decree=False`.
- **Custody sub-choice returned:** **A: "Custody inside a matrimonial proceeding (HMA s.26)"**
  (`sub_choices['custody:custody_sub_issue_choice']`).
- **Correct answer given the facts:** **B: "Standalone custody/guardianship, no HMA proceeding
  (Guardians and Wards Act 1890)"** — no proceeding exists. Divorce *asked* is not a proceeding
  *pending*: asking for divorce starts a proceeding only after filing, and H5 has no case filed
  anywhere.
- **Outcome:** kept is correct (GWA 1890, HMGA s.6, WELFARE — no HMA 26). H5 is exact in v4r.
  **No score impact.** The contradiction is invisible in the kept set.

### 4.2 Why the outcome was correct — Stage 2 never reads the custody sub-choice

Cell 7 `stage2()` lines 261–264:

```python
if 'custody' in fired:
    kept_pre |= {'gwa-1890', 'hmga-1956-s6', 'welfare-principle'}
    if facts['proceeding_pending']:
        kept_pre.add('hma-26')
```

The custody sub-choice is **not referenced anywhere in `stage2()`**. The route is decided
entirely by the hand fact `proceeding_pending`. The model's choice A is recorded in
`sub_choices` and then ignored. Stage 2 silently corrected a wrong model output — with no
`dropped` entry, no `gated_out` entry, and no error count naming it. H5's `dropped` list is
empty. The only place the contradiction is visible is by comparing `sub_choices` against
`facts` by hand, which is what this lane did.

The same shape appears in the divorce-gate node, worse: the node returns **"Divorce expressly
asked -> open gate, Family Court under HMA s.13/s.13B"** on 9 of the 12 questions where it runs,
including **8 with `divorce_asked=False`** (K0, H1, H2, H4, H6, H10, H11, H12). As a factual
statement it is correct on only 2/9 (H5, H14). It is saved from causing HMA 13 FPs only
because `stage2()` lines 279–283 additionally require `facts['divorce_asked']` *and* `'open
gate' in gate`. The custody sub-choice is correct on 3/5 (K0 B ✓, H2 B ✓, H14 A ✓, H5 A ✗,
H6 A ✗). Both choice nodes are, as factual reporters, unreliable — and both are currently
harmless only because Stage 2 does not trust them.

### 4.3 Root cause — the choice is asked a question its input cannot answer

`sub_choice_body` shows what each choice node actually sees: a **single clause**, not the full
question. H5's custody body is *"I want my daughter to stay with me."* — a clause that contains
**no information whatsoever** about whether a proceeding is pending. H6's custody body is the
whole money-plus-stay clause — also no proceeding information. H12's divorce-gate body is a
clause about who owns a house — no divorce information. The model is being asked "is there a
proceeding pending?" on an input that never mentions a proceeding, so it guesses — and it
guesses toward A / open-gate (the first / more elaborate option) on questions where the clause
gives it nothing to work with. Two distinct facts are being conflated in the guess:
"divorce asked" (H5: True) is read as "proceeding pending" (H5: False). H6, where divorce was
not even asked, still gets A — so the guess is not even tracking divorce-asked; it is a
prior toward A.

### 4.4 Why it matters despite zero score impact today

1. **Fix 4 makes `proceeding_pending` the router.** Any future lane that wires the sub-choice
   into routing ("use the model's route choice" — the natural next step once the choice node
   exists) would route H5 to HMA 26. HMA 26 with no proceeding pending is a
   forbidden-before-recheck-class fire (gate G11; cf. HMA 25 with no decree). The H5
   contradiction is a loaded gun pointed at the next lane: the model has now demonstrated,
   twice (H5, H6), that it picks the proceeding route when no proceeding exists.
2. **Prose risk (gate G12).** If answer prose ever quotes the sub-choice ("custody inside a
   matrimonial proceeding"), H5/H6 prose would assert a proceeding that does not exist — the
   same class of error as the frozen prose-forbidden mappings (wrong Act / wrong forum for the
   stated facts).
3. **It undermines §2.4.** The proceeding-pending extraction proposed there must be designed
   knowing the model conflates asked-with-pending: a choice node run on the same impoverished
   input (single clause) will reproduce the same error. The extraction must run on the full
   question, and H5/H6 are its discriminating test items.
4. **Silent correction hides model error.** The run reports 0 model errors while 2 custody
   sub-choices and 8 divorce-gate choices are factually wrong. A run record that cannot see
   its own wrong choices cannot be trusted to report the next one.

### 4.5 Fix (for v6 — NOT v5; v5 is built, do not retrofit)

1. **Pre-gate the options (Layer A, same pattern as the HMA 25 option filter):** when
   `proceeding_pending` is False, do not offer custody option A at all — offer only B/C/D
   (D, welfare, applies to all routes; C, natural guardian, is fact-independent). When True,
   offer A/B/C/D. Same for the divorce-gate: when `divorce_asked` is False, do not offer the
   open-gate option. Pre-gating makes the H5/H6 error impossible by construction for the
   gated option; the choice then measures discrimination among the *remaining* options.
2. **Run the choice on the FULL question, not the fired clause.** The clause never contains
   proceeding information; the full question sometimes does ("My divorce case is already
   going on…"). A choice that cannot see the fact cannot be scored on the fact.
3. **Record a fact-check on every sub-choice** (`sub_choice_fact_check`, §2.5): compare the
   chosen option against the facts (A requires `proceeding_pending`; open-gate requires
   `divorce_asked`). On mismatch, record `contradiction=True`, ignore the choice's routing
   implication, and **count it in the run's error tally** — it is a model error for reporting
   even though Stage 2 corrected it. Target for the v6 live run: 16/16 agreement after
   pre-gating.
4. **Rule, recorded:** facts outrank choices in Stage 2, always. Fix 4's branch already
   implements this for custody routing; extend the statement to every sub-choice: a choice
   may never add a section its prerequisite fact forbids, and never remove one its fact
   requires. (This is the general form of the HMA 25 Layer A/B precedent.)
5. **Stated tension:** pre-gating by hand facts reintroduces hand-annotation dependence —
   the same overfit class as Fix 1. The pre-gate is only as general as `proceeding_pending`;
   once that fact is model-extracted (§2.4), the pre-gate inherits the extraction's error
   rate. The alternative (full-question choice without pre-gating) is untested, and current
   evidence (2/5 custody, 2/9 divorce-gate) says the model guesses. Recommend pre-gating as
   the v6 fix, with the extraction-error caveat stated — do not present pre-gating as a
   model improvement. It is a guardrail around a demonstrated model failure.

---

## 5. Overall verdict and what v6 must do before the sealed run

**What generalises:** Fix 1's grounding logic (money vs gold-held are real, distinct facts);
Fix 3's mechanism (a ~zero full score rescued only by a weak lift is noise — *when* the scope
conditions hold); Fix 4's exclusivity rule (exactly one primary custody route). The maintenance
full-question scores separate widely enough (773×) that model extraction of `money_fact` is
credible. The residence aux-max separation (0.3813 → 0.6474) is a genuine, usable finding.

**What does NOT generalise — blunt list:**
1. **Hand-annotated facts** (`money_fact`, `gold_fact`, `residence_claim`, `proceeding_pending`,
   `demand_made`): every one restates ground truth on the 16. v5's 16/16 prediction is a
   prediction about the vetoes, not about the facts. On the fresh set, v5-as-shipped cannot
   run at all without a human annotating 20 new questions — which is the definition of not
   generalising.
2. **Fix 2's regex patterns:** 0/3 on unseen must-not-gate paraphrases; the should-gate
   "successes" are vacuous (blocking by absence of a pattern). Plus a concrete plural bug
   ("children/kids" unhandled in both the patterns and the exclusion).
3. **The 0.80 bar's safety:** its real margin is 0.0105 (H14's 0.7895), not 0.60. Three genuine
   rescues sit below it. Its safety is entirely borrowed from the dominance test and the
   ceiling, both of which are in-sample scope conditions.
4. **The stridhan 0.50 threshold:** H1's false full is 0.0052 below it. It is not a boundary.
5. **H5's custody firing:** margin 0.0189 on a model score, inverted against the H6 FP
   (0.3669). The v5 16/16 prediction is conditional on this score reproducing in a fresh
   Colab process.
6. **The sub-choice nodes as factual reporters:** 3/5 (custody) and 2/9 (divorce-gate) correct
   as statements of fact. They are currently harmless only because Stage 2 ignores them.

**Required before the sealed fresh-20 (in order):**
1. Build the §2 extraction (money/gold from full scores + choice legs; custody from the new
   per-clause choice; residence from aux-max + choice; proceeding_pending from a dedicated
   choice) and **dry-run it on the 16** in live Colab *before* wiring any extraction as a
   veto. Publish the model-vs-hand agreement table; any disagreement is a finding.
2. Convert guard blocks with lift in [0.50, 0.80) and all uncertain-band extractions to
   **flag-and-escalate** (§3.4). Report exact-clean and exact-with-flags separately.
3. Fix the H5 sub-choice contradiction (§4.5): pre-gate options, full-question input,
   fact-check recorded and counted.
4. Fix the custody plural bug if the regex is retained for v6 (morphology only — do not
   present it as a generalisation fix).
5. Have a **non-tuning rater** write the fresh paraphrase set for the extraction validation
   (the §1 paraphrases are this lane's test items, not a rater-approved set, and must not be
   used as tuning inputs).
6. **Do not tune any threshold or band on the fresh set** (gate §6 rules 3, 6, 7). If the
   fresh set breaks a veto, diagnose the general cause, fix the mechanism, and re-run both
   sets.

**What this lane did not do (out of scope, stated so it is not assumed):** no live scores were
measured — every paraphrase outcome in §1 and every extraction threshold in §2 is a prediction
from the v4r numbers, to be confirmed by the v6 dry run. No notebook was changed. No ground
truth was changed. No paraphrase in this file may enter the phrasebook, prompts, or pattern
lists.
