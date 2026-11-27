# Laya family-law system — exact plan from live 3/10 to 10/10

**Status: PLAN ONLY. No fix implemented.** This file merges the five parallel lanes (diagnosis, recall/threshold, Stage 2/court/escalate, test expansion/prose, 10/10 gate). It is the input for the Gemini + ChatGPT consultations running in parallel in the browser; their verified responses are to be merged in next, before any code changes.

**Files read by the lanes:** live results JSON + MD (`workspace/browser_downloads/sess-2896751965/`), v2 graph (`laya-crpc-bns-section-decision-tree-v2.json`, 32 sections / 46 nodes / 77 edges), notebook (`live-laya-colab-test.ipynb`, 9 cells 0–8), backtest plan (`backtest-laya-vs-llama8b.md`).

## 0. Frozen live baseline (Colab, 2026-11-26 ~22:28 IST, Laya 421M classic ModernBERT + v2 graph)

| Metric | Baseline |
|---|---|
| Exact section-set match, current 16 (K0 + H1–H15) | **5/16** (H3, H7, H9, H12, H15) |
| Mean precision / mean recall | 0.656 / 0.492 |
| Micro precision / micro recall | 0.875 / 0.368 |
| TP / FP / FN (of 57 GT sections) | **21 / 3 / 36** |
| Court correct | 10/16 |
| Escalates correctly | 11/16 |
| Silent questions (non-empty GT, empty prediction) | **5** (H1, H4, H8, H11, H14) |
| Forbidden before Stage 2 recheck | **2** (H5, H9 — both "HMA 25 with no decree") |
| Forbidden after Stage 2 recheck | 0 — **by construction** (Stage 2 drops them). Never quote as a live result; the live error count is 2. |
| Prose forbidden mappings | **NOT MEASURED** (classification only, no answer prose generated) |
| Model errors | 0/16 |
| Latency | mean ~11.8 s, max 24.17 s (K0), min 7.41 s (H4); full run 188 s; model load 25.8 s |
| Honest live rating | **3.3/10** by the frozen formula in §6 (down from provisional 5/10) |

**Graph-walk 16/16 is NOT a baseline and NOT the gate.** It walks the graph's own rules on questions written in the graph's own phrasings. Never quote it as a live score.

**Threshold note (ambiguity, stated by Lane 1):** the JSON never states a threshold. `fired_issues` is consistent in all 16 questions with a single global threshold of **0.5** (every fired issue ≥0.5366; every non-fired issue ≤0.4948). Lane 2 verified the notebook: Cell 7, Stage 1 = one `noul` question per issue (7 issues), single hard-coded line `if p is not None and p >= 0.50:`. `stage1_raw` == `stage1_probs` in every question — no calibration step exists.

**Critical finding (Lane 2): the v2 phrasebook is never read by the live notebook.** Cell 7 uses only the 7 `noul` instruction strings + graph node options. The phrasebook (126 phrases) changes nothing live until its phrases are wired into Cell 7 as auxiliary `noul` prompts.

## 1. Diagnosis — per-question root-cause table (all 16)

Prob columns are Stage 1 raw scores for the 7 issues, in order **M**aintenance / **C**ustody / **S**tridhan / **R**esidence / **V**iolence / **D**ivorce / **B**irth-cert.

| ID | Exact? | P | R | TP/FP/FN | Predicted | GT | Stage 1 raw (M/C/S/R/V/D/B) | Court? | Esc? | Root cause |
|---|---|---|---|---|---|---|---|---|---|---|
| K0 | N | 1.0 | 0.20 | 2/0/8 | BNS 316, HMA 27 | BNSS 144, PWDVA 20, GWA 1890, HMGA s.6, WELFARE, HMA 27, BNS 316, PWDVA 17/18/19 | 0.0773 / 0.222 / **0.9064** / 0.265 / 0.0527 / 0.2189 / 0.0 | Y | Y | Multi-issue dilution: only Stridhan fires (0.9064); maintenance 0.0773, custody 0.222, residence 0.265 all far below threshold. 8 FN. Court correct only by coincidence (kept Stridhan set maps to same two courts). |
| H1 | N | 0.0 | 0.0 | 0/0/2 | (none) | BNSS 144, PWDVA 20 | 0.4795 / 0.0894 / 0.4948 / 0.0968 / 0.0811 / 0.2804 / 0.0007 | N | N | Near-threshold miss: maintenance 0.4795 and (non-GT) Stridhan 0.4948 both just under 0.5; nothing fires. |
| H2 | N | 0.5 | 1.0 | 3/3/0 | GWA 1890, HMGA s.6, PWDVA 17/18/19, WELFARE | GWA 1890, HMGA s.6, WELFARE | 0.0 / **0.852** / 0.0 / **0.8247** / 0.2105 / 0.0739 / 0.0 | N | Y | Spurious over-fire: residence 0.8247 on custody-only question ("take him away" misread as eviction); sub-choice invents "threatened with eviction". All 3 FP in the run + wrong extra Magistrate court. Only question with any FP. |
| H3 | Y | 1.0 | 1.0 | 2/0/0 | BNS 316, HMA 27 | HMA 27, BNS 316 | 0.0001 / 0.0744 / **0.9332** / 0.057 / 0.0003 / 0.0753 / 0.0 | Y | Y | Worked: single issue, canonical phrasing, Stridhan 0.9332 fires cleanly and alone. |
| H4 | N | 0.0 | 0.0 | 0/0/3 | (none) | PWDVA 17/18/19 | 0.0 / 0.0492 / 0.0133 / 0.1267 / 0.1279 / 0.0001 / 0.0 | N | N | Phrase-coverage miss: residence 0.1267 despite explicit lock-change/eviction wording ("changed the lock, cannot enter"). 3 FN + court + escalation lost. |
| H5 | N | 1.0 | 0.571 | 4/0/3 | BNSS 144, HMA 13, PWDVA 18/20 | HMA 13, BNSS 144, PWDVA 20/18, GWA 1890, HMGA s.6, WELFARE | **0.5366** / 0.1098 / 0.0003 / 0.4882 / **0.8343** / **0.9475** / 0.0 | Y | Y | Multi-issue dilution for custody (0.1098) despite "daughter to stay with me" — all 3 FN are custody. Residence 0.4882 near-miss caused 0 FN (PWDVA 18 rescued via violence). Stage 2 correctly dropped HMA 25 (1 forbidden-before). |
| H6 | N | 1.0 | 0.40 | 2/0/3 | BNSS 144, PWDVA 20 | BNSS 144, PWDVA 20, PWDVA 17/18/19 | **0.898** / 0.1602 / 0.0555 / 0.2173 / 0.0543 / 0.384 / 0.0 | Y | Y | Multi-issue dilution: maintenance fires at 0.898 while residence scores 0.2173 despite "stay in the house with my daughter". All 3 FN residence. |
| H7 | Y | 1.0 | 1.0 | 1/0/0 | Births and Deaths Act 1969 | Births and Deaths Act 1969 | 0.0 / 0.0281 / 0.0 / 0.0001 / 0.0 / 0.0 / **0.6624** | Y | Y | Worked: single issue, canonical phrasing, birth-certificate 0.6624 fires alone (lowest winning score among exact questions, still 0.16 above threshold). |
| H8 | N | 0.0 | 0.0 | 0/0/2 | (none) | BNSS 144, PWDVA 20 | 0.1746 / 0.1237 / 0.0626 / 0.1008 / 0.0388 / 0.1251 / 0.0002 | N | N | Phrase-coverage miss: maintenance 0.1746 even though the word "maintenance" is in the question ("I need maintenance but I do not have salary slips"). 2 FN + court + escalation lost. |
| H9 | Y | 1.0 | 1.0 | 2/0/0 | BNSS 144, PWDVA 20 | BNSS 144, PWDVA 20 | **0.7931** / 0.0796 / 0.2546 / 0.0608 / 0.003 / 0.1262 / 0.0264 | Y | Y | Worked: maintenance 0.7931 fires on "how much money can I get every month"; Stage 2 correctly dropped HMA 25 (1 forbidden-before). Note: its sub-choice wrongly says "permanent alimony at/after an HMA decree" though no decree exists — no score impact because Stage 2 dropped it. |
| H10 | N | 1.0 | 0.50 | 2/0/2 | BNS 316, HMA 27 | HMA 27, BNS 316, BNSS 144, PWDVA 20 | 0.1467 / 0.1082 / **0.8929** / 0.1461 / 0.0745 / 0.1164 / 0.0 | Y | Y | Multi-issue dilution: Stridhan fires at 0.8929 while maintenance scores 0.1467 despite "he gives no money for me and my child". 2 FN. |
| H11 | N | 0.0 | 0.0 | 0/0/2 | (none) | BNSS 144, PWDVA 20 | 0.1432 / 0.1065 / 0.081 / 0.0555 / 0.016 / 0.0965 / 0.0 | N | N | Phrase-coverage miss: maintenance 0.1432 on "I need money while my case is going on, but I have not filed any case yet" — interim-money framing not recognised, divorce only 0.0965 so no HMA 24 route either. 2 FN + court + escalation lost. |
| H12 | Y | 1.0 | 1.0 | 0/0/0 | (none) | (none) | 0.0 / 0.1218 / 0.1146 / 0.0468 / 0.0431 / 0.085 / 0.0 | Y | Y | Exact by abstention, not recognition: out-of-scope question, all scores ≤0.1218, nothing fires, GT empty. P/R of 1.0 here are conventions for 0/0, not measured ratios. |
| H13 | N | 1.0 | 0.20 | 1/0/4 | PWDVA 18 | PWDVA 18/17/19/20, BNSS 144 | 0.1031 / 0.035 / 0.001 / 0.4212 / **0.8892** / 0.0414 / 0.0 | Y | Y | Mixed: violence fires (0.8892, PWDVA 18 TP) but residence near-miss (0.4212 → PWDVA 17/19 FN) and maintenance suppressed (0.1031 → BNSS 144/PWDVA 20 FN) despite "gives no money for school fees". Worst recall among non-empty predictions. |
| H14 | N | 0.0 | 0.0 | 0/0/7 | (none) | HMA 13, HMA 26, HMGA s.6, WELFARE, HMA 24, BNSS 144, PWDVA 20 | 0.2542 / 0.1321 / 0.097 / 0.1225 / 0.0001 / 0.1395 / 0.0 | N | N | Phrase-coverage total miss — worst single question (7 FN): all 7 issues ≤0.2542, nothing fires despite three explicit cues ("divorce case already going on", "son to stay with me", "money for school fees while the case goes on"). Court + escalation lost. |
| H15 | Y | 1.0 | 1.0 | 2/0/0 | BNS 316, HMA 27 | BNS 316, HMA 27 | 0.0001 / 0.0859 / **0.9032** / 0.067 / 0.07 / 0.0 / 0.0 | Y | Y | Worked: single issue, canonical phrasing ("sold my gold", "given by my parents at my wedding"), Stridhan 0.9032 fires cleanly and alone. |

Per-question TP/FP/FN sums check: TP 21, FP 3, FN 36 — matches the aggregate.

### Ranked root-cause families (Lane 1)

**Family 1 — Multi-issue dilution / secondary-issue suppression: 18 FN, 0 FP, 5 questions (K0, H5, H6, H10, H13-maintenance part). Rank 1.** Whenever one issue fires ≥0.83, every co-present issue scores ≤0.27 (K0: Stridhan 0.9064 vs maintenance 0.0773 / custody 0.222 / residence 0.265; H10: 0.8929 vs maintenance 0.1467; H6: 0.898 vs residence 0.2173; H5: divorce 0.9475 / violence 0.8343 vs custody 0.1098; H13: violence 0.8892 vs maintenance 0.1031). FN split: maintenance 6, custody 6, residence 6. This is a correlation in the JSON, not proof of causation — consistent with winner-takes-all scoring, but the JSON cannot prove the mechanism.

