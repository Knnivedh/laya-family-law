# Complete Problems & Pending Tasks Ledger (Updated Post-v6 Brutal Run)

**Updated:** 2026-11-27  
**Baseline Run Completed:** `live-laya-colab-test-v6-brutal.ipynb` executed locally on **RTX 5050 Laptop GPU** (`274` live questions in `132.48s`; `16/16` regression, `79/230` brutal `1.9/10 FAIL`, `5/20` sealed fresh, `1/8` sealed Kannada).

This ledger updates `README.md §9` (`P0–P3`) with **every completed item**, **newly built v4 artifacts**, **newly discovered brutal-230 failures**, and the exact remaining path to an uncapped **10/10**.

---

## 1. Completed Since Previous Repo Snapshot (`P0`, `P1.1`, `P1.4` GPU, `P2.3`, `P3.1`)

| Item | Description | Current Verified State | Evidence / Artifact |
|---|---|---|---|
| **P0.1 – P0.6, P0.8, P3.1** | Live `v6-brutal` execution (`16-Q` + `230-Q` `B1..B10` + `20` Fresh + `8` Kannada) + latency + Wilson CI + pass/fail table + filing into `results/` | **DONE (RTX 5050 GPU)** — `79/230` (`34.3%`) brutal, `16/16` regression, `5/20` fresh, `1/8` Kannada, `0.43s/Q` brutal mean, **`1.9/10` (`FAIL`)** | [`results/live-laya-colab-results-v6-brutal-final.json`](../results/live-laya-colab-results-v6-brutal-final.json), [`results/live-laya-colab-results-v6-brutal.md`](../results/live-laya-colab-results-v6-brutal.md), [`src/run_v6_brutal_local.py`](../src/run_v6_brutal_local.py) |
| **P1.1 (Prose Renderer & `Fp` Check)** | Deterministic template-locked renderer covering all 18 sections, 9 escalation kinds, D1-A `hma-27` gating, C8 male/parent roles + automated `Fp` checker | **BUILT & UNIT-TESTED (`246/246` + `15/15` mutants, `Fp=0`)** — ready to wire into `v7` notebook Cell 9 (`G12` blind human audit still open) | [`src/laya_prose_v2.py`](../src/laya_prose_v2.py), [`tests/test_prose_renderer_v2.py`](../tests/test_prose_renderer_v2.py) *(also caught/fixed `Section 27` leak in `docs/v6-lane4-prose-latency.md` §2.3.3)* |
| **P1.4 / G14 (GPU Latency + Batching)** | Verify `<=15s/Q` mean / `<=30s` max on GPU and benchmark `predict_batch` optimizations | **VERIFIED ON RTX 5050 GPU** (`0.43s/Q` sequential-cell brutal run; `0.303s/Q` warmed `fp16` batched). CPU still fails (`17.8s/Q` local, `61.93s/Q` Colab). Colab T4 `fp16` timing remains unverified | [`docs/v7-multilingual-prose-latency-design.md`](v7-multilingual-prose-latency-design.md) |
| **P2.3 (Graph v3 Dangling Edges & `hmga-6`)** | Repair `escalate_clarify`, `bns-316`, `escalate_demand_first`, `'hmga-6' -> 'hmga-1956-s6'`, canonical `related_sections` & `laya_question`, plus v4 Stage 2 nodes | **BUILT & TESTED (`Graph v4`: `34` sections / `66` nodes / `99` edges)** (`v1/v2/v3` frozen intact) | [`src/build_graph_v4.py`](../src/build_graph_v4.py), [`graph/laya-crpc-bns-section-decision-tree-v4.json`](../graph/laya-crpc-bns-section-decision-tree-v4.json), [`tests/test_graph_v4.py`](../tests/test_graph_v4.py) |

---

## 2. All Active Problems & Open Tasks (Prioritized for `v7` -> `10/10`)

### A. Accuracy & Generalisation Blockers Exposed by Live `v6-brutal` (`79/230 -> >=200/230`)

1. **PROB-1 (Critical — `35/60` English Silent Questions): Overfit English Regex Hard-Vetoes (`derive_facts_from_text`)**
   - `_CUSTODY_PATTERNS` + `_RESIDENCE_COLOC_RE` caused `37` `gwa-1890` misses & `0/20` on `C5`; `money_fact` caused `17/16` `bnss-144/pwdva-20` misses (`0/8` on `C12` arrears/variation); `gold_fact` blocked all `8` `hma-27` joint property cases; `residence_claim` blocked `13` `pwdva-17/19` cases.
   - **Verified probe fix:** Semantic prompts reduced English silent misses from `60/214` to `1/94` (`89.3%` recall), but zero-shot precision hit `0.702` (`F1=0.786`).
   - **Pending Action (`P1.2`):** Build trained lightweight Stage 0/1 classification & atomic-fact heads over the frozen `421M` ModernBERT encoder on clean non-overlapping synthetic pairs (`<=0` 8-gram overlap with all test sets) -> eliminates English regex vetoes while pushing micro-F1 `>=0.95`. See [`docs/v7-stage1-semantic-probes.md`](v7-stage1-semantic-probes.md).

