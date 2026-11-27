# Laya family-law system — the 10/10 gate definition

**Lane 5 — plan only. No fix is implemented in this document.**
**Status:** gate definition, frozen 2026-11-26. The rating formula and all targets below are
frozen from this point: they may not be changed mid-tuning to make a run pass.

**System under test:** Laya 421M (classic ModernBERT checkpoint, PIXMELT snapshot) + v2
two-stage decision graph (Stage 1 layman → legal terms → section; Stage 2 recheck of all
relations inside the picked sections).

---

## 0. Frozen baseline — the only numbers any claim is measured against

Live Colab run, 2026-11-26 ~22:28 IST (CPU, 13.6 GB RAM, torch 2.14.1+cpu, laya 0.5.5,
notebook: https://colab.research.google.com/drive/1pY2WJAyN0vyEvk462prTeTswROQSLnTa).
Results filed at `~/workspace/browser_downloads/sess-2896751965/` (`live-laya-colab-results.json/.md`).
The backtest design (test set, ground truth, judgement calls) is in
`~/workspace/goals/english-family-law-chatbot-retest/files/laya-graph/backtest-laya-vs-llama8b.md`.

| Metric | Baseline (live, 2026-11-26) |
|---|---|
| Exact section-set match, current 16 (K0 + H1–H15) | **5/16** (H3, H7, H9, H12, H15) |
| Mean precision / mean recall | 0.656 / 0.492 |
| Micro precision / micro recall | 0.875 / 0.368 |
| TP / FP / FN (of 57 ground-truth sections) | **21 / 3 / 36** |
| Court correct | 10/16 (wrong/missing: H1, H2, H4, H8, H11, H14) |
| Escalates correctly | 11/16 (wrong/missing: H1, H4, H8, H11, H14) |
| Questions predicting NOTHING with non-empty GT (silent) | **5** (H1, H4, H8, H11, H14) |
| Forbidden before Stage-2 recheck | **2** (H5, H9 — both "HMA 25 with no decree") |
| Forbidden after Stage-2 recheck | 0 — **by construction** (Stage 2 drops them). Never quote this as a live result; the live error count is the before-recheck number, 2. |
| Prose forbidden mappings | **NOT MEASURED** (classification only, no answer prose generated) |
| Model errors | 0/16 |
| Latency per question | mean 11.77 s, max 24.17 s (K0), min 7.41 s (H4); full 16-question run 188 s; model load 25.8 s |
| Honest live rating (formula in §2) | **3.3/10** (down from provisional 5/10, which was given before any live run) |

**Graph-walk ceiling is NOT a baseline and NOT the gate.** The deterministic graph walk scored
16/16 exact, but it walks the graph's own rules on questions written in the graph's own
phrasings. It is a ceiling measurement of the rules, not a live result. It must never be quoted
as a live score, never be compared against live numbers, and never be used to claim progress.

**Failure anatomy (diagnostic context for the tuning lanes, not fixes):** the system is
precise when it fires (only 3 false positives) and badly under-fires (36 false negatives,
5 questions silent). The dominant failure is recall, not precision. Stage-1 probabilities on
the silent questions show why: H1 maintenance 0.4795 (just under a 0.5 threshold), H8
maintenance 0.1746, H11 maintenance 0.1432, H14 maintenance 0.2542 / divorce 0.1395,
H4 residence 0.1267. Multi-issue questions lose whole issues (K0 recall 0.20, H13 0.20,
H6 0.40, H5 0.571, H10 0.50). H2 over-fires residence (FP 3, court wrong). H5/H9 fire a
forbidden section (HMA 25, no decree) that Stage 2 then has to catch.

---

## 1. The 10/10 gate — every row must pass, in live Colab, or the claim is not 10/10

"10/10" means **all** of the following. A single failing row means the system is not 10/10,
whatever the headline formula says (§2). Exact match is the binding gate: 16/16 exact on a
set implies mean/micro precision and recall of 1.000 on that set (given the H12 convention,
§5), so the precision/recall rows are diagnostic and tier inputs, not independent hurdles —
but they are still listed and still checked.

| # | Gate row | Target for 10/10 | Baseline |
|---|---|---|---|
| G1 | Exact section-set match, current 16 (K0 + H1–H15, GT frozen as in backtest §3) | **16/16** | 5/16 |
| G2 | Exact section-set match, fresh held-out 16 (§4) | **16/16** | not run |
| G3 | Exact section-set match, Kannada 8 (§4) | **8/8** | not run |
| G4 | Mean precision, current 16 | ≥ 0.95 (1.000 if G1 passes) | 0.656 |
| G5 | Mean recall, current 16 | ≥ 0.95 (1.000 if G1 passes) | 0.492 |
| G6 | Micro precision / micro recall, current 16 | ≥ 0.95 / ≥ 0.95 (1.000 / 1.000 if G1 passes) | 0.875 / 0.368 |
| G7 | TP / FP / FN, current 16 (57 GT sections) | **57 / 0 / 0** | 21 / 3 / 36 |
| G8 | Court correct, current 16 | **16/16** | 10/16 |
| G9 | Escalates correctly, current 16 | **16/16** | 11/16 |
| G10 | Silent questions (non-empty GT, empty prediction) | **0** | 5 |
| G11 | Forbidden before Stage-2 recheck (all sets) | **0** | 2 |
| G12 | Prose forbidden mappings (§5) | **0** | NOT MEASURED |
| G13 | Model errors (all sets) | **0** | 0/16 |
| G14 | Latency (§3): mean per question ≤ 15 s, max per question ≤ 30 s, full 16-question run ≤ 240 s excl. load, model load ≤ 60 s | within budget | mean 11.77 s, max 24.17 s, run 188 s, load 25.8 s — already inside budget; this row is a **no-regression guard**, not a hurdle |
| G15 | Confirmation re-run (§4 step 9): full gate (G1–G14) passed a **second time**, independent live Colab run, zero code changes between runs | passed twice | not run |
| G16 | Run log complete (§4 step 10): every run numbered, dated, code version recorded, results JSON+MD filed | complete | baseline filed |

**Kannada is not optional for 10/10.** English-only perfection is at most 9/10 (§2 caps).
The user's original "fraction of a second" classification aspiration is a **separate stretch
goal** and is NOT part of this gate: the gate is about correctness, and the latency row above
is the only speed requirement.

---

## 2. Rating formula — how partial progress is scored honestly

Every live run gets one number from this formula. The formula is frozen; no run may be
re-scored under a different formula.

```
E  = exact / 16            (current-16 exact-match share)
Rm = mean recall           (current 16)
Pm = mean precision        (current 16)
C  = court correct / 16
S  = escalates correct / 16
Fb = forbidden-before-recheck count   (current 16)
Fp = prose-forbidden count            (questions with ≥1 prose forbidden mapping; §5)

Rating = 10 × [ 0.60·E + 0.15·Rm + 0.10·Pm + 0.075·C + 0.075·S ] − 0.5·Fb − 1.0·Fp
```

Clamp to [0, 10]; round to 1 decimal. Exact match carries the most weight (0.60) because
"gets the whole question right" is what the user asked for; recall (0.15) outweighs precision
(0.10) because the measured failure is under-firing (36 FN vs 3 FP).

**Worked baseline (2026-11-26 live):**
10 × [0.60×0.3125 + 0.15×0.492 + 0.10×0.656 + 0.075×0.625 + 0.075×0.6875]
= 10 × [0.1875 + 0.0738 + 0.0656 + 0.0469 + 0.0516] = 10 × 0.4253 = 4.25;
minus 0.5 × 2 (Fb) = **3.25 → 3.3/10**. That reproduces the honest ~3/10 live rating. Note the
forbidden penalty costs a full point: the same 5/16 exact with Fb = 0 would rate 4.3/10.

**Caps (applied after the formula; the lower of formula and cap is the rating):**

| Condition | Cap |
|---|---|
| Any prose forbidden mapping (Fp ≥ 1) | **≤ 5.0** — wrong law in prose to a vulnerable user is a hard failure, not a deduction |
| Any forbidden-before-recheck (Fb ≥ 1) | **≤ 9.0** — cannot be 10/10 while Stage 1 still fires a forbidden section, even if Stage 2 catches it |
| Prose not measured (no answer prose generated/scored) | **≤ 9.0** — classification-only scores are provisional |
| Fresh held-out set not run, or not passed | **≤ 9.0** — tuning-set perfection alone is not 10/10 |
| Kannada set not run, or not passed | **≤ 9.0** |
| No confirmation re-run (single run only) | **≤ 9.0** |
| Any model error | that question scores 0 on every component; ≥ 3 errors in a run caps the run at **≤ 5.0** |

**The 10/10 claim additionally requires every gate row in §1 to pass.** A formula output of
10.0 without G2/G3/G12/G15 passing is a 9.0, not a 10/10.

---

## 3. Tier table — what each whole-number rating means in metric terms

The number always comes from the §2 formula + caps. This table states what that number
normally looks like, so a rating can be read back into metrics and no one can claim a tier
the metrics do not support.

| Rating | Typical exact (current 16) | Typical mean recall | Typical mean precision | Forbidden / prose | Plain-language meaning |
|---|---|---|---|---|---|
| **10** | 16/16 + fresh 16/16 + Kannada 8/8 | 1.000 | 1.000 | Fb 0, Fp 0 | Every question fully right, in English and Kannada, on seen and unseen questions, twice. Gate closed. |
| **9** | 14–15/16 | 0.85–0.94 | ≥ 0.90 | Fb 0, Fp 0 | Near-perfect; one question's section set still off. One fix away — but not 10/10. |
| **8** | 12–13/16 | 0.75–0.84 | ≥ 0.85 | Fp 0 | Most questions right; multi-issue questions still losing issues. |
| **7** | 10–11/16 | 0.65–0.74 | ≥ 0.80 | Fp 0 | Majority right; recall still the binding problem. |
| **6** | 8–9/16 | 0.60–0.64 | ≥ 0.75 | Fp 0 | Half the questions fully right; silent/under-fired questions remain. |
| **5** | 6–7/16 | 0.50–0.59 | ≥ 0.70 | Fp 0 | Better than the generic chatbot retest (4/10) on sections, but still missing whole issues. |
| **4** | 5/16, Fb 0, Fp 0 | ~0.50 | ~0.66 | clean | Same section accuracy as baseline but no forbidden fires. |
| **3** | 4–5/16, with Fb ≥ 1 or Fp ≥ 1 | 0.45–0.54 | ~0.60 | Fb ≥ 1 | **← BASELINE SITS HERE (3.3/10).** Precise when it fires, silent on 5/16 questions, fires a forbidden section twice. |
| **2** | 2–3/16 | 0.30–0.44 | — | — | Fires on only a few questions; most issues missed. |
| **1** | 0–1/16 | < 0.30 | — | — | Barely functioning as a classifier. |
| **0** | no live run | — | — | — | No measured result. A walk, a plan, or an assertion is 0, not a rating. |

---

## 4. Validation loop — exact sequence

1. **Freeze before tuning.** GT for the current 16 is already frozen (backtest §3, including the
   two documented judgement calls: H14 includes HMA 13; H4 excludes PWDVA 20). Before any
   tuning run, also freeze GT for the fresh held-out 16 and the Kannada 8, written by a rater
   who is **not** the tuning lane, and file them with a checksum/date. Nothing in steps 2–5
   may see the fresh or Kannada questions.
2. **Diagnose from the live JSON, don't guess.** Each tuning cycle starts from the latest
   per-question output (which issues under-fired, which Stage-1 probabilities sat near the
   threshold, which questions went silent). The baseline diagnosis is §0.
3. **Fix ONE thing.** One change, one hypothesis, logged with the run number (e.g. "lower
   Stage-1 threshold for maintenance from 0.50 to 0.40"). Never batch multiple fixes into one
   run — otherwise no one can attribute the change in score.
4. **Re-run the full current 16 in live Colab.** Same notebook, same 16 questions, same GT,
   fresh Colab process. Record every metric in §1 plus the full per-question JSON. Compute the
   §2 rating and tick the §6 checklist.
5. **If the gate fails:** go back to step 2 with the new output, pick the single biggest
   failure class, fix ONE thing, re-run. Repeat. There is no limit on cycles; there is a
   limit of one change per cycle.
6. **Fresh held-out run — only when the current 16 passes.** When (and only when) G1 and
   G4–G14 all pass on the current 16, run the fresh held-out 16 **once**, in live Colab, same
   system, no changes between the current-16 pass and the fresh run.
7. **If the fresh set fails: DO NOT tune on it.** Do not add its questions or phrasings to
   the phrasebook, prompts, or threshold examples. Do not adjust any threshold to fit it. Do
   not edit its GT. Diagnose the **underlying cause** in general terms (e.g. "Stage-1
   threshold too high for short maintenance questions" — a cause that must also be visible
   in, or at least consistent with, the current-16 failures or a general principle). Fix the
   cause in the general mechanism, then **re-run BOTH sets** (current 16 + fresh 16). The
   fresh set may be re-run after a general fix; each re-run is logged. If a proposed fix can
   only be justified by a specific fresh question's wording, it is overfitting and forbidden.
8. **Kannada 8.** A Kannada baseline run may happen at any time to measure (it establishes a
   number, it does not block English tuning). Tuning **on** Kannada begins only after the
   English current + fresh sets both pass. Same rules as step 7: no Kannada question wording
   goes into the phrasebook.
9. **Confirmation re-run.** After G1–G14 pass on all three sets in one run, re-run all three
   sets in a **second independent live Colab run with zero code changes between runs**. Both
   runs must pass every row. Only then may 10/10 be claimed.
10. **Publish every run.** Results JSON + MD per run, filed next to the 2026-11-26 baseline
    files, with run date, notebook link, code version/commit, change made since the previous
    run, and the §2 rating. A run that is not filed does not count. Failed runs are filed too.

### Fresh held-out set (n = 16) — composition, to be written before tuning starts

Mirror of the current set's coverage, all-new questions, no wording copied from the current 16:
single-issue maintenance ×2, custody ×1, Stridhan ×1, residence ×1, birth certificate ×1;
multi-issue ×4 (incl. 1 divorce-asked, 1 proceeding-pending, 1 demand-not-made, 1
violence + residence + school fees); divorce explicitly NOT asked ×1; salary-slips-missing ×1;
income-unknown / quantum-asked ×1; no-proceeding interim money ×1; out-of-scope ×2.
At least 2 questions must have ≥ 5 GT sections (to match K0/H5/H14 difficulty) and at least 1
must be a negated/contrast question ("I do NOT want a divorce"), since negation is a known
failure axis.

### Kannada set (n = 8) — composition

Kannada-script questions, same issue coverage: maintenance, custody, Stridhan, residence,
divorce-asked multi-issue, divorce-not-asked, birth certificate, out-of-scope. GT frozen by a
Kannada-fluent rater before any run. Script (Kannada vs Latin transliteration) is recorded in
the run record; transliterated Kannada, if tested, is a separate variant, not the Kannada gate.

---

## 5. Frozen definitions (do not change mid-tuning)

- **Exact match:** `set(pred_labels) == set(gt_labels)`, order-insensitive, exact label
  strings. No partial credit. The label normalisation used in the 2026-11-26 run is frozen;
  any label-string change requires re-running the baseline.
- **H12 convention:** a question with empty GT and empty prediction scores precision 1.0 /
  recall 1.0 / exact True (0/0 convention, as in the baseline run). This is a disclosed
  leniency: the fresh set contains 2 out-of-scope questions under the same convention.
- **Mean precision/recall:** arithmetic mean over all 16 questions, H12 included at 1.0/1.0.
- **Micro precision/recall:** TP / (TP + FP) and TP / (TP + FN) over all 57 GT sections.
- **Forbidden before recheck (Fb):** a Stage-1 candidate that Stage 2 drops for violating a
  recheck rule (e.g. HMA 25 with no decree, HMA 24 with no proceeding, HMA 13/13B with
  divorce not asked, HMA 26 with no proceeding). Counted per question.
- **Prose forbidden mappings (Fp):** the full answer prose must be generated and scored by an
  independent rater against this list; Fp = number of questions with ≥ 1 hit (total instances
  also recorded). The list, from the 2026-11-26 retest error record:
  1. Rajnesh v. Neha cited for Stridhan return (or any precedent cited for the wrong issue);
  2. Satish Chander Ahuja cited for custody (or any precedent cited for the wrong issue);
  3. HMA ss. 13/13B in prose when divorce was not asked (13B additionally requires mutual consent);
  4. residence called "tenancy rights" (or any wrong legal label for residence);
  5. user asked to pick the court instead of the system naming it;
  6. birth certificate placed under HMA (or any wrong Act);
  7. any section in prose that Stage 2 dropped for the stated facts;
  8. a maintenance amount stated as a number instead of escalated;
  9. salary slips demanded when the user said they do not have them.
  If the system produces no answer prose, Fp is NOT MEASURED and the §2 cap (≤ 9.0) applies.
- **Live Colab run:** the linked notebook run in Google Colab (CPU, PIXMELT snapshot), all
  cells clean, results JSON + MD downloaded and filed. A local/VM run, a walk, or a reasoning
  argument is not a live run.
- **Latency:** per-question inference time as recorded in the run JSON (model load excluded
  from the per-question figure, reported separately).

---

## 6. Anti-overfitting rules — forbidden once tuning starts

1. **Never edit GT to match predictions.** The two judgement calls (H14/HMA 13, H4/no-PWDVA 20)
   are frozen. Any future GT dispute goes to an independent rater, never to the tuning lane,
   and a GT change invalidates all prior runs on that set (they must be re-run and re-filed).
2. **No fresh-set or Kannada-set wording in the system.** No exact fresh/Kannada question,
   phrase, or paraphrase may be added to the phrasebook, prompts, examples, or tests used
   for tuning. Phrasebook additions must come from general layman language, not from test
   questions.
3. **No threshold fitted to a single question.** Any threshold change must improve or hold
   ≥ 2 questions and must be set from the current-16 distribution, not from one question's
   score (H1's 0.4795 alone never justifies a threshold move).
4. **No per-question special cases.** No hardcoded question-ID branches, no
   if-question-contains-X rules, no lookup keyed to a test question.
5. **No removing or redefining failing questions.** No dropping a hard question from a set,
   no redefining "exact", no reporting a subset ("14/14 excluding the hard ones").
6. **No tuning on fresh/Kannada per-question outputs** beyond general-cause diagnosis (§4.7–4.8).
7. **No quoting the graph-walk 16/16 as a live result**, ever, in any report, at any stage.
8. **No best-run cherry-picking.** Every run is filed in sequence, failures included; the
   rating is the latest run's rating, not the best run's.
9. **No changing the metric definitions, formula, or targets mid-tuning.** This document is
   frozen; amending it requires the coordinator and invalidates the "10/10" label until the
   full gate is re-passed under the amended version.
10. **No silent changes between the gate pass and the confirmation re-run** (§4.9). Any code,
    phrasebook, threshold, or prompt change resets the confirmation requirement.

---

## 7. What 10/10 does NOT mean

- **Not single-run luck on 16 questions.** One passing run without the §4.9 confirmation
  re-run is at most 9/10.
- **Not the graph-walk score.** 16/16 deterministic walk ≠ live 16/16. Quoting it as a live
  result is a misrepresentation, not progress.
- **Not precision-only.** Micro precision is already 0.875 at baseline while micro recall is
  0.368 — a system that is precise and silent is not 10/10. Recall gates bind equally.
- **Not a rating asserted without a live Colab run.** No walk, no local run, no argument from
  first principles, no model opinion substitutes for a live run.
- **Not English-only.** Without the Kannada 8 passing, the ceiling is 9/10.
- **Not classification-only.** Without measured, zero-forbidden answer prose, the ceiling is 9/10.
- **Not "close enough".** 15/16 exact is 9/10, honestly. 12/16 is 8/10. Rounding 15/16 up to
  10/10 is not permitted.
- **Not a better walk, a better plan, or a better explanation.** Only live Colab numbers move
  the rating.

---

## 8. One-page gate checklist — tick off per run

Copy this table into each run's report. "Actual" is that run's measured value; "Pass" is
judged against the Target column. Fresh/Kannada rows are N/A until their run (§4.6/4.8).

| Metric | Target (10/10) | Baseline 2026-11-26 | Run actual | Pass? |
|---|---|---|---|---|
| Exact, current 16 | 16/16 | 5/16 | | |
| Exact, fresh 16 | 16/16 | not run | | |
| Exact, Kannada 8 | 8/8 | not run | | |
| Mean precision (current 16) | ≥ 0.95 | 0.656 | | |
| Mean recall (current 16) | ≥ 0.95 | 0.492 | | |
| Micro precision (current 16) | ≥ 0.95 | 0.875 | | |
| Micro recall (current 16) | ≥ 0.95 | 0.368 | | |
| TP / FP / FN (current 16) | 57 / 0 / 0 | 21 / 3 / 36 | | |
| Court correct (current 16) | 16/16 | 10/16 | | |
| Escalates correct (current 16) | 16/16 | 11/16 | | |
| Silent questions (non-empty GT, empty pred) | 0 | 5 | | |
| Forbidden before recheck (all sets) | 0 | 2 | | |
| Prose forbidden mappings | 0 | NOT MEASURED | | |
| Model errors | 0 | 0 | | |
| Latency mean / max per question | ≤ 15 s / ≤ 30 s | 11.77 s / 24.17 s | | |
| Full-run time (excl. load) / model load | ≤ 240 s / ≤ 60 s | 188 s / 25.8 s | | |
| Confirmation re-run passed (zero changes) | yes | not run | | |
| Run filed (JSON + MD, run no., date, code version) | yes | yes (baseline) | | |
| **§2 rating (formula + caps)** | **10.0** | **3.3/10** | | |
