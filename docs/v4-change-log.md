# v4 change log — residence precision + Lane A PRIMARY thresholds

**Base:** `live-laya-colab-test-v3-empty5.ipynb` (v3 live, 2026-11-26:
exact 5/16, mean P/R 0.673/0.866, micro P/R 0.671/0.895, TP/FP/FN 51/25/6,
court 11/16, escalates 14/16, residence fired R1 11/16 vs R0 5/16).
**Builder:** `build_laya_v4_residence.py` (derived from
`build_laya_v3_empty5.py`; Cells 7–8 produced by surgical replacements on
the on-disk v3 notebook sources, each asserted to occur exactly once).
**Notebook:** `live-laya-colab-test-v4-residence.ipynb` (9 cells).
**sha256:** `af1d6a5d4749bd1e72389885081cadcc13171ea0e28e16977776f69a56e1a45b`
**Validation:** JSON parses; `nbformat.validate` PASS; Cells 7–8 compile
(`compile()` check) PASS; cells 0–5 byte-identical to v3; Cell 6 exec
reproduces the test set with GT/facts identical to v3 except the new field.

**Status: NOT RUN.** No live Colab run was done (no live browser in this
lane). Everything in §5 is a PREDICTION computed offline from the v3 live
scores — labelled PREDICTED throughout, not a result.

## 1. Exact diff vs v3

