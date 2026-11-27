# PUSH MANIFEST — LAYA v7.1 implementation + integration swarm

**Base:** `90e20c5` (recall swarm merged; already on GitHub main, 43 commits).
**Head:** `8d1ae57` + coordinator close-out commits (see git log; final HEAD recorded below at commit time).
**Working copy:** `~/workspace/laya-v71-work`. **Nothing pushed yet** — the parent handles the push after verification.
**Scope:** 14 commits, 27 files changed (+8,052/−292 vs base), plus this manifest = **28 files to push**.

## Honest numbers this push carries (do not re-claim)

- Frozen validation split: **261/500 = 52.2%** (rule-based evidence mode). Kaanoon-28: **14/28 = 50.0%**. 16-Q: **14/16**, measured rating **7.6** (the harness prints 9.0 only as a provisional upper bound — Fb unmeasured via C1; the qualifier is printed on the rating line).
- Brutal-230 via the C1 runtime + C3 harness (rule-based): **210/230 = 91.3%** — the do-not-regress bar. **230/230 is the v7 live neural/CUDA number, never an evidence-mode number** (evidence/CPU was 215/230). The 215→210 regression (−5 exact, all English) holds as a measurement; causation is unproven (bisect not run).
- **No claim of ≥70% until a real sealed re-run measures it.** No training or neural run happened on this VM (no GPU/torch); every number above is a CPU/rule-based re-run or a code-only deliverable.

## Files (vs base 90e20c5)

### New code (4)
- `src/laya_integrated.py` — C1 unified runtime (Lane C, 792c75f)
- `tests/integrated_backtest.py` — C3 backtest harness (Lane E, 43a0b4d; coordinator qualifier/F-5 fixes, 37cc835)
- `notebooks/laya_v71_train_backtest.ipynb` — C4 Colab notebook, T4, CPU smoke-test mode (Lane D, 3216272; coordinator Brutal gate-language fix, 37cc835)
- `scripts/calibrate_thresholds.py` — graph-aware OOF calibration, Train-7500 only (Lane B, 7527258)

### Modified code (2)
- `src/laya_v7_classifier.py` — FALLBACK-2 amendments (Lane B, 7527258) + A3 clause-supervision fixes (Lane B2, 8d1ae57)
- `scripts/train_v71_classifier.py` — same two lanes

### New Phase A gate scripts (5)
- `scripts/check_graph_contract.py`, `scripts/run_graph_oracle.py`, `scripts/check_clause_supervision.py`, `scripts/smoke_backbones.py`, `scripts/vram_smoke.py` (Lane A, fa9703b + 4573615)

### New docs (14)
- `docs/impl_swarm_state.md` — shared state (coordinator, updated throughout)
- `docs/impl_phaseA_A1_graph_contract.md` … `docs/impl_phaseA_A7_brief_reconciliation.md` (7 files, Lane A)
- `docs/impl_laneB_classifier_changes.md` (Lane B)
- `docs/impl_laneB2_clause_fixes.md` (Lane B2)
- `docs/impl_laneC_runtime.md` (Lane C)
- `docs/impl_laneD_notebook.md` (Lane D)
- `docs/impl_laneE_harness.md` (Lane E)
- `docs/impl_verification_report.md` (Lane F, 00d8b9f)

### Modified docs (2)
- `docs/rtx-recall-training-commands.md` — rewritten Colab T4 FIRST (Lane B)
- `docs/recall_swarm_state/lane-04-classifier.md` — Lane B amendments folded in

### This manifest (1)
- `PUSH-MANIFEST-IMPL.md`

## Frozen files — untouched (verified by Lane F, 00d8b9f)

`graph/laya-crpc-bns-section-decision-tree-v2.json`, `graph/laya-crpc-bns-section-decision-tree-v3.json`, `ground-truth/ground-truth-v2-hma27-A.json`, `test-bank/brutal-bank-v1-frozen.json`, `test-bank/sealed/sealed-fresh-20.json`, `test-bank/sealed/sealed-kannada-8.json`, `notebooks/live-laya-colab-test-v6-brutal.ipynb`, `tests/test_graph_v4.py`, `tests/test_prose_renderer_v2.py` — no diff vs base; 7/7 frozen SHAs intact; validation sha256 `7640d067…` unchanged. Sealed text was never opened.

