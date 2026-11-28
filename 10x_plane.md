# LAYA v7.1 / 10x Engineering & Legal Improvement Plan (`10x_plane.md`)

**Date:** 2026-11-27  
**Baseline Commit:** `bc7f40f` (clean tree; `7/7` frozen SHA-256 hashes verified intact)  
**Scope & Integrity:** Architectural blueprint only (`10x_plane.md`). Zero code, test, graph, ledger, README, or frozen files edited by this document; zero sealed test-bank text (`test-bank/sealed/*.json`) opened or cited beyond aggregate statistics logged in [`results/live-laya-v7-results.md`](results/live-laya-v7-results.md). Paths tagged **`[NEW]`** below designate proposed `v7.1` target files/modules not yet created in the `HEAD bc7f40f` repository.

---

## 0. Executive Diagnosis & Honest Verified Baseline (`HEAD bc7f40f`)

LAYA v7 moved the standalone pipeline ([`src/laya_v7.py`](src/laya_v7.py)) from the `v6-brutal` Colab baseline (`79/230` exact on `Brutal-230`, `1.9/10 FAIL`) to `230/230` exact on `Brutal-230` (`mode="laya"`, RTX 5050 CUDA, identical across Confirmation Runs 1 & 2). However, a full-repo engineering audit and blind aggregate evaluation expose **three structural ceilings** that prevent general public chatbot deployment:

1. **Unseen Paraphrase Recall Collapse:** `Sealed Fresh-20` achieves **`7/20`** exact (`micro_r = 0.5758`, `28` FN, `2` silent) and `Sealed Kannada-8` achieves **`4/8`** (`micro_r = 0.6957`, `7` FN) because `src/laya_v7_extractor.py` relies on only `9` zero-shot `LAYA_NOUL_PROMPTS` gated behind brittle English regex anchors in `src/laya_v7_evidence.py`, while Codex maintenance `final_check` remains at **`32/34`** (`2` FN on `bnss-144` and `bnss-146`).
2. **Unmeasured/Failing Metrics, Code Bugs & Dual Un-unified Runtimes:** `Brutal-230` strict typed escalations scored **`191/230` (`83.0%`)**, which **fails** the `>= 200/230` bar in [`docs/brutal-test-200-plan.md`](docs/brutal-test-200-plan.md#L187-L194). `src/laya_v7.py` clones post-Stage-2 `kept_ids` into `candidates_before_stage2` and passes `[]` instead of `gated_out` to `prose_forbidden_check()`, leaving `Fb` unmeasured. `src/laya_v7_graph.py` never loads [`graph/laya-crpc-bns-section-decision-tree-v4.json`](graph/laya-crpc-bns-section-decision-tree-v4.json) or calls `layer_a_filter_options()`, and contains **8 dead fact keys** never emitted by Stage 0/1. Meanwhile, [`src/laya_family.py`](src/laya_family.py) and [`src/laya_v7.py`](src/laya_v7.py) split maintenance (`bnss-144-3`, `bnss-146`, `PRE_BNSS` S.O. 848(E), `guided_assessment`) from the 18-section Graph v4 pipeline.
3. **Licensing, CPU Latency, Kannada Prose & Automated CI Debt:** `facebook/nllb-200-distilled-600M` carries a **`CC-BY-NC-4.0` noncommercial** license; neural CPU execution fails `G14` (`17.817s/Q` mean / `33.090s` max local 4Q `v6`, `61.93s/Q` Colab `v5`); `src/laya_prose_v2.py` has **zero Kannada templates** (correcting `src/README.md:15`); `.github/` CI does not exist; and human/legal gates (`G12`, `P2.1`, `P2.2`, `P2.4`/`P2.5` remaining authorities, `G14-T4`) remain open.

### Verified Baseline Metrics (`HEAD bc7f40f`, Observed Directly)

| Benchmark / Check | Exact / Pass | Precision / Recall / Micro-F1 | Court / Esc-Bool / Esc-Kinds (Strict / FE) | Silent / Fb / FpProse / Err | Latency & Caps |
|---|---:|---|---:|---:|---|
| **`Brutal-230`** (`custody statutory_primary`, CUDA Runs 1–2) | **`230/230`** (CI `[0.9836, 1.0]`) | `1.0` / `1.0` / `1.0` (`415 / 0 / 0`) | `230/230` / `230/230` / **`191/230` (`FAIL <200`)** / `216/230` | `0` / *unmeasured* / `0` / `0` | `0.133s/Q` mean (`0.138s` max), `30.517–30.620s` wall; `10.0` un-capped (raw scorer) |
| **`16-Q`** (`v2` D1-A GT, CUDA Runs 1–2) | **`14/16`** (CI `[0.6398, 0.965]`) | `1.0` / `0.9623` / `0.9808` (`51 / 0 / 2`) | `13/16` / `16/16` / `7/16` / `8/16` | `0` / *unmeasured* / `0` / `0` | `0.816–0.840s/Q`, `9.1` raw (`<= 9.0` capped per Gate §2) |
| **`Sealed Fresh-20`** (blind aggregate, CUDA) | **`7/20`** (CI `[0.1812, 0.5671]`) | `0.8837` / `0.5758` / `0.6972` (`38 / 5 / 28`) | `7/20` / `18/20` / `3/20` / `3/20` | **`2`** / *unmeasured* / `0` / `0` | `0.124–0.125s/Q`, `4.8` formula |
| **`Sealed Kannada-8`** (blind aggregate, CUDA) | **`4/8`** (CI `[0.2152, 0.7848]`) | `1.0` / `0.6957` / `0.8205` (`16 / 0 / 7`) | `5/8` / `7/8` / `1/8` / `1/8` | `0` / *unmeasured* / `0` / `0` | `0.315–0.322s/Q`, `6.3` formula |
| **`Brutal-230` CPU Baseline** (`--mode evidence`) | `215/230` (`214/214 EN`, `C13=1/16`) | `1.0` / `0.9325` / `0.9651` (`387 / 0 / 28`) | `215/230` / `230/230` / `184/230` / `205/230` | `15` / — / `0` / `0` | `0.587s` wall (`mode="evidence"`; neural CPU fails `17.8–61.9s/Q`) |
| **Codex Maintenance 4-Split** (CUDA) | Dev `48/48`, Chal `34/34`, Ver `46/46`, Final **`32/34`** | Final: `21 TP / 0 FP / 2 FN` (`bnss-144`, `bnss-146`) | Clarifications: Dev `4/4`, Ver `5/5`, Final `3/3` | `0` runtime err | Warm median `0.3871–0.4392s`, max `0.6681s` |
| **Offline Verification Suite** (CPU, verified locally) | `42/42` unittest (`0.158s`), Graph `v4` (`34/66/99`, `7/7` SHAs), Prose `v2` (`246/246`, `15/15` mutants) | `Fp=0`, `quality_flags=0` | — | `0` failures, `0` skips | Prose mean `0.0351ms`, max `0.12ms`; `.github/` absent |

---

## 1. Pillar 1 — Close Unseen Paraphrase Recall & Eliminate Overfit Heuristics (`V71-P1-*`)

**Objective:** Lift unseen generalization from `Sealed Fresh-20` **`7/20` (`micro_r = 0.5758`, `2` silent)** to **`20/20` (`micro_F1 >= 0.98 -> 1.0`, `0` silent)**, `Sealed Kannada-8` **`4/8` -> `8/8`**, and maintenance `final_check` **`32/34` -> `34/34`** by replacing brittle regex-anchored heuristics with a calibrated multi-head Stage 0/1 encoder trained on clean zero-leakage synthetic + hard-negative data, while fixing all discovered Stage 0/1/2 code bugs.

### 1.1 Exact Root-Cause Attribution of Recall Hotspots & Code Defects

1. **Top Blind Aggregate FN & FP Hotspots (`results/live-laya-v7-results.md`):**
   - `Sealed Fresh-20` FN (`28` total): `hma-27` (`4`), `welfare-principle` (`3`), `pwdva-17` (`3`), `pwdva-18` (`3`), `pwdva-19` (`3`), `hma-13` (`2`), `hma-24` (`2`), `gwa-1890` (`2`), `hmga-1956-s6` (`2`), `hma-25` (`1`), `bns-316` (`1`), `hma-26` (`1`); FP (`5` total): `pwdva-20` (`2`), `hma-13` (`2`), `bnss-144` (`1`); Category exact: `divorce 0/2`, `residence 0/2`, `stridhan 0/3`, `custody 1/3`, `violence 1/2`, `maintenance 2/4`, `out-of-scope 1/2`.
   - `Sealed Kannada-8` FN (`7` total): `pwdva-18` (`2`), `hma-27` (`1`), `bnss-144` (`1`), `pwdva-20` (`1`), `pwdva-17` (`1`), `pwdva-19` (`1`); Category exact: `divorce 0/2`, `residence 0/1`, `stridhan 0/1`.
2. **Verified Structural & Code Causes (`src/laya_v7_extractor.py`, `src/laya_v7_evidence.py`, `src/laya_v7_graph.py`):**
   - **Under-covered neural probe set (`laya_v7_extractor.py:34-44`):** `LAYA_NOUL_PROMPTS` only scores `9` prompts (`maint_a/p`, `cust_p`, `strid_p`, `res_a`, `vio_a`, `div_p`, `jp_p`, `bc_p`). There are **zero** neural probes for `hma-9` (`restitution_asked`), `pwdva-22` (`dv_injury_comp_asked`), `hma-13b` (`mutual_consent`), `decree`, `lump_sum_settlement`, `proceeding_pending_hma`, `being_filed`, `existing_order_enforcement`, `claimant_sex`/`claimant_role`, `demand_made`, `judicial_separation_only`, `in_scope`, or Graph v4 `choice` nodes.
   - **Full-text-only pooling + regex anchor gates (`laya_v7_extractor.py:379-441`):** `_merge_laya_and_grounded()` reads ONLY `full_*` (ignoring sentence `cmax`) for `strid_p`, `res_full`, `div_full`, `jp_full`, and `bc_full`; gates `strid_p`, `res_full`, and `div_full` behind English regex anchors (`has_strid_anchor`, `has_res_anchor`, `has_div_anchor`); and at `L417` (`not proved_true(facts, "residence_claim")`) **blocks neural `custody_claim` boost whenever `residence_claim` is True** — dropping custody on multi-issue custody+residence questions.
   - **Silent CPU degradation (`laya_v7_extractor.py:76-86`):** `laya_available()` returns `False` whenever `not torch.cuda.is_available()`, causing `mode="auto"` to silently fall back to regex-only `"evidence"` on CPU even with `PIXMELT/laya` cached locally.
   - **Unused Qwen structured slots (`laya_v7_extractor.py:46-65, 500-505`):** `"structured"` mode decodes 18 constrained slots (`sc, sx, rl, mn, ls, eo, dv, mc, ph, bf, dc, cs, rs, vo, st, jp, bc, of`) yet reads ONLY `slots.get("cs") == "Y"`, discarding `17/18` slots.
   - **8 Dead Fact Keys in `src/laya_v7_graph.py` (never produced by `laya_v7_evidence.py` or `laya_v7_extractor.py`):** `interim_asked` (`L453, L468` — blocks father `child_only + pending_hma` `hma-24` and `being_filed` `hma-24`), `money_fact_child_or_parallel` (`L457`), `stay_in_house_under_eviction_pressure` (`L530`), `stridhan_held_by_inlaws_refused` (`L241`), `stridhan_safe_in_own_possession` (`L212, L296`), `stridhan_abandoned_or_undisputed` (`L212`), `urgent_safety_risk` (`L362`), and `hypothetical_or_joint_prop_fact_only` (`L280`).
   - **Overfit English regexes & bugs in `src/laya_v7_evidence.py`:**
     - `_ELDER_PARENT_CLAIM_RE` (`L70-78`) misses `"70-year-old mother"` / `"an 70"` phrasing, causing fallback to spouse `female` (`bnss-144` + false `pwdva-20`), while `_CHILD_MENTION_RE` (`L90, L594`) sets `child_fact=True` on adult offspring.
     - `_EXPLICIT_RES_ONLY_RE` (`L284-287, L551`) includes `refus(?:e|ing)\s+(?:me\s+)?entry` and `residence\s+order`, suppressing `pwdva-18` on entry-refusal/lockout without physical assault.
     - `no_dispute_empty` (`L577`) omits `joint_prop_claim`, `restitution_asked`, and `birth_cert`, disabling `_merge_laya_and_grounded` (`extractor.py:357`) whenever safe gold co-occurs with joint property or birth certificate.
     - Bank-tuned patterns (`_OOS_DOMAIN_RE`, `_CUSTODY_ASK_RE` `kidz`/`wit`, `_JOINT_PROP_NEG_RE`, `kn_aunt_held` `L558`, `open_markers` `L580-584`) memorize `Brutal-230` surface forms instead of generalizing.
   - **Graph Stage 2 bugs (`src/laya_v7_graph.py`):**
     - `L430`: divorced wife with an adult child (`minor_child` denied -> `minor_child_verified=False`) skips `bnss-144` after `hma-25` (`['hma-25']` only).
     - `L506`: `bns-316` omits `sex != "male"`, routing a husband claiming wedding gold to `bns-316` with wife-specific Stridhan prose (`src/laya_prose_v2.py:227`).
     - `L512`: `("stridhan" not in negated)` lets safe Stridhan (`laya_v7_evidence.py:644-645`) block `hma-27` joint property (`kept_ids=[]`).
     - `L271-274`: emits `"recovery"` unconditionally whenever `"bns-316" in kept` (violating `docs/v4-decision-graph-architecture.md:326` and causing `16-Q` `H3`/`H10` `['demand', 'recovery']` vs GT `['demand']`).
     - `L400 + L283`: `in_scope=False` emits `"procedure"` via `_derive_escalations_v7(set(), ...)` (causing `16-Q` `H12` mismatch).

### 1.2 Concrete Solution: Supervised Multi-Head Stage 0/1 Pipeline + Bug Remediation

| Task ID | Deliverable & Target Module (`[NEW]` = proposed) | Concrete Design & Contracts |
|---|---|---|
| **`V71-P1-1`** | **Fix all Section A Code & Rule Bugs** (`src/laya_v7.py`, `src/laya_v7_graph.py`, `src/laya_v7_evidence.py`, `src/laya_v7_extractor.py`, `src/laya_prose_v2.py`) | 1. Fix `src/laya_v7.py:100,105,168,173`: pass genuine `candidates_before_gate` and `decision["gated_out"]` to `prose_forbidden_check()`.<br>2. Fix `laya_v7_graph.py`: wire all 8 dead keys (`interim_asked`, `money_fact_child_or_parallel`, `stay_in_house_under_eviction_pressure`, `stridhan_held_by_inlaws_refused`, `stridhan_safe_in_own_possession`, `stridhan_abandoned_or_undisputed`, `urgent_safety_risk`, `hypothetical_or_joint_prop_fact_only`); fix `L430` adult-child divorcee `bnss-144`, `L506` `bns-316` `sex != "male"`, `L512` decoupled `joint_property` negation, `L271-274` `recovery` gated on `demand_made is True or stridhan_sold or stridhan_refused`, and `L400` `in_scope=False` explicit OOS escalation vs `no_dispute_empty` policy.<br>3. Fix `laya_v7_extractor.py`: allow `laya_available()` on CPU when cached; remove `L417` `not proved_true(facts, "residence_claim")` block on custody; allow `cmax` pooling across `strid_p/res/div/jp/bc` with calibrated conflict resolution.<br>4. Fix `laya_v7_evidence.py`: repair `_ELDER_PARENT_CLAIM_RE` (`\d{2}-year-old`), adult-son `child_fact`, `_EXPLICIT_RES_ONLY_RE` lockout-vs-explicit split, and `no_dispute_empty` checking `joint_prop_claim`/`restitution_asked`/`birth_cert`.<br>5. Fix `laya_prose_v2.py:558,625`: emit `"status": "ok"` on normal return and check `proceeding_pending_hma` in `prose_forbidden_check()`. |
| **`V71-P1-2`** | **Clean Synthetic + Hard-Negative Corpus Builder** (`[NEW] scripts/build_synthetic_corpus.py`, `[NEW] data/synthetic_v7_1/*.jsonl`) | Build a **5,000-example** bilingual training/validation corpus generated purely from statutory grammars, paraphrase templates, and hard-negative perturbations (never from test banks):<br>- Covers all `11` issues (`4`-class intent) and all `28` atomic facts (`4`-state + role/sex/modality).<br>- Explicit **Hard-Negative Clusters**: (a) custody vs residence home co-location; (b) `pwdva-17/19` explicit-only vs `pwdva-18` coercive lockout vs physical violence; (c) `divorce_asked` vs `proceeding_pending_hma` vs `being_filed` vs `judicial_separation_only` vs `hma-9` restitution; (d) `stridhan_claim` vs `stridhan_safe` vs `joint_property_claim` (`hma-27` vs `bns-316`); (e) `male_self_maintenance` vs `father_child_only` vs `elder_parent` vs `bnss-144-3` arrears vs `bnss-146` variation; (f) hypotheticals, third-party narratives, quoted text, pre-BNSS CrPC-125 orders, and 12 OOS domains.<br>- **Mandatory Leakage Gate (`[NEW] scripts/check_ngram_leakage.py`):** mechanical check enforcing **`0` word 8-grams** and **`< 0.90` normalized cosine overlap** against `16-Q`, `Brutal-230`, `tests/fixtures/laya_maintenance_*.json`, and `test-bank/sealed/*.json` (via blind Bloom/hash index so sealed wording is never printed). |
| **`V71-P1-3`** | **Supervised Multi-Head Stage 0/1 Classifier** (`[NEW] src/laya_v7_classifier.py`) | Train a unified multi-head teacher over frozen/LoRA-tuned `answerdotai/ModernBERT-large` (Apache-2.0) or `microsoft/deberta-v3-large` (MIT) / `PIXMELT/laya` predicting **all 11 issues + 28 atomic facts** simultaneously:<br>- **Inputs:** `[CLS] <full_question> [SEP]` + batched `[CLS] <clause_i> [SEP]` (no regex anchor vetoes required for recall).<br>- **Heads:** `issue_head` (`[11, 4]` softmax over `requested, incidental, denied, uncertain`), `fact_head` (`[28, 4]` over `supported, denied, unknown, conflicting`), `enum_heads` (`claimant_sex: [F,M,U]`, `claimant_role: [spouse,parent,child,other]`, `modality_time: [present,past,future,hypothetical,quoted]`), and `span_attn_pool` (producing token-level evidence spans aligned with clause max-pooling).<br>- **Clause-vs-Full Fusion:** `requested` uses calibrated `max(full_p, cmax_p)` gated by sentence-local `denied`/`hypothetical`/`third_party` head logits (`>= tau_neg` vetoes only the negated/hypothetical clause, not sibling clauses!). |
| **`V71-P1-4`** | **Maintenance `final_check` `32/34 -> 34/34` Generalization** (`src/laya_family_evidence.py`, unified Stage 0/1) | Eliminate the `2` residual FN misses (`bnss-144` & `bnss-146`) by wiring supervised `new_support`, `vary`, `recover`, `interim`, `permanent`, and beneficiary heads into the unified extractor with evidence-span verification (replacing brittle regex conjunction gaps in `CHANGE_REQUEST`, `DIRECT_SUPPORT_ASK`, and `grounded_beneficiaries`). |
| **`V71-P1-5`** | **Confidence-Guided Clarification Fallback for Uncertain Extractions** | When any high-impact fact/issue lands in `[tau_low, tau_high)` or `in_scope` is uncertain while `kept_ids == []`, emit structured `ClarificationPrompt`s instead of silent `[]` predictions (eliminating the `2` silent misses in `Sealed Fresh-20`). |

### 1.3 Pillar 1 Exit Criteria
- `Sealed Fresh-20`: `7/20 -> 20/20` exact (`micro_r >= 0.98 -> 1.0`, `0` silent, `0` FP), logged blind.
- `Sealed Kannada-8`: `4/8 -> 8/8` exact (`micro_F1 >= 0.98 -> 1.0`, `0` silent), logged blind.
- `Brutal-230`: `230/230` exact with `esc_kinds_strict >= 225/230` (clearing `>= 200/230` §3.2 bar).
- Maintenance `final_check`: `32/34 -> 34/34` exact (`0` FP, `0` FN).
- Synthetic held-out & 5-fold CV Stage 0/1 head macro/micro-F1 `>= 0.95` across all 11 issues & 28 facts; `0` 8-gram overlap verified across all test banks.

---

## 2. Pillar 2 — Dual-Runtime Unification, Graph v4 Execution & Multi-Turn Provenance (`V71-P2-*`)

**Objective:** Merge the split maintenance runtime (`src/laya_family*.py`) and the full family-law runtime (`src/laya_v7*.py`) into **one unified Graph v4/v4.1 engine** with true multi-turn provenance, deterministic conflict resolution, user overrides, and targeted clarifying questions.

### 2.1 Current Architectural Fragmentation (Audit B3 + B4 + A2)

| Dimension | `src/laya_family.py` + `laya_family_evidence.py` | `src/laya_v7.py` + `laya_v7_graph.py` | Unified `v7.1` Target |
|---|---|---|---|
| **Statutory Scope** | 5 routes: `bnss-144`, `bnss-144-3`, `bnss-146`, `hma-24`, `hma-25` | 18 sections (`bnss-144` collapses `144(3)` & `146`) | **20 routes** via `vocab_profile="v4_full" \| "v4_legacy_18" \| "brutal_primary"` |
| **Temporal / Pre-BNSS Guard** | `PRE_BNSS` (S.O. 848(E) 1 Jul 2024) + `OLD_ORDER` (CrPC 125) | Absent (conflates CrPC 125 / pre-2024 with `bnss-144`) | Unified Stage 0/1 temporal & statute provenance guard |
| **Multi-Turn & Overrides** | `guided_assessment` loop + `QUESTIONS` + `parse_confirmations` | Broken `apply_confirmations_v7` (`divorce_asked` only); stateless | Full `SessionState` with `FactProvenance` lattice & targeted questions |
| **Graph JSON Usage** | Hardcoded procedural checks (`_route`) | `evaluate_stage2_v7` never loads `graph_v4.json` or `layer_a_filter_options()` | Declarative Graph v4.1 interpreter + Layer A pre-filter + audited `Fb` |
| **Language & Prose** | Rejects non-Latin scripts (`L129-132`); unconditional `Rajnesh` `practice_authorities` | Bilingual + `laya_prose_v2` (EN only) | Unified EN + KN + Kanglish with `laya_prose_v2` (EN + KN, `Fp=0`) |

### 2.2 Proposed Unified Data Contracts & Runtime Modules (`[NEW] src/laya_schema_v71.py`, `[NEW] src/laya_graph_engine.py`, `[NEW] src/laya_runtime.py`)

```python
ProvenanceSource = Literal[
    "user_confirmation",           # Precedence 1: explicit answer to clarification or --confirm
    "user_text_verified_span",     # Precedence 2: literal current/recent user span (non-hypothetical)
    "translated_verified_span",    # Precedence 3: span grounded after permissive translation
    "model_calibrated_high",       # Precedence 4: P >= tau_high(key)
    "model_uncertain",             # Precedence 5: tau_low <= P < tau_high -> asks clarification
    "default",                     # Precedence 6: unresolved / unknown
]

@dataclass
class TurnRecord:
    turn_id: int
    raw_text: str
    lang: str
    script: str
    extracted_facts: dict[str, FactEvidence]
    extracted_issues: dict[str, IssueEvidence]
    confirmations: dict[str, Any]

@dataclass
class SessionState:
    session_id: str
    turns: list[TurnRecord]
    fact_history: dict[str, list[FactEvidence]]     # full audit trail across turns
    active_facts: dict[str, FactEvidence]           # winner per fact after provenance & recency
    active_issues: dict[str, IssueEvidence]         # winner per issue (supports multi-turn accretion)
    override_log: list[dict[str, Any]]              # tracks e.g. turn-2 divorce -> turn-3 mutual_consent
    pending_clarifications: list[dict[str, str]]    # ranked clarifying questions
```

### 2.3 Concrete Deliverables (`V71-P2-1`..`V71-P2-4`)

1. **`V71-P2-1` — Single Unified Runtime Entrypoint (`src/laya_runtime.py`) + Adapter Preservation:**
   - Implement `assess_turn(state: SessionState | None, question: str, *, confirmations: dict[str, Any] | None = None, vocab_profile: str = "v4_legacy_18", ...) -> tuple[dict[str, Any], SessionState]`.
   - Refactor `src/laya_v7.py` (`assess_v7`, `assess_v7_batch`) and `src/laya_family.py` (`assess`, `guided_assessment`, CLI `--interactive` / `--confirm`) into thin wrappers delegating to `laya_runtime.py` while keeping 100% backward-compatible test/API signatures (`tests/test_laya_family.py` `32/32`, `tests/test_v7_rules.py` `10/10`, `tests/laya_maintenance_backtest.py` all pass without changing test contracts).
   - Add explicit **Vocabulary Profiles**:
     - `v4_legacy_18`: maps `bnss-144-3` / `bnss-146` -> `bnss-144` for `16-Q` / `Sealed` / `v7` backward comparability (`v3_bundled` custody).
     - `brutal_primary`: statutory primary custody (`[gwa-1890 | hma-26]`) with `welfare-principle` & `hmga-1956-s6` in `applied_principles`.
     - `maintenance_sub_routes`: exposes `bnss-144`, `bnss-144-3`, `bnss-146`, `hma-24`, `hma-25` cleanly for maintenance intake & `tests/laya_maintenance_backtest.py`.
2. **`V71-P2-2` — True Graph v4/v4.1 Runtime Execution & Schema Repair (`src/build_graph_v4.py`, `src/laya_graph_engine.py`):**
   - Extend `build_graph_v4.py` to emit `graph/laya-crpc-bns-section-decision-tree-v4.1.json` (preserving frozen `v2`/`v3` untouched):
     - Add edges from `root:issue-classification` (or explicit `stage0:router-entry`) to `stage1:kannada-mapping`, `stage1:confidence-gate`, `stage1:conversation-context` so **100% of nodes (including all 5 previously unreachable from root)** are reachable from a single root node.
     - Populate explicit `options` on the `4` empty `choice` nodes (`stage1:kannada-mapping`, `stage2:demand-gate`, `stage2:pwdva-per-section-gate`, `stage1:conversation-context`).
     - Standardize `welfare-principle.laya_question` type metadata alongside documentation of its scoring semantics, and add `bnss-144-3` + `bnss-146` nodes cleanly under `maintenance:post-order-enforcement`.
   - Execute Layer A (`layer_a_filter_options`) and Stage 2 graph traversal directly inside `src/laya_graph_engine.py`, recording **genuine pre-gate `candidates_before_gate`**, `gated_out_layer_a`, and `gated_out_stage2` so `Fb` (`forbidden_proposed_before_gate`) is **actually measured** (fixing `laya_v7.py:100,168`).
3. **`V71-P2-3` — Multi-Turn Provenance, Contradiction Resolution & Full Override Support:**
   - Replace `apply_confirmations_v7` (`laya_v7.py:33-49`) with generic `resolve_turn_state(state, new_turn, confirmations)`:
     - Every fact key (`divorce_asked`, `mutual_consent`, `money_fact`, `custody_claim`, `residence_claim`, `violence`, `stridhan_claim`, `joint_property_claim`, `proceeding_pending_hma`, `being_filed`, `decree`, `demand_made`, `bnss_order`, `pre_bnss_order`, `in_scope`, etc.) supports **bi-directional override**: `True` removes any prior `negated_issues` entry and upgrades `issues[k].intent = "requested"`, while `False` adds to `negated_issues` and sets `issues[k].intent = "denied"`.
     - **Turn-Evolution Rules (MT1–MT4 Compliance):**
       - **Issue accretion (`MT4`):** Non-contradictory facts/issues from Turn `1..t-1` persist into Turn `t` (e.g., Turn 1 residence -> Turn 2 +violence -> Turn 3 +maintenance).
       - **Superseding state transitions (`MT2`, `MT3`):** Explicit updates on mutually exclusive state tuples (`gwa-1890 -> hma-26` when proceeding starts; `hma-13 -> hma-13b` when mutual consent is added; `hma-24 -> hma-25` when decree passes; `demand` -> `recovery` when demand is refused) automatically retire stale sections and log the transition in `override_log` without carrying stale routes forward.
       - **Conflicting Extraction Flagging:** When two assertions in the same turn (or an unconfirmed model guess vs prior span) conflict, set `FactEvidence.status = "conflicting"` and enqueue a targeted disambiguation prompt instead of silently guessing.
4. **`V71-P2-4` — Targeted Clarifying Question Engine (`[NEW] src/laya_clarifier.py`):**
   - Rank missing/uncertain/conflicting facts by **remedy-flip information gain** (max 2 questions/turn): e.g., (1) safety check if violence cues uncertain, (2) scope disambiguation if `kept == []` and `in_scope` uncertain, (3) `proceeding_pending_hma` / `being_filed` when gating `hma-24/26/27`, (4) `bnss_order` / `pre_bnss_2024` date for enforcement/variation, (5) `demand_made` for `bns-316`, (6) `minor_child` age under 18.

### 2.4 Pillar 2 Exit Criteria
- Single unified codebase (`laya_runtime.py` + `laya_graph_engine.py`) passing all `42/42` existing unit tests plus `>= 25` new multi-turn provenance, override, Layer-A `Fb`, and unified maintenance/full-scope tests.
- Multi-turn `MT1–MT4` suite (`docs/laya-10-10-exact-plan.md §4.4`): **`12/12` turn-level exact** and **`4/4` final-turn exact**, `0` dropped-fact errors, `0` stale-section carryover errors.
- `0` silent drops on in-scope queries; `100%` of Graph v4.1 nodes reachable from `root:issue-classification`.

---

## 3. Pillar 3 — Multilingual & Licensing Resilience (`V71-P3-*`)

**Objective:** Eliminate the `CC-BY-NC-4.0` noncommercial licensing blocker on `facebook/nllb-200-distilled-600M`, lift Kannada `Sealed Kannada-8` from `4/8` to `8/8`, support colloquial/dialectal Kannada + code-mixed **Kanglish** (`Latin`-script Kannada), and establish a clean `LanguagePack` scaling interface.

### 3.1 Current Multilingual & Licensing Blockers

1. **License Blocker (`NLLB-LIC` + `LIC-01`):** `src/laya_v7_extractor.py:24` defaults to `facebook/nllb-200-distilled-600M` (`CC-BY-NC-4.0`), and `README.md §12` currently specifies no OSS/commercial repository license (`No licence file is included yet`).
2. **Zero-Shot Multilingual Encoder Collapse:** `convaiinnovations/laya` (`mmBERT-base` 322M) scored `6/16` (`EN` prompts) / `0/16` (`KN` prompts) on `C13` (`docs/v7-multilingual-prose-latency-design.md:51-54`).
3. **Translation Loss & Idiom Fragility:** Whole-text NLLB dropped sentences (`B-204`, `B-215`); sentence-split NLLB still distorted idioms (`ಕೇಳಿಲ್ಲ` -> `"didn't hear it"` requiring hardcoded Kannada regex stem `r"ಕೇಳಿಲ್ಲ|ಕೇಳಲಿಲ್ಲ"` at `laya_v7_evidence.py:561`, and `ಅತ್ತೆಯ` -> `"aunt"` requiring `kn_aunt_held` at `L558`), while `Sealed Kannada-8` still failed `divorce 0/2`, `residence 0/1`, and `stridhan 0/1` (`pwdva-18` missed 2x).
4. **Code-Mixed Kanglish Blindness:** `detect_script_locale()` (`laya_v7_extractor.py:68-73`) only checks `[\u0c80-\u0cff]` or `locale.startswith("kn")`. Romanized Kannada (`"Nanna ganda hana koduttilla, nannannu maneyinda horahakuttiddare"`) routes as `"en"`, failing English extractors completely.

### 3.2 Concrete Multilingual Architecture (`V71-P3-1`..`V71-P3-4`)

1. **`V71-P3-1` — Permissive License Audit & NLLB-200 Replacement (`Apache-2.0 / MIT`):**
   - Conduct and pass a formal model-card/weights license check before training (`Apache-2.0`, `MIT`, or `BSD-3-Clause` ONLY for all production weights):
     - **Primary Architecture (Direct Bilingual Encoder — Zero Runtime Translation):** Distill/fine-tune a permissive multilingual encoder (evaluate `BAAI/bge-m3` MIT, `FacebookAI/xlm-roberta-base/large` MIT, `google/muril-base-cased` Apache-2.0, or `jhu-clsp/mmBERT-base` Apache-2.0 — verify exact Hugging Face license metadata at execution time) **directly** on our parallel `EN + KN + Kanglish` synthetic corpus (`V71-P1-2`) with the **same single-pass multi-head Stage 0/1 heads** (`V71-P1-3` / `V71-P5-1`).
     - **Why direct bilingual encoding wins 10x:** Removes the `1,186 MB` NLLB model footprint, eliminates translation latency (`2.39s` GPU / `~2.76s/Q` CPU), prevents translation information loss (`ಕೇಳಿಲ್ಲ`, `ಅತ್ತೆಯ`, coercive eviction tone), and avoids `CC-BY-NC` completely.
     - **Permissive Translation Backup (Optional `--mode translate_fallback`):** Benchmark `ai4bharat/indictrans2-indic-en-dist-200M` (verify MIT license on distilled checkpoint) or LoRA-finetuned `Qwen/Qwen2.5-1.5B-Instruct` / `Qwen3-1.7B` (Apache-2.0, sentence-level literal translator ONLY — never end-task legal classifier!) strictly on `C13` (`16-Q`) if any dialect gap needs an explicit English pivot. Retire `facebook/nllb-200-distilled-600M` from production defaults (move behind explicit `--allow-nc-research` flag only if retained for reproducibility).
   - Add explicit repository `LICENSE` + `THIRD_PARTY_NOTICES.md` (`LIC-01`), closing `README.md §12`.
2. **`V71-P3-2` — Kannada Morphology, Colloquialisms & Code-Mixed Kanglish (`[NEW] src/laya_lang_normalizer.py`):**
   - Upgrade `detect_script_locale(raw_text, explicit_locale)` to emit `{lang: "en" | "kn" | "kn_roman", script: "latin" | "kannada" | "mixed", code_mix_ratio: float}`:
     - Detect **mixed-script** inputs (Kannada Unicode + English legal/noun insertions like `"maintenance"`, `"divorce"`, `"school fees"`, `"locker"`, `"hospital"`), splitting cleanly without stripping English tokens.
     - Detect **Kanglish (Romanized Kannada)** via morphological suffix + stopword scoring (`-uttilla`, `-uttiddare`, `-abeku`, `-beku`, `-illa`, `-inda`, `-akke`, `nanna`, `ganda`, `hendati`, `magu`, `magalu`, `maga`, `mane`, `chinna`, `hana`, `hodeyu`) with strict zero-false-positive protection against standard Indian English legal words (`stridhan`, `streedhan`, `mangalsutra`, `panchayat`, `taluk`).
   - Expand synthetic Kannada augmentation (`V71-P1-2`) across **4 morphological/register axes**:
     1. Formal/news Kannada (`ಜೀವನಾಂಶ`, `ವಿಚ್ಛೇದನ`, `ಪಾಲನೆ`, `ಕೌಟುಂಬಿಕ ದೌರ್ಜನ್ಯ`).
     2. Colloquial/spoken Bengaluru–Mysuru & North Karnataka idioms (`ದುಡ್ಡು ಕೊಡಲ್ಲ`, `ಮನೆಯಿಂದ ಆಚೆ ಹಾಕಿದ್ದಾರೆ`, `ಹೊಡೆಯುತ್ತಾನೆ`, `ತವರು ಮನೆ`, `ಬಂಗಾರ ಇಟ್ಕೊಂಡಿದ್ದಾರೆ`, `ಅತ್ತೆ-ಮಾವ`).
     3. Agglutinative case/negation morphology (`ಕೇಳಿಲ್ಲ / ಕೇಳಲಿಲ್ಲ / ಕೇಳೇ ಇಲ್ಲ`, `ಬೇಡ / ಬೇಕಿಲ್ಲ`, `ಮಾರಿದ್ದಾರೆ / ಅಡವಿಟ್ಟಿದ್ದಾರೆ`).
     4. Code-mixed Kanglish in both Kannada script + Romanized Latin (`"Nanna husband nannannu maneyinda horage haakidare, I need maintenance and residence"`).
   - Preserve explicit Kannada/Kanglish factual span hints (`demand_made=False` on `ಕೇಳಿಲ್ಲ/ಕೇಳಲಿಲ್ಲ/kelilla`, violence/eviction stems) as verification signals alongside direct multilingual neural logits.
3. **`V71-P3-3` — Multi-Language `LanguagePack` Scaling Contract (`[NEW] src/laya_lang_pack.py`):**
   - Define a clean `LanguagePack` dataclass (`lang_code`, `unicode_range`, `sentence_split_regex`, `roman_detector`, `negation_demand_lexicon`, `template_catalog`, `benchmark_manifest`, `native_audit_signoff`) so onboarding Hindi (`hi`), Tamil (`ta`), Telugu (`te`), Malayalam (`ml`), or Marathi (`mr`) requires: (1) adding one `LanguagePack` config + synthetic parallel split, (2) adding localized `laya_prose_v2` templates, and (3) passing a native-speaker audit + `>= 8/8` / `>= 95%` held-out bar — with **zero edits** to Graph v4 Stage 2 legal logic.

### 3.3 Pillar 3 Exit Criteria
- **Zero `CC-BY-NC` weights** in default production/CI runtime (`NLLB-200` retired from default path); `LICENSE` + `THIRD_PARTY_NOTICES.md` merged.
- `C13` Kannada: `16/16` exact (`>= 0.98` micro-F1); `Sealed Kannada-8`: `4/8 -> 8/8` exact (`0` silent, `0` FP).
- Code-mixed **Kanglish & Romanized Kannada** held-out suite (`n >= 30` newly commissioned items): `>= 95%` exact, `0` silent, `0` FP.
- End-to-end Kannada latency reduced from `0.315–0.322s/Q` GPU (`>2.7s/Q` CPU) to **`< 50ms/Q` GPU** and **`< 0.5s/Q` CPU** via direct single-pass multilingual student encoding.

---

## 4. Pillar 4 — Legal Rigor, Citation Verification & Safety (`V71-P4-*`)

**Objective:** Guarantee statutory correctness across India's 2023 criminal-law transition (`IPC/CrPC/IEA -> BNS/BNSS/BSA`), close all unverified case-law citations (`P2.4`/`P2.5`), enforce safety routing decoupled from procedure, and ratify `D-V4-1..4` + `ground-truth-v3`.

### 4.1 Statutory `BNS / BNSS / BSA` Transitions & Cross-Walk Verification (`V71-P4-1`)

1. **Temporal Commencement & Saving-Clause Routing (`S.O. 848(E)` & 1 July 2024 Boundary):**
   - `BNS, 2023`, `BNSS, 2023`, and `BSA, 2023` commenced on **1 July 2024** (verified for BNSS via `S.O. 848(E)` in `src/laya_family_evidence.py:117-122` and `docs/laya-family-law-runtime.md:98`; verify exact Gazette notifications for BNS & BSA during implementation).
   - **Pre-1 July 2024 & `CrPC 125` / `IPC 406` Orders/Complaints:**
     - Maintain a deterministic `StatutoryCrosswalk` table in `[NEW] src/laya_legal_registry.py`:
       - `CrPC s.125` <-> `BNSS s.144` (new maintenance orders filed on/after 1 July 2024 use `BNSS s.144`; pre-July-2024 pending applications/orders retain `CrPC s.125/127` governance under `BNSS s.531` savings clause — NEVER silently emit `bnss-144-3` / `bnss-146` on an unverified `CrPC 125` or pre-July-2024 order!).
       - `IPC s.406` <-> `BNS s.316(2)` (criminal breach of trust for Stridhan misappropriation — use `BNS s.316` for post-July-2024 retention/sale, flag `IPC s.406` transition note if entrustment/FIR predates 1 July 2024).
       - `IPC s.498A` <-> `BNS s.85` (cruelty by husband or relatives — currently excluded from frozen 34-section graph per `docs/test-report-v2-layman.md:37`; keep in `unverified_excluded` / human-lawyer criminal escalation until explicitly verified & added to a `v5` graph, never hallucinating `BNS s.85` into `kept_ids`!).
       - `IEA s.65B` <-> `BSA s.63` (electronic evidence certificate for WhatsApp messages, bank transfers, audio/video threats, or UPI proofs in `doc-evidence` / `doc-stridhan-list-proof` checklists).
   - Wire `PRE_BNSS` & `OLD_ORDER` cross-walk logic directly from `laya_family_evidence.py` into the unified Stage 0/1 grounded verifier and `laya_prose_v2.py` (using a dedicated `existing_order_statute: "bnss_144" | "crpc_125" | "hma_24" | "hma_25" | "unknown"` fact).

### 4.2 Verified Statutory & Case-Law Registry (`[NEW] legal/verified_authorities.json`, `V71-P4-2`)

1. **Closing `P2.4` and `P2.5` Accurately (Incorporating Audit C1 & `docs/legal-decisions-v4.md`):**
   - **Already Verified (`legal-decisions-v4.md:402-509`):** ***Sukhdev Singh v. Sukhbir Kaur***, Supreme Court of India, 3-Judge Bench, Civil Appeal Nos. 2536 & 5726 of 2019, decided **12 Feb 2025**, `[2025] 2 SCR 1569 : 2025 INSC 197 : 2025 LiveLaw (SC) 195` — verified primary text holding HMA s.25/s.24 applies to HMA s.11 void-marriage decrees (discretionary; still requires a decree). Promote from `"UNVERIFIED"` to `"verified_primary"` with strict `allowed_scopes = ["hma-25_nullity_decree", "hma-24_nullity_pending"]`.
   - **Remaining Unverified Citations Still Open (`V71-P4-2`):**
     - `P2.5`: Read unread paragraphs **3–13, 15–17, and 19** of *Astha Thakur v. Dhananjay Kanwar* (`2025:HHC:46178`, FAO (FC) 29/2022, HP HC) from primary text (`docs/ground-truth-v2-erratum.md:153-156`).
     - `P2.4`: Independently verify from full official/primary judgments before any external documentation or optional citation:
       - *Balkrishna Ramchandra Kadam v. Sangeeta Balkrishna Kadam*, `(1997) 7 SCC 500` / `1997 INSC 641`
       - *Babulal Yadav v. Sonu Yadav*, `2023 SCC OnLine Chh 2815` (Chhattisgarh HC Full Bench, 4 July 2023)
       - *Krishna Kumar Gupta v. Priti Gupta*, Allahabad HC FA 1116/2024 (31 May 2025)
       - *Pratibha Rani v. Suraj Kumar*, `(1985) 2 SCC 370` (Stridhan criminal breach of trust)
       - *Satish Chander Ahuja v. Sneha Ahuja* (PWDVA ss.17/19 shared household scope — currently only checked via prose forbidden list!)
       - *Rajnesh v. Neha* (primary PDF already linked in `src/laya_family.py:26`; verify exact citation metadata & ensure `laya_family.py:257-261` never attaches it to non-maintenance / wrong issues).
2. **Enforce Registry Isolation (`Fp = 0` Guarantee):**
   - Scrub the **16** section entries in `graph/laya-crpc-bns-section-decision-tree-v4.json` (`bnss-144`, `hma-24`, `hma-25`, `pwdva-20`, `hma-26`, `gwa-1890`, `hmga-1956-s6`, `welfare-principle`, `hma-27`, `bns-316`, `pwdva-17`, `pwdva-18`, `pwdva-19`, `proc-filing-magistrate`, `doc-stridhan-list-proof`, `doc-residence-proof`) that embed case references inside graph JSON strings, replacing them with canonical IDs pointing to `legal/verified_authorities.json`.
   - Maintain `laya_prose_v2.py` default rule: **zero precedent strings emitted in consumer prose** unless an explicit verified-citation mode reads `legal/verified_authorities.json` where `status == "verified_primary"` AND `section_id in kept_ids` AND `scope` matches (preserving `Fp = 0` against Forbidden Items 1 & 2).

### 4.3 Urgent DV / Child Safety Routing Decoupled from Procedure (`V71-P4-3`)

- Wire the currently dead `urgent_safety_risk` key (`src/laya_v7_graph.py:362`) plus `child_safety_risk` (`L239`), `violence`, and `coercive_eviction_or_lockout` to an **orthogonal Stage 1 Safety Classifier Head** (`severity: none | threat_or_harassment | imminent_physical_or_child_danger`).
- **Strict Decoupling Rules:**
  1. `safety` escalation fires BEFORE and INDEPENDENTLY of `kept_ids`, `claimant_sex`, `domestic_relationship`, `proceeding_pending_hma`, `demand_made`, or `clarification` holds!
  2. Male DV victims (`B-148`), non-domestic assault/workplace harassment (`B-181`), child abduction/alcoholic-parent risk (`B-108`), and unclarified-scope abuse queries MUST emit `escalation_kinds += ["safety"]` + immediate non-legal helpline block (`112` Police/Emergency, `181` Women Helpline, `1098` Childline, Protection Officer / One Stop Centre) at the **top** of the consumer response, never gated behind procedural questions (`"first clarify if an HMA case is pending"`).
  3. Non-violent residence-only requests (`explicit_residence_order_only=True`, e.g., `B-010`, `B-133`, `B-189`) MUST NOT over-fire `safety` or `pwdva-18`.

### 4.4 Governance Ratification (`D-V4-1..4` & `ground-truth-v3`, `V71-P4-4`)

1. **`D-V4-1` (Custody Vocabulary Unification):** Ratify `statutory_primary` (`kept_ids` = `["gwa-1890"]` or `["hma-26"]`; `"hmga-1956-s6"` and `"welfare-principle"` stored in `applied_principles` and always rendered in prose) as the single canonical schema in `ground-truth-v3` and `brutal-bank-v2`, eliminating the `16-Q`/`Sealed` vs `Brutal-230` split.
2. **`D-V4-2` (`16-Q` Alignment — Separating Conflated Items, Audit C3):**
   - Explicitly separate the items that were previously conflated:
     - **True `D-V4-2` items (`docs/v4-decision-graph-architecture.md:310,337,352`):** (a) `H3/H10/H15` `court_expected` updated from `['Family Court', 'Magistrate']` to `['Magistrate']` post-D1-A; (b) `safety` escalation kind added on `K0/H4/H5/H6/H13`; (c) `H12` `procedure` OOS handoff convention aligned with `C10`/`F20`.
     - **Explicitly separate `16-Q` `v2` vs `v4` deltas:** (d) `H6` `pwdva-18` (absent in `v7` because Graph `v4` decoupled `pwdva-17/19` from `pwdva-18` and `H6` states co-living wish without violence/lockout — vs `ground-truth-v2` legacy triple bundle); (e) `H14` `hma-13` (frozen governing-section call vs `v4` relief-sought-only rule, flagged in `docs/v6-lane3-legal-decisions.md §3.1` as D6).
   - Independent rater ratifies `ground-truth-v3` (never editing frozen `ground-truth-v2-hma27-A.json` SHA `87818b1b...`), triggering the required Gate §6.1 baseline re-run.
3. **`D-V4-3` & `D-V4-4`:** Confirm adjudicated `hma-25` `lump_sum_settlement` rule (`B-022, B-119, B-154`), and formally document `Sealed` pre-D1-A `F8/F9/F10/F16/KN3` `hma-27` and `F1/F2/KN1` Bengaluru FCA s.7(2)(a) `Family Court` deltas as frozen sensitivity reports (while commissioning `sealed-v2` post-gate if aligned).

### 4.5 Pillar 4 Exit Criteria
- `legal/verified_authorities.json` has `100%` primary-verified citations (`P2.4` + `P2.5` closed) and `0` unverified case strings in `graph/*.json`.
- `100%` pass on `C17` pre-BNSS / CrPC-125 / IPC-406 / BSA-63 cross-walk tests (`0` misrouted `bnss-144-3`/`146`).
- `100%` safety recall on `C18` urgent DV/child safety scenarios regardless of `claimant_sex` / `domestic_relationship` / missing procedural facts (`0` false safety triggers on benign residence-only queries).
- Signed `D-V4-1..4` & `ground-truth-v3` adjudication record filed.

---

## 5. Pillar 5 — 10x Speed, Single-Pass Distillation & Edge Deployment (`V71-P5-*`)

**Objective:** Eliminate the **CPU latency failure** (`17.817s/Q` mean / `33.090s` max local 4Q `v6`, `61.93s/Q` Colab `v5`) and unlock edge/serverless deployment by reaching **`< 0.5s/Q` CPU** and **`< 50ms/Q` GPU** with zero recall loss, plus verified **Colab T4 `fp16` parity (`G14-T4`)**.

### 5.1 Why `v7` Cannot Scale on CPU Today (`docs/v7-multilingual-prose-latency-design.md`)

1. `PIXMELT/laya` (421M `ModernBERT-large`) runs per-prompt cross-encoding (`states x 9 noul` + Stage 2 `choice` prompts); `ONNXAgent` in `laya==0.5.5` runs options sequentially; `torch.compile` fails on Windows (`118.08s` load without Triton).
2. Multilingual runs load an extra `600M` `NLLB-200` encoder-decoder (`1,186 MB` fp16) running `beam=4` autoregressive decoding (`~2.76s/Q` on CPU even at `beam=1`).

### 5.2 Distillation, Quantization & Serving Pipeline (`V71-P5-1`..`V71-P5-4`)

| Task ID | Component | Concrete Engineering Spec |
|---|---|---|
| **`V71-P5-1`** | **Single-Pass Multi-Head Student Distillation** (`[NEW] scripts/distill_student.py`, `[NEW] src/laya_v7_student.py`) | - **Teacher:** Fine-tuned `v7.1` multi-head large encoder (`V71-P1-3`) generating soft logit targets over the `5,000`-example zero-leakage synthetic bilingual corpus (`EN + KN + Kanglish`, `V71-P1-2`).<br>- **Student Backbone:** Compact Apache-2.0/MIT multilingual encoder (`<= 120M–150M` params, e.g., 6-layer distilled `mmBERT`/`ModernBERT-small`/`MiniLM-L12` multilingual initialized from permissive weights) with **1 shared forward pass** producing all `11` issue logits, `28` fact logits, `3` enum heads, and `safety` severity simultaneously.<br>- **Pass Count Reduction:** Drops `~32–72` inferences/Q (`v3–v6`) or `9+` prompt passes/Q (`v7`) down to **1 batched forward pass** over `[full_q] + filtered_clauses` (`batch_size <= 8`, `max_seq_len <= 192`). |
| **`V71-P5-2`** | **ONNX Export & Static/Dynamic INT8 Quantization** (`[NEW] scripts/export_student_onnx.py`, `[NEW] models/student_int8.onnx`) | - Export pure `PyTorch -> ONNX (opset 17)` multi-head graph (`input_ids, attention_mask -> issue_logits, fact_logits, sex_logits, role_logits, time_logits, safety_logits`), completely bypassing `laya.ONNXAgent`'s sequential loop.<br>- Apply `onnxruntime.quantization.quantize_dynamic` (`QInt8` MatMul/Attention) + `ORT_ENABLE_ALL` graph fusion (`Gemm/LayerNorm/GELU`).<br>- Implement deterministic **shape-bucket padding** (`64 / 128 / 192` tokens) and **batch permutation invariance** (verified in `tests/test_v7_rules.py` for BOTH `mode="laya"` and `mode="student_onnx"`!).<br>- **Parity Guard:** Reject quantized artifact if `max |prob_fp32 - prob_int8| > 0.015` or ANY flip occurs on `16-Q` / `Brutal-230` / dev synthetic splits. |
| **`V71-P5-3`** | **Colab T4 `fp16` Parity & Standalone `v7.1` Notebook** (`[NEW] src/build_laya_v7_colab.py`, `[NEW] notebooks/live-laya-colab-test-v7.ipynb`) | - Generate standalone deterministic `v7.1` Colab notebook (closing the gap where `README.md §1` still points to `v6-brutal.ipynb`).<br>- Explicitly enforce `LAYA_CUDA_AMP=fp16` on Turing `sm_75` (`T4` lacks hardware `bf16` tensor cores, per `docs/v7-multilingual-prose-latency-design.md:225`) and log `T4` vs RTX 5050 score parity (`max_abs_diff <= 0.03`, `0` prediction flips) + cold/warm timing (`G14-T4`). |
| **`V71-P5-4`** | **Tiered Edge & Graceful Fallback Serving (`mode="auto"`)** | `auto` priority: (1) `student_onnx_gpu` (`< 50ms/Q`), (2) `student_onnx_int8_cpu` (`< 0.5s/Q`), (3) `laya_teacher_cuda` (`~0.13s/Q`), (4) zero-model `evidence` (`< 1ms/Q` EN-only emergency fallback). |

### 5.3 Pillar 5 Exit Criteria
- **CPU (`student_int8.onnx`):** Mean **`< 0.50s/Q`**, max **`<= 1.00s/Q`**, `16-Q` wall **`<= 8s`** (excl. load), model load **`<= 5s`** — passing `G14` by `> 30x` on CPU without CUDA!
- **GPU (RTX 5050 & Colab T4 `fp16`):** Mean **`< 50ms/Q`** (`0.05s/Q`), max **`<= 100ms/Q`**, `230-Q` wall **`<= 12s`**, model load **`<= 15s`**.
- **Accuracy Parity:** Student INT8 ONNX matches teacher `v7.1` within `<= 0.5%` micro-F1 and hits **`0` accuracy drop** on `16-Q`, `Brutal-230`, `Sealed Fresh-20`, `Sealed Kannada-8`, and Codex Maintenance `4-split`.
- **`G14-T4`:** Filed Colab T4 `fp16` run JSON/MD matching RTX 5050 predictions (`0` exact flips).

---

## 6. Pillar 6 — Consumer Prose Excellence, Kannada Localization & Human Verification (`V71-P6-*`)

**Objective:** Deliver localized, layman-readable, legally actionable English and Kannada responses with `Fp = 0` by construction, and close the human audit gates (`G12` blind legal rater + `P2.1` native Kannada speaker).

### 6.1 Fixing Current `laya_prose_v2.py` Gaps & Updating `src/README.md`

1. Fix `src/laya_prose_v2.py:558` (missing `"status": "ok"` on normal return) and `L625` (`prose_forbidden_check()` checking legacy `proceeding_pending` instead of canonical `proceeding_pending_hma`, which triggers false `Fp item 3` when `hma-13` renders from `proceeding_pending_hma=True, divorce_asked=False`).
2. Fix the false documentation claim in `src/README.md:15`: `laya_prose_v2.py` currently supports **English only** (`0` Kannada templates); update documentation only after localized Kannada templates land in `V71-P6-1`.

### 6.2 Localized Kannada Templates, Action Checklists & Human Workflows (`V71-P6-1`..`V71-P6-3`)

1. **`V71-P6-1` — Deterministic Localized Kannada Templates (`src/laya_prose_v2.py` + `[NEW] src/laya_prose_kn.py`):**
   - Implement `render_prose(rec, facts, target_lang="auto" | "en" | "kn")`: when `rec["lang"] in {"kn", "kn_roman"}` (or `target_lang="kn"`), render native deterministic Kannada templates (NOT runtime machine back-translation, preventing NLLB hallucination of statute numbers or forbidden terms!).
   - Cover all **20 sections** (incl. `bnss-144-3` & `bnss-146`), all **9 escalation kinds** + `safety` emergency helplines, `INTRO_LINE`, `CLOSING_LINE`, `OUT_OF_SCOPE_LINE`, and `INVALID_RECORD_HANDOFF` (`0` `?` characters, plain everyday Kannada verified by `P2.1`).
   - Expand `prose_forbidden_check()` with **Kannada parity checks**: regex traps for `"ಬಾಡಿಗೆ ಹಕ್ಕು"` / `"ಟೆನೆನ್ಸಿ"` (Forbidden #4), `"ಸಂಬಳದ ಚೀಟಿ"` / `"ಪೇ ಸ್ಲಿಪ್"` (Forbidden #9), invented rupee numbers (`₹`/`ರೂ.`/`ಸಾವಿರ`/`ಲಕ್ಷ` + monthly context, Forbidden #8), `?` / court-choice questions (Forbidden #5), `HMA` linked with `"ಜನನ ಪ್ರಮಾಣಪತ್ರ"` (Forbidden #6), and Kannada statutory pattern parity against `kept_ids` (Forbidden #7). Add `>= 15` Kannada adversarial mutants to `tests/test_prose_renderer_v2.py`.
2. **`V71-P6-2` — Layman Readability, Forum Nuance & Non-Coercive Document Checklists (`src/laya_prose_v2.py`):**
   - Add an optional deterministic `action_plan` / `document_checklist` section (strictly template-locked, `Fp = 0` checked):
     - **Immediate Safety Banner (top of output when `"safety"` in `escalation_kinds`):** Emergency numbers (`112`, `181`, `1098`) + Protection Officer / One Stop Centre note.
     - **Court & Local Forum Guidance:** Preserves deterministic forum (`Family Court`, `Magistrate`, `Registrar`), adding an informational Bengaluru/metro note when `bnss-144` fires (`"Where a Family Court is established, BNSS s.144 claims are filed in the Family Court under FCA s.7(2)(a); otherwise before a Judicial Magistrate First Class"`) — resolving the `F1/F2/KN1` confusion without breaking Forbidden #5.
     - **Document & Evidence Checklist (per kept section, strictly `g-salary-slips`-safe):** e.g., marriage proof, child birth/school-fee records (`school_fees_fact`), bank/property co-ownership papers (`hma-27`), Stridhan list/photos/written-demand copy (`bns-316`), medical/police/message records (`pwdva-18` + `BSA s.63` electronic proof), explicitly stating *"Provide whatever records you have; if salary slips or receipts are missing, say that they are missing."*
     - **Readability Audit:** Enforce average English sentence length `<= 22` words, zero Latin/legalese jargon (`pendente lite`, `in specie`, `mutatis mutandis` avoided in user text), and plain step ordering (`What applies -> Which court -> Next steps & documents -> Missing facts -> Disclaimer`).
3. **`V71-P6-3` — Blind Human Legal Rater (`G12`) & Native Kannada (`P2.1`) Sign-Off Workflows (`[NEW] scripts/export_human_audit.py`):**
   - Generate blinded audit packets stripping `gt_ids`, classifier scores, and `prose_forbidden_check` results for:
     - **`G12` Legal Prose Audit:** 2 independent legally literate raters score all `16-Q` + `Sealed Fresh-20` + `Sealed Kannada-8` + stratified `Brutal` sample outputs against Forbidden Items `1–9` (plus Lane 4 `P10–P11`), completeness `(a)–(d)`, and `25%` double-rating + adjudication (`docs/v6-lane4-prose-latency.md §6`).
     - **`P2.1` Native Kannada Speaker & Legal Audit:** Native Kannada legal reviewer signs off on (a) fluency & GT accuracy of `C13` (`B-203..B-218`) and `Sealed Kannada-8` (under strict read-only audit; any discovered GT error documented in a separate `kn-v2` sensitivity file without mutating frozen SHAs), (b) Kannada `laya_prose_v2` templates (`V71-P6-1`), and (c) Kanglish test items.

### 6.3 Pillar 6 Exit Criteria
- `tests/test_prose_renderer_v2.py`: `100%` pass across `246` existing + `>= 60` new EN/KN/maintenance/safety scenarios, `Fp = 0`, `quality_flags = 0`, `>= 30/30` EN + KN adversarial mutants caught, render latency `< 0.5ms/Q`.
- **`G12`:** Signed blind human legal rater report with **`Fp = 0`** across all sampled EN & KN answers (lifting the `<= 9.0` prose cap!).
- **`P2.1`:** Signed native Kannada speaker verification report filed in `docs/`.

---

## 7. Pillar 7 — Evaluation Moat, Statistical Power & Automated CI Gates (`V71-P7-*`)

**Objective:** Close all scorer bugs, expand evaluation power from `n = 230` (~`98.4%` Wilson lower bound) to **`n >= 400–500`** (`> 99%` 95% CI floor), add formal confidence calibration / ROC abstention bounds, and ship automated CI regression, leakage, and frozen-hash gates.

### 7.1 Fixing `tests/v7_backtest.py` Scorer Fidelity (Audit B1 + B2)

1. **`V71-P7-1` — Honest Scoring & Diagnostic Parity in `tests/v7_backtest.py`:**
   - **Measure `Fb` genuinely:** Compute `fb_count` from `candidates_before_gate` (Layer A pre-gate proposals violating statutory prerequisites) rather than `0`-by-construction post-Stage-2 `kept_ids`, and apply **`- 0.5 * Fb`** in the rating formula at `tests/v7_backtest.py:185`.
   - **Enforce Gate §2 Caps:** Compute and print BOTH `raw_formula_rating` and `capped_rating` applying `Fp >= 1 -> <= 5.0`, `Fb >= 1 -> <= 9.0`, `G12_unverified -> <= 9.0`, `sealed_not_passed -> <= 9.0`, `confirmation_missing -> <= 9.0`, `errors >= 3 -> <= 5.0` — never printing an uncapped `10.0` when any cap binds!
   - **Stop silent `H12` masking (`L125-126`):** Report strict `16-Q` `esc_bool` and `esc_kinds_strict` alongside `legacy_16q_compat` (`H12` / `safety` delta), never hiding `H12` mismatches.
   - **Restore `v6` Sealed Diagnostic Telemetry:** Log `hma27_gt_note_ids` sensitivity breakdown (`F8, F9, F10, F16, KN3` pre-D1-A vs post-D1-A) and `F1, F2, KN1` court sensitivity (`Family Court` vs `Magistrate`) inside aggregate sealed outputs while preserving `blind_text=True` (zero sealed question text printed).
   - **Flag Brutal-230 Pass Bar Failures Explicitly:** Assert `esc_kinds_strict >= 200/230` and `per_cat_min >= 0.75` inside `v7_backtest.py --strict` so `191/230` (`83.0%`) is automatically flagged as `FAIL` rather than obscured by `10.0`.

### 7.2 Scaling to `n >= 400–500` Stratified Evaluation Moat (`> 99%` Wilson CI, `V71-P7-2`)

Per [`docs/brutal-test-200-plan.md`](docs/brutal-test-200-plan.md#L211-L225), `230/230` proves only `>= 98.36%` at 95% confidence (Rule of three: `3/230 = 1.30%`). Reaching `> 99.0%` at 95% confidence requires `>= 300` failure-free items (`400/400 -> [0.9905, 1.0]`, `500/500 -> [0.9924, 1.0]`).

- Commission **`[NEW] test-bank/brutal-bank-v2.json` (`n = 450–500`)** authored by an independent legally trained rater + `25%` blind second-rater + third-reader adjudication, enforcing `0` 8-gram overlap against all prior banks & training sets:
  - Carry forward verified `Brutal-230` items under `ground-truth-v3` (`statutory_primary`) **plus `220–270` brand-new stratified adversarial cases**:
    - `C1–C14` balanced proportional expansion (`+100` items across multi-issue, role-reversal, negation, incidental mentions, court/quantum traps).
    - **`C15` Multi-Turn Conversations (`20` dialogues / `60` turns):** testing `MT1–MT4` evolution, late confirmations, contradictions, and issue accretion.
    - **`C16` Kanglish & Dialectal Kannada (`30` items):** Romanized Kannada, code-mixed English+Kannada, colloquial regional phrasing.
    - **`C17` Statutory Transition Traps (`25` items):** pre-1 July 2024 `CrPC s.125` / `IPC s.406` vs post-July-2024 `BNSS s.144/144(3)/146` / `BNS s.316` / `BSA s.63`.
    - **`C18` Urgent DV & Child Safety Decoupled (`20` items):** male DV victims, non-domestic danger, immediate child abduction risk, contrasted against benign explicit-residence-order controls.
    - **`C19` Adversarial Out-of-Scope & Abstention Stress (`35` items):** rent/consumer/employment/cheque-bounce/tax/criminal-theft/hypothetical/quoted/third-party noise interleaved with family-law trigger words (`"husband's boss"`, `"wife's landlord"`, `"friend's divorce"`).

### 7.3 Confidence Calibration, Selective Abstention & ROC Bounds (`V71-P7-3`)

1. **Calibration Pipeline (`[NEW] src/laya_calibration.py`):** Fit per-head **temperature scaling** (and isotonic regression sanity check) strictly on a held-out clean synthetic/dev calibration split (`n >= 500`, zero overlap with `16-Q`/`Brutal`/`Sealed`).
2. **Calibration & Selective-Abstention Metrics (logged per eval run):**
   - **ECE (Expected Calibration Error):** **`<= 0.03`** across issue and fact heads.
   - **Brier Score:** **`<= 0.04`** on binary/multi-label issue predictions.
   - **Risk-Coverage & Abstention ROC:** Plot selective risk vs coverage across gray-band `(tau_low, tau_high)` thresholds; require **AURC <= 0.02** and **`>= 99%` precision on auto-accepted predictions (`P >= tau_high`)** while routing `[tau_low, tau_high)` exclusively to targeted clarifying questions (`V71-P2-4`).

### 7.4 Automated CI & Release Gates (`[NEW] .github/workflows/laya-ci.yml`, `V71-P7-4`)

Create `[NEW] .github/workflows/laya-ci.yml` + pre-push hook (`[NEW] scripts/ci_gate.py`) running on every push/PR:
1. **Frozen SHA-256 & Graph Integrity Gate:** `python -m tests.test_graph_v4` (`7/7` frozen SHAs intact, `0` dangling edges, single-root reachability on `v4.1`).
2. **Full Unit, Runtime & Batch Permutation Invariance Gate:** `python -m unittest discover -s tests -p "test_*.py" -v` — extend `tests/test_v7_rules.py` to test **`mode="laya"`** and **`mode="student_onnx"`** batch-permutation invariance (`sort_by_length=True` forward vs reversed vs shuffled batches MUST return identical `kept_ids`, `court_live`, `escalation_kinds`, `prose`, and probabilities within `1e-4`), plus Codex maintenance tests (`tests/test_laya_family.py`) and multi-turn `SessionState` tests.
3. **Prose Safety Gate (`Fp = 0`):** `python -m tests.test_prose_renderer_v2` (EN + KN templates, `>= 30` adversarial mutants, `Fp = 0`, `quality_flags = 0`).
4. **8-Gram Overlap & Leakage Gate:** `python -m scripts.check_ngram_leakage --strict` guaranteeing `0` 8-gram overlap between any training/prompt/phrasebook file and any held-out/sealed test bank.
5. **License Allowlist Gate:** Verify default runtime model config (`laya_v7_extractor.py` / `laya_v7_student.py`) contains **zero** `CC-BY-NC` model IDs (blocking `facebook/nllb-200-distilled-600M` in default mode).
6. **CPU Latency & Determinism Gate (`G14-CPU` + `G15`):** Run deterministic 16-Q + smoke benchmark via `student_int8.onnx` on CI CPU (`mean < 0.5s/Q`, `max <= 1.0s/Q`, `Run 1 == Run 2` byte-identical outcome SHA-256).

---

## 8. Master Execution Roadmap, Crosswalk & Release Exit Scorecard

### 8.1 Phased Implementation Sequence

| Phase | Scope & Tasks | Gate Before Advancing |
|---|---|---|
| **Phase 0: Immediate Code & Scorer Hygiene** | `V71-P1-1` (all Section A code/rule bugs), `V71-P7-1` (`v7_backtest.py` `Fb` / §2 caps / `H12` / `esc_kinds` check), `V71-P6-1` partial (`status="ok"`, `proceeding_pending_hma` fix in `laya_prose_v2.py`), `V71-P4-4` (`D-V4-1..4` & `ground-truth-v3` ratification). | `Brutal-230` **`esc_kinds_strict >= 225/230`**, `Fb` genuinely measured `= 0`, `42/42` + expanded unit tests pass, `16-Q` reconciled cleanly under `ground-truth-v3`. |
| **Phase 1: Clean Corpus + Unified Multi-Turn Runtime** | `V71-P1-2` (5,000-example synthetic + hard-negative corpus, `0` 8-gram overlap), `V71-P1-3` (multi-head teacher), `V71-P1-4` (maintenance `34/34`), `V71-P1-5` (clarifying fallback), `V71-P2-1..4` (unified `laya_runtime.py`, Graph v4.1 single-root execution, `SessionState` multi-turn provenance, `bnss-144-3/146` + `PRE_BNSS`). | `Sealed Fresh-20` **`20/20`**, Maintenance `final_check` **`34/34`**, `MT1–MT4` **`12/12` turns / `4/4` final**, `0` silent in-scope drops, `>= 0.95` micro-F1 on synthetic CV. |
| **Phase 2: Permissive Multilingual, Legal Registry & Safety** | `V71-P3-1..3` (retire `NLLB-200`, permissive bilingual encoder + Kanglish + `LanguagePack` + `LICENSE`), `V71-P4-1..3` (`BNS/BNSS/BSA` cross-walk, `legal/verified_authorities.json` closing `P2.4/P2.5`, graph citation scrub, urgent safety decoupling), `V71-P6-1..2` (Kannada `laya_prose_v2` templates, checklists, forum nuance). | Zero `CC-BY-NC` dependencies; `Sealed Kannada-8` **`8/8`**; Kanglish `>= 95%`; `P2.4`/`P2.5` closed; `C17` & `C18` `100%`; `Fp=0` EN+KN. |
| **Phase 3: 10x Distillation, Edge ONNX & Colab T4** | `V71-P5-1..4` (single-pass student distillation + INT8 ONNX + `mode="auto"` tiering + `notebooks/live-laya-colab-test-v7.ipynb` T4 `fp16` parity). | CPU **`< 0.5s/Q` mean**, GPU **`< 50ms/Q` mean**, `G14-T4` parity (`0` flips), `0` accuracy drop vs teacher across all suites. |
| **Phase 4: Evaluation Moat (`n>=450`), Calibration, Human Audits & CI** | `V71-P7-2` (`brutal-bank-v2` `n >= 450–500`), `V71-P7-3` (temperature/isotonic calibration `ECE <= 0.03`), `V71-P7-4` (`.github/workflows/laya-ci.yml`), `V71-P6-3` (`G12` blind rater + `P2.1` native Kannada audit), `G15` dual locked confirmation re-runs. | Wilson 95% CI lower bound **`>= 99.0%`**, `ECE <= 0.03`, `G12` & `P2.1` signed `Fp=0`, `G15` `Run 1 == Run 2` across all suites, CI green. |

### 8.2 Crosswalk: `v7.1 / 10x` Tasks vs Existing Ledger, Gate & Audit Findings

| `10x_plane.md` ID | Existing Ledger / Gate / README Mapping | `@audit-tasks` Gap Closed |
|---|---|---|
| `V71-P1-1..5` | `SEALED-RECALL`, `P1.2`, `P1.5`, `P3.3`, Codex `final_check` | Fixes Audit A1–A6 (`laya_v7*.py`, `laya_prose_v2.py`), `9`-prompt ceiling, full-text-only boost, `L417` custody block, `8` dead graph keys, maintenance `32/34 -> 34/34`, `2` silent drops in `Sealed Fresh-20`. |
| `V71-P2-1..4` | `P1.3`, `P2.3`, `P2.6`, `P3.2`, `P3.4` | Unifies `laya_v7*.py` + `laya_family*.py` (Audit B3); executes Graph v4.1 JSON + Layer A at runtime (Audit B4); fixes `apply_confirmations_v7` (Audit A2); fixes `Fb` cloning (Audit A1). |
| `V71-P3-1..3` | `P1.6`, `G3`, `NLLB-LIC`, `README.md §12` | Replaces `CC-BY-NC` `NLLB-200` with permissive encoder (Audit B5); adds Kanglish/dialect support & `LanguagePack`; adds repo `LICENSE` (Audit B5). |
| `V71-P4-1..4` | `P2.2`, `P2.4`, `P2.5`, `D-V4-1..4` | Reconciles `Sukhdev Singh` verified status vs remaining unverified citations (`Balkrishna`, `Babulal`, `Krishna Kumar Gupta`, *Astha Thakur* paras `3-13,15-17,19`, Audit C1); cleans 16 graph entries; adds `BNS/BNSS/BSA` + `PRE_BNSS` cross-walk; decouples `urgent_safety_risk`; disentangles `D-V4-2` (Audit C3). |
| `V71-P5-1..4` | `P1.4`, `G14`, `G14-T4`, `P0.5` | Solves neural CPU latency failure (`17.8–61.9s/Q -> <0.5s/Q`) via single-pass student + INT8 ONNX; builds `v7` Colab notebook & runs `G14-T4` (Audit B5). |
| `V71-P6-1..3` | `P1.1`, `G12`, `P2.1`, `src/README.md` | Fixes `laya_prose_v2.py` `status`/`proceeding_pending_hma` (Audit A6); builds real Kannada prose templates correcting `src/README.md:15` (Audit C4); closes `G12` blind rater & `P2.1` native Kannada audit. |
| `V71-P7-1..4` | `P0.6–P0.8`, `G1–G16`, `README.md §6/§9` | Fixes `v7_backtest.py` `Fb`/caps/`H12`/`esc_kinds_strict` `191/230` failure (Audit B1–B2, C2); scales `n=230` (`98.4%` CI) -> `n>=450–500` (`>99%` CI); adds ECE/ROC calibration, `mode="laya"` batch invariance, and `.github/` CI (Audit B5). |

### 8.3 End-State Go / No-Go Scorecard (`v7` Current vs `v7.1 / 10x` Target)

| Metric / Gate | `v7` Verified (`bc7f40f`) | `v7.1 / 10x` Production Exit Bar |
|---|---:|---:|
| **`Sealed Fresh-20`** (blind exact / micro-R) | `7/20` (`0.5758`, `2` silent) | **`20/20`** (`1.000`, `0` silent, `0` FP) |
| **`Sealed Kannada-8`** (blind exact / micro-F1) | `4/8` (`0.8205`) | **`8/8`** (`1.000`, `0` silent, `0` FP) |
| **`Brutal` Scale & Exact / CI Floor** | `230/230` (`98.36%` CI, **`191/230` strict esc**) | **`>= 450–500`** (`>= 99.05%` 95% CI floor, **`>= 99%` strict esc**, `0` silent) |
| **Codex Maintenance `final_check`** | `32/34` (`2` FN) | **`34/34`** (`0` FP, `0` FN) |
| **Multi-Turn `MT1–MT4` Provenance** | Untested (`apply_confirmations_v7` partial) | **`12/12` turn exact, `4/4` final exact**, `0` carryover errors |
| **Pre-Gate `Fb` & Prose `Fp`** | `Fb` unmeasured; `Fp=0` EN only (no KN templates) | **`Fb = 0`** (truly measured pre-Layer-A) & **`Fp = 0`** (EN + KN + `G12` signed) |
| **CPU / GPU Latency** | CPU `17.8–61.9s/Q` (FAIL); GPU `0.133s/Q` | **CPU `< 0.50s/Q`** (INT8 ONNX); **GPU `< 50ms/Q`** (+ `G14-T4` parity) |
| **License & Commercial Safety** | `NLLB-200` `CC-BY-NC`; no repo `LICENSE` | **100% `Apache-2.0 / MIT` weights** + repo `LICENSE` + verified primary citations |
| **Calibration & Automated CI** | No calibration; `0` `.github/` workflows | **`ECE <= 0.03`**; full `.github/` CI (`SHA`, `8-gram`, `batch invariance`, `Fp=0`, `G15` parity) |
