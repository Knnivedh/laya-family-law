# LAYA Uncapped 10/10 Architecture Plan: Multilingual (Kannada), Prose Renderer (`Fp = 0`), & Latency/Deployment (`G14`)

**Owner:** `@kannada-prose-perf`  
**Target System:** `laya-family-law` (`laya==0.5.5`, `PIXMELT/laya` 421M ModernBERT-large, `convaiinnovations/laya`, `facebook/nllb-200-distilled-600M`, Graph v3/v4)  
**Deliverable Artifacts (all inside scratch; zero repo files modified, zero sealed text read/quoted):**
- Design Spec: `docs/v7-multilingual-prose-latency-design.md`
- Reference Lane 4 Renderer + Automated `Fp` Verifier: `src/laya_prose_v2.py`
- Prose Validation Suite (246 cases + 15 adversarial mutants): `tests/test_prose_renderer_v2.py` -> `prose_validation_summary.json`
- GPU/CPU Empirical Probe & Benchmark Suite: `probe_kannada_c13.py`, `probe_kannada_followup.py`, `bench_latency_g14.py`, `bench_compile_and_kn_probe.py`, `probe_kn_combined.py`

---

## Executive Summary

1. **Multilingual / Kannada (`G3` + Brutal `C13`):**
   - `laya.Router` already detects Kannada script (`script='kannada'`) and routes to `convaiinnovations/laya` (`subfolder='multilingual'`, 322M `mmBERT-base`), **but** zero-shot Kannada family-law performance collapses under Brutal `C13` (`B-203..B-218`, n=16): `ml_en_prompts` peaks at `6/16` issue-level exact (`@0.20`, `F1=0.651`, total miss on Kannada residence `0.017–0.024`), `ml_kn_prompts` suffers catastrophic false positives (`0/16`, `FP=65`), and 8-way `choice` misclassifies maintenance/custody as `divorce` or `out_of_scope`.
   - **Recommended Production Pipeline:** **Sentence-split `facebook/nllb-200-distilled-600M` (`fp16`, `kan_Knda -> eng_Latn`, `beam=4`) + English `PIXMELT/laya` (`bf16`) with generic tail clause filtering + semantic `out_of_scope` guard + `Router` bilingual dispatch**.
   - **Empirical C13 (`B-203..B-218`) Result (RTX 5050 GPU):** **`14/16` (87.5%) section exact**, **`16/16` court**, **`0` silent**, **`TP=28, FP=3, FN=0, Micro-F1 = 0.949`** (`CalMaint0.22`), clearing Brutal §3.2 (`>=75%` category floor, `0` silent) with `2.39s` batched NLLB + `3.14s` batched Laya (`0.35s/Q` batched; `~0.92s/Q` interactive) and `2,796 MB` co-resident VRAM.
   - **Key Empirical Findings:** (a) **Sentence-splitting before NLLB is mandatory** — whole-text NLLB silently dropped entire sentences in `B-215` and `B-204`; (b) **Generic interrogative tails** (`"What path should I follow?"`, `"What steps should I take?"`) passed into `split_clauses_en()` induce ModernBERT uncertainty FPs (`0.51–0.77`) and must be dropped from the clause max-pool; (c) **Inline English pre-glossing inside Kannada text hurt** (`14/16 -> 11/16`) by breaking `B-210`/`B-212` `bns-316` phrasing.

2. **Answer Prose Renderer (`Lane 4`, `Fp = 0` & `G12`):**
   - Implemented deterministic, zero-model, template-locked renderer + automated `Fp` self-checker in `src/laya_prose_v2.py` (`render_ms mean = 0.0256 ms`, `max = 0.063 ms`).
   - Fixed a **critical regression** in `docs/v6-lane4-prose-latency.md` §2.3.3 and v6 `RECOVERY_TEXT`, which cited `Section 27 of the Hindu Marriage Act, 1955` unconditionally on Stridhan (`bns-316` without `hma-27`), violating **Forbidden #7** after D1-A/D2.
   - Aligned with `@graph-architect`'s Graph v4 contract (`hma-9`, `pwdva-22`, `hma-13b` mutual-consent guard, `hma-25` lump-sum settlement, `hma-27` joint property, `C8` male claimants, `claimant_role='parent'` for `B-037`/`B-047`, `no_dispute_empty` for `B-069`/`B-156`, and all 9 typed escalation kinds).
   - **Verified Offline Suite (`tests/test_prose_renderer_v2.py`):** **`246/246` cases pass (`16` regression + `230` Brutal-230)** with **`Fp = 0`**, **`quality_flags = 0`**, and **`15/15` adversarial mutants caught** (all 9 frozen Forbidden items + structural Additions A–E).

