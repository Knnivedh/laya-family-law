# ChatGPT Recall Consultation — Re-run on the Updated Brief (GPT-6.2, thinking max)

- **Date/time:** 2026-11-27, browser task ran 21:46–21:52 IST (measured). Response shows "Worked for 2m 11s", "Response complete".
- **Chat:** https://chatgpt.com/c/6b09ad19-2cb4-83e8-8a6a-6f3a19f4e7ad
- **Model verified:** GPT-6.2 — checked in the picker before sending (top of the list) and again after the response; thinking effort High, 3 of 3 = MAX. This is the real requested model.
- **Brief sent:** the updated brief (8,000 corpus, frozen split 261/500 = 52.2%, Kaanoon 14/28 = 50%) plus §7 asking for a critique of the four [FALLBACK-2] claims. Brief file: `files/laya-graph/chatgpt-rerun-brief.md`.
- **Purpose:** second opinion on the updated brief + a cross-check of the four Hydrogen-fallback flaws before committing to them in the 70% plan. Structured summary, not verbatim.

## 1. Executive verdict

The updated results strengthen the case for replacing regex-gated extraction. They do NOT establish that the proposed classifier will reach 70%. Critical distinction: **52.2% is the performance of the existing system on synthetic validation, not of a trained classifier** — there is no measured classifier learning curve yet. Recommendation: proceed with training after correcting the architectural problems below, rather than another cycle repairing regex patterns.

| Point | Verdict | Action |
|---|---|---|
| Replace regex-gated extraction | Agree | Adopt |
| Train existing 7,500 first | Agree | Adopt |
| mmBERT-base as predetermined winner | Amend | Benchmark first |
| Single-pass contextual span pooling | Strongly agree | Adopt |
| Replace binary ASL | Strongly agree | Adopt |
| Class-balanced focal CE | Partially agree | Compare against weighted CE |
| Graph-aware threshold calibration | Strongly agree | Adopt with corrections |
| Fixed EB shrinkage κ = 150 | Unproven | Treat as hyperparameter |
| Expand by ~4,750 records | Agree conditionally | After first learning curve |
| Relax human evaluation gate | **Disagree** | **Retain 80% per language** |
| Stop NLLB-dependent augmentation | Agree | Adopt |
| Wait for a genuine Neon response | Unnecessary | Proceed with measurable experiments |

Central judgment: architecture is moving in the right direction, but semantic grounding, training-data diversity and graph-aware calibration matter more than corpus size or a larger backbone.

## 2. Numbers and the gap (re-audit)

Measured exact (excluding known banks): Fresh-20 35% (7/20), Kannada-8 50% (4/8), fresh real-Kaanoon 50% (14/28), frozen synthetic Val-500 52.2% (261/500). Target 70%. Net exact matches still needed: Fresh-20 14/20 (+7), Kannada-8 6/8 (+2), Kaanoon-28 20/28 (+6), Val-500 350/500 (+89); Val-500 at 80% = 400/500 (+139).

**Brief inconsistency flagged AGAIN (same two as the first consultation):** (1) Fresh-20 section-level FNs sum to 27, not 28 — one FN unaccounted for. (2) Category breakdown covers 18 questions / 5 exact, not 20 / 7 — two questions omitted. Kaanoon 14/28 Wilson ≈ 32.6–67.4%. Pooled sealed 11/28 = 39.3%, but pooling conceals language differences. Reconcile before the next baseline (plan Phase A, item A7 — still open).

## 3. Q1 — Hybrid vs replacement: REPLACE

Existing architecture behaves as: Issue detected = Neural positive ∧ Regex match, so R_combined ≤ min(R_neural, R_regex). Improving the encoder cannot overcome a missing mandatory anchor.

Ownership boundary: regex owns explicit dates, statute references, deterministic normalisation — never mandatory issue anchors. Classifier owns issues, requested intent, facts, negation, role, contextual meaning — never direct legal-section generation. Calibrated decoder owns mutually exclusive states, evidence aggregation, uncertainty — never inventing missing facts. Graph v4 owns section selection. Renderer owns approved prose.

