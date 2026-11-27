# LAYA v7.1 — Deep Plan to Reach >70% Exact on Unseen Questions

- **Target (user, 2026-11-27):** minimum **70% exact** on unseen law-related questions. "Win rate" in this plan = exact-match rate: the full predicted section set must match ground truth exactly, per question.
- **Status:** plan written 2026-11-27 ~21:00 IST. This is a plan, not a result. **No claim of ≥70% is valid until a real run on the sealed sets measures it.**
- **Sources this plan is built on (all verified, none invented):** recall swarm final tracker (`docs/recall_status.md`, update 6 FINAL, HEAD `f92a9e5`); Gemini consultation (`files/laya-graph/gemini-recall-consultation.md` — Hydrogen fallback, NOT Neon; Neon re-run still owed); ChatGPT consultation (`files/laya-graph/chatgpt-recall-consultation.md` — GPT-6.2, thinking max); the both-model synthesis at the end of the ChatGPT file.
- **Working copy:** `~/workspace/laya-v71-work`. All file paths below are relative to it unless stated otherwise. All paths were verified to exist on 2026-11-27 before this plan was written.

## 0. Where we are — measured baselines (the floor this plan starts from)

| Set | Exact | What it is | When / how measured |
|---|---|---|---|
| Synthetic held-out, frozen split (500) | **261/500 = 52.2%**, Wilson 95% CI [0.4782, 0.5654] | Only progress metric until the sealed re-run. Split frozen, sha256 `7640d067c28abf539131dbcc891e4bdffedf62bbef4a7d66c1659bb96d07e58e` | Recall swarm final, HEAD `f92a9e5`, Lane 10 re-verified |
| Kaanoon fresh eval (28 real questions) | **14/28 = 50.0%**, Wilson [0.3263, 0.6737] | Real Kaanoon family-law questions, evaluation only, disjoint from train (0 shared 8-grams) | Recall swarm final, Lane 11 + Lane 09 verified |
| Sealed Fresh-20 (English) | **7/20 = 35%** | Sealed, never opened beyond aggregates | v7 live run (RTX 5050) |
| Sealed Kannada-8 | **4/8 = 50%** | Sealed, never opened beyond aggregates | v7 live run (RTX 5050) |
| Brutal-230 (known bank) | **230/230 = 100%** | Already-known adversarial bank — NOT the target | v7 live run |
| 16-question regression | **14/16 = 87.5%** | Frozen regression set | Recall swarm final, no regression |

- Gap to close: **52.2% → >70% on the frozen synthetic split, and 35% → 70% (14/20) on Sealed Fresh-20, 50% → 75% (6/8) on Sealed Kannada-8.** The sealed sets are small; even a pass there does not prove a population-level 70% (ChatGPT §6 — disclose this when reporting).
- Supporting numbers: frozen-split micro-P/R/F1 0.8905 / 0.4623 / 0.6086, TP/FP/FN 423/52/492, silent 212/500. The failure is recall, not precision — the system almost never invents a wrong section; it misses sections.
- Top failure clusters (Fresh-20 FNs, 28 total): hma-27 4; welfare-principle 3; pwdva-17/18/19 3 each; hma-13 2; hma-24 2; gwa-1890 2; hmga-1956-s6 2; hma-25, bns-316, hma-26 1 each. Categories at 0/x: divorce 0/2, residence 0/2, stridhan 0/3.
- **Known inconsistency to reconcile first (ChatGPT §8):** the consultation brief's Fresh-20 category breakdown sums to 18 questions / 5 exact and itemised FNs sum to 27, not the reported 20 / 7 / 28. Headline aggregates (7/20, 38/5/28) are internally consistent. Two exact questions are unaccounted for in the breakdown. Reconcile against the sealed aggregates (without opening sealed text) before the next evaluation report — see Phase A, item A7.

## 1. The adopted decision (both consultations, checked against our own numbers)

