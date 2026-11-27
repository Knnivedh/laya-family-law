# Complete Problems & Pending Tasks Ledger (Updated Post-v7 Standalone CUDA Confirmation)

**Updated:** 2026-11-27  
**Baseline `v6` Snapshot:** `live-laya-colab-test-v6-brutal.ipynb` on RTX 5050 Laptop GPU (`79/230` brutal `1.9/10 FAIL`, `16/16` regression, `5/20` sealed fresh, `1/8` sealed Kannada).  
**Latest Locked `v7` Snapshot:** Standalone `src/laya_v7.py` (`mode="laya"`: `PIXMELT/laya` 421M ModernBERT-large bf16 + sentence-split `NLLB-200-distilled-600M` + grounded `laya_v7_evidence.py` + Graph `v4` Stage 2 `laya_v7_graph.py` + `laya_prose_v2.py`) across two byte-equivalent CUDA Confirmation Runs:
- **`Brutal-230` (`custody statutory_primary`):** **`230/230` (`100%`, `415 TP / 0 FP / 0 FN`, `230/230` court, `0` silent, `FpProse=0`, `0.133s/Q`, `10.0/10`)**
- **`16-Q` (`v2` D1-A):** **`14/16` (`micro-F1 0.9808`, `0 FP`, `2 FN` `H6`/`H14` `D-V4-2`, `9.1/10`)**
- **`Sealed Kannada-8` (blind aggregate):** **`4/8` (`micro-F1 0.8205`, `micro_p=1.0`, `0` silent, `6.3/10`, up from `1/8` in `v6`)**
- **`Sealed Fresh-20` (blind aggregate):** **`7/20` (`micro-F1 0.6972`, `micro_p=0.8837`, `micro_r=0.5758`, `2` silent, `4.8/10`)**

This ledger updates `README.md §9` (`P0–P3`) with **every completed item**, **verified `v7` results**, and the exact **remaining `v7.1` blockers** before general public deployment.

---

## 1. Completed items (`v6` Baseline + `v7` Standalone Build & Brutal-230 Confirmation)

| Item | Description | Current Verified State | Evidence / Artifact |
|---|---|---|---|
| **P0.1 – P0.6, P0.8, P3.1** | Live `v6-brutal` execution (`16-Q` + `230-Q` + `20` Fresh + `8` Kannada) & archival | **DONE (RTX 5050 GPU)** — `79/230` (`1.9/10 FAIL`), preserved as frozen `v6` baseline | [`results/live-laya-colab-results-v6-brutal-final.json`](../results/live-laya-colab-results-v6-brutal-final.json), [`results/live-laya-colab-results-v6-brutal.md`](../results/live-laya-colab-results-v6-brutal.md) |
| **P1.1 (Prose Renderer & `Fp` Check)** | Deterministic template-locked renderer covering all 18 sections, 9 escalation kinds, D1-A `hma-27` gating, C8 male/parent roles + automated `Fp` checker | **DONE & WIRED INTO `src/laya_v7.py`** (`246/246` + `15/15` mutants pass, `Fp=0`; `fp_prose=0` across all `274` live `v7` questions; `G12` human rater check still open) | [`src/laya_prose_v2.py`](../src/laya_prose_v2.py), [`tests/test_prose_renderer_v2.py`](../tests/test_prose_renderer_v2.py) |
| **P1.4 / G14 (GPU Latency)** | Verify `<=15s/Q` mean / `<=30s` max on GPU | **VERIFIED ON RTX 5050 GPU** (`v7` brutal mean **`0.133s/Q`**, max **`0.137–0.138s/Q`**, Kannada **`0.315–0.322s/Q`**). CPU fails (`17.8s/Q` local `v6`, `61.93s/Q` Colab `v5`), though `v7 --mode evidence` CPU runs in `0.587s` total without neural weights. Colab T4 `fp16` timing remains unverified | [`results/live-laya-v7-results.md`](../results/live-laya-v7-results.md), [`docs/v7-multilingual-prose-latency-design.md`](v7-multilingual-prose-latency-design.md) |
| **P2.3 (Graph v4 Build & Integrity)** | Repair 3 dangling edges, `'hmga-6' -> 'hmga-1956-s6'`, canonical `related_sections`, and v4 Stage 2 nodes | **DONE** (`Graph v4`: `34` sections / `66` nodes / `99` edges, `0` dangling edges, `7/7` frozen SHAs intact) | [`src/build_graph_v4.py`](../src/build_graph_v4.py), [`graph/laya-crpc-bns-section-decision-tree-v4.json`](../graph/laya-crpc-bns-section-decision-tree-v4.json), [`tests/test_graph_v4.py`](../tests/test_graph_v4.py) |
| **P1.2, P1.3, P1.5, P1.6, P3.2, P3.4, P0.7 (`v7` Standalone & Brutal-230 Confirmation)** | Replace brittle `v6` regex vetoes with clause-aware `laya_v7_evidence.py`, integrate batched sentence-split `PIXMELT/laya` + `NLLB-200-distilled-600M` (`kan_Knda -> eng_Latn`), implement Stage 2 Graph `v4` (`laya_v7_graph.py`), score isolated `tests/v7_backtest.py`, and run two identical locked CUDA Confirmation Runs | **DONE FOR `Brutal-230` (`230/230`, `10.0/10`)** — `Run 1 == Run 2` (`42/42` unit tests pass, `0` silent, `0` `Fb`, `0` `FpProse`). Also preserves Codex 4-split maintenance runtime (`dev 48/48`, `challenge 34/34`, `verification 46/46`, `final_check 32/34`) | [`src/laya_v7.py`](../src/laya_v7.py), [`src/laya_v7_evidence.py`](../src/laya_v7_evidence.py), [`src/laya_v7_extractor.py`](../src/laya_v7_extractor.py), [`src/laya_v7_graph.py`](../src/laya_v7_graph.py), [`tests/v7_backtest.py`](../tests/v7_backtest.py), [`results/live-laya-v7-results.md`](../results/live-laya-v7-results.md) |