A regex positive override is permitted only after independent testing (an explicit divorce-section reference does not automatically mean divorce is requested). Acceptance checks: 100% of the 28 fact keys and every required enum/choice input reachable; zero mandatory regex recall gates; any retained override ≥98% observed precision on a dedicated contrast set. Stop expanding bank-specific regex patterns; keep the current system as baseline/rollback only.

## 4. FALLBACK-2 claim 1 — Nine-pass encoding: ADOPT with amendments

Fallback directionally correct, but context and VRAM arguments overstated. At maximum padding 9×288/320 = 8.1, an 87.65% reduction in maximum padded token positions — **not** a proven 87.65% reduction in total VRAM. The original full-question pass still preserves cross-clause context; it is the independently encoded clause representations that lose it. Parameter weights and optimizer states are not replicated nine times; dynamic padding changes the actual token ratio.

Recommended pooling: encode once H = Encoder(x); per clause/span C_j, v_j = Σ α_jt · H_t; z_h = f_h(v_full, v_1, …, v_m). Start with simple head-specific attention pooling, not a large cross-attention network. Whole-question evidence as fallback when clause boundaries are unreliable.

**Critical:** do NOT copy question-level labels onto every clause for local span training — that teaches the model background clauses express requested issues. Use annotated evidence spans or multiple-instance learning.

GPU config: BF16 (after compatibility check); max_seq_len 320 initially; micro-batch test 1, 2, 4, 8; effective batch 16; grad-accum 16/8/4/2; grad checkpointing when needed; AdamW, consider 8-bit optimizer; dynamic padding; truncation diagnostic logging lost evidence spans. mmBERT-base ≈ 307M params, ~197M embedding — memory cannot be inferred from sequence length alone. **Micro-batch 8 is a benchmark target, not a guaranteed fit on 8 GB.** Acceptance: no graph-relevant evidence lost to silent truncation; record peak GPU allocation, tokens/s, examples/s; target ≥2× throughput over nine-pass while maintaining/improving cross-clause diagnostic accuracy. Decision: adopt before the first substantive training run. No need to wait for Neon.

## 5. FALLBACK-2 claim 2 — ASL loss mismatch: ADOPT correction, mandatory before training

Fallback correct on standard binary ASL: independent sigmoids, no mutual exclusivity. Task is multi-label across heads but multiclass within each head (a fact cannot be both supported and denied; contradictory evidence → conflicting state).

Use a four-state softmax per issue/fact: p_h,k = exp(z_h,k) / Σ_j exp(z_h,j). Compare three configs: L1 standard softmax CE (baseline); **L2 class-weighted softmax CE (preferred starting config)**; L3 class-balanced focal CE (challenger). Focal: L_h = −w_h,y (1 − p_h,y)^γ log p_h,y. Search: γ ∈ {0, 1, 2}; β ∈ {0.99, 0.999}; unknown-state relative weight ∈ {0.25, 0.5, 1.0}; max relative class weight ∈ {4×, 8×}; label smoothing 0.0 initially. Class weights per head, normalised before combining head losses — otherwise rare classes in one head dominate the objective.

**Disagreements with the fallback:** the 3-independent-binary-logits alternative (unknown = all below threshold) is NOT preferred — it conflates "question does not establish a fact" with "classifier is uncertain". Keep unknown as a semantic state; track uncertainty separately. Fixed unknown weight 0.25 and 8× cap are not established optima. Weighted losses may improve rare-state recall while worsening calibration. Maintenance/restitution imbalance 2255/118 ≈ 19.11:1 warrants balancing, not indiscriminate oversampling of the same templates. Acceptance: zero invalid state combinations, improved macro-recall across active states, improved section-set exact match; select focal only if it improves grouped OOF over weighted CE without materially degrading rare-state precision. Decision: remove binary ASL from the state heads now; benchmark weighted CE vs focal CE.