2. **PROB-2 (Critical — Kannada `C13` `1/16`, `Sealed Kannada-8` `1/8`):**
   - `PIXMELT/laya` is English-only and English regexes veto Kannada inputs. Empirically proved `convaiinnovations/laya/multilingual` fails (`0/16–6/16`), whereas **sentence-split `NLLB-200-distilled-600M` (`fp16`, `kan_Knda -> eng_Latn`) + generic tail-drop + `PIXMELT/laya` achieved `14/16` (`87.5%`) exact, `16/16` court, `0` silent, `0.949` Micro-F1 on `C13` in `0.35s/Q` batched (`2.80 GB` co-resident VRAM)**.
   - **Pending Action:** Integrate `Router` + lazy sentence-split `NLLB` preprocessing (with unmodified NLLB text, no inline glosses, plus Kannada negative-demand check) into the `v7` classifier package. See [`docs/v7-multilingual-prose-latency-design.md`](v7-multilingual-prose-latency-design.md).

3. **PROB-3 (High — Stage 2 Runtime Still Uses v3 Logic Instead of Graph v4 Spec):**
   - [`graph/laya-crpc-bns-section-decision-tree-v4.json`](../graph/laya-crpc-bns-section-decision-tree-v4.json) is built, **but** the live `v6` notebook still implements old `stage2()` which:
     - Never emits `hma-13b` (`FN=5`), `hma-9` (`B-018`), `pwdva-22` (`B-019`), or `hma-27` joint property (`FN=8`)
     - Misroutes male self-maintenance / father child-only / aged parent / post-order arrears (`C8`, `C12`: `pwdva-20` `FP=25`, `bnss-144` `FP=14`)
     - Bundles `pwdva-17 + 18 + 19` together unconditionally (`pwdva-18` `FP=6` / `FN=19`)
     - Triggers `Fb=5` (`B-018, 118, 131, 150, 187` proposing `hma-24` before Stage 2 drops it) and `provisional` Family Court guesses (`F20`, `B-130`, `B-141`)
     - Misses `fact`, `procedure`, `court`, `safety` triggers in `SCORING_KINDS` (`esc-kinds strict 48/230`).
   - **Pending Action:** Implement `stage2_v4`, `court_for_v4`, Layer A zero-`Fb` pre-filtering, and 9-kind `escalate_v4` from [`docs/v4-decision-graph-architecture.md`](v4-decision-graph-architecture.md) inside a standalone `src/` pipeline (`P3.4`).

### B. Governance, Ground Truth & Verification Open Items (`P0.7`, `P1.3`, `P2.x`, `P3.x`)

| ID | Open Problem / Task | Status | Required Action |
|---|---|---|---|
| **`D-V4-1`** | **Custody vocabulary split:** `brutal-bank-v1-frozen` expects `[gwa-1890 \| hma-26]` only (`hmga-1956-s6`/`welfare-principle` absent -> `16` FPs), while `16-Q` and `Sealed-28` require the 3-label bundle | `OPEN (needs owner/rater decision)` | Ratify dual reporting (`CUSTODY_VOCAB_PROJECTION` on brutal v1 + bundled on 16-Q/Sealed) or unify `ground-truth-v3` & `brutal-bank-v2` to `statutory_primary` (`applied_principles` metadata). |
| **`D-V4-2`** | **`16-Q` Post-D1-A Court & `safety` Mismatch:** `v6` regression gets `13/16` court (`H3, H10, H15` still list `['Family Court', 'Magistrate']` after `hma-27` removal) and `11/16` `esc-kinds` (`safety` omitted on `K0, H4, H5, H6, H13`) | `OPEN (design ready)` | Update `ground-truth-v3` (`H3/H10/H15` court -> `['Magistrate']`; align `safety` + `H12` convention) under Gate §6.1 re-run. |
| **`D-V4-3`** | **`hma-25` Lump-Sum Settlement `Fb` Rule:** `B-022, B-119, B-154` have no divorce decree yet expect `hma-25`; current `FORBIDDEN_RULES` flags pre-decree `hma-25` | `OPEN` | Align `FORBIDDEN_RULES` in `v7` with adjudicated `"decree or lump_sum_settlement"` rule while keeping strict pre-decree `Fb=0` on ordinary subsistence. |
| **`P2.1 / P2.2 / D-V4-4`** | Native Kannada speaker check (`C13`), `G2` amendment sign-off (`16 -> 20`), sealed `F1/F2/KN1` court (`Family Court` vs `Magistrate`) and pre-D1-A `F8/F9/F10/F16/KN3` `hma-27` delta | `OPEN` | Complete native check & formal sign-offs (`docs/brutal-v6-build-report.md §8`); keep frozen sealed files untouched and report deltas transparently. |
| **`P2.4 / P2.5`** | Unverified legal case citations (*Sukhdev Singh v. Sukhbir Kaur* Feb 2025; *Balkrishna/Babulal/Krishna Kumar Gupta*; HMA 27 paras 3–13, 15–17, 19) | `OPEN` | Independent legal verification before citing in non-template docs (note: `src/laya_prose_v2.py` cites ZERO case names, preventing any `Fp` risk). |
| **`G12 / G14-T4`** | Blind legal rater check on live generated prose (`>=3` samples English + Kannada) + Google Colab T4 `fp16` timing run | `OPEN` | Wire `src/laya_prose_v2.py` into `v7` notebook Cell 9 (`Fp=0`), collect blind rater sign-off, and run verified T4 Colab session (`LAYA_CUDA_AMP=fp16`). |
| **`P3.2 / P3.4 / P0.7`** | Build full standalone `src/` `v7` classifier + `v7` notebook + run primary + identical **Confirmation Re-Run (`P0.7`)** | `NOT STARTED (next build milestone)` | Build after Stage 0/1 head training (`PROB-1`) + NLLB Stage 0 (`PROB-2`) + Stage 2 v4 (`PROB-3`), then run clean frozen confirmation re-run for `10/10`. |