1. **Replace Stage 1 extraction outright with the multi-head neural classifier.** Regex never gates, filters, or vetoes neural output again. Regex survives only as post-classifier evidence: explicit statutory citations, dates, amounts, and hard numeric/temporal parsers.
2. **Backbone: `jhu-clsp/mmBERT-base` (MIT, 307M, 1,833 languages) is the primary candidate.** English-only ModernBERT-large / DeBERTa-v3-large are rejected as the default — both models independently called this a fatal flaw for Kannada, and our own Kannada-8 numbers (recall 0.70 vs precision 1.00) are consistent with an English-centric encoder. Comparison backbones: `FacebookAI/xlm-roberta-large` (Gemini) and `microsoft/mdeberta-v3-base` (ChatGPT). Verify the exact checkpoint revision and licence before production use.
3. **Train the existing 8,000 first, with a nested learning curve (2,000 / 4,000 / 7,500), before deciding on expansion.** The models disagree on whether 8k alone can reach 70% (Gemini: no, plateaus 58–66% EN; ChatGPT: plausibly yes, 60–75% if diverse). Settle it by measurement, not opinion.
4. **The 500-record synthetic validation split is never the sole gate again.** It measures in-distribution fit only. The pre-sealed gate is a fresh independent human-written holdout (Phase D).
5. **Graph v4 and the prose renderer stay frozen.** No modification of Graph v4 to compensate for extraction errors.

## 2. Phase A — Pre-training gates (do all of these before Run #1; no training until every gate passes)

All work in the working copy. Each item has a file, an owner type, and a pass/fail check.

