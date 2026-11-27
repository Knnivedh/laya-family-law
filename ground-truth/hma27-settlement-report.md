# HMA 27 settlement + brutal-test bank freeze — merged report

**Status: SETTLED AND FROZEN.** D1 = Option A (user decision 2026-11-27 ~09:46 IST).
**Date:** 2026-11-27. **Work:** offline only — no Colab, no live model runs, no changes
to the sealed fresh-20/Kannada-8 sets, no changes to the v1 GT file.
**Coordinator:** merged from 4 lanes (rater, gate/D2, re-base, bank draft) + second
rater + third-reader adjudication. Lane files are cited at the end.

**One-line summary:** HMA 27 is ancillary and the old ground truth was wrong on four
questions; v2 GT is frozen at 53 sections, the paired D2 gate patch is built and
validated, v4r/v5 re-score under corrected GT as 8/16 → 10/16 (v4r, naive → D2) and
12/16 → 16/16 (v5, naive → D2), and the 230-question brutal-test bank is frozen
(SHA-256 below) after a blind second-rater check and adjudication that corrected five
of its GTs.

## 1. Astha Thakur — verified from the judgment (rater lane)

**Citation:** *Astha Thakur v. Dhananjay Kanwar*, FAO (FC) No. 29 of 2022, Himachal
Pradesh High Court, Division Bench (Vivek Singh Thakur and Romesh Verma, JJ.),
decided **31 December 2025**, neutral citation **2025:HHC:46178** (also 2025 NCHHC
46178). Read via the Indian Kanoon fragment (paras 2, 14, 18, 20, 21) + LiveLaw report.

**What it supports:** (1) s.27's "may" is discretionary — no property provision in the
decree does not strip Family Court jurisdiction; (2) the Family Court retains
jurisdiction under **FCA s.7(1) Expl. (c)** over spousal property disputes even after a
divorce decree (FCA overrides inconsistent HMA provisions); (3) an application labelled
only s.27 must still be decided by the Family Court under FCA s.7, not driven to a
separate suit; (4) a post-decree property decree is treated as part of the divorce decree.

