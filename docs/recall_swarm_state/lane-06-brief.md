# Lane 06 — Consultation Brief: DELIVERED

**Status:** done — brief delivered to coordinator 2026-11-27 ~19:2x IST (priority deliverable, first).
**Owns:** `docs/recall_consultation_brief.md` (only file written, plus this status file).

## What changed
- Wrote `docs/recall_consultation_brief.md` — self-contained brief for BOTH Gemini (Neon, Thinking High) and ChatGPT (GPT-6.2, thinking max), per the user's standing second-opinion rule. No browser work run (per task); the brief is handed to the parent for the browser runs.
- Brief contents: (1) exact problem + numbers — target ≥70% exact, Sealed Fresh-20 7/20 (35%, micro-R 0.5758, 28 FN, 2 silent), Sealed Kannada-8 4/8 (50%, micro-R 0.6957, 7 FN), Brutal-230 230/230 and 16-Q 14/16 explicitly flagged as known sets, NOT the target; (2) known cause — 9 zero-shot `LAYA_NOUL_PROMPTS` gated behind brittle English regex anchors, missing probes, bank-tuned patterns, 8 dead fact keys; (3) current approach — 5,000-record synthetic corpus (4,500 train / 500 validation, seed 7102, EN 2,316 / KN 1,333 / Kanglish 1,351, leakage gate 0 8-grams, max cosine 0.8182), multi-head classifier code (`src/laya_v7_classifier.py`, `scripts/train_v71_classifier.py`, ModernBERT-large default, clause max-fusion, no training run yet, no GPU on this VM), parallel anchor-hardening lane; (4) six precise questions — hybrid vs outright classifier replacement, paraphrase-augmentation strategy, realistic ceiling for 5k–8k synthetic examples and what pushes past 70%, failure modes most likely missed, classifier design details (fusion, veto calibration, per-head thresholds, imbalance), evaluation design (is 500-record validation an adequate gate); (5) what a good answer must include — concrete checkable recommendations, ranked priorities, explicit stop-dos, direct verdicts on Q1/Q3, named risks with detection + mitigation.
- Guardrails observed: aggregates only, no sealed text — `test-bank/sealed/*.json` never opened; no private material; no other file edited.

## Commands run
- Read: `docs/recall_swarm_state.md`, `docs/10x_plane.md` §1, `docs/10x_execution_status.md`, `results/live-laya-v7-results.md`, `data/synthetic_v7_1/manifest.json`; verified HEAD `1cb0bff`, corpus line counts 4,500 train / 500 validation, classifier docstring (ModernBERT-large default, [11,4]/[28,4] heads, clause fusion).
- No tests run (no code changed; brief is a doc). No commits made — coordinator merges.

## Still unverified / open
- Model answers themselves (Gemini + ChatGPT) — pending parent browser runs; per cross-lane contract R5, no lane adopts model advice until the coordinator checks it against our own numbers.
- Brief accuracy depends on the cited sources (shared state, plan §1, live results, manifest); Lane 09 verifier may re-check the numbers.
