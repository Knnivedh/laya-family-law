# Brutal test — 200+ questions against Laya (design only)

**Status: DESIGN ONLY. No live run, no Colab, no changes to the 16-question set, its
ground truth, or the sealed fresh-20 / Kannada-8 sets.** This plan is ready to execute
the moment a live score above 9 is confirmed.

**Gate:** execution is gated on a live run scoring **> 9** under the frozen gate
formula (`laya-10-10-gate-definition.md` §2) — i.e. a live 16/16 current-set pass,
reported as 9.0 capped. If the live score is ≤ 9, this test waits. It is a
generalisation stress test, **not** a tuning set and **not** a gate row: a brutal
pass does not confer 10/10, and a brutal fail does not revoke a gate pass — it
triggers a general-cause fix and a full re-run (see §6).

**Why this test exists (from the v6 deep-dive):** v5's fact gates are hand-annotated
oracle leakage — the 16/16 replay is a ceiling, not evidence the system generalises.
The 16 questions are now a frozen regression set: every false positive in them has
been inspected, so they can no longer test generalisation. The sealed fresh-20 hints
at generalisation (n = 20); this bank (n = 230) measures it properly, including the
failure axes the v6 lanes proved are untested: custody paraphrases (H6 regex 0/3
must-not-gate), money asked without money words, role reversal, negation, and
incidental money/gold mentions.

**Preconditions before any execution:**
1. Live > 9 confirmed (run 3 v5 or run 4 v6 filed, gate-formula rating ≥ 9.0).
2. Decision D1 (HMA 27 ground-truth correction) settled by the independent rater
   — the bank cannot be frozen until it is (§2.3).
3. Colab access resolved (nivedhbhat15 Google sign-in; the saved password was
   rejected twice ~07:08 IST on 2026-11-27 — the same block that stopped the v5
   live run and the Gemini consultation).
4. G2 gate amendment (fresh 16 → 20) recorded, so the brutal bank is not confused
   with the gate's fresh set. The brutal bank is a **separate** set; it never
   replaces or extends the sealed fresh-20.

---

## 1. Question bank structure — 230 questions, 14 categories

Counts total **230** (200 minimum + 30 margin so one category can lose a few
questions to rater rejection without dropping below 200). Every category is tied
to a known weak point from the v6 lanes. Each batch (§4) is stratified across
categories — never one category per batch.

