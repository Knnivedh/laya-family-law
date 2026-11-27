# v4.1 change log — evidence-first residence (ChatGPT Option D)

## §0 — Files, validation, status

- Notebook: `live-laya-colab-test-v4-1-evidence-first.ipynb`
  - sha256: `7453647c332a44062f72766474b3194ef1a24b218af2d2efa449d11f62c5b5af`
  - Builder: `build_laya_v4_1_evidence_first.py` (derives v4.1 from the v4r
    notebook by surgical string replacement, same pattern as the v4 builder).
  - Validation: nbformat.validate **PASS**; Cells 7–8 compile **PASS**;
    cells 0–6 byte-identical to v4r (ground truth and all facts, including
    `residence_claim`, untouched); thresholds asserted at v3 values;
    `esc_live` patch (`quantum`/`court`/`demand`) asserted present in
    Cell 8; no `v4r-residence-only` filename or version string remains.
  - Output filenames: `live-laya-colab-results-v4-1-evidence-first.json/.md`.
- Parent: v4r (`live-laya-colab-test-v4r-residence-only.ipynb`, sha256
  `7d67bd53…851ca`), currently running live in Colab at the time of writing.
- Status: **built and validated, NOT yet run.** Run order: v4r live first,
  then v4.1. Do not run v4.1 before the v4r result lands — v4r is the
  control for the evidence-first change.
- This log also records the two model consultations
  (`chatgpt-v4-consultation.md`, `gemini-v4-consultation.md`), the H4
  verdict from the data (§2), and the Gemini v4.2 design (§6).

## §1 — What v4.1 changes vs v4r (minimal diff)

Cells 0–6 are identical. Only Cells 7–8 change (11 + 16 surgical
replacements in the builder):

1. **Residence rule becomes evidence-first (ChatGPT Option D).** In v4r,
   claim True fired residence per the R0 score at 0.15. In v4.1, claim True
   FIRES residence regardless of the R0 score; claim False blocks it
   (final forced to 0.0). There is **no unknown branch**: `residence_claim`
   is a bool on every question in Cell 6, so no score-fallback branch was
   invented. The R0 score is NOT overwritten — `stage1_final['residence']`
   keeps the computed max(full, clause-max, aux) so Cell 8 diagnostics stay
   truthful; firing is forced separately after the firing loop, flagged by
   `rec['residence_evidence_fired']`.
2. **Violence → PWDVA 18 becomes a true union.** v4/v4r:
   `if 'violence' in fired and 'residence' not in fired:`. v4.1:
   `if 'violence' in fired:`. See §4 for why.
3. **Cell 8 diagnostics added:** per-question `residence_evidence_fired`,
   `violence_final` (raw Stage 1 violence score) and `violence_fired`,
   plus aggregate `residence_evidence_fired_count` /
   `violence_fired_count`.
4. **Header comments corrected (no behaviour change):** v4r carried two
   stale v4 wordings — the scope line listed divorce-asked 0.40 /
   divorce-pending 0.13 (the PRIMARY values; v4r keeps 0.45 / 0.12) and
   note 3's WARNING described applying the PRIMARY vector. Both fixed.
5. **Unchanged:** v3 thresholds (M 0.10 / C 0.20 / R 0.15 / D-asked 0.45 /
   D-pend 0.12), R0 firing prompt, residence full set (PWDVA 17+18+19),
   clause-split rules, aux prompts, HMA 25 gate, court fallback, typed
   escalations, ground truth. Both models agreed the PRIMARY thresholds
   (M 0.05 / C 0.13) must NOT be applied — see §7.

## §2 — H4 verdict from the data (read this before trusting either model)

**Question:** does H4's ground truth include residence sections, what are
its R0/R1 scores in the live v3 JSON, and is v4r expected to keep or lose
H4 exact? The coordinator's v4r prediction (exact 10/16) assumed H4 stays
exact; ChatGPT and Gemini both said R0 breaks H4. The data settles it.

