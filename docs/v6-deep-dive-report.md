# v6 DEEP-DIVE — merged report (round 3 of the overnight 10/10 run)

**Status: ANALYSIS + BUILD SPEC. No live Colab run yet.** Merges Lanes 1–5 (generalisation,
escalates, legal decisions, prose + latency, validation). Parent runs the Gemini/ChatGPT
browser consultations in parallel; this report is offline analysis only. No ground truth was
changed by any lane. No notebook was touched.

**Starting point (verified live, v4r 2026-11-27 ~00:19 IST):** exact 10/16, micro P/R
0.826/1.000, micro-F1 0.905, TP/FP/FN 57/12/0 of 57 GT, court 13/16, escalates 14/16,
recall 1.000, forbidden 0, model errors 0. Remaining work is 12 false positives only, on
H1 (×2), H3 (×2), H6 (×3), H7 (×2), H14 (×1), H15 (×2).

**User target (2026-11-27 ~07:05 IST, voice):** reach at least 9/10 measured live, via
multi-agent deep work plus both advanced models.

---

## 0. Headline correction — the ratings quoted so far are wrong (Lanes 3 + 5, agreed)

Two lanes independently found the same error: **the gate doc freezes a different rating
formula from the one used in the v3/v4r reports.**

- **Gate formula (§2, frozen):** `10 × [0.60·E + 0.15·Rm + 0.10·Pm + 0.075·C + 0.075·S] − 0.5·Fb − 1.0·Fp`,
  then the §2 caps (lower of formula and cap wins). Uses mean precision/recall; exact weighted 0.60.
- **Working formula** (used for the v3 5.9 / v4r 7.7 numbers): `10 × [0.40·E + 0.30·micro-F1 + 0.15·C + 0.15·S]`.
  No forbidden penalty, no caps, not in the gate doc anywhere. It also misattributes v1's 3.3 to
  itself — 3.3 is the gate formula's own worked example; the working formula gives v1 4.8.

| Run | Gate formula (correct) | Working formula (retired) |
|---|---|---|
| v1 live | **3.3** | 4.8 |
| v3 live | **5.0** (was quoted 5.9) | 5.9 |
| v4r live | **7.3** (was quoted 7.7) | 7.7 |
| v5 predicted (NOT live) | 9.8 raw → **capped 9.0** | 9.6 (uncapped) |
| v5 predicted + escalates 16/16 | 10.0 raw → **capped 9.0** | 10.0 (uncapped) |

**Decision D10 (coordinator): the gate formula governs; the working formula is retired.**
Gate §6 rule 9 forbids changing metric definitions mid-tuning. Cell 8 of the v6 notebook must
compute the gate formula; the working formula must not appear in any v6 artefact except as a
historical note. Past reports/MEMORY entries should be annotated with a dated correction, not
silently edited.

**What this does to the 9/10 target:** under the gate formula + caps, **9.0 is the ceiling until
prose is measured, fresh + Kannada pass, and the confirmation re-run passes.** A live v5/v6 run
matching the 16/16 prediction rates **9.0 (capped)** — that meets the 9/10 minimum, but must be
reported as "9.0, capped — not 10/10" with the four unmet conditions listed. The 9/10 target
tolerates at most ~2 non-exact questions on the current set (13/16 exact with otherwise
identical metrics gives 8.69 raw — below target). Rating 9.0 (capped) ≠ gate passed: G14
latency fails on v4r too (§6), and the 10/10 claim needs every gate row.

---

## 1. Per-FP diagnosis — does v5 generalise? (Lane 1)

Verdict, blunt: **v5's mechanisms mostly generalise; v5's shipped implementations mostly do
not.** Nothing below changes the v5 prediction of 16/16 on the 16. It changes what that
prediction is worth on the 17th question.

| FP | v5 veto | Mechanism general? | Shipped implementation general? | Verdict |
|---|---|---|---|---|
| H1 stridhan ×2 (clause 0.7545) | Fix 1 `gold_fact` gate | Yes — "no gold-held fact, no stridhan" is a legal grounding rule | **No** — hand annotation restates GT; the score pattern it replaces is knife-edge (full 0.4948 vs 0.50 threshold, margin 0.0052) | **OVERFIT as shipped; generalises only via model extraction (§2)** |
| H3/H7/H15 maintenance ×6 (aux ~0.12, clause 0.1971) | Fix 1 `money_fact` gate + Fix 3 guard (redundant) | Yes, both — full-question scores separate 773× (max false 0.0001 vs min true 0.0773); aux-pool background floor ~0.12 is a property of the pool | **No** — money gate runs on a hand fact | **GENERALISES as mechanism; needs model extraction (§2)** |
| H6 custody ×3 (aux 0.3669) | Fix 2 regex custody gate | **No** — the gate *is* four literal patterns fitted to the 16's phrasings; no existing score separates H5 (true 0.2189) from H6 (false 0.3669) — all three score channels are inverted | **No** | **OVERFIT — do not ship the regex as the long-term gate; needs a new per-clause choice node (§2)** |
| H14 GWA ×1 | Fix 4 exclusive primary route | Yes — "exactly one primary route" is a legal rule, not a fitted number | Partially — branch is general; input `proceeding_pending` is hand-annotated | **GENERALISES as a rule; fact source must be model-extracted (§2) or rater-verified** |

