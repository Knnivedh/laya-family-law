# Gemini consultation — LAYA v7.1 recall approach (fallback model, NOT Neon)

- Date: 2026-11-27 ~20:07–20:12 IST. Chat: https://gemini.google.com/app/18aadfecd490504c ("LAYA v7.1 Extraction Fixes and Recall Strategy"), signed in as Rocky Balbao (elvyn32@santarivn.store).
- **MODEL CAVEAT — read first:** "Deeper analysis 4 Neon" was selected with Thinking High, picker showed "currently Neon High" before sending. Gemini then displayed: "Pro is in high demand at the moment — Another model was used for this response. This didn't count towards your limit." Picker afterwards showed "currently Hydrogen High". **The answer below was produced by Gemini's fallback model (Hydrogen, Thinking High), NOT by Neon.** Per the standing rule (consult Gemini Neon, Thinking High), this consultation does NOT satisfy the Neon requirement — a Neon re-run is still owed when Neon is available. Two sentences were also truncated in the page's own text view (marked below).
- Sign-in note: nivedhbhat15@gmail.com was rejected by Google ("Wrong password"). Signed in with the saved login for elvyn32@santarivn.store instead, on Muse's direction. The nivedh Google password in the vault does not match that account (or has changed) — unresolved, not investigated further.
- The brief was pasted exactly as given; the model asked no clarifying question. Full response finished generating.

## Direct verdicts

- **Q1 (hybrid vs replace): REPLACE Stage 1 outright with the multi-head neural classifier.** Deterministic rules only as (a) post-classifier statutory consistency guards and (b) high-precision regex overrides for explicit section citations ("Section 125 CrPC", "HMA 13B", "DV Act") and hard numeric/temporal parsers (dates pre/post-2024, child age < 18). Regex must never gate, filter, or veto neural logits.
- **Q3 (realistic ceiling, 5k–8k synthetic): 58–66% exact on English, 48–58% on Kannada/Kanglish — SHORT of the 70% floor.** Reaching ≥70% exact needs ≥0.90 micro-recall and ≥0.93 micro-precision (micro-F1 ≥0.91), because exact match needs all ~3.3 sections per query recalled at once with no false positive. Crossing 70% needs three additions before or right after Run #1: (1) multilingual backbone, (2) 3,000–4,000 LLM-diversified lay-seed paraphrases, (3) recall-biased per-head threshold calibration. Expanding 8,000 → 12,000–13,000 with those should push unseen exact to ~72–78% (EN) and ~65–72% (KN/Kanglish).

## Critical §4 flaws to fix before training Run #1

1. **English-only encoders on a trilingual task (called "Fatal").** ModernBERT-large and DeBERTa-v3-large are English-centric; Kannada script fragments into <unk>/byte-fallback, destroying Kannada-8 recall. Switch default backbone in `src/laya_v7_classifier.py` to `jhu-clsp/mmBERT-base` (MIT, 307M, ModernBERT arch, 1,833 languages incl. Kannada) or `FacebookAI/xlm-roberta-large` (MIT, 560M, 100 languages incl. Kannada); alternative `ai4bharat/IndicBERTv2-MLM-only` (MIT, 278M, 20.9B IndicCorp v2 tokens).
2. **8 GB VRAM OOM in current batching math.** Full + 8 clauses at batch 4 = 36 sequences/step; fp32 large encoders will OOM on RTX 5050. Enable bf16, gradient checkpointing, dynamic padding, raise max_seq_len to 256–320 (Kannada subword fertility ~2.3× English; 192 truncates multi-issue Kannada queries).
3. **Random vs grouped validation split leakage.** If the 7,500/500 split was row-level rather than grouped by statutory grammar/seed scenario, near-duplicate templates leak across train/val and inflate validation exact. Re-split grouped by template_family_id / grammar_rule_id.
4. **8 dead Graph v4 fact keys.** Audit all 28 fact keys + 3 enum heads against Graph v4's exact input dictionary; any key the graph reads but Stage 0/1 never emits is a guaranteed silent FN.