**Ground truth (Cell 6, verified):** H4 — "They changed the lock and I
cannot enter my house. The house is in my husband's name." — GT is exactly
PWDVA 17, PWDVA 18, PWDVA 19 (`pwdva-17/18/19`). Yes, GT includes residence
sections, and nothing else. `residence_claim` is True. Court expected:
Magistrate. Escalate expected: True.

**v3 live (verified from
`browser-download-20261126T175956.703524888Z-2-live-laya-colab-results-v3-empty5.json`):**
H4 was **exact** (TP 3 / FP 0 / FN 0, pred = GT, court correct, escalates
wrong — expected True, live False). Fired issues: residence, divorce.

**H4 scores (verified, all from the v3 live JSON):**

| Score | Value | Source in the JSON |
|-------|-------|--------------------|
| R0 full-question | 0.1267 | `residence_r0_vs_r1` / `residence_r0` |
| R0 clause-max (true key `stage1_clause_max['residence']`) | 0.1254 | `raw_live_runs[H4].stage1_clause_max['residence']` |
| Aux residence max (verbatim H4-lock aux prompt) | **0.6474** | `raw_live_runs[H4].aux_max['residence']` |
| **R0 final = max(full, clause-max, aux)** | **0.6474** | notebook final-score formula |
| R1 full-question | 0.8789 | `residence_r1` |
| R1 clause-max (true key `residence_r1`) | 0.8791 | `stage1_clause_max['residence_r1']` |
| R1 final | 0.8791 | `stage1_final['residence']` |

**Verdict: v4r is EXPECTED TO KEEP H4 exact on sections.** Both models'
H4-break claim uses the R0 **full-question score alone (0.1267 < 0.15)**
and ignores the aux term — but the notebook's final score is
`max(full, clause-max, aux)`, and H4's aux term is 0.6474, more than four
times the threshold. Under v4r (R0 @ 0.15 + gate, claim True), H4's R0
final is 0.6474, residence fires, the full set keeps 17+18+19, and H4 stays
exact on sections (court correct; escalates still wrong, as in v3 — the
residence fix does not touch escalation).

**Two caveats, stated plainly:**

- (a) H4's R0 final depends **entirely on one aux prompt** — the verbatim
  H4-lock phrase. If that aux prompt ever scored below 0.15 on a
  paraphrased lockout question, v4r would lose the residence sections.
  That fragility is exactly what v4.1's evidence-first rule removes: under
  v4.1, H4 fires on the claim itself, and the aux score becomes irrelevant
  to firing (it is still recorded).
- (b) This is an offline deduction from v3 saved scores. The aux prompts
  are unchanged between v3 and v4r, so the aux value should reproduce live,
  but **the live v4r run is the decider**. If v4r loses H4, the deduction
  is wrong somewhere (e.g. live aux scores differ) and both the
  coordinator's and this log's predictions must be recomputed from the
  live numbers.

**Consequence for the models' projections:** ChatGPT's projection
(TP 56 / FP 12 / FN 1) and Gemini's v4 projection (TP 54 / FP 12 / FN 3)
both assume H4 loses residence sections under R0. If v4r keeps H4, both
projections are wrong on that point and the coordinator's v4r projection
(TP 57 / FP 12 / FN 0, F1 0.905) stands. Do not quote any of the three as
a result — they are projections, and the live run arbitrates.

## §3 — Residence finals for all 16 (verified from the v3 live JSON)

Final = max(full-question, clause-max, aux), per the notebook's formula.
`claim` is the frozen Cell 6 `residence_claim`. "v4r fires" = R0 final ≥
0.15 AND claim True. "v4.1 fires" = claim True. "R1@0.35 fires" = R1 final
≥ 0.35 AND claim True (Gemini v4.2 candidate).

