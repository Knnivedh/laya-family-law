# RTX 5050 — LAYA v7.1 Classifier Training + Evaluation Commands (Lane 04)

Owner: Lane 04 (classifier training prep). Run on the user's RTX 5050 machine
(8 GB VRAM, CUDA), from the repo root `~/workspace/laya-v71-work`.
**No training runs on the coordinator VM — it has no GPU and no torch.**
Every command below was verified torch-free on this VM only up to the point
where torch is required (`--check-data-only` passes; training/eval exit 2
there with the RTX instruction). The GPU steps themselves are unverified
until the RTX run happens — report the actual outputs back, do not assume them.

Target (user, 2026-11-27 ~19:19 IST): unseen law-related questions ≥70% exact.
Current sealed: Fresh-20 7/20 (35%), Kannada-8 4/8 (50%). The validation-split
number below is a PROXY, never the sealed number. The sealed re-run happens
only on the RTX machine, after the exit bars in §4 pass, and never on this VM.

Baseline to beat on the validation split (Lane 07, evidence mode, CPU,
`results/recall_eval_summary_baseline.json`): **173/500 exact (34.6%)**,
micro-P/R/F1 0.8498 / 0.3389 / 0.4846, silent 263. Per-language: EN 129/228
(56.6%), KN 23/153 (15.0%), Kanglish 21/119 (17.6%). The classifier must beat
34.6% by a wide margin, and KN/Kanglish are the weak lanes to watch.

## 0. Prerequisites (RTX machine, one-time)

```bash
cd ~/workspace/laya-v71-work
git log --oneline -1          # expect a commit at/after the Lane 04 R-LANE04 commits
git status --short            # expect a clean tree (training writes only under models/)
nvidia-smi                    # expect the RTX 5050 listed, 8 GB VRAM, driver OK
python3 -c "import torch; print(torch.__version__, torch.cuda.is_available())"
# expect e.g. 2.x and True. If torch is missing:
pip install torch transformers
# LoRA fallback only:
pip install peft
```

Model download on first run (~1.5 GB for `answerdotai/ModernBERT-large`,
Apache-2.0): the first training/smoke invocation downloads it from Hugging
Face — allow 2–10 min depending on network. If the box is offline, pre-fetch
with `huggingface-cli download answerdotai/ModernBERT-large` while online.
Do NOT train on `PIXMELT/laya` — the code refuses it until Lane 06's license
audit verifies it is permissive.

Corpus (Lane 02, current): `data/synthetic_v7_1/train.jsonl` (4,500) +
`data/synthetic_v7_1/validation.jsonl` (500), seed 7102, EN 2,316 / KN 1,333 /
Kanglish 1,351. **If Lane 02 lands the expanded 8,000+ corpus first:**
re-run §1 and confirm the new counts, then use the same commands with the new
file paths (the `--train-file` / `--val-file` paths below are the only thing
that changes). Re-run the leakage gate after any expansion
(`scripts/check_ngram_leakage.py`) — training on a leaked split invalidates
every number below.

## 1. Verify the corpus loads cleanly (CPU-safe, ~10 s)

```bash
python3 scripts/train_v71_classifier.py \
    --train-file data/synthetic_v7_1/train.jsonl \
    --val-file data/synthetic_v7_1/validation.jsonl \
    --check-data-only
```

Expected output (exact lines at the end):

```
OK: train=4500 val=500 (torch NOT needed for this mode).
```

And in the JSON report above it: `n_ok` 4500 / 500, `n_skipped` 0 / 0,
`unknown_issue_keys` `{}` and `unknown_fact_keys` `{}` on both splits
(Lane 04 PC-2 fix: the classifier vocab is now set-identical to
`data/synthetic_v7_1/schema.json` — 11 issues / 28 facts, including
`in_scope`). Languages: train EN 2088 / KN 1180 / Kanglish 1232;
validation EN 228 / KN 153 / Kanglish 119. If any unknown key appears, STOP
and report it to the coordinator — do not train on a mismatched vocab.

## 2. Smoke run — 32 examples, 1 epoch (~1–3 min on GPU)

Verifies the whole pipeline (tokenizer, model build, loss, eval, checkpoint
write) before the real run. Uses the same flags as §3 plus `--smoke`.

```bash
python3 scripts/train_v71_classifier.py \
    --train-file data/synthetic_v7_1/train.jsonl \
    --val-file data/synthetic_v7_1/validation.jsonl \
    --backbone answerdotai/ModernBERT-large \
    --epochs 5 --batch-size 4 --grad-accum 2 --lr 2e-5 \
    --class-weights --patience 2 \
    --max-seq-len 192 --max-clauses 8 \
    --output-dir models/v71-classifier-smoke --device cuda --fp16 \
    --grad-checkpoint --seed 42 --smoke
```

