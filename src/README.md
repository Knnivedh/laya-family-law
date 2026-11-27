# src/ — builders and helpers

**Family-law maintenance intake** is available through the local LAYA model.
Run `python -m src.laya_family --interactive` from the repository root.
See the [runtime guide](../docs/laya-family-law-runtime.md).

The legacy full-benchmark classification pipeline (Stage 1 typed decisions + Stage 2 graph recheck +
scoring) currently lives inside the Colab notebooks in `../notebooks/`. This
directory holds the deterministic builder scripts that generate those notebooks
plus the graph merge / replay helpers used during development.

## Files

| File | What it does |
|---|---|
| `build_laya_colab_notebook.py` | Builds the v1 live notebook |
| `build_laya_v3_empty5.py` | Builds the v3 (empty-5 fix) notebook |
| `build_laya_v4_residence.py` | Builds the v4 residence notebook |
| `build_laya_v4_1_evidence_first.py` | Builds the v4.1 evidence-first notebook |
| `build_laya_v5_precision.py` | Builds the v5 precision notebook |
| `build_laya_v6_brutal.py` | Builds the v6 brutal notebook (24 cells) — the current one |
| `merge.py` / `merge_v2.py` | Graph merge helpers (v1 → v2) |
| `gen_report_v2.py` | Report generator used for v2 |
| `offline_replay_harness_v5.py` | Offline replay of v5 scoring logic (predictions only — never a live result) |

## Rebuilding

```bash
python3 src/build_laya_v6_brutal.py
```

Re-running a builder must reproduce its notebook byte-identically (same SHA-256
— see the README's frozen-hash table). If it does not, the builder or the
notebook was edited; stop and investigate.

## Missing (pending task P3.4)

Full standalone benchmark coverage is tracked under P3.4. The local
maintenance intake handles the routes listed in the runtime guide.