| ID | R0 full | R0 clause | Aux res | **R0 final** | R1 full | R1 clause* | **R1 final** | Claim | v4r | v4.1 | R1@0.35 |
|----|---------|-----------|---------|--------------|---------|------------|--------------|-------|-----|------|---------|
| K0 | 0.265 | 0.7674 | 0.8905 | **0.8905** | 0.298 | 0.3158 | **0.8905** | T | ✓ | ✓ | ✓ |
| H1 | 0.0968 | 0.0453 | 0.0947 | 0.0968 | 0.1643 | 0.1140 | 0.1643 | F | – | – | – |
| H2 | 0.8247 | 0.8464 | 0.3813 | **0.8464** | 0.1713 | 0.2538 | 0.3813 | F | – | – | – |
| H3 | 0.057 | 0.1727 | 0.1285 | 0.1727 | 0.1899 | 0.1392 | 0.1899 | F | – | – | – |
| H4 | 0.1267 | 0.1254 | 0.6474 | **0.6474** | 0.8789 | 0.8791 | 0.8791 | T | ✓ | ✓ | ✓ |
| H5 | 0.4882 | 0.3523 | 0.2143 | 0.4882 | 0.1291 | 0.6972 | 0.6972 | F | – | – | – |
| H6 | 0.2173 | 0.2820 | 0.7318 | **0.7318** | 0.6272 | 0.7923 | 0.7923 | T | ✓ | ✓ | ✓ |
| H7 | 0.0001 | 0.1307 | 0.0001 | 0.1307 | 0.0000 | 0.0958 | 0.0958 | F | – | – | – |
| H8 | 0.1008 | 0.1008 | 0.1177 | 0.1177 | 0.1344 | 0.1344 | 0.1344 | F | – | – | – |
| H9 | 0.0608 | 0.0608 | 0.0638 | 0.0638 | 0.0626 | 0.0626 | 0.0638 | F | – | – | – |
| H10 | 0.1461 | 0.1067 | 0.1901 | 0.1901 | 0.2719 | 0.1506 | 0.2719 | F | – | – | – |
| H11 | 0.0555 | 0.0555 | 0.0895 | 0.0895 | 0.0006 | 0.0006 | 0.0895 | F | – | – | – |
| H12 | 0.0468 | 0.2177 | 0.1330 | 0.2177 | 0.1244 | 0.3480 | 0.3480 | F | – | – | – |
| H13 | 0.4212 | 0.4212 | 0.8786 | **0.8786** | 0.1924 | 0.1924 | 0.8786 | T | ✓ | ✓ | ✓ |
| H14 | 0.1225 | 0.1550 | 0.1021 | 0.1550 | 0.5167 | 0.7560 | 0.7560 | F | – | – | – |
| H15 | 0.067 | 0.0712 | 0.0847 | 0.0847 | 0.0681 | 0.0831 | 0.0847 | F | – | – | – |

\* R1 clause = true key `stage1_clause_max['residence_r1']` (the v3 Cell 8
table printed the R0 clause-max in this column — see the consultation
files). R0 clause = key `stage1_clause_max['residence']`.

**Reading the table:** all three designs (v4r, v4.1, R1@0.35) fire
residence on exactly the same four questions — K0, H4, H6, H13 — which is
exactly the set whose ground truth contains residence sections. The gate
does the work in all three: five questions would fire on score alone and
are blocked by it (H2, H3, H5, H10, H12, H14 by R0 final ≥ 0.15 — six;
H2, H5, H12, H14 by R1 final ≥ 0.35 — four). On the current 16, the three
designs are **indistinguishable by outcome**; they differ only in
robustness to unseen phrasings (§6–§7). The live runs therefore cannot
rank them — that ranking needs the sealed fresh-20 (after 16/16) or
synthetic lockout paraphrases, not more runs on the 16.

## §4 — H5 and the violence union (verified)

- H5 GT includes PWDVA 18 (via violence: "He beats me"). v3 predicted
  PWDVA 17 + 19 but not 18 (TP 6 / FP 2 / FN 1).
- Verified from the v3 JSON: H5 Stage 1 violence final is **0.8343**
  (threshold 0.50) and `violence` IS in H5's fired issues. Violence fired.
  PWDVA 18 was lost because Stage 2 was conditional —
  `if 'violence' in fired and 'residence' not in fired:` — residence
  fired, so the path was suppressed, and the residence sub-choice then
  kept only 17+19. **Suppression confirmed; not a violence failure.**
