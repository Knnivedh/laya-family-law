# Neon Re-run Brief — LAYA v7.1 Unseen-Question Recall (≥70% exact)

**Purpose of this file:** the exact brief to send to Gemini (Neon, Thinking High) for the genuine Neon consultation. The brief was first answered by a Hydrogen fallback on 2026-11-27 ~20:07 IST, and the re-run on 2026-11-27 ~21:15 IST fell back to Hydrogen again. Neon then became rate-limited until **28 Nov 2026, 00:07 IST**. Send this brief only when the Gemini model picker shows "Neon High" before sending. If Neon is unavailable or greyed out, STOP — do not send it to any other model.

**To:** Gemini (Neon, Thinking High). Same brief was previously answered by a fallback model (Hydrogen), not Neon — this is the re-run for a genuine Neon answer. Numbers below are updated to the 2026-11-27 evening state.
**From:** LAYA engineering team. **Date:** 2026-11-27.
**Role of this consultation:** Second opinion only. Your recommendations will be checked against our own numbers before anything is adopted. You have no repository access and no test-set text — this brief is everything you get. Do not ask for the test questions; they are sealed and will not be shared.

## 1. The system (what LAYA is)

LAYA is a deterministic Indian family-law chatbot for laypeople. Pipeline:
1. **Stage 0/1 — extraction:** from a free-text user question, extract which legal *issues* are requested (11 issues: maintenance, custody, residence, divorce, stridhan [wife's wedding gold/property], joint_property, violence, dv_compensation, restitution, birth_certificate, procedure) and which *atomic facts* hold (28 facts, e.g. `divorce_asked`, `custody_claim`, `residence_claim`, `coercive_eviction_or_lockout`, `demand_made`, `proceeding_pending_hma`, `decree`, `minor_child`).
2. **Stage 2 — decision graph:** a fixed statutory decision tree (Graph v4) maps issues + facts to the applicable legal sections (e.g. HMA s.27 joint property, PWDVA ss.17/18/19 residence/protection, BNSS s.144 maintenance, BNS s.316 breach of trust). Stage 2 is rule-based and frozen; the recall problem lives entirely in Stage 0/1.
3. **Prose:** templated layman answer from the selected sections (zero hallucinated citations by construction).

Languages: English, Kannada (Kannada script), and Kanglish (Romanised Kannada, e.g. "Nanna ganda hana koduttilla" — Kannada words in Latin script). A question is scored **exact** only if the full set of predicted sections matches the ground truth exactly.

## 2. The problem — exact numbers, no hype

**Target (set by the product owner, 2026-11-27): minimum 70% exact on unseen law-related questions.**

Measured on two small *sealed* held-out sets (we report aggregates only; the question text is never opened by us):

| Set | Exact | Micro-P / Micro-R / Micro-F1 | TP / FP / FN | Silent (no answer) | 95% Wilson CI |
|---|---|---|---|---|---|
| Sealed Fresh-20 (English, unseen paraphrases) | **7/20 (35%)** | 0.8837 / 0.5758 / 0.6972 | 38 / 5 / 28 | 2 | [0.18, 0.57] |
| Sealed Kannada-8 (Kannada, unseen) | **4/8 (50%)** | 1.000 / 0.6957 / 0.8205 | 16 / 0 / 7 | 0 | [0.22, 0.78] |

The failure is **recall, not precision**: precision is 0.88–1.00, but recall is 0.58–0.70. The system almost never invents a wrong section; it silently *misses* sections the question does ask for.

False-negative counts by section (Fresh-20, 28 FN total): hma-27 (joint property) 4; welfare-principle (custody welfare test) 3; pwdva-17, pwdva-18, pwdva-19 (residence/protection orders) 3 each; hma-13 (divorce) 2; hma-24 (interim maintenance) 2; gwa-1890 (guardianship/custody) 2; hmga-1956-s6 (minor's guardian) 2; hma-25, bns-316, hma-26 1 each. False positives (5 total): pwdva-20 2, hma-13 2, bnss-144 1.
Exact by category (Fresh-20): divorce 0/2, residence 0/2, stridhan 0/3, custody 1/3, violence 1/2, maintenance 2/4, out-of-scope 1/2.
Kannada-8 FN (7 total): pwdva-18 2; hma-27, bnss-144, pwdva-20, pwdva-19, pwdva-17 1 each. Category exact: divorce 0/2, residence 0/1, stridhan 0/1.

**Contrast — known sets (these are NOT the target and must not be confused with it):** Brutal-230 (our own adversarial bank, already known to the team) is 230/230 exact, and the 16-question regression set is 14/16 exact. So the system is near-perfect on wording it has seen and collapses to 35–50% on genuinely unseen paraphrases. That gap — not the known-set scores — is the whole problem.

**Update since the brief was first written:** a recall-improvement swarm finished. On a frozen 500-record synthetic validation split the current system scores 261/500 = 52.2% exact (Wilson [0.4782, 0.5654]); on a fresh 28-question real-Kaanoon eval set, 14/28 = 50.0%. The 70% target is not reached. No classifier training has run yet (no GPU here).

## 3. Known cause (diagnosed, not guessed)

Stage 1 extraction today is:
- **11 zero-shot neural prompts** scored by a 421M multilingual encoder (PIXMELT/laya). There are **zero neural probes** for hma-13b (mutual consent), decree, lump-sum settlement, proceeding-pending, being-filed, existing-order enforcement, claimant sex/role, demand-made, judicial-separation-only, in-scope, and several Graph v4 choice nodes. (hma-9 restitution and pwdva-22 DV injury compensation gained probes in the current tree — `restit_p`, `dvcomp_p`, thresholds uncalibrated.)
- Those 11 prompts are **gated behind brittle English regex anchors**: if the user's wording does not match the regex, the neural signal is discarded. Clause-max pooling across strid/res/div/jp/bc already exists in the merger (`score = max(full, cmax)`), but the anchor gate still vetoes recall before pooling can help. (An earlier rule blocking the neural custody boost whenever `residence_claim` was true has been removed; the custody boost is no longer residence-gated.)
- Several regexes are **bank-tuned**: they memorise surface forms from the known 230-question bank instead of generalising. Eight fact keys the graph reads are never produced by Stage 0/1 at all (dead keys), so whole graph branches are unreachable from unseen wording.

In short: recall depends on the user's phrasing matching our hand-written English patterns. Unseen paraphrases — especially indirect, colloquial, multi-issue, negated, hypothetical, or Kannada/Kanglish phrasing — fall through.

## 4. Our current approach (what is already built / in flight)

**(a) Synthetic corpus (built, not yet used for training).** `data/synthetic_v7_1/`: **8,000 records — 7,500 train / 500 validation, seed 7102, validation split frozen** (sha256 7640d067c28abf539131dbcc891e4bdffedf62bbef4a7d66c1659bb96d07e58e), generated purely from statutory grammars, paraphrase templates, and hard-negative perturbations; expanded from 5,000 with thin-cluster and hard-negative additions (clusters hn_g/hn_h). Never derived from any test bank. Schema per record: `{id, lang, text, issues, facts, enums, spans}` — 11 issues × 4 intents (requested / incidental / denied / uncertain), 28 facts × 4 states (supported / denied / unknown / conflicting), plus enums for claimant sex (F/M/U), claimant role, and modality/time. **Leakage gate enforced:** 0 word-8-gram overlap and max cosine 0.8269 against all test banks (checked via a blind hash index, so sealed wording is never printed). The 500-record validation split is our *only* progress metric until the sealed re-run.

**(b) Multi-head classifier (code written, no training run yet).** A unified multi-head teacher over a permissive-licensed encoder. Inputs: `[CLS] full question [SEP]` plus batched `[CLS] clause_i [SEP]` (up to 8 clauses). Heads: issue head [11, 4], fact head [28, 4], enum heads (sex, role, modality), and a span-attention pool for evidence spans. Clause-vs-full fusion: `requested` uses calibrated `max(full_p, cmax_p)`, where a sentence-local denied/hypothetical/third-party gate logit ≥ τ_neg vetoes **only that clause**, never sibling clauses. No regex anchor vetoes on recall. Training is planned on a single RTX 5050 laptop GPU (8 GB VRAM). **This VM has no GPU and no torch — no training run has happened; do not assume any trained-model result exists.**

**(c) Anchor hardening (parallel lane, stopgap).** The regex anchors are being repaired in parallel. This is a stopgap to lift the current system while the classifier is trained — not the long-term fix.

**Current working direction (from the other consultation + our own analysis — NOT committed; challenge it):** replace Stage 1 outright with the classifier; backbone `jhu-clsp/mmBERT-base` (MIT) as primary (English-only ModernBERT-large / DeBERTa-v3-large rejected as the default for a trilingual task); train the existing 8,000 first with a nested learning curve (2,000 / 4,000 / 7,500) before deciding on expansion; bf16, micro-batch 1, grad-accum 8, max_seq_len 288, ASL loss, label smoothing 0.0, per-head thresholds via out-of-fold predictions + Empirical Bayes shrinkage; then ~4,750 targeted LLM-diversified records aimed at the failing clusters (residence/lockout 1,100; joint property + Stridhan 900; custody 900; divorce 700; maintenance 450; dense multi-issue 400; scope/negation 300); pre-sealed gate is a fresh 300-question independent human-written holdout (100 per language, ≥80% exact per language).

**Hard constraints on any recommendation:** (i) only permissively licensed weights in the production path (Apache-2.0 / MIT / BSD) — the current Kannada translator (facebook/nllb-200, CC-BY-NC-4.0) is being retired from the default path, so do not propose a solution that depends on it or any other non-commercial model; (ii) Stage 2 (the decision graph) and the prose templates are frozen — fixes must land in Stage 0/1 extraction; (iii) no claim of ≥70% is accepted until a real run on the sealed sets measures it (sealed re-run happens only on the GPU machine, never here); (iv) end-state latency target is <0.5 s/question on CPU via a distilled student, but that is a later phase — recall comes first.

## 5. Precise questions

1. **Hybrid vs replacement.** Is a regex-anchor + classifier hybrid the right fix for paraphrase recall, or should Stage 1 be replaced by the classifier outright (regex kept only as a high-precision override / safety net, never as a recall gate)? If hybrid, state exactly which decisions each side should own, and where the boundary must sit so the regex cannot veto a classifier recall. Also judge the current working direction above (replace outright, mmBERT-base, train 8k first) — agree, disagree, or amend, with reasons.
2. **Paraphrase augmentation.** What paraphrase-augmentation strategy generalises best to *unseen legal phrasing* from a template-generated synthetic corpus — and what specifically will *not* generalise (i.e. what template artefacts should we expect the classifier to overfit to)? Rank: more templates per fact, LLM-based paraphrase generation, back-translation (EN↔KN), perturbation/noise (negation swaps, entity swaps, word-order), or hard-negative mining from classifier errors. If you recommend LLM paraphrases, say how to keep them leakage-free and label-correct at scale.
3. **Realistic ceiling.** What is the realistic ceiling for a 5,000–8,000-example synthetic corpus on genuinely unseen paraphrases in this 11-issue / 28-fact multi-label setting — and what would it take to push past 70% exact? Give a number with reasoning (not optimism): is 70% plausible from this corpus size, or does it need 20k+ examples, real user questions, a bigger/different backbone, or a different task formulation? If the corpus is the bottleneck, say what the next 3,000–5,000 examples should cover first, by cluster. The current measured point is 52.2% on the frozen synthetic split — where does the curve go from here?
4. **Failure modes we are most likely missing.** Given the FN distribution above (hma-27, welfare-principle, pwdva-17/18/19 dominate; divorce/residence/stridhan categories at 0/x; precision high, recall low; 2 silent failures), what failure modes is our diagnosis most likely *missing*? In particular: (a) multi-issue questions where one issue suppresses another; (b) Kannada/Kanglish-specific failure modes beyond translation loss (agglutinative negation, colloquial idiom, code-mixing); (c) calibration/threshold failure (a single τ for all 39 heads vs per-head thresholds); (d) anything about the 500-record validation split that would make it a misleading proxy for the sealed sets.
5. **Classifier design details.** For this exact setup (mmBERT-base or a comparable multilingual encoder, 8 GB VRAM, max-seq-len 288, ≤8 clauses): (a) is clause-level max-pooling the right fusion, or should we use something else (cross-attention, per-clause classification with voting, full-question-only)? (b) How should the denied/hypothetical/third-party clause veto be calibrated so it stops false positives without re-introducing the recall collapse? (c) Per-head thresholds vs a global threshold — what procedure, using only the 500-record validation split plus out-of-fold predictions on the 8,000, sets them without overfitting? (d) What training detail is most likely to silently wreck generalisation here (class imbalance — e.g. maintenance 2,255 requested vs restitution 118; label smoothing; epoch count; clause-splitting errors)?
6. **Evaluation design.** Is a 500-record synthetic validation split an adequate gate for "will this hit 70% on unseen human-written questions"? If not, what is the minimum additional held-out evaluation we should build *before* the sealed re-run — and how do we build it without touching or approximating the sealed sets? What metric (exact-match, per-section recall, per-category exact) should be the go/no-go, and at what value? Judge the proposed 300-question independent human-written holdout (100 per language, ≥80% exact per language) as the pre-sealed gate.

## 6. What a good answer must include

- **Concrete, checkable recommendations**, each with: what to do, in which file/layer (Stage 0/1 extraction, corpus builder, classifier, evaluation), and how we will know it worked (metric + threshold on the 500-record validation split or a named diagnostic). General advice ("use more data", "try augmentation", "tune thresholds") without numbers, priorities, or a falsifiable check is not useful.
- **A ranked priority order** — what to do first, second, third — with anything you would explicitly *stop doing* (e.g. stop hardening regexes beyond a stated point).
- **A direct verdict on Q1 and Q3** (hybrid vs replace; is 70% plausible from 5–8k synthetic examples, and if not, what closes the gap), with the reasoning and the assumptions behind the number.
- **Named risks and failure modes** from Q4, each with a concrete detection (a diagnostic we can run) and a mitigation.
- **Anything in §4 you believe is wrong** — e.g. a design choice in the classifier or corpus that you would change before the first training run, and why.

Keep the answer tight and structured (headings + bullets). Do not reproduce or request any sealed question text. Do not propose solutions requiring non-commercially-licensed models, live user data we do not have, or access to the test banks.
