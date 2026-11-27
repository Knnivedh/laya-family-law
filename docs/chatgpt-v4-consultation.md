# ChatGPT consultation on the v4 residence fix — record

- **Model consulted:** ChatGPT GPT-6.2, thinking High (per the parent agent's brief).
- **Date:** 2026-11-26 night (overnight 10/10 push, after the v3 live run).
- **Input:** `v4-consultation-pack.md` (v3 live numbers, all 25 FP + 6 FN per
  question, R0/R1 residence scores, proposed v4 fix, 5 questions).
- **Provenance note:** this file records the verdict as transmitted in the
  parent agent's brief of ChatGPT's answer. It is a faithful summary of that
  verdict, NOT a verbatim transcript — the full verbatim answer is held in
  the parent chat. Where this file adds our own verification against the v3
  live JSON, that is marked **Verification (ours)** and is not ChatGPT's
  wording. Options A and C were in ChatGPT's answer but were not transmitted
  in the brief; they are recorded as a gap in §5, not reconstructed.

## Executive verdict

1. **Approve the Boolean `residence_claim` gate — WITH MODIFICATION.**
2. **REJECT reverting exclusively to R0** as the residence firing prompt.
3. **Do NOT lower maintenance to 0.05 or custody to 0.13 yet** — keep the v3
   thresholds (maintenance 0.10, custody 0.20). This confirms the v4r
   residence-only variant, not v4 as specified.

## §1 — Why R0-only is rejected: H4

- H4 is a single-issue residence question ("They changed the lock and I
  cannot enter my house. The house is in my husband's name."). Ground truth
  is PWDVA 17/18/19. It was **exact in v3**.
- ChatGPT's reasoning: H4's R0 score is 0.1267, below the 0.15 threshold,
  though `residence_claim` is True and R1 full is 0.8789. Reverting to R0
  alone would therefore lose H4's residence sections — H4 drops from exact
  to 0/3 on sections.
- **Verification (ours) — this claim does NOT survive the data as stated:**
  0.1267 is H4's R0 **full-question** score only. The notebook's final
  residence score is `max(full, clause-max, aux)`, and H4's aux residence
  max is **0.6474** (from the verbatim H4-lock aux prompt), so H4's R0
  final as the notebook computes it is **0.6474 ≥ 0.15**. v4r should
  therefore KEEP H4 exact on sections; ChatGPT's H4-break prediction uses
  the wrong number (full-question score instead of the max-pool final).
  The live v4r run is the decider. Full analysis in `v4-1-change-log.md`
  §2. This does not invalidate ChatGPT's preferred fix — evidence-first
  still fires H4 regardless — but it changes what v4r is expected to do.

## §2 — Preferred fix: Option D, evidence-first

- If `residence_claim` is **True**, residence **FIRES regardless of the R0
  score** — the claim itself is the evidence.
- If `residence_claim` is **False**, residence is **blocked**.
- Only if the claim is **unknown** should the system fall back to scores.
- In our notebook there is no unknown case: `residence_claim` is a bool on
  every question in Cell 6, so v4.1 implements the first two branches only
  and states that explicitly. No unknown branch was invented.
- Minimal acceptable alternative, **Option B: R0 threshold 0.12 + gate**
  (4/4 residence). **Overfit flag (ChatGPT's own, recorded here):** 0.12 is
  fitted to H4's 0.1267 full-question score. Our verification adds: the
  notebook never fires on the full-question score alone — it fires on the
  max-pool final (H4: 0.6474) — so 0.12 is fitted to a number the system
  does not use. Option B was not built; Option D was built as v4.1.

## §3 — Per-question audit (v3 failures → what the fix does)

| ID | v3 failure (verified from live JSON) | Fix mechanism in v4/v4.1 |
|----|--------------------------------------|--------------------------|
| H1 | FP BNS 316, HMA 27 (Stridhan clause-max 0.7545 on "has not given me any money") | Not a residence failure. Residence blocked (claim False; R0 final 0.0968 < 0.15 anyway). Stridhan/maintenance cross-fire is v5/v6 work. |
| H2 | FP PWDVA 17/18/19 (residence R1 clause-max 0.8464 on "take him away") | Gate blocks it (claim False). R0 final 0.8464 would otherwise fire. |
| H3 | FP BNSS 144, PWDVA 20, PWDVA 17, PWDVA 19 (pure Stridhan Q) | Gate blocks residence (claim False; R0 final 0.1727 ≥ 0.15 would otherwise fire). Maintenance over-fire is v5/v6 work. |
| H4 | Exact in v3 on sections; escalates wrong (expected True, live False) | See §1. Evidence-first fires residence regardless of score. Escalates is NOT fixed by this change. |
| H5 | FP PWDVA 17/19; FN PWDVA 18 (residence fired, sub-choice split the set) | Gate blocks residence (claim False) + violence→18 true union (§4). |
| H6 | FP GWA 1890, HMGA s.6, WELFARE; FN PWDVA 17/18/19 (custody fired instead of residence) | Residence full set fixes the 3 FNs (claim True; R0 final 0.7318). Custody FPs remain — v6/v7 work. |
| H7 | FP BNSS 144, PWDVA 20 (birth-certificate Q) | Not a residence failure. Maintenance over-fire is v5/v6 work. |
| H10 | FP PWDVA 17/18/19 (pure gold/Stridhan Q) | Gate blocks residence (claim False; R0 final 0.1901 ≥ 0.15 would otherwise fire). |
| H12 | FP PWDVA 17/18/19 (out-of-scope ancestral-house Q; GT empty) | Gate blocks residence (claim False; R0 final 0.2177 ≥ 0.15 would otherwise fire). Must stay empty. |
| H13 | FN PWDVA 17/19 (residence fired, sub-choice kept only PWDVA 18) | Residence full set keeps 17+18+19 (claim True; R0 final 0.8786). |
| H14 | FP GWA 1890 (standalone GWA though a divorce proceeding is pending; GT route is HMA 26) | Not a residence failure. Proceeding-aware custody routing is v5 work. |
| H15 | FP BNSS 144, PWDVA 20 ("He sold my gold without asking me.") | Not a residence failure. Maintenance over-fire is v5/v6 work. See also the §5-table mislabel flag below. |
| K0 | Exact in v3 | Residence fires (claim True; R0 final 0.8905). No change. |

## §4 — H5 and the violence → PWDVA 18 path

- ChatGPT's instruction: preserve the violence → PWDVA 18 path as an
  **independent union** — residence False + violence True must still yield
  PWDVA 18. Whether v3's miss was violence failing to fire or its output
  being suppressed was **unverified** in ChatGPT's answer; ChatGPT asked for
  the raw violence score to be recorded as a diagnostic in the notebook
  output. v4.1 does that (`violence_final`, `violence_fired` per question
  in Cell 8).
- **Verification (ours) — mechanism now confirmed from the v3 live JSON:**
  H5's Stage 1 violence final is **0.8343** (≥ 0.50) and `violence` IS in
  H5's fired issues. Violence did fire. PWDVA 18 was lost because Stage 2
  was `if 'violence' in fired and 'residence' not in fired:` — residence
  fired, so the path was suppressed — and the residence sub-choice then
  kept only 17+19. Suppression confirmed, not a violence failure. v4.1
  makes the path a true union (`if 'violence' in fired:`), so a residence
  sub-choice can never delete violence's 18 again. On the current 16 the
  union and the v4r conditional agree (a fired residence always brings the
  full 17/18/19 set), so this is a robustness fix, not a score change.

## §5 — Next fix after residence; thresholds; projections

- **Next fix (ChatGPT §5):** evidence-grounded verification for
  maintenance / Stridhan / custody — each issue fires only on a stated
  fact that grounds it, not on a bare prompt score. (Carried into
  `v5-planning-note.md`.)
- **Thresholds:** keep v3 maintenance 0.10 / custody 0.20. Lowering them
  was rejected — no new true positives are available (v3 already has 0
  maintenance FNs and 0 custody FNs), only new FPs.
- **Projection (ChatGPT, PROJECTION — not a result):** if the residence
  fix works with H4 preserved and no new errors: **TP 56, FP 12, FN 1,
  micro-F1 0.896** (2×56/(2×56+12+1) = 112/125 = 0.896). Note: the
  coordinator's v4r projection is TP 57 / FP 12 / FN 0 (F1 0.905). The
  one-TP / one-FN discrepancy between the two projections is unexplained
  in the material transmitted — the single FN is not identified in the
  brief. The live runs will settle it. Do not quote either as a result.

## ⚠️ Model error flag — H15 mislabelled in ChatGPT's §5 table

- In ChatGPT's §5 table, H15 ("He sold my gold without asking me.") is
  labelled **Maintenance, not Stridhan**.
- **Ground truth is BNS 316 + HMA 27 (Stridhan); maintenance (BNSS 144,
  PWDVA 20) is the FALSE POSITIVE there.** ChatGPT's label is wrong and
  was NOT adopted. Recorded here so the error is not carried into v5,
  where the financial-claim boundary is the fix: H15 is a Stridhan-only
  question with a maintenance over-fire, not a maintenance question.

## Options A–D comparison (as transmitted)

| Option | Description | Status |
|--------|-------------|--------|
| A | Not transmitted in the parent brief — do not reconstruct. | Gap — parent to fill from the full answer. |
| B | R0 threshold 0.12 + residence_claim gate (4/4 residence) | Minimal acceptable alternative; overfit risk flagged (§2). Not built. |
| C | Not transmitted in the parent brief — do not reconstruct. | Gap — parent to fill from the full answer. |
| D | Evidence-first: claim True → fire regardless of R0; claim False → block; unknown → score fallback | **Preferred. Built as v4.1.** No unknown branch exists in our notebook (bool on all 16). |