## Known open items carried by this push (not hidden)

1. **A1 FAIL (exit 1):** 21 graph-consumed keys uncovered on the classifier path — schema decision (28→36 facts or adapter derivations) still owed; coordinator/parent call.
2. **A2 OPEN:** full graph oracle needs human-annotated gold issues + 28 facts + enums; degraded GG on the 16-Q is 9/16 (missing-input artifact, not a graph ceiling).
3. **A3 FIXED, with residuals:** `check_clause_supervision.py` exits 0 on the original unedited checker. No hypothetical clause gating and no third-party veto exist in the model (both need span labels / schema change). The new span-anchored clause loss (weight 0.10) has never executed — Colab Run #1 must confirm it decreases. The checker's printed C2 VACUOUS lines are stale wording (placeholder label columns, no trained head) — wording only, exit code unaffected.
4. **A4/A6 OPEN:** backbone tokenizer audit + VRAM smoke test are code-only; they must run on Colab T4 (no transformers/torch on this VM).
5. **A5 FAIL:** grouped-split claim is false (500/500 val records share families with train); no group-disjoint dev set was built — coordinator decision, new file, never replaces validation.
6. **A7:** category gap reconciled (birth-cert pair F17/F18, 2/2 exact); FN 27-vs-28 stays open — next report must carry "27 itemised + 1 unitemised".
7. **Fb unmeasurable via C1:** Lane C does not yet expose `candidates_before_gate`/`gated_out` — the 16-Q 9.0 is an upper bound; measured rating is 7.6. Exposing the pre-gate data is a post-push follow-up.
8. **Brutal 215→210 regression:** measurement confirmed, causation unproven — bisect over recall-swarm commits not run (parent decision).
9. **Neon re-run:** genuine Neon answer still owed; one-time cron `neon-retry-after-reset` fires 2026-11-28 00:15 IST. Per the ChatGPT re-run, "you do not need to wait for Neon" — completeness check, not a blocker.

## What still needs the Colab GPU run (after this push lands)

See `notebooks/laya_v71_train_backtest.ipynb` (top-to-bottom, T4) and `docs/rtx-recall-training-commands.md`. Order: (1) 3-backbone smoke benchmark (mmBERT vs MuRIL vs XLM-R, stratified en/kn/kanglish — no predetermined winner); (2) `scripts/vram_smoke.py` micro-batch sweep (micro-batch 8 is a target, fail loudly on OOM, never silently shrink); (3) Train Run #1 nested curve 2,000 → 4,000 → 7,500 (mmBERT-base first, `--loss weighted_ce`, 1-pass pooling, max_seq_len 320, bf16, micro-batch 8 / grad-accum 2, max 4 epochs, lr 2e-5 / 1e-4 heads, cosine + 10% warmup, wd 0.01) + focal-CE challenger comparison; (4) 5-fold grouped OOF on Train-7500 only + `scripts/calibrate_thresholds.py` (κ ∈ {50,150,300}); (5) classifier-mode backtest (`--mode classifier --suite all` + rule-based comparison; Brutal bar is do-not-regress below 210/230). **No sealed re-run cell exists in the notebook** — Phase E sealed re-run happens only after the Phase D 300-item human-written holdout gates pass (≥80% exact per language).

## Verification on this VM (final, coordinator re-run 2026-11-27 ~22:25 IST)

- Full unit suite: **66 tests OK**. `test_graph_v4.py` PASS (7/7 frozen hashes intact). `test_prose_renderer_v2.py` PASS (246 cases, Fp=0, 15/15 mutants).
- `scripts/check_clause_supervision.py`: **exit 0** (original unedited checker). `scripts/check_graph_contract.py`: **exit 1** (A1 FAIL, as designed).
- 16-Q rule-based harness: **14/16** (micro-P 1.0 / micro-R 0.9623, silent 0, misses H6/H14), qualifier line prints. Harness `--self-test` PASS.
- Notebook JSON + nbformat valid. Working tree clean.
