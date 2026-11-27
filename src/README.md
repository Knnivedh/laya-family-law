# `src/` — Standalone LAYA v7 Runtime, Maintenance CLI & Frozen Notebook Builders

This directory contains the standalone `v7` family-law classification package, the `v7` deterministic prose renderer, the interactive maintenance runtime, and the deterministic Colab notebook builders (`v1–v6`).

## Files

### Standalone `v7` Decision Graph Runtime (`mode="laya"` default)
| File | What it does |
|---|---|
| `laya_v7.py` | Public `v7` classifier API combining Stage 0/1 extraction, Graph `v4` Stage 2 routing, court selection, typed escalations, and `laya_prose_v2` rendering |
| `laya_v7_schema.py` | Typed evidence, disposition, forum, and escalation dataclasses (`CUSTODY_VOCAB_PROJECTION` boundary helpers included) |
| `laya_v7_evidence.py` | Clause-aware grounded evidence extractor (hypothetical/past/quoted/negation guards, beneficiary vs speaker, BNSS/HMA proceeding disambiguation, commercial OOS guards) |
| `laya_v7_extractor.py` | Batched `PIXMELT/laya` (421M ModernBERT-large bf16 sentence-split) + lazy `facebook/nllb-200-distilled-600M` (`kan_Knda -> eng_Latn`) + optional `Qwen3-1.7B` `"structured"` mode |
| `laya_v7_graph.py` | Executable Graph `v4` Stage 2 router, claimant-sex/role filtering (`C8`), `PWDVA 17/18/19` decoupling, Layer A zero-`Fb` guard, 9-kind escalations |
| `laya_prose_v2.py` | Deterministic template-locked English/Kannada prose renderer + automated `Fp=0` safety checker (`246/246` + `15/15` mutants) |

### Family-Law Maintenance Intake Runtime (`--interactive`)
| File | What it does |
|---|---|
| `laya_family.py` | Standalone maintenance intake classifier & CLI (`python -m src.laya_family --interactive`, guide in [`docs/laya-family-law-runtime.md`](../docs/laya-family-law-runtime.md)) |
| `laya_family_evidence.py` | Procedural and relief fact grounding for maintenance scenarios |
| `laya_family_model.py` | Model wrapper for local maintenance evaluation |
| `laya_family_structured.py` | Structured fallback decoder for maintenance route experiments |

### Graph Builders, Local Brutal Runner & Frozen Notebook Builders
| File | What it does |
|---|---|
| `build_graph_v4.py` | Builds Graph `v4` (`34` sections / `66` nodes / `99` edges, `0` dangling edges) from frozen `v3` |
| `run_v6_brutal_local.py` | Local RTX 5050 runner for the frozen `v6-brutal` notebook benchmark (`results/live-laya-colab-results-v6-brutal*`) |
| `analyze_v6_brutal.py` | Failure-mode analyzer for `v6-brutal` outputs |
| `build_laya_colab_notebook.py` | Builds the `v1` live Colab notebook |
| `build_laya_v3_empty5.py` | Builds the `v3` (`empty-5` fix) notebook |
| `build_laya_v4_residence.py` | Builds the `v4` residence notebook |
| `build_laya_v4_1_evidence_first.py` | Builds the `v4.1` evidence-first notebook |
| `build_laya_v5_precision.py` | Builds the `v5` precision notebook |
| `build_laya_v6_brutal.py` | Builds the `v6` brutal notebook (24 cells, frozen SHA `d6ee5795...`) |
| `merge.py` / `merge_v2.py` | Graph merge helpers (`v1 -> v2`) |
| `gen_report_v2.py` | Report generator used for `v2` |
| `offline_replay_harness_v5.py` | Offline replay of `v5` scoring logic (never cited as a live result) |

## Quick Commands (from repository root)

```powershell
$env:PYTHONUTF8="1"
# Unit tests, Graph v4 integrity + frozen SHAs, and Prose v2 safety checks
python -m unittest discover -s tests -p "test_*.py" -v
python -m tests.test_graph_v4
python -m tests.test_prose_renderer_v2

# Full v7 CUDA benchmark (`16-Q`, `Brutal-230`, `Sealed Fresh-20`, `Sealed Kannada-8`)
python -m tests.v7_backtest --suite all_with_sealed --mode laya --device cuda --misses 0

# Zero-model CPU grounded-evidence baseline
python -m tests.v7_backtest --suite both --mode evidence --device cpu --misses 0

# Interactive maintenance intake CLI
python -m src.laya_family --interactive
```

Rebuilding a frozen notebook builder (for example `python src/build_laya_v6_brutal.py`) must reproduce its notebook byte-identically (same SHA-256 — see `README.md` §8).

## Current Scope (`v7` vs `v7.1`)

- **Done (`v7`):** Standalone `v7` runtime is implemented in `src/laya_v7*.py`, clearing **`230/230` (`100%`, `10.0/10`)** on `Brutal-230` across two identical locked CUDA confirmation runs (`results/live-laya-v7-run{1,2}.log`).
- **Remaining (`v7.1`):** Lifting unseen-paraphrase recall on `Sealed Fresh-20` (`7/20`, `micro_p=0.8837`, `micro_r=0.5758`) and `Sealed Kannada-8` (`4/8`, `micro_p=1.0`, `micro_r=0.6957`), completing blind/native/Colab-T4 audits, and building a standalone `v7` Colab notebook.