Paraphrase stress tests (Lane 1 §1; items are test items written by the lane, NOT tuning
inputs — per gate §6 rules 2/4 none may enter the phrasebook, prompts, or pattern lists, and a
non-tuning rater must re-write/approve the set before any use):
- **H1 family:** gate logic generalises; vocabulary is the risk. "Ornaments" / "jewellery" /
  "streedhan" (legal term alone) may not be recognised by an extraction prompt that lists only
  gold/cash/gifts → new FN. The stridhan full score does NOT separate: any fresh money-only
  question scoring 0.51 fires on score alone.
- **H3/H15 family:** generalises, with one sharp edge — money need phrased without money words
  ("books and uniforms", no "money/maintenance/fees") is the must-not-gate risk; it sits one
  paraphrase step past H13 ("school fees count as money").
- **H7 family:** generalises. The "did not give" bleed is a property of the clause-max mechanism.
  Residual risk is a true second issue hiding behind a ≤0.01 full score (§3, guard-scope risk).
- **H6 family: 3/3 should-gate correct (all by absence of a pattern, none by recognition),
  0/3 must-not-gate correct.** "I want my child to live with me", "Who gets the kids after a
  divorce?", "Can I keep my son with me?" — all blocked → new 3-section FNs. Plus a concrete
  plural bug: "children/kids" matches neither the patterns nor the exclusion. Patching plurals
  and verbs one at a time turns the whitelist into a second phrasebook; the fix is model
  extraction, not more patterns.
- **H14 family:** routes correctly given a correct fact. Entire risk is in
  `proceeding_pending`: the model demonstrably conflates "divorce asked" with "proceeding pending".

### Guard margins (Lane 1 §3) — thinner than v5 reported
- The guard's 0.80 bar looks safe (0.60 above the highest target lift 0.1971) but its **real
  margin is 0.0105**: H14's genuine custody lift (0.7895) sits just under the bar and survives
  only via the ceiling/dominance legs.
- Break pattern: a single-dominant question whose true second issue has full ≤ 0.01 and lift in
  [0.20, 0.80) — e.g. money asked in a subordinate clause. Lane 1 specifies a
  **flag-and-escalate fallback** for lifts in [0.50, 0.80), uncertain extractions, and any fired
  issue within 0.05 of threshold (H5 custody, 0.0189 — the run's tightest number, untouched by
  any v5 fix).
- H5 sub-choice is worse than reported (see §4): the divorce-gate sub-choice returns
  "expressly asked → open gate" on 9 questions, 8 with `divorce_asked=False`.

---

## 2. Model-extracted facts — replacing hand annotation (Lane 1 §2)

**Governing rule for all facts: uncertain → fail open + flag + escalate, never a silent veto.**
When extraction lands in its uncertain band, the fact defaults to True (the veto does not fire;
the score decides) AND the question is flagged (`extraction_uncertain=True`, `escalate=True`).
A wrong veto creates the run's first FN, strictly worse than leaving a known, bounded FP. The
run report must show exact-clean and exact-with-flags separately. If the flagged rate on any
set exceeds ~10%, the extraction is not fit to ship as a hard veto.

**Calibration rule:** bands are set from the current-16 distribution (max false vs min true),
never from a single question (gate §6 rule 3). Each band is provisional until a live dry run
runs the extraction on the 16 and reports model-vs-hand agreement per fact. A dry-run
disagreement is a finding, not a threshold to quietly re-fit.

| Fact | Extraction procedure (existing notebook mechanisms only) |
|---|---|
| `money_fact` | Primary signal: maintenance FULL-question score — clean channel (true set min 0.0773, false set max 0.0001). Certain-True ≥ 0.05 / certain-False ≤ 0.002 / choice node in between. |
| `gold_fact` | Stridhan full score is NOT clean here (H1 at 0.4948). Bands ≥ 0.70 / ≤ 0.60 with a choice leg in between. Extraction prompt must cover ornaments/jewellery/streedhan explicitly (§1). |
| `custody_claim` | **New per-clause choice node required** — no existing score separates H5 from H6. Dry-run gate: must hit H5/H14/K0/H2 ≥ 0.70 and H6/H10/H13/H12 ≤ 0.50 before wiring as a veto. |
| `residence_claim` | From aux-max — separates 0.3813 → 0.6474, threshold 0.50 (a genuine new finding). |
| `proceeding_pending` | Dedicated choice — the existing pending noul does not separate (H2 false at 0.6445). |
| `demand_made` | Keep as annotated fact for v6; Lane 3 D11 confirms sale = refusal evident (see §4). |

Hand facts are kept in Cell 6 for comparison only and **never as gate inputs** once extraction
ships. Full per-question record-field list is in Lane 1 §2 (extraction value, band, source,
flag). Sub-choice fix (Lane 1 §4, Lane 3 D8): pre-gate sub-choice options by facts (Layer A
pattern), run the choice on the full question, record a fact-check per sub-choice and count
contradictions as model errors; record "facts outrank choices" as a rule.