| # | Gate | What to do | Pass check |
|---|---|---|---|
| A1 | **Dead fact keys + graph contract** | Audit all 28 fact keys + 3 enum heads against Graph v4's exact input dictionary. Every key the graph reads must have a defined producer in Stage 0/1 (explicit head or deterministic derivation). The 8 dead keys found by the 10x swarm (Lane 01) must be closed. Files: `src/laya_v7_classifier.py`, `src/laya_v7_graph.py`, Stage 0/1 adapter. | 100% of graph input keys covered. 0 dead keys in the schema check. |
| A2 | **Graph oracle** (ChatGPT §4.1 — new, was not in the swarm plan) | On independently annotated dev examples, run four configurations: gold issues + gold facts → Graph; gold issues + predicted facts; predicted issues + gold facts; predicted issues + predicted facts. Gold section labels must come from independent annotation, never generated from Graph v4 itself (circular). | 100% section exact on unambiguous in-scope examples with gold inputs. If the gold-input oracle fails, the recall problem is NOT entirely in Stage 0/1 — record it as a system ceiling under the frozen-graph constraint; do not hide it with incorrect fact predictions. |
| A3 | **Clause supervision audit** (ChatGPT §5.5, ranked #1 danger) | Audit `src/laya_v7_classifier.py` + `scripts/train_v71_classifier.py`: never assign question-level labels to every clause. Use the existing spans to assign local supervision where supported; where clause-level labels are unavailable, mask that loss and rely on question-level supervision. | Audit report lists every clause-loss site and its supervision source; 0 sites assign question labels to all clauses. |
| A4 | **Backbone swap + tokenizer audit** | Change the default backbone in `src/laya_v7_classifier.py` to mmBERT-base. Compare tokenizer fragmentation, truncation, and extraction performance across English / Kannada / Kanglish before committing. Verify checkpoint revision + MIT licence. | Tokenizer audit table (3 languages) filed; mmBERT-base selected or the comparison winner named with reasons. |
| A5 | **Grouped validation split audit** (Gemini flaw #3; ChatGPT §4.4) | Verify the 7,500/500 split was grouped by template_family_id / grammar_rule_id (or scenario family), not row-level. Audit the frozen split's provenance: shared templates, scenario families, grammar rules, label combinations, translation siblings across train/val. | Split audit filed. If related scenario families cross the split, record the limitation and create an additional genuinely group-disjoint development set. Do not use the sealed-bank similarity index repeatedly as a training-data optimisation feedback loop. |
| A6 | **VRAM smoke test (RTX 5050, 8 GB)** | Before training: forward/backward smoke test with the real config (bf16, gradient checkpointing, dynamic padding, max_seq_len 288). Record peak GPU memory. Verify loss decreases on a small debugging subset. Verify no annotated requested issue/fact is removed by truncation in the diagnostic corpus. Both models independently computed 36 sequences/step at batch 4 — that OOMs in fp32. | Peak memory <6.5 GB (Gemini gate) with the adopted config; truncation events recorded (0 annotated labels lost). |
| A7 | **Brief inconsistency reconciliation** | Reconcile the Fresh-20 category breakdown (18 questions / 5 exact / 27 FNs) against the headline aggregates (20 / 7 / 28) using only logged aggregates — sealed text is never opened. | Written reconciliation filed before the next evaluation report; the two unaccounted exact questions explained or flagged as a reporting error. |

- **Phase A exit rule:** training starts only when A1–A7 all pass. A failure in A2 (oracle) does not block training, but it changes the plan: the ceiling is recorded and Phase B's target is re-scoped (see §9).

## 3. Phase B — Training Run #1 (RTX 5050 only; this VM has no GPU/torch)

- **Exact commands:** see `docs/recall_swarm_state/lane-04-classifier.md` (Lane 04: training prep, PC-2 vocab pin, LoRA fix, RTX doc). Do not invent commands; run Lane 04's documented commands and update them for the mmBERT-base swap + the config below.
- **Config (both models agree, with ChatGPT's sequencing):** backbone mmBERT-base; BF16 mixed precision; micro-batch **1 question**; gradient accumulation **8** (effective batch 8 questions); lr 2e-5; max epochs 5; checkpoint evaluation every 0.5–1 epoch; gradient clipping 1.0; warmup 5–10%; gradient checkpointing + dynamic padding; memory-efficient AdamW if needed; max_seq_len **288** (Kannada subword fertility ~2.3× English; 192 truncates multi-issue Kannada queries). If full fine-tuning does not fit, use parameter-efficient fine-tuning or partial layer freezing as a controlled alternative — never silently discard information beyond 192 tokens or 8 clauses; record truncation events, use overlapping windows/overflow processing.
- **Loss:** Asymmetric Loss (ASL: γ−=2, γ+=0, margin clip m=0.05) or class-weighted focal with positive weights capped at min(4.0, N_neg/N_pos), normalised within each loss group. Loss decomposition (starting weights, each group normalised separately so the 28 fact heads do not dominate the 11 issue heads): L = L_issue + L_fact + 0.5 L_enum + 0.5 L_clause + 0.2 L_span. **Label smoothing = 0.0** (both models agree; smoothing compresses rare-head logits). Class imbalance is real: maintenance 2,255 requested vs restitution 118 (~19:1) — unrestricted inverse-frequency weighting overcorrects; use capped weighting + targeted augmentation.
- **Nested learning curve (ChatGPT §3):** train subsets of **2,000 → 4,000 → 7,500** examples first, plot independent development performance vs sample size. **Decision rule:** if the curve has already flattened below the target, adding more of the same data will not solve it — go to Phase C with LLM-diversified data (not more templates), or re-examine the backbone.
- **Fusion (adopted):** keep full-question + clause max-pooling as the baseline: s_i = max(p_i^full, m_i), m_i = max_j c_ij. Calibrate the fused score — do not treat the raw maximum as a calibrated probability. Watch the multiple-comparisons problem (ChatGPT §5.2: a 5% per-clause FP rate becomes 33.7% at 8 clauses); if FPs appear on longer questions, compare against the learned fusion z_i = b_i + w1_i z_i^full + w2_i max_j z_ij + w3_i log(1+n); p_i = σ(z_i). Architecture upgrade (Gemini §5a): single-pass packed sequence with [C_SEP] clause boundary tokens + span-attention pooling — 1 sequence per example instead of 9 (~9× VRAM saving), clauses keep full-sentence context for coreference, negation stays clause-scoped.
- **Veto / gating (adopted):** no generic clause-level veto. Polarity and modality are per-issue/per-fact, via the four-state intent head. Soft gating only: c~_ij = c_ij (1 − g_ij), where g_ij = probability that the particular issue evidence is non-asserted/non-requested. Hard suppression only when evidence is confidently non-requested (initial confidence 0.95), scope unambiguous, and no independent affirmative evidence is suppressed. Do not treat third-party or hypothetical language as automatically out-of-scope (a parent asking about a child's rights, or a prospective remedy, can still have valid legal intent). Gemini's margin variant (penalty only when p_veto ≥0.75 AND p_veto − p_req > 0.25) is an acceptable implementation of the same rule — pick one, document it, and measure the gate diagnostics below.
- **Thresholds (adopted):** per-head thresholds via **5-fold out-of-fold (OOF) predictions on all 8,000 records** (not 500), then Empirical Bayes shrinkage toward a recall-biased global threshold: τ_k = [n_k+/(n_k+ + κ)]·τ_k* + [κ/(n_k+ + κ)]·τ_global, κ = 30–50 (Gemini 30, ChatGPT 50 — evaluate both, keep the one with better OOF micro-F_1.75), clipped [0.22, 0.75]. τ_global maximises micro-F_β=1.75 (recall weighted 3×). Temperature scaling first (single scalar T on validation NLL). Heads with <~20 positive calibration examples keep the shared threshold. Optimise downstream Graph v4 exact match subject to precision/recall constraints — never micro-F1 alone.
- **Early stopping:** linear warmup + cosine decay, weight decay 0.02, dropout 0.15 on classification heads; early stopping on Blind Stress Set / grouped-val micro-F_1.75 (typically peaking at epoch 3 — do not run all 5 epochs blindly).
- **Phase B acceptance gates (all must pass to proceed to Phase C as a "good baseline"):**
  - Frozen synthetic validation: micro-R ≥0.90, micro-P ≥0.92, exact ≥0.78 (Gemini P3 gate — note this is in-distribution; it is a sanity gate, not the 70% proof).
  - Silent failure rate <1% on validation (in-scope questions with zero sections).
  - Gate diagnostics: FN rate introduced by gating ≤2%; positive sibling-clause retention ≥98%; same-clause mixed-polarity accuracy ≥95%; explicit denial suppression ≥95%.
  - Combined-question requested-issue recall ≥92%; recall drop after combining issues ≤5pp; negation minimal-pair accuracy ≥95%; claimant-role accuracy ≥95%; mention-vs-request accuracy ≥95%; graph input contract coverage 100%.
  - 16-Q regression: still 14/16 (no regression). Frozen hashes intact. Unit suite green.
  - **If Run #1 fails these gates:** do not expand the corpus yet. Diagnose by head (per-head recall/precision), by cluster, and by language slice — then fix the specific failure (backbone, supervision, gating, or thresholds) and re-run.

## 4. Phase C — Error mining + targeted expansion (only after Run #1 is measured)

- **Hard-negative mining (rank 2 in both models):** run Run #1 on the independent holdout / Blind Stress Set (once built in Phase D — build it in parallel with Phase B), collect errors, cluster them, generate targeted contrastive minimal pairs (custody vs residence, divorce_asked vs being_filed, stridhan vs joint property, mentioned vs requested). Do NOT repeatedly mine and retrain on the frozen 500-record validation set — that converts it into another known bank.
- **LLM-diversified paraphrases (rank 1 in both models):** generate from abstract legal scenarios (fact tuples), never by rewriting template sentences and never from sealed questions. Pipeline: scenario spec → natural question generation (layman narratives, indirect requests, emotional language, incomplete sentences) → independent label extraction (second LLM prompt re-extracts issues/facts/roles/spans) → semantic consistency verification (reject label drift, ambiguous references, contradictory facts) → deduplication + grouped partitioning (scenario families and paraphrase siblings stay together) → approved corpus with provenance, generator version, labels, verification status. Leakage gates: 0 8-gram overlap and cosine <0.80 vs the blind test hash index and the validation/stress sets; character-trigram diversity <0.55 across paraphrases of the same seed. 3-step label filter (Gemini): reverse-extraction check → Stage-2 Graph v4 equivalence check → lexical ban-list rotation (for 40% of prompts, forbid the canonical English legal term to force lay-register phrasing). Manual audit: stratified sample ≥300 records, target ≥98% label correctness, zero critical polarity or claimant-role errors. Use only generation models/services whose licences/terms permit the training use.
- **Next-4,000 allocation (union of both models' allocations, weighted to the top two clusters both models agree on):**

| Cluster | Records | Why (FN evidence) |
|---|---|---|
| Residence & coercive lockout (pwdva-17/18/19) | 1,100 | 12 combined FNs; non-violent lockout, in-laws blocking entry, constructive eviction, shared household without explicit violence, residence after separation |
| Joint property & Stridhan (hma-27, bns-316) | 900 | 5 FNs; stridhan 0/3 exact; co-owned flats/plots/savings, wedding gold held by in-laws, blurred joint-property vs stridhan, gold kept "for safekeeping" |
| Child custody & welfare (welfare-principle, gwa-1890, hmga-1956-s6, hma-26) | 900 | 8 combined FNs; implicit minor-child mentions ("my 3-year-old", "school-going daughter"), welfare triggers without explicit "custody" wording |
| Divorce stage & ancillary relief (hma-13, hma-13b, hma-24, hma-25, hma-9) | 700 | 5+ FNs; divorce 0/2 exact; interim maintenance vs permanent alimony, mutual consent vs contested, restitution |
| Maintenance / enforcement / compensation | 450 | ChatGPT allocation; arrears, variation, enforcement |
| Dense multi-issue single-sentence queries (<25 words, 3–4 facts) | 400 | Breaks the length-to-label shortcut; English + Kanglish |
| Scope / negation / third-party narratives | 300 | ChatGPT allocation; denied, hypothetical, third-party, quoted text |
| **Total** | **~4,750** | Target 40% English, 30% native Kannada, 30% Kanglish; ≥40% multi-issue; minimal-pair counterexamples across all six clusters |

- **Upstream fact fan-out (Gemini Q4.1 — the highest-leverage training fix):** Graph v4 fans one upstream fact into 2–3 sections; missing 5 upstream facts explains ~70% of all FNs. Weight training loss and threshold selection by fan-out degree: facts unlocking ≥2 sections get 1.5× positive loss weight and lower activation thresholds. Log fact-level recall on Stage 1 outputs before Graph v4 runs, grouped by downstream section fan-out. The five high-fan-out triggers to gate individually (recall ≥0.88 each): joint_property, coercive_eviction_or_lockout, residence_claim, custody_claim, minor_child.
- **Kannada/Kanglish specifics:** deterministic Kannada↔Kanglish transliteration augmentation (indic-transliteration / Aksharamukha rules, Apache-2.0/MIT) so every Kannada example also appears romanised; claimant_sex/role prior from kinship nouns when pronouns are dropped; slice all metrics by language (en/kn/kanglish) and inspect sex/role enum recall on Kannada; parallel-language diagnostic with the same scenarios in all three languages — targets ≥90% cross-language section-set agreement, ≥90% recall per language, max recall difference 5pp.
- **Phase C exit:** re-train (Run #2) on 8,000 + new records and re-measure on the independent holdout (Phase D). The decision to expand further (toward 12–15k) comes only from the measured holdout curve.

## 5. Phase D — Independent human-written holdout (build in parallel with Phase B; never used for training or tuning)

- **What:** 300 questions, 100 per language (English / Kannada script / Kanglish), fictional questions by bilingual contributors + independent legal annotators. (Gemini's 250-item Blind Human-Register Stress Set is the same idea at a smaller size; this plan adopts ChatGPT's 300/100-per-language version because its ≥80% per-language gate has a stated statistical basis: an observed 80/100 gives a two-sided 95% Wilson lower bound of 71.1%, vs 60.4% for 70/100.)
- **Build protocol:** sample target (issues, facts, enums) tuples stratified across all 11 issues (minimum 20 positives per issue, 15 per rare fact like hma-27 and coercive_eviction_or_lockout, plus 30 hard negatives/out-of-scope). Authors write realistic, messy, colloquial layperson questions from bare Stage-2 fact tuples — never from synthetic templates, never from sealed questions, and never with a category distribution designed to imitate the sealed banks. Authors must not see the training templates. Ground-truth annotators must not see classifier predictions. ≥2 independent annotators review the legal outputs; disagreements adjudicated before evaluation.
- **Purity:** 0 8-gram overlap and cosine <0.80 vs synthetic_v7_1 and the sealed blind hash index; dual-annotator Graph v4 label verification on 100% of items.
- **Pre-sealed go/no-go gates (ALL must pass before any sealed GPU run is spent):**
  - Independent holdout overall exact ≥80% (target ≥80% per language — English, Kannada, Kanglish each).
  - Micro-R ≥0.90 and micro-P ≥0.92 (micro-F1 ≥0.91).
  - Top-FN upstream fact recall ≥0.88 individually on joint_property, coercive_eviction_or_lockout, residence_claim, custody_claim, minor_child.
  - Silent failure rate ≤1.0% and out-of-scope / negated-clause FP rate ≤5.0%.
  - Graph oracle exact 100% on supported, unambiguous cases.
- **Lock rule:** if the holdout is used for model selection or threshold tuning, it ceases to be a locked holdout — a fresh independent final evaluation is then required. Keep the holdout completely untouched by model developers and the training pipeline.

## 6. Phase E — Sealed re-run (RTX 5050 or Colab; never on this VM)

- Only after Phase D's gates pass. Freeze the checkpoint first.
- Re-run **Sealed Fresh-20** (target 14/20 = 70%, net gain of 7) and **Sealed Kannada-8** (target 6/8 = 75%, net gain of 2). Combined 20/28 = 71.43%.
- **Disclosure rule (ChatGPT §6):** the aggregate sealed results have already informed development priorities — disclose that adaptive exposure when reporting the eventual sealed re-run. The sealed sets are too small to establish a population-level 70% guarantee with strong statistical confidence, and neither sealed set establishes Kanglish accuracy — say so in the report.
- Also re-run: Brutal-230 (must stay 230/230), 16-Q regression (must stay 14/16), latency (mean per-question time vs the 15 s gate — GPU run only), and the full unit suite.
- **Claim rule:** >70% is claimed only if the sealed re-run measures it. A holdout pass is not a sealed pass.

## 7. Phase F — Distillation + latency (only after >70% is measured)

- Distill the teacher to `jhu-clsp/mmBERT-small` (MIT, 140M) or ONNX INT8 mmBERT-base for <0.5 s CPU latency.
- Gate: CPU p95 latency <350 ms/query with ≤1.5% exact-match drop vs the teacher (Gemini P5 gate). Do not do latency work before accuracy is established (both models' stop lists).

## 8. Human gates & owners

| Gate | Who | Status |
|---|---|---|
| 300-item holdout authors (bilingual contributors) + ≥2 independent legal annotators | Humans — not yet recruited | **Open, blocks Phase D** |
| Ground-truth-v3 ratification (independent human rater; HMA 27 D1-A re-base) | Human rater | **Open since the 10x swarm** |
| G12 blind legal rater; P2.1 native Kannada sign-off; P2.4/P2.5 legal verification | Humans | **Open** |
| RTX 5050 training runs (Run #1, Run #2, sealed re-run) | User's machine (Nivedh) | **Open — nothing here can run them** |
| T4 GPU parity / latency gate | Colab or RTX | **Open** |
| Final >70% claim | Measured sealed re-run only | **Not claimed** |

- **What agents can do without humans:** Phases A (except A2's independent annotation), B-prep (code, config, smoke-test scripts), C's generation pipeline code, D's build tooling. **What agents cannot do:** train, run sealed sets, write the holdout questions as if they were independent humans (authors must be real contributors, not the training pipeline), or ratify ground truth.

## 9. Risks & kill conditions (what would stop this plan)

1. **The gold-input oracle fails (A2).** Then the recall problem is not entirely in Stage 0/1 and the frozen graph is a ceiling. The plan re-scopes: the target becomes the oracle-measured ceiling, and any graph change needs the user's explicit decision (Graph v4 is frozen by his rule).
2. **The learning curve flattens below target (Phase B).** Then more of the same data will not help. Pivot to: different backbone, different task formulation, or real user questions (which we do not have) — do not just add 20k repetitive templates (both models agree 20k repetitive can still sit below 70%).
3. **The classifier memorises the new synthetic grammar instead of the test bank (ChatGPT's "biggest risk").** Detected by the holdout (Phase D) diverging from the synthetic validation split. Mitigation is the holdout itself + grouped splits + LLM-diversified data from scenarios, not templates.
4. **Annotator availability.** The 300-item holdout needs real bilingual contributors and two legal annotators. Without them, Phase D cannot be built honestly — and without Phase D, no sealed run should be spent.
5. **Neon re-run changes the advice.** The Gemini consultation came from the Hydrogen fallback, not Neon. If a real Neon (Thinking High) consultation disagrees with the adopted synthesis, re-open §1 and reconcile before training.
6. **RTX availability.** Every training and sealed run needs the user's RTX 5050 (or Colab T4). No GPU here, no torch here — no neural run can be faked or substituted on this VM.

## 10. Timeline (conditional, not a promise)

| Step | Depends on | Rough effort |
|---|---|---|
| Phase A gates (A1–A7) | Agents only (except A2 annotation) | 1–2 focused work sessions |
| Phase D holdout build | Human authors + annotators | Days (recruiting is the bottleneck, not the writing) |
| Phase B Run #1 (nested 2k/4k/7.5k) | RTX 5050 + Phase A passing | Hours of GPU time once the machine is free |
| Phase C mining + expansion | Run #1 measured + holdout built | 1–2 sessions + LLM generation time |
| Phase E sealed re-run | Phase D gates passing | One GPU session |
| Phase F distillation | >70% measured | After the target is met |

- No date is committed here. The binding constraints are the user's RTX time and the human annotators, not agent effort.

## 11. Stop list (both models, adopted)

- Stop tuning regex anchors as the primary recall strategy.
- Stop treating Brutal-230's 100% as evidence of generalisation.
- Stop adding thousands of repetitive templates without a learning-curve experiment.
- Stop using English-first model size as a proxy for multilingual capability.
- Stop tuning 39 thresholds independently against 500 questions.
- Stop globally suppressing issues because of local negation or third-party wording.
- Stop treating missing facts as explicitly false facts.
- Stop modifying Graph v4 to compensate for extraction errors.
- Stop latency optimisation and distillation until extraction accuracy is established.
- Stop repeatedly consulting sealed results to make incremental training decisions.

## 12. How we know we've won

1. Independent holdout (300, 100/language): ≥80% exact per language, micro-R ≥0.90, micro-P ≥0.92, silent ≤1%.
2. Sealed re-run on the frozen checkpoint: Fresh-20 ≥14/20 AND Kannada-8 ≥6/8, with the adaptive-exposure disclosure in the report.
3. No regressions: Brutal-230 230/230, 16-Q 14/16, frozen hashes intact, unit suite green.
4. Only then is ">70%" claimed — and only as the measured sealed number, with its confidence limits stated.