## 6. FALLBACK-2 claim 3 — Graph-aware calibration: ADOPT with corrections, highest downstream leverage

Most important mathematical observation in the fallback response. If a section needs two facts jointly, S = A ∧ B, both at 75% recall: R_S = 0.75² = 56.25% (independence); three decisions: 42.19%. But independence must not be assumed — joint recall for two 75% events ranges 50–75% depending on error correlation. Compounding (independent, per-decision recall 90%): 1 decision 90.0%, 2: 81.0%, 3: 72.9%, 4: 65.6%, 5: 59.0%, 6: 53.1%. Recall needed for 70% joint success: 2 decisions 83.67%, 3: 88.79%, 4: 91.47%, 5: 93.11%, 6: 94.23%. This explains respectable per-head metrics coexisting with poor exact section-set accuracy.

**Critical correction — OOF scope:** generate OOF predictions using only the **7,500 training records, not all 8,000**. Including Val-500 in OOF calibration would compromise its frozen evaluation status. Protocol: (1) five grouped folds from Train-7500; (2) group related templates/scenarios/multilingual siblings; (3) train five models, each excluding its fold; (4) collect OOF logits; (5) calibrate multiclass probabilities with shared or head-specific temperature; (6) optimise decoder thresholds against actual Graph v4 outputs; (7) evaluate calibration on excluded outer groups or a separate calibration partition; (8) refit final model, freeze calibration policy; (9) evaluate on untouched Val-500.

Optimise θ* = argmax_θ (1/N) Σ 1[G(D_θ(z_i)) = Y_i], subject to initial precision constraint P_micro,OOF ≥ 0.91. The 0.91 floor is reasonable as a starting constraint — measure the Pareto frontier at 0.88, 0.90, 0.91, 0.93, 0.95; do not treat 0.91 as optimal, and do not let aggregate precision hide critical FPs in individual categories.

**EB shrinkage critique:** τ_h = [N_h+/(N_h+ + 150)]·τ_h^OOF + [150/(N_h+ + 150)]·τ_0 is useful regularisation, but without estimating a prior or its strength from data it is a heuristic shrinkage rule, not necessarily empirical Bayes. At κ=150, a head with 118 positives gets only 44% local-threshold weight (shrunk threshold 0.434), vs ~94% for 2,255. Rare but graph-critical facts may need thresholds far from the shared prior. Use separate priors for issue intent, fact states, enums. Compare κ = 50, 150, 300 on grouped dev data. Both positive and negative support, threshold uncertainty and graph sensitivity matter. Replace the single coordinate-refinement pass with **up to three regularised passes, including paired adjustments for strongly coupled graph inputs** (a single-coordinate optimiser misses improvements needing two thresholds to move together).

Acceptance: target ≥ +3pp OOF exact match over independent per-head calibration, with the precision floor maintained on independent calibration assessment data; smaller gains are inconclusive. Decision: adopt graph-aware calibration; reject fixed κ = 150 and a single coordinate pass as defaults.

## 7. FALLBACK-2 claim 4 — Backbone and Kanglish: ADOPT benchmark, REJECT gate relaxation

Backbone concern valid: broad language coverage does not guarantee competence in Romanised Kannada legal narratives. Licences verified from published model cards: mmBERT-base — MIT; MuRIL-base — Apache-2.0 (Indian-language focus, transliteration-aware pretraining; includes Kannada + translation/transliteration pairs — a particularly relevant challenger, not proven superior on Kanglish); XLM-RoBERTa-base — MIT.

Two-stage benchmark — diagnostics: token fragmentation (median + P95 tokens per whitespace word); length inflation across languages; evidence retention at 320 tokens; negation robustness (minimal positive/negative pairs); graph performance (exact per language); compute (peak VRAM, examples/s). First tokenizer-only diagnostics over Train-7500; then train all three on the same grouped 2,000-example subset with identical exposure, loss, partitions. The 20-minute benchmark is a compatibility smoke test, not enough to establish a reliable winner. Prefer the model with the highest worst-language exact match among comparable candidates; if the difference is < ~3pp, repeat with more seeds/data. Do not assume mmBERT has worse Kanglish fragmentation until tokenization measurements establish it; nor that fewer tokens automatically means better semantics.