---

## 3. Escalates redesign — breaking the 9.6 ceiling (Lane 2, agreed with Lane 3)

**Key finding (Lane 2):** v4r's H7/H15 "True" was an artefact — the quantum boilerplate attached
to a *false* maintenance fire. Once v5 gates that fire out, the reason disappears. The fix is
genuine new kinds, never re-attaching the boilerplate.

### 3.1 Design (Lane 2 §1) — four new kinds, all triggered on kept sections / frozen facts only
Never on raw scores, never on pre-gate fired state, never on a question ID. A gated-out issue
must never escalate. No catch-all kind (a generic "needs human review" would make the metric
vacuous and teach nothing).

| Kind | Trigger | What it does |
|---|---|---|
| `custody` | kept ∩ {gwa-1890, hma-26} ≠ ∅ | Who-gets-the-child is a Family Court welfare decision; bot names the route, never states an outcome; urgency clause for a parent threatening to take the child. → H2 True. |
| `residence` | `'residence' in fired` (post-gate — NOT kept set: H5 keeps PWDVA 18 via the violence-only branch, a protection order not a residence order, and a kept-set trigger would wrongly attach re-entry text there) | Only a Magistrate's residence order restores entry; house in husband's name doesn't remove the right. → H4 True. |
| `recovery` | stridhan kept AND `demand_made is True` | Sold/withheld gold needs valuation, BNS 316 complaint, HMA 27 recovery. Mutually exclusive with `demand` by construction. → H15 True. |
| `procedure` | `'births-deaths-act-1969' in kept` | Procedure branches on unstated facts (DOB, delay, hospital issuance); in-person Registrar application. Asserts no unstated fact. → H7 True. |

Also in the spec: `quantum` moves to kept-only, `demand` trigger `is False` → `is not True`
(both behaviour-preserving on the 16); Cell 8 becomes
`esc_live = bool(kinds & {'quantum','court','demand','custody','residence','recovery','procedure'})`,
with `fact` deliberately excluded from scoring. New diagnostics: per-row `escalation_kinds` and
an aggregate `escalates_on_empty_kept` guard (must be 0). Optional, not load-bearing: a `safety`
kind for violence (fires H5, H13; changes no score).

**Predicted escalates under this design: 16/16** (H2/H4/H7/H15 fixed, nothing else changes).
With v5's predicted 16/16 sections and 16/16 courts that is 10.0 by formula on the current 16 —
**capped at 9.0** until G2/G3/G12/G15 pass. G9 alone is not 10/10.

### 3.2 H7/H15 — both sides argued, recommendations (Lanes 2 + 3 agree)
- **H7 — KEEP True (both lanes).** Lane 2: borderline — the most fully answerable question in
  the set on its face, and the one expectation a rater could reasonably flip; the keep rests on
  the hospital's non-issuance plus genuinely branching procedure (s.13's three delay tiers:
  ≤30 days Registrar; 30d–1yr District Registrar; >1yr Magistrate's order). Lane 3: True is
  correct on a named fact-ask, not quantum — add `kind: fact` with the named ask (DOB, delay,
  registration status); court stays Registrar; **no GT change**. If the rater flips H7 to False,
  drop the `procedure` kind — escalates is still 16/16, since 16/16 depends on kinds and
  expectations being decided consistently, not on the rater agreeing.
- **H15 — KEEP True (both lanes).** Strong keep: sold property needs valuation, a BNS 316
  complaint, HMA 27 recovery; the bot cannot value sold gold or file a complaint. Lane 3 adds:
  re-ground on a fact/proof kind (proof, sale details/value, criminal-route facts); demand kind
  is no longer the reason.
- **Reconciliation note:** Lane 3 proposes a single `fact` kind (D9) with named asks; Lane 2
  proposes four specific kinds. They are the same idea at different grains: **adopt Lane 2's
  four kinds as the implementation of Lane 3's fact-kind concept** — each is a named, falsifiable
  fact-ask, and no generic kind ships. The audit agrees: only H7/H15 expectations are genuinely
  ambiguous; H2/H4 expectations are plainly correct (the gap is missing kinds, not wrong
  expectations); the other 12 are well-defined. Minor defect noted: quantum text claims "school
  fees unknown" on questions with no school fees.

---

## 4. Legal decisions (Lane 3) — decision table D1–D11