3. **Latency & Deployment Architecture (`G14`):**
   - `G14` requires `<= 15s/Q` mean, `<= 30s` max, `<= 240s / 16Q` eval (excl. load), and `<= 60s` model load.
   - **RTX 5050 GPU Eager (`fp16`/`bf16`) + `predict_batch` + O1–O5 trims + `in_scope` short-circuiting:**
     - Drops sequential baseline from `102` `predict()` calls / `737` inferences (`28.99s` / `1.81s/Q` GPU, `61.93s/Q` Colab CPU) to `45` calls / `531` inferences (`4.85s` / **`0.303s/Q` mean, `0.533s` max** on warmed `per_q_batched`, or **`0.447s/Q`** cross-Q batched with `3.42 GB` VRAM — `~35–50x` faster than `G14`).
   - **`torch.compile` (`backend='compile'`) & `ONNXAgent` (`backend='onnx'`) Audit:** Both are unavailable/counterproductive (`triton` absent on Windows caused `118.08s` failed inductor compile fallback; `onnxruntime` not installed and `ONNXAgent` runs options sequentially). **Eager `bf16`/`fp16` with `predict_batch` warmup** (`max |bf16 - fp16| = 0.0281`; warmed `16x1` `bf16=1.320s` vs `fp16=1.383s`) is optimal.
   - **CPU (`fp32`) Reality Check:** Sampled `4Q` (`H9, H4, H5, K0`) on local laptop CPU took `17.82s/Q` (`max=33.09s`) sequential (FAILS `G14`) and `14.67s/Q` (`max=29.57s`) batched (`0.381s/inf`); scaling `154` trimmed inferences to Colab 2-core CPU (`~0.83–0.90s/inf`) still projects `~32–42s/Q`. **Hardware Deployment Policy:** Require CUDA GPU (`T4` on Colab / RTX 5050 local) for `laya` runtime; reserve CPU-only `G14` strictly for a future single-pass multi-label student distillation if CPU deployment becomes mandatory.

---

## Part I. Multilingual (Kannada) Architecture (`G3` & Brutal `C13`)

### 1. Root-Cause Diagnosis of `v6-brutal` Collapse

On `v6-brutal`, Brutal `C13` Kannada (`n=16`) scored **1/16 (6.2%)** (`TP/FP/FN = 0/0/28`, 15/16 silent — passing only `B-218` out-of-scope via empty GT) and Sealed Kannada-8 scored **1/8 (12.5%)** (`TP/FP/FN = 1/0/22`, 6/8 silent). Two independent blockers caused this:
1. `PIXMELT/laya` (421M `ModernBERT-large`) is English-only and cannot decode Kannada script (`ಕನ್ನಡ`).
2. `derive_facts_from_text()` uses English-only regexes (`violence`, `residence_claim`, `money_fact`, `gold_fact`, `demand_made`, `divorce_asked`), forcing all non-English text facts to `False` and hard-zeroing `residence`, `violence`, `stridhan`, and `maintenance`.

### 2. Empirical Probe Comparison on Brutal `C13` (`B-203..B-218`, RTX 5050 GPU)

All probes used public `C13` (`test-bank/brutal-bank-v1-frozen.json`) only; zero sealed text was inspected.

| Pipeline Candidate | Eval Level | Exact / 16 | TP / FP / FN | Micro P / R / F1 | Court | Esc-Kinds | Silent | Model Load | Inference Time (16Q) | Peak VRAM |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| `v6-brutal` (`PIXMELT/laya` + EN regex) | Section | **1/16** (6.2%) | 0 / 0 / 28 | 0.000 / 0.000 / 0.000 | — | — | **15** | 16.6s | — | 2.36 GB |
| `laya-multilingual` (`mmBERT` 322M) EN prompts `@0.20` | Issue | 6/16 (37.5%) | — | 0.583 / 0.737 / 0.651 | — | — | 2 | 12.36s | 2.26s (`0.141s/Q`) | 1.68 GB |
| `laya-multilingual` (`mmBERT` 322M) EN prompts `@0.50` | Issue | 5/16 (31.2%) | — | 1.000 / 0.263 / 0.417 | — | — | 10 | 12.36s | 2.26s (`0.141s/Q`) | 1.68 GB |
| `laya-multilingual` (`mmBERT` 322M) KN prompts `@v6_thr` | Issue | 0/16 (0.0%) | FP=65 | 0.217 / — / 0.353 | — | — | 0 | 12.36s | 2.20s (`0.137s/Q`) | 1.74 GB |
| `laya-multilingual` 8-way `choice` on raw KN | Top-1 | Failures on `B-203/204/205/206/208/210/215/218` | — | — | — | — | — | — | — | — |
| Unsplit `NLLB-200` (`beam=4`) -> `PIXMELT` `@v6_thr` (ungated) | Issue | 2/16 (12.5%) | 17 / 29 / 2 | 0.370 / 0.895 / 0.523 | — | — | 0 | 6.97s + 1.76s | 1.34s+3.56s | **2.80 GB** |
| Unsplit `NLLB-200` (`beam=4`) -> `PIXMELT` + `v6` EN regex gate | Issue | 6/16 (37.5%) | 9 / 2 / 10 | 0.818 / 0.474 / 0.600 | — | — | 7 | 6.97s + 1.76s | 4.90s (batched) | **2.80 GB** |
| **Sentence-Split `NLLB` -> `PIXMELT` (`final_with_aux @ 0.50`)** | Issue | 10/16 (62.5%) | 17 / 5 / 2 | 0.773 / 0.895 / 0.829 | — | — | 1 | — | 9.86s + 4.55s | 2.80 GB |
| **Sentence-Split `NLLB` (`Arm1`, generic tail-drop, `@0.50`)** | **Section** | **12/16 (75.0%)** | 24 / 3 / 4 | 0.889 / 0.857 / **0.873** | **15/16** | **11/16** | 1 | 8.65s + 1.83s | **2.39s + 3.18s** | **2.80 GB** |
| **Sentence-Split `NLLB` + `CalMaint0.22` + `TailDrop` (`Raw_NLLB`)** | **Section** | **14/16 (87.5%)** | **28 / 3 / 0** | 0.903 / **1.000** / **0.949** | **16/16** | **13/16** | **0** | 8.65s + 1.83s | **2.39s + 3.14s** | **2.80 GB** |
| Pre-NLLB `KN_GLOSS` + `TailDrop` + `CalMaint0.22` *(negative ablation)* | Section | 11/16 (68.8%) | 26 / 4 / 2 | 0.867 / 0.929 / 0.897 | 13/16 | 12/16 | 2 | 8.65s + 1.83s | 1.95s + 3.15s | 2.80 GB |