Expected: one `epoch 1/1 loss=... val issue macro/micro=... fact
macro/micro=... requested_recall=... mean_macro=...` line, then
`DONE. Best mean val macro-F1 ... Best checkpoint:
models/v71-classifier-smoke/best/model.pt`. The numbers will be poor (32
examples) — only the pipeline completing matters. If it OOMs here, go to §6
before attempting §3. Delete the smoke dir afterwards
(`rm -rf models/v71-classifier-smoke`).

## 3. Full training run (~15–30 min on GPU, see timing note)

```bash
python3 scripts/train_v71_classifier.py \
    --train-file data/synthetic_v7_1/train.jsonl \
    --val-file data/synthetic_v7_1/validation.jsonl \
    --backbone answerdotai/ModernBERT-large \
    --epochs 5 --batch-size 4 --grad-accum 2 --lr 2e-5 \
    --class-weights --patience 2 \
    --max-seq-len 192 --max-clauses 8 \
    --output-dir models/v71-classifier --device cuda --fp16 \
    --grad-checkpoint --seed 42
```

Timing note (estimate, not a promise): the corpus averages 3.75 clauses and
~25 words per record (~115 tokens per example incl. clauses), so an effective
batch of 8 is ~920 tokens per optimizer step; 4,500 train records = ~563
steps/epoch. Expect roughly 3–6 min/epoch including the 500-record validation
pass, i.e. ~15–30 min for 5 epochs. Early stopping (`--patience 2`) may end
it sooner — that is a normal outcome, not a failure. Report the actual wall
time and per-epoch lines.

Expected stdout (one line per epoch, plus a `new best` line when it improves):

```
train=4500 val=500 backbone=answerdotai/ModernBERT-large device=cuda fp16=True
epoch 1/5 loss=... val issue macro/micro=.../... fact macro/micro=.../... requested_recall=... mean_macro=...
  new best (mean_macro=...) -> models/v71-classifier/best/model.pt
...
epoch 5/5 loss=... ...
DONE. Best mean val macro-F1 (issue+fact): ... Best checkpoint: models/v71-classifier/best/model.pt
Exit bar (plan §1.3): synthetic held-out macro/micro-F1 >= 0.95 per head; requested_recall >= 0.98 before any sealed evaluation.
```

Files produced under `models/v71-classifier/`:

| Path | Contents |
|---|---|
| `best/model.pt` + `best/config.json` + `best/label_maps.json` | Best checkpoint by mean val macro-F1 (issue+fact) — **use this one** |
| `last/model.pt` + `last/config.json` | Final-epoch checkpoint (may be worse than best) |
| `train_log.jsonl` | One JSON object per epoch (losses + all val metrics) |
| `data_report.json` | Corpus load report (§1 numbers, for the record) |

## 4. Evaluate the best checkpoint on the held-out split (~2–5 min on GPU)