**Family 2 — Pure phrase-coverage miss (no issue fires, all relevant scores ≤0.26): 14 FN, 0 FP, 4 questions (H4, H8, H11, H14). Rank 2.** H4 residence 0.1267 (3 FN), H8 maintenance 0.1746 (2 FN), H11 maintenance 0.1432 (2 FN), H14 all issues ≤0.2542 (7 FN). H8 is sharpest — the literal word "maintenance" is in the question and still scores 0.1746. FN split: maintenance 7 (incl. HMA 24 in H14), residence 3, custody 3, divorce-route (HMA 13) 1.

**Family 3 — Near-threshold miss (relevant score 0.42–0.50, just under inferred 0.5): 4 FN, 0 FP, 2 questions (H1, H13-residence part). Rank 3.** H1 maintenance 0.4795 (2 FN; non-GT Stridhan 0.4948 also just under, so a lower threshold would add an FP there); H13 residence 0.4212 (2 FN: PWDVA 17/19). H5 residence 0.4882 is a third near-miss but caused 0 FN (PWDVA 18 rescued via violence). Smallest FN family — lowering the threshold alone recovers at most these 4 FN and risks new FPs.

**Family 4 — Spurious over-fire: 0 FN, 3 FP, 1 question (H2). Rank 4 (by FN; only FP family).** Residence 0.8247 fires on a custody-only question; the residence sub-choice hallucinates an eviction ("threatened with eviction, still living in the house") that the question never states. All 3 FP in the run + H2's wrong court (extra Magistrate). H1's Stridhan 0.4948 shows the same over-fire tendency sitting just below threshold.

**Family 5 — Stage 2 drops: 0 FN, 0 FP. Exonerated.** Stage 2 dropped nothing in GT in any question (`candidates_before_stage2` = `kept_ids` except H5/H9, where HMA 25 was correctly dropped for "no decree"). Every FN traces to an issue never firing; every FP traces to an issue firing wrongly. Graph logic is not implicated by the live numbers.

**Family 6 — Downstream court / escalation cascade: 0 independent FN/FP, but court wrong 6/16, escalates wrong 5/16.** Court and escalation derive from the kept set, so they inherit Stage 1: all 5 empty-prediction questions lose both court and escalation, and H2's court error comes solely from its FP residence set. Conversely K0's court is correct despite 8 FN — court correctness does not imply section correctness. The 5 empty questions also produce zero escalations (`escalations: []`), so even the generic quantum escalation is lost with them. Lane 3 correction: H2's court error is downstream of Stage 1 firing something *wrong*, not nothing — the empty-5 mechanism explains 5 of 6 court errors and all 5 escalate errors; H2 is the separate spurious-fire mechanism.

### Cross-check by label (sums to 36 FN)

Maintenance-route labels 15 (BNSS 144 ×7, PWDVA 20 ×7, HMA 24 ×1) · residence labels 11 (PWDVA 17 ×4, 19 ×4, 18 ×3) · custody labels 9 (HMGA s.6 ×3, WELFARE ×3, GWA 1890 ×2, HMA 26 ×1) · divorce-route (HMA 13) 1. **Maintenance is the worst issue: missed in 7 of the 16 questions** (K0, H1, H8, H10, H11, H13, H14).

### Sub-choice contradictions (Lane 1, flagged — do not ignore)

- H2's custody sub-choice says "custody inside a matrimonial proceeding (HMA s.26)" yet HMA 26 is not kept (GWA route is).
- H5/H9's maintenance-root says "permanent alimony at/after an HMA decree" though no decree exists (Stage 2 saved the output by dropping HMA 25).
- H3/H10/H15 differ on Stridhan civil-vs-criminal ("both" vs "civil_only") yet all three keep the same BNS 316 + HMA 27 pair — the sub-choice had no observable effect on output.
- "WELFARE" (welfare-of-the-child principle) is counted as a label alongside sections in both GT and predictions.

## 2. Ordered fix steps

Fix in this order. One change, one hypothesis, one live Colab re-run per cycle (§7). Do not batch multiple fixes per run.

### Step 1 — Offline threshold sweep (no model calls; minutes)

New notebook Cell 9: load `live-laya-colab-results.json`, recompute the issue-level table and the global sweep (t = 0.05…0.50) from saved `stage1_raw`, print per-issue POS/NEG sorted lists and best-F1 thresholds, output 2–3 candidate threshold vectors. **This cell cannot give true section scores for newly fired issues** (their sub-choices were never run) — it only shortlists vectors. Do not quote its issue-level F1 as a section score.

Per-issue threshold ranges TO TEST (Lane 2, issue-level GT derived from JSON `gt_ids` + `facts`; 27 issue-positives total; at t=0.50: issue TP 12 / FP 1 / FN 15, P 0.923 / R 0.444). **Ranges, not final values. All "best" values are in-sample on n=16 and will overfit — validate on a fresh held-out set before locking anything.**

| Issue | True-positive probs (low→high) | Highest false-positive probs | Range to test | Evidence / expected pick |
|---|---|---|---|---|
| maintenance | 0.0773 K0, 0.1031 H13, 0.1432 H11, 0.1467 H10, 0.1746 H8, 0.2542 H14, 0.4795 H1, 0.5366 H5, 0.7931 H9, 0.898 H6 | **0.0001** (H3, H15) — all 6 negatives ≈0 | **0.05–0.20** (grid 0.05, 0.07, 0.10, 0.15, 0.20) | Perfectly separable: t=0.05 gives 10/10 TP, 0 FP in-sample. Lowest true is diluted K0 (0.0773); lowest single-issue true is H13 0.1031. Expected pick ≈0.10. Only issue where a big drop is safe. |
| custody | 0.1098 H5, 0.1321 H14, 0.222 K0, 0.852 H2 | 0.1602 H6, 0.1237 H8, 0.1218 H12, 0.1082 H10, 0.1065 H11 | **0.10–0.22** (grid 0.10, 0.13, 0.16, 0.20) | **No clean threshold exists:** positives and negatives overlap 0.11–0.16. Best in-sample F1 0.667 at t=0.20 (TP 2, FP 0, FN 2); t=0.10 gives TP 4 but FP 5. Threshold alone cannot fix custody — needs Step 2 (clause-split). |
| stridhan | 0.8929 H10, 0.9032 H15, 0.9064 K0, 0.9332 H3 | 0.4948 H1, 0.2546 H9 | **0.50–0.70** (test 0.50, 0.60 only) | Perfect at 0.50 (4/4, 0 FP). **Do not test below 0.50:** H1's 0.4948 is a hair under the line — lowering to 0.25 fires H1 + H9 as false stridhan. Keep 0.50. |
| residence | 0.1267 H4, 0.2173 H6, 0.265 K0, 0.4212 H13 | **0.8247 H2, 0.4882 H5**, 0.1461 H10, 0.1225 H14 | **0.10–0.20** (grid 0.10, 0.13, 0.15, 0.20) **only with new prompt + clause-split** | **Inverted:** highest negative (H2 0.8247) exceeds every true positive (max 0.4212). Best in-sample F1 0.667 at t=0.15 (TP 3, FP 2, FN 1). Threshold alone cannot fix residence. |
| violence | 0.8343 H5, 0.8892 H13 | 0.2105 H2, 0.1279 H4 | **0.30–0.50** (keep 0.50; test 0.30 as sensitivity only) | Clean gap 0.21→0.83; perfect at 0.50. No drop needed. |
| divorce | 0.1395 H14, 0.9475 H5 | 0.384 H6 ("I do not want a divorce" — negation), 0.2804 H1, 0.2189 K0 | **Split into two signals:** divorce-asked **0.40–0.50**; divorce-pending **0.10–0.15** | H5 (asked) 0.9475 vs negatives ≤0.384 — clean at 0.40. H14 (0.1395) is *pending*, not *asked*; one prompt conflates the two. Pending signal needs its own low threshold, gated by Stage 2 (§3). |
| birth_certificate | 0.6624 H7 | 0.0264 H9 | **0.30–0.50** (keep 0.50) | Clean gap; no change needed. |

**Why a single global threshold cannot work — with numbers.** True-positive floors differ by 0.82 across issues (maintenance 0.0773 vs stridhan 0.8929), and three issues have inverted/overlapping ranges (residence NEG 0.8247 > all POS; custody POS 0.1098 < NEG 0.1602; divorce POS 0.1395 < NEG 0.384). Global sweep on saved probs (issue-level proxy): t=0.50 → TP 12/FP 1/FN 15, P 0.923/R 0.444/F1 0.600; t=0.25 → 16/6/11, F1 0.653; t=0.15 → 19/9/8, F1 0.691; **best global t=0.12 → 24/16/3, P 0.600/R 0.889/F1 0.716**; t=0.10 → 26/21/1, P 0.553/R 0.963. No global t reaches P>0.8 and R>0.8 together.

### Step 2 — Clause-split multi-issue questions before embedding (fixes Family 1, 18 FN)

**Dilution evidence:** H5 custody 0.1098 although it contains verbatim "I want my daughter to stay with me" (already in the phrasebook); H13 maintenance 0.1031 although it contains "gives no money for my son's school fees" (phrasebook has the daughter version); H10 maintenance 0.1467 although it contains "he gives no money for me and my child"; K0 maintenance 0.0773 (10 GT sections, 4 issues); H14 all 7 issues ≤0.2542 (7 GT sections, 3 issues). Single-issue questions score high (H6 maintenance 0.898, H9 0.7931, H2 custody 0.852, H5 violence 0.8343). Several "missing" phrases are in fact already in the phrasebook yet still scored low (H5 custody, H6 residence) — that is dilution, not a phrase gap.

**Exact splitting rule (deterministic, no model call):**
1. Keep the full-question pass as a fallback/baseline (record it; do not delete it).
2. Split into clauses: first on sentence boundaries `[.!?;]\s+`; then within each sentence on `,\s+and\s+` and on `\s+and\s+` **only when followed by** `I|my|he|they|my husband|my son|my daughter` (so "gold and cash" and "money and my child" do not split, but "…and I want my daughter…" does). Also split on `\s+but\s+` when followed by `I|my` ("but I have not filed any case yet" stays attached to its money clause — do **not** split it off alone).
3. Never split inside a negation: "do not want a divorce", "do not have salary slips", "have not filed any case yet" each stay whole inside their clause.
4. Drop clauses with <3 words after stripping (e.g. stray "and").

Worked splits: K0 → ["My husband left us two years ago and gives no money", "I earn forty thousand a month, it is not enough for me and my eight year old daughter", "My gold … is with my husband's family and they will not return it", "They are throwing me out of the house which is in my husband's name", "Who will get my daughter", "how do I get my gold back", "which court do I go to?"]; H5 → ["I want a divorce from my husband", "He beats me", "I need money every month", "I want my daughter to stay with me"]; H13 → ["He beats me", "throws me out of the house", "gives no money for my son's school fees"]; H14 → ["My divorce case is already going on in the Family Court", "I want my son to stay with me", "money for his school fees while the case goes on"]; H11 → single clause (kept whole, negation intact); H4 → ["They changed the lock and I cannot enter my house", "The house is in my husband's name"].

**Merge rule:** per issue, score = **max over clauses** (never mean — mean re-introduces dilution). Fire the issue iff max-clause score ≥ its per-issue threshold (Step 1). Record `fired_clause[issue]` = the argmax clause text, for audit. **Sub-choices:** run the graph sub-choice `choice` predict on the argmax clause as the body (not the full question), falling back to the full question if the clause has <5 words. Stage 2 facts stay as annotated in the test set. **Guardrails:** single-clause questions (H3, H7, H9, H12) are unchanged by construction (max = full score); H12 (out-of-scope, GT empty) must stay empty — report it as a control in every run.

**What to measure to prove it works:** per-question, per-issue full-score vs max-clause score; H5 custody, H13 maintenance, H10 maintenance, K0 maintenance, H14 maintenance/custody/divorce must rise; H2 residence must **not** rise (single clause, no house mention); exact/mean-recall/micro-recall vs baseline 5/16 / 0.492 / 0.368, with micro-precision not below 0.875.

### Step 3 — Wire layman phrases in as auxiliary Laya prompts (fixes Family 2, 14 FN)

Each phrase becomes an auxiliary `noul` prompt per issue — instruction: `Does this question say "<verbatim phrase>" or mean the same thing?` — issue score = max(main prompt, aux prompts). **Adding text to the v2 JSON phrasebook alone does nothing live** (Cell 7 never reads it).

