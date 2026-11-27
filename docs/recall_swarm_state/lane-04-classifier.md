# Lane 04 — Classifier Training Prep — STATUS

- Lane: 04 (recall swarm; V71-P1-3 training prep)
- Files owned (only these touched): `src/laya_v7_classifier.py`,
  `scripts/train_v71_classifier.py`, `docs/rtx-recall-training-commands.md`
  (new), this status file.
- Status: DONE (code + commands only — NO training run here: this VM has no
  torch/GPU, and no neural execution of any kind was attempted or faked).
- No other lane's files edited; no frozen files touched; no sealed files opened.

## 1. What was fixed

### PC-2 vocab pin — RECONCILED (the one unknown key: `in_scope`)
Lane 03's classifier vocab vs `data/synthetic_v7_1/schema.json` (contract R2),
checked record-by-record against the real corpus (5,000 records):

| | Lane 03 list | Schema / corpus |
|---|---|---|
| Issues | 11, set-identical, different order | 11 — order now matches the schema exactly |
| Facts | 27 overlap + `stridhan_held_or_disposed` (phantom) | 28 incl. `in_scope`, NO `stridhan_held_or_disposed` in any record |

- `stridhan_held_or_disposed` was a DERIVED downstream fact (graph L210
  derives it from `stridhan_claim`); it appears in 0/5,000 corpus records,
  so its head would have trained on all-`unknown` labels forever.
- `in_scope` is in ALL 5,000 records (supported 4,712 / denied 288 — 5.8%
  denied = the out-of-scope signal) and was being silently dropped as an
  "unknown key" on every record. It is now the 28th fact head: supported =
  in scope, denied = out of scope. It drives the graph's in_scope=False OOS
  escalation (graph L400) and the V71-P1-5 clarification fallback.
- `FACTS` / `ISSUES` in `src/laya_v7_classifier.py` are now ordered exactly
  as in `schema.json`, so label indices line up with the corpus by
  construction. The stridhan disposition signal the corpus DOES carry is
  `stridhan_sold_or_mortgaged` (unchanged).
- NOTE for coordinator: `src/laya_schema_v71.py:168` also lists
  `stridhan_held_or_disposed` (not my file — flagging, not editing).

### Loader span-shape fix (gate/span heads had ZERO supervision)
The corpus spans are `{start, end, text, key, kind}` (key = fact/issue name,
kind = `fact` | `issue`, offsets verified valid on samples); Lane 03's loader
expected `{clause_idx, label}` and stored both as None, so `span_mask` was
all zeros and gate labels never fired. The loader now derives `clause_idx`
from char offsets against `split_clauses()` and keeps `key`/`kind`
(legacy `{clause_idx, label}` samples still accepted). `encode_labels()`
now marks a clause gate-denied=1 when a span in it names a fact/issue the
corpus marks `denied`. Measured on the real train split: **155 denied-gate
clause rows (was 0)**, 4,096 span-masked clauses; 1,664 records carry no
spans (span head trains on the rest — expected, not an error).

### LoRA NameError — FIXED
`train()` wrapped the model with `get_peft_model(model, ...)` BEFORE `model`
existed → `NameError` on every `--lora` run. The build now happens first,
gradient checkpointing is enabled on the built model, then the wrap. The
LoRA config is factored into `lora_config_for(backbone)` (shared by train
and merge). New `--merge-lora CKPT OUT` mode merges a LoRA checkpoint into a
plain `model.pt` loadable by `load_checkpoint()` / `--eval-checkpoint`.
**Unverified on this VM (no torch/peft here)** — the RTX run must confirm
it; if it fails, report the exact error, do not hand-edit state dicts.

### Early stopping — ADDED
`--patience 2` (default) + `--min-delta 0.001`: training stops when mean val
macro-F1 (issue+fact) fails to improve by >0.001 for 2 consecutive epochs;
the best checkpoint is always kept. `--patience 0` disables it.

### Validation harness hook — WIRED to Lane 07 (not duplicated)
- Model-side, in `src/laya_v7_classifier.py`: `score_label_predictions()`
  (pure python per-head macro/micro-F1, pooled `requested` recall,
  `in_scope` accuracy + denied recall) and `evaluate_checkpoint()` (torch;
  loads a checkpoint, runs `predict_text()` per validation record, scores;
  `return_predictions=True` also returns gold + preds).