## Ranked execution order + stop list

1. **Now:** swap backbone to mmBERT-base or xlm-roberta-large; audit/map all 28 fact + 3 enum keys; enable bf16 + grad checkpointing + max_seq_len=288. Files: `src/laya_v7_classifier.py`, `scripts/train_v71_classifier.py`. Gate: dry-run forward/backward fits <6.5 GB VRAM; 0 dead Graph v4 keys.
2. **Now:** build a 250-item Blind Human-Register Stress Set (EN/KN/Kanglish) written from bare Stage-2 fact tuples, not synthetic templates. File: `data/eval_blind_register_250.jsonl`. Gate: 0% 8-gram overlap with synthetic_v7_1 and sealed hash index; covers all 11 issues & 28 facts.
3. **Run 1:** train baseline multi-head classifier with Asymmetric Loss (ASL), no label smoothing on rare labels, per-head thresholds via OOF + Empirical Bayes shrinkage. Files: `scripts/train_v71_classifier.py`, `src/calibration.py`. Gate: val micro-R ≥0.90, micro-P ≥0.92, exact ≥0.78; Blind Stress Set exact ≥0.65.
4. **Iter 2:** generate +3,500 LLM-diversified lay-register & code-mixed paraphrases targeting top FN clusters (hma-27, pwdva-17/18/19, welfare-principle, divorce/residence/stridhan), verified via Stage-2 round-trip graph check. Files: `scripts/augment_paraphrases.py`, `data/synthetic_v7_2`. Gate: Blind Stress Set exact ≥0.72 across EN and KN/Kanglish before touching sealed sets.
5. **Post-70%:** distill to mmBERT-small (MIT, 140M) or ONNX INT8 mmBERT-base for <0.5 s CPU latency. File: `scripts/distill_student.py`. Gate: CPU p95 <350 ms/query with ≤1.5% exact-match drop vs teacher.

**Explicitly STOP:** tuning regex anchors (memorises surface n-grams, risks new FPs, diverts effort from the classifier); global single-threshold τ or uniform label smoothing across imbalanced heads; running unverified English-only backbones on trilingual data.

## Q2 — paraphrase augmentation ranking (best → worst)

1. Constrained LLM paraphrase generation conditioned on structured fact tuples (highest ROI) — prompt an LLM with the (issues, facts, enums, persona, register) JSON into colloquial Indian English, Kannada, Kanglish without seeing any template text. [Remainder of this bullet truncated in page view.]
2. Hard-negative mining from classifier errors on the Blind Stress Set — cluster errors, generate targeted contrastive minimal pairs.
3. Perturbation & discourse noise — clause reordering, dropping legal nouns for pronouns/kinship terms, conversational filler/preambles. [Remainder truncated in page view.]
4. Back-translation EN↔KN via permissive models (e.g. IndicTrans2 — check license first). Do NOT use facebook/nllb-200 (CC-BY-NC-4.0).
5. More hand-written templates per fact (lowest ROI — diminishing returns; same register as existing templates).

Template artefacts the classifier will overfit to: explicit statutory noun leakage (templates name the concept; real users describe the situation — "he took my gold", "he threw me out"); clause-to-issue 1:1 alignment (one clean sentence per issue vs real users blending 3 facts into one run-on clause); clean Kanglish orthography (real users mix spellings, drop vowels, switch scripts mid-sentence); length-to-multi-label correlation (longer synthetic texts have more labels, teaching length → more sections).

LLM paraphrases leakage-free & label-correct: generate strictly from abstract JSON fact schemas (never feed template or test-bank text); enforce 0 8-gram overlap and cosine <0.80 vs blind test hash index and validation/stress sets; character-trigram diversity <0.55 across paraphrases of the same seed. 3-step filter: (1) reverse-extraction check by a second independent LLM prompt, discard on key mismatch; (2) Stage-2 Graph v4 equivalence check on source vs reverse-extracted JSON, discard on section-set difference; (3) lexical ban-list rotation — for 40% of prompts forbid the canonical English legal term to force lay-register phrasing.

