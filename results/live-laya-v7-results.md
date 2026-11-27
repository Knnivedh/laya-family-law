# LAYA v7 Verification & Confirmation Results

**Date:** 2026-11-27  
**Runtime:** `src/laya_v7.py` (`mode="laya"` default: `PIXMELT/laya` 421M ModernBERT-large bf16 sentence-split + `facebook/nllb-200-distilled-600M` Kannada→English + clause-aware `src/laya_v7_evidence.py` + Graph `v4` Stage 2 `src/laya_v7_graph.py` + `src/laya_prose_v2.py`)  
**Hardware:** Local RTX 5050 Laptop GPU (`--device cuda`) & CPU evidence-only baseline (`--device cpu`)  
**Archived Logs:** [`live-laya-v7-run1.log`](live-laya-v7-run1.log) · [`live-laya-v7-run2.log`](live-laya-v7-run2.log)

---

## 1. Locked Confirmation Runs (`Run 1` vs `Run 2` — Byte-Equivalent Predictions)

Command executed twice identically on locked code without edits between runs:

```powershell
$env:PYTHONUTF8="1"
..\.laya_venv\Scripts\python.exe -m tests.v7_backtest --suite all_with_sealed --mode laya --device cuda --misses 0
```

| Suite | Exact | Wilson 95% CI | Micro-P / Micro-R / Micro-F1 | TP / FP / FN | Mean-P / Mean-R | Court | Esc Bool | Esc Kinds (Strict / FE) | Silent / FpProse / Err | Mean Latency (Run 1 / Run 2) | Total Wall (Run 1 / Run 2) | Rating |
|---|---:|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|
| **`16-Q`** (`v2` D1-A) | **14/16** | `[0.6398, 0.965]` | `1.0` / `0.9623` / `0.9808` | `51 / 0 / 2` | `1.0` / `0.9786` | `13/16` | `16/16` | `7/16` / `8/16` | `0 / 0 / 0` | `0.840s` / `0.816s` | `13.435s` / `13.049s` | **9.1** |
| **`Brutal-230`** (custody `statutory_primary`) | **230/230** | `[0.9836, 1.0]` | `1.0` / `1.0` / `1.0` | `415 / 0 / 0` | `1.0` / `1.0` | `230/230` | `230/230` | `191/230` / `216/230` | `0 / 0 / 0` | `0.133s` / `0.133s` | `30.620s` / `30.517s` | **10.0** |
| **`Sealed Fresh-20`** *(blind aggregate)* | **7/20** | `[0.1812, 0.5671]` | `0.8837` / `0.5758` / `0.6972` | `38 / 5 / 28` | `0.7875` / `0.6176` | `7/20` | `18/20` | `3/20` / `3/20` | `2 / 0 / 0` | `0.124s` / `0.125s` | — | **4.8** |
| **`Sealed Kannada-8`** *(blind aggregate)* | **4/8** | `[0.2152, 0.7848]` | `1.0` / `0.6957` / `0.8205` | `16 / 0 / 7` | `1.0` / `0.7851` | `5/8` | `7/8` | `1/8` / `1/8` | `0 / 0 / 0` | `0.322s` / `0.315s` | — | **6.3** |

### Per-Suite Notes Observed in Run 1 & Run 2
- **`Brutal-230`:** `14/14` categories hit `100%` (`per_cat_min=1.0`, `latency_max_s=0.138s` Run 1 / `0.137s` Run 2). Compared to `v6` baseline (`79/230`, `micro_f1=0.629`, `75` silent, `1.9/10`), `v7` moved to `230/230`, `415 TP / 0 FP / 0 FN`, `230/230` court, `0` silent, `FpProse=0`, **`10.0/10`**.
- **`16-Q` (`2` FN):** `pwdva-18: 1` (`H6` legacy `v2` vs `v4` interpretation) and `hma-13: 1` (`H14` `D-V4-2` intentional v4 behavior, already noted in the frozen GT/blueprint).
- **`Sealed Fresh-20` (`top_fn_sections`):** `hma-27: 4, welfare-principle: 3, pwdva-17: 3, pwdva-18: 3, pwdva-19: 3, hma-13: 2, hma-24: 2, gwa-1890: 2, hmga-1956-s6: 2, hma-25: 1, bns-316: 1, hma-26: 1` (`2` silent, `38 TP / 5 FP / 28 FN`).
- **`Sealed Kannada-8` (`top_fn_sections`):** `pwdva-18: 2, hma-27: 1, bnss-144: 1, pwdva-20: 1, pwdva-19: 1, pwdva-17: 1` (`0` silent, `0 FP`, improved from `1/8` in `v6` to `4/8` with `micro_p=1.0` and `court_correct=5/8`).

---

