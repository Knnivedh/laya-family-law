# LAYA v7.1 — Implementation + Integration Swarm — Shared State

Coordinator: parent agent's implementation coordinator (this session). Working copy: `~/workspace/laya-v71-work`, HEAD `90e20c5` (recall swarm merged, pushed to GitHub, 43 commits).
Goal: implement the classifier system properly, integrate it end to end, and make it runnable in Google Colab with proper backtesting. User rule: **Google Colab ONLY for computing/testing/code — no Kaggle, no comparison.**

## Baselines (measured, do not re-claim)

- Frozen validation split (500, sha256 `7640d067c28abf539131dbcc891e4bdffedf62bbef4a7d66c1659bb96d07e58e`): **261/500 = 52.2%** (rule-based evidence mode). Kaanoon-28: **14/28 = 50.0%**. 16-Q: **14/16**. Unit suite: **66 tests OK**. Brutal-230 via the C1 integrated runtime + C3 harness (rule-based): **210/230 = 91.3%**; the **230/230** figure is the v7 live run (neural/CUDA), never an evidence-mode number — see the Brutal note below.
- Sealed Fresh-20 **7/20 (35%)**, Kannada-8 **4/8 (50%)** — sealed re-run happens ONLY on Colab/RTX, never here.
- **No claim of ≥70% until a real sealed re-run measures it.**

## Frozen files — NEVER touch (any lane)

- `graph/laya-crpc-bns-section-decision-tree-v2.json`
- `graph/laya-crpc-bns-section-decision-tree-v3.json`
- `ground-truth/ground-truth-v2-hma27-A.json` (16-Q GT lives here; read-only)
- `test-bank/brutal-bank-v1-frozen.json`
- `test-bank/sealed/sealed-fresh-20.json`, `test-bank/sealed/sealed-kannada-8.json` (never open beyond aggregates already logged)
- `notebooks/live-laya-colab-test-v6-brutal.ipynb`
- `tests/test_graph_v4.py`, `tests/test_prose_renderer_v2.py` (expectations frozen; the tests must keep passing)
- Graph v4 (`src/laya_v7_graph.py` routing logic) and the prose renderer (`src/laya_prose_v2.py`) stay frozen — no behaviour change to compensate for extraction errors. (Lane B may read them; Lane C calls them; nobody edits their decision logic.)

## Environment

- This VM has **NO GPU and NO torch** (`python3 -c "import torch"` → ModuleNotFoundError). No training runs, no neural runs, no faked scores anywhere. Code that needs torch must guard with a clear error/exit-2 message pointing at the Colab notebook. Pure-Python checks (data loading, audits, rule-based runtime) run here and must be verified here.
- Commit prefix: `R-IMPL:`. Commit per lane as you go. Never push — the parent handles the push after verification.

## Cross-lane contracts

- **C1 — Integrated runtime** (`src/laya_integrated.py`, owned by Lane C): Python `run_question(text, mode="auto", checkpoint=None) -> dict` and CLI `python3 src/laya_integrated.py --mode {classifier,rule-based,auto} [--checkpoint PATH] [--json] "question"`. Output dict keys: `question`, `language`, `extractor` (`"classifier"` | `"rule_based"`), `checkpoint` (path or None), `fallback_reason` (None or str), `issues`, `facts`, `enums`, `sections` (sorted list), `court`, `escalations` (list), `prose` (str or None), `latency_ms`. Exit 0 on success; exit 2 if `--mode classifier` is requested but no checkpoint exists. Rule-based fallback must say so in its output — never fake classifier scores.
- **C2 — Classifier interface** (owned by Lane B): keep `predict_text(model, tokenizer, text, ...)`, `load_checkpoint(path, ...)`, `save_checkpoint(model, config, path)`, `evaluate_checkpoint(...)`, `score_label_predictions(...)` signatures stable (Lane 04 established them). Checkpoint dir layout: `models/<name>/best/model.pt` + `config.json` + `thresholds.json` (thresholds written by the calibration step). Document the layout in the module docstring. Default checkpoint path the runtime looks for: `models/v71-classifier/best/model.pt` (overridable with `--checkpoint`).
- **C3 — Backtest harness** (`tests/integrated_backtest.py`, owned by Lane E): one command `python3 tests/integrated_backtest.py [--mode auto|rule-based|classifier] [--suite all|validation|kaanoon|16q|brutal] --json-out <path>`; imports the integrated runtime (C1), never subprocesses it for scoring; prints per-set exact / micro-P / micro-R / silent + the frozen gate rating; refuses any sealed suite (exit with a message, never loads sealed files). Validation split SHA must be verified before scoring (must equal `7640d067…`).
- **C4 — Colab notebook** (`notebooks/laya_v71_train_backtest.ipynb`, owned by Lane D): runs top to bottom on a free Colab T4 with no manual edits beyond paths; cells: setup (clone repo @ HEAD, pip install), 3-backbone smoke test, Train Run #1 (nested 2k/4k/7.5k, mmBERT-base first), backtest on frozen-500 + Kaanoon-28 + 16-Q + Brutal-230 (do-not-regress bar 210/230; 230/230 is the v7-live aspiration, not the C1 baseline), print exact / micro-P / micro-R / silent per set + frozen gate rating; a `CPU_SMOKE_TEST = True` mode that runs the integrated runtime end to end with the rule-based extractor (verifiable on this VM before any GPU run).
- **C5 — Guardrail after every change**: `python3 tests/test_graph_v4.py` and `python3 tests/test_prose_renderer_v2.py` must PASS; `python3 -m unittest discover -s tests -p "test_*.py"` must stay 66 OK (or grow, never shrink); 16-Q must stay 14/16.

