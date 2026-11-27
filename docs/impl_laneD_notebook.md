# Lane D — Colab Notebook (`notebooks/laya_v71_train_backtest.ipynb`)

Owner: Lane D. Contract: C4 (see `docs/impl_swarm_state.md`). Status: **done,
verified on this VM (CPU, no torch) for the smoke path; GPU cells are written
and grounded but cannot execute here — first real GPU run is the user's Colab T4.**

## 1. Deliverable

- `notebooks/laya_v71_train_backtest.ipynb` — 21 cells (9 markdown, 12 code),
  nbformat-validated, JSON-valid. Runs top to bottom on a free Colab T4 with
  no manual edits beyond flipping `CPU_SMOKE_TEST` to `False` (and the clone
  path, which needs no edit — it clones to `/content/laya-family-law`).
- This file (`docs/impl_laneD_notebook.md`) — status, verification, open items.

No other files were created or edited by Lane D. No frozen file touched.
Lane B's uncommitted edits (`src/laya_v7_classifier.py`,
`scripts/train_v71_classifier.py`) were read only — NOT committed, NOT edited.

## 2. Cell map

| # | Kind | What it does |
|---|---|---|
| 0 | md | Purpose, Colab-only rule, honest claim rule, how to run |
| 1 | code `cpu_smoke` | `CPU_SMOKE_TEST = True` (default), `EXPECTED_VAL_SHA256`, `sh()` helper |
| 2 | code `cpu_smoke` | Clone (GPU mode only) + resolve `REPO_ROOT` + print repo HEAD |
| 3 | md | ⚠️ PUSH DEPENDENCY (see §4) |
| 4 | code | `nvidia-smi` (GPU mode only) |
| 5 | code | `pip install torch transformers sentencepiece` + version print + torch/CUDA check (GPU mode only) |
| 6 | code `cpu_smoke` | Verify frozen validation sha256 `7640d067…` + train/val counts; asserts before anything else |
| 7 | code `cpu_smoke` | CPU smoke test — `src/laya_integrated.py --self-test` + 16-Q spot check, first 5 (rule-based). Runs in BOTH modes. |
| 8 | md | 3-backbone smoke test (no predetermined winner) |
| 9 | code | `scripts/smoke_backbones.py --help` + bare run (GPU mode only; loud SKIP if absent from the checkout) |
| 10 | md | Train Run #1 config table + OOM fallback + learning-curve decision rule |
| 11 | code `cpu_smoke` | `--check-data-only` (CPU-safe; expected `OK: train=7500 val=500`) |
| 12 | code | Nested curve: `--train-subset 2000` → `models/v71-classifier-2k`, `4000` → `models/v71-classifier-4k`, full 7500 → `models/v71-classifier` (GPU mode only) |
| 13 | code | `--eval-checkpoint` each best checkpoint on frozen validation 500 (GPU mode only) |
| 14 | code | Learning-curve results table from each `train_log.jsonl` (GPU mode only; `NOT RUN` rows, never invented numbers) |
| 15 | md | OOF calibration contract |
| 16 | code | OOF dump on TRAIN split only + `scripts/calibrate_thresholds.py` (GPU mode only; loud SKIP if absent) |
| 17 | md | Backtest gates, incl. the Brutal-230 discrepancy (§5) |
| 18 | code | `tests/integrated_backtest.py --mode classifier --suite all --checkpoint models/v71-classifier/best/model.pt` + `--mode rule-based` comparison (GPU mode only; loud SKIP if absent) |
| 19 | md | Phase E — **no sealed re-run cell, deliberately** |
| 20 | code | Run summary: which artifacts exist on disk + open items + claim rule |

Training config (task spec + `scripts/train_v71_classifier.py` docstring,
FALLBACK-2 as amended by the GPT re-run — supersedes the pre-amendment Phase B
config in `docs/70-percent-plan.md` §3): mmBERT-base first,
`--loss weighted_ce`, `--pooling one_pass`, max_seq_len 320, max-clauses 8,
bf16, micro-batch 8 / grad-accum 2 (effective 16 — a TARGET, not guaranteed;
on OOM the script fails loudly suggesting `--batch-size 4 --grad-accum 4`),
max 4 epochs, `--patience 2`, lr 2e-5 encoder / 1e-4 heads, linear warmup
10% → cosine decay (built into the script's `LambdaLR`), weight decay 0.01,
seed 42. `--class-weights` is NOT in the Run #1 command — neither the task
spec nor Lane B's docstring command includes it; toggling it needs its own
before/after numbers (Lane 04 doc §8). Verified in the tree: the scheduler
is warmup+cosine, `--train-subset`, `--loss`, `--pooling`, `--head-lr`,
`--bf16`, `--dump-predictions` all exist as flags.

Calibration CLI is the LANDED script's real interface (verified
`--help` on this VM, 2026-11-27): `--oof-predictions … --train-file
data/synthetic_v7_1/train.jsonl --checkpoint-dir models/v71-classifier/best
--kappas 50,150,300 --max-passes 3`. OOF on Train-7500 ONLY, never Val-500;
the script refuses validation files.

Backtest CLI matches contract C3 and the landed harness (`--help` verified):
`--mode {auto,rule-based,classifier} --suite {all,validation,kaanoon,16q,brutal}
[--checkpoint …] --json-out <path>`; sealed suites refused by the harness.
The notebook passes `--checkpoint models/v71-classifier/best/model.pt`
explicitly (the C2 default).

## 3. Verification on this VM (CPU, no torch)

- `python3 -m json.tool` on the notebook — OK. `nbformat.validate` — OK.
  Code cells reference **no sealed file** (asserted in the build check; the
  sealed filenames appear only in the Phase E markdown cell, as names, never
  loaded).