## Q3 — next 4,000 records allocation (by FN counts)

- 1,100 — Residence & coercive lockout (pwdva-17/18/19, 12 combined FNs): non-violent lockout, in-laws blocking entry, constructive eviction, shared household claims without explicit violence, residence after separation.
- 900 — Joint property & Stridhan (hma-27, bns-316, 5 FNs; stridhan 0/3 exact): co-owned flats/plots/savings, wedding gold/gifts held by in-laws, blurred joint-property vs stridhan boundaries, gold kept "for safekeeping".
- 900 — Child custody & welfare (welfare-principle, gwa-1890, hmga-1956-s6, hma-26, 8 combined FNs): implicit minor child mentions, welfare triggers without explicit "custody" wording, mother vs father defaults.
- 700 — Divorce stage & ancillary relief (hma-13, hma-13b, hma-24, hma-25, hma-9, 5+ FNs; divorce 0/2 exact): interim maintenance vs permanent alimony, mutual consent vs contested, restitution.
- 400 — Dense multi-issue 3-to-4-fact single-sentence queries (<25 words) in English and Kanglish to break the length-to-label shortcut.

## Q4 — missing failure modes

1. **Upstream fact fan-out collapse (hidden cause of the FN distribution).** Graph v4 fans one upstream fact into 2–3 sections (custody_claim + minor_child → welfare-principle + gwa-1890 + hmga-1956-s6; coercive_eviction_or_lockout → pwdva-17/18/19; joint_property + divorce → hma-27). Missing just 5 upstream facts explains ~70% of all FNs. Detection: log fact-level recall on Stage 1 outputs before Graph v4, grouped by fan-out. Mitigation: weight loss/thresholds by fan-out degree (facts unlocking ≥2 sections get 1.5× positive loss weight, lower thresholds).
2. **Multi-issue suppression.** High-frequency issues (maintenance 2,255) dominate shared representations; low-frequency co-occurring issues fall just below τ (p=0.38 vs τ=0.50). Detection: stratify validation recall by issue cardinality (watch >10% drop when cardinality ≥2). Mitigation: per-clause classification with max across clauses; oversample multi-issue examples (≥35% of batch with ≥2 active issues).
3. **Kannada/Kanglish beyond translation loss.** Agglutinative suffix/postposition fusion flips requested vs denied; subject/pronoun pro-drop leaves claimant_sex/role uncertain (stalls bnss-144/hma-24/pwdva branches); code-mixed Kanglish clause boundaries break punctuation-based splitters. Detection: slice metrics by lang; inspect sex/role enum recall on Kannada. Mitigation: deterministic Kannada↔Kanglish transliteration augmentation (indic-transliteration/Aksharamukha, Apache-2.0/MIT); claimant_sex/role prior from kinship nouns.
4. **Calibration/threshold failure.** Single τ=0.50 under-predicts rare heads, produces silent failures (0 active issues on valid queries — matches 2/20 silent in Fresh-20). Detection: silent_rate = P(empty | in_scope) must be <1%. Mitigation: temperature scaling + Empirical Bayes per-head thresholds + top-1 fallback (if in_scope >0.50 and zero issues pass τ_k, promote argmax_k (p_k/τ_k) if p_k ≥0.25).
5. **Why the 500-record synthetic validation split will mislead.** Same grammar distribution as training — measures in-distribution fit, not unseen paraphrase generalisation (hence 230/230 vs 7/20). An unregularised model can hit 94% exact on synthetic val while scoring ~55–60% on unseen human questions. Mitigation: never use synthetic val as sole go/no-go gate (see Q6).

## Q5 — classifier design details