**Gate: retain 80% per language.** Statistical justification in §11 below. Decision: adopt the benchmark; reject the proposed relaxation.

## 8. Q2 — Paraphrase augmentation

Next dataset must increase semantic and discourse diversity, not just rewording count. Ranked: 1. Verifier-filtered LLM narrative generation (very high; risk fact/intent drift); 2. Hard-negative mining from classifier errors (very high after first training; risk overfitting dev errors); 3. Targeted semantic perturbations (high; risk inherited labels); 4. More manual templates (moderate; risk template memorisation); 5. EN↔KN back-translation (low as default; risk formal-language bias, drift, licensing). Hard-negative mining becomes the top priority once real OOF predictions exist.

Generation pipeline: generate a structured legal scenario first (issues, facts, roles, timeline, polarity, unknowns), then generate the narrative independently in each language — do NOT simply translate every English record into Kannada/Kanglish. Per record: independent verification pass on all facts/issues; reject records introducing new graph-relevant facts or altering facts unless independently relabelled; require evidence spans for supported/denied facts where explicit evidence exists; permit multiple spans for contextual inference; run frozen Graph v4 on gold labels and check the expected section set; preserve provenance, scenario ID, template-family ID, language-sibling ID; leakage-check without exposing sealed questions to the generator/annotators. Note: the same expected section set does not prove all atomic labels are correct — different extraction errors can cancel at the graph level.

Quality gates: invalid state combinations 0; schema-invalid 0; unreachable required graph inputs 0; confirmed train/eval scenario-family overlap 0; gold labels inconsistent with independently specified sections 0 unresolved; human-audited full-label correctness ≥98% on an audit sample (~300 records stratified across languages + high-risk fact types; record errors by fact/intent, not just pass %).

Template artefacts that cause overfitting: consistent fact ordering (position predicts fact identity); explicit legal terms in every question (keyword dependence); uniform final request sentence (last clause determines intent); unknown facts always omitted similarly (generator style predicts unknown); negation in a few repeated phrases (surface negation detection); all translations preserving English syntax (poor authentic Kannada); fixed issue associations (one issue implies another). Counter by varying chronology, request position, length, vocabulary, speaker perspective, code-mixing, irrelevant background detail.

Back-translation verdict: stop NLLB-200 in the default production path AND the augmentation pipeline (CC-BY-NC-4.0, fails the permissive-only requirement). Prefer directly generated colloquial Kannada/Kanglish. **But the stronger fallback claim — that back-translation systematically corrupts Kannada negation suffixes — is unverified for our corpus; test with bilingual contrast tests rather than accepting it as established.**

## 9. Q3 — Realistic ceiling

Direct verdict: 70% genuinely unseen exact is **plausible with 7,500 training examples, but not the most likely first-training result**. No empirical basis for deriving the trained classifier's ceiling from the existing 52.2% rule-system result. The fallback's projected ranges are possible but too narrow for the evidence.

Planning estimates (subjective, NOT measured outcomes or fitted curves):
- Current untrained extraction: synthetic Val-500 52.2% measured; unseen human 35–50% measured.
- Trained classifier, 7,500 examples: synthetic Val-500 65–80%; unseen human **50–68%**.
- ~12,250 diverse training examples: synthetic Val-500 75–88%; unseen human **60–78%**.

Assumes correct annotations, functioning graph inputs, useful multilingual pretraining, meaningful narrative diversity. Poor label quality or a large synthetic-to-human gap could land below these ranges.

Why exact match is hard: Fresh-20 averages 3.3 required sections/question (66/20). Under a simplified model P(exact) ≈ r^3.3 · q (r = section recall, q = P(no extra sections)): r=0.90, q=0.95 → 67.1%; r=0.92 → 72.1%. Target section recall above 90% while preserving precision. Micro-precision is not interchangeable with the question-level probability of avoiding false positives.