## Lane map

| Lane | Task | Files owned | Status |
|---|---|---|---|
| A | Phase A gates A1–A7 | NEW files only: `scripts/check_graph_contract.py`, `scripts/run_graph_oracle.py`, `scripts/check_clause_supervision.py`, `scripts/smoke_backbones.py`, `scripts/vram_smoke.py`, `docs/impl_phaseA_A*.md` | **done — commits `fa9703b` + `4573615`** (corrections to Lane B state). CORRECTED verdicts from Lane A's report (the row I wrote earlier from the commit message was wrong): **A1 FAIL** (exit 1 — 59 graph-consumed keys, **21 UNCOVERED**; "8 dead keys wired" holds only for the evidence path, 7/8 still dead on the classifier path; reverse-dead: school_fees_fact, procedure, modality_time) · **A2 OPEN** (harness built, GG/GP/PG/PP + tautology check verified; 16-Q GT has NO gold issues/enums, only legacy 8-key facts, so only a degraded GG could run: **9/16** — a missing-input artifact, NOT a graph ceiling; full oracle needs human-annotated gold issues + 28 facts + enums) · **A3 FAIL** (exit 1 — C1: `encode_labels:678–680` broadcasts question-level modality_time to EVERY clause, 637 train + 28 val rows; C2: `third_party` gate column 0 positives in 8,000 records; C3: gate BCE unmasked over padded slots, `train.py:752`; C4: `clause_issue/fact_logits` never enter any loss, only fusion use; 3,289/7,500 train records carry no spans) · **A4 OPEN** (transformers NOT importable on this VM — no fertility numbers were measured here; `--part a` exits 2, code ready for Colab; no predetermined winner, MuRIL is the Kanglish challenger) · **A5 FAIL as a grouped split** (no template_family_id/grammar_rule_id/scenario_family fields; global random shuffle; 136/136 val blocks in train; 500/500 val records share label combos, full label tuples, block signatures, cross-language siblings; 489/500 share ≥1 word 8-gram; frozen split NOT rewritten; a genuinely group-disjoint dev set still needs building — coordinator decision) · **A6 OPEN** (vram_smoke.py exits 2 here, no torch; code ready for Colab; micro-batch 8 is a target, never assumed) · **A7 RECONCILED + 1 open** (category gap resolved from aggregates only: the 2 unaccounted Fresh-20 questions are the birth-cert pair F17/F18, 2/2 exact; Kannada-8 remaining 4 must be 4/4 exact; FN gap OPEN — itemised FNs sum to 27 vs headline 28, one FN unitemised; next report must carry "27 itemised + 1 unitemised"). Lane A's two failed execs are the A1/A3 checkers exiting 1 as designed. |
| B2 | A3 clause-supervision fixes (follow-up to Lane A) | `src/laya_v7_classifier.py`, `scripts/train_v71_classifier.py` (fix only; NEW doc note) | **done — commit `8d1ae57`** (C1 broadcast deleted, gate BCE masked, third_party head dropped, span-anchored clause CE added weight 0.10; original unedited checker exits 0; checker edit reverted in full; 66 tests OK, 16-Q 14/16; residuals: no hypothetical clause gating, no third-party veto, clause loss never executed — needs Colab Run #1) |
| F | Independent verification | NEW `docs/impl_verification_report.md` (runs only) | **done — commit `00d8b9f`** (guardrails PASS, frozen SHAs intact, all lanes verified; A1/A3 verified as FAILING, A2 9/16, A5 failing, A7 verified; Brutal 210/230 + 16-Q rating 7.6 reconciled — see Lane F findings below) |
| B | FALLBACK-2 classifier amendments | `src/laya_v7_classifier.py`, `scripts/train_v71_classifier.py`, `docs/rtx-recall-training-commands.md`, NEW `docs/impl_laneB_classifier_changes.md` | **done — commit `7527258`** (1-pass pooling; weighted-CE baseline / focal challenger; OOF calibration script, Train-7500 only; Colab-first doc; loader verified 7500/500; 66 tests OK) |
| C | Unified integration runtime | NEW `src/laya_integrated.py`, NEW `docs/impl_laneC_runtime.md` | **done — commit `792c75f`** (C1 built, no drift; 16-Q spot-check 14/16, rule-based; 66 tests OK) |
| D | Colab notebook | NEW `notebooks/laya_v71_train_backtest.ipynb`, NEW `docs/impl_laneD_notebook.md` | **done — commit `3216272`** (C4 built; CPU smoke test exit 0; 16-Q spot-check 5/5; see Brutal note below) |
| E | Backtesting harness | NEW `tests/integrated_backtest.py`, NEW `docs/impl_laneE_harness.md` | **done — commit `43a0b4d`** (rule-based verification: validation 261/500, Kaanoon 14/28, 16-Q 14/16, Brutal 210/230 — see discrepancy note; 16-Q rating 9.0 is a provisional upper bound, measured rating 7.6) |

## File-ownership rules (no merge conflicts by construction)

- Lane A writes NEW files only; it audits `src/laya_v7_classifier.py` and `scripts/train_v71_classifier.py` but does NOT edit them (fixes found go to Lane B via this file's §Notes).
- Lane B is the ONLY lane editing `src/laya_v7_classifier.py`, `scripts/train_v71_classifier.py`, `docs/rtx-recall-training-commands.md`.
- Lane C writes NEW files only; it reads `src/laya_v7.py`, `src/laya_v7_extractor.py`, `src/laya_v7_graph.py`, `src/laya_prose_v2.py`, `src/laya_lang_normalizer.py` but does not edit them.
- Lane E writes NEW files only; it imports Lane C's runtime per C1 and Lane 07's `tests/recall_eval.py` scoring (read-only).
- Lane D writes the notebook + its own status doc only.
- Lane F runs tests only; it does not edit code (fixes go back to the owning lane via the coordinator).

## Reading list (all lanes)

- `docs/70-percent-plan.md` (Phases A–F; NOTE: the working-copy plan still carries the pre-amendment Phase B config — micro-batch 1, ASL, max_seq_len 288. The FALLBACK-2 amendments in the re-run file SUPERSEDE it; the parent task spec states the amended config. Do not "fix" the plan file silently — Lane B notes the supersession in its change doc.)
- `workspace/goals/english-family-law-chatbot-retest/files/laya-graph/gemini-recall-consultation-rerun.md` (FALLBACK-2: 1-pass span pooling, focal CE, graph-aware calibration, MuRIL smoke test)
- `workspace/goals/english-family-law-chatbot-retest/files/laya-graph/chatgpt-recall-consultation-rerun.md` (GPT-6.2 re-run: fact binding P0, oracle replay, gate 80% stays, "no need to wait for Neon")
- `workspace/goals/english-family-law-chatbot-retest/files/laya-graph/gemini-recall-consultation.md`, `chatgpt-recall-consultation.md` (first consultations + adopted synthesis)
- `docs/recall_status.md` (final numbers + open items)
- `docs/recall_swarm_state/lane-04-classifier.md` (Lane 04 training prep + RTX commands; NOTE: old-corpus-pinned 5,000, ModernBERT default — Lane B updates it for 8,000 + mmBERT + Colab)

## GPT-RERUN corrections (2026-11-27 21:46–21:52 IST, ChatGPT GPT-6.2 verified, thinking max) — OVERRIDE the fallback's claims where they conflict

Filed at `workspace/goals/english-family-law-chatbot-retest/files/laya-graph/chatgpt-recall-consultation-rerun.md`. These corrections are binding on Lanes A/B:

1. **1-pass span pooling adopted, but the VRAM claim is overstated** — 8.1× padded tokens, not proven VRAM; micro-batch 8 is a TARGET, not guaranteed. Lane A A6 must verify it fits; Lane B's training script must fail loudly on OOM and suggest the fallback, never silently change batch size.
2. **ASL→multiclass fix adopted, but weighted CE is the BASELINE and focal CE the CHALLENGER** (reject 3-binary-logits; unknown stays a semantic state). Lane B implements `--loss {weighted_ce,focal_ce}`, default `weighted_ce`.
3. **Graph-aware calibration adopted WITH corrections** — OOF on Train-7500 ONLY (never Val-500 — the frozen split must stay untouched by calibration); κ=150 is an unproven hyperparameter (compare 50/150/300, separate priors); up to 3 coordinate passes.
4. **3-backbone benchmark adopted** (mmBERT vs MuRIL vs XLM-R base) — mmBERT is NOT the predetermined winner; MuRIL is a serious Kanglish challenger. Lane A A4 treats all three as equals.
5. **75/70 gate relaxation REJECTED — 80% per language stays** (Wilson: 80/100 → lower bound 71.1% vs 70/100 → 60.4%). GATE DISAGREEMENT RESOLVED.
6. **New P0 items: fact binding** (subject/event/polarity/time/span in evidence) **and oracle replay with the tautology warning.** Lane B implements minimal fact binding from existing spans; Lane A A2's oracle harness must detect/report tautological gold labels.
7. **Ceiling ranges widened:** first trained classifier 50–68% unseen, post-expansion 60–78% (planning ranges, not forecasts).
8. **Phase C allocation redistributed** (residence 1,100; joint/stridhan 850; custody 750; divorce 600; dense multi-issue 550; scope/negation 500; maintenance 400; total still ~4,750).
9. **Back-translation negation-corruption claim UNVERIFIED.**
10. **"You do not need to wait for Neon"** — the 00:15 Neon retry is a completeness check, not a blocker.

## Notes (coordinator → lanes)

- **⚠️ Brutal-230 discrepancy (found by Lane D, 2026-11-27; RECONCILED by Lane F, commit `00d8b9f`):** the task spec says Brutal-230 "must stay 230/230", but measured through the C1 integrated runtime + C3 harness the rule-based reference is **210/230 (91.3%, micro-P/R 0.9974/0.9205, silent 15)** — confirmed by the harness's own baselines block (pre-recall-swarm reference 215/230, current-code reference 210/230, measured 210/230 = MATCH). Lane F confirmed it independently through the frozen scorer (`tests/v7_backtest.py --suite brutal --mode evidence`): identical aggregates (382/1/33, court 215/230, esc 213/230, silent 15, C13 1/16) and the same miss IDs. The 230/230 figure was **never an evidence-mode number**: `results/live-laya-v7-results.md:45–46` records evidence/CPU at 215/230 and neural `laya`/CUDA at 230/230. The notebook gate is therefore **do not regress below 210/230**, with 230/230 as aspiration. The 215→210 regression holds **as a measurement** (−5 exact, all English: B-024, B-027, B-075, B-086, B-127; C13 unchanged). **Causation is UNPROVEN** — Lane 03 anchor hardening / Lane 08 route fixes are suspects only; confirming it needs a bisect over recall-swarm commits, which no lane ran (coordinator/parent decision). Do not report a classifier Brutal number against the 230/230 bar.
- **16-Q rating (reconciled by Lane F):** the honest number is **7.6**. Both scorers agree on the components (raw 9.1 from E=0.875, Rm=0.9786, Pm=1.0, C=0.8125, S=1.0); the frozen scorer subtracts 0.5×Fb = 1.5 for the measured Fb=3 (statutory_prerequisite_gate), giving 7.6. The harness reports 9.0 only because Fb is unmeasurable through the C1 output (no pre-gate candidates/dispositions). Quote 7.6, never 9.0 unqualified. Coordinator fix applied: the harness now prints the qualifier on the gate-rating line and the baseline-delta line (verified: 16-Q re-run 14/16, self-test PASS).

## Lane F verification findings (2026-11-27, report `docs/impl_verification_report.md`, commit `00d8b9f`)

- Guardrails VERIFIED (graph v4 PASS, prose PASS, 66 tests OK); frozen SHAs VERIFIED (all 9 paths vs `90e20c5`, validation `7640d067…`, 7/7 intact); Lane C/D/E/B all VERIFIED; A1 VERIFIED AS FAILING (exit 1, 21 uncovered); A3 VERIFIED AS FAILING (both violation sites confirmed in committed code; fix sized in report §6b); A2 VERIFIED (degraded GG 9/16, misses K0/H2/H4/H5/H6/H7/H14); A5 VERIFIED AS FAILING (`dev_grouped.jsonl` does NOT exist); A4/A6 VERIFIED AS OPEN (both exit 2, no torch); A7 VERIFIED (7/20, 38/5/28 arithmetic checks out; birth-cert 2/2 resolves the category gap; FN 27-vs-28 stays open); git hygiene VERIFIED (no frozen file touched, no cross-lane code commits).
- **Lane D's two failed execs:** NOT verifiable from the repo — no trace in any Lane D file or the shared state, and nothing in Lane D's deliverables depends on a failed command (CPU smoke exits 0, verified; GPU cells are gated/SKIP). Not a blocker.
- **Fix list — pre-push:** (1) A3 fixes — Lane B2 running; Train Run #1 must not start until C1+C4 are decided. (2) Harness 16-Q rating qualifier — DONE by coordinator (this commit). (3) Sweep for "Brutal must stay 230/230" — DONE by coordinator (notebook line 434 + this state file + baselines line; the push manifest must use the 210/230 C1 baseline).
- **Fix list — before Colab GPU run:** (4) Lane C expose `candidates_before_gate`/`gated_out` so Fb becomes measurable — OPEN (post-B2 follow-up). (5) Stale "stand-in assess call" label in the harness Brutal method note — DONE by coordinator (this commit, F-5). (6) Build `dev_grouped.jsonl` — OPEN (coordinator decision, new file, never replaces validation). (7) A1 schema decision 28→36 facts — OPEN (human/coordinator). (8) A2 human annotation gate — OPEN.
- **Human only:** (9) Brutal-regression bisect decision. (10) Phase D 300-item holdout + Phase E sealed re-run. **Can wait:** A4/A6 Colab runs, Lane B's filed open items (full fact binding, LoRA, grids).
- Note: `git status` at Lane F's commit time showed `M src/laya_v7_classifier.py` — Lane B2 had already started editing the classifier. Lane F's A3 findings are against the pre-B2 code; B2's changes need a re-run of `check_clause_supervision.py` to exit 0 (already in B2's brief).
- A2's independent annotation is a HUMAN gate: build the harness, run it on whatever independently-annotated data already exists (check whether `ground-truth-v2-hma27-A.json` carries gold issues/facts for the 16-Q — if yes, the oracle can smoke-test on those 16 with the caveat recorded), and flag the full independent dev set as OPEN. Never generate gold labels from Graph v4 itself (circular).
- A7 uses aggregates only (from `results/live-laya-v7-results.md` + `docs/recall_status.md` §11). Sealed text is never opened.
- Lane B: fact binding (ChatGPT re-run P0 — subject/event/polarity/time/span in evidence) is a design item. Implement the minimal version the existing corpus spans already support (spans carry text/key/kind/offsets); if a clean implementation needs a schema change, file the design in your change doc and flag it — do not hack the schema.
- The user ruled Colab ONLY for computing/testing/code. The RTX doc update (Lane B) must lead with Colab T4 commands; RTX 5050 stays as the equivalent local path, not a comparison.

## Lane A findings for Lane B (2026-11-27, Phase A gates A1–A7)

Full evidence: `docs/impl_phaseA_A1_graph_contract.md` … `docs/impl_phaseA_A7_brief_reconciliation.md`.
Per-gate verdicts: **A1 FAIL** (21 uncovered graph keys, exit 1) · **A2 OPEN**
(harness built; degraded oracle 9/16; full oracle needs human gold inputs) ·
**A3 FAIL** (1 question-labels-to-all-clauses site, exit 1) · **A4 OPEN**
(code ready, run on Colab; no numbers) · **A5 FAIL as a grouped split**
(random row-level shuffle; limitation recorded, frozen split untouched) ·
**A6 OPEN** (code ready, run on Colab; no numbers) · **A7 RECONCILED**
(birth-cert 2/2 explains the 2 missing exacts; 1 FN still unitemised).

Lane B must fix (coordinator decision where noted):

1. **A1 — 21 uncovered graph keys** (`scripts/check_graph_contract.py`,
   exit 1). 7 of the 8 "dead keys" are still dead on the classifier path
   (only `interim_asked` is a FACT); the evidence path wiring does not
   count for the classifier. Also uncovered: post-order split facts
   (`arrears_recovery_asked`, `maintenance_variation_asked`), the five
   `*_negated` facts, `interim_only_asked` (known 2-FN artifact),
   `urgent_safety_risk`, `money_fact_child_or_parallel`,
   `stay_in_house_under_eviction_pressure`, `stridhan_held_by_inlaws_refused`,
   `stridhan_safe_in_own_possession`, `stridhan_abandoned_or_undisputed`,
   `hypothetical_or_joint_prop_fact_only`, `interim_unpaid_with_joint_or_parallel`,
   `post_decree_lump_sum_enforcement`, `first_demand_never_made`,
   `forum_question_asked`, `procedure_how_to_asked`, `no_dispute_empty`.
   Schema extension (28→36 facts) is a coordinator decision; derivations
   for `interim_only_asked` / `money_fact_child_or_parallel` belong in
   the Stage 1→2 adapter, NOT the frozen graph. Reverse-dead heads to
   decide on: `school_fees_fact`, `procedure`, `modality_time`.
2. **A3 — clause supervision** (`scripts/check_clause_supervision.py`,
   exit 1). (a) Remove the all-clause hypothetical broadcast in
   `src/laya_v7_classifier.py::encode_labels` 678–680. (b) `third_party`
   gate column has 0 positive rows in all 8,000 records — add span
   labels or drop the column. (c) Mask the gate BCE in
   `scripts/train_v71_classifier.py:752` to real clause counts (span
   loss :757–760 already is). (d) `clause_issue_logits` /
   `clause_fact_logits` never enter any loss (train.py:745–747 use
   full logits only) yet fusion max-pools over them (train.py:694–695,
   classifier.py:1114–1116) — define the clause-supervision source
   (spans or MIL) for the 1-pass architecture before Run #1.
3. **A4 — backbones:** LANDED by Lane B before this audit ran
   (default `jhu-clsp/mmBERT-base`, all three backbones in
   `--backbone` choices + `BACKBONES`, licences verified from HF
   cards in code, 1-pass pooling default, `--loss
   {weighted_ce,focal_ce}` default `weighted_ce`, `max_seq_len`
   320). `scripts/smoke_backbones.py --part b` is unblocked on the
   backbone side — only the GPU run remains. NOTE: the default was
   swapped before the benchmark names a winner; if MuRIL or XLM-R
   wins, the default must change to match.
4. **A5 — grouped split:** no `template_family_id` exists; the frozen
   split is a random shuffle (`build_synthetic_corpus.py::generate`
   ~1892–1900), 500/500 validation records share label combos and
   block signatures with train. OOF calibration must use grouped
   (block-signature) folds on Train-7500 only, never Val-500. A new
   group-disjoint dev file is still to be built (coordinator).
5. **A6 — VRAM:** `scripts/vram_smoke.py` sweeps micro-batch 1/2/4/8
   on Colab; if 8 OOMs, fail loudly and suggest the fallback — never
   silently shrink the batch. Peak < 6.5 GB target.
6. **A2 — oracle:** `scripts/run_graph_oracle.py` is ready; it needs
   independently annotated gold issues + 28 facts + enums (human
   gate) before GG/GP/PG/PP can run. Never derive gold from Graph v4
   (harness exits 3 on tautological provenance).
7. **A7 — reporting:** next evaluation report uses Fresh-20 7/20 with
   birth-cert 2/2 in the category table, and carries the FN list as
   "27 itemised + 1 unitemised (section unknown)".
