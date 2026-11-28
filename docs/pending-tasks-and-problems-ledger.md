# Complete Problems & Pending Tasks Ledger (Updated Post-v7 Standalone CUDA Confirmation + Full-Repo Audit)

**Updated:** 2026-11-28
**Baseline `v6` Snapshot:** `live-laya-colab-test-v6-brutal.ipynb` on RTX 5050 Laptop GPU (`79/230` brutal `1.9/10 FAIL`, `16/16` regression, `5/20` sealed fresh, `1/8` sealed Kannada).
**Latest Locked `v7` Snapshot:** Standalone `src/laya_v7.py` (`mode="laya"`: `PIXMELT/laya` 421M ModernBERT-large bf16 + sentence-split `NLLB-200-distilled-600M` + grounded `laya_v7_evidence.py` + Graph `v4` Stage 2 `laya_v7_graph.py` + `laya_prose_v2.py`) across two byte-equivalent CUDA Confirmation Runs:
- **`Brutal-230` (`custody statutory_primary`):** **`230/230` (`100%`, `415 TP / 0 FP / 0 FN`, `230/230` court, `0` silent, `FpProse=0`, `0.133s/Q`, `10.0/10` raw un-capped)**
- **`16-Q` (`v2` D1-A):** **`14/16` (`micro-F1 0.9808`, `0 FP`, `2 FN` `H6`/`H14` `D-V4-2`, `9.1/10` raw → `<= 9.0` capped per Gate §2)**
- **`Sealed Kannada-8` (blind aggregate):** **`4/8` (`micro-F1 0.8205`, `micro_p=1.0`, `0` silent, `6.3/10`, up from `1/8` in `v6`)**
- **`Sealed Fresh-20` (blind aggregate):** **`7/20` (`micro-F1 0.6972`, `micro_p=0.8837`, `micro_r=0.5758`, `2` silent, `4.8/10`)**
- **`Brutal-230` `esc_kinds_strict`:** **`191/230` (`83.0%`) — FAILS `docs/brutal-test-200-plan.md` §3.2 `>= 200/230` bar**
- **`Brutal-230` `Fb`:** **unmeasured** (`candidates_before_stage2` clones post-Stage-2 `kept_ids`)
- **Codex Maintenance `final_check`:** **`32/34`** (`2 FN`: `bnss-144`, `bnss-146`)