### Cell 6 — test set (only change: +7 header lines, +16 facts lines)
- New frozen facts field `residence_claim` (bool) on all 16 questions,
  inserted after the `violence` key of each facts dict (see §2 for the
  rule and values). Ground truth, questions, `court_expected`,
  `escalate_expected`, and all other facts fields are byte-identical to
  v3 (verified by exec-comparing the Cell 6 `TEST_SET` against v3's).
- Header comment extended to document the new field and its rule.

### Cell 7 — Stage 1 + Stage 2 (16 surgical replacements)
1. **Thresholds (Lane A PRIMARY vector):** maintenance **0.05** (v3 0.10),
   custody **0.13** (v3 0.20), residence **0.15** (unchanged value),
   divorce-asked **0.40** (v3 0.45), divorce-pending **0.13** (v3 0.12),
   stridhan 0.50, violence 0.50, birth_certificate 0.50, in_scope 0.50
   (unchanged). See §4 for the brief-ambiguity note on the divorce values
   (behaviourally moot — no v3 live final falls in the delta bands).
2. **Residence prompt reverted R1 → R0.** `RESIDENCE_PROMPT = 'R0'`;
   `TRACK = {'residence': 'residence'}`. The R0 text is the exact v1
   prompt, copied verbatim from v1 Cell 7 (verified present in v3 Cell 7
   before the edit):
   `Does this question ask about staying in, or being thrown out of, the shared house, or about protection from threats or violence at home?`
   R1 is still asked and recorded per question (full + clause-max) for
   diagnosis and never fires.
3. **Residence final = max(R0 full, R0 clause-max, aux residence max)**,
   threshold 0.15 — same max-pool shape as v3, R0 in place of R1.
4. **NEW residence fact gate (Stage 1, before firing):** if
   `facts['residence_claim']` is False, residence final is forced to 0.0
   and residence can never fire; a `gated_out` entry is recorded:
   `residence: gated, no residence claim in facts (residence_claim=false)`.
   If True, residence fires per the R0 score. `fired_clause` /
   `fired_source` for residence stay as computed (what *would* have
   fired) — only the final score is forced. `gated_out_a` initialisation
   moved to the top of the `try` block so the gate can append to it.
   New per-question record fields: `residence_claim`, `residence_gated`,
   `residence_sub_choice_info`.
5. **Residence full-set (Stage 2):** when residence fires, keep
   PWDVA 17 + 18 + 19 as a set (`kept_pre |= {'pwdva-17', 'pwdva-18',
   'pwdva-19'}`). The old sub-choice split logic
   (`residence_sub_issue` / `protection_vs_residence` branching, incl.
   the `Money cut off → PWDVA 20` arm) is deleted from Stage 2. The
   sub-choice calls still run for a fired residence issue; their outcome
   is recorded in `rec['residence_sub_choice_info']` for information
   only and never splits the set.
6. **Violence → PWDVA 18 path completely untouched** (`if 'violence' in
   fired and 'residence' not in fired: kept_pre.add('pwdva-18')`).
7. Header comments updated (v4 scope, PRIMARY vector, R0-fires note,
   note 5 corrected to say the residence fact gate IS fitted in v4,
   new note 8 documenting the gate + full set).

### Cell 8 — scoring (11 surgical replacements)
1. Version string → `v4-residence (...)`; output files →
   `live-laya-colab-results-v4-residence.json` / `.md`; print header →
   `(v4 residence)`; md title → `Colab run v4-residence`.
2. Aggregate gains `v3_baseline_reference` (v3 live numbers) alongside
   the v1 reference, plus `residence_fired_r1_count_at_0.15_diagnostic`,
   `residence_fired_count` (actually fired), `residence_gated_count`.
3. **Residence R0-vs-R1 table key fix:** v3 read
   `stage1_clause_max['residence_r0']` (a key that does not exist, so
   its R0 clause-max column was always `None`) and `['residence']` (the
   R0 clause-max) for R1 — the v3 table mislabelled R0 clause-max as R1.
   v4 reads the true keys (`'residence'` = R0 clause-max,
   `'residence_r1'` = R1 clause-max) and adds aux residence max, R0/R1
   finals, `residence_claim`, `residence_gated`, `residence_fired`
   columns (print + markdown tables).
4. `esc_live` line **unchanged, verbatim from the on-disk v3 notebook**:
   `esc_live = bool(kinds & {'quantum', 'court', 'demand'})`
   (the 2026-11-26 patch; the builder asserts its presence before and
   after the Cell 8 edits). Known stale comment carried over from v3
   (not introduced by v4): the Cell 8 header still describes the flag
   as "quantum/court" while the patched line also includes 'demand'.
   Left as-is — out of v4 scope; recorded here so it is not mistaken
   for a v4 change.

### NOT changed
Ground truth, any other facts field, court logic, escalate logic,
clause-split rules, aux prompts, the HMA 25 gate (both layers + shadow
test, still present in Cell 7), graph v2 JSON, cells 0–5. No
per-question special cases, no hardcoded question-ID branches beyond
the frozen `residence_claim` facts annotations in Cell 6 (same status
as v3's facts annotations).

## 2. residence_claim — rule and values

**Rule (documented in the builder, Cell 6 header, and Cell 7 note 8):**
true iff the question states eviction / lockout / being thrown out /
changed lock / cannot enter the house, OR a claim to stay in the shared
house, OR a threat to throw the person out.

| ID | claim | Evidence in the question text |
|----|-------|-------------------------------|
| K0 | **True** | "They are throwing me out of the house" |
| H1 | False | money only, no house claim |
| H2 | False | "he will take him [son] away" — custody, not a house eviction |
| H3 | False | gold only |
| H4 | **True** | "They changed the lock and I cannot enter my house" |
| H5 | False | "I want my daughter to stay with me" — custody stay, not a house-stay claim |
| H6 | **True** | "to stay in the house with my daughter" |
| H7 | False | birth certificate only |
| H8 | False | maintenance only |
| H9 | False | maintenance only |
| H10 | False | gold + money only |
| H11 | False | money only |
| H12 | False | ancestral-house ownership / stop-sale dispute, no eviction or stay claim |
| H13 | **True** | "throws me out of the house" |
| H14 | False | "I want my son to stay with me" — custody stay, not a house-stay claim |
| H15 | False | gold sold only |

**Rule-vs-list check: NO discrepancy.** Every value above follows from
the rule as written. The two judgement calls are H5/H14: "stay with me"
is a custody stay, not a claim to stay in the shared house, so both are
False under the rule — this is stated explicitly in the builder and in
Cell 6 so a later reviewer can see it was deliberate, not an oversight.

## 3. R0 scores the gate actually sees (from v3 live data)

R0 final = max(R0 full, R0 clause-max, aux residence max), threshold 0.15:

| ID | R0 full | R0 clause-max | Aux residence max | R0 final | Would fire on R0 | claim | v4 residence fires |
|----|---------|---------------|-------------------|----------|------------------|-------|--------------------|
| K0 | 0.2650 | 0.7674 | 0.8905 | 0.8905 | yes | True | **yes** |
| H1 | 0.0968 | 0.0453 | 0.0947 | 0.0968 | no | False | no |
| H2 | 0.8247 | 0.8464 | 0.3813 | 0.8464 | yes | False | **no — gated** |
| H3 | 0.0570 | 0.1727 | 0.1285 | 0.1727 | yes | False | **no — gated** |
| H4 | 0.1267 | 0.1254 | 0.6474 | 0.6474 | yes | True | **yes** (via aux — R0 full and clause-max are both < 0.15) |
| H5 | 0.4882 | 0.3523 | 0.2143 | 0.4882 | yes | False | **no — gated** |
| H6 | 0.2173 | 0.2820 | 0.7318 | 0.7318 | yes | True | **yes** |
| H7 | 0.0001 | 0.1307 | 0.0001 | 0.1307 | no | False | no |
| H8 | 0.1008 | 0.1008 | 0.1177 | 0.1177 | no | False | no |
| H9 | 0.0608 | 0.0608 | 0.0638 | 0.0638 | no | False | no |
| H10 | 0.1461 | 0.1067 | 0.1901 | 0.1901 | yes | False | **no — gated** |
| H11 | 0.0555 | 0.0555 | 0.0895 | 0.0895 | no | False | no |
| H12 | 0.0468 | 0.2177 | 0.1330 | 0.2177 | yes | False | **no — gated** |
| H13 | 0.4212 | 0.4212 | 0.8786 | 0.8786 | yes | True | **yes** |
| H14 | 0.1225 | 0.1550 | 0.1021 | 0.1550 | yes | False | **no — gated** (barely above threshold) |
| H15 | 0.0670 | 0.0712 | 0.0847 | 0.0847 | no | False | no |

Two facts this table establishes: (a) reverting to R0 alone does **not**
fix H2 — its R0 clause-max is 0.8464 ("take him away" read as a threat);
only the fact gate blocks it. (b) H4's R0 fire depends entirely on the
aux prompt (0.6474); without aux, R0 full (0.1267) and clause-max
(0.1254) both miss 0.15.

## 4. Brief-ambiguity note (divorce thresholds)

The task lists divorce-asked 0.40 / divorce-pending 0.13 while also
saying "(v3 used maintenance 0.10, custody 0.20 — change ONLY
maintenance and custody to the PRIMARY vector values)". The listed
values are applied (divorce-asked 0.45→0.40, divorce-pending 0.12→0.13).
This is behaviourally moot: no v3 live final falls in the divorce delta
bands (asked in [0.40, 0.45), pending in [0.12, 0.13)), so divorce
firing is identical under either reading. The firing changes that DO
matter come from maintenance 0.05 and custody 0.13 (see §5).

## 5. PREDICTED outcome (not a result — computed offline from v3 live scores)

**Method.** Applied only the v4 changes to the v3 live per-question
scores (`raw_live_runs` in the v3 results JSON): residence fires iff
R0 final ≥ 0.15 AND `residence_claim` is True, then keeps 17+18+19;
violence path untouched (PWDVA 18 when violence fires and residence
does not); PRIMARY thresholds M 0.05 / C 0.13 / D-asked 0.40 /
D-pend 0.13; all other issues at their v3 firing. Newly fired
maintenance/custody are assumed to contribute only their forced base
sets (maintenance → BNSS 144 + PWDVA 20; custody → GWA 1890 + HMGA s.6
+ WELFARE) — HMA 24/26 cannot survive the recheck on any question
except H14 (proceeding pending, where v3 already kept them), and
HMA 25 is gated. Sub-choice picks for newly fired issues cannot be
known offline, but no sub-choice can remove a base set, so the FP
counts below are lower bounds on the predicted damage, not guesses.
Live scores are assumed to reproduce v3's recorded R0/R1/aux scores
(same model, same prompts, deterministic). Rating uses the frozen
formula: 0.4·exact + 0.3·micro-F1 + 0.15·court + 0.15·escalates.

### 5a. v4 AS SPECIFIED — PREDICTED: exact 6/16, TP/FP/FN 57/27/0, micro-P/R 0.679/1.000, micro-F1 0.809, mean P/R 0.684/0.938, court 11/16, escalates 15/16, rating ~6.4/10 (v3 live: 5.9/10)

| ID | PREDICTED exact | TP | FP | FN | Court | Escalates | What changes vs v3 |
|----|-----------------|----|----|----|-------|-----------|--------------------|
| K0 | yes | 10 | 0 | 0 | ✓ | ✓ | unchanged (residence fires, full set = v3 kept set) |
| H1 | no | 2 | 2 | 0 | ✗ | ✓ | unchanged (BNS 316 + HMA 27 FPs remain; residence contributed only PWDVA 20, already via maintenance) |
| H2 | no | 3 | 2 | 0 | ✗ | ✓ | residence FPs (17/18/19) GONE, but maintenance **newly fires at 0.05** (final 0.082) → BNSS 144 + PWDVA 20 FPs replace them; escalates fixed (quantum) |
| H3 | no | 2 | 2 | 0 | ✓ | ✓ | residence FPs (17/19) gone; BNSS 144 + PWDVA 20 FPs remain |
| H4 | no | 3 | 2 | 0 | ✓ | ✓ | residence fires (via aux), full set kept; but maintenance **newly fires at 0.05** (final 0.0844) → BNSS 144 + PWDVA 20 FPs; exact LOST vs v3; escalates fixed (quantum) |
| H5 | **yes** | 7 | 0 | 0 | ✓ | ✓ | residence gated → 17/19 FPs gone; **PWDVA 18 returns via the untouched violence path** (violence final 0.8343) |
| H6 | no | 5 | 3 | 0 | ✗ | ✓ | residence FNs 17/18/19 FIXED (full set); custody FPs (GWA/HMGA/WELFARE) remain — not a v4 fix |
| H7 | no | 1 | 5 | 0 | ✗ | ✓ | custody **newly fires at 0.13** (final 0.1372) → +3 FPs (GWA/HMGA/WELFARE); worse than v3 |
| H8 | yes | 2 | 0 | 0 | ✓ | ✓ | unchanged |
| H9 | yes | 2 | 0 | 0 | ✓ | ✓ | unchanged |
| H10 | no | 4 | 3 | 0 | ✓ | ✓ | residence FPs (17/18/19) GONE, but custody **newly fires at 0.13** (final 0.1713) → +3 FPs; not exact |
| H11 | yes | 2 | 0 | 0 | ✓ | ✓ | unchanged |
| H12 | no | 0 | 5 | 0 | ✗ | ✗ | residence FPs gone, but maintenance (0.0824) + custody (0.1397) **newly fire** → 5 FPs (was 3); does NOT stay empty; escalates now WRONG (quantum True vs expected False) |
| H13 | **yes** | 5 | 0 | 0 | ✓ | ✓ | residence FNs 17/19 FIXED (full set; 18 already there) |
| H14 | no | 7 | 1 | 0 | ✓ | ✓ | unchanged (residence sub-choice contributed nothing in v3; GWA FP remains — not a v4 fix) |
| H15 | no | 2 | 2 | 0 | ✓ | ✓ | unchanged |

**Expected fixed (as the brief hoped):** H13 FN 17/19 ✓, H6 FN
17/18/19 ✓. **Expected fixed but PREDICTED NOT fixed:** H2, H10, H12
residence FPs are removed, but the PRIMARY thresholds add replacement
FPs on the same questions (maintenance on H2, custody on H10,
maintenance + custody on H12), so none of the three becomes exact —
H12 gets worse (FP 3→5, escalates flips to wrong). H4 LOSES its v3
exact status the same way. **Contrary to the brief's remain-list:**
H5's PWDVA 18 is PREDICTED FIXED, not remaining — once residence is
gated out, the untouched violence path (`violence fires, residence
not fired → PWDVA 18`) fires, and H5 becomes exact. That follows
mechanically from the v4 rules as written; if the intent was for H5's
18 to stay missing, the violence path would have to be changed, which
the brief forbids.

### 5b. Counterfactual — residence fix ONLY, v3 thresholds kept (M 0.10 / C 0.20 / D 0.45/0.12): PREDICTED exact 10/16, TP/FP/FN 57/12/0, micro-P/R 0.826/1.000, micro-F1 0.905, mean P/R 0.833/1.000, court 13/16, escalates 14/16, rating ~7.7/10

Same residence changes, thresholds untouched. H2, H4, H10, H12 all
become exact (H12 stays empty: kept [], court [], escalates False);
H5 and H13 exact as in §5a; H2/H4 escalates stay wrong (no maintenance
fire → no quantum reason — the known typed-escalation trade-off).
Only H1, H3, H6, H7, H14, H15 remain non-exact, all on out-of-scope
issues (stridhan/maintenance over-fire, custody FPs, birth-certificate
over-fire). This counterfactual is reported so the live run can be
judged fairly: **if v4 live lands near 6/16, the residence fix worked
and the PRIMARY thresholds cost ~4 exact; if it lands near 10/16, the
thresholds did not reproduce their offline effect.** Either way the
numbers, not the prediction, decide — re-score from the live run only.

### 5c. What remains after v4 (predicted, both variants)
H1 (BNS 316 + HMA 27 stridhan over-fire), H3 (BNSS 144 + PWDVA 20
maintenance over-fire), H7 (BNSS 144 + PWDVA 20, plus custody FPs in
the PRIMARY variant), H15 (BNSS 144 + PWDVA 20), H14 (GWA 1890
custody FP), H6-custody (GWA/HMGA/WELFARE FPs). None of these is a
v4 fix; all are left for later versions, as specified.

## 6. Validation performed
- Builder run: `python3 build_laya_v4_residence.py` — exit 0; printed
  sha256 `af1d6a5d...e1a45b` (full value at top of this log).
- Notebook JSON parses; 9 cells; `nbformat.validate` PASS; Cells 7–8
  `compile()` PASS.
- Cells 0–5 identical to the v3 notebook (asserted in the builder and
  re-checked by diff).
- Cell 6 diff vs v3 is exactly +7 header lines and +16
  `residence_claim` lines; exec of Cell 6 gives the §2 values and GT /
  facts otherwise identical to v3.
- Cell 7 diff: 155 changed lines; Cell 8 diff: 84 changed lines
  (comments + the edits in §1). All 16 Cell 7 and 11 Cell 8 replacements
  asserted to occur exactly once at build time.
- `esc_live = bool(kinds & {'quantum', 'court', 'demand'})` asserted
  present in Cell 8 before and after the edits.
- R0 prompt text verified verbatim against v1 Cell 7 before the edit.
- No Colab run, no external model consulted (per task).