| Verbatim phrase (copied from `raw_live_runs[].question`) | Source | Maps to issue → sections | Note |
|---|---|---|---|
| "They changed the lock and I cannot enter my house" | H4 | residence → PWDVA 17/18/19 | Phrasebook has only hypothetical "can they change the lock and keep me out" — H4 is completed eviction, past tense. Single biggest residence gap (0.1267). |
| "I need money while my case is going on, but I have not filed any case yet" | H11 (full question) | maintenance → **BNSS 144 / PWDVA 20 only, explicitly NOT HMA 24** | Phrasebook's "I need support while my case is going on" maps to HMA 24/BNSS 144 — that mapping is wrong for H11 (no proceeding pending; Stage 2 would drop HMA 24 anyway, but the phrase must not route there). Negation ("not filed") is the whole point. |
| "I need maintenance but I do not have my husband's salary slips and I do not know what he earns" | H8 (full question) | maintenance → BNSS 144 / PWDVA 20 | "I do not have my husband's salary slips" exists in the phrasebook's documents/court section but **not** under maintenance, and the notebook never reads the phrasebook — live score 0.1746. Add as maintenance aux prompt; guardrail: absence of slips must never block the claim. |
| "gives no money for my son's school fees" | H13 clause | maintenance → BNSS 144 / PWDVA 20 | Phrasebook has only the daughter version. Son variant missing. |
| "money for his school fees while the case goes on" | H14 clause | maintenance → BNSS 144 / PWDVA 20 (+ HMA 24 only if proceeding pending — H14 yes) | Same school-fees gap, in a pending-case context. |
| "he gives no money for me and my child" | H10 clause | maintenance → BNSS 144 / PWDVA 20 | Near-duplicate of phrasebook "my husband is not giving me money" yet scored 0.1467 full-question — clause-split (Step 2) is the fix here, phrase is the aux-prompt backup. |
| "My husband has not given me any money for three months" | H1 clause | maintenance → BNSS 144 / PWDVA 20 | Duration ("three months") + "two small children" + "no case filed anywhere" — the no-case fact must route to BNSS 144/PWDVA 20, not HMA 24. |
| "I want my son to stay with me" | H14 clause | custody → GWA 1890 / HMGA s.6 / WELFARE (+ HMA 26 if proceeding pending — H14 yes) | Phrasebook has only the daughter version. |
| "throws me out of the house" | H13 clause | residence → PWDVA 17/18/19 | Phrasebook has present-continuous "they are throwing me out of the house" only. |
| "My divorce case is already going on in the Family Court" | H14 clause | divorce-pending → HMA 13 (already filed) + HMA 24/26 via Stage 2 | **No phrasebook divorce phrase covers a case already pending** — all 18 are "I want a divorce" (future). This is why H14 divorce scored 0.1395. |
| "I want my daughter to stay with me" | H5 clause | custody → GWA / HMGA / WELFARE | Already in phrasebook verbatim — add as aux prompt anyway to prove the gap is dilution (Step 2), not phrase coverage; if clause-split alone lifts H5 custody from 0.1098, this aux prompt is redundant. |
| "to stay in the house with my daughter" | H6 clause | residence → PWDVA 17/19 | Near-identical to phrasebook "I want to stay in the same house with my daughter" yet scored 0.2173 — again dilution, not coverage. |

No stridhan/violence/birth phrases to add (stridhan 4/4, violence 2/2, birth 1/1 at t=0.50).

### Step 4 — Fix H4 / H8 / H11 / H14 without breaking H2 precision (combined levers)

**Diagnosis of H2 (the precision trap):** H2 is custody-only — "Who will get my six year old son? My husband says as the father he will take him away from me." — yet residence scored **0.8247**, higher than any true residence positive (max 0.4212 H13), producing all 3 live FP. Cause is in the Cell 7 residence prompt itself: "…or about protection from threats or violence at home?" — "he will take him away" reads as a threat, so residence fires. Violence has its own prompt and Stage 2 already adds PWDVA 18 when violence fires alone, so the residence prompt does not need the violence clause at all.

**Combined fix (all three levers together — no single lever suffices):**
1. Per-issue thresholds (Step 1): maintenance ~0.10 (catches H8 0.1746, H11 0.1432, H14 0.2542, H1 0.4795); residence ~0.13–0.15 (catches H4 0.1267 only at the low end — hence levers 2–3 must lift H4 first); divorce-pending ~0.10–0.15 (catches H14 0.1395). Stridhan/violence/birth stay at 0.50.
2. Clause-split (Step 2): H14's "money for his school fees…" and "I want my son to stay with me" clauses score alone; H4's lock clause scores alone; H13's school-fees clause scores alone. H2 is a single clause with no house/home/shared-household mention, so its residence score should **fall** under the split.
3. Phrase aux prompts (Step 3) for the lock (H4), salary-slips (H8), not-filed-yet (H11), pending-case + son-custody (H14).
4. **Residence prompt A/B test:** R0 = current prompt (with "…or about protection from threats or violence at home?"); R1 = residence-only: "Does this question ask about staying in, or being thrown out of, the shared house or home?" Run both; R1 is expected to cut H2 residence sharply while H4/H6/H13/K0 (all mention house/home) hold. If R1 also cuts a true positive, keep R0 and rely on levers 1–3 instead — decide from the numbers, not by assumption.

**Proof precision did not regress (report all of these per run):** H2 residence prob before/after (must fall below its threshold; baseline 0.8247); H2 predicted sections (must lose PWDVA 17/18/19, keep GWA/HMGA/WELFARE); total section FP (baseline 3 — must stay ≤3, target 0); micro-precision (baseline 0.875 — must not fall); exact match (baseline 5/16 — must not fall); H12 stays empty; single-issue controls H3/H7/H9/H15 stay exact. If any of these regress, that run is rejected even if recall rises.

## 3. Stage 2 / court / escalate fixes (Lane 3)

### 3.1 HMA 25 gate — move the decree check before candidate generation

**Exact rule:** `hma-25` may enter the candidate set only if `facts['decree'] is True` (decree being passed or already passed — v2 `hma-25` prerequisites[0]). The check keys on **decree, not on divorce_asked**: H5 had divorce asked but no decree and still picked HMA 25; H9 had neither divorce nor decree and picked it. The model conflates "divorce asked / money asked" with "decree".

