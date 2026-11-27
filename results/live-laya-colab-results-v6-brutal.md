# LIVE Laya inference test — v6-brutal (RTX 5050 GPU, Laya 421M + v3 graph)

**Run Date:** 2026-11-27  
**Runtime:** Local Windows 11, **NVIDIA GeForce RTX 5050 Laptop GPU** (`cuda:0`, `bf16` autocast via `laya==0.5.5`, `torch==2.11.0+cu128`)  
**Model:** `PIXMELT/laya` classic `LayaTypedDecisions` ModernBERT-large (`421M`, `model.safetensors` SHA-256 `891102d3...`, load `7.6s`)  
**Runner:** [`src/run_v6_brutal_local.py`](../src/run_v6_brutal_local.py) executing [`notebooks/live-laya-colab-test-v6-brutal.ipynb`](../notebooks/live-laya-colab-test-v6-brutal.ipynb) Cells `3..23` verbatim (all 6 frozen SHA-256 digests verified canonical LF before run; zero threshold/gate tuning between batches `B1..B10`).  
**GPU vs Colab CPU Parity:** On the 16-question regression set across 160 raw Stage 1 prompts, local RTX 5050 (`bf16`) vs Colab CPU `v5` (`results/live-laya-colab-results-v5.json`) measured **`mean_abs_diff = 0.002306`**, `max_abs_diff = 0.025300` (`H6.divorce`), **zero differences in fired issues**, and identical `16/16` exact section matches.

---

## 1. Aggregate Results Across All 4 Evaluation Sets (`274` Live Questions, `132.48s` Total)

| Set | Questions | Exact Match | Micro P / R / F1 | TP / FP / FN | Court Correct | Esc-Bool | Esc-Kinds (Strict / Fact-Excl) | Silent (`kept=[]`) | `Fb` (pre-recheck) | `Fp` (prose) | Errors | Mean / Max Latency | Rating (/10) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| **16-Q Regression (`v2` D1-A GT)** | 16 | **16/16** (`100%`) | `1.000 / 1.000 / 1.000` | `53 / 0 / 0` | `13/16` (`H3,H10,H15`) | `16/16` | `11/16` / `11/16` | `0` | `0` | NOT MEASURED | `0` | `0.52s / 1.51s` | `9.9` raw → **`9.0` capped** |
| **Brutal Bank (`B-001..B-230`)** | 230 | **79/230** (`34.3%`, 95% CI `0.285–0.407`) | `0.750 / 0.542 / 0.629` | `225 / 75 / 190` | `152/230` (`66.1%`) | `144/230` (`62.6%`) | `48/230` / `70/230` | `75` (`60 EN, 15 KN`) | `5` (`B-018,118,131,150,187`) | NOT MEASURED | `0` | `0.43s / 1.00s` | **`1.9 / 10` (`FAIL`)** |
| — *Brutal English (`n=214`)* | 214 | **78/214** (`36.4%`) | `0.750 / 0.581 / 0.655` | `225 / 75 / 162` | `151/214` | — | — | `60` | — | NOT MEASURED | `0` | — | — |
| — *Brutal Kannada (`n=16`, C13)* | 16 | **1/16** (`6.2%`, `B-218` `gt=[]`) | `0.000 / 0.000 / 0.000` | `0 / 0 / 28` | `1/16` | `0/16` | `0/16` | `15` | `0` | NOT MEASURED | `0` | `0.53s` | — |
| **Sealed Fresh-20 (`F1..F20`)** | 20 | **5/20** (`25.0%`) | `0.868 / 0.500 / 0.635` | `33 / 5 / 33` | `8/20` | `17/20` | `6/20` / `7/20` | `3` (`F5,F6,F11`) | `1` (`F4`) | NOT MEASURED | `0` | `0.45s` | — (`3.6` formula) |
| **Sealed Kannada-8 (`KN1..KN8`)** | 8 | **1/8** (`12.5%`) | `1.000 / 0.043 / 0.083` | `1 / 0 / 22` | `1/8` | `1/8` | `1/8` / `5/8` | `6` (`KN1..4,6,7`) | `0` | NOT MEASURED | `0` | `0.57s / 0.84s` | — (`1.4` formula) |

*Note:* Dropping the brutal-bank custody vocabulary mismatch (`hmga-1956-s6`, `welfare-principle`, absent in `brutal-bank-v1-frozen.json`) yields `84/230` (`36.5%`) exact and `0.644` micro-F1 (`TP=225, FP=59, FN=190`).

---

## 2. Brutal-230 Per-Category Breakdown (`C1–C14`)