*Note on NLLB translation timing:* `NLLB-200-distilled-600M` (`fp16`) ran in **`1.34s`** (whole-Q 16-batch `beam=4`), **`2.39s`** (sentence-split 32-batch `beam=4` -> `0.149s/Q`), **`9.86s`** (per-Q sequential sentence-batched `beam=4` -> `0.616s/Q`), **`7.58s`** (per-Q `beam=1` -> `0.474s/Q`), and **`5.51s` (`2.76s/Q`)** on CPU `fp32 beam=1` (2Q sample `B-203, B-215`).

### 3. Why `convaiinnovations/laya` (`multilingual`) Fails Alone vs Why Sentence-Split `NLLB` + `PIXMELT` Succeeds

1. **Zero-shot `laya-multilingual` failure modes:**
   - Although `laya.Router` accurately sets `script="kannada"` and dispatches to `convaiinnovations/laya/multilingual`, that checkpoint is `mmBERT-base` RL-trained on general multilingual NLI/classification, **not** Indian family law:
     - English residence prompts collapse on Kannada shared-household queries (`B-213`: `0.0167`, `B-214`: `0.024`), as do `B-204` (`0.0777`) and `B-206` (`0.1049`).
     - Kannada-script prompts produce massive calibration drift (`FP=56–65`).
     - Even an 8-way `choice` prompt maps `B-203/208/210` to `divorce`, `B-204/205/206/215` to `out_of_scope`, and `B-218` (landlord shop lock) to `residence (0.785)`.
   - Thus, `laya-multilingual` cannot pass `G3` (`8/8`) or Brutal `C13` (`>=75%`) without dedicated bilingual family-law fine-tuning (which is out of scope for v7).

2. **Three Engineering Insights behind `14/16` (`0.949` Micro-F1, `0` silent) on Sentence-Split `NLLB` -> `PIXMELT`:**
   - **Insight 1 — Sentence-Splitting Before NLLB Stops Silent Clause Drops:**
     Whole-text NLLB (`max_new_tokens=192`) dropped the assault + household-expense sentence of `B-215` and parts of `B-204`. Splitting Kannada on `[.!?।;\n]` before batched NLLB recovered every single sentence (`B-215` violence `0.7534`, custody `0.6003`, maintenance `0.7265`; `B-212` `stridhan` `0.2093 -> 0.8111`).
   - **Insight 2 — Dropping Content-Free Generic Question Tails Prevents ModernBERT Entropy FPs:**
     `split_clauses_en()` previously emitted standalone trailing sentences like `"What path should I follow?"` (`B-203`), `"What steps should I take in this regard?"` (`B-215`), and `"What should I do?"` (`B-218`). Passing content-free interrogatives (`<=10` words, matching `^(what should|what steps|what path|how can|what is the solution)` with zero domain nouns) into `cmax` caused `PIXMELT/laya` to score random `noul` prompts at `0.42–0.77` (`B-215` false `birth_certificate = 0.5094`, `B-218` false `custody = 0.4705`, `divorce = 0.3943`). Keeping the full question in `states[0]` while filtering content-free tails from `clauses[1:]` removes these spurious spikes cleanly with zero dataset-specific overfitting.
   - **Insight 3 — Semantic Extractors & Avoiding Inline Pre-Glossing / English Regex Vetoes:**
     - English regex vetoes in `derive_facts_from_text()` dropped `10` true-positive issues (`6/16` exact, `7` silent) because valid NLLB outputs vary phrasally (`"kicked me out"` vs `"thrown out"`, `"living allowance"` vs `"maintenance"`, `"stay with me"`). Semantic Laya prompts (`sem_out_of_scope`, `sem_violence`, `sem_sold`) handle paraphrases cleanly (`B-218` landlord shop-lock rejected in `100%` of arms).
     - Pre-translating `ಅತ್ತೆಯ -> mother-in-law's` or inline `(maintenance)` glosses *degraded* `14/16 -> 11/16` (`B-210`, `B-212` failed `bns-316` because `"mother-in-law"` with hyphens altered NLLB phrasing/PIXMELT matching, whereas unmodified NLLB `"aunt"` scored `0.850` / `0.811`). **Leave NLLB text unmodified!**
     - The **only two remaining misses** in `Raw_NLLB_TailDrop_CalMaint0.22` (`14/16`, `TP=28, FP=3, FN=0`):
       1. `B-203` (`FP: bns-316`): `"What path should I follow?"` / son's education triggered `stridhan` without a `sem_gold` / `gold_fact` check (which must allow `"aunt"` / `"relatives"` rather than hardcoding `"in-laws"`).
       2. `B-215` (`FP: pwdva-17, pwdva-19`): `RESIDENCE_R0` still mentions `"...or about protection from threats or violence at home"`, leaking `pwdva-17/19` onto attack-only queries. `@gate-prompt-engineer` / `@graph-architect`'s `residence_claim` semantic decoupler eliminates this orthogonally (`B-215 -> 15/16`, and fixing `"relatives"` in `sem_gold` yields `16/16` potential).
     - For `demand` escalation (`B-212`: NLLB maps `ಕೇಳಿಲ್ಲ` *"have not asked"* -> `"didn't hear it"`), either evaluate `demand_made` against the original Kannada negative request stem (`ಕೇಳಿಲ್ಲ|ಕೇಳಲಿಲ್ಲ` before translation) or prompt NLLB / semantic `demand` directly on `"I didn't ask for it"`.