- **Name-collision found and resolved:** `tests/recall_eval.py` (Lane 07,
  landed mid-task) defines its own `score_predictions(records,
  predicted_sections)` scoring SECTION-SET exact — a different function with
  the same name as Lane 03's planned model scorer. Lane 04's per-head scorer
  is therefore named `score_label_predictions`, NOT `score_predictions`.
- Lane 04 CONFIRMS Lane 07's proposed shared signature as written in
  `tests/recall_eval.py`: `predict_sections_from_stage1(issues, facts,
  enums, *, custody_vocab="v3_bundled") -> set[str]`, accepting
  `predict_text()`-style dicts and plain strings. The composed model path is:
  `predict_text()` → `predict_sections_from_stage1()` →
  `recall_eval.score_predictions()` (section-exact R1 number) +
  `score_label_predictions()` (per-head diagnostics).
- `scripts/train_v71_classifier.py --eval-checkpoint CKPT --val-file ...`
  runs BOTH in one command (section part guarded: if the harness file is
  absent it prints a NOTE and the label metrics still stand). The classifier
  module never imports the harness (the harness imports the classifier — the
  dependency runs one way only).

## 2. Loader verification output (exact commands + lines)

```bash
python3 scripts/train_v71_classifier.py \
    --train-file data/synthetic_v7_1/train.jsonl \
    --val-file data/synthetic_v7_1/validation.jsonl --check-data-only
# OK: train=4500 val=500 (torch NOT needed for this mode).
```

Loader report (both splits): `n_ok` 4500 / 500, `n_skipped` 0 / 0,
`unknown_issue_keys` `{}`, `unknown_fact_keys` `{}`, `unknown_enum_values`
`{}`. Train langs EN 2088 / KN 1180 / Kanglish 1232; validation EN 228 /
KN 153 / Kanglish 119. Spans: 4,276 train / 453 validation, all with valid
offsets. Vocab check: `list(ISSUES)==schema["issues"]` True,
`list(FACTS)==schema["facts"]` True. `score_label_predictions` self-check
(gold vs gold, n=200): all 1.0, `requested_recall` 1.0, `in_scope` accuracy
1.0 / denied recall 1.0.

CPU-only smoke test: `--check-data-only` is the only runnable mode here
(no torch/GPU — training and `--smoke` exit 2 with the RTX instruction, and
`--eval-checkpoint` exits 2 the same way; verified, no traceback). No tiny
subset training was possible on this VM; the RTX `--smoke` run in
`docs/rtx-recall-training-commands.md` §2 is the pipeline smoke test.

Corpus text lengths (grounds `max_seq_len` 192): mean 154.6 chars / 25.5
words, p95 262 chars / 47 words, p99 316 / 60, max 409 / 78. Mean 3.75
clauses/record, p95 6, max 8 after merging (40 records hit the merge).

## 3. Hyperparameter choices with reasons

(Full table in `docs/rtx-recall-training-commands.md` §5; the decisions:)

- **LR 2e-5, AdamW, warmup 10% → cosine decay** — standard full fine-tune
  rate for a ~400M encoder on a small set. LoRA fallback uses 1e-4 (§6).
- **Effective batch 8 (4 × grad-accum 2)** — largest that fits 8 GB VRAM
  (each example = 1 full + up to 8 clauses); fp16 + grad-checkpoint on.
- **Epochs 5 + early stopping (patience 2, min-delta 0.001)** — ~2,800
  steps total; enough for multi-head fine-tuning, short enough to limit
  template overfit; best checkpoint kept regardless.
- **`--class-weights` ON (in the recommended command)** — imbalance is
  severe: `in_scope` denied 288/5,000 (5.8%), `dv_compensation` requested
  134, `restitution` 118, `birth_certificate` 135, `procedure` 135,
  `child_safety_risk` supported 50. Inverse-frequency weights clipped
  [0.25, 4.0]; without them the model can post high micro-F1 while never
  predicting a rare class.