| # | Category | n | What it stresses (known weak point) |
|---|---|---|---|
| C1 | Multi-issue (2–4 issues in one question) | 30 | Multi-issue dilution — the v1 failure (K0 recall 0.20, H13 0.20). Must fire every issue, not just the loudest. Includes 4 divorce-asked, 4 proceeding-pending, 4 demand-not-made, 4 violence + residence + school fees. |
| C2 | Maintenance-only, single issue | 20 | Quantum asked, income unknown, salary slips missing (forbidden #9: never demand slips the user said they lack), interim money with no proceeding. |
| C3 | Stridhan vs maintenance confusion | 20 | Gold held vs sold, demand made vs not made, jointly-owned vs solely-owned property. The H1/H3/H15 confusion axis; `gold_fact` must fire only on a real recovery claim. |
| C4 | Residence over-firing (must NOT fire) | 20 | Custody-only, violence-only, money-only and divorce-only questions where residence must stay silent. The v3/v4r leak (R1 fired 11/16). |
| C5 | Custody vs residence | 20 | "Stay in the house with my daughter", "I want my child to live with me", "Who gets the kids after divorce?", "Can I keep my son with me?" — the H6 regex failed 0/3 must-not-gate paraphrases; plurals (children/kids) included. |
| C6 | HMA 27 / HMA 26 proceeding prereq | 16 | Proceeding pending vs divorce merely asked vs not filed vs "being filed". Divorce-asked ≠ proceeding-pending (H5 sub-choice error). GT follows the decided D1 branch (§2.3). |
| C7 | Negation / contrast | 16 | "I do NOT want a divorce", "I don't want maintenance, only my gold", "no violence happened". Negation is a known failure axis (gate §4 composition). |
| C8 | Role reversal | 12 | Husband as claimant, wife as earner, father seeking custody, wife withholding the child. The system must not assume the claimant is always the wife. |
| C9 | Incidental money / gold mentions | 16 | Money mentioned but not claimed; gold as an object, not a claim; money need phrased without money words ("books and uniforms"). The `money_fact`/`gold_fact` false-fire axis. |
| C10 | Out-of-scope (non-family-law) | 12 | Landlord–tenant eviction, property dispute between brothers, unrelated criminal theft, employment dispute. Empty GT; H12 0/0 convention applies. |
| C11 | Court / forum traps | 12 | Birth certificate → Registrar, not Family Court; residence order → Magistrate; divorce/custody → Family Court; maintenance enforcement forum. Wrong-forum GT is a failure even if sections are right. |
| C12 | Quantum disputes | 8 | Ordered amount not paid, amount contested, interim amount, arrears. Tests quantum escalation (not a number in prose — forbidden #8). |
| C13 | Kannada forms (Kannada script) | 16 | Same issue coverage as C1–C5/C7 in Kannada script: maintenance ×4, custody ×3, Stridhan ×3, residence ×2, multi-issue ×2, birth certificate ×1, out-of-scope ×1. Written by a Kannada-fluent rater; transliterated Kannada is a separate variant, not this category. |
| C14 | Adversarial paraphrases | 12 | Same legal facts as C1–C5 in layman slang, typos, one-line questions, and long rambly narratives. Tests whether the system understands facts or memorised phrasings. |
| | **Total** | **230** | |

**Bank hygiene (binding):**
- No question, phrase, or paraphrase may be copied from the current 16, the sealed
  fresh-20, the sealed Kannada-8, the v5/v6 lane paraphrase tests, or the 20 design
  examples in §5. An 8-gram overlap check against all of those is run before freeze;
  any hit is rewritten by the rater.
- No question may be written to fit a threshold, a prompt, or a phrasebook entry.
  The rater never sees the notebook, the thresholds, or the phrasebook.
- Question length: mix of one-liners (≥ 20), medium (2–3 sentences, majority) and
  long narratives (≥ 10, as in BX-20).

---

## 2. Ground-truth protocol

### 2.1 Who writes the bank and the GT
- **One independent rater** writes all 230 questions and their GT. The rater must
  **not** be anyone who tuned v3/v4/v5/v6, wrote the v6 lanes, or ran the
  consultations. Rater name/ID, legal qualification, and Kannada fluency (for C13)
  are recorded in the freeze note before writing starts.
- **Second rater** double-rates a random 25% of the bank (58 questions) blind.
  Agreement is reported per question; any disagreement goes to adjudication (§2.2).
- The tuning lanes, the coordinator, and Nivedh may set the **categories and counts**
  (§1) but may not write, edit, or veto individual questions or GT entries. If a
  question is rejected, the rater replaces it with another in the same category.
- The 20 examples in §5 are **design examples only** — written by the design side
  to prove the format. They are **not** part of the bank, and the rater must not
  reuse them (the 8-gram check in §1 covers them).

### 2.2 Freezing and disagreement
1. Rater writes questions + GT (sections, court, escalates + typed kind, see §3).
2. Second rater double-rates 25% blind. **Rater wins on disagreement** (same rule
   as the prose protocol, v6 §5); the second rater's view is logged, not imposed.
3. Adjudication: where the two raters disagree on a **legal** point (not a wording
   point), a third qualified reader settles it and the reasoning is logged in one
   line per adjudicated question. Where they disagree on escalates, the typed-kind
   design (§3) is applied and the kind is recorded.
4. Freeze: the bank JSON is checksummed (SHA-256) with a dated freeze note
   (rater name/ID, D1 branch applied, counts per category, 8-gram check result,
   adjudication log). **GT is frozen before any run.** After freeze, no GT edit is
   permitted; a GT error found during/after a run is logged as a bank defect and
   fixed only by a new bank version (B-bank v2) with a fresh freeze — never by
   editing the frozen file.
5. The bank file is **never** opened by any tuning lane, notebook, or prompt. The
   Colab runner reads it at run time only, and emits IDs + scores only (same
   sealed-runner discipline as the fresh-20: no sealed wording in outputs).

### 2.3 HMA 27 — the D1 decision gates the freeze
- The bank **cannot be frozen** until D1 is decided (v6 §4.3): **D1-A** (remove
  HMA 27 from GT where no proceeding is pending or being filed; GT shrinks) or
  **D1-C** (replace with the new label `FCA 7(1) Expl. (c) / CPC 151` where
  applicable; GT size unchanged). D1-B (keep GT, weaken the prereq) is rejected
  by the v6 lanes and is not an option for this bank.
- The freeze note records which branch was applied, question by question, for
  every C6 question and any other question touching jointly-owned property.
- If D1-C is chosen, the new label must first be added to the system's label set
  (graph + notebook) — otherwise the system physically cannot produce it and
  every such question is a guaranteed miss. That addition is a system change,
  logged with its own run number, and the brutal run happens after it.
- If D1 is changed **after** the bank freezes, the bank is invalidated exactly as
  gate §6.1 invalidates a set on a GT change: the run is discarded, the bank is
  re-frozen as v2, and the run is repeated from batch 1.

### 2.4 GT record format (per question)
```json
{
  "id": "B-001",
  "category": "C1",
  "question": "<full question text, as the user would type it>",
  "language": "en | kn",
  "gt_sections": ["bnss-144", "pwdva-20"],
  "gt_court": "Magistrate",
  "gt_escalates": true,
  "gt_escalation_kinds": ["quantum"],
  "gt_notes": "one line: why these sections, why this court (rater only)"
}
```
- `gt_court` values: `Family Court`, `Magistrate`, `Registrar`, `District Registrar`,
  `none` (out-of-scope / no forum). For multi-issue questions, the court is the
  **lead forum** for the dominant relief; the rater states the lead-forum rule in
  the freeze note and applies it uniformly.
- `gt_escalates` uses the **typed** kinds from v6 §3 (quantum, court, demand,
  custody, residence, recovery, procedure, fact, safety). A question may carry
  more than one kind; scoring is per-kind (§3).
- Empty-GT questions (C10 and some C9/C12 items) follow the H12 0/0 convention:
  empty prediction scores exact True, precision 1.0, recall 1.0.

---

## 3. Scoring

### 3.1 Metrics — same frozen definitions as the 16-set, generalised to N = 230
All definitions from gate §5 apply unchanged (exact = set equality, order-insensitive;
H12 0/0 convention; mean/micro precision and recall; Fb = forbidden-before-recheck;
Fp = prose-forbidden count; silent = non-empty GT with empty prediction; model
errors counted per question). The only change is the denominator: **16 → 230**.

- Exact section-set match: `exact / 230`
- Mean precision / mean recall (over 230, H12-style empties at 1.0/1.0)
- Micro precision / micro recall; TP / FP / FN (over all GT sections in the bank)
- Court correct: `/ 230` (lead-forum rule, §2.4)
- Escalates correct: `/ 230`, scored on **typed kinds** — a question is correct
  only if the predicted kind set equals the GT kind set (a correct boolean with
  the wrong kind is a miss)
- Silent questions: count, must be 0
- Forbidden before recheck (Fb): count, must be 0
- Prose forbidden mappings (Fp): count, must be 0 — **only if prose exists by
  then**. If the system produces no answer prose, Fp is NOT MEASURED and the
  ≤ 9.0 cap applies to any rating quoted from this run (gate §2).
- Delivered-answer F1 (if prose exists): per-section F1 computed from the
  **delivered answer prose** (sections actually stated), scored by the independent
  rater blind to the checker, rater wins on disagreement, 25% double-rating
  (v6 §5 protocol). Reported alongside graph F1; a gap between graph F1 and
  delivered F1 is a renderer finding, not a classifier finding.
- Model errors: count, must be 0
- Latency: mean / max per question, total run time, model load (G14-style budget
  reported for the bank, not gated — see §4.3)

**Rating from this run:** the frozen gate formula with N = 230:
`Rating = 10 × [0.60·E + 0.15·Rm + 0.10·Pm + 0.075·C + 0.075·S] − 0.5·Fb − 1.0·Fp`,
clamped [0, 10], rounded to 1 decimal, with the same caps as gate §2. This rating
is a **brutal-bank rating**, not a gate rating — it must always be quoted with
"(brutal bank, n = 230)" and never presented as the 10/10 gate score.

### 3.2 Pass bar — stated explicitly, before any run
The brutal test **passes** only if **all** of the following hold:

| Metric | Pass bar |
|---|---|
| Exact | ≥ 200 / 230 (87.0%) |
| Micro-F1 | ≥ 0.95 |
| Micro precision / micro recall | ≥ 0.95 / ≥ 0.95 |
| Mean precision / mean recall | ≥ 0.90 / ≥ 0.90 |
| Court correct | ≥ 200 / 230 |
| Escalates correct (typed) | ≥ 200 / 230 |
| Silent questions | 0 |
| Forbidden before recheck (Fb) | 0 |
| Prose forbidden (Fp), if prose exists | 0 |
| Model errors | 0 |
| Per-category exact | no category below 75% exact (a pass must not hide a collapsed category) |

If any row fails, the brutal test **fails as a whole** — there is no partial pass,
no "passed except custody". The failure report names the failing categories and
the failure taxonomy (§3.3).

### 3.3 What 230 questions can and cannot prove (statistics — do not invent a 99% claim)
Exact-match rate is a proportion; the honest statement is the rate **with its
95% confidence interval** (Wilson interval, approximate). The table below is the
reading guide — the run report must print the interval for the achieved rate,
not just the point estimate.

| Achieved exact | Point rate | Approx. 95% Wilson interval | What it proves |
|---|---|---|---|
| 230 / 230 | 100% | 98.4% – 100% | ≥ ~98.4% true exact rate at 95% confidence. Does **not** prove 99%. |
| 228 / 230 | 99.1% | 96.8% – 99.8% | Consistent with 99%, but the lower bound is 96.8% — 99% is not established. |
| 220 / 230 | 95.7% | 92.2% – 97.7% | Solid generalisation; not a 99% system. |
| 200 / 230 | 87.0% | 81.9% – 91.0% | Pass bar met, but the true rate could be as low as ~82%. |
| 180 / 230 | 78.3% | 72.5% – 83.1% | Fail; generalisation is materially below the 16-set score. |

**The user's "minimum 99% accuracy" cannot be established by 200–230 questions.**
Rule of three: 230 failure-free trials prove a failure rate ≤ 1.3% (≥ 98.7%) at
95% confidence. To claim ≥ 99% at 95% confidence needs **~300 failure-free
trials** (3/300 = 1.0%). The bank is therefore structured so it can be extended
to 300 by the same rater under the same protocol (+70 questions, same category
ratios, fresh freeze as bank v2) **if** a 99% claim is ever wanted. Until then, no
report may claim 99% from this test — the correct claim is the interval above.

### 3.4 Diagnostics the run report must include (the point of the test)
- Per-category exact, micro-F1, FP/FN counts (14 rows — this is where the
  generalisation verdict lives).
- Per-issue confusion: for each issue (maintenance, custody, Stridhan, residence,
  divorce, violence, birth), over-fire count (FP) and under-fire count (FN).
- Failure taxonomy per failed question, one of: `over-fire` (extra section),
  `under-fire` (missed section), `wrong-forum` (sections right, court wrong),
  `wrong-escalation` (sections right, kind wrong), `silent`, `forbidden`,
  `model-error`, `prose-only` (graph right, prose wrong). Counts per taxonomy
  class are reported.
- Margin table (v6 §7.3 discipline): every per-question score within 0.05 of a
  threshold, to 4 decimals.
- Comparison table vs the 16-set live run and vs the sealed fresh-20 (same
  metrics, side by side) — with the explicit warning that the sets differ in
  size and difficulty, so the comparison is diagnostic, not a ranking.

---

## 4. Execution plan for Colab

### 4.1 Gating and sequencing
1. Brutal run starts **only** after the live > 9 gate (§0) is met and D1 is
   decided (§2.3). Starting earlier turns the bank into a tuning set — the
   exact failure the gate's anti-overfitting rules exist to prevent.
2. One frozen system version runs the whole bank. The notebook, builder, graph,
   thresholds, prompts, phrasebook and fact annotations are checksummed before
   batch 1; **zero changes** between batches. A change mid-run invalidates all
   completed batches.
3. Run numbering: brutal runs use their own series — **B1, B2, …** — never the
   gate's global run numbers (run 0 = v1, run 1 = v3, run 2 = v4r, run 3 = v5,
   run 4 = v6). A brutal re-run after a fix is B2, and must be labelled
   "regression re-run on a used bank" (§4.4).

### 4.2 Batching and checkpointing
- **10 batches: B1–B9 of 25 questions, B10 of 5 questions** (230 total).
  Each batch is **stratified**: it contains questions from every category in
  proportion to §1 (e.g. a 25-question batch has ~3–4 C1, ~2 C2, ~2 C3, ~2 C4,
  ~2 C5, ~2 C6, ~2 C7, ~1 C8, ~2 C9, ~1 C10, ~1 C11, ~1 C12, ~2 C13, ~1 C14).
  Batch composition is fixed in the freeze note; a crash therefore never loses
  a whole category.
- Each batch runs as its own Colab session (fresh process, same notebook,
  model load per batch). After each batch, the runner **downloads and files
  the batch JSON + MD immediately** (`brutal-B{n}-results.json/.md`) before
  starting the next batch. A crash loses at most one batch.
- Batch files record: batch id, question IDs, hardware class, per-question
  pred/GT/scores/timing, batch aggregate, and the frozen artefact hashes.
- The merged final report (`brutal-final-report.md`) is written only after all
  10 batches are filed, from the batch files — never by re-running questions.

### 4.3 Timing — CPU vs T4 (measured figures only; T4 is unverified)
Measured on Colab CPU (v4r live JSON): mean **57.6 s/question**, max 133.3 s,
~728 inferences per 16 questions (~46/question, ~1.27 s/inference).

| Hardware | Per question (planning) | Batch of 25 | Full 230 |
|---|---|---|---|
| Colab CPU (measured) | ~58 s mean | ~24 min + ~30 s load | ~3.7 h + loads ≈ **~4 h** |
| Colab T4 GPU (unverified planning figure 0.2–0.4 s/inference, v6 §6) | ~9–18 s | ~4–8 min | ~35–70 min |

- **T4 figure must be measured, not assumed.** Batch 1 is the measurement batch:
  record actual per-question time; re-forecast the remaining batches from it. If
  T4 actual per-question time exceeds 15 s, the plan falls back to CPU batches
  and the forecast is revised in the coordinator log.
- **One hardware class for the whole run.** CPU and GPU batches must not be mixed
  in one brutal run (same rule as the G15 confirmation pair, v6 §7.3): a class
  change is a declared deviation and the run is re-labelled accordingly.
- Practical schedule on CPU: 5 batches per sitting (~2 h), two sittings, or one
  overnight run with checkpointing. On T4: the whole bank fits in a single
  sitting (~1 h). Colab's idle-session limits apply — the runner must keep the
  session alive between batches and must never leave a batch half-written.

### 4.4 No tuning on the brutal bank — the rule that protects it
- **No fix between batches.** A failure found in batch 2 is not fixed before
  batch 3. All 10 batches run, the report is filed, and only then is a fix
  diagnosed — in **general** terms (a cause that must also be visible in, or
  consistent with, the 16-set failures or a general principle), exactly as gate
  §4.7 requires for the fresh set.
- **No bank wording into the system.** No brutal question, phrase, or paraphrase
  may enter the phrasebook, prompts, examples, or threshold fittings. A fix
  justifiable only by a specific brutal question's wording is overfitting and
  forbidden.
- **Re-run discipline:** after a general fix, the whole bank is re-run as B2.
  B2 is a **regression re-run on a used bank** — it measures whether the fix
  worked, not clean generalisation. A clean generalisation claim after a B2 fix
  needs a **new unseen bank** (bank v2, same protocol, new rater questions).
  B1's questions are never re-used as tuning inputs between B1 and B2.
- **Prose:** if the template renderer (Cell 9) exists by run time, prose is
  generated for all 230 and scored per §3.1. If it does not exist, Fp is NOT
  MEASURED and the ≤ 9.0 cap applies to the brutal rating.

---

## 5. Twenty example brutal questions (design examples — NOT part of the bank)

These prove the format works. They were written by the design side, so they are
**excluded from the bank** and the rater must not reuse them (§1 hygiene). GT
below assumes **D1-A** (HMA 27 removed where no proceeding is pending/being
filed); the two examples touching HMA 27 (BX-07) are flagged — if D1-C is chosen,
the rater re-labels them. Courts follow the lead-forum rule (§2.4).

| ID | Cat. | Question | GT sections | Court | Escalates (kinds) | Stresses |
|---|---|---|---|---|---|---|
| BX-01 | C1 | My husband beat me last week, threw me out of the house, and has not given money for our daughter's school fees for three months. | bnss-144, pwdva-20, pwdva-17, pwdva-18, pwdva-19 | Magistrate | True (quantum, safety) | Multi-issue: violence + residence + money |
| BX-02 | C2 | My husband earns ₹80,000 a month but gives me nothing. How much maintenance can I get for myself and my 6-year-old son? | bnss-144, pwdva-20 | Magistrate | True (quantum) | Quantum asked; income stated |
| BX-03 | C3 | My mother-in-law is keeping my gold bangles and necklace that my parents gave me at the wedding. She refuses to return them. | bns-316 | Magistrate | True (recovery) | Stridhan held, demand refused |
| BX-04 | C3 | My husband sold my gold chain last year without asking me and spent the money. I want the money back. | bns-316 | Magistrate | True (recovery) | Stridhan sold; valuation needed |
| BX-05 | C5 | I want my 8-year-old daughter to live with me after the divorce. My husband says he will keep her. | gwa-1890 | Family Court | True (custody) | Custody only — residence must NOT fire |
| BX-06 | C5 | Can I keep my son with me? I don't want him to go to his father's house. | gwa-1890 | Family Court | True (custody) | Must-not-gate paraphrase (v6: regex failed this) |
| BX-07 | C6 | My divorce case is already going on in Family Court and we bought a house together during the marriage. Can the court divide the house in the divorce case? | hma-27 ⚠️ D1-A assumed; re-label under D1-C | Family Court | True (fact — valuation) | Proceeding pending → HMA 27 available |
| BX-08 | C7 | I do NOT want a divorce. I only want my husband to pay for my children's school fees. | bnss-144, pwdva-20 | Magistrate | True (quantum) | Negation: no HMA 13/13B |
| BX-09 | C7 | My husband never hit me and I don't want to file any case. I just want my gold back from my in-laws. | bns-316 | Magistrate | True (recovery) | Negation + Stridhan, no violence sections |
| BX-10 | C8 | I am a father and my wife left with our son. I want custody of my son. | gwa-1890 | Family Court | True (custody) | Role reversal: father claimant |
| BX-11 | C9 | My husband gives me money every month but he never lets me meet my parents. Can I do something? | pwdva-18 | Magistrate | True (fact, safety) | Money mentioned, NOT claimed — maintenance must NOT fire |
| BX-12 | C9 | My husband gifted me a gold ring on our anniversary. It is kept in our bank locker. Can I take it out? | [] (no legal issue) | none | False | Gold as object, no claim — Stridhan must NOT fire |
| BX-13 | C10 | My landlord has locked my shop and is demanding two months' rent. What can I do? | [] (out of scope) | none | True (handoff — civil tenancy matter, human lawyer) | Out-of-scope; H12 convention |
| BX-14 | C11 | The hospital did not give a birth certificate for my baby. How do I get one? | births-deaths-act-1969 | Registrar | True (procedure) | Forum trap: Registrar, not Family Court |
| BX-15 | C11 | The house is in my husband's name and he has thrown me out. Can I go back and stay there? | pwdva-17, pwdva-18, pwdva-19 | Magistrate | True (residence) | Residence right vs ownership |
| BX-16 | C12 | The court ordered my husband to pay ₹10,000 maintenance but he pays only ₹4,000. What can I do? | bnss-144 | Magistrate | True (quantum) | Enforcement of an existing order |
| BX-17 | C1 | I want a divorce from my husband. He drinks every day, hits me, and I want our 5-year-old daughter to stay with me. I also need money for her school. | hma-13, bnss-144, pwdva-20, pwdva-18, gwa-1890 | Family Court | True (quantum, custody, safety) | Multi-issue, divorce asked |
| BX-18 | C13 | ನನ್ನ ಗಂಡ ನನಗೆ ಜೀವನಾಂಶ ಕೊಡುತ್ತಿಲ್ಲ. ನನ್ನ ಮಗಳಿಗೆ ಶಾಲಾ ಫೀಸ್ ಕಟ್ಟಬೇಕು. ನಾನು ಏನು ಮಾಡಬೇಕು? | bnss-144, pwdva-20 | Magistrate | True (quantum) | Kannada script: maintenance + school fees |
| BX-19 | C14 | hubby took my gold n sold it, i want it back pls help | bns-316 | Magistrate | True (recovery) | Adversarial: slang/typos, Stridhan sold |
| BX-20 | C14 | I got married in 2019, we have two kids, my husband lost his job in 2024, since then my mother-in-law taunts me daily, last month she took my jewellery box and says it belongs to the family, my husband supports her, I have no salary slips because I never worked outside, I want my jewellery back and some money to run the house — what are my rights? | bns-316, bnss-144, pwdva-20, pwdva-18 | Magistrate | True (quantum, recovery) | Long narrative; salary-slips-missing (never demand slips); jewellery = Stridhan |

---

## 6. What a brutal pass / fail means

- **Pass (all §3.2 rows):** the system generalises beyond the 16. Report the
  brutal rating with its interval (§3.3) and the per-category table. It does **not**
  confer 10/10 — the gate still needs fresh-20, Kannada-8, prose Fp = 0, G14 and
  the G15 confirmation re-run. It is the strongest evidence short of the gate
  that the v5/v6 fixes were real and not oracle leakage.
- **Fail:** file the report, name the failing categories and taxonomy classes,
  diagnose the **general cause** (never a per-question patch), fix the general
  mechanism, and re-run the whole bank as B2 (regression re-run, §4.4). If the
  failing category is one the v6 lanes already flagged (custody paraphrases,
  money-without-money-words, HMA 27 prereq), the fix is the v6-specified one
  (per-clause choice node, model-extracted facts) — not a new pattern list.
- **Inconclusive (crash / partial batches):** report the completed batches only,
  with their counts, and resume from the next unfiled batch. A partial bank is
  never scored as a full result and never quoted as a rating.

## 7. Open items before execution (checklist — all must be ticked)

- [ ] Live > 9 confirmed (run 3 or run 4 filed, gate-formula rating ≥ 9.0)
- [ ] D1 decided by the independent rater (A or C); branch recorded
- [ ] G2 amendment (fresh 16 → 20) recorded in the gate doc
- [ ] Rater appointed (name/ID recorded) + second rater for 25% double-rating;
      Kannada-fluent rater confirmed for C13
- [ ] Colab access resolved (nivedhbhat15 sign-in)
- [ ] Hardware class decided (CPU vs T4) and recorded; T4 timing measured in batch 1
- [ ] Prose renderer status decided (Cell 9 exists → Fp measured; else NOT MEASURED + cap)
- [ ] Bank written, 8-gram check passed, frozen with SHA-256 + freeze note
- [ ] Batch composition (stratified, §4.2) fixed in the freeze note

## Sources
- `v6-deep-dive-report.md` (§1 generalisation verdicts, §2 extraction design,
  §3 typed escalations, §4 D1–D11, §6 latency, §7 validation/confirmation)
- `laya-10-10-gate-definition.md` (§2 frozen formula + caps, §4 validation loop,
  §5 frozen definitions, §6 anti-overfitting rules, §8 checklist)
- v4r live JSON (`workspace/browser_downloads/sess-2184034649/…-live-laya-colab-results-v4r-residence-only.json`):
  exact 10/16, micro-F1 0.905, TP/FP/FN 57/12/0, mean 57.6 s/question, 728 inferences/16 questions
