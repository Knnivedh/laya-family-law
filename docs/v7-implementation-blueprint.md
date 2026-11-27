# LAYA v7 Implementation Blueprint — End-to-End 10/10 Decision Graph

**Baseline Recorded:** `HEAD = c71a16f` (`tests.laya_maintenance_backtest` on RTX 5050 CUDA: `development 48/48`, `challenge 34/34`, `verification 46/46`, `final_check 32/34` — `0` FP, `2` FN on `bnss-144` and `bnss-146`; `live-laya-colab-test-v6-brutal`: `16/16` dev, `79/230` brutal `1.9/10`, `5/20` fresh, `1/8` Kannada).

## 1. Architecture Separation (Zero Scorer Leakage)

1. **`src/laya_v7_schema.py` — Typed Evidence & Decision Contract:**
   - Stage 0 preprocesses raw text + explicit locale (`latin` vs `kannada` via Unicode script range `\u0c80-\u0cff`, optional bilingual NLLB/Qwen translation trace).
   - Stage 1 emits `IssueEvidence` (`requested | incidental | denied | uncertain`, span, source, confidence) and `FactEvidence` (`supported | denied | unknown | conflicting`, subject, beneficiary, span, modality_time, source, confidence).
   - Strict boolean-safety helper `proved_true()` guarantees string values like `"unknown"` or `"no"` never act truthy.
   - `assess_v7(question, ...)` accepts **only** raw question text, optional `locale`, and optional `confirmations`. Never accepts item IDs, dataset names, query hashes, or GT dicts.
2. **`src/laya_v7_graph.py` — Executable Graph v4 Engine (`34/66/99` + Independent Predicates):**
   - Loads and validates `graph/laya-crpc-bns-section-decision-tree-v4.json`, declaring all Stage 1 entry points (`root:issue-classification`, `stage1:confidence-gate`, `stage1:conversation-context`, `stage1:kannada-mapping`) so **66/66 (100%)** nodes are reachable.
   - Evaluates independent per-remedy Stage 2 rules returning `RemedyDisposition` (`eligible | conditional | needs_fact | inapplicable`), canonical `kept_ids`, `kept_statutory_ids`, `applied_principles` (`welfare-principle`, `hmga-1956-s6`), `gated_out`, `court_live` + `court_source`, and 9-kind typed `escalations_typed` (`quantum`, `custody`, `residence`, `safety`, `recovery`, `demand`, `procedure`, `court`, `fact`).
   - Fixes `build_graph_v4.py:410` edge note so `pwdva-17/19` and `pwdva-18` evaluate strictly independently and can co-fire whenever both predicates hold.
   - Keeps urgent `safety` independent of statutory eligibility (`claimant_sex == "male"` or child risk still triggers safety advice).
3. **`src/laya_v7_evidence.py` & `src/laya_v7_extractor.py` — Batched `PIXMELT/laya` + `NLLB-200` + Grounded Evidence (`E2` + `K1`):**
   - Primary CUDA/CPU extractor runs `PIXMELT/laya` (421M ModernBERT-large bf16, `predict_batch` sentence-split max-pool over `49` legal fact/topic signals) combined with clause-aware grounded evidence (`supported | denied | unknown | conflicting`, hypothetical/past/quoted/third-party/negation guards, beneficiary vs speaker distinction, and BNSS/HMA proceeding disambiguation). Also preserves Codex's 4-split maintenance runtime (`dev 48/48`, `challenge 34/34`, `verification 46/46`, `final_check 32/34`) and an optional `Qwen3-1.7B` `"structured"` mode (benchmarked and rejected as primary due to `B-207`/`B-214` Kannada and `16-Q` `H6`/`H13` OOS hallucinations).
   - For Kannada script (`K1`), translates sentences with `facebook/nllb-200-distilled-600M` (`kan_Knda -> eng_Latn`) before running the shared English Stage 1 + Stage 2 pipeline (`C13` improved from `1/16` in evidence-only mode to `16/16` in `laya` mode, and `Sealed Kannada-8` improved from `1/8` in `v6` to `4/8` with `micro_p=1.0` in `v7`; `NLLB-200` noncommercial weights remain noted separately from Apache-2.0 `Qwen3-1.7B`).
4. **`src/laya_prose_v2.py` — Template-Locked Prose (`P1`, `Fp = 0`):**
   - Closes all known adapter/renderer edge defects: typed-fact boolean projection (`"unknown"` never truthy), suppression of `BNS §316` in `recovery` text unless `"bns-316"` is in `kept_ids`, no court inference from escalation kinds, out-of-scope safe template when `in_scope=False`, and explicit fail-safe handoff for unknown enum values or violated statutory preconditions.
5. **`tests/v7_backtest.py` — Isolated Scorer & Iterative Verification:**
   - Joins predictions with `16-Q` (`ground-truth-v2-hma27-A.json`), `Brutal-230` (`brutal-bank-v1-frozen.json`), and (only once locked) `Sealed-20/8` strictly *after* inference, logging both untouched legacy scores (`CUSTODY_VOCAB_PROJECTION`, `16-Q` D-V4-2 deltas) and clean v4 metrics.