### 4.1 HMA 27 — prereq right, GT wrong (Lane 3 §1; concurs with v4, with refinements)
s.27 ("in any proceeding under this Act… in the decree") is ancillary: it can only be pressed
inside a matrimonial proceeding under the HMA that is pending or being filed together with the
claim, never as a freestanding application. The graph already applies this correctly to
HMA 24/25/26 (R-HMA24-01 and R-HMA26-02 are `drop`), but R-HMA27-04 is `escalate`-only and the
notebook never gates HMA 27 — an internal contradiction (the Stage 2 pipeline's own drop rule
says a section failing any prereq check is DROPPED). **Refinements vs v4:** (1) **K0 is a fourth
affected question** — its GT also contains HMA 27 with `proceeding_pending: false` (GT would fall
57→53 on removal, not 57→54); (2) the graph's "alternatively… pressed as part of the
family-court case for maintenance/custody/residence" limb is **itself legally wrong** (a
BNSS/PWDVA/GWA case is not an HMA proceeding) and must be deleted, not kept. Corrected rule
wording is in Lane 3 §1.4, including a definition of "being filed" (user states they are
filing/will file an HMA petition; wanting divorce ≠ being filed — consistent with HMA 24 on H5).
Replacement label recommended: Family Courts Act s.7(1) Expl. (c) / CPC s.151; BNS 316 stays.
**Caveat:** authorities are as recorded in v4 (Balkrishna, Babulal Full Bench, Krishna Kumar
Gupta), not re-verified by fresh browser research in this offline lane; HP *Astha Thakur* full
judgment remains unread — the rater should read it before freezing D1.

### 4.2 Other verdicts (Lane 3)
- **H14/HMA 13: DEFENSIBLE but the thinnest frozen call** (governing section of a pending case,
  not a relief sought — rater to confirm; dropping it needs a paired gate change).
- **H4/no-PWDVA 20: DEFENSIBLE; keep** (s.20 fires iff money/rent claimed).
- **H5 sub-choice:** sub-choice A ("HMA s.26") is wrong on the facts (divorce-asked ≠ proceeding
  pending); GT (GWA) is right and Stage 2 reached it silently with no `gated_out` entry. Fix the
  derivation + audit trail, not GT. Full-16 sweep also found: H3 sub-choice `civil_only_s27` vs GT
  keeping BNS 316; H15 sub-choice `criminal_only_s316` vs GT keeping HMA 27 (supports the Q1
  verdict); a false divorce-gate sub-choice text on K0/H4/H10/H12; H15's `demand_made: true` as an
  inference (sale = refusal evident) — confirm, with the inference recorded.
- **D1 + D2 must be paired:** under corrected GT (D1-A, 53 sections) the v5 fixes still remove
  the same FPs, but the system must *also* stop firing HMA 27 on those four questions (D2-A, same
  change). If D1 is adopted without D2, corrected-GT exact would be 14/16 (K0, H10 non-exact by
  HMA 27 FP); if D2 without D1, old-GT exact would be 14/16 (K0, H10 non-exact by HMA 27 FN).
  **Either half alone makes the v5 "predicted 16/16" fall away — it was computed under the old GT.**

### 4.3 Decision table (condensed from Lane 3 §5; full reasoning in the lane file)