## 2. Zero-Model CPU Baseline (`mode="evidence"`) vs `v7` CUDA (`mode="laya"`)

Command:

```powershell
..\.laya_venv\Scripts\python.exe -m tests.v7_backtest --suite both --mode evidence --device cpu --misses 0
```

| Suite | Mode | Exact | Micro-P / Micro-R / Micro-F1 | TP / FP / FN | Court | Esc Bool | Esc Kinds (Strict / FE) | Silent | Wall | Rating |
|---|---|---:|---|---:|---:|---:|---|---:|---:|---:|
| **`16-Q`** | `evidence` (`cpu`) | `14/16` | `1.0` / `0.9623` / `0.9808` | `51 / 0 / 2` | — | — | — | — | `0.051s` | `9.1` |
| **`Brutal-230`** | `evidence` (`cpu`) | `215/230` *(214/214 EN, `C13=1/16`)* | `1.0` / `0.9325` / `0.9651` | `387 / 0 / 28` | `215/230` | `230/230` | `184/230` / `205/230` | `15` | `0.587s` | `9.4` |
| **`Brutal-230`** | `laya` (`cuda`) | **`230/230`** *(incl. `C13=16/16`)* | **`1.0` / `1.0` / `1.0`** | **`415 / 0 / 0`** | **`230/230`** | **`230/230`** | **`191/230` / `216/230`** | **`0`** | `30.620s` | **`10.0`** |

**Architecture takeaway (`Qwen3-1.7B` vs `PIXMELT/laya` + `NLLB-200`):**
- Diagnostic probing of `Qwen3-1.7B` (`1`-token YES/NO & direct Kannada) observed hallucinations on direct Kannada (`B-207`, `B-214`) and `16-Q` out-of-scope cases (`H6`, `H13`).
- `PIXMELT/laya` (bf16 sentence-split) paired with sentence-split `NLLB-200-distilled-600M`, grounded evidence (`src/laya_v7_evidence.py`), and Graph `v4` Stage 2 (`src/laya_v7_graph.py`) is therefore the primary `v7` runtime (`mode="laya"`).

---

## 3. Maintenance Runtime Regression (Codex 4-Split Benchmark on CUDA)

| Split | Exact | Positive Exact | Provision TP / FP / FN | Correct Required Clarifications | Warm Median | Warm Max |
|---|---:|---:|---|---:|---:|---:|
| `development` | **48/48** | `24/24` | `26 / 0 / 0` | `4/4` | `0.4392s` | `0.6656s` |
| `challenge` | **34/34** | `15/15` | `17 / 0 / 0` | — | `0.4190s` | `0.5106s` |
| `verification` | **46/46** | `23/23` | `25 / 0 / 0` | `5/5` | `0.3871s` | `0.6681s` |
| `final_check` | **32/34** | `19/21` | `21 / 0 / 2` | `3/3` | `0.4111s` | `0.5190s` |

---

## 4. Unit, Graph v4, Frozen-Hash & Prose Validation

- **`unittest` (`test_*.py`):** `42` tests ran (`0` failures, `0` skips; 32 Codex maintenance tests + 10 `v7` rule, prose safety, scorer-isolation, and batch permutation invariance tests).
- **Graph v4 & frozen SHAs (`tests.test_graph_v4`):** `34 sections / 66 nodes / 99 edges, 0 dangling edges, 7/7 frozen hashes intact`.
- **Prose Renderer v2 (`tests.test_prose_renderer_v2`):** `246 cases, Fp=0, quality_flags=0, 15/15 adversarial mutants caught, mean=0.0295ms, max=0.122ms`.

---

## 5. Honest Open Gaps (Before Production Public Chatbot Use)

1. **Unseen English & Kannada Paraphrase Recall (`Sealed Fresh-20`: `7/20`, `Sealed Kannada-8`: `4/8`):** Precision is strong (`0.8837` EN, `1.0` KN) with zero unsafe prose violations (`fp_prose=0`), but recall (`0.5758` EN, `0.6957` KN) shows that unseen paraphrase wording still drops sections without rule/paraphrase generalization (`hma-27`, `welfare-principle`, `pwdva-17/18/19`, `hmga-1956-s6`, `gwa-1890`, etc.).
2. **Legacy vs `v4` GT Deltas & Unclosed Gate Items (`G12`, `P2.1`, `P2.4`, `G14-T4`):** `16-Q` `H6`/`H14` deltas remain unchanged per frozen `v2` GT policy; blind legal rater sign-off on live prose (`G12`), native Kannada speaker audit (`P2.1`), live case-law URL/citation check (`P2.4`), `NLLB-200` license vs Apache-2.0 fallback decision, and Colab T4 `fp16` timing (`G14-T4`) remain open for `v7.1`.