One command prints BOTH numbers: per-head label metrics (model-side) and the
section-exact R1 number (Lane 07's harness, same run — no retraining).

```bash
python3 scripts/train_v71_classifier.py \
    --eval-checkpoint models/v71-classifier/best/model.pt \
    --val-file data/synthetic_v7_1/validation.jsonl --device cuda
```

Expected output: a `per-head label metrics` JSON block (`issue` / `fact` /
enum heads, `issue_requested_recall`, `mean_macro_f1_issue_fact`,
`in_scope` with `accuracy` + `denied_recall`), then a `section-exact`
JSON block (`exact_count`, `exact_rate`, Wilson 95% CI, micro-P/R/F1,
`silent`, per-language / per-issue / per-cluster exact, failure tags, top
missing/extra sections), then the one-line summary
`section-exact: N/500 (...) Wilson 95% CI [...] silent=M`.

**Exit bars (plan §1.3 + swarm target) — all must hold before any sealed run:**

1. Per-head macro/micro-F1 ≥ 0.95 on issue AND fact heads (label metrics).
2. `issue_requested_recall` ≥ 0.98 (a missed `requested` is a silent drop).
3. Section-exact on the 500 validation split clearly above the 173/500
   (34.6%) evidence baseline, with silent well below 263 — and KN/Kanglish
   exact visibly improved from 15.0% / 17.6% (the target is ≥70% exact on
   unseen questions; the validation split is a proxy, not proof — a pass
   here earns the sealed re-run, it does not claim the sealed number).

If any bar fails: paste the full per-epoch log + both eval blocks back to the
coordinator (do NOT proceed to sealed). If all pass: the sealed re-run is a
separate coordinator step on the RTX machine only.

CPU evaluation is also possible (`--device cpu`) but slow (per-question
`predict_text`, batch 1, no GPU) — expect tens of minutes for 500 records;
prefer GPU.

## 5. Hyperparameters (defaults in code + the §3 command) and why

| Setting | Value | Reason |
|---|---|---|
| Backbone | `answerdotai/ModernBERT-large` (Apache-2.0) | Permissive license; 395M params fits 8 GB with checkpointing. DeBERTa-v3-large (MIT) is the accepted alternative. |
| Learning rate | 2e-5, AdamW, linear warmup 10% → cosine decay | Standard full fine-tune rate for a ~400M encoder; warmup avoids early-step instability on the small (4.5k) set. LoRA runs (fallback) use 1e-4 instead — see §6. |
| Batch | 4 per step × grad-accum 2 = effective 8 | Largest that fits 8 GB VRAM: each example encodes 1 full question + up to 8 clauses (mean 3.75). |
| Epochs | 5, with early stopping `--patience 2`, `--min-delta 0.001` | 4,500 examples × 5 epochs ≈ 2,800 steps — enough for a multi-head fine-tune, short enough to limit template overfit. Stops when mean val macro-F1 (issue+fact) fails to improve by >0.001 for 2 epochs; best checkpoint is kept either way. |
| `--class-weights` | ON | Class imbalance is severe: `in_scope` denied is 288/5,000 (5.8%); `dv_compensation` requested 134, `restitution` 118, `birth_certificate` 135, `procedure` 135; `child_safety_risk` supported only 50. Inverse-frequency weights (clipped [0.25, 4.0]) keep rare heads from being ignored. Without this flag the model can hit high micro-F1 while never predicting a rare class. |
| Max seq len | 192 | Corpus max is 409 chars / 78 words; even with Kannada subword expansion (~2× words) the longest record is ~156 tokens — 192 covers everything with headroom, no truncation of real records. |
| Max clauses | 8 | p95 is 6 clauses/record, max 8 after merging (only 40 records hit the merge). |
| Dropout / weight decay | 0.1 / 0.01 | Standard regularisation for a small synthetic set. |
| Loss weights | issue 0.35, fact 0.35, enum 0.15, gate 0.10, span 0.05 | Issue+fact heads drive the downstream section routing, so they dominate; enum/gate/span are auxiliary (gate vetoes clauses in fusion; span is evidence attribution). |
| `tau_neg` | 0.5 | Per-clause gate veto threshold: a clause is excluded from the clause max-pool iff any gate sigmoid (denied/hypothetical/third-party) ≥ 0.5. Neutral default; Lane 10 fits it on held-out dev. |
| Seed | 42 | Deterministic split (stratified by lang) and shuffling. |
| fp16 + grad-checkpoint | ON | fp16 halves memory/speeds the RTX 5050; gradient checkpointing trades ~30% speed for the memory headroom that makes batch 4 possible. |

## 6. Fallbacks (in order — try the next only if the previous OOMs/fails)

```bash
# (a) Smaller per-step batch, same effective batch:
--batch-size 2 --grad-accum 4
# (b) Heads-only training (backbone frozen, much less memory):
--freeze-backbone
# (c) LoRA (needs peft; attention projections only, r=8; use lr 1e-4):
python3 scripts/train_v71_classifier.py \
    --train-file data/synthetic_v7_1/train.jsonl \
    --val-file data/synthetic_v7_1/validation.jsonl \
    --backbone answerdotai/ModernBERT-large --epochs 5 \
    --batch-size 4 --grad-accum 2 --lr 1e-4 \
    --class-weights --patience 2 \
    --output-dir models/v71-classifier-lora --device cuda --fp16 \
    --grad-checkpoint --seed 42 --lora
# LoRA checkpoints must be MERGED before evaluation (peft-prefixed keys):
python3 scripts/train_v71_classifier.py \
    --merge-lora models/v71-classifier-lora/best/model.pt \
    models/v71-classifier-lora/best/model-merged.pt
# then evaluate the merged file with the §4 command.
# (d) Different backbone (same command, swap the value):
--backbone microsoft/deberta-v3-large
```

Known fixed bug (Lane 04): `--lora` previously crashed with `NameError`
(the wrap referenced `model` before it was built). The build now happens
first, then the wrap. The `--merge-lora` path is new code and is NOT verified
on this VM (no torch here) — if it fails on the RTX box, report the exact
error rather than working around it by hand-editing state dicts.

## 7. What to report back (paste verbatim)

1. The `OK: train=... val=...` line from §1 (or the new counts if Lane 02
   expanded the corpus).
2. The smoke-run `epoch 1/1 ...` line + `DONE` line from §2.
3. Every per-epoch line from §3 + the `DONE` line + actual wall time.
4. The full §4 output (both JSON blocks + the `section-exact:` line).
5. Which exit bars in §4 passed/failed, and whether early stopping fired
   (which epoch it stopped at).
6. Any OOM/fallback used (§6) and its outcome.

## 8. What NOT to do

- Do not train or evaluate on this coordinator VM (no torch/GPU — it exits 2).
- Do not score anything under `test-bank/sealed/` with these commands. The
  harness refuses sealed paths; the sealed re-run is a separate coordinator
  step after §4 passes.
- Do not present the validation-split exact rate as the sealed Fresh-20 /
  Kannada-8 number. It is a paraphrase-template proxy; the user target is
  measured on sealed sets only.
- Do not change `--class-weights` off, the backbone, or the loss weights
  without recording the change — the §5 reasons are the tuned defaults and
  any deviation needs its own before/after numbers.