| # | Decision (who settles it) | Options | Recommendation | Consequence |
|---|---|---|---|---|
| D1 | HMA 27 GT correction (independent rater) | A. Remove HMA 27 from K0/H3/H10/H15 GT, no replacement (GT 57→53). B. Keep GT, weaken prereq (reject — §4.1). C. Replace with new label `FCA 7(1) Expl. (c) / CPC 151` (GT stays 57). | **C if the label set can gain a label; otherwise A.** Rater to read *Astha Thakur* first. | A or C **invalidate all prior runs on the current 16** (gate §6.1): v3/v4r/v5 must be re-run and re-filed under corrected GT; v5 predicted 16/16 falls away. Under A, v4r exact re-scores 8/16 before the gate is applied, then recovers with D2. |
| D2 | HMA 27 corrected rule + gate (coordinator + notebook lane) | A. Adopt §1.4 wording, R-HMA27-04 → drop, delete "alternatively…" limb, amend co-fire rule + BNS 316 exclusion, gate in notebook — same logged change as D1. B. Adopt wording, leave R-HMA27-04 as escalate. C. Leave ungated. | **A.** | A: HMA 27 stops firing on no-proceeding questions; with D1, exact can reach 16/16. B: gate never drops — contradiction persists. C: plan §3.2 hold continues, 10/10 blocked on sections. No GT invalidation from D2 alone. |
| D3 | H7 escalate expectation (rater confirms) | A. Keep True, add `kind: fact` with named ask. B. Flip to False. | **A.** | A: no GT change, no invalidation; H7 correct, 12/16 → 13/16 on this row alone. B: GT change → invalidates all prior runs; asserts the system can give the complete next step without the DOB, which is false. |
| D4 | H15 escalate expectation (rater confirms) | A. Keep True, re-ground on fact/proof kind. B. Flip to False. | **A.** | A: no GT change, no invalidation. B: GT change → invalidates all prior runs; asserts a sold-gold claim with no proof/value needs no follow-up. |
| D5 | H2/H4 escalate expectations + typed kinds (coordinator; rater confirms as-is) | A. Keep both True; add fact kinds (Lane 2's four kinds implement this). B. Flip either/both to False. C. Keep True, leave kinds as-is. | **A.** | A: no GT change, no invalidation. **A + D3 + D4 together move v5 predicted escalates 12/16 → 16/16**; gate formula moves 9.8 → 10.0 formula — still capped 9.0. B: GT change → invalidates all prior runs. C: escalates stays 12/16, G9 can never pass. |
| D6 | H14 HMA 13 — keep or drop (rater) | A. Keep. B. Drop. | **A (keep)**, rater-confirmed — weakest call in the set, rater may reasonably choose B. | A: no change. B: GT change → invalidates all prior runs; GT 57→56 (53→52 with D1-A); notebook's pending-divorce fire of HMA 13 must be gated in the same change. |
| D7 | H4 PWDVA 20 exclusion — confirm (rater) | A. Confirm exclusion. B. Add PWDVA 20. | **A.** | A: no change. B: GT change → invalidates all prior runs; forces re-examination of every residence question's s.20 treatment. |
| D8 | H5 sub-choice fix + audit trail (notebook lane) | A. Derive custody sub-choice from `proceeding_pending`/being-filed fact; record HMA 26 drop in `gated_out`. Fix divorce-gate text the same way. B. Leave as-is. | **A.** | A: no GT change, no invalidation; no score change expected; auditability + fresh-set generalisation improve. B: next fresh question with a wrong sub-choice and wrong kept set will be undebuggable. |
| D9 | Typed-escalation design (coordinator) | A. Add fact kind(s) alongside quantum/court/demand; score from the applicable kind, never from quantum boilerplate. B. Keep three kinds only. | **A** (implemented as Lane 2's four kinds, §3). | A: the four fact-ask questions become scorable-correct without GT change. B: escalates caps at 12/16, G9 can never pass. |
| D10 | Rating formula discrepancy (coordinator) | A. Gate §2 formula governs. B. Adopt the v5 formula by amending the gate doc. | **A** — gate states its formula is frozen; §6.9 forbids changing metrics mid-tuning. | A: ratings restated (v3 5.0, v4r 7.3); no GT impact. B: requires a gate amendment, which per §6.9 invalidates the "10/10" label until re-passed. |
| D11 | H15 `demand_made: true` annotation (rater) | A. Confirm (sale = refusal evident). B. Set False/None. | **A**, inference recorded in the annotation. | Either way: no GT change, no invalidation — BNS 316 stays via the demand-first fallback; only the escalation kind changes. |

**Who decides what:** rater decisions (independent of the tuning lane): D1, D3 (confirm), D4
(confirm), D6, D7, D11. Coordinator decisions: D2, D8, D9, D10. **Nivedh decisions:** strictly
none of the above, except (i) whether to authorise the new FCA label (D1-C) as a label the
system should produce — a product-scope choice; and (ii) being told plainly that the HMA 27
correction invalidates the v4r/v5 runs and requires re-running them (a gate-rule consequence,
not a preference — but the headline "10/16 → predicted 16/16" story is re-based by it).

---

## 5. Prose renderer design (Lane 4)

**Template-based assembler, NOT free generation.** Free generation can only be checked post-hoc,
and one slip caps the run at ≤ 5.0. Templates keyed to `kept_ids` + facts + kept court only
(never question text, never a model, zero model calls). Exact templates are given in Lane 4 §2
for: maintenance-only (H1/H8/H9/H11 variants), stridhan-only (H3 held / H15 sold),
custody-only (H2), residence-only (H4), birth-certificate (H7), divorce variants (H5/H14), and
K0 multi-issue — plus worked renderings against the v5 predicted kept sets (§3, NOT live results).

**Corrections to the existing `prose-renderer-design.md` (4 bugs + 1 gap, Lane 4 §4):**
1. Its maintenance template asserts a child/school fees on childless questions (H8/H9/H11) —
   fixed with new annotation-only Cell 6 facts `child_fact`, `school_fees_fact`, `stridhan_sold`
   (values tabulated for the 16; GT untouched).
2. Its residence paragraph asserts a residence right when only `pwdva-18` is kept (H5) — base
   sentence now conditional on `pwdva-17`/`pwdva-19`.
3. Divorce paragraph wrong tense when a proceeding is pending (H14) — pending variant added.
4. Stridhan-sold variant for H15, flagged for legal confirmation.
5. No-escalation gap (H2/H4, H7/H15 under v5) — left as a coordinator decision (now resolved by
   §3's kinds; the renderer keys escalation lines to the typed kinds).

**Forbidden prevention by construction (Lane 4 §5):** full 9-item prevention table — e.g.
precedent citations only from an allow-list keyed to kept sections; court named from the kept
court field, never asked; no amount numbers (escalate instead); birth certificate under the
correct Act; plus the existing §8 self-checker adopted verbatim with two new tripwires
(Addition A: residence-right sentence without a residence section; Addition B: child/school-fee
sentence without the fact).

**Prose scoring protocol (G12, Lane 4 §6):** independent rater, blind to the checker, rater wins
on disagreement, 25% double-rating. Per-question record fields the notebook must emit: `prose`,
`prose_citations`, `prose_court_named`, `prose_amounts_stated`, `prose_forbidden_hits`,
`prose_render_ms`, `prose_template_version`, `prose_facts_used`. Prose lives in a **new Cell 9**
(after Cell 8); it needs zero model calls (~ms/question), so it cannot affect latency or any
classification metric, and it can be **rehearsed offline** against the filed v4r/v5 JSONs before
any live run.

---

## 6. Latency — G14 fails on v4r too, and CPU cannot fix it (Lanes 4 + 5)

Measured from the filed v4r JSON (correcting `latency-analysis.md`, which quoted v3 figures):

| Run | Mean / question | Max / question | Full run (excl. load) | Load | G14 (≤15 s / ≤30 s / ≤240 s / ≤60 s) |
|---|---|---|---|---|---|
| v1 | 11.77 s | 24.17 s | 188.4 s | 25.8 s | ✅ PASS |
| v3 | 56.09 s | 122.92 s | 897.5 s | 28.9 s | ❌ FAIL |
| v4r | **57.6 s** | **133.32 s** | **921.6 s** | 29.0 s | ❌ FAIL |

Cause is sheer inference count, not a slow call: **105 `agent.predict` calls / 728 inferences per
16-question run** (682 `noul` + 46 `choice`), ~1.27 s/inference on Colab CPU. The three passes
re-score the same question three times (full → every clause → aux) with nothing shared or cached.
No question is below 32 `noul` keys; cheapest observed question (H9) took 36.31 s; K0 took 133.32 s.

Verified score-preserving trims (Lane 4 §7.3–7.4, all verified offline on the v4r JSON):
O1 skip clause pass when C == 1 (40 keys); O2 drop residence R0 (45 keys net); O3 skip an
issue's aux prompts once it already fires pre-aux (**106 keys — verified, firing unchanged on all
16**; H5's custody is automatically protected since it doesn't fire pre-aux); O4 restrict
`in_scope`/`divorce_pending` to full question (58 keys net; no boolean change on the 16, low
fresh-set risk for clause-only pending signals); O5 drop dead sub-choice calls (12 keys in v5).
**Combined: ~584 s/run, mean ~36.5 s, max ~61 s — still a G14 failure by 2.4×.**

**G14 is unachievable on Colab CPU with this architecture.** The only intact-recall route is a
recorded **T4 GPU run** (trimmed, ~92–184 s at the unverified 0.2–0.4 s/inference planning figure
— must be measured). Consequence (Lane 5 §5.4): G14 is a gate row, and G1–G14 must all pass for
the gate pass that precedes confirmation — **until G14 is addressed, no run can be a gate pass
and the confirmation protocol cannot start, whatever the section scores are.** Decide the
hardware class before run 1 of the confirmation pair; run 1 and run 2 must be the same class.

**"Fraction of a second" classification is not achievable** with this model on CPU, and not with
this architecture at all (lowest observed per-inference cost 1.10 s, lowest per-call cost 7.3 s).
It needs a single-forward-pass multi-label head + GPU/quantised serving + bypassing
`agent.predict` overhead — a model rebuild with real recall risk, **out of scope for v6**.
The user should be told this plainly: the gate's G14 (≤15 s/question) is the achievable target,
not sub-second.

---

## 7. Validation readiness (Lane 5)

### 7.1 Freeze check — sound in substance, gaps in record
Both sealed SHA-256s recomputed and match the freeze note
(fresh-20 `1d8b5dc3…8837`, Kannada-8 `2f652af1…5853`). Blind writer (only the backtest read),
GT fixed before any sealed run, zero 8-gram overlap, Kannada script confirmed (0.83–0.87
Kannada-char fraction on all 8), Kannada composition matches the gate's 8 elements exactly.
Missing: no rater name/ID recorded; no Kannada-fluency evidence (recommend one independent
Kannada-fluent check of the KN GT *before* the Kannada gate run, read-only); `frozen_date`
"2026-11-27" vs file mtime 26 Nov 23:51 IST (UTC/IST slip — one-line addendum, do not touch
the JSONs); no checksum on the freeze note itself (hash it now, file the hash, addenda as
separate dated files); no backup location recorded. The open HMA 27 dispute threatens the
freeze: sealed sets also contain HMA 27 in GT, so a GT change invalidates all prior runs on
every affected set — decide D1 *before* the fresh run.

### 7.2 Fresh-16 vs fresh-20 — amend the gate, do not touch the sealed sets
The gate says fresh 16 with its own composition table; the sealed file has 20 built to a
different, mostly stricter table (6 questions with ≥5 GT sections, 3 negations, first-ever 13B
GT, judicial separation). Two gate elements aren't verifiably present in the 20
(salary-slips-missing, no-proceeding interim money). **Recommendation: amend G2 to 20/20
before any fresh run**, with a dated amendment footer (approval recorded in the coordinator log;
G2 row, §4 composition table replaced verbatim with the freeze note's table, §4 step 6, §8
checklist, §3 tier table row 10 updated). Never trim 20→16 (selection bias + coverage loss).
Record the two missing elements as accepted composition deviations. Until the amendment is made,
the fresh gate is ambiguous and **no fresh run may be scored against it**. The v6 sealed runner
must read the set size from the JSON (20) and report "20/20", not hardcode 16. Note the F20
escalate rule: F20 has empty GT/court but `escalates: true` (human-lawyer handoff) — the scorer
must apply the F20-specific rule, not mark it a failure.

### 7.3 Confirmation re-run protocol (G15, Lane 5 §4)
Preconditions: run 1 filed complete and passing **every** gate row G1–G14 on **all three sets**
with prose Fp = 0 measured; H7/H15 and HMA 27 decisions resolved *before* run 1; G14 passing on
run 1. Frozen artefact list (all SHA-256, recorded in both run files): notebook `.ipynb`,
builder script, graph JSON (+ 32/46/77 assert), all thresholds/prompts/phrasebook/fact
annotations/gate constants (covered by notebook SHA), test-set files (sealed SHAs re-verified
immediately before run 2), prose renderer + checker (Cell 9, version string), model + snapshot +
`laya` version, Colab runtime (fresh process for run 2; same hardware class as run 1 — a class
change is a declared deviation). Protocol: freeze declared in coordinator log → re-verify all
hashes → fresh Colab process, same `.ipynb`, cells 0–9 in order, no in-browser edits (a cell
error means stop, file the failed attempt, diagnose offline) → all three sets in the same run,
same order → file run 2 with mandatory comparison table. Comparison cases: identical (≤0.005
per score, no flag flips) → confirmation passes; passes with larger score divergence → passes
with a reproducibility note (coordinator decides whether to claim or run a third confirmation);
any row fails → confirmation fails, no 10/10, fix resets confirmation entirely; nondeterminism
with flag flips → reproducibility failure, not bad luck, do not average or cherry-pick.
**Margin watch (report to 4 decimals in both runs):** H5 custody aux 0.2189 vs 0.20 (margin
0.0189); H1 stridhan clause 0.7545 vs H3 true 0.7868 (gap 0.032); guard bar 0.80 vs genuine
aux-rescue cluster 0.8495–0.9018 (gap 0.0495); any per-question score within 0.05 of threshold
goes in a "margin table" in every run MD from v6 onward.

### 7.4 Run filing audit (Lane 5 §5)
Run numbers are **global and sequential, never reused, never per-version**: run 0 = v1, run 1 = v3,
run 2 = v4r. Next live run (v5) is **run 3**; v6 live run is **run 4**; confirmation takes the
next number after the gate-pass run. v4 and v4.1 were built but never run live (mark superseded
in the log rather than leaving pending rows); v5 built, no live run (prediction only); no
sealed/prose/confirmation runs. Coordinator log run table is stale (no v4r row — correct it).
v1 notebook SHA was never recorded (unrecoverable; note it). v4r MD omits latency and the §2
rating computation — every run MD from v6 onward must include both.

---

## 8. What the v6 notebook must contain (merged spec)

**Cells:** keep Cells 0–8 structure; add **Cell 9 prose renderer** (Lane 4 §2 templates verbatim,
§7 cell plan). Cell 6: add `money_fact`/`gold_fact` (v5, for comparison only — never gate inputs
once extraction ships) + new annotation-only facts `child_fact`, `school_fees_fact`,
`stridhan_sold` (Lane 4 §1.4, values tabulated for the 16; GT untouched). Cell 7: v5 Fixes 1–4
**with Lane 1's verdicts applied** — Fix 2 regex custody gate is demoted to a *stopgap* pending
the new per-clause choice node (§2); Fix 1 gates run on **model-extracted** facts after the dry
run (§2), with hand facts kept for comparison; Fix 3 guard keeps bar 0.80/ceiling 0.01 **plus**
the flag-and-escalate fallback for lifts in [0.50, 0.80) and near-threshold fires; Fix 4 H14
route as shipped; D2 HMA 27 gate (drop) in the same change as D1; D8 sub-choice derivation +
audit trail; O1–O5 latency trims (re-verify O3 on the v5 live JSON before shipping); per-call
timing instrumentation. Cell 8: gate-formula §2 rating with full arithmetic shown; §8 checklist
ticked per row with actuals; latency aggregates (mean/max/total/load); margin table; per-question
fields per Lane 5 §6.2; `escalation_kinds` per row + `escalates_on_empty_kept` guard (§3);
`gated_out` with distinct reasons per veto; `money_fact`/`gold_fact`/`custody_claim`/
`custody_gated` (pre-gate final too), `single_issue_guard` {armed, dominant, blocked},
extraction values + bands + flags (§2). **Sealed runner:** verifies sealed SHAs first, never
emits sealed wording (IDs + scores only), reads set size from the JSON (20), enforces the
F20 human-lawyer rule, validates guard bar/ceiling read-only (v5 §7 item 7 — do not tune the
bar on the fresh set). **Run numbering:** global sequential (next live run is run 3 for v5,
run 4 for v6); run number printed in Cell 8 output and output filenames; frozen artefact
hashes recorded at build time.

**One-change rule (gate §4 step 3):** v6 as specified here bundles several changes (extraction,
escalates kinds, HMA 27 gate, prose Cell 9, latency trims). The gate says fix ONE thing per
cycle. The coordinator must decide the sequencing: recommended order is (a) v5 live run first
(run 3, unchanged v5 — it is the only way to confirm the 16/16 prediction before building on
it); (b) v6 as the escalates + HMA 27 + extraction dry-run build, with prose rehearsed offline
first; (c) sealed runs only after the current 16 passes under the corrected GT. Do not run the
sealed fresh-20 as a tuning set at any point.

---

## 9. Path to 9/10 — two branches (coordinator decision)

**Branch A — decide D1 before the v6 live run (recommended by Lanes 3 + 5).** Rater settles
HMA 27 (D1-A or D1-C) and H14/HMA 13 (D6) first; D2 gate ships in the same logged change; all
prior runs are invalidated and re-run under the corrected GT (GT 53 under A, 57 under C with a
new label the system must learn to produce). The v5 "predicted 16/16" is discarded and
re-predicted under the corrected GT. Honest, but the headline progress re-bases: v4r re-scores
8/16 exact under D1-A before the gate is applied.

**Branch B — defer D1, run v6 under the old GT.** The v5 prediction stays testable as-is and the
9.0 capped rating is reachable fastest. Cost: the system ships a known-wrong label (HMA 27 on
no-proceeding questions) and the sealed sets carry the same error, so the GT correction — when
it comes — invalidates the v6 run too. Only defensible if D1 is decided immediately after the
v6 live run, before any sealed run.

Either branch, the 9/10 minimum is met by a **live 16/16 current-set pass (capped 9.0)** — never
by the 9.8 raw formula output, never by the offline replay, never before the live v5/v6 run
exists. 10/10 additionally needs: fresh 20/20 (after the G2 amendment), Kannada 8/8, prose
Fp = 0 measured, G14 passing (T4), and the G15 confirmation re-run with zero changes.

---

## 10. Decisions needed (merged — owners in §4.3 / §7)

| # | Decision | Owner | Blocks |
|---|---|---|---|
| D1 | HMA 27 GT correction (A remove / C replace label / B reject) | Independent rater (read *Astha Thakur* first) | Everything downstream — invalidates all prior runs; decide before any sealed run |
| D2 | HMA 27 corrected rule + gate, paired with D1 | Coordinator + notebook lane | 16/16 on sections under corrected GT |
| D3/D4/D5 | H7/H15/H2/H4 escalate expectations (keep True) + Lane 2 kinds | Rater confirms; coordinator implements | G9 (16/16 escalates) |
| D6/D7/D11 | H14 HMA 13 keep; H4 PWDVA 20 exclusion confirm; H15 demand_made confirm | Independent rater | GT stability |
| D10 | Gate formula governs (restate v3 5.0, v4r 7.3) | Coordinator | Any rating quoted from now on |
| G2 amendment | Fresh gate 16 → 20, dated footer | Coordinator (parent approves in writing) | Any fresh run being scored |
| Hardware | T4 GPU run for G14 (recorded, same class for run 1 + run 2) | Coordinator / parent | Any gate pass; confirmation cannot start without it |
| Prose | Template renderer + rater identity + stridhan-sold wording sign-off | Coordinator / rater | G12 (Fp measured) |
| Freeze record | Rater name/ID, Kannada-fluency evidence, freeze-note hash, backup location | Coordinator | Kannada gate run; audit completeness |
| Colab access | nivedhbhat15 Google password (rejected twice ~07:08 IST; passkey unusable in cloud browser) | **Nivedh** | Every live run (v5, v6, sealed, confirmation) + Gemini consultation |

---

## 11. Blockers and caveats

1. **Live runs blocked:** Google rejected the saved nivedhbhat15 password twice ~07:08 IST and
   the only other option was a passkey the cloud browser cannot use. Same block hit the Gemini
   consultation. No live run can execute until the parent resolves Colab access. All v6 work
   above is offline design until then.
2. **No v5 live result exists.** The "16/16, 9.6" prediction is an offline replay of v4r scores
   through v5 code. Under the gate formula it is 9.8 raw → capped 9.0. Nothing in v5 may be
   quoted as measured until run 3 is filed.
3. **HMA 27 re-bases the story.** If D1 is adopted, the v5 prediction falls away and v4r
   re-scores 8/16 under the corrected GT before the gate is applied. Tell the user plainly.
4. **Sub-second classification is not achievable** with this model/architecture (§6). G14
   (≤15 s/question) is the achievable target, via T4.
5. **Lane caveats:** Lane 3's Q1 authorities are as recorded in v4, not re-verified by fresh
   browser research; *Astha Thakur* full judgment unread. Lane 1's paraphrases are test items,
   not tuning inputs, and need a non-tuning rater's approval before use. Lane 4's T4 latency
   figures (0.2–0.4 s/inference) are unverified planning estimates. Lane 5's freeze findings are
   metadata-only (no sealed wording read).

## Sources (lane files)
- `v6-lane1-generalisation.md` — per-FP verdicts, paraphrase tests, model-extraction design
- `v6-lane2-escalates.md` — four-kind design, H7/H15 arguments, Cell 8 spec
- `v6-lane3-legal-decisions.md` — HMA 27 verdict + corrected wording, decision table D1–D11
- `v6-lane4-prose-latency.md` — template renderer, latency verification + trims, Cell 9 plan
- `v6-lane5-validation.md` — freeze check, formula table, confirmation protocol, run audit
- Base: `v5-precision-report.md`, `laya-10-10-gate-definition.md`, v4r live JSON
  (`workspace/browser_downloads/sess-2184034649/browser-download-20261126T185447.300061282Z-0-live-laya-colab-results-v4r-residence-only.json`)
