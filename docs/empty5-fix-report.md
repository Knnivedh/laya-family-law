# Empty-5 fix — Laya family-law live test (H1, H4, H8, H11, H14)

**Status: BUILT AND VALIDATED OFFLINE ONLY. No live Colab run yet.**
Scope is ONLY the 5 empty questions. This is not the full 10/10 plan.

- Baseline (live Colab 2026-11-26 ~22:28 IST): exact **5/16**, mean P/R 0.656/0.492, micro-P/R 0.875/0.368, TP/FP/FN **21/3/36** (57 GT sections), court 10/16, escalates 11/16, model errors 0/16.
- The 5 empties: H1, H4, H8, H11, H14 — all predicted `[]`, court `[]`, escalates `False`, GT non-empty. Together they account for 16 of the 36 missed sections (H1 2, H4 3, H8 2, H11 2, H14 7).
- Deliverables: this report + `live-laya-colab-test-v3-empty5.ipynb` (9 cells, 83 KB) + `build_laya_v3_empty5.py` (reproduces the notebook; re-run verified byte-identical, sha256 `c2042f14…`).
- Path correction: the v2 graph lives at `files/laya-crpc-bns-section-decision-tree-v2.json` (32 sections / 46 nodes / 77 edges, verified), **not** under `files/laya-graph/` as the task brief stated. Cell 5 uploads it by filename, so the notebook is unaffected.

## 1. Per-question diagnosis

### H1 — near-threshold miss
- Q: "My husband has not given me any money for three months. I earn fifteen thousand a month and I have two small children and no case filed anywhere."
- GT: BNSS 144, PWDVA 20. Stage 1: maintenance **0.4795**, stridhan (non-GT) **0.4948**, divorce 0.2804.
- Diagnosis: both maintenance and the non-GT stridhan sit just under 0.50. Threshold alone suffices — maintenance fires at any maintenance threshold ≤0.4795, and stridhan kept at 0.50 means the 0.4948 never fires. No FP added.
- Clause split (Lane B): ["My husband has not given me any money for three months" | "I earn fifteen thousand a month" | "I have two small children and no case filed anywhere"]. Split/aux are redundant backup only.

### H4 — phrase-coverage miss, completed eviction
- Q: "They changed the lock and I cannot enter my house. The house is in my husband's name."
- GT: PWDVA 17/18/19. Stage 1: residence **0.1267**, violence 0.1279.
- Diagnosis: explicit lock-change/eviction wording scores 0.1267. The phrasebook has only the hypothetical "can they change the lock and keep me out" — H4 is completed eviction, past tense. Threshold alone is fragile/unsafe: it fires only at t ≤0.1267, and a low residence threshold fires negatives in-sample (H2 0.8247, H5 0.4882).
- Needs the combination: clause-split + aux #1 + residence t≈0.13–0.15 + R1 residence prompt. No single lever suffices on the evidence.

### H8 — phrase-coverage miss, literal word present
- Q: "I need maintenance but I do not have my husband's salary slips and I do not know what he earns."
- GT: BNSS 144, PWDVA 20. Stage 1: maintenance **0.1746** despite the literal word "maintenance" in the question.
- Diagnosis: sharpest proof that verbatim wording does not guarantee a Laya score. Single clause by construction (negation-attachment — see §4), so clause-split contributes nothing (max = full score).
- Threshold alone predicted sufficient (0.1746 > maintenance ≈0.10; maintenance negatives are ≈0.0001 in-sample), OR aux #3 alone. Belt-and-braces: both.
- Correct behaviour once it fires: BNSS 144/PWDVA 20 + quantum escalation with ask-income text, explicitly never demanding slips. If it still does not fire, the court/escalate fallback (§5) is what saves H8, not a threshold change.

### H11 — interim-money framing + negation is the point
- Q: "I need money while my case is going on, but I have not filed any case yet."
- GT: BNSS 144, PWDVA 20 — **NOT HMA 24** (no proceeding pending). Stage 1: maintenance **0.1432**, divorce 0.0965.
- Diagnosis: the "not filed" negation is the whole point; the phrasebook's "I need support while my case is going on" maps to HMA 24/BNSS 144, which is wrong for H11. Single clause (the `but I` split is explicitly blocked), so clause-split is inapplicable.
- Threshold alone is marginal: fires at 0.10 (margin only 0.0432), misses at 0.15. Needs threshold (≈0.10) + aux #2 (verbatim full question, BNSS 144/PWDVA 20 only). If maintenance fires, Stage 2 must gate out the interim-HMA 24 option (`proceeding_pending=false`).

### H14 — total miss, worst question (7 FN)
- Q: "My divorce case is already going on in the Family Court. I want my son to stay with me and money for his school fees while the case goes on."
- GT: HMA 13, HMA 26, HMGA s.6, WELFARE, HMA 24, BNSS 144, PWDVA 20 (7 sections). Stage 1: maintenance **0.2542**, custody 0.1321, divorce 0.1395 — all ≤0.2542.
- Diagnosis: three explicit cues, three issues, all diluted. No phrasebook divorce phrase covers a case already pending — all 18 are "I want a divorce" (future), which is why divorce scored 0.1395. Custody has no clean threshold (positives/negatives overlap 0.11–0.16); divorce has none either (pending 0.1395 < H6 negation 0.384).
- Needs the combination: clause-split (primary mechanism) + aux #5/#8/#10 + per-issue thresholds (maintenance ≈0.10, custody ≈0.10–0.13, divorce-pending ≈0.10–0.15). HMA 24 / HMA 26 are Stage 2 consequences (`proceeding_pending=true`) — they fire only if maintenance/custody fire AND the sub-choice picks the interim / HMA 26 route.

## 2. Offline threshold sweep (Lane A — recomputed from saved stage1_raw, no model calls)