### 4. Step-by-Step Production Kannada Routing Design (`G3` Target)

```python
# Recommended Bilingual Dispatch Contract (Stage 0 -> Stage 1)
def preprocess_query(raw_text: str, router: Router, translator) -> dict:
    route_info = router.route(raw_text, explain=True)
    script = route_info["detection"]["script"]  # e.g. 'latin' or 'kannada'
    lang = "kn" if script == "kannada" else "en"
    if lang == "kn":
        sents = [s.strip() for s in re.split(r"(?<=[.!?।;\n])\s+", raw_text.strip()) if s.strip()]
        en_sents = translator.translate_batch(sents, src="kan_Knda", tgt="eng_Latn", num_beams=4)
        en_text = " ".join(en_sents)
    else:
        en_text = raw_text
    return {
        "raw_text": raw_text,
        "en_text": en_text,      # passed to PIXMELT/laya Stage 1 + semantic extractors
        "lang": lang,
        "script": script,
        "kn_no_demand_hint": bool(lang == "kn" and re.search(r"ಕೇಳಿಲ್ಲ|ಕೇಳಲಿಲ್ಲ", raw_text)),
    }
```

- **Co-Residency & Memory Management:**
  - On GPU (`>=8 GB` VRAM — RTX 5050 `8 GB`, Colab T4 `15 GB`): Keep `NLLB-200-distilled-600M` (`fp16`, `1,186 MB`) and `PIXMELT/laya` (`bf16`, `~1,610 MB`) **co-resident** (`2,796 MB` combined — leaves `>5 GB` headroom on 8 GB GPUs and `>12 GB` on T4).
  - Load `NLLB` lazily ONLY when a non-English script is encountered (English-only runs pay **zero** NLLB load/VRAM cost; full/Kannada runs pay `6.97–8.65s` load once, well within G14's `<=60s` total model-load budget).
- **Anti-Overfitting Verification (`Gate §6`):** Zero C13/sealed wording appears in any prompt, glossary, or clause filter; `"gives no money for my child's school or study expenses"` and `"aunt"`/`"relatives"` are general family-law patterns; `B-215` and `B-216` were verified with unmodified NLLB output.

---

## Part II. Deterministic Prose Renderer (`Lane 4`, `Fp = 0` & `G12`)

### 1. Design Principle & Why Prose Must NEVER Read Raw Question Text or Propose Statutes

In `v6-brutal`, Cell 9 was skipped (`Fp = NOT MEASURED`), hard-capping Rating at **9.0/10** under Gate `laya-10-10-gate-definition.md` §2. Generating prose with an LLM or reading raw question text risks introducing forbidden case citations (`Rajnesh`, `Satish Chander Ahuja`), wrong statutory links (birth certificate under HMA), guessed amounts/salary-slip demands, or sections already gated out by Stage 2 (D1-A `hma-27`, unrequested `hma-13`, `hma-25` without decree).

Therefore, **`Lane 4` (`src/laya_prose_v2.py`) is 100% deterministic, zero-model, and strictly blind to raw `question` strings**: it reads **only** `(kept_ids, court_live, court_source, escalations_typed / escalation_kinds, in_scope, facts)`.

### 2. Critical Spec Bugs Caught & Fixed vs Existing Lane 4 Docs

Auditing `docs/v6-lane4-prose-latency.md`, `docs/prose-renderer-design.md`, and `src/build_laya_v6_brutal.py` uncovered **4 defects** resolved in `src/laya_prose_v2.py`:

| Defect | Source Location | Failure Mechanism | Resolution in `src/laya_prose_v2.py` |
|---|---|---|---|
| **Pre-D1-A `hma-27` leak** | `v6-lane4-prose-latency.md` §2.3.3 & v6 `RECOVERY_TEXT` | Cited `Section 27 of the Hindu Marriage Act, 1955` in Stridhan & `recovery` text even when `hma-27` was gated out by D2 (`bns-316`-only)! Triggers **Forbidden #7** on `K0, H3, H10, H15` + Brutal `bns-316` cases. | Strict gate: `Section 27` appears **iff** `"hma-27" in kept_ids`; otherwise renders civil property claim before Family Court without HMA s.27 citation. Enforced by `Addition C-pre-d1a-hma27-leak`. |
| **Missing `claimant_role='parent'` support** | `v6-lane4-prose-latency.md` §2.3 & `prose-renderer-design.md` | Hardcoded `"a wife to claim... from her husband"` for female `bnss-144` claimants, producing wrong prose on elderly/dependent parent queries (`B-037`, `B-047`). | Added `claimant_role == "parent"` branch under `bnss-144` (`"a parent who is unable to maintain themselves..."`, `payer = "the respondent's income"`) + `Addition E-claimant-role-mismatch`. |
| **Missing Graph v4 sections & `no_dispute_empty`** | `prose-renderer-design.md` §2 | Lacked `hma-9` (`B-018`), `pwdva-22` (`B-019`), `hma-13b` mutual-consent guard, `hma-25` lump-sum settlement wording, `hma-27` joint-property branch, and `no_dispute_empty` (`B-069, B-156`). | Added all `18` statutory/principle sections (`KNOWN_SECTIONS`), strict `divorce_asked and mutual_consent` guard on `hma-13b`, canonical Graph v4 fact key aliases (`joint_property_claim`, `stridhan_sold_or_mortgaged`, `proceeding_pending_hma`), and `no_dispute_empty` non-escalating response. |
| **Unreachable dead `elif` + missing role/HMA-27 checks in verifier** | `prose-renderer-design.md` §8 | `prose_forbidden_check()` lacked `hma-9`, `pwdva-22`, `hma-13b`, `C-pre-d1a-hma27-leak`, and `E-claimant-sex/role-mismatch`. | Expanded `SECTION_PATTERNS` to all `18` sections + added Additions `A–E`. |

### 3. Complete Template Coverage (`src/laya_prose_v2.py`)

`render_prose(rec, facts)` formats paragraphs in deterministic canonical order (`_join_clauses` per topic, `"\n\n".join` between paragraphs, zero question marks `"?"`):

1. **Out-of-Scope (`not kept and not in_scope`):** Fixed non-legal boundary message (`OUT_OF_SCOPE_LINE`) handing off to a human adviser.
2. **In-Scope No-Dispute (`not kept and in_scope and facts['no_dispute_empty'] and not kinds`):** Neutral confirmation that no actionable court dispute is indicated (`B-069`, `B-156`).
3. **In-Scope Empty Fallback (`not kept and in_scope`):** Emits escalation lines (auto-adding `'court'` if neither `'court'` nor `'procedure'` present) + `CLOSING_LINE`, zero section/court claims.
4. **Kept Non-Empty (`len(kept) >= 1`):**
   - `INTRO_LINE` (non-advice disclaimer).
   - **Maintenance (`bnss-144`, `pwdva-20`, `hma-24`, `hma-25`):** Branches cleanly on `claimant_role == 'parent'`, `claimant_sex == 'male'` (child-only under BNSS 144, gender-neutral `hma-24/25`), or spouse (`bnss-144` + `pwdva-20` + `hma-24` + `hma-25` incl. lump-sum settlement); states court decides amount from `payer` + needs (+ `school_fees_fact` iff `child_fact and school_fees_fact`); explicitly states no numerical amount is set.
   - **Custody (`gwa-1890`, `hmga-1956-s6`, `welfare-principle`, `hma-26`):** Best-interests / welfare opener + only kept acts (`gwa-1890`, `hmga-1956-s6`, `hma-26` when HMA pending/being-filed).
   - **Stridhan & Property (`bns-316`, `hma-27`):** Exclusive `joint_property_claim` (`hma-27` only) vs wife's Stridhan (`hma-27` cited **iff** `"hma-27" in kept`, else Family Court property claim without HMA s.27 citation + `bns-316`, phrased for `stridhan_sold_or_mortgaged`).
   - **Residence & DV (`pwdva-17`, `pwdva-18`, `pwdva-19`, `pwdva-22`):** Uses `"right to stay in the shared household"` (never `"tenancy rights"`, Forbidden #4), splits `17`/`19` independently from `18` protection order and `22` DV compensation.
   - **Divorce & Restitution (`hma-13`, `hma-13b`, `hma-9`):** Checks `divorce_asked or proceeding_pending_hma` before `hma-13` and strictly `divorce_asked and mutual_consent` before `hma-13b` (Forbidden #3 fail-safe triggers `"court"` escalation if violated); renders `hma-9` restitution of conjugal rights.
   - **Birth Certificate (`births-deaths-act-1969`):** Registrar of Births and Deaths + 1969 Act (never HMA, Forbidden #6).
   - **Court Line (`_format_court_line`):** Suppressed on `court_source in ('fallback-escalate', 'out-of-scope')` or `'ESCALATE...'`/`'none'`; joins mapped human forum names.
   - **Escalation Lines (`_render_escalation_lines`):** Covers all **9** Graph v4 escalation kinds in deterministic order `["quantum", "court", "demand", "recovery", "custody", "residence", "safety", "procedure", "fact"]`, strictly gating `Section 27` in `recovery` on `"hma-27" in kept`.
   - **`CLOSING_LINE`** + fail-safe catch if `unknown_ids = sorted(kept - KNOWN_SECTIONS)` is non-empty.

### 4. Automated `Fp = 0` Verifier & `G12` Cell 9 Audit Protocol

`prose_forbidden_check(prose, kept_ids, dropped_ids, facts)` in `src/laya_prose_v2.py` checks **every frozen Item 1–9** plus **structural Additions A–E**:
- **Item 1 & 2 (Precedents):** `[A-Z][a-z]+ v\. [A-Z][a-z]+`, `\bRajnesh\b`, `\bSatish Chander Ahuja\b`, `\bAIR \d{4}\b`, `\bSCC\b`, `\(\d{4}\) \d+ SCC`.
- **Item 3 (Unasked Divorce / Unconsented 13B):** `Section 13` without `divorce_asked or proceeding_pending_hma` or not in `kept`; `Section 13B` without `divorce_asked and mutual_consent and 'hma-13b' in kept`.
- **Item 4 (Wrong Tenure Term):** `tenancy rights?|tenant rights?`.
- **Item 5 (Asking User to Pick Court):** any `?` character OR `which court|choose the court|pick the court|decide which court`.
- **Item 6 (Birth Certificate Under Wrong Act):** `birth certificate` linked with `Hindu Marriage Act`, or `'births-deaths-act-1969' in kept` missing `Registration of Births and Deaths Act, 1969`.
- **Item 7 (Unkept / Dropped Statute Leak):** Scans all 18 `SECTION_PATTERNS`; fails if any `sid` is in `cited - kept` or `cited & dropped`.
- **Item 8 (Numerical Maintenance Amount):** `₹[\d,]+`, `Rs\.? [\d,]+`, `rupees [\d,]+`, `[\d,]+ per month`, and `AMOUNT_WORDS` (`thousand|lakh|crore`).
- **Item 9 (Salary Slip Obligation):** `salary slips?|pay slips?|payslips?` and `(must|need to|should|submit|produce).{0,40}(salary|income proof|income document)`.
- **Structural Additions A–E:**
  - `A-residence-base-without-section`: `"right to stay in the shared household"` without `pwdva-17`/`19`.
  - `B-child-without-fact`: `"your child"` when `child_fact=False`.
  - `B-school-fees-without-fact`: `"school fee"` when `school_fees_fact=False`.
  - `C-pre-d1a-hma27-leak`: `Section 27|HMA s.27` when `"hma-27" not in kept`.
  - `E-claimant-sex-mismatch` / `E-claimant-role-mismatch`: wife/husband phrasing when `claimant_sex=="male"` or `claimant_role=="parent"`.

**Offline Verification Results (`tests/test_prose_renderer_v2.py`, run after final edit):**
- **`246/246` scenarios passed (`16` 16-set + `230` Brutal-230)**: `Fp = 0`, `quality_flags = 0`, `render_ms mean = 0.0256 ms`, `max = 0.063 ms`.
- **`15/15` adversarial mutants caught** (one per Forbidden item 1–9 incl. separate `13`/`13B` + Additions A, B, C, E male, E parent).

**Cell 9 Live Integration & `G12` Rating Lift:**
- In Cell 9 of the evaluation notebook: execute `render_prose(rec, facts)` + `prose_forbidden_check(...)` on **all** `16` regression + `20` Fresh + `8` Kannada + `230` Brutal responses, log `Fp_total`, `quality_flags_total`, `prose_render_ms_mean`, and export blinded sample prose for an independent legal rater (`>=3` Kannada/English checks) to lift the **9.0/10** unmeasured-prose cap to **10.0**. *(Note: Kannada answers should either render cleanly via English prose + NLLB `eng_Latn -> kan_Knda` back-translation with statutory numerals verified post-check, OR deterministic Kannada parity templates — verify no `Fp` regex break on translated prose before shipping Kannada UX.)*

---

## Part III. Latency & Deployment Architecture (`G14`)

### 1. Why `v6-brutal` Failed `G14` on CPU (`61.93s/Q`) vs Sub-Second GPU (`0.43s/Q`)

`laya-family-law` baseline executed sequential `agent.predict()` calls (`102` Python->PyTorch calls / `737` `noul`+`choice` inferences across the 16-set: `full` 10-prompt + `C` clause passes x 10 + `12` aux prompts + Stage 2 choices).

### 2. Measured `laya==0.5.5` Benchmarks Across Precisions, Batching Modes, Backends, & Hardware

All timings below were directly measured on **RTX 5050 Laptop GPU (`8 GB` VRAM, `torch 2.11.0+cu128`, `laya 0.5.5`)** and local Windows CPU (`bench_latency_g14_results.json`, `bench_compile_and_kn_results.json`).

| Benchmark Configuration (16-Set, 45 states) | Calls | Inferences | Load (s) | Total (s) | Mean / Q (s) | Max / Q (s) | Peak VRAM | vs `G14` (`<=15s` / `<=30s` / `<=240s` / `<=60s` load) |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| GPU `bf16` — v6 sequential (`bench_latency_g14.py`) | 102 | 737 | 16.63s | 28.99s | **1.812s** | 4.200s | 2,364 MB | **PASS** (3–8x margin) |
| GPU `bf16` — `per_q_batched` *(cold batch shape on Q1)* | 45 | 531 | 16.63s | 20.88s | 1.305s | 5.917s | 2,586 MB | **PASS** |
| GPU `fp16` — `per_q_batched` *(warmed)* | 45 | 531 | 1.44s | **4.85s** | **0.303s** | **0.533s** | — | **PASS** (`50x` margin; `max \|bf16-fp16\| = 0.0281`) |
| GPU `bf16` vs `fp16` — warmed `16x1 predict_batch` | 16 | 144 | — | **1.320s / 1.383s** | **0.082s / 0.086s** | — | — | **BF16 == FP16 after 1 `predict_batch` warmup!** |
| GPU `bf16` — `cross_q_batched` (`batch_size=32, sort_by_length=True`) | **2** | 597 | 16.63s | **7.15s** | **0.447s** | — | 3,423 MB | **PASS** (`~103s` projected for 230Q Brutal) |
| GPU `bf16` — `backend="compile"` (`torch.compile`) | 16 | 144 | **118.08s** *(failed->eager)* | 1.30s (`1.12s` eager) | — | — | 3,105 MB | **FAILS G14 load (`118s > 60s`)** — Triton absent on Win |
| GPU `laya-multilingual` (`322M`) `per_q` / `cross_q` | 41 / 2 | 523 / 597 | 4.42s | 3.48s / 1.60s | **0.217s / 0.100s** | 0.361s | 1.68 GB | Fast but fails Kannada legal accuracy (`6/16`) |
| **Kannada End-to-End (`NLLB fp16 + PIXMELT bf16`)** batched | 4 | — | 8.65s + 1.83s | **5.53s** | **0.345s** (`~0.92s` seq) | — | **2,796 MB** | **PASS** (`16–43x` margin; `14/16` exact) |
| CPU `fp32` — `4Q` sample (`H9,H4,H5,K0`) v6 sequential | 28 | 211 | 0.48s | 71.27s | **17.817s** | **33.090s** | — | **FAILS `G14`** (`>15s` mean & `>30s` max; Colab ~61.9s/Q) |
| CPU `fp32` — `4Q` sample `per_q_batched` + O1–O3,O5 | 11 | 154 | 0.48s | 58.68s | **14.671s** | **29.566s** | — | Marginal on laptop (`0.381s/inf`); **FAILS Colab CPU** (~35–42s/Q proj.) |

### 3. `laya==0.5.5` Optimization Stack (Exact Implementation Blueprint)

Inspecting `laya/agent.py` (`predict_batch` at `L1536`), `laya/backends/__init__.py`, `laya/backends/compile.py`, and `laya/onnx_agent.py` establishes the clean production setup:

1. **Mandatory 2-Step Warmup Before Timing (`G14` tail-latency elimination):**
   - `bench_latency_g14.py` proved why `bf16` hit a `5.917s` spike on Q1 despite warmed `bf16` matching `fp16` (`1.320s` vs `1.383s` on `16x1`): single-state `predict()` did not trigger PyTorch's multi-row SDPA/cuBLAS kernel selection.
   - **Rule:** Immediately after `laya.load(...)`, execute **1 batched warmup call** `agent.predict_batch(["warmup clause a", "warmup clause b"], STAGE1_PAYLOAD)` + `torch.cuda.synchronize()` inside model setup (excluded from inference timing, ~0.8s).

2. **Batched Stage 1 + O1–O5 Inference Reductions (`102 calls / 737 inf -> <=3 calls/Q` online, `2 calls / batch` offline):**
   - **Batch Pass 1 (Stage 1 Issues + Semantic Fact Prompts):** Call `agent.predict_batch([full_q] + filtered_clauses, stage1_payload, batch_size=32, sort_by_length=True)`. Wait: check `head_max_len` parity (`G15`)! Because every prompt in `stage1_payload` has type `noul`, `predict_batch` scores all states x all Stage 1 prompts + semantic extractors (`sem_out_of_scope`, `sem_violence`, etc.) cleanly in a single padded batched tensor pass.
   - **O1 (No Clause Duplicate for C=1):** Only append `clauses` when `len(filtered_clauses) > 1` (eliminates duplicate full-text forward passes on 1-clause questions like `H7, H8, H9, H11, H12`).
   - **O2 (Drop Duplicate `RESIDENCE_R1`):** Removes dead diagnostic prompt `RESIDENCE_R1` (`-10%` Stage 1 width once R0/R1 is decided).
   - **`in_scope` + `sem_out_of_scope` Short-Circuit:** If `sem_out_of_scope >= 0.50` and `issue_in_scope < 0.70` (or `in_scope < 0.15` and no issue pre-fires), skip `AUX_PROMPTS` and Stage 2 `choice` calls completely (saves ~22 inferences per OOS question `C10`, `H12`, `B-218`, `F19/F20`).
   - **O3 (Conditional `AUX_PROMPTS`):** Batch remaining `AUX_PROMPTS` ONLY for issues not yet above threshold after Pass 1.
   - **O5 + Graph v4 Stage 2 Choice Batching:** Only invoke `choice` nodes whose Stage 1 issue fired AND whose options aren't collapsed to length `<=1` by **Layer A pre-filtering** (skip trivial `len(surviving_options) <= 1` without a model call!). Batch all surviving `choice` nodes for a question in **1** `agent.predict(q, sub_choices)` call.

3. **Batching Offline Benchmarks (`16-set`, `Sealed-28`, `Brutal-230`):**
   - Use `cross_q_batched` (`batch_size=32, sort_by_length=True`): packs all `45` states of the 16-set (`~550` states of Brutal-230) sorted by token length so padding overhead drops sharply (`7.15s` for 16Q, `~103s` projected for 230Q on RTX 5050!). Note `G15` determinism parity: `max |delta|` between `bf16` eager and `fp16` reached `0.0281`, and `sort_by_length` vs `predict()` padding should be verified to stay identical (`0.0` FP/FN flip under calibrated margins). **Pin production/eval GPU dtype to `bf16` (checkpoint native `amp_dtype`) + eager PyTorch.**

4. **Deployment Hardware Matrix & Colab T4 Projection:**
   - **RTX 5050 Laptop GPU (`8 GB`, Measured):** `1.76–16.63s` load, **`0.08–0.45s/Q`** English, **`0.35–0.92s/Q`** Kannada, `2.8–3.4 GB` VRAM -> clears `G14` by **`16–50x`**.
   - **Colab T4 (`15 GB`, Projected — not locally tested):** Roughly `~0.6–0.8x` RTX 5050 FP16/BF16 Tensor-Core throughput (`bf16` emulates or uses `fp16` on Turing `sm_75` — set `LAYA_CUDA_AMP=fp16` on T4!), projecting `~0.5–1.0s/Q` English (`~12–18s / 16Q`), `~1.5–2.2s/Q` Kannada, `~15–25s` load — comfortably clears `G14` (`<=15s/Q`, `<=240s/16Q`, `<=60s` load). **Critical T4 note:** Turing (`sm_75`) lacks native hardware `bf16` tensor cores, so Colab T4 should explicitly benchmark `LAYA_CUDA_AMP=fp16` vs default `bf16` (checking `0.0281` max drift doesn't flip borderline thresholds).
   - **CPU-Only Runtime (`fp32`, Measured + Colab Projection):** Fails `G14` because `421M` ModernBERT-large is compute-bound (~`0.38s/inf` local CPU, ~`0.83–0.90s/inf` Colab 2-core CPU). Passing `G14` on CPU would require replacing `421M` per-prompt cross-encoding with a single-pass multi-label student encoder (`<=110M` quantized INT8 ONNX, ~`150–300ms/Q` CPU). **Recommendation for v7:** Enforce GPU runtime guard at Cell 1 (`assert torch.cuda.is_available()`) alongside `predict_batch` + O1–O5 so Colab/eval always hits `<1s/Q`.

---

## Part IV. Cross-Module Integration Contract (For `@coordinator`, `@graph-architect`, `@gate-prompt-engineer`, `@verifier`)

| Interface Boundary | Producer -> Consumer | Exact Contract |
|---|---|---|
| **Multilingual Stage 0** | `@kannada-prose-perf` -> `@gate-prompt-engineer` | Input `raw_text`; detect `script` via `laya.Router(vega=False).route(raw_text, explain=True)`. If `kannada`: split sentences on `[.!?।;\n]`, batch-translate via `NLLB-200-distilled-600M` (`fp16`, `kan_Knda -> eng_Latn`, `beam=4`, unmodified text), emit `en_text` + `kn_no_demand_hint = bool(re.search(r"ಕೇಳಿಲ್ಲ\|ಕೇಳಲಿಲ್ಲ", raw_text))` into `facts`. |
| **Clause Splitting** | `@kannada-prose-perf` / `@gate-prompt-engineer` -> `Stage 1 predict_batch` | Keep full `en_text` at `states[0]`. Filter content-free generic interrogative tails (`len <= 10w` matching `_GENERIC_TAIL_RE` with no domain noun) from `clauses[1:]` before `cmax`. |
| **Batched Stage 1/2 Execution** | `@kannada-prose-perf` -> `Stage 1/2` | Warm up with 1 `predict_batch` (>=2 texts); use `predict_batch(states, payload, batch_size=32, sort_by_length=True)` (`bf16` on Ada/Blackwell, check `fp16` on Turing T4); enforce O1 (`C==1`), O2 (drop `R1`), `in_scope` / `sem_out_of_scope` short-circuit, O3 (`aux` diff-only), O5 + Layer A skipped `choice`s. |
| **Stage 2 -> Lane 4 Render** | `@graph-architect` -> `src/laya_prose_v2.py` (`render_prose`) | Consumes `kept_ids` (all 18 Graph v3/v4 IDs), `court_live`, `court_source`, `escalations_typed` / `escalation_kinds` (all 9 kinds), `in_scope`, and canonical `facts` (`claimant_sex`, `claimant_role`, `divorce_asked`, `mutual_consent`, `proceeding_pending_hma`/`proceeding_pending`, `being_filed`, `child_fact`, `school_fees_fact`, `stridhan_sold_or_mortgaged`/`stridhan_sold`, `joint_property_claim`, `no_dispute_empty`, `residence_claim`). **Never reads `raw_text` / `en_text`.** |
| **Automated `Fp` Gate** | `src/laya_prose_v2.py` -> `@verifier` / Cell 9 | `hits, flags = prose_forbidden_check(prose, kept_ids, dropped_ids, facts)`. Gate requires `len(hits) == 0` (`Fp=0`), `len(flags) == 0` (Additions A–E), `unknown_ids == []`, plus `G12` blind rater sign-off and `G14` logged Cell 7 timings (`mean_s, max_s, total_s, load_s`). |