- CPU smoke-test cells (tagged `cpu_smoke`, extracted verbatim and run as a
  plain script, exit 0):
  - `REPO_ROOT` resolved; HEAD printed (`792c75f…` at verification time).
  - Frozen validation sha256 matches `7640d067…`; `train=7500 val=500`.
  - `--self-test` ran end to end (rule-based; 3 questions, 12 C1 keys).
  - 16-Q spot check: **5/5 exact** (K0, H1–H4; full-set baseline 14/16,
    known misses H6/H14).
  - `--check-data-only`: `OK: train=7500 val=500 (torch NOT needed for this
    mode)`; `n_skipped` 0/0, no unknown issue/fact keys.
- Extra verification (not required by the task, done because the harness
  landed mid-task): full harness run `python3
  tests/integrated_backtest.py --mode rule-based --suite all --json-out
  /tmp/laneD_harness_rulebased.json` — exit 0, all four suites reproduced
  their baselines exactly: validation **261/500 (52.2%)**, Kaanoon **14/28
  (50.0%)**, 16-Q **14/16**, Brutal **210/230** (see §5 — this is the
  discrepancy, not a typo). Validation + brutal sha256 both `ok: true` in
  the harness JSON.
- Guardrails: `python3 tests/test_graph_v4.py` PASS (34 sections / 66 nodes
  / 99 edges, 0 dangling, 7/7 frozen hashes intact);
  `python3 tests/test_prose_renderer_v2.py` PASS (246 cases, Fp=0, 15/15
  mutants); `python3 -m unittest discover -s tests -p "test_*.py"` — Ran 66
  tests, OK.
- `python3 -m py_compile` on the extracted smoke script — OK. No helper
  `.py` files were created by Lane D (the notebook builder lives in `/tmp`,
  not the repo).

## 4. Push dependency (plainly)

The GPU cells need the coordinator's push first. Status at Lane D commit time:

- ON GitHub already (per shared state): everything up to HEAD `90e20c5`
  plus nothing else — the notebook clones `main`.
- In the working copy but NOT on GitHub: `src/laya_integrated.py` (Lane C,
  committed locally `792c75f`); `tests/integrated_backtest.py`,
  `scripts/smoke_backbones.py`, `scripts/calibrate_thresholds.py`
  (Lanes E/A/B — **landed in the working copy, uncommitted, while this
  notebook was being written**; their real CLIs are used in the notebook
  and verified via `--help`); `src/laya_v7_classifier.py` +
  `scripts/train_v71_classifier.py` (Lane B — **uncommitted edits in
  progress**).
- The notebook prints the repo HEAD it runs from so a stale checkout is
  visible, and every GPU cell that calls a not-yet-pushed file prints a loud
  SKIP instead of failing silently if the file is absent from the checkout.

## 5. ⚠️ Brutal-230 discrepancy — found by Lane D, needs the coordinator

The task spec and shared state say Brutal-230 "must stay 230/230". Measured
through the C1 integrated runtime + C3 harness on this VM, the rule-based
reference is **210/230 (91.3%, micro-P/R 0.9974/0.9205, silent 15)** — and
the harness's own baselines block confirms it (pre-recall-swarm reference
215/230, current-code reference 210/230, measured 210/230 = MATCH). The
"230/230" figure is from the **v7 live run** (a different code path, RTX),
not from the integrated runtime. The notebook records this honestly in its
backtest cell: the classifier gate through this notebook is **do not regress
below 210/230 on Brutal-230**, with closing the gap toward 230/230 as the
aspiration, not the measured C1 baseline. Do not report a classifier Brutal
number against 230/230 as if 230/230 were the C1 baseline. The coordinator
owns reconciling the 230/230 (v7 live) vs 210/230 (C1 harness) gap — Lane D
did not change any code or gate to hide it.

## 6. Colab steps for the user (exact)

1. Wait for the coordinator to confirm the push has landed (see §4).
2. Open `notebooks/laya_v71_train_backtest.ipynb` in Google Colab.
3. Runtime → Change runtime type → **T4 GPU**.
4. In the first code cell set `CPU_SMOKE_TEST = False`.
5. Runtime → Run all.
6. Watch the printed HEAD (cell 2) — it must be at/after the pushed HEAD
   the coordinator announced. Watch the per-subset training lines, the
   learning-curve table (cell 14), the calibration output, and the backtest
   per-set exact / micro-P / micro-R / silent + frozen gate rating.
7. Report back: the per-epoch lines, the `section-exact:` lines, the
   backtest JSONs under `results/`, and whether any gate in §2/§5 failed.
   No ≥70% claim until a sealed re-run measures it (Phase E, separate
   session after Phase D gates pass).

## 7. Still open

- GPU cells have never executed (no GPU/torch on this VM). First real run
  is the user's Colab T4.
- `scripts/smoke_backbones.py` is called with no arguments (its defaults);
  Lane A may document a preferred invocation — if it does, the notebook
  cell should be updated to match before the GPU run.
- Lane B's classifier/train-script edits are uncommitted; if Lane B changes
  any flag the notebook passes (`--train-subset`, `--loss`, `--pooling`,
  `--head-lr`, `--bf16`, `--dump-predictions`, `--eval-checkpoint`), the
  notebook must be re-grounded at merge time.
- The 16-Q spot check in the CPU smoke path covers the first 5 questions
  only; the full 16-Q gate runs in the harness cell (`--suite 16q`).
- Phase D (300-item independent holdout) and Phase E (sealed re-run) are
  out of scope for this notebook by design.
