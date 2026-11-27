# Lane B — FALLBACK-2 Classifier Amendments (with GPT-RERUN corrections)

- Lane: B (implementation swarm; coordinator: parent agent's implementation coordinator)
- Date: 2026-11-27
- Files owned (only these touched + one NEW script + this doc):
  `src/laya_v7_classifier.py`, `scripts/train_v71_classifier.py`,
  `docs/rtx-recall-training-commands.md`, NEW `scripts/calibrate_thresholds.py`,
  NEW this file. Amendment note added to
  `docs/recall_swarm_state/lane-04-classifier.md` (top — Lane 04's record
  itself untouched below that note).
- Status: CODE ONLY — no training/neural run anywhere (this VM has no GPU
  and no torch). Everything torch-dependent is guarded; the Colab T4 run
  is still owed. No frozen files touched; no sealed files opened.
- Supersession note: `docs/70-percent-plan.md` §3 (Phase B) still carries
  the PRE-amendment config (micro-batch 1, ASL, max_seq_len 288, OOF on
  all 8,000, κ=150 fixed). The FALLBACK-2 + GPT-RERUN amendments in this
  doc SUPERSEDE it. The plan file was NOT silently edited (per task spec).

## 0. Corpus the work is against (verified on this VM)

`data/synthetic_v7_1/train.jsonl` = **7,500** records,
`data/synthetic_v7_1/validation.jsonl` = **500** records (sha256
`7640d067c28abf539131dbcc891e4bdffedf62bbef4a7d66c1659bb96d07e58e` —
matches the frozen split in `docs/impl_swarm_state.md`). Lane 02's 8,000
expansion already landed; Lane 04's doc was pinned to the old 5,000.
Languages (train): EN 3,573 / KN 1,931 / `kn_roman` (Kanglish) 1,996.
Validation: EN 235 / KN 153 / `kn_roman` 112. Spans: 5,829 train / 401 val.

## 1. 1-pass contextual span pooling (FALLBACK-2 item 1)

- `ClassifierConfig.pooling`: `"one_pass"` (default) | `"nine_pass"`.
- One-pass: the full question is encoded ONCE (`max_seq_len` 320, bf16);
  clause vectors come from `span_pool_clauses()` — token-span attention
  pooling over the contextualised token embeddings inside each clause's
  char offsets, via `clause_token_spans()` on the tokenizer offset
  mapping. Same `span_attn` scorer as the full-question pooling, softmax
  restricted to the clause span; empty spans fall back to [CLS]; padded
  slots return zero vectors (masked by `clause_counts`).
- Nine-pass: the old Lane 03/04 path (full + each clause encoded
  separately) kept behind `pooling="nine_pass"` for auditability only.
  `scripts/train_v71_classifier.py --pooling nine_pass` selects it.
- `predict_text()` tokenizes once in one-pass mode (no clause batch);
  the nine-pass branch keeps the old clause tokenization.
- **VRAM CLAIM — UNVERIFIED (GPT-RERUN, binding):** 1-pass cuts MAXIMUM
  PADDED TOKEN positions ~8.1× (9×288/320 at max padding), NOT a proven
  ~8× VRAM saving. Parameter weights and optimizer states are not
  replicated 9×, and dynamic padding changes the real token ratio. This
  is stated in the module docstring, the training-script docstring, and
  the OOM error message. Micro-batch 8 is a TARGET, not a guaranteed fit
  (Lane A A6 verifies it fits; the training script fails loudly on OOM).

## 2. Loss — ASL REPLACED (FALLBACK-2 item 2, GPT-RERUN claim 2)

### Why ASL was wrong
Asymmetric Loss is a binary multi-label loss: independent sigmoids per
state, no mutual exclusivity. Each issue/fact head has 4 MUTUALLY
EXCLUSIVE states (e.g. a fact cannot be both supported and denied;
contradictory evidence is the `conflicting` state). Binary ASL across 4
states allows simultaneous supported=0.8 AND denied=0.8 — an invalid
state combination the graph can never interpret. Meanwhile plain softmax
CE lets the ~85% `unknown` majority crush rare positives (restitution:
118/7,500).

### What replaced it
- **BASELINE (default): weighted cross-entropy** over the 4 states per
  head — `--loss weighted_ce` (default), `ClassifierConfig.loss`.
- **CHALLENGER: class-balanced focal CE** — `--loss focal_ce`
  (`focal_ce_loss()` in the training script; γ grid {0, 1, 2},
  default γ=2.0). Select focal ONLY if it improves grouped OOF over
  weighted CE without materially degrading rare-state precision.
- **REJECTED: the 3-binary-logits variant** (unknown = all below
  threshold). It conflates "the question does not establish a fact" with
  "the classifier is uncertain". Unknown stays a semantic state; track
  uncertainty separately.
- Class weights: effective-number weighting (Cui et al.),
  `effective_number_weights()` in the classifier module (pure python):
  w = (1−β)/(1−β^n), β=0.999 (grid {0.99, 0.999}), unknown w₀=0.25
  (grid {0.25, 0.5, 1.0}) relative to mean active-state weight, capped
  at 8× (grid {4×, 8×}), renormalised to mean 1.0. This REPLACES Lane
  04's inverse-frequency weights (clipped [0.25, 4.0]) — the
  `--class-weights` flag now means effective-number weights. Sanity
  check on this VM: counts [2255, 300, 4000, 118] →
  weights [0.296, 1.021, 0.308, 2.376] (rare state ~8× the frequent
  active state; unknown held at ~0.25× mean active). β / w₀ / cap are
  search grids, NOT established optima (GPT-RERUN).
- **History note (auditable, not rewritten):** ASL never reached code.
  It existed only in `docs/70-percent-plan.md` §3 ("Asymmetric Loss
  (ASL: γ−=2, γ+=0, margin clip m=0.05) or class-weighted focal...").
  There was no ASL implementation in `src/laya_v7_classifier.py` or
  `scripts/train_v71_classifier.py` to preserve — the old loss in code
  was plain cross-entropy. The removal is therefore a plan-level
  correction, recorded here, not a silent rewrite. No ASL code path
  remains anywhere in the repo (verified by grep: no "asymmetric" in
  src/ or scripts/ outside this doc's explanation).

## 3. Graph-aware OOF threshold calibration (FALLBACK-2 item 3)

New script: `scripts/calibrate_thresholds.py` (pure python, no torch;
the cleaner option vs. embedding it in the training script — calibration
is a separate step with different inputs (OOF probs) and a different
guard (refuse Val-500), and it must be runnable without a GPU).

- **OOF on Train-7500 ONLY (never Val-500).** Guards: sha256 of
  `--train-file` is refused if it equals the frozen validation hash
  `7640d067…`, and any filename containing "validation" is refused
  (verified on this VM: exit 2 with the refusal message). The OOF dump
  must cover exactly the 7,500 training records (same count, same id
  set) or the script errors.
- **How the OOF dump is produced:** `--eval-checkpoint` + `--val-file
  data/synthetic_v7_1/train.jsonl` + `--dump-predictions <path>` (new
  flag in the training script; writes per-record gold + full prob
  vectors as JSONL). The 5-fold grouped OOF itself (5 training runs,
  one per fold) is still to be run on Colab — this script consumes its
  output; it does not train the folds.
- **Order:** temperature scaling FIRST (per family, grid T in
  {0.5, 0.75, 1.0, 1.25, 1.5, 2.0} on OOF NLL) → global τ₀ per family
  (grid 0.25–0.65 on OOF Stage 2 exact) → per-head τ_h maximising F1.2
  for the active state (requested / supported) → EB shrinkage
  τ_h = [N+/(N+ + κ)]·τ_h^OOF + [κ/(N+ + κ)]·τ₀ with SEPARATE priors
  (τ₀_issue, τ₀_fact) → up to 3 coordinate passes (±0.05 per head, then
  PAIRED ±0.05 moves on coupled (issue, fact) pairs:
  residence/coercive_eviction_or_lockout, divorce/divorce_asked,
  custody/custody_claim, joint_property/joint_property_claim,
  stridhan/stridhan_claim) subject to micro-P ≥ floor (default 0.91).
- **κ is compared in {50, 150, 300} on OOF Stage 2 exact** (tie-breaks
  to 150); κ=150 is an unproven hyperparameter, NOT hard-coded.
- **Pareto:** thresholds.json records where the final point sits
  relative to floors 0.88 / 0.90 / 0.91 / 0.93 / 0.95 (pass/fail per
  floor). It is NOT a re-optimisation under each floor — a per-floor
  re-optimisation is a possible follow-up, flagged here.
- **Output:** thresholds.json next to the checkpoint (contract C2:
  `models/<name>/best/thresholds.json`), with temperatures, τ₀s,
  per-head τs, selected κ + all compared κ results, OOF exact/micro-P/R,
  Pareto table, train-file sha, and `val_500_untouched: true`. The
  runtime applies it at decode time via
  `decode_with_thresholds()` (argmax, neutral fallback if argmax prob <
  threshold); `predict_text()` itself still returns argmax + full probs.
- **Verified on this VM** (synthetic OOF dump, gold-derived probs,
  `--limit 200`, dummy checkpoint dir): full pipeline runs in ~8 s,
  temperature/τ₀/κ/coordinate passes execute, thresholds.json written,
  fast-path Stage 2 scoring agrees with the harness cross-check, and
  the Val-500 refusal fires (exit 2). Stage 2 scoring itself timed at
  ~0.03 s / 500 records (~1 s per full 7,500 scoring), so a full
  calibration is minutes on CPU, not hours.

## 4. Config (FALLBACK-2 Phase B)

| Setting | New value | Was (Lane 04 / plan §3) |
|---|---|---|
| Epochs | **max 4** (refused if >4) | 5 |
| LR | 2e-5 encoder / **1e-4 heads** (separate param groups; `--lr` / `--head-lr`) | 2e-5 single |
| Schedule | cosine, 10% warmup, wd 0.01 | same |
| Micro-batch / grad-accum | **8 / 2** (effective 16) | 4 / 2 (effective 8) |
| Precision | **bf16** (`--bf16`; `--fp16` legacy) | fp16 |
| max_seq_len | **320** | 192 |
| max_clauses | 8 | 8 |
| Loss | weighted CE baseline / focal CE challenger | plain CE (+ ASL in plan) |
| Backbone | mmBERT-base default (see §5) | ModernBERT-large |

- **OOM rule (GPT-RERUN):** micro-batch 8 is a TARGET. On
  `torch.cuda.OutOfMemoryError` the training/eval loop FAILS (exit 2)
  with a message suggesting `--batch-size 4 --grad-accum 4` (same
  effective batch 16), then `--freeze-backbone`, then `--lora`. The
  batch size is NEVER silently changed.
- `--train-subset N` added for the nested learning curve (2000 / 4000 /
  7500) — see the RTX/Colab doc §3.
- `--pooling {one_pass,nine_pass}` added (default one_pass).

## 5. Backbone (FALLBACK-2 item 4, GPT-RERUN claim 4)

`--backbone` choice among:
- `jhu-clsp/mmBERT-base` (MIT) — **default, primary candidate**
- `google/muril-base-cased` (Apache-2.0) — serious Kanglish challenger
- `FacebookAI/xlm-roberta-base` (MIT)

**No predetermined winner** — the A4 smoke benchmark decides (Lane A).
mmBERT-base is ~307M params (~197M embedding).

Licence check (Lane B, 2026-11-27, recorded here):
- mmBERT MIT — HF model card `jhu-clsp/mmBERT-base` ("license: mit");
  corroborated by a second source (litert-community mmBERT-MIT.txt).
- MuRIL Apache-2.0 — HF card metadata `google/muril-base-cased`
  ("license: apache-2.0").
- XLM-R MIT — HF card `FacebookAI/xlm-roberta-base`; corroborated by
  GPT-RERUN §7, which verified all three from the published model cards.
- Re-verify on the card before any training run if the checkpoint
  revision changes.
- SUPERSEDED (documented, not silently dropped): Lane 04's
  `answerdotai/ModernBERT-large` (Apache-2.0) and
  `microsoft/deberta-v3-large` (MIT) are no longer accepted backbones;
  `build_model()` refuses them. `PIXMELT/laya` stays refused (no
  verified permissive licence).
- LoRA target modules updated for the new backbones: mmBERT → `Wqkv`
  (ModernBERT-style fused QKV); MuRIL / XLM-R → `query`, `key`, `value`.

## 6. Fact binding (GPT-RERUN P0) — minimal version + OPEN design

Implemented: `bind_evidence()` in `src/laya_v7_classifier.py` (pure
python). Each corpus span already carries text/key/kind/offsets; the
function attaches `binding` = {subject (claimant_role + claimant_sex
from the record's enums), event (the span's key), polarity (fact state /
issue intent mapped to asserted / negated / unknown / conflicting),
time (modality_time), span {start, end, text}}. `predict_text()` spans
carry the same binding (subject/time from the predicted enums; event
None / polarity "unknown" for attention spans, which carry no key —
they are evidence pointers, not bound facts, and must not be presented
as bound facts).

**OPEN — full binding needs a schema change (do NOT hack the schema):**
when two proceedings, demands or properties co-occur in one question
(e.g. a past proceeding AND a current one, or one person's demand
alongside another person's property), the corpus cannot say WHICH span
belongs to WHICH event/claimant. Spans carry one key and no subject or
event id; enums carry one claimant role/sex per record. Resolving that
needs a span-level `subject` + `event_id` field in the schema (e.g.
`spans[].subject` ∈ {claimant, spouse, parent, child, other, unknown}
and `spans[].event_id` grouping spans that refer to the same proceeding/
demand/property, plus an `events[]` table on the record when a question
contains >1 event of the same type). That is a Lane 02 schema decision
with corpus regeneration — filed here, not implemented. The minimal
version above is what the existing spans support, and it is the correct
scope for this lane.

## 7. Training-commands doc (Colab T4 FIRST)

`docs/rtx-recall-training-commands.md` rewritten for the 8,000 corpus
(7,500 train / 500 validation) + the new config:
- **Colab T4 FIRST** throughout (user rule: Google Colab ONLY for
  computing/testing/code). RTX 5050 stays as the equivalent local path,
  not a comparison. No Colab-vs-RTX comparison anywhere.
- `--check-data-only` expectations updated: `OK: train=7500 val=500`
  (verified on this VM — see §9 below).
- Nested 2k/4k/7.5k learning-curve commands added (`--train-subset`).
- New sections: 3-backbone smoke benchmark commands, OOF dump +
  calibration step (§5), thresholds.json in the checkpoint layout.
- Old 5,000-corpus numbers (4,500 train, EN 2088 / KN 1180 / Kanglish
  1232) replaced with the measured 8,000 numbers (§0 above).

## 8. Signatures kept stable (contract C2)

`predict_text(model, tokenizer, text, ...)`,
`load_checkpoint(path, ...)`, `save_checkpoint(model, config, path)`,
`evaluate_checkpoint(...)`, `score_label_predictions(...)` — all
unchanged in signature. Additive only:
- `predict_text()` now also returns `probs` on facts and enums (issues
  already had them) and a `pooling` field; spans gain `binding`.
- `save_checkpoint()` now also writes `config.json` next to `model.pt`
  (every checkpoint self-describing, whichever caller saved it).
- Checkpoint dir layout documented in the module docstring:
  `models/<name>/best/model.pt` + `config.json` + `thresholds.json`
  (+ `label_maps.json`, written by training).
- New pure-python helpers (no torch needed):
  `clause_token_spans()`, `effective_number_weights()`,
  `bind_evidence()`, `decode_with_thresholds()`.

## 9. Verification on this VM (exact outputs)

```bash
python3 scripts/train_v71_classifier.py \
    --train-file data/synthetic_v7_1/train.jsonl \
    --val-file data/synthetic_v7_1/validation.jsonl --check-data-only
# OK: train=7500 val=500 (torch NOT needed for this mode).
# Loader report: n_ok 7500 / 500, n_skipped 0 / 0,
#   unknown_issue_keys {} / unknown_fact_keys {} / unknown_enum_values {}
#   on both splits. Train langs EN 3573 / KN 1931 / kn_roman 1996;
#   validation EN 235 / KN 153 / kn_roman 112. Spans 5829 / 401.

python3 -m py_compile src/laya_v7_classifier.py \
    scripts/train_v71_classifier.py scripts/calibrate_thresholds.py
# (no output = OK)

python3 tests/test_graph_v4.py
# GRAPH V4 + FROZEN SHA TEST PASS: 34 sections / 66 nodes / 99 edges,
# 0 dangling edges, 7/7 frozen hashes intact.
python3 tests/test_prose_renderer_v2.py
# PROSE VALIDATION PASS: 246 cases, Fp=0, quality_flags=0,
# 15/15 adversarial mutants caught, mean=0.02ms, max=0.28ms
python3 -m unittest discover -s tests -p "test_*.py"
# (66 tests OK — see report; full output in the coordinator handoff)

# Calibration smoke (synthetic OOF, --limit 200, dummy checkpoint dir):
#   temperature issue T=0.5, fact T=0.5; tau_0 issue=0.25 fact=0.25;
#   kappa 50/150/300 all exact 0.98 -> selected 150; coordinate pass 1
#   no improvement; thresholds.json written; Val-500 refusal verified
#   separately (exit 2).
# Pure-python helper checks: clause_token_spans maps clauses to token
#   ranges; effective_number_weights [2255,300,4000,118] ->
#   [0.296, 1.021, 0.308, 2.376]; bind_evidence / decode_with_thresholds
#   behave as documented (§6 / §3).
```

## 10. What still needs the Colab GPU run (NOT done here)

1. **3-backbone smoke benchmark** (Lane A A4): mmBERT vs MuRIL vs XLM-R
   on the grouped 2k subset — decides the backbone. No winner assumed.
2. **Train Run #1, nested curve** (2k → 4k → 7.5k, mmBERT first):
   commands in `docs/rtx-recall-training-commands.md` §3. Watch the
   OOM behaviour at micro-batch 8 (the TARGET claim is unverified) and
   report the actual outcome + fallback used, if any.
3. **Loss comparison:** weighted CE (baseline) vs focal CE (challenger)
   on grouped OOF — focal is adopted only if it beats weighted CE
   without degrading rare-state precision.
4. **5-fold grouped OOF on Train-7500** (fold files / fold training),
   then `scripts/calibrate_thresholds.py` for real thresholds.json.
   The script is smoke-tested only (see §9).
5. **--merge-lora** and the LoRA path generally: code updated for the
   new backbones but unverified without torch/peft (same caveat as
   Lane 04 — report the exact error if it fails, do not hand-edit
   state dicts).
6. **Epochs >4, lr, γ/β/w₀/cap grids** are search spaces, not tuned
   values — the Colab runs measure them.

## 11. Deliberately left OPEN (with reasons)

- **Full fact binding** (§6): needs a Lane 02 schema change
  (span-level subject + event_id). Not hacked into the current schema.
- **Per-floor Pareto re-optimisation** (§3): thresholds.json reports
  pass/fail per floor for the final point; re-running refinement under
  each floor is a follow-up, not done here.
- **5-fold grouped OOF generation** (§3): needs fold files / fold
  training runs on GPU; the calibration script consumes the dump, it
  does not produce the folds.
- **Backbone choice** (§5): no winner picked here; A4 decides.
- **Gate disagreement**: RESOLVED (80% per language stays — GPT-RERUN
  §11); the Hydrogen ≥75%/≥70% relaxation is rejected, recorded in
  `docs/impl_swarm_state.md` and NOT re-litigated here.
- **Neon re-run**: completeness check only ("you do not need to wait
  for Neon" — GPT-RERUN). Nothing in this lane blocks on it.