Next-4,750 allocation (total budget retained, redistributed toward conjunctions, overlapping issues, role/scope ambiguity): residence/eviction/protection 1,100; joint property / stridhan distinctions 850; custody/guardianship/welfare 750; divorce/proceedings/decree 600; dense multi-issue narratives 550; scope/negation/role/modality 500; maintenance/interim/enforcement 400. Primary sampling clusters, not mutually exclusive issues; multi-issue labels cross cluster boundaries. Per cluster ~35% EN / 35% KN / 30% Kanglish initially, adjusted by language-specific dev errors. Explicitly cover rare restitution, birth-certificate, procedural, DV-compensation states inside the appropriate contrast clusters. After expansion: ≥100 distinct scenarios per critical active state where feasible — translated duplicates do not count as independent coverage.

Learning-curve decision rules (nested 2k/4k/7.5k, grouped by scenario family, 3 seeds where feasible, separate grouped dev assessment): 4k→7.5k improves ≥5pp → more diverse data likely worthwhile; 2–5pp → expand targeted weak clusters; <2pp → diagnose labels, graph inputs, capacity, domain mismatch before expanding; synthetic improves but human proxy stagnates → prioritise narrative realism; individual heads improve but graph exact does not → prioritise joint decoding/calibration. These thresholds are not statistically significant findings without paired uncertainty estimates. No justification yet for 20,000 records or a much larger backbone.

Fallback ceiling verdict: its 56–62% first-training unseen estimate is reasonable as a planning midpoint; its 72–78% post-expansion estimate is achievable in principle but too narrow and optimistic to adopt as an expected outcome.

## 10. Q4 + Q5 — Missing failure modes and classifier diagnostics

Highest-risk failures (failure — detection — mitigation): dead graph inputs (reachability + oracle replay); multi-issue suppression (isolated vs combined narratives); request vs background confusion (requested/incidental contrast pairs); cross-clause claimant confusion (role-swap, pronoun/pro-drop tests); Kannada negation morphology (native minimal-pair tests); Kanglish spelling variability (multiple transliterations of same scenario); hypothetical vs actual event (modality contrast tests); temporal confusion (pending/completed/future proceeding pairs); correlated graph failures (joint recall of graph prerequisites); template-family leakage (grouped vs random split); silent failures (count in-scope empty-section outputs).

**Most important missing failure: fact binding.** The schema has facts and enums, but an atomic fact can have different subjects, objects, events and times — e.g. two proceedings (past + current), or one person's demand alongside another person's property. Extracting proceeding_pending = 1 AND demand_made = 1 does not establish both refer to the legally relevant event/claimant. Recommendation: internal Stage 0/1 evidence representations containing subject, event, polarity, time and evidence span; resolve these into the graph's existing input schema before calling Graph v4. This does NOT require changing the graph.

**Oracle extraction replay (before spending GPU time):** run Y_oracle = G(gold issues, gold facts, gold enums); compare with independently annotated expected section sets; target 100% oracle exact on internally validated, representable scenarios. If the oracle fails, determine whether the cause is an annotation error, an input-schema limitation, or a genuinely unreachable graph branch. If two questions need different correct section sets but have identical valid input representations, no classifier can resolve that distinction while the graph/interface stay unchanged — the strongest check against the brief's assumption that the problem lives entirely in Stage 0/1. **Warning:** if existing synthetic section labels were generated by the same graph, replay is necessary but tautological — an independently annotated scenario set is required for a meaningful oracle test.