- v4r fixes H5 a different way: residence is gated out (claim False), so
  the conditional path unblocks and violence adds 18. v4.1 fixes it twice
  over: the gate still unblocks it, AND the path is now an unconditional
  union, so no future residence sub-choice can delete it. Cell 8 now
  records the raw violence score per question, so the live run shows the
  mechanism instead of leaving it to inference.

## §5 — Predicted v4.1 outcome (PROJECTION — not a result)

Same residence firing set as v4r (§3), same thresholds, same full set, and
the violence union can only add H5's PWDVA 18 (which v4r already gets via
the unblocked path). So v4.1's projection is the coordinator's v4r
projection: **exact 10/16** (new exact: H2, H5, H10, H12, H13; H4, K0,
H8, H9, H11 stay exact), **TP 57 / FP 12 / FN 0, micro-P/R 0.826/1.000,
micro-F1 0.905, court ~13/16, escalates ~15/16, rating ~7.7/10** (frozen
formula: 0.4×0.625 + 0.3×0.905 + 0.15×0.8125 + 0.15×0.9375 ≈ 0.78).
Remaining after v4.1: H1/H3/H7/H15 (Stridhan/maintenance over-fire),
H6 (custody FP), H14 (GWA FP), H4 escalates. ChatGPT's projection
(TP 56 / FP 12 / FN 1, F1 0.896) differs by one unidentified FN — if the
live v4r run shows H4 lost or H5's 18 missing, v4.1's projection falls to
ChatGPT's numbers or below. The live runs decide; do not quote any of
these as results.

A checkable prediction for the v4.1 live run: `residence_evidence_fired`
should read **False on all 16** (every claim-True question already clears
0.15 on its R0 final, so the force-fire branch never triggers) and
`violence_fired` should read True on H5 and H13 (violence finals 0.8343
and 0.8892 in v3). If `residence_evidence_fired` is True anywhere, the
force-fire branch did real work and the R0 scores dipped live — report it.

## §6 — Gemini alternative: v4.2 candidate (DESIGN ONLY — do not build yet)

**Design:** keep R1 as the firing prompt (full-question text in the
max-pool), raise the R1 threshold to 0.35–0.45, keep the
`residence_claim` gate, keep the full set. Plus Gemini's gate upgrade:
a single Laya 2-option choice gate applied only when R1 ≥ 0.35 —
(A) spouse locked out / threatened eviction / claiming right to reside in
the shared matrimonial household vs (B) child custody / taking-away,
ancestral property title / partition, or violence / gold claim without
eviction — which kills H2/H5/H12 semantically via softmax.

**Verified R1 values for the cutoff (Gemini's formula:
`min(0.45, min(R1(K0), R1(H13)) − 0.05)`):**

| Definition of "R1 score" | R1(K0) | R1(H13) | Cutoff |
|--------------------------|--------|---------|--------|
| R1 final as the notebook computes it (max full, clause-max, aux) | 0.8905 | 0.8786 | min(0.45, 0.8286) = **0.45** |
| R1 full only | 0.298 | 0.1924 | 0.1424 — does NOT support 0.35–0.45 |
| Gemini's table values (max of printed R1 full + printed clause-max, which is R0 clause-max) | 0.7674 | 0.4212 | 0.3712 |

**Recommended definition if v4.2 is built:** the notebook's own final
(max of full, clause-max, aux) → cutoff **0.45**. At 0.45 the gate is
load-bearing only for H5 (R1 final 0.6972) and H14 (0.7560); at 0.35 it is
also load-bearing for H2 (0.3813) and H12 (0.3480 — killed by 0.002, a
knife edge; see the Gemini consultation file). The 0.35–0.45 range must be
pinned to one number with one stated score definition before building —
Gemini's brief leaves both open.

**Head-to-head (all projections, not results):**

