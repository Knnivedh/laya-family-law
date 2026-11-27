# PUSH MANIFEST — LAYA v7.1 / 10x Swarm (one push by the coordinator)

Owner: Lane 11 (docs/repo) prepared the draft; the coordinator refreshed it to FINAL and pushes.
Baseline: `bc7f40f` (remote `main` head, verified live 2026-11-27 ~18:20 IST — no other writer
has pushed since). Working copy: `~/workspace/laya-v71-work`.
Manifest finalized: 2026-11-27 ~18:20 IST (coordinator).
Status: **FINAL — all 11 lanes merged (21 commits ahead of `origin/main`).**

## Files for the one push (from `git diff --name-only origin/main..HEAD`, 57 files)

Total snapshot size: 10,468,042 bytes (~10.0 MiB) — under the 16 MiB `push_files` limit.
Changed/added files only — the other ~93 repo files are untouched and are NOT re-pushed.

### Plan + swarm state + tracker
| File | Change |
|---|---|
| `docs/10x_plane.md` | NEW — the user's pasted 10x plan, verbatim (blueprint only) |
| `docs/10x_swarm_state.md` | NEW — shared state: lane map, contracts C1–C5, status board, plan corrections PC-1–PC-5, open follow-ups |
| `docs/10x_execution_status.md` | NEW — live tracker: Phase 0 tasks, test results run here, mismatches, Phases 1–4 needs |
| `docs/10x_swarm_state/merged.md` | NEW — merged lane status view (11/11 done) |
| `docs/10x_swarm_state/lane-01-p1-1.md` … `lane-11-docs.md` | NEW — 11 lane status files |
| `PUSH-MANIFEST.md` | NEW — this file |

### Lane 01 (V71-P1-1 + P6-1 partial) — commit `c9da5f1` + coordinator `28f5424`
| File | Change |
|---|---|
| `src/laya_v7.py` | MODIFIED — genuine `candidates_before_gate` (C1), real `gated_out` to prose check |
| `src/laya_v7_graph.py` | MODIFIED — recovery gate, OOS handoff, L430/L506 fixes, joint-property decoupling (L512) |
| `src/laya_v7_evidence.py` | MODIFIED — elder-parent/adult-offspring/lockout regexes, 8 dead keys wired |
| `src/laya_v7_extractor.py` | MODIFIED — CPU-when-cached, L417 block removed, cmax pooling, 16/18 Qwen slots |
| `src/laya_prose_v2.py` | MODIFIED — `status="ok"`, `proceeding_pending_hma` fix, EN item-8 bare-comma fix |

### Lane 02 (V71-P1-2) — commit `c718f36`
| File | Change |
|---|---|
| `scripts/build_synthetic_corpus.py` | NEW — deterministic (seed 7102) corpus builder |
| `scripts/check_ngram_leakage.py` | NEW — 8-gram + TF-cosine leakage gate, blind-hash sealed mode |
| `data/synthetic_v7_1/train.jsonl` | NEW — 4,500 records (sha256 `8777bddd…`) |
| `data/synthetic_v7_1/validation.jsonl` | NEW — 500 records |
| `data/synthetic_v7_1/manifest.json`, `schema.json`, `leakage_report.json` | NEW — corpus manifest, C2 schema, leakage report (0 8-grams, max cosine 0.8182) |

### Lane 03 (V71-P1-3) — commit `7d34f05`
| File | Change |
|---|---|
| `src/laya_v7_classifier.py` | NEW — multi-head teacher (code only, no training run) |
| `scripts/train_v71_classifier.py` | NEW — training script (code only; RTX command in docstring) |