**Negation / hypothetical / third-party gating — amend the proposed clause veto substantially.** A hypothetical clause is not necessarily irrelevant: a user asking about a future remedy can express a real requested intent without asserting the future event happened. Someone asking on behalf of their sister can still be making a genuine legal request. Separate three decisions: (1) Is the issue requested? — intent head. (2) Has the relevant event occurred? — fact-state and modality heads. (3) Who does it concern? — role and evidence binding. Do not apply one generic gate across these. For pooling, use soft relevance weighting first: a_hj = p_hj(relevant evidence); u_hj = a_hj · p_hj(requested) — candidate evidence scores, not calibrated joint probabilities. Aggregate with the full-question representation and calibrate after fusion. Hard vetoes only where a specific interpretation has been independently validated. A 0.95 threshold on a poorly calibrated gate does not guarantee 95% correctness. Calibrating max(full, cmax) must account for span count — more spans mean more chances for an erroneous high maximum.

Named diagnostic targets (proposed engineering acceptance thresholds, NOT measured LAYA performance): multi-issue recall retention vs isolated requests ≥95%; negation contrast-pair accuracy ≥95%; role-binding contrast accuracy ≥95%; requested-hypothetical recall ≥90%; irrelevant-hypothetical FP rate ≤5%; Kanglish spelling-variant prediction agreement ≥90%; gate-induced loss of genuine requests ≤1%; silent in-scope failure rate ≤1%. Use independently authored contrasts with adequate coverage.

Training defaults: backbone = benchmark winner; encoder lr 1e-5 to 3e-5; head lr 5e-5 to 1e-4; epochs 3–6 with early stopping; warmup 5–10%; weight decay 0.01; dropout 0.1; gradient clipping 1.0; label smoothing 0.0; loss = weighted softmax CE baseline; seeds = 3 where practical; model selection = grouped dev graph exact match constrained by precision. Most dangerous training mistake: incorrect supervision of rare and context-dependent states, then scenario-family leakage, then excessive repetition of synthetic patterns. A model can learn a perfectly consistent wrong mapping if every generated narrative expresses the same annotation shortcut.

## 11. Q6 — Evaluation design and the 80% gate

Val-500 is useful for synthetic-domain progress and inadequate as the sole predictor of unseen human-question accuracy. A frozen random split is not necessarily an independent distribution if train/val share templates, scenarios, generator styles or multilingual siblings. Zero 8-gram overlap and max cosine 0.8269 are useful leakage safeguards; they do not prove semantic independence. Keep Val-500 frozen, audit its provenance, build an additional grouped dev evaluation if related families cross the split. Do not retroactively replace Val-500 and present the new result as comparable.

Evaluation hierarchy: Graph oracle (representability/label consistency) 100% on validated scenarios → Grouped training OOF (architecture/calibration selection) ≥75% exact initially → Val-500 (frozen synthetic checkpoint) ≥80% exact → Named contrast diagnostics (thresholds in §10) → Human-300 (independent pre-sealed) ≥80% exact per language → Original sealed sets (final product-target) ≥70% exact. OOF and synthetic thresholds are development targets, not substitutes for human or sealed outcomes.

**Why the relaxed gate is rejected — two-sided 95% Wilson intervals:** 70/100 (70%) → 60.4–78.1%; 75/100 (75%) → 65.7–82.5%; 80/100 (80%) → 71.1–86.7%; 225/300 (75%) → 69.8–79.6%; 226/300 (75.33%) → 70.2–79.9%. The fallback's 75% overall / 70% per language allows one language to pass while its estimated accuracy has a lower confidence bound of only 60.4%. The original 80/100-per-language gate is substantially more defensible for a 70% product target — it gives a marginal 95% Wilson lower bound above 70% per language (assuming independent representative questions). It does not give a simultaneous 95% guarantee across all three languages; a more conservative simultaneous gate would need ~81/100 per language (Bonferroni-adjusted Wilson). **Retain 80% per language as the operational gate.** The gate disagreement is now RESOLVED: both ChatGPT consultations agree on 80%; the Hydrogen relaxation is rejected with statistical reasoning.