**Full-repo engineering audit completed** (`HEAD bc7f40f`, `@audit-tasks` #20, 2026-11-27): every discovered code bug, scorer gap, and architectural debt item is catalogued below. **`v7.1 / 10x` engineering blueprint:** [`10x_plane.md`](../10x_plane.md).

This ledger updates `README.md §9` (`P0–P4`) with **every completed item**, **verified `v7` results**, and the exact **remaining `v7.1` blockers** before general public deployment.

---

## 1. Completed items (`v6` Baseline + `v7` Standalone Build & Brutal-230 Confirmation)

| Item | Description | Current Verified State | Evidence / Artifact |
|---|---|---|---|
| **P0.1 – P0.6, P0.8, P3.1** | Live `v6-brutal` execution (`16-Q` + `230-Q` + `20` Fresh + `8` Kannada) & archival | **DONE (RTX 5050 GPU)** — `79/230` (`1.9/10 FAIL`), preserved as frozen `v6` baseline | [`results/live-laya-colab-results-v6-brutal-final.json`](../results/live-laya-colab-results-v6-brutal-final.json), [`results/live-laya-colab-results-v6-brutal.md`](../results/live-laya-colab-results-v6-brutal.md) |
| **P1.1 (Prose Renderer & `Fp` Check)** | Deterministic template-locked renderer covering all 18 sections, 9 escalation kinds, D1-A `hma-27` gating, C8 male/parent roles + automated `Fp` checker | **DONE & WIRED INTO `src/laya_v7.py`** (`246/246` + `15/15` mutants pass, `Fp=0`; `fp_prose=0` across all `274` live `v7` questions; `G12` human rater check still open) — **bugs at `L558` (`status: ok` missing) and `L625` (`proceeding_pending` vs `proceeding_pending_hma`) found by audit** | [`src/laya_prose_v2.py`](../src/laya_prose_v2.py), [`tests/test_prose_renderer_v2.py`](../tests/test_prose_renderer_v2.py) |
| **P1.4 / G14 (GPU Latency)** | Verify `<=15s/Q` mean / `<=30s` max on GPU | **VERIFIED ON RTX 5050 GPU** (`v7` brutal mean **`0.133s/Q`**, max **`0.137–0.138s/Q`**, Kannada **`0.315–0.322s/Q`**). CPU fails (`17.8s/Q` local `v6`, `61.93s/Q` Colab `v5`), though `v7 --mode evidence` CPU runs in `0.587s` total without neural weights. Colab T4 `fp16` timing remains unverified | [`results/live-laya-v7-results.md`](../results/live-laya-v7-results.md), [`docs/v7-multilingual-prose-latency-design.md`](v7-multilingual-prose-latency-design.md) |
| **P2.3 (Graph v4 Build & Integrity)** | Repair 3 dangling edges, `'hmga-6' -> 'hmga-1956-s6'`, canonical `related_sections`, and v4 Stage 2 nodes | **DONE** (`Graph v4`: `34` sections / `66` nodes / `99` edges, `0` dangling edges, `7/7` frozen SHAs intact) — **audit found `v4.json` is never loaded at runtime** (`laya_v7_graph.py` bypasses it; `layer_a_filter_options()` dead; `5/66` nodes unreachable from root; `3` choice nodes have `options==[]`) | [`src/build_graph_v4.py`](../src/build_graph_v4.py), [`graph/laya-crpc-bns-section-decision-tree-v4.json`](../graph/laya-crpc-bns-section-decision-tree-v4.json), [`tests/test_graph_v4.py`](../tests/test_graph_v4.py) |
| **P1.2, P1.3, P1.5, P1.6, P3.2, P3.4, P0.7 (`v7` Standalone & Brutal-230 Confirmation)** | Replace brittle `v6` regex vetoes with clause-aware `laya_v7_evidence.py`, integrate batched sentence-split `PIXMELT/laya` + `NLLB-200-distilled-600M` (`kan_Knda -> eng_Latn`), implement Stage 2 Graph `v4` (`laya_v7_graph.py`), score isolated `tests/v7_backtest.py`, and run two identical locked CUDA Confirmation Runs | **DONE FOR `Brutal-230` (`230/230`, `10.0/10` raw un-capped)** — `Run 1 == Run 2` (`42/42` unit tests pass, `0` silent, `0` `Fb` *unmeasured*, `0` `FpProse`). Also preserves Codex 4-split maintenance runtime (`dev 48/48`, `challenge 34/34`, `verification 46/46`, `final_check 32/34`) | [`src/laya_v7.py`](../src/laya_v7.py), [`src/laya_v7_evidence.py`](../src/laya_v7_evidence.py), [`src/laya_v7_extractor.py`](../src/laya_v7_extractor.py), [`src/laya_v7_graph.py`](../src/laya_v7_graph.py), [`tests/v7_backtest.py`](../tests/v7_backtest.py), [`results/live-laya-v7-results.md`](../results/live-laya-v7-results.md) |

---

## 2. Active Problems & Remaining `v7.1` Blockers

### A. Unseen Paraphrase Generalisation Gap (`Sealed Fresh-20`: `7/20`, `Sealed Kannada-8`: `4/8`)

1. **`SEALED-RECALL` (Critical before public chatbot launch):**
   - On frozen **`Brutal-230`**, `v7` hits **`230/230` (`100%`, `10.0/10` raw)** and `14/16` (`micro-F1 0.9808`, `0 FP`) on **`16-Q`**.
   - On completely unseen blind **`Sealed Fresh-20`** (`7/20`, `micro_p=0.8837`, `micro_r=0.5758`, `2` silent, `38 TP / 5 FP / 28 FN`) and **`Sealed Kannada-8`** (`4/8`, `micro_p=1.0`, `micro_r=0.6957`, `0` silent, `16 TP / 0 FP / 7 FN`), precision remains high (`0` `FpProse`), **but** unseen phrasing drops recall (most affected sections in blind aggregate: `hma-27`, `welfare-principle`, `pwdva-17/18/19`, `hma-13`, `hma-24`, `gwa-1890`, `hmga-1956-s6`).
   - **Sealed Fresh-20 category failures:** `divorce 0/2`, `residence 0/2`, `stridhan 0/3`, `custody 1/3`, `violence 1/2`, `maintenance 2/4`, `out-of-scope 1/2`.
   - **Sealed Kannada-8 category failures:** `divorce 0/2`, `residence 0/1`, `stridhan 0/1`.
   - Why `Qwen3-1.7B` was not made primary: diagnostic benchmarking showed `Qwen3-1.7B` hallucinated on direct Kannada (`B-207`, `B-214`) and `16-Q` out-of-scope cases (`H6`, `H13`); clean supervised/synthetic head calibration on `PIXMELT/laya` (without touching or leaking sealed sets) is still needed for `v7.1`.

### B. Discovered Code Bugs & Edge Cases (Audit `@audit-tasks` #20, Section A)

| ID | Bug / Edge Case | Location | Impact | `10x_plane.md` Fix |
|---|---|---|---|---|
| **`BUG-A1`** | **Unmeasured `Fb` & empty `dropped_ids`**: `candidates_before_stage2` clones *post*-Stage-2 `list(decision["kept_ids"])`; `prose_forbidden_check()` receives `[]` instead of `decision["gated_out"]` | `src/laya_v7.py:100,105,168,173` | `Fb` always `0` by construction — `docs/laya-10-10-gate-definition.md` §2 caps never apply | `V71-P1-1`, `V71-P2-2` |
| **`BUG-A2`** | **Broken `apply_confirmations_v7`**: only handles `k == "divorce_asked"`; non-divorce confirmations (e.g., `{"money_fact": True}`) do NOT clear `negated_issues` or update `issues[...]` | `src/laya_v7.py:33-49` | Multi-turn confirmations for maintenance (`bnss-144`/`pwdva-20`) silently dropped | `V71-P2-3` |
| **`BUG-A3`** | **8 dead fact keys** in Graph Stage 2 never emitted by Stage 0/1 | `src/laya_v7_graph.py` (`interim_asked` L453/L468, `money_fact_child_or_parallel` L457, `stay_in_house_under_eviction_pressure` L530, `stridhan_held_by_inlaws_refused` L241, `stridhan_safe_in_own_possession` L212/L296, `stridhan_abandoned_or_undisputed` L212, `urgent_safety_risk` L362, `hypothetical_or_joint_prop_fact_only` L280) | Routing branches silently unreachable; father `child_only`+`pending_hma` `hma-24` and `being_filed` `hma-24` always skipped | `V71-P1-1` |
| **`BUG-A4a`** | `L430`: divorced wife with adult child (`minor_child` denied) silently skips `bnss-144` (`['hma-25']` only) | `src/laya_v7_graph.py:430` | Missing maintenance route for adult-child divorcees | `V71-P1-1` |
| **`BUG-A4b`** | `L506`: `bns-316` omits `sex != "male"`, routing male spouse to `bns-316` with wife-specific Stridhan prose | `src/laya_v7_graph.py:506`, `src/laya_prose_v2.py:227` | Incorrect legal output for male Stridhan claimants | `V71-P1-1` |
| **`BUG-A4c`** | `L512`: safe Stridhan (`laya_v7_evidence.py:644-645`) blocks `hma-27` joint property (`kept_ids=[]`) | `src/laya_v7_graph.py:512` | `hma-27` joint property silently dropped when safe Stridhan present | `V71-P1-1` |
| **`BUG-A4d`** | `L271-274`: unconditionally emits `"recovery"` whenever `"bns-316" in kept` (contradicts `docs/v4-decision-graph-architecture.md:326`) | `src/laya_v7_graph.py:271-274` | `16-Q` `H3`/`H10` produce `['demand','recovery']` vs GT `['demand']` | `V71-P1-1` |
| **`BUG-A4e`** | `L400`+`L283`: `in_scope=False` calls `_derive_escalations_v7(set(), ...)` emitting `"procedure"` | `src/laya_v7_graph.py:400,283` | `16-Q` `H12` false escalation | `V71-P1-1` |
| **`BUG-A5a`** | `LAYA_NOUL_PROMPTS` only has 9 prompts; 0 neural probes for `hma-9`, `pwdva-22`, `hma-13b`, `decree`, `lump_sum_settlement`, `proceeding_pending_hma`, `being_filed`, `existing_order_enforcement`, `claimant_sex/role`, `demand_made`, `in_scope`, or `choice` gates | `src/laya_v7_extractor.py:34-44` | Recall ceiling on unseen paraphrases for all uncovered issues | `V71-P1-3` |
| **`BUG-A5b`** | `laya_available()` requires `torch.cuda.is_available()`, so `mode="auto"` silently degrades to regex-only `"evidence"` on CPU even with cached `PIXMELT/laya` | `src/laya_v7_extractor.py:76-86` | Silent CPU quality degradation | `V71-P1-1` |
| **`BUG-A5c`** | `_merge_laya_and_grounded()` uses ONLY `full_*` (ignoring sentence `cmax`); `L417` **blocks neural `custody_claim` boost whenever `residence_claim` is True** | `src/laya_v7_extractor.py:379-441` | Custody dropped on multi-issue custody+residence questions | `V71-P1-1`, `V71-P1-3` |
| **`BUG-A5d`** | `"structured"` Qwen3-1.7B mode reads ONLY `slots.get("cs") == "Y"`, discarding `17/18` constrained slots | `src/laya_v7_extractor.py:46-65,500-505` | 17 unused Qwen slot predictions | `V71-P1-3` |
| **`BUG-A5e`** | `_ELDER_PARENT_CLAIM_RE` misses `"70-year-old mother"` / `"an 70"` phrasing; `_CHILD_MENTION_RE` sets `child_fact=True` on adult offspring | `src/laya_v7_evidence.py:70-78,90,459,483,594` | Elder parent fallback to spouse `female`; false `bnss-144`/`pwdva-20` | `V71-P1-1` |
| **`BUG-A5f`** | `_EXPLICIT_RES_ONLY_RE` includes lockout/entry-refusal patterns, suppressing `pwdva-18` without beating | `src/laya_v7_evidence.py:284-287,551` | Missing `pwdva-18` on lock-change/entry-refusal | `V71-P1-1` |
| **`BUG-A5g`** | `no_dispute_empty` ignores `joint_prop_claim`, `restitution_asked`, `birth_cert`, disabling `_merge_laya_and_grounded` on safe-gold + joint-property queries | `src/laya_v7_evidence.py:577` | `hma-27` joint property dropped when safe-gold co-occurs | `V71-P1-1` |
| **`BUG-A5h`** | Overfit English heuristics: `_OOS_DOMAIN_RE`, `_CUSTODY_ASK_RE` (`kidz`,`wit`), `_JOINT_PROP_NEG_RE`, `kn_aunt_held`, `open_markers` memorize `Brutal-230` surface forms | `src/laya_v7_evidence.py:37-40,238,354,558,580-584` | `214/214` Brutal EN exact vs `7/20` Sealed-20 | `V71-P1-2`, `V71-P1-3` |
| **`BUG-A6a`** | `laya_prose_v2.py:558`: normal return dict missing `"status": "ok"` | `src/laya_prose_v2.py:558` | Inconsistent API contract | `V71-P6-1` |
| **`BUG-A6b`** | `prose_forbidden_check` checks legacy `proceeding_pending` instead of canonical `proceeding_pending_hma`, causing false `Fp item 3` when `hma-13` renders from `proceeding_pending_hma=True, divorce_asked=False` | `src/laya_prose_v2.py:625` | Potential false prose forbidden trigger | `V71-P6-1` |

### C. Scorer Bugs, Benchmark Failures & Architectural Gaps (Audit Section B)

| ID | Problem | Evidence | `10x_plane.md` Fix |
|---|---|---|---|
| **`SCORE-B1`** | **Scorer masks & omits penalties**: `tests/v7_backtest.py` drops `Fb` (` - 0.5*Fb` absent at `L185`), masks `16-Q` `H12` `'procedure'` via `legacy_16q_compat` (`L125-126`), omits `docs/laya-10-10-gate-definition.md` §2 caps (`<= 9.0` while `G12` & `16-Q`/`Sealed` fail), drops `v6` diagnostics (`hma27_gt_note_ids` on `F8/F9/F10/F16/KN3` and `F1/F2/KN1` court deltas) | `tests/v7_backtest.py:125-126,185,307-326` | `V71-P7-1` |
| **`SCORE-B2`** | **`Brutal-230` `esc_kinds_strict 191/230` (`83.0%`) FAILS `docs/brutal-test-200-plan.md` §3.2 `>= 200/230` bar**; `16-Q` `esc_kinds_strict 7/16`; `Sealed Fresh-20` `7/20`; `Sealed Kannada-8` `4/8`; Maintenance `final_check 32/34` (`bnss-144` & `bnss-146` FN) | `results/live-laya-v7-results.md` | `V71-P1-1`, `V71-P7-1` |
| **`ARCH-B3`** | **Dual un-unified runtimes**: `src/laya_family.py` (5 maintenance routes, `PRE_BNSS` S.O. 848(E), `guided_assessment`, `--interactive`/`--confirm`, rejects Kannada, no `laya_prose_v2`) vs `src/laya_v7.py` (18 sections, `NLLB`+`PIXMELT`, `laya_prose_v2`, lacks `bnss-144-3`/`146`, `PRE_BNSS`/CrPC-125 guard, multi-turn state & clarifying-question UX) | `src/laya_family.py` vs `src/laya_v7.py` | `V71-P2-1` |
| **`ARCH-B4`** | **Graph v4 JSON unused at runtime**: `evaluate_stage2_v7` & `laya_v7.py` never call `load_graph_v4()` or `layer_a_filter_options()`; `5/66` nodes unreachable from root; `3` `choice` nodes have `options==[]`; `welfare-principle` has `type=="score"`; 14 sections embed case citations in graph JSON metadata | `src/laya_v7_graph.py`, `graph/laya-crpc-bns-section-decision-tree-v4.json` | `V71-P2-2`, `V71-P4-2` |
| **`INFRA-B5`** | **Missing CI, Colab notebook, calibration, licensing & human gates**: Zero `.github/` CI or pre-push hooks; no `v7` Colab notebook (`README.md §1` links `v6-brutal.ipynb`); `G14-T4` Colab T4 unverified; CPU latency fails (`17.8–61.9s/Q`); `NLLB-200` `CC-BY-NC` noncommercial license & no Kannada prose templates; no confidence calibration/ECE/ROC abstention; `test_v7_rules.py` skips batch-invariance test on `mode="laya"`; `n=230` (`98.4%` Wilson lower bound) vs `~300+` for `>=99%` CI; no repo `LICENSE` (`README.md §12`); open `G12` blind human rater, `P2.1` native Kannada audit, `P2.2` unsigned `G2` amendment, `G15` Colab confirmation, and remaining unverified citations | Repo root `.github/`, `README.md §1,§12`, `docs/laya-10-10-gate-definition.md` | `V71-P3-1`, `V71-P5-3`, `V71-P6-3`, `V71-P7-4` |

### D. Documentation Inaccuracies Discovered by Audit (Section C)

| ID | Inaccuracy | Location | Correction |
|---|---|---|---|
| **`DOC-C1`** | **Stale `P2.4`**: marks *Sukhdev Singh v. Sukhbir Kaur* unverified, whereas `docs/legal-decisions-v4.md:402-509` already verified it (`2025 INSC 197`, `[2025] 2 SCR 1569`, 12 Feb 2025); omits remaining unverified citations (*Balkrishna*, *Babulal*, *Krishna Kumar Gupta*, *Astha Thakur* paras `3-13,15-17,19`) | Former `ledger:44`, `README.md:328,418` | `P2.4` updated below; *Sukhdev Singh* promoted to verified; remaining citations tracked under `V71-P4-2` |
| **`DOC-C2`** | **`10.0/10` headlines without flagging `esc_kinds_strict 191/230` failure** and scorer omissions (`Fb` unmeasured, Gate §2 caps not applied) | Former `ledger:6`, `README.md:9,306` | Headline updated to note `10.0/10 raw un-capped`; `esc_kinds_strict` failure now explicitly stated |
| **`DOC-C3`** | **`D-V4-2` conflation**: lumps `H6 pwdva-18` + `H14 hma-13` under `D-V4-2`, but `docs/v4-decision-graph-architecture.md:310,337,352,365` defined `D-V4-2` only for `H3/H10/H15` court, `safety`, and `H12` | Former `ledger:7,41` | `D-V4-2` items now explicitly separated per `V71-P4-4` |
| **`DOC-C4`** | **False Kannada prose claim**: `src/README.md:15` calls `laya_prose_v2.py` `"English/Kannada prose renderer"`, but it is English-only (0 Kannada templates) | `src/README.md:15` | Noted; fix deferred to `V71-P6-1` (create real Kannada templates first) |
| **`DOC-C5`** | **Stale Graph v4 status**: `README.md:130` states `"pending v7 runtime integration"` without noting `laya_v7_graph.py` bypasses the JSON | `README.md:130` | Outside §9/§11 scope (frozen §3); documented as known inaccuracy here |

### E. Governance, Ground Truth, Licensing & Verification Open Items (`D-V4-1..4`, `G12`, `P2.x`, `G14-T4`)

| ID | Open Problem / Task | Status | Required Action |
|---|---|---|---|
| **`D-V4-1`** | **Custody vocabulary split:** `brutal-bank-v1-frozen` expects `[gwa-1890 | hma-26]` (`statutory_primary`), while `16-Q` and `Sealed-28` require the 3-label bundle (`hmga-1956-s6` + `welfare-principle`) | `OPEN (reported transparently)` | `v7` supports `CUSTODY_VOCAB_PROJECTION` on `Brutal-230`; formal owner/rater ratification of `ground-truth-v3` (`statutory_primary` + `applied_principles`) remains open. `10x_plane.md` task `V71-P4-4`. |
| **`D-V4-2`** | **`16-Q` Post-D1-A Deltas (separated per audit `DOC-C3`):** (a) `H3/H10/H15` court expected `['Family Court', 'Magistrate']` after `hma-27` removal → should be `['Magistrate']`; (b) `safety` escalation kind omitted on 5 GT rows; (c) `H12` `procedure` OOS handoff; (d) `H6 pwdva-18` (decoupled `pwdva-17/19` vs legacy triple bundle — not strictly `D-V4-2`); (e) `H14 hma-13` (frozen governing-section call vs `v4` relief-sought-only rule, `docs/v6-lane3-legal-decisions.md §3.1` D6 — also not strictly `D-V4-2`) | `OPEN (design ready)` | Decide whether to issue a frozen `ground-truth-v3` under Gate §6.1 rather than leaving as known deltas. `10x_plane.md` task `V71-P4-4`. |
| **`D-V4-3`** | **`hma-25` Lump-Sum Settlement Rule:** `B-022, B-119, B-154` have no divorce decree yet expect `hma-25` | `SOLVED IN v7 STAGE 2 / GT NOTE OPEN` | Implemented `lump_sum_settlement` in `src/laya_v7_graph.py` (`0` `Fb` in `Brutal-230`); keep formally documented in adjudicated rule specs. |
| **`P2.1 / P2.2 / D-V4-4`** | Native Kannada speaker check (`C13` + `Sealed Kannada-8`), `G2` amendment sign-off (`16 -> 20`), and pre-D1-A sealed `F8/F9/F10/F16/KN3` / forum checks | `OPEN` | Complete native check & formal sign-offs while keeping frozen sealed files untouched. `10x_plane.md` tasks `V71-P6-3`, `V71-P4-4`. |
| **`P2.4`** | **Case-law verification** — *Sukhdev Singh v. Sukhbir Kaur* **VERIFIED** (`2025 INSC 197`, `[2025] 2 SCR 1569`, 12 Feb 2025, per `docs/legal-decisions-v4.md:402-509`); **remaining OPEN**: *Balkrishna Ramchandra Kadam v. Sangeeta* `(1997) 7 SCC 500`, *Babulal Yadav v. Sonu Yadav* `2023 SCC OnLine Chh 2815`, *Krishna Kumar Gupta v. Priti Gupta* Allahabad HC FA 1116/2024, *Pratibha Rani v. Suraj Kumar* `(1985) 2 SCC 370`, *Satish Chander Ahuja v. Sneha Ahuja*, *Rajnesh v. Neha* | `PARTIALLY CLOSED` | Promote *Sukhdev Singh* to verified; independently verify remaining citations from primary judgments before external documentation. `10x_plane.md` task `V71-P4-2`. |
| **`P2.5`** | Full HMA 27 judgment paras 3–13, 15–17, 19 check (*Astha Thakur v. Dhananjay Kanwar*, `2025:HHC:46178`) | `OPEN` | Independent legal verification. `10x_plane.md` task `V71-P4-2`. |
| **`G12 / G14-T4 / NLLB-LIC`** | Blind legal rater review on live `v7` prose (`>=3` EN + KN samples), Google Colab T4 `fp16` verification notebook, and noncommercial `NLLB-200` weight license vs Apache-2.0 EN-only/replacement decision | `OPEN` | Collect blind rater sign-off on `laya_prose_v2` outputs, verify Colab T4 latency/parity in a standalone `v7` notebook if Colab distribution is required, and confirm deployment licensing for `facebook/nllb-200-distilled-600M`. `10x_plane.md` tasks `V71-P6-3`, `V71-P5-3`, `V71-P3-1`. |

---

## 3. `v7.1 / 10x` Improvement Roadmap

Full engineering blueprint with concrete module specs, data contracts, and exit criteria: **[`10x_plane.md`](../10x_plane.md)** (authored `@architect-10x`, verified `@audit-tasks` #20).

### Pillar 1 — Close Unseen Paraphrase Recall & Eliminate Overfit Heuristics (`V71-P1-1..5`)

| Task ID | Deliverable | Status | Exit Bar |
|---|---|---|---|
| `V71-P1-1` | Fix all Section A code/rule bugs (`BUG-A1`..`A6b` above) in `src/laya_v7.py`, `src/laya_v7_graph.py`, `src/laya_v7_evidence.py`, `src/laya_v7_extractor.py`, `src/laya_prose_v2.py` | `OPEN` | `Brutal-230` `esc_kinds_strict >= 225/230`; `Fb` genuinely measured `= 0` |
| `V71-P1-2` | Clean 5,000-example bilingual synthetic + hard-negative corpus (`0` 8-gram overlap with all test banks) | `OPEN` | Leakage gate (`scripts/check_ngram_leakage.py`) passes; covers all `11` issues and `28` atomic facts |
| `V71-P1-3` | Supervised multi-head Stage 0/1 classifier (ModernBERT/DeBERTa) replacing 9-prompt + regex-anchor heuristics | `OPEN` | `>= 0.95` micro-F1 across all heads on 5-fold synthetic CV |
| `V71-P1-4` | Maintenance `final_check` `32/34 -> 34/34` generalisation (`bnss-144` & `bnss-146` FN) | `OPEN` | `34/34` exact (`0` FP, `0` FN) |
| `V71-P1-5` | Confidence-guided clarification fallback for uncertain extractions (eliminating `2` silent `Sealed Fresh-20` misses) | `OPEN` | `Sealed Fresh-20` `0` silent; `Sealed Kannada-8` `0` silent |

**Combined Pillar 1 Exit:** `Sealed Fresh-20` **`20/20`**, `Sealed Kannada-8` **`8/8`**, `Brutal-230` `esc_kinds_strict >= 225/230`, maintenance `final_check` **`34/34`**.

### Pillar 2 — Dual-Runtime Unification, Graph v4 Execution & Multi-Turn Provenance (`V71-P2-1..4`)

| Task ID | Deliverable | Status | Exit Bar |
|---|---|---|---|
| `V71-P2-1` | Merge `src/laya_v7*.py` + `src/laya_family*.py` into unified `src/laya_runtime.py` (`20` routes incl. `bnss-144-3`/`146` + `PRE_BNSS`) | `OPEN` | All `42/42` + `>= 25` new tests pass; backward-compatible API |
| `V71-P2-2` | True Graph v4.1 runtime execution & schema repair (single-root reachability, genuine `Fb` measurement, `layer_a_filter_options()` live) | `OPEN` | `100%` node reachability from root; `Fb` genuinely measured |
| `V71-P2-3` | Multi-turn provenance (`SessionState`), contradiction resolution & full override support (replacing broken `apply_confirmations_v7`) | `OPEN` | `MT1–MT4` **`12/12` turns / `4/4` final**, `0` dropped-fact errors |
| `V71-P2-4` | Targeted clarifying question engine (`src/laya_clarifier.py`) ranked by remedy-flip information gain | `OPEN` | `0` silent drops on in-scope queries |

### Pillar 3 — Multilingual & Licensing Resilience (`V71-P3-1..3`)

| Task ID | Deliverable | Status | Exit Bar |
|---|---|---|---|
| `V71-P3-1` | Retire `CC-BY-NC` `NLLB-200`; permissive Apache-2.0/MIT bilingual encoder + repo `LICENSE` + `THIRD_PARTY_NOTICES.md` | `OPEN` | Zero `CC-BY-NC` weights in default runtime; `LICENSE` file merged |
| `V71-P3-2` | Kannada morphology, colloquialisms & code-mixed Kanglish normaliser (`src/laya_lang_normalizer.py`) | `OPEN` | Kanglish held-out suite `>= 95%` exact, `0` FP |
| `V71-P3-3` | Multi-language `LanguagePack` scaling contract | `OPEN` | Zero Graph v4 logic edits needed to onboard new language |

### Pillar 4 — Legal Rigor, Citation Verification & Safety (`V71-P4-1..4`)

| Task ID | Deliverable | Status | Exit Bar |
|---|---|---|---|
| `V71-P4-1` | `BNS/BNSS/BSA` + `CrPC-125`/`IPC-406`/`IEA-65B` statutory cross-walk with temporal commencement routing | `OPEN` | `100%` pass on `C17` pre-BNSS cross-walk tests |
| `V71-P4-2` | Verified `legal/verified_authorities.json` — close remaining unverified citations (`P2.4` remaining + `P2.5`); scrub 16 graph entries embedding case citations | `OPEN` | `100%` primary-verified citations; `0` unverified case strings in `graph/*.json` |
| `V71-P4-3` | Urgent DV/child safety routing decoupled from procedure (wire `urgent_safety_risk` + `child_safety_risk`) | `OPEN` | `100%` safety recall on `C18` urgent scenarios; `0` false safety on benign residence-only |
| `V71-P4-4` | `D-V4-1..4` governance ratification & `ground-truth-v3` (separating conflated `D-V4-2` items per audit `DOC-C3`) | `OPEN` | Signed adjudication record filed |

### Pillar 5 — 10x Speed, Distillation & Edge Deployment (`V71-P5-1..4`)

| Task ID | Deliverable | Status | Exit Bar |
|---|---|---|---|
| `V71-P5-1` | Single-pass multi-head student distillation (`<= 120-150M` params) | `OPEN` | `0` accuracy drop vs teacher on all suites |
| `V71-P5-2` | ONNX export + INT8 quantization (`models/student_int8.onnx`) | `OPEN` | CPU `< 0.5s/Q` mean, `<= 1.0s/Q` max; GPU `< 50ms/Q` mean |
| `V71-P5-3` | Colab T4 `fp16` parity notebook (`notebooks/live-laya-colab-test-v7.ipynb`) closing `G14-T4` | `OPEN` | `0` prediction flips vs RTX 5050 |
| `V71-P5-4` | Tiered edge serving (`mode="auto"`: student_onnx_gpu → student_onnx_cpu → laya_teacher → evidence) | `OPEN` | Graceful fallback with logged mode selection |

### Pillar 6 — Consumer Prose, Kannada Localisation & Human Verification (`V71-P6-1..3`)

| Task ID | Deliverable | Status | Exit Bar |
|---|---|---|---|
| `V71-P6-1` | Deterministic Kannada prose templates (`src/laya_prose_kn.py`) covering 20 sections + fix `BUG-A6a/A6b` + correct `src/README.md:15` | `OPEN` | `Fp=0` EN+KN; `>= 30` KN adversarial mutants caught |
| `V71-P6-2` | Layman readability, forum nuance & non-coercive document checklists | `OPEN` | Average sentence length `<= 22` words; deterministic `Fp=0` checked |
| `V71-P6-3` | `G12` blind human legal rater + `P2.1` native Kannada sign-off workflows (`scripts/export_human_audit.py`) | `OPEN` | Signed `Fp=0` reports from `>= 2` raters (lifting `<= 9.0` prose cap) |

### Pillar 7 — Evaluation Moat, Statistical Power & Automated CI (`V71-P7-1..4`)

| Task ID | Deliverable | Status | Exit Bar |
|---|---|---|---|
| `V71-P7-1` | Fix `tests/v7_backtest.py` scorer: genuine `Fb`, Gate §2 caps, stop `H12` masking, restore sealed diagnostics, flag `esc_kinds_strict < 200` as FAIL | `OPEN` | Scorer prints both `raw` and `capped` ratings; `191/230 FAIL` flagged |
| `V71-P7-2` | Scale to `brutal-bank-v2` (`n >= 450-500`) with `C15`–`C19` stratified categories | `OPEN` | Wilson 95% CI lower bound `>= 99.0%` on new bank |
| `V71-P7-3` | Confidence calibration (`ECE <= 0.03`), selective abstention & ROC bounds | `OPEN` | `ECE <= 0.03`; `AURC <= 0.02`; `>= 99%` precision on auto-accepted |
| `V71-P7-4` | `.github/workflows/laya-ci.yml` + pre-push hook: frozen SHA, 8-gram leakage, batch invariance, `Fp=0`, license allowlist, CPU latency gates | `OPEN` | CI green on every push/PR |

### Phased Execution Sequence (`10x_plane.md` §8.1)

| Phase | Scope | Gate |
|---|---|---|
| **Phase 0** | `V71-P1-1`, `V71-P7-1`, `V71-P6-1` partial (prose fixes), `V71-P4-4` | `esc_kinds_strict >= 225/230`, `Fb` genuinely `= 0`, expanded unit tests pass |
| **Phase 1** | `V71-P1-2..5`, `V71-P2-1..4` | `Sealed Fresh-20` **`20/20`**, maintenance `34/34`, `MT1–MT4` `12/12` turns |
| **Phase 2** | `V71-P3-1..3`, `V71-P4-1..3`, `V71-P6-1..2` | Zero `CC-BY-NC`; `Sealed Kannada-8` **`8/8`**; Kanglish `>= 95%`; `P2.4`/`P2.5` closed |
| **Phase 3** | `V71-P5-1..4` | CPU `< 0.5s/Q`; GPU `< 50ms/Q`; `G14-T4` parity |
| **Phase 4** | `V71-P7-2..4`, `V71-P6-3`, `G15` | Wilson `>= 99.0%` CI floor; `ECE <= 0.03`; `G12` & `P2.1` signed; CI green |