| Cat | N | Exact | Exact % | Micro F1 | Court | Esc-Bool | Esc-Kinds (Strict) | Silent | Mean Lat |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `C1` | 30 | `3/30` | `10.0%` | `0.633` | `23/30` | `24/30` | `3/30` | `6` | `0.49s` |
| `C2` | 20 | `14/20` | `70.0%` | `0.892` | `18/20` | `20/20` | `9/20` | `2` | `0.44s` |
| `C3` | 20 | `10/20` | `50.0%` | `0.771` | `17/20` | `15/20` | `3/20` | `2` | `0.46s` |
| `C4` | 20 | `8/20` | `40.0%` | `0.680` | `12/20` | `15/20` | `8/20` | `7` | `0.43s` |
| `C5` | 20 | **`0/20`** | **`0.0%`** | `0.071` | `5/20` | `8/20` | `0/20` | `18` | `0.36s` |
| `C6` | 16 | `6/16` | `37.5%` | `0.591` | `15/16` | `6/16` | `4/16` | `4` | `0.42s` |
| `C7` | 16 | `7/16` | `43.8%` | `0.767` | `13/16` | `13/16` | `4/16` | `3` | `0.44s` |
| `C8` | 12 | `2/12` | `16.7%` | `0.370` | `6/12` | `9/12` | `5/12` | `4` | `0.45s` |
| `C9` | 16 | `7/16` | `43.8%` | `0.605` | `10/16` | `10/16` | `3/16` | `5` | `0.41s` |
| `C10` | 12 | **`11/12`** | **`91.7%`** | `0.000` | `11/12` | `1/12` | `0/12` | `0` | `0.30s` |
| `C11` | 12 | `6/12` | `50.0%` | `0.750` | `10/12` | `7/12` | `3/12` | `2` | `0.38s` |
| `C12` | 8 | **`0/8`** | **`0.0%`** | `0.300` | `3/8` | `6/8` | `4/8` | `3` | `0.43s` |
| `C13` | 16 | `1/16` | `6.2%` | `0.000` | `1/16` | `0/16` | `0/16` | `15` | `0.53s` |
| `C14` | 12 | `4/12` | `33.3%` | `0.708` | `8/12` | `10/12` | `2/12` | `4` | `0.31s` |

---

## 3. Brutal-230 Per-Section Confusion (`TP / FP / FN`) & Key Root Causes

- `bnss-144`: `79 / 14 / 23` · `pwdva-20`: `68 / 25 / 22` · `bns-316`: `23 / 5 / 18` · `hma-13`: `19 / 5 / 5` · `pwdva-18`: `12 / 6 / 19`
- `gwa-1890`: `7 / 1 / 41` · `pwdva-17`: `5 / 1 / 16` · `pwdva-19`: `5 / 1 / 16` · `hma-24`: `3 / 1 / 3` · `births-deaths-act-1969`: `3 / 0 / 4`
- `hma-27`: `1 / 0 / 8` · `hma-13b`: `0 / 0 / 5` · `hma-25`: `0 / 0 / 4` · `hma-26`: `0 / 0 / 4` · `hma-9`: `0 / 0 / 1` · `pwdva-22`: `0 / 0 / 1`
- Custody vocabulary mismatch FPs: `hmga-1956-s6` (`FP=8`), `welfare-principle` (`FP=8`)

**Top Measured Failure Drivers (`190` FNs, `75` Silent):**
1. **English regex hard-vetoes overfit to the 16-set:** In `35/60` English silent questions, full-text `stage1_raw` was already above threshold before v5 regex gates zeroed it out (`gwa-1890` gated by `_CUSTODY_PATTERNS`: `37`; `bnss-144`/`pwdva-20` gated by `money_fact=False`: `17`/`16`; `pwdva-17/19` gated by `residence_claim=False`: `13` each; `hma-27` gated by `gold_fact=False` on joint property: `8`).
2. **Kannada script blindness (`C13` `1/16`, `Sealed Kannada-8` `1/8`):** English regex gates + English-only `PIXMELT/laya` produced `0/28` section hits on `C13`.
3. **Stage 2 missing routes & hardcoding:** `hma-13b` never emitted (`5`), `hma-9`/`pwdva-22` unrouted (`2`), `hma-25` pre-decree lump sum & settlement blocked, male claimants (`C8`) getting `pwdva-20`/`bnss-144`, `pwdva-17/18/19` bundled together on `C7`/`C9`, `Fb=5` (`B-018, 118, 131, 150, 187` proposing `hma-24` with pending=False — all caught after recheck).
4. **Raw paraphrase/threshold drops:** `stridhan=0.50` missed `14` English `bns-316` queries (`0.098–0.494`), while `"monthly money"` / negated `"do not want monthly money"` triggered `maintenance=0.10` FPs (`B-058`).
5. **16-Q & Sealed Post-D1-A Deltas:** On the 16-set, `H3/H10/H15` kept `court_expected=['Family Court','Magistrate']` despite D1-A removing `hma-27` (leaving `Magistrate` only -> `13/16` court), and `gt_escalation_kinds` lacked `safety` (`11/16`).