Human-300 build: 100 independently authored questions per language — do NOT treat translations of the same 100 scenarios as 300 independent observations. Suggested composition per language: ordinary single-issue requests 35; multi-issue narratives 25; indirect/colloquial requests 15; negation/scope/role/modality contrasts 15; out-of-scope and genuinely ambiguous 10. Cover all 11 issues. Authors work from the statutory task specification, not existing banks, observed classifier mistakes or sealed-set distributions. Two independent annotators establish gold issues/facts/sections; disagreements adjudicated by a qualified reviewer. Do not inspect Human-300 errors to repeatedly optimise the model and then reuse it as an independent release gate — it then becomes development data and a fresh confirmation set is needed. Real-Kaanoon-28 is a useful external signal; since its aggregate is already known and influencing design, treat it as supplementary, not the sole pristine release test.

Final go/no-go metrics: Human-300 exact ≥240/300; EN ≥80/100; KN ≥80/100; Kanglish ≥80/100; micro section precision ≥0.91; micro section recall ≥0.92; in-scope silent failures ≤1%; critical graph-input reachability 100%; unresolved invalid state combinations 0; dangerous section FPs separately reviewed, no unresolved critical failures. Exact section-set match stays the primary go/no-go; precision/recall/category exact are diagnostic/safety guardrails. Do not exclude silent answers, uncertain predictions or unsuccessful out-of-scope classifications from the exact-match denominator. A correct empty section set for a genuinely out-of-scope question differs from an erroneous empty answer to an in-scope question.

Limitation of the final sealed sets: even at minimum passing counts — Fresh-20 14/20 (70%) → Wilson 48.1–85.5%; Kannada-8 6/8 (75%) → 40.9–92.9%; combined 20/28 (71.4%) → 52.9–84.8% — the requested ≥70% sample accuracy is measured, but population accuracy ≥70% is NOT statistically established. Neither sealed set measures Kanglish; the Human-300 gate partly addresses that.

## 12. Ranked implementation plan

P0 Oracle replay, dead-key and schema audit — Stage 0/1 + evaluation — all required inputs reachable; oracle errors resolved
P1 Remove mandatory regex gates — Stage 1 — zero anchor-based recall vetoes
P2 Implement one-pass contextual pooling — Classifier — correct evidence alignment; GPU benchmark passes
P3 Replace binary ASL with multiclass CE — Classifier — mutually exclusive valid states
P4 Benchmark mmBERT, MuRIL and XLM-R — Classifier — select by grouped multilingual results
P5 Train 2k, 4k, 7.5k learning curve — Training — measured performance and error slices
P6 Build graph-aware OOF calibration — Decoder — improved exact match with precision constraint
P7 Mine errors and expand by up to 4,750 records — Corpus builder — verified semantic and cluster diversity
P8 Run Human-300 — Evaluation — ≥80% in each language
P9 Run original sealed evaluation — Evaluation — ≥70% measured exact
P10 Distil and optimise CPU latency — Production — below 0.5 seconds without material accuracy loss
Human-300 authoring can proceed in parallel, provided its contents are isolated from the model-development team. For distillation, use both hard labels and calibrated teacher distributions, and evaluate the distilled model through the entire graph — fast inference is useless if distillation removes rare graph-critical facts.

## 13. Stop list (additions to the adopted list)

Stop bank-specific regex hardening (230/230 is no longer a useful optimisation objective). Stop treating 52.2% as a trained classifier learning-curve point. Stop treating synthetic validation accuracy as equivalent to human-question accuracy. Stop tuning thresholds repeatedly against Val-500 or including its records in OOF calibration. Stop generating thousands of near-identical variations before measuring the first classifier's actual errors. Stop using question-level labels as unconditional clause-level labels. Stop applying hypothetical and third-party vetoes indiscriminately. Stop assuming mmBERT wins because its pretraining covers more languages. Stop treating high micro-precision as proof that every legal category is safe. Stop architectural expansion, larger-model experiments and latency optimisation until the extraction baseline is established.

## 14. Final disposition of [FALLBACK-2] (per this consultation)