---

## 2. Active Problems & Remaining `v7.1` Blockers

### A. Unseen Paraphrase Generalisation Gap (`Sealed Fresh-20`: `7/20`, `Sealed Kannada-8`: `4/8`)

1. **`SEALED-RECALL` (Critical before public chatbot launch):**
   - On frozen **`Brutal-230`**, `v7` hits **`230/230` (`100%`, `10.0/10`)** and `14/16` (`micro-F1 0.9808`, `0 FP`) on **`16-Q`**.
   - On completely unseen blind **`Sealed Fresh-20`** (`7/20`, `micro_p=0.8837`, `micro_r=0.5758`, `2` silent, `38 TP / 5 FP / 28 FN`) and **`Sealed Kannada-8`** (`4/8`, `micro_p=1.0`, `micro_r=0.6957`, `0` silent, `16 TP / 0 FP / 7 FN`), precision remains high (`0` `FpProse`), **but** unseen phrasing drops recall (most affected sections in blind aggregate: `hma-27`, `welfare-principle`, `pwdva-17/18/19`, `hma-13`, `hma-24`, `gwa-1890`, `hmga-1956-s6`).
   - Why `Qwen3-1.7B` was not made primary: diagnostic benchmarking showed `Qwen3-1.7B` hallucinated on direct Kannada (`B-207`, `B-214`) and `16-Q` out-of-scope cases (`H6`, `H13`); clean supervised/synthetic head calibration on `PIXMELT/laya` (without touching or leaking sealed sets) is still needed for `v7.1`.

### B. Governance, Ground Truth, Licensing & Verification Open Items (`D-V4-1..4`, `G12`, `P2.x`, `G14-T4`)

| ID | Open Problem / Task | Status | Required Action |
|---|---|---|---|
| **`D-V4-1`** | **Custody vocabulary split:** `brutal-bank-v1-frozen` expects `[gwa-1890 \| hma-26]` (`statutory_primary`), while `16-Q` and `Sealed-28` require the 3-label bundle (`hmga-1956-s6` + `welfare-principle`) | `OPEN (reported transparently)` | `v7` supports `CUSTODY_VOCAB_PROJECTION` on `Brutal-230`; formal owner/rater ratification of `ground-truth-v3` (`statutory_primary` + `applied_principles`) remains open. |
| **`D-V4-2`** | **`16-Q` Post-D1-A Deltas:** `v7` matches `14/16` (`2` FN: `H6` `pwdva-18`, `H14` `hma-13`) and `13/16` court (`H3/H10/H15` still list `['Family Court', 'Magistrate']` after `hma-27` removal; `safety` kind omitted on 5 GT rows) | `OPEN (design ready)` | Decide whether to issue a frozen `ground-truth-v3` under Gate §6.1 rather than leaving `H6`/`H14`/`H3/H10/H15` as known `v2` deltas. |
| **`D-V4-3`** | **`hma-25` Lump-Sum Settlement Rule:** `B-022, B-119, B-154` have no divorce decree yet expect `hma-25` | `SOLVED IN v7 STAGE 2 / GT NOTE OPEN` | Implemented `lump_sum_settlement` in `src/laya_v7_graph.py` (`0` `Fb` in `Brutal-230`); keep formally documented in adjudicated rule specs. |
| **`P2.1 / P2.2 / D-V4-4`** | Native Kannada speaker check (`C13` + `Sealed Kannada-8`), `G2` amendment sign-off (`16 -> 20`), and pre-D1-A sealed `F8/F9/F10/F16/KN3` / forum checks | `OPEN` | Complete native check & formal sign-offs while keeping frozen sealed files untouched. |
| **`P2.4 / P2.5`** | Unverified legal case citations (*Sukhdev Singh v. Sukhbir Kaur* Feb 2025; *Balkrishna/Babulal/Krishna Kumar Gupta*; HMA 27 paras 3–13, 15–17, 19) | `OPEN` | Independent legal verification before citing in external docs (`src/laya_prose_v2.py` cites ZERO case names, preventing any `Fp` risk). |
| **`G12 / G14-T4 / NLLB-LIC`** | Blind legal rater review on live `v7` prose (`>=3` EN + KN samples), Google Colab T4 `fp16` verification notebook, and noncommercial `NLLB-200` weight license vs Apache-2.0 EN-only/replacement decision | `OPEN` | Collect blind rater sign-off on `laya_prose_v2` outputs, verify Colab T4 latency/parity in a standalone `v7` notebook if Colab distribution is required, and confirm deployment licensing for `facebook/nllb-200-distilled-600M`. |