| Design | Residence rule | Firing set on the 16 | Projected exact / F1 | Main fragility |
|--------|---------------|----------------------|----------------------|----------------|
| v4r | R0 @ 0.15 + gate (claim False blocks) | K0, H4, H6, H13 | 10/16 / 0.905 | H4's firing rides on one aux prompt (0.6474); R0 full 0.1267 |
| v4.1 (ChatGPT Option D) | Claim True → fire regardless of score; False → block | K0, H4, H6, H13 | 10/16 / 0.905 (ChatGPT: 56/12/1, 0.896) | Gate is a frozen per-question annotation (§7); score-independent by design |
| v4.2 (Gemini) | R1 @ 0.35–0.45 + gate | K0, H4, H6, H13 | 10/16 / 0.905 | H12 sits 0.002 below the 0.35 cutoff; threshold fitted on the 16; Gemini's H2/H12 numbers were the mislabelled table values |

**Recommendation — run v4.1 FIRST after v4r, and why:** v4.1 is the only
design whose claim-True firing does not depend on any score threshold at
all, so it cannot be broken by a threshold fitted on 16 questions; its
force-fire branch is directly observable in the output
(`residence_evidence_fired`), giving a checkable prediction (§5); and it
carries the violence-union fix, which v4.2 as specified does not mention.
v4.2's 0.35 threshold is balanced on H12's 0.3480 (margin 0.002) and its
supporting numbers for H2/H12 were the mislabelled table values, so the
design needs re-derivation from the corrected keys before it can be
trusted — the re-derivation is done above (cutoff 0.45 on notebook
finals), but the choice between 0.35 and 0.45 still has no evidence behind
it on this set. If live v4r == live v4.1 (expected, §3), do NOT burn a run
on v4.2 to break the tie on the 16 — the tie cannot be broken there. Rank
v4.1 vs v4.2 on the sealed fresh-20 after 16/16, or on synthetic lockout
paraphrases, and keep the winner.

## §7 — Convergence, divergence, and the generalisation risk

**Both models agree:** keep the v3 maintenance/custody thresholds
(M 0.05 / C 0.13 buys 0 new TPs, only new FPs); the residence_claim gate
is good; R0 @ 0.15 as the *sole* firing signal is fragile on H4; the next
fix is the financial-claim boundary (maintenance vs Stridhan).

**They diverge on the residence mechanism:** ChatGPT Option D (gate as the
firing signal — claim True fires, score irrelevant) vs Gemini R1 @ 0.35
(score + gate as veto). Both project F1 0.905 / exact 10/16 on the current
16, and §3 shows their firing sets are identical there — so the live runs
on the 16 must decide nothing between them; the projections cannot
discriminate. The decision has to come from generalisation evidence, not
from re-running the 16.

**Generalisation risk (Gemini's flag, confirmed by inspection):**
`residence_claim` is a **frozen hand-written boolean per question in
Cell 6** — it is not extracted by a deterministic parser and not produced
by a Laya prompt at run time. On an unseen question, someone must annotate
it. A hard-zero veto on a hand annotation fails silently on indirect
lockout idioms ("in-laws kept my house keys", "he put my clothes outside
the door"). This is the same risk for v4r, v4.1 and v4.2 (all three use the
gate). The fix is Gemini's 2-option choice gate (§6) or a stated
extraction rule — a v5/v6 item, not a reason to delay the v4.1 run, but it
caps any claim that the residence fix generalises until it is done.

## §8 — Run order and what the live v4r run must report

1. **v4r live (running now).** Report: exact/16, micro-F1, TP/FP/FN,
   court, escalates; per-question: H4 exact? (settles §2), H5 PWDVA 18
   present? (settles §4), residence fired set (expect K0, H4, H6, H13),
   H12 empty? If H4 is lost, stop and re-derive — the aux assumption in
   §2 is wrong and v4.1's projection must be recomputed before running it.
2. **v4.1 live.** Expect identical headline numbers to v4r (§5) with
   `residence_evidence_fired` False everywhere and `violence_fired` True
   on H5/H13. Any difference from v4r is a live-score surprise, not a
   design difference — record it exactly.
3. **v4.2 (Gemini) — design only, do not build** until the parent decides
   run order after the v4r result (§6). If built, pin the cutoff to 0.45
   on notebook finals and record the choice in its change log.
4. Then v5 per `v5-planning-note.md` (financial-claim choice), not more
   residence variants.