### Lane 04 (V71-P1-4/P1-5) — commit `90dc517`
| File | Change |
|---|---|
| `src/laya_family_evidence.py` | MODIFIED — maintenance final_check evidence fixes (+281/−21) |
| `docs/clarification-fallback-spec.md` | NEW — clarification fallback spec (adopts Lane 05's clarifier entry points) |

### Lane 05 (V71-P2) — commit `17fff27`
| File | Change |
|---|---|
| `src/laya_schema_v71.py` | NEW — provenance + TurnRecord/SessionState schema |
| `src/laya_graph_engine.py` | NEW — v4.1 loader, reachability audit, genuine `candidates_before_gate` |
| `src/laya_runtime.py` | NEW — unified multi-turn runtime |
| `src/laya_clarifier.py` | NEW — clarifier (max 2 questions/turn, safety first) |
| `src/build_graph_v4.py` | MODIFIED — extended only; `build_v4_graph()` output identical to disk v4 |
| `graph/laya-crpc-bns-section-decision-tree-v4.1.json` | NEW — 36 sections / 68 nodes / 104 edges (SHA-256 `27b03d4c…`) |

### Lane 06 (V71-P3) — commit `01b686b`
| File | Change |
|---|---|
| `src/laya_lang_normalizer.py` | NEW — Kanglish-aware normalizer |
| `src/laya_lang_pack.py` | NEW — LanguagePack (KN + EN defined; others TODO stubs) |
| `LICENSE` | NEW — Apache-2.0 draft, **pending owner confirmation** |
| `THIRD_PARTY_NOTICES.md` | NEW — license audit (MuRIL primary encoder recommendation) |

### Lane 07 (V71-P4) — commit `4cc53ba`
| File | Change |
|---|---|
| `legal/verified_authorities.json` | NEW — 9 authorities, 1 verified_primary (Sukhdev Singh) |
| `src/laya_legal_registry.py` | NEW — CrPC/BNSS, IPC/BNS, IEA/BSA crosswalk (self-test 31/31) |
| `docs/ground-truth-v3-ratification-pack.md` | NEW — D-V4-1..4 drafts + adjudication template, PREP ONLY (v3 NOT created) |

### Lane 08 (V71-P5) — commit `6149de9`
| File | Change |
|---|---|
| `scripts/distill_student.py` | NEW — distillation script (code only, no GPU run) |
| `src/laya_v7_student.py` | NEW — 6-head student (code only) |
| `scripts/export_student_onnx.py` | NEW — ONNX opset 17 + INT8 export (code only) |
| `src/build_laya_v7_colab.py` | NEW — Colab notebook builder |
| `notebooks/live-laya-colab-test-v7.ipynb` | NEW — 9-cell T4 notebook (nbformat.validate PASS) |

### Lane 09 (V71-P6) — commit `e69433a`
| File | Change |
|---|---|
| `src/laya_prose_kn.py` | NEW — Kannada prose templates (20/20 sections, all DRAFT pending P2.1) |
| `tests/test_prose_kn_mutants.py` | NEW — 7 tests, 25 KN adversarial mutants |
| `scripts/export_human_audit.py` | NEW — blind G12 + P2.1 audit packet exporter |

### Lane 10 (V71-P7) — commit `77d9bac`
| File | Change |
|---|---|
| `tests/v7_backtest.py` | MODIFIED — honest Fb, raw + capped ratings, H12 unmasked, `--strict` |
| `src/laya_calibration.py` | NEW — temperature scaling + ECE/Brier/AURC gates (code only) |
| `.github/workflows/laya-ci.yml` | NEW — 7-job CI workflow |
| `scripts/ci_gate.py` | NEW — CI gate reporter (exit 0/1/2, never a silent pass) |

## Pre-push verification checklist (coordinator, run at final HEAD before pushing)

- [x] Frozen-SHA test passes — `python3 tests/test_graph_v4.py` →
  `GRAPH V4 + FROZEN SHA TEST PASS: 34 sections / 66 nodes / 99 edges, 0 dangling edges,
  7/7 frozen hashes intact.` (exit 0).
- [x] Prose test passes — `python3 tests/test_prose_renderer_v2.py` →
  `PROSE VALIDATION PASS: 246 cases, Fp=0, quality_flags=0, 15/15 adversarial mutants caught`
  (exit 0).
- [x] Full unit suite — `python3 -m unittest discover -s tests -p "test_*.py"` → `Ran 49 tests — OK`.
- [x] `test_v7_rules` — 10/10 OK.
- [x] 16-Q evidence-mode backtest — `python -m tests.v7_backtest --suite 16q --mode evidence
  --device cpu` → exact 14/16, esc_bool_strict 16/16, esc_kinds_strict 10/16, fp_prose 0.
- [x] No frozen files in the changed list — `git diff --name-only origin/main..HEAD` contains
  none of: graph v2/v3, ground-truth-v2-hma27-A.json, brutal-bank-v1-frozen.json,
  test-bank/sealed/*, v6-brutal notebook.
- [x] No sealed text in the diff — no sealed-bank file is in the changed list; the diff's
  "sealed" mentions are references (IDs, filenames, "sealed check QUEUED") only. No sealed
  question text was opened by any lane or by the coordinator.
- [x] Remote head verified live — `main` is still `bc7f40f097afb7f4463d18bd16d2ea6b1edd98ae`
  (no other writer has pushed).
- [x] Snapshot size — 57 files, 10,468,042 bytes (~10.0 MiB) < 16 MiB `push_files` limit.
- [x] No model weights (808 MB) or retest PDFs in the selection; no binary files; no deletions.

## Push command (exact, for the next attempt if this one is blocked)

```text
github push-files --owner Knnivedh --repo laya-family-law --branch main \
  --message "LAYA v7.1 / 10x swarm: all 11 lanes — Phase 0 fixes, corpus + leakage gate, classifier, maintenance fixes, unified runtime + Graph v4.1, multilingual + licensing, legal registry, distillation + ONNX + T4 notebook, Kannada prose, honest scorer + CI" \
  --source-dir /home/hatch/workspace/laya-v71-work \
  --paths-file <NUL-delimited manifest of the 57 files above, stored outside the source dir>
```

Manifest generation (changed/added files only — NOT all repo files):

```text
git -C /home/hatch/workspace/laya-v71-work diff --name-only -z origin/main..HEAD > <paths-file>
```

Verify live after pushing with `get_file_contents` (`docs/10x_plane.md` renders) and `list_commits`
(new head lists the swarm work).