**Two-layer fix, both in Cell 7:**
- **Layer A (preferred, at generation time) — filter the option list before it is offered to Laya.** In the sub-payload construction loop (where `sub_payload[node_id]` is built from `NODES[node_id]['options']`), drop the option *"permanent alimony at/after an HMA decree"* from `maintenance:maintenance-root` when `facts['decree'] is False`. The choice question itself presupposes a decree; offering it invites the forbidden pick. Record each filtered option in a new per-question list `gated_out` (e.g. `["hma-25: option 'permanent alimony…' removed, decree=false"]`).
- **Layer B (defence in depth, in `stage2()`) — never add, don't add-then-drop.** Replace `kept.add('hma-25')` with: add only if `facts['decree']`; otherwise append to `gated_out` (`("hma-25", "gated before generation: no decree")`) and do **not** put it in `dropped[]` (it was never a candidate). Delete the existing `if not facts['decree'] and 'hma-25' in kept` recheck block — it becomes dead code, and keeping it would preserve the propose-then-drop shape.
- **Graph-side fix (v2 JSON, not the notebook):** the Stage 1 phrasebook itself seeds this error — maintenance phrase *"how much money can I get every month"* lists `section_candidates: [BNSS 144, PWDVA 20, HMA 25]` unconditionally (H9's exact question). Make HMA 25 in that phrase conditional on decree. Notebook-only fixing leaves the graph still advertising the forbidden candidate.

**Measurement caveat — read this first:** the existing `forbidden_before_recheck` metric becomes 0-by-construction after this fix, exactly as `forbidden_after_recheck` is 0-by-construction today. Cell 8 computes it from `candidates_before_stage2`, and Cell 7 computes `candidates_before_stage2` *after* `stage2()` as `kept ∪ {dropped ∩ SECTION_IDS}` — a reconstruction, not the true pre-Stage-2 list. So: add a new recorded field per question in Cell 7: `candidates_before_gate` (what Stage 1 + sub-choices would have proposed with no gates) and `gated_out` (what the gates blocked). Add a new Cell 8 metric `forbidden_proposed_before_gate` (forbidden sections in `candidates_before_gate`) and `gated_out_total`. **Pass criteria on re-running the same 16 in Colab:** `forbidden_proposed_before_gate == 0` (was 2: H5, H9), `gated_out_total == 0` option-picks on the fixed run (the option is absent, so nothing can be picked), and `kept_ids` for H5/H9 **byte-identical** to the 2026-11-26 run (H5 `[bnss-144, hma-13, pwdva-18, pwdva-20]`, H9 `[bnss-144, pwdva-20]`). A shadow unit test must also prove the gate works: forced sub-choice *"permanent alimony at/after an HMA decree"* with `decree=false` → `hma-25` not in kept, entry present in `gated_out`. **Expected score impact: none on exact match.** Gating changes nothing kept (HMA 25 was dropped anyway). Exact stays 5/16; this lane fixes forbidden-proposal and auditability, not recall.

### 3.2 Every other Stage 2 rule with the same "propose then drop" shape

| Rule | Current Cell 7 shape | Live status | Fix (same pattern: gate before generation) |
|---|---|---|---|
| **HMA 24 interim** | `stage2()` adds `hma-24` if maintenance-root contains *"interim maintenance during a pending HMA proceeding"*, then drops if `not proceeding_pending` | **Never fired live** (no question combined maintenance-firing + interim choice; H11 maintenance 0.1432 didn't fire, H14 nothing fired) — latent, untested | Filter the *"interim maintenance during a pending HMA proceeding"* option out of `maintenance:maintenance-root` when `facts['proceeding_pending'] is False`; Layer-B guard in `stage2()`; record in `gated_out`. Adjacent defect, same node: option *"full maintenance picture (all routes together)"* matches **neither** substring check in `stage2()`, so it silently yields only BNSS 144 + PWDVA 20 — under-generation, not propose-then-drop; define its mapping explicitly or remove the option. |
| **Divorce gate, HMA 13/13B** | `stage2()` adds `hma-13` only if divorce fired AND `facts['divorce_asked']` AND gate contains *"open gate"*; recheck then drops 13/13B if not asked | Recheck drop is **unreachable** as written (add already requires `divorce_asked`); the live risk is the reverse — the Laya gate choice is offered unconditionally and can contradict `facts` | Filter `procedure:divorce-gate` options by `facts`: when `divorce_asked` is False, offer only *"No divorce asked → gate closed"* and *"Ambiguous → escalate"*; offer *"open gate"* only when True. HMA 13B is never added anywhere (Cell 7 comment: no question states mutual consent) — if ever added it needs a new `facts` field `mutual_consent` (no such field exists today); gate it on that field, do not infer it. |
| **HMA 26 custody route** | Inverted defect: `stage2()` adds `hma-26` only if `proceeding_pending`, so its recheck drop is **dead code**; meanwhile the custody sub-choice is **ignored entirely** — H2 *chose* option A *"Custody inside a matrimonial proceeding (HMA s.26)"* with no proceeding pending, and the choice left no trace in `dropped[]` (propose-then-ignore, worse than propose-then-drop) | Live on H2 (choice A taken, silently discarded; kept GWA/HMGA/WELFARE was correct by the facts path, not by the choice) | Gate the options: when `proceeding_pending` is False, remove option A from `custody:custody_sub_issue_choice` (offer only B/C/D); when True, keep A **and make `stage2()` honour it** — add `hma-26` as the primary route with GWA 1890 as fallback only, per the v2 custody-set rule ("exactly one of HMA 26 / GWA 1890 is the primary"). Record a `gated_out` entry if A would have been picked. |
| **Residence PWDVA 17/18/19/20** | No gate at all — `stage2()` builds the set from two free Laya sub-choices by substring match, with no fact check (shared household? eviction? violence?). The only residence drop path (`'residence sections'` pseudo-drop when the sub-choice yields no set) never fired live | **Live failure: H2** (§1) — residence fired at 0.8247 on a custody-only question | Pre-generation fact gate: residence sub-choices are offered only if the question states eviction/lockout/threat/violence/shared-household facts. Requires a new Cell 6 `facts` field (e.g. `eviction_or_threat`: H2=false, H4=true, H13=true, K0=true). Upstream Stage 1 cause also in scope: the residence issue prompt itself conflates residence with violence (*"…or about protection from threats or violence at home?"*). |
| **BNS 316 demand** | **Do NOT gate.** Deliberately propose-and-escalate, not propose-then-drop: v2 stridhan-set rule says BNS 316 is *not* dropped when no demand was made — demand-first fallback (H3, H10 kept BNS 316 with `demand_made=false` + got the demand-first escalation, correctly per graph; BNS 316 prereq: demand made *or* refusal evident from conduct, e.g. sale of gold — H15) | Correct as-is | Leave; only ensure the demand-first escalation is typed (§3.4) rather than mixed into the quantum boilerplate. |
| **HMA 27 proceeding prereq** | **Do NOT gate — unresolved contradiction.** v2 `hma-27` prereq requires "a matrimonial proceeding pending or being filed", yet GT includes HMA 27 with no proceeding on H3/H10/H15 and `stage2()` adds it unconditionally on stridhan firing | Gating it would break 3 exact matches | **Coordinator decision needed first:** either the prereq is wrong (the "alternatively… pressed as part of the family-court case" clause) or the GT is wrong. No pre-generation gate until that is settled. |
| **Prose-level guardrails (Rajnesh for Stridhan, Satish for custody, "tenancy rights")** | Not section-level at all; Cell 8 reports them as NOT MEASURED (no answer prose is generated in this test) | Unmeasurable here | No Stage 2 section gate can fix these; they need a prose-generation gate (§4). Do not claim progress on them from section scores. |

### 3.3 Court derivation fix

**Current (Cell 7 `court_for(kept_ids)`):** a pure function of kept sections — HMA 24/25/26/27/13/13B → Family Court; GWA/HMGA/WELFARE → Family Court; BNSS 144 / PWDVA 17–20 / BNS 316 → Magistrate; `kept == {births-deaths-act-1969}` → Registrar. No other input, no fallback: empty kept → `[]`. This mapping itself is correct per v2 guardrail `g-court` (one nuance: v2 says BNS 316 is the "criminal complaint / FIR route" while the code maps it to Magistrate — keep the mapping, note the nuance).

**Why it fails, by mechanism:**
- *Empty kept → silent `[]`* (H1/H4/H8/H11/H14): the system states no court at all, which is worse than stating the wrong court — the user asked "which court do I go to" and gets nothing.
- *Spurious kept → wrong court* (H2): Magistrate enters via PWDVA 17/18/19 that should never have fired. No court-level repair is possible without the residence fact gate (§3.2) — `court_for` cannot know the residence sections are spurious from `kept` alone.
- *Right court, wrong reason* (K0, H5, H13): court is correct while whole issues are missing. The 10/16 court score therefore masks recall failure.

**Exact replacement — `court_for(kept, fired, probs, facts, in_scope)` with a fallback hierarchy:**
1. **Kept non-empty:** `court_for(kept)` as now. No change.
2. **Kept empty and in-scope:** do **not** guess a court from sub-threshold probs and do **not** emit `[]`. Emit `court: ["ESCALATE — no section kept, court cannot be derived"]` plus the top-2 candidate issues with their probs as the escalation payload, and set the typed escalate flag (§3.4). Rationale, verified on this set: no prob-based fallback recovers the right court — H1's argmax is stridhan (0.4948) but GT is maintenance (0.4795), so argmax gives Family+Magistrate vs expected Magistrate; any ≥0.15 band includes stridhan/divorce and over-generates the same way; H14's top (maintenance 0.2542) is below any defensible dominance threshold. On all 5 empty questions the honest output is escalation, not a provisional court. A provisional court may be emitted only if a single issue dominates (top prob ≥ 0.40 **and** margin over second ≥ 0.15) — that condition holds for **none** of the 5, so on this set the fallback is escalation-only. Say so in the report; do not tune thresholds to force a court out of these numbers.
3. **Kept empty and out-of-scope:** court `[]`, escalate False — H12 stays correct. This needs a new 8th Stage 1 `noul` question in Cell 7 `ISSUES` (e.g. *"Does this question concern a Hindu matrimonial / domestic-relationship family-law matter?"*) plus an `in_scope` annotation in Cell 6 `facts`, because prob mass cannot separate H4 (in-scope, max 0.1279) from H12 (out-of-scope, max 0.1218).
4. **Spurious-fire guard (H2):** once the residence fact gate exists, court follows automatically (H2 kept becomes GWA/HMGA/WELFARE → Family Court only → court 11/16). Without the gate, add a court-level consistency flag only: if every section supporting a court came from a single fired issue whose required fact is absent, mark that court provisional and escalate — implementable only after the new `facts` fields exist.
5. **Diagnostics (Cell 8):** add `court_from_kept_covers_gt_court_via_gt_sections` — True only when the live court is right *and* at least one kept GT section supports each expected court. K0/H5/H13 would read False on this stricter metric, stopping the court score from masking recall failure.
6. **Edge fixes in `court_for`:** the Registrar branch uses equality (`kept == {births-deaths-act-1969}`), so Registrar silently disappears if birth-certificate ever co-fires with anything — change to membership (`'births-deaths-act-1969' in kept`).

**Expected effect:** court stays 10/16 from the HMA 25 gate alone (that gate changes nothing kept); court becomes 11/16 only if the residence fact gate is implemented (H2 fixed). The empty-5 fallback converts 5 court errors into 5 correct escalations instead — court still wrong, escalates fixed (§3.4).

### 3.4 Escalate logic

**Current (Cell 7 + Cell 8):** `stage2()` appends the two escalation strings *only* `if kept:` (non-empty), and Cell 8 scores `esc_live = bool(r['escalations'])`. So "escalates" literally means "did anything survive Stage 2" — not "did the system recognise something needs a human/fact". Consequences, all verified in the JSON:
- The 5 escalate errors are exactly the empty 5 (H1/H4/H8/H11/H14): False vs expected True — same root cause as the court `[]`, one mechanism, two scores.
- H12's correct False is right by the same accident (empty → no escalations).
- H7 (birth certificate) gets the quantum/income escalation text — boolean correct (expected True) but **content wrong**: a birth-certificate question has no maintenance quantum. The same unconditional boilerplate ("husband's income / school fees unknown") is attached to stridhan-only questions (H3/H10/H15) where no maintenance was asked. The boolean hides content errors.

**Exact replacement — escalate as a per-need decision, with typed escalations:**
- Split `escalations` (list of strings) into typed entries `{kind, text}` with kinds: `quantum`, `court`, `demand`, `fact`. Cell 8 scores `escalates_live` from the typed `quantum`/`court` flag, not from `bool(escalations)`.
- **Quantum — escalate iff** a maintenance section is kept, or maintenance fired, or maintenance is the top near-miss issue, **and** husband's income is unknown. Requires new Cell 6 `facts` fields (`income_known`, `school_fee_known`, `husband_location_known` — all unknown/False on this set; currently income-unknown is assumed, never represented). **Never state an amount.** Text (keep verbatim, but attach only to maintenance questions): *"Quantum: husband's income / school fees unknown — escalate the amount, never invent it"* + *"Ask husband's income (estimate/range), school-fee amount, where husband lives now; never demand salary slips"* (guardrail `g-salary-slips` — the current text already complies; keep it, stop attaching it to non-maintenance questions).
- **Court — escalate** (not `[]`) when kept is empty and in-scope (§3.3 rule 2).
- **Demand — escalate** when Stridhan kept and `demand_made is False` (already implemented; keep, typed as `demand`).
- **Fact — ask once, then re-run recheck** (v2 pipeline step 8): the income/school-fee/location asks are questions to the user, after which the recheck re-runs; today they are static appended text. Make them conditional on the fact actually being unknown.
- **H8 is the key test:** *"I need maintenance but I do not have my husband's salary slips and I do not know what he earns"* — correct behaviour is BNSS 144/PWDVA 20 + quantum escalation with the ask-income text, explicitly not demanding slips. Today H8 fires nothing (maintenance 0.1746) and gets no escalation at all — the user said the exact thing the guardrail covers and the system went silent. The empty-fallback (§3.3 rule 2) is what saves H8, not a threshold change.
- **H7 ground-truth ambiguity — flag for coordinator, do not paper over:** Cell 6 sets H7 `escalate_expected: true`, but the question is fully answerable (Registrar, Registration of Births and Deaths Act 1969) with no missing fact. Either H7's expected value should be False, or the escalation reason must be named (e.g. "escalate: confirm hospital/registration procedure"). With typed escalations, H7's quantum flag would be False — resolve the expectation before re-scoring, or H7 becomes a false regression.
- **Expected effect:** escalates 11/16 → **16/16** on this set if H7's reason is resolved as above (empty 5 become True via the court/quantum fallback, H12 stays False, H7 True on a named reason); **15/16** if H7 is left unresolved. Exact match unchanged (5/16).

### 3.5 Per-question court/escalate error table

Court wrong 6/16 (H1, H2, H4, H8, H11, H14); escalate wrong 5/16 (same minus H2).

| ID | Court live → expected | Escalates live → expected | Upstream cause |
|---|---|---|---|
| H1 | `[]` → `[Magistrate]` ✗ | False → True ✗ | Stage 1 under-fire: maintenance 0.4795, stridhan 0.4948 — both just under 0.50. Nothing kept → `court_for([])=[]` and `if kept:` false → no escalations. One mechanism, two scores. |
| H2 | `[Family Court, Magistrate]` → `[Family Court]` ✗ | True → True ✓ | Spurious residence fire (0.8247) on custody-only question; residence sub-choices added PWDVA 17/18/19 → Magistrate. Fix is the residence fact gate (§3.2), not the fallback. Custody sub-choice A (HMA s.26 route) was chosen with no proceeding pending and silently ignored by `stage2()`. |
| H4 | `[]` → `[Magistrate]` ✗ | False → True ✗ | Stage 1 under-fire: residence top prob only 0.1267; violence 0.1279. Indistinguishable from H12 by prob mass alone (max 0.1279 vs 0.1218) — needs the `in_scope` question (§3.3 rule 3). |
| H8 | `[]` → `[Magistrate]` ✗ | False → True ✗ | Stage 1 under-fire: maintenance 0.1746. Worst instance: the question states the exact salary-slip/income-unknown facts the guardrail covers, and the system went silent instead of escalating quantum. |
| H11 | `[]` → `[Magistrate]` ✗ | False → True ✗ | Stage 1 under-fire: maintenance 0.1432. The HMA 24 interim-vs-BNSS 144 distinction never gets reached because maintenance never fires. |
| H14 | `[]` → `[Family Court, Magistrate]` ✗ | False → True ✗ | Stage 1 under-fire despite the richest facts (`proceeding_pending=true`, `divorce_asked=true`): maintenance 0.2542, custody 0.1321, divorce 0.1395. The HMA 24 and HMA 26 routes the question exists to test never fire. |
| H5 | ✓ (right, wrong reason) | ✓ | Custody missed entirely (0.1098), residence missed (0.4882); court right only via HMA 13 + BNSS 144/PWDVA 18/20. HMA 25 proposed then dropped (forbidden-before = 1 of the 2). Court score masks the custody miss. |
| H9 | ✓ | ✓ | Exact-true *despite* the forbidden HMA 25 proposal (dropped by Stage 2). The gate fix (§3.1) changes nothing kept here. |
| K0 | ✓ (right, wrong reason) | ✓ | Only stridhan fired (0.9064); maintenance 0.0773, custody 0.222, residence 0.265 missed; court right via HMA 27 → Family + BNS 316 → Magistrate. |
| H13 | ✓ (right, wrong reason) | ✓ | Kept only PWDVA 18 (violence 0.8892); residence 0.4212 and maintenance 0.1031 missed, GT PWDVA 17/19/20 + BNSS 144 all lost (recall 0.2) while court/escalate both read correct. |
| H7 | ✓ | ✓ (boolean only) | Escalation *content* wrong: quantum/income text attached to a birth-certificate question. See H7 ambiguity in §3.4. |
| H12 | ✓ | ✓ | Out-of-scope, correct by empty coincidence. Must stay untouched by any empty-fallback — hence the `in_scope` gate. |
| H3, H6, H10, H15 | All ✓ | All ✓ | Correct; H3/H10 additionally carry the correct demand-first Stridhan escalation. |

## 4. Test expansion + prose + Kannada + multi-turn + latency (Lane 4)

### 4.1 Fresh held-out test set — design (size 20, F1–F20)

20, not 16: large enough that one lucky/unlucky question moves exact-match by only 5 points, small enough to run live in one Colab session (~4 min at current latency). It is a **final gate only** — see the hard rule below.

Composition by issue (primary issue; sums to 20):

| Primary issue | n | What must be in the slots |
|---|---|---|
| Maintenance | 4 | 1 plain single-issue; 1 quantum-only ("how much", income unknown); 1 interim-money; 1 maintenance + school fees with husband's whereabouts unknown |
| Custody | 3 | 1 no-proceeding (GWA route); 1 child **under 5** (HMGA s.6 mother-as-natural-guardian — never tested; all 16 use ages 6–8); 1 visitation-only (no custody claim — tests the unmapped-visitation rule) |
| Stridhan | 3 | 1 demand-made + refused; 1 **sold/misappropriated** variant distinct from H15; 1 **no proof** (no bills/photos — tests whether the system still classifies vs escalates proof) |
| Residence | 2 | 1 lockout/eviction (paraphrase, not H4 wording); 1 alternate-accommodation / rent-money instead (PWDVA 20 via rent — tests the s.20 residence link) |
| Violence / protection | 2 | 1 violence-only, no residence/maintenance claim; 1 threats/intimidation after separation |
| Divorce | 2 | 1 contested (husband will not agree → HMA 13 only); 1 **mutual consent, both agree → HMA 13B** (first-ever 13B GT; the 13-vs-13B distinction is untested) |
| Birth certificate | 2 | 1 fresh English paraphrase (not H7 wording); 1 birth certificate **bundled inside a multi-issue question** (tests it is not dropped when other issues fire) |
| Out-of-scope / escalate | 2 | 1 new out-of-scope domain (not ancestral-house — H12's domain); 1 **dowry demand / second marriage** (both on the v2 unmapped list: must escalate to a human lawyer, must not invent a section id) |

Composition by difficulty (overlapping tags, minimum counts): single-issue 8; multi-issue (≥3 issues) 5, incl. 1 five-issue question comparable to K0; missing facts (income unknown / no salary slips / no proof / husband whereabouts unknown) 5; no case filed anywhere 5; case pending (HMA proceeding on) 2; **decree already passed 1 — HMA 25 must keep, the keep-branch has never been exercised in any live or walk run; the single most important new slot**; divorce NOT asked (explicit trap) 3, incl. 1 "confused / undecided about divorce" (escalate, don't fire); negation / "I do NOT want…" 2; judicial separation vs divorce 1 (ambiguity case AMB-8: living apart with a court order, no divorce — HMA 13/13B must not fire).

**Hard rule — final gate only:**
1. The set is **sealed**: question texts + GT + facts + court + escalation expectations are written to one frozen JSON file, checksummed (SHA-256 recorded in the run report), **before** any live run. No edits after the first live inference on any F-question.
2. It must **NOT be used for threshold tuning or phrase additions**. Concretely forbidden: lowering any Stage-1 threshold because H1 (0.4795) / H8 / H11 / H14 under-fired; adding any phrasebook phrase whose wording comes from an F-question; adding any Stage-2 rule justified only by an F-question outcome.
3. If a GT error is found after running, it is reported as a **separate sensitivity re-score** (original GT vs corrected GT, both numbers shown); the headline number never changes silently.
4. Report dev-16 and fresh-20 **side by side, always** — never replace the 5/16 with the fresh number.

**How ground truth is fixed BEFORE running, and by whom/what:** authority is the GT rules in §3 of `backtest-laya-vs-llama8b.md` (HMA 24 only with proceeding pending; HMA 25 only at/after decree; HMA 26 only inside a pending HMA proceeding else GWA 1890; HMA 13/13B only if divorce asked; BNS 316 kept for Stridhan even with no demand yet, with a written-demand escalation; residence = PWDVA 17+18+19 as a set; PWDVA 20 only when money/rent is in play) plus the v2 guardrails. No new GT rule may be invented for the fresh set; any case the rules don't cover is marked **escalate / out-of-scope**, not guessed. Who: one drafter writes question + GT + facts + expected court + expected escalations; a **second, independent human rater** (legally literate, not Laya, not either second-opinion model as sole rater) checks each GT set against the rules. Disagreements are resolved by a **documented judgement call** in the file (same convention as the H14 HMA-13 call), recorded before running. What is frozen per question: question text, GT section set (exact ids), facts flags (`divorce_asked`, `proceeding_pending`, `decree`, `demand_made`, `violence` — same schema as the Colab JSON), expected court set, expected escalation(s), difficulty tags. The rater's sign-off and the file hash are part of the frozen record. **No-overlap check before freezing:** no F-question may share a sentence (≥8-word overlap) with any K0/H-question or any phrasebook phrase; checked mechanically, overlap report filed with the frozen set.

Known graph gaps the fresh set must probe: Stage-2 rechecks exist for only 5 sections (no recheck for HMA 13/13B, PWDVA 17–20, BNS 316, GWA/HMGA); HMA 25 was **dropped in all 16** (no decree-passed case exists, so the keep-branch is untested); HMA 13B (mutual consent) never appears in any GT set.

### 4.2 Prose-answer test design

**Premise to state honestly:** Laya 421M is a classification/choice model — it picks sections, it does not write prose. Prose must therefore come from a **frozen template renderer** (section set + court + escalations + guardrails → layman answer), not free generation. That makes the prose test a test of the **template + graph output**, and a forbidden mapping in prose is a template/graph bug, not a model hallucination — which is exactly why it is measurable and fixable. The template itself must be frozen before the prose run, same sealing rule as §4.1.

**Method:** for each of the 20 fresh questions (plus K0 re-run for comparability), render one full answer from the live system's actual output (live section set, live court, live escalations — **not** the GT set). Score the rendered prose, not the section list. If the live section set is empty (the 5/16 failure mode), the prose must say so / escalate — an empty answer that invents sections to fill the gap is a fail.

**Pass/fail criteria per forbidden item (each binary per question: present = FAIL that question):**

| # | Forbidden prose mapping | Exact FAIL criterion (prose contains…) | Check |
|---|---|---|---|
| P1 | Rajnesh v. Neha cited for Stridhan return | Case name "Rajnesh" (any spelling variant) appearing in the Stridhan paragraph / as authority for gold return. Rajnesh cited **only** for maintenance quantum is a pass. | Automated regex + human confirm |
| P2 | Satish Chander Ahuja cited for custody | "Satish Chander Ahuja" / "Ahuja" appearing as authority for custody/guardianship. Cited only for shared-household/residence is a pass. | Automated + human |
| P3 | HMA 13/13B when divorce not asked | "13" or "13B" / "divorce" as a cited section in any answer whose facts say `divorce_asked=false` or undecided. Includes listing it under "options" without the gate. | Automated (facts-aware) + human |
| P4 | Residence called "tenancy rights" | The string "tenancy" anywhere in the answer. Correct label is "right to reside in the shared household". | Automated string match |
| P5 | Asking user to pick the court | Any interrogative pushing court choice to the user ("which court would you prefer / family court or magistrate? / you can choose"). Naming the graph-picked court is required, not a fail. | Human judge (automated flag on "which court" + "?") |
| P6 | Birth certificate under HMA | Birth-certificate paragraph citing HMA / "Hindu Marriage Act" as its legal basis. Correct basis: Registration of Births and Deaths Act 1969, Registrar. | Automated + human |
| P7 | Raw JSON leak | Any `{`, `}`, `"section"`, `"gt_"`, `null`/`true`/`false` literals, or bracketed id strings (`bnss-144`, `hma-27`) in user-facing prose. | Automated (deterministic — zero tolerance) |
| P8 | Invented maintenance amount | Any specific rupee figure as the maintenance entitlement ("you will get ₹X / Rs X per month") when husband's income is unknown. Stating a **range the user supplied** or "depends on income, to be decided" is a pass; any number presented as the answer's own computation is a fail. | Automated (₹/Rs + digits) + human |
| P9 | Demanding salary slips | Any imperative/obligation wording requiring salary slips ("you must provide / bring / submit your husband's salary slips", "without salary slips you cannot…"). Asking for an income **estimate/range** is required, not a fail. | Human judge (automated flag on "salary slip") |
| P10 | HMA 24 as sole maintenance section (extra, from the retest) | Maintenance paragraph citing **only** HMA 24, with no BNSS 144 / PWDVA 20, when no proceeding is pending. | Automated (facts-aware) + human |
| P11 | HMA 25 with no decree (extra; was the live pre-recheck failure) | "HMA 25" / "permanent alimony" as a live (not clearly conditional/future) remedy when `decree=false`. Labelling it explicitly "only after a decree — not available now" is a pass. | Automated (facts-aware) + human |

**Also scored per answer (completeness, not just forbidden):** (a) every live-kept section is actually explained in prose (no silent drops between classification and rendering); (b) the graph-picked court is named; (c) the expected escalation question is asked (income / school fees / whereabouts / written Stridhan demand, as applicable); (d) no section is cited that Stage 2 dropped (cross-check prose sections vs kept_ids).

**Scoring — automated first, human judge decides:** automated pre-screen (deterministic, scripted): regex/string checks for P1, P2, P4, P6, P7, P8-flag, P9-flag + facts-aware section checks for P3, P10, P11. Output per question: list of flagged items with the exact offending span quoted. Human judge rubric (blinded): two independent raters read the full prose without seeing the section scores, mark each P1–P11 pass/fail and each completeness item (a)–(d), using a one-line rubric per item (the FAIL criteria above, verbatim). Disagreements go to a third adjudication read; the adjudicated mark is final and the disagreement rate is reported. Why human, not automated-only: P5, P9 and P11 turn on wording ("must provide" vs "it helps if you can estimate"; "you could choose" vs "the court is…"), which regex cannot judge. Automated-only scoring would under-count exactly the failures the original 4/10 retest committed. Aggregate reporting: per-item fail rate across 20 (e.g. "P8: 2/20"), per-question forbidden count, and **gate: 0 questions with any P1–P11 fail** on the fresh set. One fail = gate failed, with the item named. Also report the same 11 items on K0 for comparability with the original 6 forbidden mappings.

### 4.3 Kannada live test design

**Size: 8 questions, live in Colab, scored with the identical metrics** (exact set, per-section precision/recall, court, escalates, P1–P11 prose equivalents). This is the first-ever live Kannada measurement — the 5/5 graph-walk number must not be quoted alongside it as if comparable.

Slots, drawn only from the existing 21-phrase phrasebook — no new wording invented here:

| # | Issue | Existing phrasebook slot to use |
|---|---|---|
| KN1 | Maintenance | "ನನ್ನ ಗಂಡ ನನಗೆ ಹಣ ಕೊಡುತ್ತಿಲ್ಲ" (Nanna ganda nanage hana koduttilla) |
| KN2 | Custody | "ನನ್ನ ಮಗಳನ್ನು ಯಾರು ಪಡೆಯುತ್ತಾರೆ" (Nanna magalanu yaru padeyuttare) |
| KN3 | Stridhan | "ಅವನು ನನ್ನ ಚಿನ್ನ ಮತ್ತು ಹಣ ತೆಗೆದುಕೊಂಡು ವಾಪಸ್ ಕೊಡುತ್ತಿಲ್ಲ" (Avanu nanna chinna mattu hana tegedukondu vapas koduttilla) |
| KN4 | Residence | "ಅವರು ನನ್ನನ್ನು ಮನೆಯಿಂದ ಹೊರಹಾಕುತ್ತಿದ್ದಾರೆ" (Avaru nannannu maneyinda horahakuttiddare) |
| KN5 | Violence | "ಅವನು ನನ್ನನ್ನು ಹೊಡೆಯುತ್ತಾನೆ" (Avanu nannannu hodeyuttane) |
| KN6 | Divorce | "ನನಗೆ ವಿಚ್ಛೇದನ ಬೇಕು" (Nanage vichchedana beku) |
| KN7 | Documents / court | "ನಾನು ಯಾವ ನ್ಯಾಯಾಲಯಕ್ಕೆ ಹೋಗಬೇಕು" (Nanu yava nyayalayakke hogabeku) |
| KN8 | Multi-issue | Maintenance + Stridhan combined in Kannada (two of the KN1/KN3 patterns in one question — tests co-firing in Kannada, not just single-issue) |

**Script split (deliberate):** 6 in Kannada script, **2 in Romanised Kannada** (transliteration as typed, e.g. the "Nanna ganda nanage hana koduttilla" form) — real users type Roman script, and the phrasebook's transliteration field exists precisely for this; Romanised input is untested in any run. Which 2 are Romanised is fixed at freeze time (recommend KN1-maintenance and KN3-Stridhan, the two highest-frequency issues).

**Known gap to close before freezing:** **birth certificate has no Kannada phrase at all.** KN-birth-cert is therefore NOT in the 8 — it is a separate prerequisite task: a native Kannada speaker must draft and gloss the birth-certificate question (and verify the 21 existing phrases), and only then does it enter a follow-up Kannada set. Do not machine-translate it into the test.

**Scoring specifics for Kannada:** same GT rules; forbidden items scored on their Kannada equivalents (e.g. P4 = any tenancy-rights label in Kannada; P5 = court-choice question in Kannada; P8 = invented rupee amount in either script). The two raters for prose must include a Kannada reader. Report Kannada exact/precision/recall **separately** from English — never pooled into one headline number, since the failure modes (script, transliteration, synonym map) are different.

### 4.4 Multi-turn test design

**Size: 4 conversations × 3 turns = 12 live turns.** Single-turn scoring cannot catch the failure the user actually cares about: facts that arrive late must change the answer, and facts that never arrive must never be assumed.

| Conversation | Turn 1 | Turn 2 | Turn 3 (the discriminating turn) |
|---|---|---|---|
| MT1 — Stridhan demand (C5-style) | Maintenance only, no case | Adds: gold held, **no demand made yet** | Adds: **written demand made, family refused to return** — BNS 316 must flip from conditional/escalated to live; HMA 27 stays; maintenance set unchanged |
| MT2 — Divorce decision evolves | "I want help but I am not sure about divorce" (undecided → no HMA 13/13B, escalate) | "I have decided — I want a divorce" (HMA 13 fires) | "We both agree to end it peacefully" (HMA 13B fires; contested-13 framing must not persist) |
| MT3 — Proceeding state evolves | Interim money, **no case filed** (HMA 24 must drop) | "My divorce case is now going on in Family Court" (HMA 24 keeps; HMA 26 becomes the custody route) | "The court has passed the divorce decree" (HMA 25 keeps for the first time; interim HMA 24 framing must not persist as the live route) |
| MT4 — Issue accretion | Residence only (lockout) | Adds violence (protection order PWDVA 18 must join; residence set must stay complete) | Adds maintenance + school fees, income unknown (BNSS 144 / PWDVA 20 join; quantum escalated, never invented) |

**Rules:** GT is fixed per turn in advance (12 GT sets frozen with the set in §4.1). A turn is scored against its own turn's GT, never against the final turn's GT. No retroactive rescoring: turn 1's answer is judged on turn-1 facts only. If turn 3 reveals a fact, turn 1 is not re-marked wrong — but the turn-3 answer **must** reflect all accumulated facts, and a turn-3 answer that contradicts turn 1 without acknowledging the new fact is a completeness fail. State handling must be declared before running: does the implementation pass full conversation history each turn, or an accumulated facts object? Record which one was actually used; if the implementation has no conversation state at all (each turn treated as fresh), that is reported as a finding, not silently worked around — and MT2/MT3 then become the test that proves it. Carryover errors scored separately: (a) dropped-fact errors (a turn-1 fact missing from the turn-3 section set); (b) stale-section errors (a section that was correct at turn 1 but must drop by turn 3, e.g. GWA route after a proceeding starts); (c) forbidden mappings per turn (same P1–P11). Metric: per-turn exact-match rate (x/12) plus final-turn exact-match (x/4), reported alongside the single-turn numbers, never merged into them.

### 4.5 Latency plan

**What to measure (per question, not just a total):** separate timers for (i) **model load** (cold start, once per session); (ii) **Stage 1** — number of Laya forward passes actually executed and their total time (root choice + one per fired issue; the current 7–24 s spread suggests pass count / question length drives it — prove or disprove this by logging pass count vs latency); (iii) **Stage 2** graph walk + recheck time; (iv) **template render** time; (v) **total per-question** end-to-end. Log hardware (Colab CPU vs GPU, RAM), model dtype (FP16/FP32), and whether the run was cold (first question after load) vs warm. Report **median, p90 and max** per question, not just the mean — the current mean (~11.8 s) hides a 3.3× spread (7.41–24.17 s).

**What "a fraction of a second" realistically means:** the original request ("classified in a fraction of a second") is **not met and not close**: 188 s / 16 questions ≈ 11.8 s/question on Colab CPU, slowest 24.17 s, plus 25.8 s load. That is ~12–24× over a 1-second budget and ~120× over a 0.1 s "fraction of a second". A 421M ModernBERT-class model doing ~7+ sequential choice passes per question on CPU cannot plausibly hit sub-second per question. Each pass is a full forward pass; the passes are sequential because later choices depend on earlier ones (root → per-issue). Sub-second would require a different serving setup, not a tweak.

**Honest targets:**

| Target | Value | Status |
|---|---|---|
| Warm, Colab GPU (T4) | **< 2 s / question** (median), p90 < 4 s | **The target to set and test.** Achievable plausibly via GPU + batching Stage-1 choices into one batched forward call where independent + caching the loaded model across questions. Must be measured, not assumed. |
| Warm, Colab CPU (interim) | **< 5 s / question** (median) | Acceptable interim if GPU is unavailable; still 5× over "fraction of a second" — say so. |
| Cold start (model load) | Report separately; do not fold into per-question time | Load is 25.8 s now; it is a session cost, not a per-question cost, once the model stays loaded. |
| Sub-second (< 1 s / question) | **Do not claim.** Requires ONNX/quantised serving or a distilled single-pass classifier + pre-computed graph walk — a different build, to be scoped separately if the user wants it. | Explicitly out of scope for this gate. |

**Method notes:** measure GPU vs CPU on the **same 20 fresh questions** (same Colab session type, back-to-back) so the comparison is clean. Test batching explicitly: run Stage-1 choices batched (one call, all independent issue-choices) vs sequential, and report both latencies — if batching is not implemented, report sequential as the measured number and batching as untested, not as a claimed saving. Latency is a **separate gate from accuracy**: a run can pass accuracy and fail latency or vice versa; never trade one for the other silently (e.g. do not raise thresholds to go faster).

### 4.6 Overfitting guards — what counts as overfitting, and how the fresh set catches it

**What would count as overfitting to the 16 (each is a named, checkable act):**
1. **Threshold tuning to the 16:** any Stage-1 threshold change justified by H1 (0.4795), H8 (0.1746), H11 (0.1432) or H14 (all ≤0.25) — e.g. "lower maintenance threshold to 0.14 so H8/H11 fire". Those four numbers are the fingerprint of threshold-overfitting; a threshold set from them will fire on noise in fresh data.
2. **Phrasebook additions copied from H-questions:** adding a phrase whose wording comes from an H-question (or a paraphrase of one) rather than from independent layman speech. The walk already proved this circularity: it scored 16/16 on phrasings it was built from, while phrase-level matching on the same phrases scored 3/16.
3. **Stage-2 rules written for H-specific facts:** e.g. a rule that only fires on the exact H14 fact pattern (divorce pending + school fees) rather than on the general condition (proceeding pending).
4. **GT redefinition after seeing live output:** changing a GT set because the live system predicted something else (e.g. redefining H2's residence over-fire as correct). The §4.1 rule (corrections only as a separate sensitivity re-score) blocks this.
5. **Latency/accuracy trade hidden in the numbers:** e.g. dropping low-confidence issues to raise precision on the 16 while recall on fresh multi-issue questions collapses.

**How the fresh set catches each:**

| Overfit | Fresh-set tripwire |
|---|---|
| Threshold lowered to 0.14 | Fresh single-issue questions over-fire (FP rate rises, precision falls vs dev-16); out-of-scope F-questions fire sections (H12 was the only such tripwire in the 16 — the fresh set has 2, in new domains) |
| Phrases copied from H-wording | Fresh questions use **new paraphrases** (mechanically checked for ≥8-word overlap, §4.1); copied phrases don't match, recall falls back toward the live 0.492 instead of the walk's 1.000 |
| H-specific Stage-2 rules | Fresh decree-passed / mutual-consent / under-5 / visitation slots exercise the **general** condition the rule was supposed to encode; a narrow rule misses them |
| GT redefinition | Frozen hash + two-rater sign-off before running makes silent redefinition impossible; any post-hoc change appears as a separate sensitivity number |
| Precision/recall trade hidden | Fresh set reports precision **and** recall **and** exact separately, per issue and per difficulty tag — a trade shows up as a recall collapse on multi-issue / missing-facts tags specifically |

**Detection rule (pre-registered):** compute the dev-16 live numbers and fresh-20 live numbers side by side. Flag overfitting if **either** (a) fresh exact-match is ≥3 questions below dev exact-match rate (i.e. fresh ≤2/20 if dev stays 5/16, proportionally), **or** (b) fresh mean recall is >0.15 below dev mean recall, **or** (c) fresh FP count on out-of-scope questions is >0. A flag means: stop, diagnose which of the five overfits above occurred, and report it — do not tune on the fresh set to clear the flag (that would overfit to the fresh set instead).

**Final gate on the fresh set (all must hold, reported together):** exact ≥12/20 is the *minimum progress bar*, not 10/10 (see §5 — 10/10 needs 20/20); mean recall ≥0.75 (the live 0.492 is the number that must move — precision at 0.875 micro is already adequate); **0 forbidden prose mappings (P1–P11) across all 20 prose answers**; court ≥16/20; Kannada exact ≥5/8; multi-turn final-turn exact ≥3/4; warm GPU median latency <2 s/question (CPU interim <5 s). If any gate fails, the report names the failing gate and the questions that failed it — no single blended score is quoted instead.

## 5. The 10/10 gate — exact definition (Lane 5)

Gate definition also filed separately at `laya-10-10-gate-definition.md`.

### 5.1 Gate rows — every row must pass in live Colab

| # | Gate row | Target | Baseline |
|---|---|---|---|
| G1 | Exact, current 16 (GT frozen per backtest §3) | **16/16** | 5/16 |
| G2 | Exact, fresh held-out 20 (Lane 4 set; Lane 5 originally specified 16 — reconciled to 20 in §8) | **20/20** | not run |
| G3 | Exact, Kannada 8 | **8/8** | not run |
| G4 | Mean precision, current 16 | ≥ 0.95 (1.000 if G1 passes) | 0.656 |
| G5 | Mean recall, current 16 | ≥ 0.95 (1.000 if G1 passes) | 0.492 |
| G6 | Micro P / R, current 16 | ≥ 0.95 / ≥ 0.95 | 0.875 / 0.368 |
| G7 | TP / FP / FN, current 16 (57 GT) | **57 / 0 / 0** | 21 / 3 / 36 |
| G8 | Court correct | **16/16** | 10/16 |
| G9 | Escalates correctly | **16/16** | 11/16 |
| G10 | Silent questions | **0** | 5 |
| G11 | Forbidden before Stage-2 recheck — measured as `forbidden_proposed_before_gate` after the §3.1 gate fix (old metric becomes 0-by-construction) | **0** | 2 |
| G12 | Prose forbidden mappings (P1–P11, §4.2) | **0** | NOT MEASURED |
| G13 | Model errors | **0** | 0/16 |
| G14 | Latency: mean ≤ 15 s, max ≤ 30 s, run ≤ 240 s excl. load, load ≤ 60 s | within budget | 11.77 s / 24.17 s / 188 s / 25.8 s — already inside; a **no-regression guard**, not a hurdle. The <2 s GPU target (§4.5) is a stretch goal, not part of this gate. |
| G15 | Confirmation re-run: full gate passed a **second time**, independent live Colab run, zero code changes between runs | passed twice | not run |
| G16 | Run log complete (every run numbered, dated, code version, JSON+MD filed) | complete | baseline filed |

Exact match is the binding gate (16/16 exact implies P/R 1.000 on that set, given the H12 convention). Kannada is not optional — English-only perfection is at most 9/10. The user's original "fraction of a second" aspiration is a **separate stretch goal**, not part of this gate.

### 5.2 Rating formula (frozen)

```
E=exact/16, Rm=mean recall, Pm=mean precision, C=court/16, S=escalates/16
Fb=forbidden-before-recheck count, Fp=prose-forbidden count
Rating = 10 × [0.60·E + 0.15·Rm + 0.10·Pm + 0.075·C + 0.075·S] − 0.5·Fb − 1.0·Fp
```
Clamp [0,10], round to 1 decimal. Recall outweighs precision (0.15 vs 0.10) because the measured failure is under-firing (36 FN vs 3 FP).

**Worked baseline:** 10 × [0.60×0.3125 + 0.15×0.492 + 0.10×0.656 + 0.075×0.625 + 0.075×0.6875] = 4.25, minus 0.5×2 = **3.25 → 3.3/10** — reproduces the honest ~3/10. Same 5/16 exact with Fb=0 would rate 4.3/10: the forbidden penalty costs a full point.

**Caps (lower of formula and cap is the rating):** Fp ≥ 1 → ≤ 5.0 (wrong law in prose to a vulnerable user is a hard failure); Fb ≥ 1 → ≤ 9.0; prose not measured → ≤ 9.0; fresh set not run/passed → ≤ 9.0; Kannada not run/passed → ≤ 9.0; no confirmation re-run → ≤ 9.0; ≥ 3 model errors in a run → ≤ 5.0. A formula output of 10.0 without G2/G3/G12/G15 passing is a 9.0, not a 10/10.

### 5.3 Tier table (number always comes from the formula + caps)

| Rating | Typical exact | Typical mean recall | Forbidden/prose | Meaning |
|---|---|---|---|---|
| **10** | 16/16 + fresh 20/20 + Kannada 8/8 | 1.000 | Fb 0, Fp 0 | Every question fully right, English and Kannada, seen and unseen, twice. Gate closed. |
| **9** | 14–15/16 | 0.85–0.94 | Fb 0, Fp 0 | Near-perfect; one question's section set still off. |
| **8** | 12–13/16 | 0.75–0.84 | Fp 0 | Most questions right; multi-issue still losing issues. |
| **7** | 10–11/16 | 0.65–0.74 | Fp 0 | Majority right; recall still binding. |
| **6** | 8–9/16 | 0.60–0.64 | Fp 0 | Half fully right; silent/under-fired remain. |
| **5** | 6–7/16 | 0.50–0.59 | Fp 0 | Better than generic retest (4/10) on sections, still missing whole issues. |
| **4** | 5/16, Fb 0, Fp 0 | ~0.50 | clean | Same section accuracy as baseline, no forbidden fires. |
| **3** | 4–5/16 with Fb ≥ 1 or Fp ≥ 1 | 0.45–0.54 | Fb ≥ 1 | **← BASELINE (3.3/10).** Precise when it fires, silent on 5/16, forbidden fired twice. |
| **2** | 2–3/16 | 0.30–0.44 | — | Fires on only a few questions. |
| **1** | 0–1/16 | < 0.30 | — | Barely functioning as a classifier. |
| **0** | no live run | — | — | A walk, plan, or assertion is 0, not a rating. |

### 5.4 What 10/10 does NOT mean

- Not single-run luck on 16 questions (one pass without confirmation re-run is at most 9/10).
- Not the graph-walk score (16/16 walk ≠ live 16/16).
- Not precision-only (micro P is already 0.875 while micro R is 0.368 — precise and silent is not 10/10).
- Not a rating asserted without a live Colab run (no walk, local run, or argument substitutes).
- Not English-only (without Kannada 8, ceiling is 9/10).
- Not classification-only (without measured, zero-forbidden answer prose, ceiling is 9/10).
- Not "close enough" — 15/16 is honestly 9/10; rounding it up is not permitted.
- Not a better walk, plan, or explanation — only live Colab numbers move the rating.

### 5.5 One-page gate checklist (per run)

| Metric | Target | Baseline | Run actual | Pass? |
|---|---|---|---|---|
| Exact, current 16 | 16/16 | 5/16 | | |
| Exact, fresh 20 | 20/20 | not run | | |
| Exact, Kannada 8 | 8/8 | not run | | |
| Mean precision | ≥ 0.95 | 0.656 | | |
| Mean recall | ≥ 0.95 | 0.492 | | |
| Micro precision | ≥ 0.95 | 0.875 | | |
| Micro recall | ≥ 0.95 | 0.368 | | |
| TP / FP / FN | 57 / 0 / 0 | 21 / 3 / 36 | | |
| Court correct | 16/16 | 10/16 | | |
| Escalates correct | 16/16 | 11/16 | | |
| Silent questions | 0 | 5 | | |
| Forbidden before recheck (pre-gate metric) | 0 | 2 | | |
| Prose forbidden mappings | 0 | NOT MEASURED | | |
| Model errors | 0 | 0 | | |
| Latency mean / max | ≤ 15 s / ≤ 30 s | 11.77 s / 24.17 s | | |
| Run time (excl. load) / load | ≤ 240 s / ≤ 60 s | 188 s / 25.8 s | | |
| Confirmation re-run passed | yes | not run | | |
| Run filed (JSON + MD, no., date, code version) | yes | yes | | |
| **§5.2 rating** | **10.0** | **3.3/10** | | |

### 5.6 Definitions frozen for the prose gate (currently unmeasured — this is what must be built to measure it)

Fp = number of questions with ≥ 1 prose forbidden mapping (total instances also recorded), scored by an independent rater against the 11-item list in §4.2 (Lane 4's P1–P11, which supersedes Lane 5's 9-item list — it adds P10 HMA 24-only and P11 HMA 25 with no decree). If the system produces no answer prose, Fp is NOT MEASURED and the ≤ 9.0 cap applies. Also frozen: exact = `set(pred) == set(gt)`, order-insensitive, no partial credit; H12 (empty GT + empty prediction) scores P/R 1.0 and exact True — a disclosed leniency, same convention in the fresh set's 2 out-of-scope questions; "live Colab run" = the linked notebook in Colab (CPU, PIXMELT snapshot), all cells clean, JSON + MD filed.

## 6. What NOT to do

- **Blind global drop to 0.10 (or 0.12):** issue-level FP jumps 1 → 21 (t=0.10) / 16 (t=0.12), precision 0.923 → 0.553 / 0.600. Concretely it fires H1 stridhan (0.4948 → +2 section FP), H9 stridhan (0.2546), H5 residence (0.4882 → up to +3 section FP), H6 divorce (0.384), H6 custody (0.1602), H12 custody (0.1218, breaking the out-of-scope control). It "fixes" recall by flooding.
- **Do not lower stridhan, violence, or birth_certificate** — all three are perfect at 0.50 with clean gaps; lowering only adds FP (H1 stridhan 0.4948 is the tripwire).
- **Do not lower residence alone without the R1 prompt + clause-split** — H2 (0.8247) and H5 (0.4882) sit above every true residence positive, so any residence threshold that catches H4 (0.1267) also catches both.
- **Do not add a keyword/phrase fallback** if Laya scores low — Cell 7's hard rule (no fallback; errors scored as misses) is what makes the live number honest. Phrasebook text must enter as Laya prompts (§2 Step 3), not as string matching.
- **Do not quote the offline sweep's issue-level F1 as a section score**, and do not lock any threshold from n=16 alone — every "best" above is in-sample; a fresh held-out set is required before locking.
- **Do not gate BNS 316 on demand-made** (§3.2) — it is deliberately propose-and-escalate, and H3/H10 kept it correctly with `demand_made=false`.
- **Do not gate HMA 27 on its proceeding prereq** until the coordinator settles the prereq-vs-GT contradiction (§3.2) — gating would break 3 exact matches.
- **Do not guess a court from sub-threshold probs on empty predictions** (§3.3 rule 2) — no prob-based fallback recovers the right court on this set; escalate instead.
- **Do not tune on the fresh set, ever** (§4.1, §7) — that overfits to the fresh set instead.
- **Do not change metric definitions, formula, or targets mid-tuning** (this document frozen; amending it requires the coordinator and re-passing the full gate).

## 7. Validation loop (exact sequence)

1. **Freeze before tuning.** Current-16 GT already frozen (backtest §3, incl. the two judgement calls: H14 includes HMA 13; H4 excludes PWDVA 20). Freeze GT for fresh-20 and Kannada-8, written by a rater who is **not** the tuning lane, filed with checksum/date — before any tuning run sees them.
2. **Diagnose from the live JSON, don't guess** (diagnosis in §1 above).
3. **Fix ONE thing** — one change, one hypothesis, logged with run number. Never batch multiple fixes per run.
4. **Re-run the full current 16 in live Colab** (same notebook, same GT, fresh process). Record all §5 metrics + full per-question JSON. Compute §5.2 rating, tick the checklist.
5. **If gate fails:** back to step 2, biggest failure class, one fix, re-run. Unlimited cycles, one change per cycle.
6. **Fresh held-out run only when current 16 passes** (G1, G4–G14 all pass). Run fresh 20 **once**, no changes between the current-16 pass and the fresh run.
7. **If fresh fails: DO NOT tune on it.** No adding its questions/phrasings to the phrasebook, prompts, or threshold examples; no threshold fitted to it; no GT edits. Diagnose the **underlying cause** in general terms (must be justifiable from current-16 failures or a general principle), fix the cause in the general mechanism, **re-run BOTH sets**. Fresh re-runs after a general fix are allowed and logged; a fix justifiable only by a specific fresh question's wording is overfitting and forbidden.
8. **Kannada 8.** A Kannada baseline run may happen any time to measure. Tuning *on* Kannada begins only after English current + fresh both pass. Same no-tune-on-it rules as step 7.
9. **Confirmation re-run.** After G1–G14 pass on all three sets in one run, re-run all three in a **second independent live Colab run with zero code changes**. Both runs must pass. Only then may 10/10 be claimed.
10. **Publish every run** — JSON + MD filed next to the 2026-11-26 baseline, with run date, notebook link, code version/commit, change since previous run, §5.2 rating. Unfiled runs don't count; failed runs are filed too.

**Anti-overfitting rules (forbidden once tuning starts):** (1) Never edit GT to match predictions (frozen judgement calls; disputes go to an independent rater; a GT change invalidates all prior runs on that set). (2) No fresh-set or Kannada-set wording in the system (phrasebook/prompts/examples/tests). Phrasebook additions come from general layman language only. (3) No threshold fitted to a single question (a change must improve or hold ≥ 2 questions; H1's 0.4795 alone never justifies a threshold move). (4) No per-question special cases (no question-ID branches, no if-question-contains-X rules). (5) No removing/redefining failing questions; no reporting a subset. (6) No tuning on fresh/Kannada per-question outputs beyond general-cause diagnosis. (7) Never quote the graph-walk 16/16 as a live result, at any stage. (8) No best-run cherry-picking — every run filed in sequence; rating is the latest run's, not the best's. (9) No changing metric definitions, formula, or targets mid-tuning. (10) No silent changes between the gate pass and the confirmation re-run — any change resets the confirmation requirement.

## 8. Reconciliation notes (where lanes disagreed)

- **Fresh-set size:** Lane 4 designed 20 questions; Lane 5's gate specified 16. **Adopted: 20 (F1–F20).** Lane 5's G2 is therefore 20/20, and its tier table's "fresh 16/16" reads as fresh 20/20. Lane 4's "exact ≥12/20" is a *minimum progress bar*, not the 10/10 bar.
- **Prose list:** Lane 5 defined 9 prose items; Lane 4 defined 11 (P1–P11). **Adopted: Lane 4's 11**, a superset (adds P10 HMA 24-only, P11 HMA 25 with no decree).
- **Latency:** Lane 5's gate is a no-regression guard (mean ≤15 s, max ≤30 s — already met). Lane 4's <2 s/question GPU median / <5 s CPU is the **stretch target**; sub-second is explicitly out of scope for this gate.
- **H2 mechanism:** Lane 1 and Lane 3 agree (spurious residence fire → wrong court). Lane 3 adds the correction that court/escalate failures are *not* all downstream of firing nothing — H2 is the separate spurious-fire mechanism.
- **HMA 25 metric:** Lane 3's warning is adopted — after the pre-generation gate, the old `forbidden_before_recheck` reads 0-by-construction, so the gate uses the new `forbidden_proposed_before_gate` metric (§3.1).
- **Multi-turn + Kannada baselines:** Lane 4's MT1–MT4 and KN1–KN8 designs are adopted as §4.3–4.4; Lane 5's Kannada-8 gate (G3) uses the same 8 questions.

## 9. Open decisions (need the coordinator / user before implementation)

1. **HMA 27 proceeding prereq vs GT contradiction** (§3.2): v2 `hma-27` prereq requires a matrimonial proceeding pending or being filed, yet GT includes HMA 27 with no proceeding on H3/H10/H15. Either the prereq is wrong or the GT is wrong. No gate until settled.
2. **H7 `escalate_expected: true` ambiguity** (§3.4): the birth-certificate question is fully answerable with no missing fact. Either the expected value should be False, or the escalation reason must be named. Resolve before re-scoring, or H7 becomes a false regression.
3. **Fresh-20 + Kannada-8 authorship:** both sets must be written by a non-tuning rater with GT frozen before tuning starts (§4.1, §7 step 1). Not yet commissioned.
4. **Prose-generation path does not exist yet** — until a frozen template renderer exists, the system is capped at 9.0 regardless of section scores.
5. **Native Kannada speaker prerequisite** for the birth-certificate Kannada question and verification of the 21 existing Kannada phrases (§4.3).
6. **Notebook cell changes (consolidated, for the implementer — plan only, not yet applied):**
   - Cell 5 (graph upload/verify): no code change. The v2 JSON file itself needs the phrasebook fix (§3.1: HMA 25 conditional on decree in *"how much money can I get every month"*); Cell 5's 32/46/77 assertion is unaffected.
   - Cell 6 (test set + GT): **do not touch section GT** — ground truth stays frozen. Add per-question `facts` fields: `income_known`, `school_fee_known`, `husband_location_known` (all False/unknown on this set), `mutual_consent` (False everywhere; needed before HMA 13B can ever be added), `eviction_or_threat` (H2=false, H4=true, H13=true, K0=true, others as annotated), `in_scope` (H12=false, all others true). Resolve the H7 ambiguity (item 2 above) before re-scoring. Ground-truth section sets and `court_expected` unchanged.
   - Cell 7 (Stage 1 + Stage 2) — the main change: replace the hard-coded `if p is not None and p >= 0.50:` with a `THRESHOLDS` dict (starting test vector: `{'maintenance': 0.10, 'custody': 0.15, 'stridhan': 0.50, 'residence': 0.15, 'violence': 0.50, 'divorce': 0.50, 'birth_certificate': 0.50}` plus separate `DIVORCE_PENDING_THRESHOLD = 0.12`); add `split_clauses(q)` (§2 Step 2) and `AUX_PROMPTS` (§2 Step 3 verbatim phrases as extra `noul` instructions per issue) plus a second divorce prompt `divorce_pending`: "Does this question say a divorce case is already going on / already filed in court?"; change the `ISSUES` residence instruction to the R1 residence-only wording, with R0 kept as a flag-switchable alternative (`RESIDENCE_PROMPT = 'R1'`); add an 8th `noul` issue for in-scope (§3.3 rule 3); add a `FACT_GATES` structure and filter sub-choice option lists at `sub_payload` build time (§3.1–3.2); scoring loop: run the 7 main prompts on the **full question** (baseline, kept) **and** on each clause; per issue store `stage1_full`, `stage1_clause_raw` (dict clause→prob), `stage1_clause_max`, `fired_clause`; fire iff `max(full?, clause_max)` ≥ per-issue threshold — **test both variants**: (a) clause-max only, (b) max(full, clause-max) — and report which variant each run used; aux prompts: issue score = max(main, aux) per clause; record which prompt fired; sub-choices: pass the argmax clause as `body` (fallback full question if <5 words), record `sub_body[issue]`; in `stage2()`: replace `kept.add('hma-25')` / `kept.add('hma-24')` / `kept.add('hma-13')` with gated adds (Layer B); delete the now-dead recheck drop blocks; make the custody branch honour sub-choice A when `proceeding_pending` (HMA 26 primary, GWA fallback only); define the *"full maintenance picture"* option mapping explicitly; replace `court_for(kept_ids)` with `court_for(kept, fired, probs, facts, in_scope)` (§3.3); change the Registrar branch from equality to membership; replace the unconditional `if kept: esc.append(...)` boilerplate with typed escalations (§3.4); record new per-question fields in `rec`: `candidates_before_gate`, `gated_out`, `court_provisional`, typed `escalations`; also record `stage1_full`, `stage1_clause_max`, `fired_clause`, `sub_body`.
   - New Cell 9 — offline threshold sweep (no model calls, seconds): load the baseline JSON, recompute the §2 Step 1 issue-level table and global sweep, output 2–3 candidate threshold vectors. Cannot give true section scores for newly fired issues — shortlists only.
   - New Cell 10 — live re-run harness: re-run Cell 7's loop for each shortlisted vector (2–3 vectors max, ~3 min each at the observed 188 s/run) with `THRESHOLDS` swapped in, saving each run as `live-laya-colab-results-<vector-name>.json` with the vector recorded in the file. Do **not** sweep live over a fine grid — cost and Colab time forbid it.
   - Cell 8 (scoring/saving) — extend, do not rewrite scoring: loop over each saved run file; add a per-issue TP/FP/FN table, a per-question residence-before/after line (H2 in particular), H12-empty check, and a comparison table (baseline 0.50 vs each vector: exact, mean P/R, micro P/R, FP total); add metrics `forbidden_proposed_before_gate` (from `candidates_before_gate`), `gated_out_total`, `court_correct_strict` (court right via kept GT sections only); score `escalates_live` from the typed quantum/court flag, not `bool(escalations)`; keep the old `forbidden_before_recheck` key for comparability but label it post-gate in the output MD; update the MD table with a `gated` column. Keep the "prose NOT MEASURED" note until §4.2 exists.
   - Cells 0–4: no change.

## 10. Gemini + ChatGPT consultation merge (2026-11-26 ~22:31–22:35 IST)

Both models were consulted in the browser in parallel (per the user's ~22:30 IST instruction): Gemini Neon Thinking High and ChatGPT GPT-6.2 thinking max, on the live 5/16 failure. Their answers are recorded in MEMORY.md; this section reconciles them with the five lanes above. **Nothing in the plan depends on model opinion alone — every point below is either already grounded in the live JSON or is flagged as a new experiment to run.**

**What both models agree on:**
- **NOT a threshold-only problem.** A single global threshold cannot work: the lanes' numbers already prove it — need t≤0.0773 to recover all relevant issues, t>0.8247 to suppress the H2 residence FP (0.8247). Both models independently reached the same conclusion as Lane 2's global sweep (no global t reaches P>0.8 and R>0.8 together).
- **Rank 1 is layman-phrase / representation mismatch**, then whole-question dilution (K0, H14), then the uncalibrated 0.50 cutoff (H1 0.4795/0.4948). H4 (single-issue residence 0.1267) is their proof that the phrase gap exists independently of dilution. Reconciliation with Lane 1: Lane 1 ranked dilution #1 (18 FN) vs phrase-coverage #2 (14 FN) by FN count. The two rankings are compatible — dilution explains more FN in total, but H4 proves phrase mismatch is an independent cause that dilution fixes alone cannot cure. The plan already fixes both together (Steps 2 + 3 in the same cycle), which matches the models' ordered fix.
- **Ordered fix both models agree on:** (1) clause-split + max-pool per issue, (2) multi-prototype layman expansion + hard negatives (esp. residence vs custody), (3) per-issue thresholds + gray-band escalation, never one global cutoff, (4) test Laya's native 2-option A/B choice head vs embedding cosine (`noul` biases to 'no'), (5) fine-tune LoRA only if separation still <0.08 after steps 1–3.
- **HMA 25 must be blocked pre-graph by a decree-state guard** (Gemini 4-state posture; ChatGPT: allow only if decree being_granted/granted, type HMA 9–13 incl. nullity, citing Sukhdev Singh v Sukhbir Kaur 2025). This agrees with Lane 3 §3.1 (Layer A/B gate). The Sukhdev Singh citation is **model-provided and unverified** — verify it against the source before citing it in the graph or any answer.
- **Validation: freeze the 16 as regression only; fresh blind held-out needed.** Gemini: 56 questions with gates recall ≥0.92, precision ≥0.90, exact ≥0.85, F1 ≥0.92, empty 0%, forbidden 0. ChatGPT: ablation E0–E7 + 300 functional + 300 safety, release gates ≥95% exact/precision/recall/F1, court ≥98%. Reconciliation: the plan's 10/10 gate (16/16 + 20/20 + 8/8, i.e. 100% on small sets) is stricter than both models' percentage gates on the sets it covers, so there is no conflict — but the models' larger-N validation (56, then 300+300) is adopted as **extended release validation after the 10/10 gate passes**, not as a replacement for it. A 20-question fresh set cannot prove a 95% rate; the 300-question suites can.

**New items from the models that no lane proposed (added here as experiments, not as asserted fixes):**
- **(a) Test Laya's native 2-option A/B choice head vs embedding cosine.** Hypothesis: `noul` biases toward 'no', which would explain systematically depressed scores (H8 maintenance 0.1746 despite the literal word "maintenance"). Experiment: run the same 7 issues on the same 16 questions through the native choice head and through cosine similarity, compare per-issue score distributions and separation. If the choice head separates better, switch Stage 1 to it; if not, keep cosine and record the negative result.
- **(b) Gray-band escalation.** Per-issue thresholds plus a gray band (scores between the low and high thresholds) that escalates instead of firing or dropping — i.e. a third outcome between "fire" and "silent". Ties into §3.4 typed escalations: a gray-band issue produces a `fact`/`quantum` escalation naming the uncertain issue, rather than silence. Define the band per issue from the Step 1 sweep (e.g. maintenance gray band 0.05–0.10 if the fire threshold is 0.10) and validate it on the fresh set.
- **(c) Hard negatives, esp. residence vs custody.** Add hard-negative prototype pairs to the aux-prompt set: custody-only questions that must NOT fire residence (H2 pattern: "take him away" ≠ eviction) and residence questions that must NOT fire custody. This is the targeted version of the R1 prompt A/B test (§2 Step 4).
- **(d) LoRA fine-tune, conditional only.** Only if separation is still <0.08 after steps 1–3 (clause-split, prototypes, per-issue thresholds). Not a first resort; the plan's Steps 1–4 must be measured first, and the fine-tune decision is gated on that measurement.

**What the models did not change:** the diagnosis (§1), the per-issue threshold ranges (§2 Step 1), the clause-split design (§2 Step 2), the verbatim phrases (§2 Step 3), the Stage 2/court/escalate fixes (§3), the fresh-set sealing rules (§4.1), the prose test (§4.2), the rating formula and caps (§5.2), and the validation loop (§7) all stand as written — the models' answers corroborate them rather than contradicting them.

---

*End of plan. Next action (not part of this file): coordinator/parent to merge any further Gemini/ChatGPT follow-ups, settle the open decisions in §9, commission the fresh-20 + Kannada-8 sets, then begin §7 validation loop step 3 (one fix per run).*
