# Gemini consultation on the v4 residence fix — record

- **Model consulted:** Gemini Neon, Thinking High (per the parent agent's brief).
- **Date:** 2026-11-26 night (overnight 10/10 push, after the v3 live run).
- **Input:** `v4-consultation-pack.md` (v3 live numbers, all 25 FP + 6 FN per
  question, R0/R1 residence scores, proposed v4 fix, 5 questions).
- **Provenance note:** this file records the verdict as transmitted in the
  parent agent's brief of Gemini's answer. It is a faithful summary of that
  verdict, NOT a verbatim transcript — the full verbatim answer is held in
  the parent chat. Where this file adds our own verification against the v3
  live JSON, that is marked **Verification (ours)** and is not Gemini's
  wording.

## Executive verdict

**Do NOT ship v4 as written.** Two bugs, the same two ChatGPT found:

1. **R1→R0 @0.15 breaks H4** — 3 new FNs; H4 drops from exact to 0/3 on
   sections. Only R1 full 0.8789 rescued H4 in v3 (Gemini states R1 clause
   was 0.1254).
2. **M 0.05 / C 0.13 buys 0 new TPs** — v3 already has 0 maintenance FNs and
   0 custody FNs — while worsening FPs, risking H7 custody FPs (+3) and H12
   pollution.

## §1 — Gemini's preferred residence fix (v4.2 candidate, design only)

Keep **R1** (full-question text in the max-pool) + raise the R1 threshold to
**0.35–0.45** + keep the `residence_claim` gate + keep the full set. This is
DIFFERENT from ChatGPT's Option D (evidence-first): Gemini keeps a score
threshold and uses the gate as a veto; ChatGPT uses the gate as the firing
signal itself. Both are recorded; neither notebook is built yet for the
Gemini variant — see `v4-1-change-log.md` §6 for the head-to-head and the
run-order recommendation.

### Head-to-head on the 16 (Gemini's numbers, as transmitted)

- R1@0.35 kills H1 (0.1643), H3 (0.1899), H12 (0.2177), H10 (0.2719) by
  threshold alone.
- H2 (0.8464) still needs the gate.
- H4 passes via R1 full 0.8789 (+0.5289 over 0.35).
- H6 passes 0.6272 (+0.2772 — Gemini: 4× safer than R0's +0.0673).

### Projection (Gemini, PROJECTION — not a result)

- **v4.2 (R1@0.35 + gate + full-set): TP 57 / FP 12 / FN 0, micro-F1 0.905,
  exact 10/16** — exact set K0, H2, H4, H5, H8, H9, H10, H11, H12, H13.
- **v4 as specified (PRIMARY thresholds): TP 54 / FP 12 / FN 3, micro-F1
  0.878, exact 9/16** — 8/16 if H5 violence < 0.50.
- F1 checks: 2×57/(2×57+12+0) = 114/126 = 0.905; 2×54/(2×54+12+3) =
  108/123 = 0.878. Both projections assume H4 loses its 3 residence
  sections under R0 — see the verification below, which disputes that
  assumption.

### **Verification (ours) — Gemini's numbers come from the mislabelled v3 table**

The v3 Cell 8 residence table mislabelled its clause-max columns (v4
builder, confirmed): the printed `r1_clause_max` column is actually the
**R0** clause-max, and the R0 clause-max column was always None. Gemini
read the printed table, so two of its numbers are R0 values, not R1:

| Question | Gemini's number | What it actually is (verified) | True R1 final* |
|----------|-----------------|--------------------------------|----------------|
| H2 | 0.8464 ("R1") | R0 clause-max (stage1_clause_max['residence']) | 0.3813 |
| H12 | 0.2177 ("R1") | R0 clause-max | 0.3480 |
| H4 | 0.8789 (R1 full) | Correct — R1 full | 0.8791 |
| H6 | 0.6272 (R1 full) | Correct — R1 full | 0.7923 |
| H1 | 0.1643 | R1 final (full 0.1643) | 0.1643 |
| H3 | 0.1899 | R1 final (full 0.1899) | 0.1899 |
| H10 | 0.2719 | R1 final (full 0.2719) | 0.2719 |

\* True R1 final = max(R1 full, R1 clause-max [true key `residence_r1`],
aux residence max), as the notebook computes it.

Consequences, all verified from the v3 live JSON:

- **H12 at R1@0.35:** true R1 final is 0.3480 — killed by the threshold,
  but by **0.002**, not by the margin Gemini implied (0.2177 → 0.1323).
  The 0.35 cutoff is balanced on a knife edge on H12. At 0.45, H12 is
  killed comfortably (0.3480 < 0.45).
- **H2 at R1@0.35:** true R1 final 0.3813 — still ≥ 0.35, so H2 DOES still
  need the gate at 0.35 (Gemini's outcome is right, its number is wrong).
  At 0.45, H2 is killed by the threshold alone (0.3813 < 0.45) and the
  gate is not load-bearing for it.
- **H6 "4× safer":** Gemini compares R1 full (0.6272, +0.2772 over 0.35)
  with R0 full (0.2173, +0.0673 over 0.15). But the notebook fires on the
  max-pool final, not the full-question score: H6's R0 final is **0.7318**
  (aux 0.7318) and its R1 final is **0.7923**. R1 is still safer on the
  final, but by +0.0605, not 4×. The "4×" comparison uses numbers the
  notebook does not fire on.
- **H4 "only R1 full rescued it":** same error as ChatGPT's. H4's R0 final
  is 0.6474 via the aux verbatim-lockout prompt — see `v4-1-change-log.md`
  §2. Gemini's "R1 clause was 0.1254" is the R0 clause-max (mislabeled
  column); the true R1 clause-max for H4 is 0.8791.
- **Gemini's v4 projection (TP 54 / FN 3) assumes H4 loses 3 sections
  under R0.** If the live v4r run keeps H4 (as the aux term predicts), that
  projection is wrong in the same way ChatGPT's H4-break claim is.

### Cutoff formula (Gemini) — verified three ways

Gemini: set the cutoff to `min(0.45, min(R1(K0), R1(H13)) − 0.05)`.

| Definition of "R1 score" | R1(K0) | R1(H13) | Cutoff from the formula |
|--------------------------|--------|---------|-------------------------|
| R1 final as the notebook computes it (max full, clause-max, aux) | 0.8905 | 0.8786 | min(0.45, 0.8286) = **0.45** |
| R1 full only | 0.298 | 0.1924 | min(0.45, 0.1424) = 0.1424 — does NOT support 0.35–0.45 |
| Gemini's table values (max of printed R1 full + printed clause-max) | 0.7674 | 0.4212 | min(0.45, 0.3712) = **0.3712** |

The formula only yields a 0.35–0.45 cutoff when "R1 score" includes the
aux term (or the mislabelled R0 clause-max). The v4.2 design must pin the
definition down before it is built: the recommended definition is the
notebook's own final (max of full, clause-max, aux), which gives **0.45**.
At 0.45 the gate is load-bearing only for H5 (R1 final 0.6972) and H14
(0.7560); at 0.35 it is load-bearing for H2, H5, H12 and H14 as well.

## §2 — Gate upgrade for generalisation (Gemini)

Instead of a brittle boolean keyword flag, use a single Laya 2-option
choice gate, applied only when R1 ≥ 0.35:

- **(A)** spouse locked out / threatened eviction / claiming right to
  reside in shared matrimonial household;
- **(B)** child custody / taking-away, ancestral property title /
  partition, or violence / gold claim without eviction.

It kills H2/H5/H12 semantically via softmax. (Design only — not built.
Carried into `v5-planning-note.md`.)

## §3 — Generalisation risk flag (Gemini)

Is `residence_claim` extracted by a deterministic parser or a Laya prompt?
**Neither, in our notebook: it is a frozen hand-written boolean per
question in Cell 6** (same status as the other facts). A keyword hard-zero
veto will fail silently on unseen indirect lockout idioms — Gemini's
examples: "in-laws kept my house keys", "he put my clothes outside the
door". Recorded as a generalisation risk in `v4-1-change-log.md` §7 and
in the v5 plan: the gate must eventually be produced by the model (the
2-option choice in §2) or by a stated extraction rule, not by a
per-question annotation, before the system can claim to generalise.

## §4 — H5 violence check (Gemini's question, answered from the data)

- Gemini asked: H5 Stage 1 violence score (≥ 0.50?) and whether Stage 2 is
  a true set union (sections `|=` violence; `|=` residence) so a residence
  sub-choice can never delete violence's PWDVA 18.
- **Verification (ours):** H5 violence final is **0.8343** and violence
  fired in v3. Stage 2 in v3/v4/v4r was NOT a true union — it was
  `if 'violence' in fired and 'residence' not in fired:`, and residence
  fired, so the path was suppressed. v4.1 makes it a true union
  (`if 'violence' in fired: kept_pre.add('pwdva-18')`).

## §5 — Next fix after residence (v5): the 4-option financial-claim choice

Replace the independent maintenance / Stridhan `noul` prompts with **ONE
4-option Laya choice** financial-claim classifier:

- `maintenance_only` / `stridhan_only` / `both` / `neither`

Gemini projects this resolves H1, H3, H7, H15 (8 of the 12 remaining FPs)
→ **exact 10 → 14/16, micro-F1 0.905 → 0.966 (TP 57 / FP 4 / FN 0)**,
leaving only H6 custody (3 FP), H14 HMA-26 routing (1 FP), and H4
escalation. (PROJECTION — not a result. F1 check: 2×57/(2×57+4+0) =
114/118 = 0.966.) Exact option definitions are carried into
`v5-planning-note.md`; the "both" option must preserve K0 and H10, which
are genuinely both maintenance and Stridhan.

## §6 — Laya prompt behaviour note (Gemini)

Per Laya docs as cited by Gemini: out-of-distribution `noul` prompts
collapse toward "no"; 2-option choice prompts with neutral keys move the
signal into a separable 0.35–0.85 range. This is the mechanism behind both
the R1@0.35–0.45 proposal (§1) and the 4-option financial-claim choice
(§5): choice prompts separate better than yes/no prompts on this model.
Recorded as a design principle for v5, to be tested live rather than
assumed.