Claim 1 — Single-pass contextual encoding: **Adopt now.** Correct the VRAM estimate and benchmark the actual feasible batch size.
Claim 2 — ASL mismatch: **Adopt now.** Mutually exclusive softmax heads; weighted CE as baseline, focal CE as challenger.
Claim 3 — Graph-aware threshold calibration: **Adopt now.** Restrict OOF to Train-7500, validate shrinkage strength, account for coupled decisions.
Claim 4 — Backbone benchmark and evaluation relaxation: **Adopt the benchmark. Reject the gate reduction.**
Ceiling projection: treat as a plausible engineering hypothesis, not an empirical forecast.

## 15. Overall assessment

Current measured real-question exact: 50% (Kaanoon-28). First trained classifier planning range: 50–68% (estimate, not measured). Post-expansion planning range: 60–78% (estimate, not measured). Independent human pre-sealed gate: 80% required per language.
The Hydrogen fallback identified three genuine architectural weaknesses and one legitimate backbone-selection concern. Its proposed remedies are mostly sound, but its numerical forecasts, memory assumptions and evaluation-gate relaxation require correction.
**You do not need to wait for Neon before proceeding.** The unresolved questions are now primarily empirical: which backbone generalises best, which loss balances rare states most effectively, and whether graph-aware calibration closes the synthetic-to-human accuracy gap.
Consultation limited to the supplied brief and publicly documented model information. No repository, corpus, graph, or sealed questions inspected; no classifier training executed. All hyperparameters, sampling allocations and forecast ranges require experimental confirmation.
Final recommendation: complete the oracle and schema audit, adopt single-pass contextual pooling and multiclass state heads, and train the existing corpus before generating more data. The next major milestone should be a measured classifier learning curve — not another consultation, regex-hardening swarm, or unvalidated accuracy projection.

## 16. Synthesis note (Muse, checked against our own numbers)

Adopted from this re-run into the 70% plan (marked [GPT-RERUN]):
1. **Gate disagreement RESOLVED: 80% per language stays.** Both ChatGPT consultations agree; the Hydrogen relaxation is rejected on Wilson-interval grounds (80/100 → lower bound 71.1% vs 70/100 → 60.4%). The Neon re-run (scheduled 28 Nov ~00:15 IST) is now a completeness check, not a blocker — ChatGPT's verdict is explicit that proceeding does not need to wait for Neon.
2. **Loss: weighted CE is the baseline, focal CE the challenger** — the plan's [FALLBACK-2] adoption of focal CE as the design is amended to a benchmark between the two.
3. **OOF on Train-7500 only** — the plan's "OOF on all 8,000" is corrected; Val-500 must never enter calibration.
4. **κ = 150 is a hyperparameter, not a default** — compare 50/150/300 with separate priors per head family; up to 3 regularised coordinate passes (incl. paired adjustments).
5. **mmBERT-base is not the predetermined winner** — benchmark mmBERT vs MuRIL vs XLM-R (base) on a grouped 2k subset before committing; MuRIL is a serious challenger for Kanglish.
6. **Fact binding is a new P0 item** — internal evidence representations carry subject/event/polarity/time/span; resolve to the graph schema before Graph v4.
7. **Oracle replay is P0, with the tautology warning** — meaningful only on independently annotated scenarios, not on graph-generated labels.
8. **Clause veto amended** — hypothetical/third-party language is not automatically out-of-scope; soft relevance weighting first, hard vetoes only where independently validated; never copy question-level labels onto clauses (spans or MIL).
9. **Back-translation negation-corruption claim is UNVERIFIED** — test with bilingual contrasts; do not treat as established.
10. **Phase C allocation redistributed** (total still ~4,750): residence 1,100; joint/stridhan 850; custody 750; divorce 600; dense multi-issue 550; scope/negation/role/modality 500; maintenance 400.
11. **Ceiling ranges widened:** first trained classifier 50–68% unseen; post-expansion 60–78% (planning ranges, not forecasts). Hydrogen's 56–62% is a reasonable midpoint; 72–78% too narrow/optimistic.
12. **Brief inconsistency re-flagged a second time** — A7 reconciliation still open; both ChatGPT consultations caught the same two discrepancies.