- (a) Keep clause-level max-pooling (max(full_p, cmax_p)) but upgrade encoding: **single-pass packed sequence + span pooling** — encode full text once with [C_SEP] clause boundary tokens (max_seq_len=288); pool [CLS] for full logits + global enums; span-attention pooling over token spans for each clause's logits. Benefits: clauses attend to full context (coreference), negation stays clause-scoped, 1 sequence per example instead of 9 (~9× VRAM saving).
- (b) Denied/hypothetical/third-party veto: NO hard binary cutoff. Distinguish true non-actionable hypotheticals ("My friend's brother...", "In a movie...") from conditional future planning ("If I file for divorce, can I...?") — the latter must stay requested. Continuous multiplicative penalty, only when p_veto ≥0.75 AND p_veto − p_req > 0.25 (margin δ=0.25): p_eff = p_req · (1 − p_veto)². Calibrate the 0.75 trigger for ≥98% precision on true negations/third-party narratives on the hard-negative cluster.
- (c) Per-head thresholds without overfitting 500 rows: 3 steps in `src/calibration.py` — (1) temperature scaling (single scalar T on validation NLL); (2) 5-fold OOF predictions across all 8,000 records, tune thresholds on OOF (n≈8,000); (3) Empirical Bayes shrinkage toward recall-biased global τ: find τ_global maximising micro-F_β=1.75 (recall weighted 3×), then τ_k = [n_k+/(n_k+ + κ)]·τ_k* + [κ/(n_k+ + κ)]·τ_global, κ=30, clipped [0.22, 0.75].
- (d) Training details that silently wreck generalisation: label smoothing >0.0 (set 0.0 — compresses rare-head logits); class imbalance (use Asymmetric Loss γ−=2, γ+=0, margin clip m=0.05, or class-weighted focal with positive weights capped at min(4.0, N_neg/N_pos)); clause-splitting errors on Kannada/Kanglish (protect legal/currency abbreviations first, then split on sentence boundaries + strong conjunctions incl. " ಆದರೆ ", " ಮತ್ತು ", " aadre ", " matte "); epochs/LR (5 epochs at lr 2e-5, eff. batch 8 = 4,685 steps — overfits synthetic phrasing by epoch 4; use 10% warmup + cosine decay, weight decay 0.02, dropout 0.15 on heads, early stopping on Blind Stress Set / grouped-val micro-F_1.75, typically peaking at epoch 3).

## Q6 — evaluation design & pre-sealed go/no-go

- 500-record synthetic validation split is NOT adequate as a gate — it verifies optimisation convergence and in-distribution fit only.
- Build a **250-record Blind Human-Register Stress Set** (`data/eval_blind_register_250.jsonl`) before any sealed re-run: sample 250 target (issues, facts, enums) tuples stratified across all 11 issues (min 20 positives per issue, 15 per rare fact, 30 hard negatives/out-of-scope); 2–3 annotators (or an isolated LLM prompted only with statutory text, never synthetic templates) write realistic messy colloquial questions: 125 English, 65 Kannada script, 60 Kanglish. Purity: 0 8-gram overlap and cosine <0.80 vs synthetic_v7_1 and sealed blind hash index; dual-annotator Graph v4 label verification on 100% of items.
- Go/no-go (all must pass before spending a sealed GPU run): Blind Stress Set exact ≥72.0% (target ≥74% English slice, ≥68% KN+Kanglish); micro-R ≥0.90 and micro-P ≥0.92 (micro-F1 ≥0.91); top-FN upstream fact recall ≥0.88 individually on joint_property, coercive_eviction_or_lockout, residence_claim, custody_claim, minor_child; silent failure rate ≤1.0% and out-of-scope/negated-clause FP rate ≤5.0%.

## Status

- Filed 2026-11-27 ~20:12 IST. ChatGPT consultation (GPT-6.2, thinking max) still running at filing time — its answer must be checked against this one before anything is adopted (second-opinion discipline).
- Open: re-run this consultation on real Neon (Thinking High) when Neon is available, since this answer came from the Hydrogen fallback.