- **Loss weights issue 0.35 / fact 0.35 / enum 0.15 / gate 0.10 / span 0.05**
  — issue+fact drive downstream section routing; the rest are auxiliary.
- **`tau_neg` 0.5** — neutral per-clause gate veto default; Lane 10 fits it
  on held-out dev.
- **Backbone `answerdotai/ModernBERT-large` (Apache-2.0)**, DeBERTa-v3-large
  (MIT) as alternative; `PIXMELT/laya` still refused until Lane 06's
  license audit verifies it.

## 4. Exact RTX commands (copied from docs/rtx-recall-training-commands.md)

```bash
# 1. Verify corpus (~10 s)
python3 scripts/train_v71_classifier.py \
    --train-file data/synthetic_v7_1/train.jsonl \
    --val-file data/synthetic_v7_1/validation.jsonl --check-data-only
# expect: OK: train=4500 val=500

# 2. Smoke (~1-3 min GPU)
python3 scripts/train_v71_classifier.py \
    --train-file data/synthetic_v7_1/train.jsonl \
    --val-file data/synthetic_v7_1/validation.jsonl \
    --backbone answerdotai/ModernBERT-large \
    --epochs 5 --batch-size 4 --grad-accum 2 --lr 2e-5 \
    --class-weights --patience 2 \
    --max-seq-len 192 --max-clauses 8 \
    --output-dir models/v71-classifier-smoke --device cuda --fp16 \
    --grad-checkpoint --seed 42 --smoke

# 3. Full training (~15-30 min GPU estimate; early stopping may end it sooner)
python3 scripts/train_v71_classifier.py \
    --train-file data/synthetic_v7_1/train.jsonl \
    --val-file data/synthetic_v7_1/validation.jsonl \
    --backbone answerdotai/ModernBERT-large \
    --epochs 5 --batch-size 4 --grad-accum 2 --lr 2e-5 \
    --class-weights --patience 2 \
    --max-seq-len 192 --max-clauses 8 \
    --output-dir models/v71-classifier --device cuda --fp16 \
    --grad-checkpoint --seed 42

# 4. Evaluate best checkpoint (~2-5 min GPU; prints per-head AND section-exact)
python3 scripts/train_v71_classifier.py \
    --eval-checkpoint models/v71-classifier/best/model.pt \
    --val-file data/synthetic_v7_1/validation.jsonl --device cuda
```

Exit bars before any sealed run: per-head macro/micro-F1 ≥ 0.95 (issue+fact),
`issue_requested_recall` ≥ 0.98, section-exact clearly above the 173/500
(34.6%) evidence baseline with silent well below 263. Validation exact is a
proxy, never the sealed number.

## 5. Guardrails run (exact output lines)

```bash
python3 tests/test_graph_v4.py
# GRAPH V4 + FROZEN SHA TEST PASS: 34 sections / 66 nodes / 99 edges, 0 dangling edges, 7/7 frozen hashes intact.
python3 tests/test_prose_renderer_v2.py
# PROSE VALIDATION PASS: 246 cases, Fp=0, quality_flags=0, 15/15 adversarial mutants caught, mean=0.02ms, max=0.28ms
python3 tests/recall_eval.py --self-test
# SELF-TEST: PASS (0 failures)
```

## 6. Still unverified / open

- NO training run has happened anywhere — GPU steps (§2–§4 of the RTX doc)
  are unverified until the RTX 5050 run; no scores exist, nothing is claimed.
- `--merge-lora` is new code, unverified without torch/peft (see §1).
- If Lane 02 lands the expanded 8,000+ corpus, re-run §1, confirm new
  counts, re-run the leakage gate, and use the new file paths — the commands
  are otherwise unchanged. If the expansion adds a new fact/issue key (e.g.
  `stridhan_held_or_disposed`), the vocab must be re-pinned — coordinator
  decision, not a silent loader default.
- Lane 07's `score_predictions` and Lane 04's `score_label_predictions` are
  now distinct by name; any future doc/code must not conflate them.
- `tau_neg` and per-head temperatures are Lane 10's calibration job on
  held-out dev (defaults 0.5 / 1.0 are neutral, not fitted).
