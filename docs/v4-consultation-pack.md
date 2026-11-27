# v4 consultation pack — paste into Gemini (Neon, Thinking High) AND ChatGPT (GPT-6.2, thinking max)

Purpose: get a second opinion on the v4 residence-precision fix BEFORE the live Colab run.
Both models get the identical prompt below. Their answers must be checked against our own
numbers before use; no private material is in this pack (only test-set numbers, which are
our own synthetic test data).

---

## Prompt (paste verbatim into each model)

You are reviewing a fix to an Indian family-law question classifier. The system is Laya
(421M ModernBERT) + a two-stage decision graph. Stage 1 scores 7 issues per question with
`noul` prompts (maintenance / custody / Stridhan / residence / violence / divorce /
birth-certificate), using clause-split max-pooling plus auxiliary verbatim-phrase prompts.
Per-issue thresholds fire issues; Stage 2 maps fired issues to statute sections.

LIVE v3 RESULT (Google Colab, 16 questions, 57 ground-truth sections): exact section-set
match 5/16, micro precision/recall 0.671/0.895, micro-F1 0.767, TP/FP/FN 51/25/6,
court 11/16, escalates 14/16. v1 was exact 5/16, F1 0.518, TP/FP/FN 21/3/36 — so v3 fixed
recall (FN 36→6) and broke precision (FP 3→25).

REMAINING FAILURES (all 25 FP + 6 FN, per question):
- H1: FP BNS 316, HMA 27 — Stridhan clause-max 0.7545 on the clause "My husband has not given
  me any money for three months" (money-not-given misread as Stridhan-held). GT is maintenance
  only (BNSS 144, PWDVA 20).
- H2: FP PWDVA 17/18/19 — residence R1 clause-max 0.8464 on "My husband says as the father he
  will take him away from me" (custody-only question, GT custody only).
- H3: FP BNSS 144, PWDVA 20, PWDVA 17, PWDVA 19 — maintenance + residence over-fired on a
  pure Stridhan question (GT: HMA 27, BNS 316). v1 had H3 exact — v3 regressed it.
- H5: FP PWDVA 17, PWDVA 19; FN PWDVA 18 — residence fired though GT has only PWDVA 18
  (which comes via the violence issue, "He beats me"); the residence sub-choice split the set.
- H6: FP GWA 1890, HMGA s.6, WELFARE; FN PWDVA 17/18/19 — custody fired INSTEAD of residence
  on "I just want money every month from my husband and to stay in the house with my daughter."
  (GT: BNSS 144, PWDVA 20, PWDVA 17/18/19). Clause-split never split "and to stay in the house".
- H7: FP BNSS 144, PWDVA 20 — maintenance over-fired on a birth-certificate question
  (GT: Births and Deaths Act 1969 only).
- H10: FP PWDVA 17/18/19 — residence fired on a pure gold/Stridhan question (GT: HMA 27,
  BNS 316, BNSS 144, PWDVA 20).
- H12: FP PWDVA 17/18/19 — residence fired on the OUT-OF-SCOPE ancestral-house question
  (GT empty, must stay empty).
- H13: FN PWDVA 17, PWDVA 19 — residence fired but the sub-choice kept only PWDVA 18
  (GT: PWDVA 17/18/19/20, BNSS 144).
- H14: FP GWA 1890 — custody sub-choice picked standalone Guardians and Wards Act though a
  divorce proceeding is pending (GT custody route is HMA 26).
- H15: FP BNSS 144, PWDVA 20 — maintenance over-fired on "He sold my gold without asking me."
  (GT: BNS 316, HMA 27).
- H4 is exact on sections but escalates wrong (expected True, live False — residence-only kept,
  no typed escalation fires).

RESIDENCE SCORES (R0 = original prompt with "...or about protection from threats or violence
at home?"; R1 = residence-only prompt "Does this question ask about staying in, or being
thrown out of, the shared house or home?"; threshold 0.15):
- R0 fired 5/16 (K0, H2, H5, H6, H13); R1 fired 11/16 (adds H1, H3, H4, H10, H12, H14).
  H2 R0 full 0.8247, R1 clause-max 0.8464. H4 R0 0.1267, R1 full 0.8789 / clause 0.1254.
  H12 R0 0.0468, R1 clause-max 0.2177. H6 R0 0.2173, R1 0.6272. H13 R0 0.4212.
  H1 R0 0.0968, R1 0.1643. H3 R0 0.057, R1 0.1899. H10 R0 0.1461, R1 0.2719.

PROPOSED v4 FIX (one focused change — residence precision + Lane A PRIMARY thresholds):
1. Thresholds: maintenance 0.05, custody 0.13, residence 0.15, divorce-asked 0.40 /
   divorce-pending 0.13, Stridhan/violence/birth 0.50. (v3 used maintenance 0.10, custody 0.20.)
2. Residence firing prompt reverts R1 → R0 (both scores still recorded for diagnosis).
3. New facts field `residence_claim` (bool): true iff the question states eviction / lockout /
   being thrown out / changed lock / cannot enter, OR a claim to stay in the shared house, OR a
   threat to throw out. Values: K0 T, H1 F, H2 F, H3 F, H4 T, H5 F, H6 T, H7 F, H8 F, H9 F,
   H10 F, H11 F, H12 F, H13 T, H14 F, H15 F. If `residence_claim` is False, residence is forced
   to 0.0 and never fires.
4. When residence fires (and passed the gate), Stage 2 keeps PWDVA 17+18+19 as a full set —
   sub-choices may not split it. The violence → PWDVA 18 path is untouched.
Nothing else changes (no GT change, no other thresholds, no clause-split/aux changes).

QUESTIONS FOR YOU:
1. Will this v4 fix, on these numbers, fix H2/H10/H12 (residence FPs), H13 (FN 17/19),
   H6 (FN 17/18/19) and H5 (FP 17/19)? Walk through each question with the R0 scores and the
   gate values above. Where does it NOT fix, and why?
2. Does the `residence_claim` gate risk breaking any TRUE residence case on this set
   (K0, H4, H6, H13)? H5's GT PWDVA 18 comes via violence, not residence — does the gate
   preserve it?
3. Does lowering maintenance to 0.05 and custody to 0.13 risk NEW false positives on this
   set? Check H1 (maintenance full 0.4795, Stridhan 0.4948), H3, H7, H15 against the new
   thresholds — which of the remaining FPs get worse, and what would you do instead?
4. Is there a better single residence fix than R0 + fact gate + full-set (e.g. R1 with a higher
   threshold, or a different gate)? Give numbers, not generalities.
5. What is the single most important fix AFTER v4, and which question(s) prove it?

Answer with per-question numbers. Do not suggest changing ground truth. Do not suggest
per-question special cases or hardcoded question IDs.
