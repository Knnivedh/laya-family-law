# LAYA v7.1 / 10x — Merged Lane Status View

Owner: Lane 11 (docs/repo) created this file; the coordinator owns updates now that Lane 11 is
done. Merged view of all lane status files in `docs/10x_swarm_state/lane-*.md`.
Last updated: 2026-11-27 ~18:19 IST (coordinator, all 11 lanes merged).

## Summary

- Lane status files landed: **11 of 11 — all lanes merged.**
- Commits on top of baseline `bc7f40f`: 21 (plan `f4cfd6f`, swarm state `167af57`, Lane 11
  `50a2855`, Lane 06 `01b686b`, Lane 03 `7d34f05`, Lane 07 `4cc53ba`, Lane 08 `6149de9`,
  Lane 09 `e69433a`, Lane 10 `77d9bac`, Lane 05 `17fff27`, Lane 04 `90dc517`, Lane 02
  `c718f36`, Lane 01 `c9da5f1`, coordinator item-8 fix `28f5424`, plus coordinator tracker
  commits). 57 files changed vs `origin/main`, +34,072/−77.
- Tests re-verified by the coordinator after every merge (see `docs/10x_execution_status.md`):
  graph test PASS (34/66/99, 0 dangling, 7/7 frozen SHAs); prose PASS (246 cases, Fp=0,
  15/15 mutants); full unit suite 49/49 OK; test_v7_rules 10/10; 16-Q evidence-mode
  backtest exact 14/16, esc_bool_strict 16/16, esc_kinds_strict 10/16, fp_prose 0.

## Per-lane status

| Lane | Scope (plan IDs) | Status file | Status | Changes | Needs / blockers |
|---|---|---|---|---|---|
| 01 | P1-1 Section A bugs + P6-1 partial | `lane-01-p1-1.md` | DONE — commit `c9da5f1` | `src/laya_v7.py`, `src/laya_v7_graph.py`, `src/laya_v7_evidence.py`, `src/laya_v7_extractor.py`, `src/laya_prose_v2.py` (235+/38−) | Queued specs from Lanes 05/07/06 NOT applied (see swarm state open follow-ups); RTX confirmation runs |
| 02 | P1-2 synthetic corpus + leakage gate | `lane-02-p1-2.md` | DONE — commit `c718f36` | `scripts/build_synthetic_corpus.py`, `scripts/check_ngram_leakage.py`, `data/synthetic_v7_1/` (5,000 records) | Sealed check QUEUED (trusted command recorded); P2.1 KN audit; PC-2 vocab pin |
| 03 | P1-3 multi-head classifier (code only) | `lane-03-p1-3.md` | DONE — commit `7d34f05` | `src/laya_v7_classifier.py`, `scripts/train_v71_classifier.py` | Blocked on Lane 02 corpus (now landed); GPU training run; PC-2 vocab pin |
| 04 | P1-4 maintenance 34/34 + P1-5 clarification spec | `lane-04-p1-4-p1-5.md` | DONE — commit `90dc517` | `src/laya_family_evidence.py` (+281/−21), `docs/clarification-fallback-spec.md` | RTX run to prove 34/34; Lane 03 SupervisedSignal mappings |
| 05 | P2 unified runtime + Graph v4.1 + multi-turn | `lane-05-p2.md` | DONE — commit `17fff27` | `src/laya_schema_v71.py`, `src/laya_graph_engine.py`, `src/laya_runtime.py`, `src/laya_clarifier.py`, `src/build_graph_v4.py`, `graph/laya-crpc-bns-section-decision-tree-v4.1.json` (36/68/104) | MT1–MT4 12/12 neural suite on RTX; PC-5 v4.1 label collision decision |
| 06 | P3 multilingual + licensing | `lane-06-p3.md` | DONE — commit `01b686b` | `src/laya_lang_normalizer.py`, `src/laya_lang_pack.py`, `LICENSE`, `THIRD_PARTY_NOTICES.md` | Owner confirmation of Apache-2.0 + copyright holder; NLLB retirement still open (license gate FAILs) |
| 07 | P4 legal registry + citations + safety | `lane-07-p4.md` | DONE — commit `4cc53ba` | `legal/verified_authorities.json`, `src/laya_legal_registry.py`, `docs/ground-truth-v3-ratification-pack.md` (PREP ONLY) | Independent rater for GT-v3; 8 authorities need human primary-judgment verification; safety patch spec NOT applied |
| 08 | P5 distillation + ONNX + T4 notebook (design) | `lane-08-p5.md` | DONE — commit `6149de9` | `scripts/distill_student.py`, `src/laya_v7_student.py`, `scripts/export_student_onnx.py`, `src/build_laya_v7_colab.py`, `notebooks/live-laya-colab-test-v7.ipynb` | Blocked on Lane 02 corpus, Lane 03 teacher, Lane 06 licence; PC-2 vocab re-alignment; PC-3 Parity Guard confirm |
| 09 | P6 Kannada prose + readability + audit packets | `lane-09-p6.md` | DONE — commit `e69433a` | `src/laya_prose_kn.py`, `tests/test_prose_kn_mutants.py`, `scripts/export_human_audit.py` | P2.1 native-speaker sign-off (all templates DRAFT); G12 ratings |
| 10 | P7 scorer honesty + calibration + CI | `lane-10-p7.md` | DONE — commit `77d9bac` | `tests/v7_backtest.py`, `src/laya_calibration.py`, `.github/workflows/laya-ci.yml`, `scripts/ci_gate.py` | Open follow-up: `compute_fb` H12 empty-candidates fix; calibration fitting needs RTX + Lane 02 split |
| 11 | Docs/repo: tracker + merged view + push manifest | `lane-11-docs.md` | DONE — commit `50a2855`; tracker/merged view now coordinator-owned | `docs/10x_execution_status.md`, `docs/10x_swarm_state/merged.md`, `docs/10x_swarm_state/lane-11-docs.md`, `PUSH-MANIFEST.md` | — |

## Cross-lane contracts — status

- C1 — `candidates_before_gate` (Lane 01 produces, Lane 10 consumes): **LANDED** — Lane 01
  returns genuine `sorted(dispositions.keys())` from `evaluate_stage2_v7`; Lane 10's scorer
  reads it with dispositions fallback. Open: `compute_fb` H12 empty-list handling.
- C2 — Corpus schema (Lane 02 produces, Lane 03 consumes): **VERIFIED END-TO-END** — Lane 03's
  loader reads Lane 02's corpus 4500/4500 OK (only unknown key `in_scope`). Open: one-key
  vocab pin (PC-2).
- C3 — Clarifier ownership (Lane 05 owns `src/laya_clarifier.py`; Lane 04 specs only):
  **CLOSED** — Lane 04's spec adopts Lane 05's entry points as normative (deltas D-1/D-2).
- C4 — Refactors of Lane 01 files out of scope for other lanes (specs only): specs filed by
  Lanes 05/07/09 — **NOT applied by Lane 01** (open follow-ups, except the EN item-8 fix
  applied by the coordinator as `28f5424`).
- C5 — LICENSE Apache-2.0 draft, pending owner confirmation (Lane 06): **OPEN** — awaiting
  owner decision.

## How this file updates

Coordinator-owned now. Status is asserted only from lane files or commands the coordinator ran.
