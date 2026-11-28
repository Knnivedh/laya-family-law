# LAYA v7.1 — Balanced Multilingual MuRIL + Hybrid Runtime Verification Report

**Date:** 2026-11-28  
**Branch:** `v7.1-chatbot-10x`  
**Classifier Backbone:** `google/muril-base-cased` (`pool_mode="mean_ln"`, 4 epochs on NVIDIA RTX 5050 `bf16`)  
**Training / Dev Split:** `data/synthetic_v7_1_balanced/` (`8,084` balanced train rows; `498` untouched block-disjoint `grouped_dev` rows; `0` 8-gram overlap)  
**Honest Claim Rule:** *No claim of >=70% on truly unseen real user queries until blind/sealed re-runs (`test-bank/sealed/*`, kept unread and unmeasured here) and independent legal review verify it.*

---

## 1. End-to-End Benchmark Summary (Non-Sealed Suites)

| Suite | Rule-Based (`evidence`, CPU) | Pure MuRIL (`classifier`) | Hybrid (`auto`) | Notes / Source |
|---|---:|---:|---:|---|
| **Disjoint `grouped_dev` (`n=498`)** | `314/498` (`63.05%`) | `374/498` (`75.10%`) | **`418/498` (`83.94%`)** | `results/grouped_dev_auto.json`; EN `90.0%`, KN `77.9%` (vs `38.2%`), Kanglish `78.9%` (vs `32.8%`), silent `176 -> 38` |
| **Brutal-230** | `215/230` (`93.5%`, `0` EN miss) | `129/230` (`56.1%`) | **`227/230` (`98.7%`)** | `results/laya_v71_muril_auto.json`; `TP/FP/FN [410, 0, 5]`, **`micro-F1 0.9939`**, **`C13` KN `13/16` (`81.25%`)**, `per_cat_min 0.8125 >= 0.75`, `1` silent (`B-206`, so §3.2 `silent_0` stays `N`) |
| **Frozen `validation-500`** | `261/500` (`52.2%`) | **`493/500` (`98.6%`)** | **`466/500` (`93.2%`)** | `results/laya_v71_muril_auto.json`; leaky proxy vs `train.jsonl` (`500/500` block overlap); `silent 212 -> 2` |
| **16-Q (`v2` D1-A GT)** | **`14/16` (`87.5%`)** | `10/16` (`62.5%`) | **`14/16` (`87.5%`)** | `results/laya_v71_muril_auto.json`; `micro-F1 0.9808`, `51 TP / 0 FP`, `Fb=3`, `Fp=0`, `7.6/10` capped |
| **Kaanoon-28 (`heldout`)** | **`14/28` (`50.0%`)** | `8/28` (`28.6%`) | **`14/28` (`50.0%`)** | Real lay phrasing with graph-derived labels; requires independent legal adjudication |

---

## 2. Live HTTP Chatbot (`POST /v1/assess`, Turn-1 Non-Sealed, `0` HTTP Errors across `1,548` requests)

| Suite | `evidence` Mode (`p95 ms`) | `auto` Hybrid Mode (`p95 ms`) | Notes |
|---|---:|---:|---|
| `validation-500` exact provisions | `219/500` (`29.60 ms`) | **`369/500` (`65.05 ms`)** | Delivered exact answers jumped **`133/500 -> 283/500`**; stalled `needs_review` dropped **`282 -> 58`** |
| `brutal-230` exact provisions | `169/230` (`29.47 ms`) | **`181/230` (`51.21 ms`)** | `357 TP / 0 FP`; `needs_review` dropped **`21 -> 6`** |
| `16-Q` exact provisions | `13/16` (`28.67 ms`) | **`13/16` (`31.05 ms`)** | `40 TP / 0 FP`, `12/16` with delivered answer |
| `kaanoon-28` exact provisions | `10/28` (`36.45 ms`) | **`10/28` (`46.55 ms`)** | HMA routes intentionally await Turn-2 applicability confirmation (`needs_clarification=6`) |

---

## 3. Verification Gates & What Remains Before Public `10/10`

- **Passing gates (`src/` + `tests/`):** `124` unit tests (`4.17s`), Graph v4 integrity + `7/7` frozen SHAs (`34` sections / `66` nodes / `99` edges), `100%` Graph Contract coverage (`61/61` keys, `0` uncovered), `test_prose_renderer_v2` (`246/246` + `15/15` mutants, `Fp=0`), `check_ngram_leakage.py --strict` (`0` 8-gram overlap), and `license` (`0` CC-BY-NC default dependencies). `latency-determinism` remains blocked until ONNX int8 student export (`models/student_int8.onnx`).
- **Remaining gaps to `10/10`:**
  1. Statutory expansion documented in `docs/statutory-gaps-government-sources.md` (Muslim Women Acts 1986/2019, Divorce Act 1869, Parsi/Foreign Marriage Acts, HAMA §§18–22, JJ Act §61 DM adoption forum, Parents & Senior Citizens §12 election bar, RBD §§13 vs 15 split, BNSS §531 / BNS §358 pre-July-2024 savings).
  2. Primary-authority legal verification (`8/9` cases in `legal/verified_authorities.json` remain unverified) and multi-turn independent lawyer adjudication on real citizen chats.
  3. Blind confirmation on frozen `test-bank/sealed/` and out-of-distribution English real-question recall (bridging `Kaanoon-28` from `50%` and pure classifier `hn_b`/`neg` generalization toward `>= 90%` without rule fallback).
