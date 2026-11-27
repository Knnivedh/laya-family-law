# Recall Swarm — Shared State (LAYA v7.1, unseen-question recall → ≥70% exact)

Owner: recall coordinator. Every lane reads this before starting and writes its own status file at `docs/recall_swarm_state/lane-NN-<name>.md` (never edit this file directly — the coordinator merges).
Working copy ONLY: `~/workspace/laya-v71-work`. Baseline: 10x swarm merged, HEAD `1cb0bff`, 22 commits ahead of `origin/main`, tree clean at swarm start.

## Target (user, voice call 2026-11-27 ~19:19 IST)
Unseen law-related questions must reach a MINIMUM of 70% exact. Current measured: Sealed Fresh-20 7/20 (35%), Sealed Kannada-8 4/8 (50%). Brutal-230 is 230/230 but that set is already known — the gap is unseen paraphrase recall. Do NOT claim 70% until a real run measures it.

## Starting point
- Synthetic corpus: `data/synthetic_v7_1/` — 5,000 records (4,500 train / 500 validation, seed 7102), EN 2,316 / KN 1,333 / Kanglish 1,351. Schema: 11 issues, 28 facts, 4-class intents, 4-state facts. Manifest: `data/synthetic_v7_1/manifest.json`.
- Classifier code: `src/laya_v7_classifier.py`, `scripts/train_v71_classifier.py` (code only, no training run yet).
- Leakage gate: `scripts/check_ngram_leakage.py` (8-gram; last run 0 8-grams, max cosine 0.8182).
- Known cause: Stage 1 relies on brittle English regex anchors in `src/laya_v7_evidence.py` + only 9 zero-shot `LAYA_NOUL_PROMPTS` in `src/laya_v7_extractor.py`.
- Baseline numbers: 16-Q evidence-mode 14/16, esc_bool 16/16, esc_kinds 10/16 (10x swarm coordinator re-run).

## Lane map (file ownership — NEVER edit another lane's files)

| Lane | Scope | Owns (only these files) |
|---|---|---|
| 01 Diagnosis | per-cause failure breakdown | `docs/recall_swarm_state/lane-01-diagnosis.md` (analysis only; read-only on code/corpus) |
| 02 Paraphrase expansion | grow corpus, keep split clean | `scripts/build_synthetic_corpus.py`, `data/synthetic_v7_1/` |
| 03 Evidence anchors | harden regex anchors | `src/laya_v7_evidence.py` |
| 04 Classifier training prep | runnable training, RTX commands | `src/laya_v7_classifier.py`, `scripts/train_v71_classifier.py` |
| 05 Kannada/Kanglish | KN + Kanglish coverage | NEW files only: `scripts/kn_templates.py` (or similar new file), `src/laya_lang_normalizer.py`, `src/laya_lang_pack.py` — do NOT edit `scripts/build_synthetic_corpus.py` (Lane 02's); Lane 02 integrates your templates |
| 06 Consultation brief | Gemini + ChatGPT brief | `docs/recall_consultation_brief.md` — PRIORITY: deliver first |
| 07 Evaluation harness | held-out validation scoring | `tests/recall_eval.py` (new) |
| 08 Stage 1 routes audit | route audit + fixes | `docs/recall_stage1_routes_audit.md`, `src/laya_v7_extractor.py`, `src/laya_v7_graph.py` (route fixes only) |
| 09 Independent verifier | blind-checks other lanes | `docs/recall_swarm_state/lane-09-verifier.md` (read-only on others' files; re-runs tests, recomputes numbers) |
| 10 Docs/merge | tracker + manifest | `docs/recall_status.md`, `docs/recall_swarm_state/merged.md`, `PUSH-MANIFEST-RECALL.md` |
| 11 Kaanoon eval set | real-question held-out eval + pattern study | `data/kaanoon_eval/` (new), `docs/recall_swarm_state/lane-11-kaanoon.md` |

## Kaanoon workstream (user, 2026-11-27 ~19:23 IST, blanket permission — DO BOTH, no further questions)
- (1) Pull a sample of real Kaanoon family-law questions (custody, maintenance, divorce, eviction, Stridhan) and build a FRESH held-out test set from their phrasing — evaluation only, kept separate from training data, source URL noted per item.
- (2) Study how laypeople phrase things there and use the patterns to improve Stage 1 mappings/paraphrase templates.
- Bounds that still hold: do NOT copy Kaanoon Q&A content wholesale into the training corpus; write our own templates informed by the patterns. Do not present their lawyers' answers as legal authority and do not cite them in prose. Record sample size, categories, and what changed in `docs/recall_status.md`.

## Cross-lane contracts
- R1 — Validation split is the ONLY progress number: `data/synthetic_v7_1/validation.jsonl` (500 records). Every claim cites split size + method. No validation item within 8-gram overlap of train (Lane 02 re-runs the leakage gate after every expansion).
- R2 — Corpus schema (Lane 02 owns): JSONL `{id, lang, text, issues: {issue: intent}, facts: {fact: state}, enums, spans}`. Lane 04 codes against this schema; if it differs, coordinator reconciles.
- R3 — Lane 03 owns anchors in `laya_v7_evidence.py` ONLY; Lane 08 owns route/emission fixes in extractor/graph. Lane 03 does not touch extractor.py or graph.py.
- R4 — Lane 05 writes KN/Kanglish templates as NEW files; Lane 02 wires them into the builder. Lane 05 never edits the builder.
- R5 — Lane 06's brief goes to the parent FIRST (before other lanes finish). Model answers come back through the coordinator; no lane adopts model advice until the coordinator checks it against our own numbers.
- R6 — Kaanoon eval set is EVALUATION ONLY: `data/kaanoon_eval/heldout.jsonl` is never used for training, templates, anchors, or tuning. Only Lane 07 measures it (read-only scoring). No lane may tune a threshold, template, or anchor against its items.
- R7 — Kaanoon study sample and eval sample are DISJOINT (no shared question, no shared 8-gram). Lane 11 owns the split; Lane 09 verifies disjointness. Patterns for templates/anchors come ONLY from the study sample, never from eval items.

## Hard guardrails (all lanes)
- NEVER touch the 7 frozen files: `graph/laya-crpc-bns-section-decision-tree-v2.json`, `graph/laya-crpc-bns-section-decision-tree-v3.json`, `graph/ground-truth-v2-hma27-A.json`, `graph/brutal-bank-v1-frozen.json`, `test-bank/sealed/fresh-20.json`, `test-bank/sealed/kannada-8.json`, `notebooks/live-laya-colab-test-v6-brutal.ipynb`.
- NEVER open `test-bank/sealed/*.json` beyond aggregates already logged in `results/`. The sealed Fresh-20/Kannada-8 re-run happens ONLY on the RTX machine, never here.
- Never edit the brutal bank, GT v2, or filed results. New results go in new files only.
- This VM has NO GPU/torch: no neural runs, no training, no faked scores, no faked Fresh-20 number.
- After every change run `python3 tests/test_graph_v4.py` and `python3 tests/test_prose_renderer_v2.py` — both must PASS; revert if either fails.
- One logical fix per commit, task-ID in the message (e.g. `R-LANE02: ...`). Commit your own lane's files only; coordinator merges and resolves conflicts.
- Every status file states: what changed, what command was run, the exact output line, and what is still unverified.