**Critical correction to the lane record (rater lane, stated plainly):** the s.27
application in *Astha Thakur* **was filed during the pendency** of the divorce petition
(HMA Pet. No. 140/2016, decreed ex parte 31.01.2018). It does **not** decide a
freestanding s.27 with no HMA proceeding ever filed — "independent application" in the
LiveLaw summary means independent of the *decree*, not of any proceeding. It supports
D1-A precisely because the correct label for a no-proceeding Stridhan claim is the FCA
s.7 route, not s.27. It does not address BNSS/PWDVA/GWA cases, is a single-HC Division
Bench (not binding outside HP, not SC), and **paras 3–13, 15–17, 19 were not read in
full**. *Balkrishna* / *Babulal* / *Krishna Kumar Gupta* were **not** re-verified
(v4's record stands, unverified).

## 2. v2 ground truth — FROZEN under Option A (rater lane)

- **File:** `ground-truth-v2-hma27-A.json` —
  SHA-256 `87818b1b659583bf06a25280a6b53dabedf65f29cab99058f02b8ed31c9ac97e`
- **Erratum:** `ground-truth-v2-erratum.md` —
  SHA-256 `42012b2b146f299ca9328a97865f215d11b88e945bf8f4471f5e772582f86c71`
- **Change (only change):** HMA 27 removed from K0, H3, H10, H15. GT total **57 → 53**.
  Built programmatically from v1 (verbatim copy, only the four elements deleted, v1
  order/label strings preserved). Courts and escalate expectations unchanged on all 16;
  BNS 316 kept on all four. No Option C file was produced (user rejected C).
- **Affected questions verified from v1 GT, not taken on trust:** K0 (10 → 9 sections),
  H3 ([HMA 27, BNS 316] → [BNS 316]), H10 (4 → 3), H15 ([BNS 316, HMA 27] →
  [BNS 316]) — all with `proceeding_pending: false`, no filing intention in any question
  text. H14 is the only question with `proceeding_pending: true` (and carries no HMA 27
  — the control). The v4/plan count of three affected questions (omitting K0) was wrong.
- **Coordinator cross-check (independent):** diffed the v2 file against the v1 GT
  recorded in the v5 live JSON — the only differences are the four HMA 27 removals;
  courts and escalate expectations are identical on all 16. 57 → 53 confirmed.
- **D3/D4 confirmations (rater, no GT change):** H7 escalate KEEP True, kind
  `procedure` (route turns on unstated facts — DOB/age, place, registration status;
  RBD Act s.13's three delay tiers assign different authorities). H15 escalate KEEP
  True, kind `recovery` (re-grounded on fact/proof — no proof of Stridhan, no sale
  details/value, criminal-route facts unstated; bot cannot value sold gold or file a
  BNS 316 complaint). The old `demand` kind is no longer the reason for H15.

## 3. D2 gate — patch built and validated (gate lane; coordinator re-verified)

- **Patch:** `hma27-D2-gate.patch` (363 lines, unified diff, paths relative to `files/`) —
  SHA-256 `6349c922944275d26bdc38f6c725daee12ddcd25f86f39ae1485f104e507fc04`
- **Validation log:** `hma27-D2-gate-validation.md`
- **Graph changes** (`laya-crpc-bns-section-decision-tree-v2.json`, 17 string-value edits):
  R-HMA27-04 `if_fail` escalate → **drop** with the lane-3 §1.4 wording verbatim;
  the "alternatively… pressed as part of the family-court case for
  maintenance/custody/residence" limb deleted (0 occurrences of "alternatively" remain);
  co-fire rule + BNS 316 exclusion amended everywhere stated — civil route now "HMA 27
  where an HMA proceeding is pending/being filed, otherwise the Family Court property
  suit under FCA s.7(1) Expl. (c) / CPC s.151". BNS 316 stays as the Stridhan criminal route.
- **Notebook changes** (`live-laya-colab-test-v5-precision.ipynb`, Cells 6–7): new frozen
  fact `being_filed: False` on all 16 questions; D2 gate in `stage2()` drops HMA 27 when
  neither proceeding pending nor being filed, recorded in `gated_out` with its own
  distinct reason; BNS 316 not gated. Offline shadow tests pass.
- **Validation (temp copies only; live SHAs verified unchanged):** patch applies clean;
  graph parses with **32 sections / 46 nodes / 77 edges unchanged**; nbformat PASS;
  all 8 code cells compile; Cell 6/7 execute; gate behaviour verified on real facts
  (K0/H3/H10/H15 gated out with BNS 316 kept; H14 pending → HMA 27 kept).
  **Coordinator re-verification:** applied the patch independently to fresh temp copies
  with the correct layout — dry-run OK, applies clean, counts unchanged, 0
  "alternatively", nbformat PASS, all code cells compile. Confirmed.
- **Deviations (reported bluntly):** (1) the brief gave a wrong graph path — canonical
  file is `files/laya-crpc-bns-section-decision-tree-v2.json` (patch paths are relative
  to `files/`; the `colab_bundle/` copy needs the same patch when next bundled);
  (2) no "being-filed" fact existed in Cell 6, so the lane added it as a new frozen
  annotation (all False; H5 "I want a divorce" does not count); (3) "ask once, then
  drop" is only half-implementable — no interactive ask exists in the notebook, so the
  gate drops on the annotated fact and the ask survives as R-HMA27-04's unchanged
  `fact_needed`; (4) GT is NOT changed by this patch (D1 is the rater's job) —
  **the patch must ship in the same logged change as D1, never alone**: applying D2
  alone under old GT makes K0/H3/H10/H15 non-exact by HMA 27 false-negative.

## 4. Re-based scores — v4r and v5 under corrected 53-section GT (re-base lane, offline)

Method validated first: the lane's recomputation reproduces both filed aggregates
exactly under the old 57-section GT, and its court/escalates re-derivations match the
recorded values on all rows. HMA 27 firing verified from recorded predictions (not
assumed): v5 fired it on exactly K0/H3/H10/H15; v4r fired it on those four **plus H1**
(already a false positive there). Proceeding status is unambiguous — false everywhere
except H14 (true, never fired HMA 27); no question text states filing/will file
(H1 "no case filed anywhere", H11 "I have not filed any case yet"); H5's "I want a
divorce" ≠ being filed. D2 therefore drops HMA 27 from all five v4r fires and all four
v5 fires. Mean recall is 1.000 in all four re-scores (FN = 0 throughout).

| Re-score | Exact | Micro-F1 | TP / FP / FN | Court | Escalates | Rating (frozen formula) |
|---|---|---|---|---|---|---|
| v4r naive (corrected GT, recorded preds) | 8/16 | 0.869 | 53 / 16 / 0 | 10/16 | 14/16 | 6.4 |
| v4r D2-adjusted (D2 gate simulated) | 10/16 | 0.906 | 53 / 11 / 0 | 14/16 | 14/16 | 7.4 |
| v5 naive (corrected GT, recorded preds) | 12/16 | 0.964 | 53 / 4 / 0 | 13/16 | 12/16 | 8.1 |
| v5 D2-adjusted (D2 gate simulated) | 16/16 | 1.000 | 53 / 0 / 0 | 16/16 | 12/16 | 9.8 raw → capped 9.0 |

- **v6 expectation CONFIRMED exactly:** v4r naive re-scores 8/16 (H2, H4, H5, H8, H9,
  H11, H12, H13); the two questions lost vs filed 10/16 are K0 and H10, each by the
  HMA 27 false positive alone.
- **Correction to v6 §4.2:** its "14/16" is wrong in both directions — D1-without-D2 on
  v5 is 12/16, not 14/16 (it missed H3 and H15, which also fired HMA 27), and
  D2-without-D1 on old GT is likewise 12/16, not 14/16.
- **D2 recovers all section exactness but NOT escalates:** v5 D2-adjusted is still
  12/16 (H2, H4, H7, H15 — the typed-kinds gap, D3/D4/D5 territory).
- **Caveat:** court-expected is re-derived from corrected GT via the frozen map
  (validated); if the rater had frozen different courts for H3/H10/H15, ratings would
  shift slightly (v4r naive 6.4→6.5, v4r D2 7.4→7.2, v5 naive 8.1→8.2, v5 D2 still
  capped 9.0) — exact / TP-FP-FN / escalates unaffected. The rater lane confirmed
  courts unchanged, so the assumption holds.
- **Gate §6.1 consequence:** adopting D1-A invalidates the v3, v4r and v5 runs on the
  current 16 — all were scored against the old 57-section GT containing the wrong HMA 27
  labels, so none may be quoted as the standing score under corrected GT. Each must be
  re-run live in Colab under corrected GT, with the D2 gate in the same logged change,
  and re-filed under a new sequential run number. This re-base is an offline estimate of
  what those re-runs should show, not a substitute: a live re-run could differ, and only
  its filed numbers count. Sealed-set HMA 27 impact was not assessed.

## 5. Brutal-test bank — drafted, checked, adjudicated, FROZEN (bank + second-rater + adjudication lanes)

- **Frozen file:** `brutal-bank-v1-frozen.json` —
  SHA-256 `934a2b2265ac137c96939e1fbeca3682a037010e42f972bfd459c2fcac4ec717`
- **Freeze note:** `brutal-bank-freeze-note.md` (full adjudication log, conventions,
  pre-run requirements). **Draft retained:** `brutal-bank-v1-draft.json`
  (pre-adjudication record; differs from frozen by exactly the 5 corrections in §5.3).
- **Counts (total 230):** C1 30, C2 20, C3 20, C4 20, C5 20, C6 16, C7 16, C8 12, C9 16,
  C10 12, C11 12, C12 8, C13 16, C14 12. Length mix: 47 one-liners, 10 long narratives,
  majority medium. IDs B-001…B-230. Lead-forum rule (header, applied uniformly): any
  HMA/GWA relief → Family Court; else any PWDVA/BNSS/BNS relief → Magistrate;
  birth/death registration → Registrar; no family-law relief → none.
- **D1-A applied throughout:** 9 questions carry `hma-27` in frozen GT, all verified
  pending/being-filed by the coordinator from the question texts: B-005, B-111, B-114,
  B-119, B-122, B-123, B-125, B-126, B-228.

### 5.1 Second-rater blind check (25%)

Stratified random sample of 58, fixed seed 20261127, own GT written from
questions-only text before seeing draft GT. **Full agreement 45/58 (77.6%)**; sections
55/58 (94.8%), court 57/58 (98.3%), escalates boolean 58/58 (100%), kinds 47/58
(81.0%). All 16 C13 items blind-rated for fluency + GT. Report:
`brutal-bank-second-rater-report.md`.

- **Kannada verdict: verified at working-reading level, NOT native-verified.** All 16
  C13 items fluent, natural Kannada, no defects found; GT 12/16 full agreement, 15/16
  sections. The second rater is not a native Kannada speaker — native-speaker
  confirmation is still recommended and is recorded as open (see §6).
- **B-148 verdict: empty GT is CORRECT.** PWDVA s.2(a) defines "aggrieved person" as a
  woman, so no PWDVA order is available to a male claimant; empty sections + procedure
  handoff is the right treatment. Consistent with B-146/B-153 (husband claiming child
  maintenance → BNSS 144 only).
- **Extended label set: all six legitimate, none to be replaced** — hma-24 (×6), hma-25
  (×4), hma-26 (×4), hma-13b (×5), hma-9 (×1, B-018), pwdva-22 (×1, B-019). Two
  qualifications: the hma-26/gwa-1890 fork rule must be written down (done — §5.4);
  and system label-set coverage could not be verified from within the rater's allowed
  scope — the coordinator verified it (see §5.5).

### 5.2 Adjudication (third reader)

4 legal disagreements (B-030, B-123, B-007, B-213): **DRAFT STANDS on all four**
(B-030 pwdva-18 + safety — threatened dispossession is economic abuse; B-123 hma-26 —
"will be filing next week" is a definite filing statement; B-007 hma-24 + Family Court
— money "while the case continues" in a pending divorce is maintenance pendente lite;
B-213 pwdva-18 + safety — actual expulsion is itself domestic violence). Report:
`brutal-bank-adjudication.md`.

### 5.3 The five GT corrections (adjudicated — the ONLY draft → frozen differences)

| ID | Change | Reason |
|---|---|---|
| B-012 | [hma-13, hma-27] → [hma-13] | "I want a divorce" + "never filed anything" is a wish, not a filing. |
| B-022 | [hma-13, hma-25, hma-27] → [hma-13, hma-25] | Wanting a divorce is not being filed; hma-25 kept (flagged, §6). |
| B-026 | [hma-13b, hma-27, gwa-1890] → [hma-13b, gwa-1890] | "We both want" is a shared wish, not a filing; custody stays GWA. |
| B-112 | [hma-13, hma-27] → [hma-13] | "I want a divorce" is a wish, not a filing (found by the C6 audit). |
| B-120 | [hma-13, hma-27] → [hma-13] | "If I file" is hypothetical, not a filing. |

Courts, escalates booleans, and kinds unchanged on all five. The adjudicator also
audited all of C6 (B-111–B-126): 15/16 correct, B-112 the only additional error. The
first rater's wider "being filed" convention (including conditional "if I file") was
**rejected**: "being filed" only on a definite filing/will-file/going-to-file statement.

### 5.4 Kind conventions recorded in the freeze note (binding for scoring)

- `fact`: open/disputed fact that changes the remedy or forum (44 uses) — tight
  boundary, not a catch-all. `demand`: Stridhan sought but no demand yet made.
  `procedure`: procedural relief sought; forum choice = `court` kind, process =
  `procedure` kind.
- `hma-26` / `gwa-1890` rule: custody inside a pending or being-filed HMA proceeding →
  `hma-26`; custody with divorce merely asked/contemplated → `gwa-1890`. Same
  pending/being-filed trigger as HMA 27.
- Out-of-scope: empty-GT items carry `gt_escalates=true` with `["procedure"]` handoff;
  the two C9 no-dispute empties carry `gt_escalates=false`.
- 8-gram overlap check: 3 runs, final **0 flagged of 230** (vs current-16, sealed
  sets, 20 plan examples, v5 lane paraphrases, gate lines). Adjudication changed GT +
  notes only (no question text), so the check stands.

### 5.5 Label-coverage gap — verified by the coordinator (pre-run requirement)

Checked the graph's 32-section list directly: hma-24, hma-25, hma-26, hma-13b ARE
present. **`hma-9` (B-018) and `pwdva-22` (B-019) are NOT in the label set** — both
questions are guaranteed misses unless the labels are added to the system (graph +
notebook) as a separate logged system change before the brutal run. Recorded in the
freeze note §6; the bank is frozen as drafted (GT is correct — the system must catch up).

## 6. What is frozen vs what still waits

**FROZEN (this change, logged together):**
- v2 ground truth under D1-A (`ground-truth-v2-hma27-A.json` + erratum) — 53 sections.
- D2 gate patch (`hma27-D2-gate.patch` + validation log) — ships only with D1, never alone.
- Brutal-test bank v1 (`brutal-bank-v1-frozen.json` + freeze note) — 230 questions.

**STILL WAITING (not done in this round):**
- Live re-runs of v3/v4r/v5 under corrected GT in Colab (gate §6.1 requires them; the
  re-base in §4 is an offline estimate only). Next live run is run 4 (v6) or a v5
  re-run under corrected GT + D2 gate.
- hma-9 + pwdva-22 label addition before the brutal run (B-018/B-019 guaranteed
  misses until then).
- Native-speaker Kannada confirmation for C13 (working-reading level verified only).
- Lane 2 `recovery` escalation text fix ("civil recovery under HMA s.27" is wrong on
  K0/H15 under D1-A) before any v6 run is scored; same for the BNS 316 node exclusion text.
- Typed escalations (D5 — H2/H4 kinds; v5 D2-adjusted escalates is still 12/16) and
  D6/D7/D11 confirmations (H14 HMA 13, H4 PWDVA 20, H15 demand_made).
- Sealed fresh-20/Kannada-8 also carry HMA 27 (v6 §7.1) — not touched, not opened;
  the same D1 question must be decided before any sealed run is scored.
- G2 amendment (fresh 16 → 20), T4 hardware for G14, prose renderer + rater identity
  — unchanged from v6 §10.

## 7. Corrections to the record made in this round

- v6 §4.2's "14/16" is wrong in both directions (see §4): D1-without-D2 on v5 is 12/16
  and D2-without-D1 on old GT is 12/16.
- The v4/plan count of three HMA 27-affected questions was wrong — K0 is a fourth.
- The bank draft's "being filed" convention (wanting / conditional "if I file" counts
  as being filed) was wrong — rejected by adjudication; 5 GTs corrected (§5.3).
- The settlement brief's graph path (`files/laya-graph/laya-crpc-bns-section-decision-tree-v2.json`)
  does not exist — canonical file is `files/laya-crpc-bns-section-decision-tree-v2.json`.

## 8. Files (all under `workspace/goals/english-family-law-chatbot-retest/files/laya-graph/` unless noted)

| File | SHA-256 (first 16) | Status |
|---|---|---|
| `ground-truth-v2-hma27-A.json` | `87818b1b659583bf…` | FROZEN (v2 GT, 53 sections) |
| `ground-truth-v2-erratum.md` | `42012b2b146f299c…` | FROZEN (erratum + D3/D4) |
| `hma27-D2-gate.patch` | `6349c922944275d2…` | Validated patch (not yet applied to live files) |
| `hma27-D2-gate-validation.md` | — | Validation log |
| `hma27-rebase-report.md` | — | Offline re-base (v4r/v5, both variants) |
| `brutal-bank-v1-frozen.json` | `934a2b2265ac137c…` | FROZEN (230 questions) |
| `brutal-bank-freeze-note.md` | — | Freeze note |
| `brutal-bank-v1-draft.json` | — | Retained pre-adjudication draft |
| `brutal-bank-second-rater-report.md` | — | Blind check (58/230, seed 20261127) |
| `brutal-bank-adjudication.md` | — | Third-reader adjudication |
| `v6-deep-dive-report.md` §4 | — | Settlement spec (D1–D11) |
| `v6-lane3-legal-decisions.md` §1 | — | HMA 27 verdict + §1.4 wording |
| `laya-10-10-gate-definition.md` §2/§6.1 | — | Frozen formula + GT-invalidation rule |
| `brutal-test-200-plan.md` | — | Bank design (230, 14 categories, pass bar) |

## Sources (lane reports)

- Rater lane: Astha Thakur verification, v2 GT + erratum (this report §1–§2)
- Gate lane: `hma27-D2-gate.patch` + `hma27-D2-gate-validation.md` (§3)
- Re-base lane: `hma27-rebase-report.md` (§4)
- Bank lane: `brutal-bank-v1-draft.json` (§5); second rater:
  `brutal-bank-second-rater-report.md`; adjudication: `brutal-bank-adjudication.md`
- Coordinator verifications (independent): v2-vs-v1 diff (only the four removals);
  patch applied clean to temp copies (counts 32/46/77, nbformat PASS, cells compile);
  bank counts + IDs; hma-27 carriers spot-checked (9 correct); label coverage vs the
  32-section list (hma-9/pwdva-22 missing).