Issue–GT mapping: maintenance→BNSS 144/PWDVA 20/HMA 24; custody→GWA/HMGA/WELFARE/HMA 26; stridhan→BNS 316/HMA 27; residence→PWDVA 17 or 19 (PWDVA 18 alone does not count — H5's PWDVA 18 is the violence route); violence→`facts.violence==true`; divorce→HMA 13/13B or `divorce_asked`; birth→Births Act. 27 issue-positives total. Baseline at global 0.50 re-verified: issue TP 12/FP 1/FN 15, P 0.923/R 0.444/F1 0.600.

### 2.1 Per-issue POS/NEG (sorted) and best-F1 thresholds

| Issue | POS low→high | Highest NEG | Best F1 |
|---|---|---|---|
| Maintenance (10 POS, 6 NEG) | K0 0.0773, H13 0.1031, H11 0.1432, H10 0.1467, H8 0.1746, H14 0.2542, H1 0.4795, H5 0.5366, H9 0.7931, H6 0.898 | 0.0001 (H3, H15) — all 6 NEG ≈0 | **1.000 at any t ≤0.0773** (10/0/0). Perfectly separable. At t=0.10: 9/0/1 (misses diluted K0 only). |
| Custody (4 POS, 12 NEG) | H5 0.1098, H14 0.1321, K0 0.222, H2 0.852 | H6 0.1602, H8 0.1237, H12 0.1218, H10 0.1082, H11 0.1065 | **0.750 at t=0.13** (3/1/1; FP H6, FN H5). No clean threshold — overlap 0.11–0.16. |
| Stridhan (4 POS, 12 NEG) | H10 0.8929, H15 0.9032, K0 0.9064, H3 0.9332 | **H1 0.4948**, H9 0.2546 | **1.000 at t=0.50** (4/0/0). Keep 0.50 — any t ≤0.4948 fires false stridhan on H1. |
| Residence (4 POS, 12 NEG) | H4 0.1267, H6 0.2173, K0 0.265, H13 0.4212 | **H2 0.8247, H5 0.4882**, H10 0.1461, H14 0.1225 | **0.727 at t=0.1267** (4/3/0; FPs H2, H5, H10). Inverted: highest NEG exceeds every POS. Threshold alone cannot fix residence. |
| Violence (2 POS, 14 NEG) | H5 0.8343, H13 0.8892 | H2 0.2105, H4 0.1279 | **1.000 at any t in 0.22–0.83, incl. 0.50.** Keep 0.50. |
| Divorce, single-t (2 POS, 14 NEG) | H14 0.1395 (pending), H5 0.9475 (asked) | H6 0.384 ("I do not want a divorce" — negation), H1 0.2804 | **0.667 at t=0.40/0.50** (1/0/1 — H14 always missed). Split required: asked 0.40 (clean vs NEG max 0.384, margin only 0.016 — fragile), pending 0.10–0.15 (only when `proceeding_pending==true`; in this set, only H14). |
| Birth (1 POS, 15 NEG) | H7 0.6624 | H9 0.0264 | **1.000 at any t ≤0.66, incl. 0.50.** Keep 0.50. |

### 2.2 Candidate vectors — per-empty-5 recovery + FP added

All vectors keep stridhan/violence/birth at 0.50. Residence values are **conditional** on the R1 prompt + clause-split (see §2.3). Baseline V0 (all 0.50): issue TP 12/FP 1/FN 15, F1 0.600; all 5 empties empty; sole FP = H2 residence.

| Vector | Issue TP/FP/FN, P/R/F1 | H1 | H4 | H8 | H11 | H14 | New issue-FPs vs baseline (total FP) |
|---|---|---|---|---|---|---|---|
| **PRIMARY: M 0.05, C 0.13, R 0.15\*, D-asked 0.40, D-pend 0.13** | **25/3/2, P 0.893/R 0.926/F1 0.909** | maintenance ✓ | still empty | maintenance ✓ | maintenance ✓ | all 3 GT issues ✓ | H5 residence 0.4882, H6 custody 0.1602 (total 3, incl. H2 residence) |
| FALLBACK: M 0.10, C 0.20, R 0.15\*, D-asked 0.40, D-pend 0.13 | 23/2/4, P 0.920/R 0.852/F1 0.885 | ✓ | empty | ✓ | ✓ | maintenance ✓ + divorce ✓; custody ✗ (0.1321 < 0.20) | H5 residence only (total 2) |
| V2 conservative: M 0.10, C 0.20, R 0.20\*, D-asked 0.40, D-pend 0.15 | 22/2/5, P 0.917/R 0.815/F1 0.863 | ✓ | empty | ✓ | ✓ | maintenance only | H5 residence (total 2) |
| V4: M 0.10, C 0.13, R 0.13\*, D-asked 0.40, D-pend 0.10 | 24/4/3, P 0.857/R 0.889/F1 0.873 | ✓ | empty | ✓ | ✓ | all 3 ✓ | + H5 res, H6 cust, H10 res 0.1461 (total 4) — dominated by PRIMARY |
| V3 aggressive (**REJECTED**): M 0.07, C 0.10, R 0.10\*, D-asked 0.40, D-pend 0.10 | 27/10/0, P 0.730/R 1.000/F1 0.844 | ✓ | residence ✓ — only vector recovering H4 by threshold | ✓ + custody FP + residence FP | ✓ + custody FP | all 3 ✓ + residence FP | + H5 res, H6 cust, H8 cust+res, H10 cust+res, H11 cust, **H12 custody 0.1218 (breaks the out-of-scope control)**, H14 res (total 10) |

Other PRIMARY effects vs baseline: K0 gains maintenance + custody + residence (all 4 GT issues fire); H6 gains residence (custody FP also fires); H10 gains maintenance; H13 gains maintenance + residence (all 3 GT issues fire). H12 stays empty under PRIMARY and FALLBACK (max score custody 0.1218 < 0.13) — control preserved. H3/H7/H9/H15 unchanged and exact.

**H1 stridhan check (explicit):** 0.4948 stays below 0.50 in every candidate vector — no false stridhan added. It fires only if stridhan is lowered to ≤0.4948; do not.
**H2 residence check (explicit):** 0.8247 fires under every threshold in every candidate (and every global t ≤0.82). Threshold alone cannot fix it — needs the R1 prompt and/or the residence fact gate. Under PRIMARY, H2's 3 section-FPs remain, exactly as in the live baseline.

### 2.3 Residence conditional (\*) — read before applying
The R 0.15 numbers are computed on the *current* prompt/scores. Applied as-is, R 0.15 adds 2 issue-FPs (H2, H5) and still leaves H4 empty (0.1267 < 0.15). The 0.15 value is only valid **with** the R1 residence prompt + clause-split, which are expected to (a) cut H2 residence sharply below threshold and (b) lift H4's lock clause above 0.15. If those levers are not in place, the honest statement is: residence thresholding recovers K0/H6/H13 residence but does **not** recover H4 and adds H5-residence FP.

### 2.4 No global threshold works — proof
Fine 0.01 global sweep (single t, all 7 issues): best global t is **0.13, F1 0.767 (TP 23/FP 10/FN 4, P 0.697/R 0.852)** — slightly better than the plan's quoted t=0.12 (24/16/3, P 0.600/R 0.889/F1 0.716), but it still fails P>0.8 and R>0.8 together, and no global t in 0.05–0.50 achieves both (high-precision end t=0.39–0.42 gives P 0.824 but R 0.519; high-recall end gives R ≥0.85 only with P ≤0.697). **At t=0.10, FP explodes 1→21** (TP 26/FN 1, P 0.553/R 0.963) — including H1 stridhan (0.4948) and divorce, H2 violence, H9 stridhan + divorce, H12 custody + stridhan (breaking the out-of-scope control), and custody/residence FPs on H5/H6/H8/H10/H11/H14. **Do not propose global 0.10 alone.** Structural reason: true-positive floors differ by 0.82 across issues (maintenance 0.0773 vs stridhan 0.8929) and three issues are inverted/overlapping. Per-issue vectors (F1 0.885–0.909) beat the best global (0.767) by 0.12–0.14.

### 2.5 Corrections to the 10/10 plan §2 (Lane A, recomputed)
1. Custody best in-sample F1 is **0.750 at t=0.13**, not 0.667 at t=0.20.
2. Residence best in-sample F1 is **0.727 at t=0.1267**, not 0.667 at t=0.15.
3. Best global t is **0.13 (F1 0.767)**, not 0.12 (F1 0.716). None of these changes the no-global-threshold conclusion.

### 2.6 Hard caveat — issue-level firing ≠ section-level score
Everything in §2 is **issue-level only**. Sub-choice scores for newly fired issues were never run, so no section recovery claimed here is a measured score — all section numbers are estimates / upper bounds. Under the idealised assumption that every newly fired true issue's sub-choice picks exactly its GT sections: PRIMARY would give section TP 51/FP 8/FN 6, micro-P 0.864/micro-R 0.895, exact **12/16\*** (baseline 5/16 + K0, H1, H8, H10, H11, H13, H14); FALLBACK would give TP 46/FP 5/FN 11, micro-P 0.902/micro-R 0.807, exact **11/16\***. Remaining 6 section-FNs under PRIMARY are exactly H4 residence (PWDVA 17/18/19) + H5 custody (GWA/HMGA/WELFARE). The 8 section-FPs under PRIMARY are H2 residence (3, already live) + H5 residence (2 new — PWDVA 17/19 only, since 18 is already TP via violence) + H6 custody (up to 3 — route unknown, sub-choice never run). A real sub-choice could pick the wrong route (e.g. H14 custody → GWA instead of HMA 26, or HMA 25 via the maintenance root) and break an "exact\*" question, so 12/16 is a ceiling, not a prediction. All thresholds are in-sample on n=16 and will overfit — validate on the fresh held-out set before locking anything.

## 3. Clause-split + auxiliary prompts (Lane B)

### 3.1 Split rule (plan §2 Step 2, verbatim)
1. Keep the full-question pass as fallback/baseline — record it, do not delete it.
2. Split first on sentence boundaries `[.!?;]\s+`; then within a sentence on `,\s+and\s+` and on `\s+and\s+` **only when followed by** `I|my|he|they|my husband|my son|my daughter` (so "gold and cash" / "money and my child" do NOT split); also split on `\s+but\s+` when followed by `I|my` — **except** "but I have not filed any case yet" stays attached to its money clause, never split off alone.
3. Never split inside a negation ("do not want a divorce", "do not have salary slips", "have not filed any case yet" stay whole inside their clause).
4. Drop clauses with <3 words after stripping.
**Merge rule:** per-issue score = **max over clauses** (never mean — mean re-introduces dilution). Fire iff max-clause score ≥ its per-issue threshold. Record `fired_clause[issue]` = argmax clause text. Sub-choices run on the argmax clause (fallback to full question if clause <5 words).

### 3.2 Worked splits — the 5 empties
- **H1** → ["My husband has not given me any money for three months" | "I earn fifteen thousand a month" | "I have two small children and no case filed anywhere"] ("and no case…" does NOT split: "no" is not in the follow-list.)
- **H4** → ["They changed the lock and I cannot enter my house" | "The house is in my husband's name"]
- **H8** → single clause, kept whole: "I need maintenance but I do not have my husband's salary slips and I do not know what he earns" (20 words). The only candidate split points (`but I`, `and I`) both sit inside/introduce the negation chain; splitting would orphan "I need maintenance" from the facts that define the claim.
- **H11** → single clause, kept whole: "I need money while my case is going on, but I have not filed any case yet" (17 words). The `but I` split is explicitly blocked by the plan's own exception.
- **H14** → ["My divorce case is already going on in the Family Court" | "I want my son to stay with me" | "money for his school fees while the case goes on"]

All clauses in the 5 are ≥5 words, so no sub-choice fallback to the full question is triggered by clause length on this set. No <3-word fragment is produced by any of these splits.

### 3.3 Worked splits — controls that must NOT change
Treated as single clause = whole question, unchanged by construction (max = full-question score). H2: "Who will get my six year old son? My husband says as the father he will take him away from me." — no house/home mention; residence must NOT rise (fix is via the R1 prompt, not split). H3, H7, H9, H12, H15 likewise single-clause. H12 must stay empty.

### 3.4 The 12 auxiliary prompts (plan §2 Step 3, verbatim phrases)
Each aux prompt is `Does this question say "<verbatim phrase>" or mean the same thing?` Issue score = max(main prompt, aux prompts).

| # | Verbatim phrase | Source | Issue → sections | Note |
|---|---|---|---|---|
| 1 | "They changed the lock and I cannot enter my house" | H4 | residence → PWDVA 17/18/19 | Phrasebook has only hypothetical "can they change the lock and keep me out" — H4 is completed eviction, past tense. Single biggest residence gap (0.1267). **Directly covers H4.** |
| 2 | "I need money while my case is going on, but I have not filed any case yet" | H11 (full question) | maintenance → **BNSS 144 / PWDVA 20 only, explicitly NOT HMA 24** | Phrasebook's "I need support while my case is going on" maps to HMA 24/BNSS 144 — wrong for H11 (no proceeding pending). Negation is the whole point. **Directly covers H11.** |
| 3 | "I need maintenance but I do not have my husband's salary slips and I do not know what he earns" | H8 (full question) | maintenance → BNSS 144 / PWDVA 20 | "I do not have my husband's salary slips" exists in the phrasebook's documents/court section but **not** under maintenance, and the notebook never reads the phrasebook — live 0.1746. Guardrail: absence of slips must never block the claim. **Directly covers H8.** |
| 4 | "gives no money for my son's school fees" | H13 clause | maintenance → BNSS 144 / PWDVA 20 | Phrasebook has only the daughter version. (H13 outside empty-5 scope; retained as part of the 12.) |
| 5 | "money for his school fees while the case goes on" | H14 clause | maintenance → BNSS 144 / PWDVA 20 (+ HMA 24 only if proceeding pending — H14 yes) | **Directly covers H14 maintenance.** |
| 6 | "he gives no money for me and my child" | H10 clause | maintenance → BNSS 144 / PWDVA 20 | Near-duplicate of phrasebook "my husband is not giving me money" yet scored 0.1467 full-question — clause-split is the fix here, phrase is the aux backup. (H10 outside scope.) |
| 7 | "My husband has not given me any money for three months" | H1 clause | maintenance → BNSS 144 / PWDVA 20 | Duration + "two small children" + "no case filed anywhere" — no-case fact must route to BNSS 144/PWDVA 20, not HMA 24. **Directly covers H1.** |
| 8 | "I want my son to stay with me" | H14 clause | custody → GWA 1890 / HMGA s.6 / WELFARE (+ HMA 26 if proceeding pending — H14 yes) | Phrasebook has only the daughter version. **Directly covers H14 custody.** |
| 9 | "throws me out of the house" | H13 clause | residence → PWDVA 17/18/19 | Phrasebook has present-continuous "they are throwing me out of the house" only. (H13 outside scope.) |
| 10 | "My divorce case is already going on in the Family Court" | H14 clause | divorce-pending → HMA 13 (already filed) + HMA 24/26 via Stage 2 | **No phrasebook divorce phrase covers a case already pending** — all 18 are "I want a divorce" (future). This is why H14 divorce scored 0.1395. **Directly covers H14 divorce.** |
| 11 | "I want my daughter to stay with me" | H5 clause | custody → GWA / HMGA / WELFARE | Already in phrasebook verbatim — add as aux anyway to prove the gap is dilution, not coverage. (H5 outside scope.) |
| 12 | "to stay in the house with my daughter" | H6 clause | residence → PWDVA 17/19 | Near-identical to phrasebook "I want to stay in the same house with my daughter" yet scored 0.2173 — dilution, not coverage. (H6 outside scope.) |

7 of the 12 directly cover the 5 empties (#1 H4; #2 H11; #3 H8; #5, #8, #10 H14; #7 H1). **Wiring warning:** the v2 phrasebook is never read live. Cell 7 uses only the 7 `noul` instruction strings + graph node options. Adding any of these 12 phrases to the v2 JSON phrasebook alone does **nothing** live — each must be wired into Cell 7 as an auxiliary `noul` prompt. No stridhan/violence/birth phrases to add (stridhan 4/4, violence 2/2, birth 1/1 at t=0.50).

### 3.5 Per-question mechanism needed (predictions, not measurements)

| Q | Threshold alone? | Clause-split alone? | Aux alone? | Predicted needed |
|---|---|---|---|---|
| H1 maintenance | **Yes — sufficient.** 0.4795 fires at t≈0.10 and even 0.40; stridhan stays 0.50 so 0.4948 does not fire. | Not needed. | Not needed (redundant backup). | **Threshold alone.** |
| H4 residence | No — fragile/unsafe (fires only ≤0.1267; low t fires H2/H5 negatives). | Cannot be relied on alone (clause score rise unknown; may still sit below 0.13–0.15). | Strongest single lever, still unproven. | **Combination: split + aux #1 + residence t≈0.13–0.15 + R1 prompt.** |
| H8 maintenance | **Yes — sufficient (predicted).** 0.1746 > ≈0.10; maintenance negatives ≈0.0001. | **Cannot fix — inapplicable.** Single clause: max = full 0.1746. | Also sufficient in principle (verbatim full question). | **Threshold alone OR aux alone; combination is belt-and-braces.** Split: nothing. |
| H11 maintenance | Marginal — fires at 0.10 (margin 0.0432), misses at 0.15. | **Cannot fix — inapplicable.** Single clause. | Needed as second lever (aux #2, BNSS 144/PWDVA 20 only). | **Combination: threshold (≈0.10) + aux #2.** |
| H14 maintenance | Fires at ≈0.10 — only H14 issue threshold alone handles reliably. | **Primary mechanism, strongest hypothesis.** 3 clauses isolate 3 issues. | Could in principle fire all three without split, but aux-on-full-question still faces dilution; magnitudes unproven. | **Combination: split + aux (#5, #8, #10) + per-issue thresholds.** Split alone cannot be claimed sufficient. |
| H14 custody | No — no clean threshold (overlap 0.11–0.16). | Clause 2 isolated is the best hypothesis. | Aux #8. | Combination. |
| H14 divorce-pending | No — one divorce prompt conflates asked vs pending. | Clause 1 isolated is the best hypothesis. | Aux #10 — only phrase covering an already-pending case. | Combination. |

**What clause-split CANNOT fix on its own:** H8 and H11 are single-clause by construction (max = full score); H1 needs neither split nor aux; H4's split is plausible but unproven; H14 is the one question where split is primary — and even there it cannot be claimed sufficient without aux + thresholds, because no clause score has ever been run.

**Offline-proof caveat:** no clause-level score and no aux-prompt score was ever run. Every "lift" in §3.5 is a hypothesis to test live in Colab, not a measured score. Verbatim match does not guarantee a high Laya score — proven twice live: H8 contains the literal word "maintenance" and scored 0.1746; H5 contains the phrasebook-verbatim "I want my daughter to stay with me" and custody scored 0.1098.

## 4. Splitter divergences — coordinator decisions needed (do not silently pick one)

Lane B and Lane D both found the plan's worked splits deviate from a literal regex implementation. Recorded here; the v3 notebook implements Lane D's reading (below). If the live run's clause counts differ from §3.2, this section is the first place to look.

1. **H4 lock-event:** literal regex on `\s+and\s+` + `I` would split clause 1 into "They changed the lock" (4 words) / "I cannot enter my house". Plan §2's worked split keeps it whole. Lane B follows the worked split (lock-change + cannot-enter = one completed-eviction event; aux #1 is the whole sentence). Lane D implements it as a negation/fragment rule: a fragment whose first 4 words contain not/n't/never/cannot stays attached — covers "cannot enter my house". **Decision:** keep the lock clause whole (worked split governs).
2. **H14 "and money":** literal regex would NOT split sentence 2 ("and money" — "money" is not in the follow-list), giving 2 clauses. Plan §2's worked split gives 3. Lane B follows the 3-clause split (textbook dilution case, one clause per issue; aux #5/#8 are the two halves). Lane D's implementation: check the v3 `rec['clauses']` output in the live run to see which count it actually produced — if it produced 2, the H14 custody/maintenance separation is weaker than §3.2 assumes.
3. **H8 `but I` non-split:** rests on the negation-attachment reading of rule 3. Lane D implements the same via its fragment rule.
4. **Controls are "single clause" only if splitting is gated to multi-issue questions:** literal sentence-boundary splitting (`[.!?;]\s+`) fragments H2/H3/H7/H12/H15 into 2 sentence-fragments each. Lane D confirmed in validation: H3/H7/H15 are two-sentence questions, so they correctly yield 2 clauses — the plan's "single-clause" label for them meant single-issue. **Consequence:** "unchanged by construction" does NOT hold for the controls under a blind regex; the guardrail must be asserted as max-clause == full score on controls in every run, not assumed.
5. **Comma-only split (Lane D):** the plan's worked splits also split at bare commas ("He beats me, throws me out…", K0's last sentence). The verbatim rule has no comma-only split, so **H13 stays a single clause** in v3 and H5/K0 keep some comma-joined clauses whole. H13's fix must therefore come from thresholds (residence 0.4212 ≥ 0.15; maintenance 0.1031 ≥ 0.10) + aux phrases, not the split. `rec['clauses']` records the actual split per question in the live run.

## 5. Residence R1 + H2 guard + court/escalate fallback (Lane C)

### 5.1 Residence A/B test: R0 vs R1
- **R0 (current):** the existing residence prompt, containing "…or about protection from threats or violence at home?"
- **R1 (residence-only):** "Does this question ask about staying in, or being thrown out of, the shared house or home?"
- Do not silently alter R1's wording during the test. Known wording gap, recorded not fixed: R1 contains "shared house or home" but not "shared household" — a question phrased only as "shared household" may score low under R1. Follow-up would be a separate R1b arm adding "shared household", not a quiet edit to R1.
- **Run:** same 16 questions, same model/checkpoint, both prompts as the residence `noul` question; every other Stage-1 prompt, threshold and Stage-2 rule held fixed. Two layers, reported separately: **Layer A (isolated)** — full-question pass only, the clean R0-vs-R1 comparison; **Layer B (combined)** — clause-split max-clause + aux prompts. The adopt/reject decision is taken on Layer B (the configuration that would ship); Layer A must be reported alongside it so a Layer-B difference can be attributed.
- **Thresholds fixed across arms:** primary residence t=0.15; sensitivity grid t ∈ {0.10, 0.13, 0.20} recomputed offline. Other issues keep Step-1 thresholds.
- **Record per question:** R0_prob, R1_prob, delta, fired_R0/R1 @ 0.15 and @ {0.10, 0.13, 0.20}, residence sub-choice text if fired (a fired residence whose sub-choice hallucinates an eviction the question never states is a failure even if the prob looks plausible), kept residence sections, court under each arm. Plus run-level aggregates per arm: total section FP, micro-precision, exact match, H12 empty Y/N, controls H3/H7/H9/H15 exact Y/N.
- R0 anchors (live JSON, R0 arm must reproduce as sanity check): H2 0.8247, H4 0.1267, H6 0.2173, K0 0.265, H13 0.4212, H5 0.4882 (not GT residence), H10 0.1461, H14 0.1225.

**Proof H2 residence MUST fall under R1:** H2 — "Who will get my six year old son? My husband says as the father he will take him away from me." — is a single clause (split cannot change it, so any fall is attributable to the prompt alone) and contains **no** house/home/shared-household token and no eviction/lockout/stay language. The only residence-adjacent hook is "take him away" — whose object is the **child**, in a custody claim. The R0 mechanism is identified: R0's "…or about protection from threats or violence at home?" lets "he will take him away" read as a threat. R1 contains no threat/violence language; its only hooks are "staying in" / "being thrown out of" / "shared house or home", none of which the question states. **Prediction to verify (not a measured fact):** H2 R1 prob should collapse well below 0.15 — expect <0.10. If it does not, the prompt is not the mechanism and the residence fact gate (§3.2 of the plan) becomes the sole H2 fix.
**Consequence if it falls:** residence does not fire → no residence sub-choices → no PWDVA 17/18/19. H2 kept becomes exactly GT (GWA 1890, HMGA s.6, WELFARE). PWDVA 18 cannot sneak back via violence (H2 violence 0.2105 < 0.50). Court follows: Family Court only, fixing H2's court error (10/16 → 11/16).

**What R1 risks:** all four dev-16 true residence positives mention house/home (H4 "house", H6 "house", H13 "house", K0 "house"). **Zero dev-16 true residence positives lack a house/home token — so the R1 risk is untested on the dev set, not absent.** At-risk cases are all outside/edge of dev: rent/alternate accommodation (PWDVA 20 via rent, no "house" word — a fresh-set slot); "shared household" phrasing with no house/home token; "throw me out" with home implied not stated; violence-only residence (PWDVA 18 via beating, no house mention — partial mitigation: violence fires separately and adds PWDVA 18, so only PWDVA 17/19 are lost, as in H13's shape).
**If R1 cuts a true positive:** that question loses PWDVA 17/19 (and 18 if violence does not fire); exact match and recall fall; court may still survive via another kept issue, so the court score can mask the loss — judge R1 on section FP/FN and micro-precision, not court alone.

**Decision rule — adopt R1 iff ALL of (a)–(c) pass on the Layer-B run at t=0.15:**
(a) H2 fixed: H2 R1 prob <0.15, residence not fired, H2 kept == GT exactly, H2 court == [Family Court].
(b) No true positive lost: H4, H6, H13, K0 residence all still fire under R1 at t=0.15 in Layer B.
(c) No regression: total section FP ≤3 (target 0), micro-precision ≥0.875, exact ≥5/16, H12 stays empty, controls H3/H7/H9/H15 stay exact.
If (a) passes but (b) fails for ≥1 true positive → **keep R0**; fall back to thresholds + clause-split + aux prompts plus the residence fact gate (`eviction_or_threat`: H2=false, H4=true, H13=true, K0=true). If (b) fails only for a positive the fact gate/aux prompt recovers in the combined run, re-decide on the combined numbers. If (a) itself fails → R1 rejected outright; the fact gate is then the only H2 fix.

### 5.2 Court fallback — `court_for(kept, fired, probs, facts, in_scope)`
Replaces current `court_for(kept_ids)` (pure function of kept; empty kept → `[]`). Kept→court mapping unchanged (HMA 24/25/26/27/13/13B → Family Court; GWA/HMGA/WELFARE → Family Court; BNSS 144 / PWDVA 17–20 / BNS 316 → Magistrate; births-deaths-act → Registrar — see rule 6).
1. **Kept non-empty:** `court_for(kept)` as now. No change.
2. **Kept empty AND in-scope:** do **not** guess a court, do **not** emit `[]`. Emit `court: ["ESCALATE — no section kept, court cannot be derived"]` + `court_source: "fallback-escalate"` + top-2 candidate issues with probs as escalation payload, plus a typed `court` escalation. **Provisional court only if** a single issue dominates — top prob ≥0.40 **AND** margin over second ≥0.15. Dominance check on the 5 empties (from `stage1_raw`, verified by calculation):

| ID | Top (prob) | Second (prob) | Margin | Top ≥0.40? | Margin ≥0.15? | Dominates? |
|---|---|---|---|---|---|---|
| H1 | stridhan 0.4948 | maintenance 0.4795 | 0.0153 | Yes | No | **No** — and argmax is the *wrong* issue (GT is maintenance); argmax court would be Family+Magistrate vs expected [Magistrate] |
| H4 | violence 0.1279 | residence 0.1267 | 0.0012 | No | No | **No** |
| H8 | maintenance 0.1746 | custody 0.1237 | 0.0509 | No | No | **No** |
| H11 | maintenance 0.1432 | custody 0.1065 | 0.0367 | No | No | **No** |
| H14 | maintenance 0.2542 | divorce 0.1395 | 0.1147 | No | No | **No** |

So on this set the fallback is **escalation-only for all 5**. Do not tune the dominance thresholds to force a court out of these numbers. Per-question fallback payloads (top-2): H1 stridhan 0.4948, maintenance 0.4795; H4 violence 0.1279, residence 0.1267; H8 maintenance 0.1746, custody 0.1237; H11 maintenance 0.1432, custody 0.1065; H14 maintenance 0.2542, divorce 0.1395 (label the divorce entry `divorce-pending`, not `divorce-asked`, since H14's case is already going on).
**Scoring accounting:** the `"ESCALATE — …"` string is not in any expected court set, so Cell 8 must score all 5 as **court incorrect** under this fallback. The fallback converts court errors into correct escalations; it does not convert them into correct courts. Any report counting them as court-correct is wrong.
3. **Kept empty AND out-of-scope (H12):** stays `[]` / escalate False (`court_source: "out-of-scope-empty"`). Needs an `in_scope` flag: prob mass cannot separate in-scope empty H4 (max 0.1279) from out-of-scope empty H12 (max 0.1218) — gap **0.0061**. New 8th Stage-1 `noul` question: *"Does this question concern a Hindu matrimonial / domestic-relationship family-law matter?"* Record its prob as `stage1_raw["in_scope"]` on every question and report the full 16-question `in_scope` prob column. New Cell 6 `facts` field `in_scope: bool` — True for all except H12=False (H7 birth-certificate is True — within remit, GT non-empty, Registrar route). **Implementation honesty note:** in the Colab backtest the fallback gates on the **annotated** `facts['in_scope']`, consistent with every other `facts` field. In production there is no annotation — the gate must use the **model's `in_scope` prob with its own threshold**, not yet swept. Do not present the annotated-facts backtest as proof the production gate works; the `in_scope` prob column from the next run is the evidence that decides it.
4. **Spurious-fire guard (H2):** once the residence fact gate exists, court follows automatically. Without the gate, add a court-level consistency flag only: if every section supporting a court came from a single fired issue whose required fact is absent, mark that court provisional and escalate. For H2: Magistrate supported only by PWDVA 17/18/19, all from residence, with `eviction_or_threat=false` → Magistrate provisional + escalate. Implementable only after the new `facts` fields exist; `court_for` cannot know residence sections are spurious from `kept` alone.
5. **Cell 8 diagnostic:** `court_from_kept_covers_gt_court_via_gt_sections` — True only when the live court is right AND at least one kept GT section supports each expected court. On the baseline this reads **False for K0, H5, H13** (court right, wrong reason), stopping the court score from masking recall failure.
6. **Registrar edge fix:** equality (`kept == {births-deaths-act-1969}`) → membership (`'births-deaths-act-1969' in kept`). No live effect on dev 16 (H7 fires alone); protects the fresh-set "birth certificate bundled inside a multi-issue question" slot.

### 5.3 Typed escalations
Shape: `escalations_typed` entries `{kind, text}`, kinds `quantum` / `court` / `demand` / `fact`. New Cell 6 `facts` fields required (all currently assumed, never represented; on dev 16 all unknown/False unless stated): `income_known`, `school_fee_known`, `husband_location_known`.

| Kind | Fire iff | Text (verbatim where given) |
|---|---|---|
| `quantum` | Maintenance kept, OR fired, OR top near-miss (maintenance prob **≥0.05** — this floor matters: K0 maintenance is 0.0773 and must still qualify), AND income unknown | *"Quantum: husband's income / school fees unknown — escalate the amount, never invent it"*. **Never state an amount.** Attach only to maintenance questions. |
| `court` | Kept empty AND in-scope (§5.2 rule 2) | *"Court: no section kept — escalate; court cannot be derived from sub-threshold scores"* + top-2 payload. Never a guessed court. |
| `demand` | Stridhan kept AND `demand_made is False` | *"Stridhan: make a written demand for return first, then re-evaluate BNS s.316"* (already implemented; keep, typed). Do NOT gate BNS 316 itself (propose-and-escalate, not propose-then-drop). |
| `fact` | A fact the system needs is actually unknown | Ask text, conditional on the fact actually being unknown **and relevant**. An information ask to the user, after which the recheck re-runs; today it is static appended text. A `fact` entry alone does **not** count toward `escalates_live`. |

Conditional ask text (fixes the boilerplate): the current ask — *"Ask husband's income (estimate/range), school-fee amount, where husband lives now; never demand salary slips"* — is attached unconditionally to every non-empty question, including H7 (birth certificate) and H3/H10/H15 (stridhan-only). Under typed rules: income ask iff maintenance in play AND `income_known is False` ("Ask husband's income (estimate/range); never demand salary slips."); school-fee ask iff maintenance in play AND a child/school-fee context is present AND `school_fee_known is False` (H8 has no child/school-fee context → **no school-fee ask for H8**; H14 → ask it); location ask iff `husband_location_known is False` AND location is relevant to the remedy. The "never demand salary slips" guardrail stays verbatim wherever the income ask appears.

**H8 worked example (the key test):** "I need maintenance but I do not have my husband's salary slips and I do not know what he earns." Live: maintenance 0.1746, nothing fires, `escalations: []` — the user stated the exact facts the guardrail covers and the system went silent.
- **Path A — recovery (preferred):** maintenance ≥≈0.10 → fires → kept [BNSS 144, PWDVA 20] → court [Magistrate]. Typed: `quantum` (text above) + `fact` "Ask husband's income (estimate/range); never demand salary slips." No school-fee ask, no location ask, no amount, **no demand for salary slips — explicitly the opposite**.
- **Path B — fallback (this lane, if maintenance still does not fire):** kept empty + in-scope → court `["ESCALATE — …"]` with payload top-2 [maintenance 0.1746, custody 0.1237], plus typed `court` + `quantum` (maintenance is top issue at 0.1746 ≥0.05 near-miss floor, income unknown) + `fact` (ask-income text). Either path ends with the quantum escalation + ask-income text and no slip demand. **The empty-fallback is what saves H8 on Path B, not a threshold change** — Path A is strictly better (correct court as well as correct escalation).

**Scoring correction (Lane C, coordinator to confirm):** `escalates_live = True` iff any typed entry has kind ∈ {`quantum`, `court`, `demand`}. `fact` alone does not count. The plan's literal "score from the quantum/court flag" would flip H3 (stridhan-only, `demand_made is False`, maintenance 0.0001; its only genuine escalation is demand-first, `escalates_expected` True) to False — a false regression created by the typing itself. The 0.05 near-miss floor covers K0 (0.0773), H10 (0.1467) and H13 (0.1031) while correctly excluding H3/H15 (0.0001).

**Expected effects (this lane alone):** exact stays 5/16 (no Stage-1 firing or kept-section change, except via the R1/fact-gate H2 fix, which removes FPs but adds no TPs). Court stays 10/16 from the HMA 25 gate alone; **11/16 only if the residence fact gate / R1 fixes H2**. The empty-5 fallback converts 5 court errors into 5 correct escalations (court still wrong, escalates fixed). Escalates 11/16 → **16/16 if H7 resolved; 15/16 if not** (plan headline) — see the H15 caveat below: as the typed rules are specified here, H15 has no trigger and would score False, capping the honest ceiling at 15/16 even with H7 resolved unless H15's expected-True is resolved with a named reason.

## 6. What changed in the v3 notebook

File: `live-laya-colab-test-v3-empty5.ipynb` (9 cells, 83 KB) + builder `build_laya_v3_empty5.py` (re-run verified byte-identical).

**Cell 7 (Stage 1 + Stage 2):**
- Clause-split (plan §2 Step 2, Lane D implementation): sentence split, then `and`/`but` only before I/he/they/my husband/my son/my daughter; never split inside a negation (fragment whose first 4 words contain not/n't/never/cannot stays attached — covers "they will not return it", "have not filed any case yet", "cannot enter my house"); drop <3-word clauses; full question kept as baseline and in the max pool. Per-issue score = **max over clauses, never mean**. Records `fired_clause` (argmax clause), `fired_source` (clause/full/aux), `clauses`, `stage1_clause_max`, `stage1_final`.
- 12 aux prompts (§2 Step 3): all verbatim phrases wired as `Does this question say "<phrase>" or mean the same thing?` on the full question; issue score = max(main, aux).
- **Per-issue THRESHOLDS dict (as built):** maintenance 0.10, custody 0.20, stridhan 0.50, residence 0.15 (R1), violence 0.50, divorce-asked 0.45, divorce-pending 0.12, birth 0.50, in_scope 0.50. **Divorce split into two signals** (asked vs pending, separate prompt + aux phrase; fires if either meets its threshold); `divorce_signal` recorded.
- Residence R0/R1 A/B: both probs recorded (full + clause-max); `RESIDENCE_PROMPT="R1"` (default) selects the firing prompt; R0 retained for comparison only and never fires.
- **HMA 25 gate — FITTED, both layers** (plan §3.1): Layer A filters the "permanent alimony at/after an HMA decree" option out of `maintenance:maintenance-root` before offering it when `decree` is False; Layer B in `stage2()` adds hma-25 only if `decree` is True, else `gated_out` (never `dropped[]`). Old add-then-drop recheck block deleted. Records `candidates_before_gate` + `gated_out`. Offline shadow test embedded in the cell (fails fast if the gate breaks).
- Court fallback (§5.2): `court_for(kept, fired, probs, facts, in_scope)`; kept non-empty as v1 except Registrar is now membership; kept empty + in-scope → `["ESCALATE — no section kept, court cannot be derived"]` + top-2 payload + typed court escalation, never `[]`, never a guessed court; provisional court only if top ≥0.40 AND margin ≥0.15 (noted: holds for none of the 5); kept empty + out-of-scope → `[]` / escalate False. `in_scope` from the 8th Stage-1 noul question.
- Typed escalations (§5.3): `escalations_typed` {kind, text} — quantum only for maintenance questions (fired or kept), never an amount, ask-income text, never demand salary slips; demand-first Stridhan typed as `demand` (BNS 316 deliberately not gated). Plain-text `escalations` list also kept for backward compatibility.
- Hard rules kept: no keyword fallback, model error = miss; sub-choices only for fired issues, one call per fired issue with body = that issue's argmax clause (full question if <5 words).

**Cell 8 (scoring):**
- All original metrics kept (exact, mean/micro P/R, TP/FP/FN, court, escalates, forbidden before/after recheck, latency). **Added:** per-empty-5 table (exact, P/R, TP/FP/FN, court, escalates, fired issues + fired clauses); `forbidden_proposed_before_gate` + `gated_out_total` (+ Layer-B subtotal); `court_from_kept` diagnostic; residence R0-vs-R1 table (full + clause-max probs, fired under each); H2 check (residence fired? PWDVA 17/18/19 kept?) and H12 check (stays empty?).
- **Escalates scored from the typed quantum/court flag**, not `bool(escalations)` — with two diagnostics alongside (`escalates_live_any_typed`, `escalates_live_bool_plain`) so the change is visible. H7 `escalate_expected` kept exactly as-is; flagged OPEN in both cells.
- Saves/downloads **`live-laya-colab-results-v3-empty5.json/.md`** (new filenames; v1 filenames never overwritten).

**Deliberately left out (Lane D):** plan §3.2 pre-generation gates for HMA 24 / HMA 26 / divorce-gate / custody-route, and the residence fact gate — out of this lane's scope (task: HMA 25 gate only, "if it fits"). HMA 24/26 still use the v1 add-then-drop recheck shape in `stage2()`; the residence fact gate needs a new Cell 6 `facts` field, which would change ground truth. Both are stated in the Cell 7 header, not hidden.

## 7. ⚠️ MERGER DIVERGENCE — v3 thresholds are NOT Lane A's primary vector

This is the most important thing to know before the Colab run. Lane D implemented the **conservative** thresholds, not Lane A's recommended primary:

| | Maintenance | Custody | Residence | Divorce-asked | Divorce-pending |
|---|---|---|---|---|---|
| **Lane A PRIMARY** | 0.05 | 0.13 | 0.15\* | 0.40 | 0.13 |
| **v3 as built** | 0.10 | 0.20 | 0.15 | 0.45 | 0.12 |

Consequences on full-question scores alone (before any clause/aux lift):
- H14 custody 0.1321 **misses** under v3 (0.20) but fires under PRIMARY (0.13) — in v3, H14 custody depends entirely on the clause-split/aux lift, which is unproven.
- K0 maintenance 0.0773 **misses** under v3 (0.10) but fires under PRIMARY (0.05) — in v3, K0 maintenance depends entirely on clause/aux lift.
- H11 maintenance 0.1432 fires under both; H8 0.1746 fires under both; H1 0.4795 fires under both.
- Lane A issue-level PRIMARY: 25/3/2, F1 0.909. The v3-as-built vector is closest to Lane A's FALLBACK (23/2/4, F1 0.885) — it trades H14 custody (and K0 maintenance) for the H6 custody FP. That trade is defensible, but it was **not** a coordinator decision — it is a lane-implementation divergence, recorded here, not silently adopted. If the live run shows H14 custody or K0 maintenance still missing, the first thing to try is the PRIMARY vector (one-line THRESHOLDS change), not a new mechanism.

## 8. ⚠️ KNOWN v3 DEFECT — escalates scoring excludes `demand` (pre-run patch required)

Lane C corrected the plan's scoring to `escalates_live = True iff kind ∈ {quantum, court, demand}` (see §5.3 — without `demand`, H3 flips to False). **Lane D did not apply this correction.** v3 Cell 8 as built has:

```python
esc_live = bool(kinds & {'quantum', 'court'})  # PRIMARY v3 rule
```

with `esc_live_any = bool(kinds)` and `esc_live_bool = bool(r.get('escalations'))` recorded only as diagnostics. Consequence as built: **H3 (demand-only, `escalates_expected` True) will read escalates=False — a false regression created by the typing itself** — and H15 will also read False (see §9, OPEN #3). The diagnostics make this visible in the output, but the headline `escalates_correct` will be wrong for H3.

**Required pre-run patch (one line, in Cell 8, before running in Colab):**
```python
esc_live = bool(kinds & {'quantum', 'court', 'demand'})
```
Apply it, re-run the builder validation (`python3 -m json.tool`, `nbformat.validate`, `compile()` of Cells 7–8), and record in the run report that the patch was applied. Do **not** run v3 in Colab with the as-built line and then quote the escalates score — it will under-count by at least H3. This patch was deliberately NOT applied silently by the coordinator; it is recorded here as a required step for the parent to approve/apply.

## 9. Predicted empty-5 outcome (estimates, NOT scores)

Caveat first, repeated: **sub-choice scores for newly fired issues were never run, so every section-level prediction below is an estimate, not a score.** Clause/aux lifts are hypotheses until the live run measures them. Predicted at **issue level** under v3-as-built thresholds (M 0.10 / C 0.20 / R 0.15 / D-asked 0.45 / D-pend 0.12), assuming clause/aux lifts behave as hypothesised:

| Q | Predicted issue outcome | Predicted sections (if sub-choices pick GT routes) | What could still fail |
|---|---|---|---|
| H1 | maintenance fires (0.4795 ≥ 0.10); stridhan does NOT fire (0.4948 < 0.50) | BNSS 144, PWDVA 20 — **exact** | Sub-choice picks HMA 25 route (maintenance-root "permanent alimony") — mitigated by the HMA 25 gate (decree=False). |
| H4 | residence fires ONLY if split+aux #1+R1 lift it above 0.15 (full 0.1267 does not) | PWDVA 17/18/19 — **exact, conditional** | Aux #1 score stays ≤0.15; R1 cuts residence instead of lifting it; sub-choice invents a wrong residence route. |
| H8 | maintenance fires (0.1746 ≥ 0.10); aux #3 as backup | BNSS 144, PWDVA 20 — **exact** | Sub-choice picks HMA 25 route — mitigated by the HMA 25 gate. |
| H11 | maintenance fires (0.1432 ≥ 0.10); aux #2 as backup | BNSS 144, PWDVA 20 — **exact, conditional on aux/threshold holding** | Margin above 0.10 is only 0.0432; if the live threshold is re-picked at 0.15, H11 goes empty again. Stage 2 must not add HMA 24 (proceeding_pending=False). |
| H14 | maintenance fires (0.2542 ≥ 0.10); divorce-pending fires (0.1395 ≥ 0.12); custody fires ONLY if split+aux #8 lift 0.1321 above the v3 0.20 threshold (or PRIMARY 0.13 is used) | If all 3 fire + sub-choices pick HMA 13 / HMA 26 / interim-HMA 24 routes: all 7 GT sections — **exact, conditional**. If custody does not lift: 4/7 (HMA 13, HMA 24, BNSS 144, PWDVA 20) — still a large recovery, not exact. | Custody clause score stays ≤0.20; custody sub-choice picks GWA instead of HMA 26 (proceeding pending, so HMA 26 is the primary route); divorce sub-choice picks the wrong gate option. |

**Overall predicted (issue-level, PRIMARY vector):** 4 of 5 empties recover at issue level (H1, H8, H11 fully; H14 fully); H4 remains empty by threshold and needs Steps 2–3. **Under v3-as-built thresholds:** H1/H8/H11 as above; H14 custody is the swing issue; H4 unchanged. Section-level ceiling under PRIMARY (idealised): exact 12/16\* (see §2.6). Under v3-as-built thresholds the ceiling is lower (H14 custody + K0 maintenance depend on unproven lifts) — do not quote 12/16 for the v3 run.

**Guardrails that must hold on re-run (reject the run if any regresses, even if recall rises):**
- H12 stays empty; H2 loses residence FP (PWDVA 17/18/19 not kept) and keeps GWA/HMGA/WELFARE; H3/H7/H9/H15 stay exact.
- Micro-precision not below 0.875; exact not below 5/16.
- H5/H9 `kept_ids` byte-identical to v1 (H5 `[bnss-144, hma-13, pwdva-18, pwdva-20]`, H9 `[bnss-144, pwdva-20]`); `forbidden_proposed_before_gate` == 0 (was 2: H5, H9).
- Total section FP ≤3 (target 0).

## 10. OPEN items — contradictions recorded, not resolved

1. **HMA 27 prereq vs GT (H3/H10/H15).** v2 `hma-27` prereq requires "a matrimonial proceeding pending or being filed", yet GT includes HMA 27 with no proceeding on H3, H10 and H15, and `stage2()` adds it unconditionally on stridhan firing. **Do NOT gate HMA 27** — gating would break 3 exact matches. Coordinator decision needed first: either the prereq is wrong (the "alternatively… pressed as part of the family-court case" clause) or the GT is wrong. No pre-generation gate until settled.
2. **H7 escalate ambiguity.** Cell 6 `escalate_expected: True` for a fully answerable birth-certificate question with no missing fact. Either the expectation should be False, or a named escalation reason must be supplied (and a `fact`-kind entry alone does not make `escalates_live` True under §5.3). Unresolved → escalates ceiling 15/16.
3. **H15 escalate ambiguity (new, found by Lane C).** `escalates_expected: True` with no typed trigger under the §5.3 rules (maintenance 0.0001, `demand_made is True`, kept non-empty). Currently True only via the spurious quantum boilerplate this fix removes. Same treatment as H7: either the expectation is wrong or a named reason exists. Unresolved → honest ceiling 15/16 even with H7 resolved.
4. **Escalates scoring wording (plan §3.4 vs Lane C).** Plan's literal "score from the quantum/court flag" would flip H3 to False. Lane C corrects to {quantum, court, demand} (§5.3); v3 as built does NOT apply the correction (§8 — pre-run patch required). Coordinator to confirm the correction.
5. **`in_scope` production gate unproven.** Backtest gates on annotated `facts['in_scope']`; the live gate needs the model `in_scope` prob + threshold, not yet swept. The next run must report the `in_scope` prob column for all 16 before the production gate is claimed.
6. **R1 "shared household" wording gap.** R1 as specified lacks the token "household"; a household-only phrasing may miss. Follow-up R1b arm if the A/B shows it — not a silent edit.
7. **H2 custody sub-choice contradiction (carried).** H2 chose custody option A ("Custody inside a matrimonial proceeding (HMA s.26)") with no proceeding pending; `stage2()` silently discarded it and the facts path kept GWA/HMGA/WELFARE correctly. Option-gating fix is plan §3.2 (HMA 26 row); Lane C's court guard only flags the downstream court effect.
8. **Splitter rule text vs worked splits (§4).** H4 lock-event, H14 "and money", H8 negation-attachment, controls fragmentation, comma-only split — the rule text must be amended to state these exceptions explicitly, or the next implementer running the regex literally gets different clause counts and different scores.
9. **HMA 24 / HMA 26 / divorce-gate / custody-route pre-generation gates and the residence fact gate** were deliberately left out of v3 (Lane D scope). HMA 24/26 still use the v1 add-then-drop recheck shape in `stage2()`.

## 11. Validation performed (coordinator re-check + Lane D)

- `python3 -m json.tool` on the v3 notebook: PASS. `nbformat.validate`: PASS. 9 cells.
- **Cells 0–5 byte-identical** to the original (all 6 PASS, re-checked by coordinator).
- **Cell 6 diff: exactly 96 lines changed, every one differing ONLY by `false→False` / `true→True` / `null→None`** (80 facts values + 16 `escalate_expected` values); no `false`/`true`/`null` literals remain in Cell 6; TEST_SET execs from the v3 notebook (original Cell 6 cannot exec as Python — that is the known bug v3 fixes); v3 TEST_SET ids K0+H1–H15, GT ids unchanged (H1 `[bnss-144, pwdva-20]`, H4 `[pwdva-17, pwdva-18, pwdva-19]`, H8 `[bnss-144, pwdva-20]`, H11 `[bnss-144, pwdva-20]`, H14 `[hma-13, hma-26, hmga-1956-s6, welfare-principle, hma-24, bnss-144, pwdva-20]`).
- `compile()` of Cell 7 and Cell 8 sources: PASS.
- Offline functional tests (Lane D, Cell 7 defs exec'd with stubs, no model): clause-splitter on all 16 questions — K0 → 5 clauses, H5 custody clause split out, H14 pending-case clause split out, H11 single clause (negation intact), H4 lock clause kept whole, no clause <3 words. HMA 25 gate shadow tests PASS both directions; quantum not attached to birth-certificate-only; demand typed correctly; `court_for` PASS for kept, fallback-escalate, out-of-scope `[]`, provisional-on-dominance, and no-provisional-below-threshold cases. Cell 7's own embedded shadow test also printed PASS during validation.
- Rebuild reproducibility: re-running `build_laya_v3_empty5.py` produces an identical sha256 (`c2042f14…`).
- **What was NOT validated:** no live Laya call was made in this task. Clause-level scores, aux-prompt scores, R1 probs, `in_scope` probs, and every section-level prediction in §9 are unproven until the Colab run.

## 12. Exact Colab steps to run v3 next

1. **Apply the §8 pre-run patch first** (one line in Cell 8: `esc_live = bool(kinds & {'quantum', 'court', 'demand'})`), then re-validate (`python3 -m json.tool`, `nbformat.validate`, `compile()` Cells 7–8) and record the patch in the run report. Do not run with the as-built line and quote the escalates score.
2. Upload `live-laya-colab-test-v3-empty5.ipynb` to Google Drive (account used before: nivedhbhat15@gmail.com) and open in Colab. Optional: Runtime → Change runtime type → T4 GPU (CPU-only also works; expect ~10–20 min, longer than v1's 188 s because v3 makes ~1 full + n_clauses + 1 aux + n_fired sub-choice calls per question).
3. Run cells in order 0–8 (Runtime → Run all). Cell 2 installs `laya==0.5.5`; Cell 4 downloads the PIXMELT/laya snapshot and loads the classic checkpoint only; Cell 5 will prompt to upload `laya-crpc-bns-section-decision-tree-v2.json` — **it lives at `files/laya-crpc-bns-section-decision-tree-v2.json`** (also in `colab_bundle/`), not under `files/laya-graph/` (asserts 32/46/77).
4. Watch Cell 7 output: the HMA 25 gate shadow test must print PASS before the live loop starts; per-question lines show `fired=… kept=… court=… (source)`.
5. Cell 8 prints the aggregate, per-question table, empty-5 table, residence R0-vs-R1 table, and H2/H12 checks, then saves and downloads **`live-laya-colab-results-v3-empty5.json`** and **`live-laya-colab-results-v3-empty5.md`** — send both files back to Muse to record the live score.
6. Expected checks on the results: H5/H9 `kept_ids` byte-identical to v1, `forbidden_proposed_before_gate` 0, H12 stays empty, H2 loses PWDVA 17/18/19, guardrails in §9 hold. If H14 custody or K0 maintenance is still missing, first try the Lane A PRIMARY thresholds (M 0.05, C 0.13 — one-line THRESHOLDS change, §7) before inventing a new mechanism.
