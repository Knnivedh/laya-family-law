# Colab T4 (FIRST) — LAYA v7.1 Classifier Training + Evaluation Commands (Lane B)

Owner: Lane B (FALLBACK-2 classifier amendments; supersedes Lane 04's
RTX-first version of this doc). Run in **Google Colab (T4) FIRST** — user
rule: Google Colab ONLY for computing/testing/code. The RTX 5050 commands
in each section are the equivalent local path, NOT a comparison. No
Colab-vs-RTX comparison anywhere in this doc.
**No training runs on the coordinator VM — it has no GPU and no torch.**
Every command below was verified torch-free on this VM only up to the
point where torch is required (`--check-data-only` passes; training/eval
exit 2 there with the Colab instruction). The GPU steps themselves are
unverified until the Colab run happens — report the actual outputs back,
do not assume them.

Target (user, 2026-11-27 ~19:19 IST): unseen law-related questions ≥70% exact.
Current sealed: Fresh-20 7/20 (35%), Kannada-8 4/8 (50%). The validation-split
number below is a PROXY, never the sealed number. The sealed re-run happens
only on Colab/RTX, after the exit bars in §4 pass, and never on this VM.

Baseline to beat on the validation split (Lane 07, evidence mode, CPU,
`results/recall_eval_summary_baseline.json`): **173/500 exact (34.6%)**,
micro-P/R/F1 0.8498 / 0.3389 / 0.4846, silent 263. Per-language: EN 129/228
(56.6%), KN 23/153 (15.0%), Kanglish 21/119 (17.6%). The classifier must beat
34.6% by a wide margin, and KN/Kanglish are the weak lanes to watch.
(Note: those per-language counts are the old 5,000-corpus split's; the
frozen 500-record validation file itself is unchanged — sha256
`7640d067c28abf539131dbcc891e4bdffedf62bbef4a7d66c1659bb96d07e58e`.)

## 0. Prerequisites (Colab T4, one-time per session)

```python
# Colab cell 1 — setup (the notebook notebooks/laya_v71_train_backtest.ipynb
# does this for you; the commands below are the manual equivalent)
!git clone <repo-url>            # working copy HEAD 90e20c5 + Lane B commits
%cd laya-v71-work
!git log --oneline -1            # expect a commit at/after the Lane B R-IMPL commits
!git status --short              # expect a clean tree (training writes only under models/)
!nvidia-smi                      # expect a Tesla T4, ~15 GB VRAM
!python3 -c "import torch; print(torch.__version__, torch.cuda.is_available())"
# expect e.g. 2.x and True. If torch/transformers are missing:
!pip install torch transformers
# LoRA fallback only:
!pip install peft
```

Model download on first run (~1.2 GB for `jhu-clsp/mmBERT-base`, MIT;
`google/muril-base-cased`, Apache-2.0; `FacebookAI/xlm-roberta-base`,
MIT — licences verified 2026-11-27, see
`docs/impl_laneB_classifier_changes.md` §5): the first training/smoke
invocation downloads the backbone from Hugging Face — allow 2–10 min
depending on network. If the box is offline, pre-fetch with
`huggingface-cli download jhu-clsp/mmBERT-base` while online.
Do NOT train on `PIXMELT/laya` or the superseded Lane 04 backbones
(`answerdotai/ModernBERT-large`, `microsoft/deberta-v3-large`) — the
code refuses them (see the change doc §5).

Corpus (Lane 02, current — 8,000 expansion already landed):
`data/synthetic_v7_1/train.jsonl` (**7,500**) +
`data/synthetic_v7_1/validation.jsonl` (**500**), seed 7102.
Languages: train EN 3,573 / KN 1,931 / `kn_roman` (Kanglish) 1,996;
validation EN 235 / KN 153 / `kn_roman` 112. Spans: 5,829 train / 401 val.
Re-run the leakage gate after any further expansion
(`scripts/check_ngram_leakage.py`) — training on a leaked split
invalidates every number below.

RTX 5050 equivalent (local path, not a comparison): same commands from
the repo root `~/workspace/laya-v71-work` with `--device cuda`; the only
differences are the 8 GB VRAM (vs T4 ~15 GB — micro-batch 8 is a TARGET
on both; on OOM see §6) and `pip install` instead of `!pip install`.

## 1. Verify the corpus loads cleanly (CPU-safe, ~10 s)

```bash
python3 scripts/train_v71_classifier.py \
    --train-file data/synthetic_v7_1/train.jsonl \
    --val-file data/synthetic_v7_1/validation.jsonl \
    --check-data-only
```

Expected output (exact lines at the end):

```
OK: train=7500 val=500 (torch NOT needed for this mode).
```

And in the JSON report above it: `n_ok` 7500 / 500, `n_skipped` 0 / 0,
`unknown_issue_keys` `{}` and `unknown_fact_keys` `{}` on both splits
(Lane 04 PC-2 fix: the classifier vocab is now set-identical to
`data/synthetic_v7_1/schema.json` — 11 issues / 28 facts, including
`in_scope`). Languages: train EN 3573 / KN 1931 / kn_roman 1996;
validation EN 235 / KN 153 / kn_roman 112. If any unknown key appears, STOP
and report it to the coordinator — do not train on a mismatched vocab.

## 2. Smoke run — 32 examples, 1 epoch (~1–3 min on GPU)

Verifies the whole pipeline (tokenizer, model build, 1-pass span pooling,
loss, eval, checkpoint write) before the real run. Uses the same flags as
§3 plus `--smoke`.

```bash
python3 scripts/train_v71_classifier.py \
    --train-file data/synthetic_v7_1/train.jsonl \
    --val-file data/synthetic_v7_1/validation.jsonl \
    --backbone jhu-clsp/mmBERT-base \
    --epochs 4 --batch-size 8 --grad-accum 2 --lr 2e-5 --head-lr 1e-4 \
    --loss weighted_ce --patience 2 \
    --max-seq-len 320 --max-clauses 8 \
    --output-dir models/v71-classifier-smoke --device cuda --bf16 \
    --grad-checkpoint --seed 42 --smoke
```

Expected: one `epoch 1/1 loss=... val issue macro/micro=... fact
macro/micro=... requested_recall=... mean_macro=...` line, then
`DONE. Best mean val macro-F1 ... Best checkpoint:
models/v71-classifier-smoke/best/model.pt`. The numbers will be poor (32
examples) — only the pipeline completing matters. If it OOMs here, go to §6
before attempting §3. Delete the smoke dir afterwards
(`rm -rf models/v71-classifier-smoke`).

**3-backbone smoke benchmark (Lane A A4 — run before committing to a
backbone; no predetermined winner).** Same smoke command with each
backbone, on the same grouped 2,000-example subset (`--train-subset
2000`); compare per-language exact (EN / KN / Kanglish) + peak VRAM.
MuRIL is a serious Kanglish challenger — do not assume mmBERT wins.

```bash
for BB in jhu-clsp/mmBERT-base google/muril-base-cased FacebookAI/xlm-roberta-base; do
  python3 scripts/train_v71_classifier.py \
      --train-file data/synthetic_v7_1/train.jsonl \
      --val-file data/synthetic_v7_1/validation.jsonl \
      --backbone "$BB" \
      --epochs 4 --batch-size 8 --grad-accum 2 --lr 2e-5 --head-lr 1e-4 \
      --loss weighted_ce --patience 2 \
      --max-seq-len 320 --max-clauses 8 --train-subset 2000 \
      --output-dir "models/smoke-$(basename $BB)" --device cuda --bf16 \
      --grad-checkpoint --seed 42 --smoke
done
```

## 3. Full training run — nested learning curve (Phase B)

Train subsets of **2,000 → 4,000 → 7,500** first, plot independent
development performance vs sample size. **Decision rule (GPT-RERUN §9):**
4k→7.5k improves ≥5pp → more diverse data likely worthwhile; 2–5pp →
expand targeted weak clusters; <2pp → diagnose labels, graph inputs,
capacity, domain mismatch before expanding; synthetic improves but human
proxy stagnates → prioritise narrative realism; individual heads improve
but graph exact does not → prioritise joint decoding/calibration.

```bash
# 3a. 2,000-subset run (mmBERT-base first)
python3 scripts/train_v71_classifier.py \
    --train-file data/synthetic_v7_1/train.jsonl \
    --val-file data/synthetic_v7_1/validation.jsonl \
    --backbone jhu-clsp/mmBERT-base \
    --epochs 4 --batch-size 8 --grad-accum 2 --lr 2e-5 --head-lr 1e-4 \
    --loss weighted_ce --patience 2 \
    --max-seq-len 320 --max-clauses 8 --train-subset 2000 \
    --output-dir models/v71-classifier-2k --device cuda --bf16 \
    --grad-checkpoint --seed 42

# 3b. 4,000-subset run (same flags, --train-subset 4000,
#     --output-dir models/v71-classifier-4k)

# 3c. Full 7,500 run (~20–40 min on T4, see timing note)
python3 scripts/train_v71_classifier.py \
    --train-file data/synthetic_v7_1/train.jsonl \
    --val-file data/synthetic_v7_1/validation.jsonl \
    --backbone jhu-clsp/mmBERT-base \
    --epochs 4 --batch-size 8 --grad-accum 2 --lr 2e-5 --head-lr 1e-4 \
    --loss weighted_ce --patience 2 \
    --max-seq-len 320 --max-clauses 8 \
    --output-dir models/v71-classifier --device cuda --bf16 \
    --grad-checkpoint --seed 42
```

Timing note (estimate, not a promise): 1-pass encoding means each example
is ONE sequence (max 320 tokens, mean ~25 words/record) plus span pooling
— no 9× clause re-encoding. An effective batch of 16 is ~5,120 tokens
per optimizer step at max padding (far less with dynamic padding);
7,500 train records = ~469 steps/epoch at effective batch 16. Expect
roughly 5–10 min/epoch including the 500-record validation pass, i.e.
~20–40 min for 4 epochs. Early stopping (`--patience 2`) may end it
sooner — that is a normal outcome, not a failure. Report the actual wall
time and per-epoch lines.

**Loss comparison (do after the weighted-CE curve):** repeat the 7.5k run
with `--loss focal_ce` (challenger) and compare on grouped OOF — adopt
focal ONLY if it improves grouped OOF over weighted CE without materially
degrading rare-state precision. Weighted CE is the baseline; do not
present focal numbers as the default.

Expected stdout (one line per epoch, plus a `new best` line when it improves):

```
train=7500 val=500 backbone=jhu-clsp/mmBERT-base device=cuda bf16=True fp16=False loss=weighted_ce pooling=one_pass
epoch 1/4 loss=... val issue macro/micro=.../... fact macro/micro=.../... requested_recall=... mean_macro=...
  new best (mean_macro=...) -> models/v71-classifier/best/model.pt
...
epoch 4/4 loss=... ...
DONE. Best mean val macro-F1 (issue+fact): ... Best checkpoint: models/v71-classifier/best/model.pt
Exit bar (plan §1.3): synthetic held-out macro/micro-F1 >= 0.95 per head; requested_recall >= 0.98 before any sealed evaluation.
```

Files produced under `models/v71-classifier/`:

| Path | Contents |
|---|---|
| `best/model.pt` + `best/config.json` + `best/label_maps.json` | Best checkpoint by mean val macro-F1 (issue+fact) — **use this one** |
| `best/thresholds.json` | Added later by §5 calibration (NOT written by training) |
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
separate coordinator step on Colab/RTX only.

CPU evaluation is also possible (`--device cpu`) but slow (per-question
`predict_text`, batch 1, no GPU) — expect tens of minutes for 500 records;
prefer GPU.

## 5. OOF predictions + graph-aware threshold calibration

After the 5-fold grouped OOF models are trained on Train-7500 (one model
per fold, each excluding its fold — fold files/commands are a Lane A /
coordinator item, not in this doc yet), dump per-record probs from the
OOF predictions and calibrate:

```bash
# Dump OOF probs (TRAIN split only — the calibration script REFUSES
# validation files; exit 2 if you pass validation.jsonl here)
python3 scripts/train_v71_classifier.py \
    --eval-checkpoint models/v71-classifier/best/model.pt \
    --val-file data/synthetic_v7_1/train.jsonl --device cuda \
    --dump-predictions models/v71-classifier/oof-preds.jsonl

# Calibrate (pure python, CPU, minutes): temperature first, tau_0 per
# family, per-head F1.2 thresholds, EB shrinkage comparing kappa
# {50,150,300}, up to 3 coordinate passes (incl. paired moves), floor 0.91
python3 scripts/calibrate_thresholds.py \
    --oof-predictions models/v71-classifier/oof-preds.jsonl \
    --train-file data/synthetic_v7_1/train.jsonl \
    --checkpoint-dir models/v71-classifier/best
# -> writes models/v71-classifier/best/thresholds.json
```

The runtime applies thresholds.json at decode time
(`src/laya_v7_classifier.decode_with_thresholds()`). Re-run §4 after
calibration to confirm the calibrated decode (the §4 eval uses argmax;
the integrated runtime's calibrated numbers come from the backtest
harness — Lane E — not from this command).

## 6. Hyperparameters (defaults in code + the §3 command) and why

| Setting | Value | Reason |
|---|---|---|
| Backbone | `jhu-clsp/mmBERT-base` (MIT) | Primary candidate; ~307M params. MuRIL (Apache-2.0) is the serious Kanglish challenger, XLM-R (MIT) the third equal — A4 benchmark decides, no predetermined winner. |
| Learning rate | 2e-5 encoder / 1e-4 heads, AdamW, warmup 10% → cosine decay | FALLBACK-2 split rates; warmup avoids early-step instability on the small (7.5k) set. LoRA runs (fallback) use 1e-4 for the adapter — see §7. |
| Batch | 8 per step × grad-accum 2 = effective 16 | 1-pass encoding (one 320-token sequence per example). **TARGET, not guaranteed** — the ~9× VRAM saving claim is UNVERIFIED (8.1× padded tokens, not proven VRAM); on OOM the script FAILS and suggests the fallback (§7a) instead of silently shrinking. |
| Epochs | **max 4**, with early stopping `--patience 2`, `--min-delta 0.001` | Over-training past 4 epochs on 7.5k synthetic examples memorises templates (FALLBACK-2). `--epochs 5` is refused outright. Stops when mean val macro-F1 (issue+fact) fails to improve by >0.001 for 2 epochs; best checkpoint is kept either way. |
| `--class-weights` | ON in the §3 command | Effective-number weights (β=0.999, unknown w₀=0.25, capped 8×) — see change doc §2. Imbalance is severe: `in_scope` denied ~5.8%, `dv_compensation` requested ~134/7,500, `restitution` 118, `child_safety_risk` supported ~50. Without this flag the model can hit high micro-F1 while never predicting a rare class. |
| Loss | `--loss weighted_ce` (baseline) / `focal_ce` (challenger) | ASL REMOVED — binary loss, invalid on 4 mutually exclusive states (change doc §2). Focal adopted only if it beats weighted CE on grouped OOF. |
| Max seq len | 320 | 1-pass encoding of the full question; Kannada subword expansion (~2× words) still fits the longest records (max 409 chars / 78 words in the old corpus). Truncation of real records is logged as a diagnostic, not silent. |
| Max clauses | 8 | p95 is 6 clauses/record, max 8 after merging. |
| Dropout / weight decay | 0.1 / 0.01 | Standard regularisation for a small synthetic set. |
| Loss weights | issue 0.35, fact 0.35, enum 0.15, gate 0.10, span 0.05 | Issue+fact heads drive the downstream section routing, so they dominate; enum/gate/span are auxiliary (gate vetoes clauses in fusion; span is evidence attribution). |
| `tau_neg` | 0.5 | Per-clause gate veto threshold: a clause is excluded from the clause max-pool iff any gate sigmoid (denied/hypothetical/third-party) ≥ 0.5. Neutral default; Lane 10 fits it on held-out dev. Hypothetical/third-party language is NOT automatically out-of-scope (GPT-RERUN). |
| Seed | 42 | Deterministic split (stratified by lang) and shuffling. |
| bf16 + grad-checkpoint | ON | bf16 halves memory/speeds the T4; gradient checkpointing trades ~30% speed for memory headroom. |

## 7. Fallbacks (in order — try the next only if the previous OOMs/fails)

```bash
# (a) Smaller per-step batch, same effective batch:
--batch-size 4 --grad-accum 4
# (b) Heads-only training (backbone frozen, much less memory):
--freeze-backbone
# (c) LoRA (needs peft; attention projections only, r=8; use lr 1e-4):
python3 scripts/train_v71_classifier.py \
    --train-file data/synthetic_v7_1/train.jsonl \
    --val-file data/synthetic_v7_1/validation.jsonl \
    --backbone jhu-clsp/mmBERT-base --epochs 4 \
    --batch-size 8 --grad-accum 2 --lr 2e-5 --head-lr 1e-4 \
    --loss weighted_ce --class-weights --patience 2 \
    --max-seq-len 320 --max-clauses 8 \
    --output-dir models/v71-classifier-lora --device cuda --bf16 \
    --grad-checkpoint --seed 42 --lora
# LoRA checkpoints must be MERGED before evaluation (peft-prefixed keys):
python3 scripts/train_v71_classifier.py \
    --merge-lora models/v71-classifier-lora/best/model.pt \
    models/v71-classifier-lora/best/model-merged.pt
# then evaluate the merged file with the §4 command.
# (d) Different backbone (same command, swap the value):
--backbone google/muril-base-cased
--backbone FacebookAI/xlm-roberta-base
```

Known fixed bug (Lane 04): `--lora` previously crashed with `NameError`
(the wrap referenced `model` before it was built). The build now happens
first, then the wrap. The `--merge-lora` path is new code and is NOT verified
on this VM (no torch here) — if it fails on Colab, report the exact
error rather than working around it by hand-editing state dicts. The LoRA
target modules were updated for the new backbones (mmBERT `Wqkv`;
MuRIL/XLM-R `query`/`key`/`value`) — also unverified until a GPU run.

## 8. What to report back (paste verbatim)

1. The `OK: train=... val=...` line from §1 (expect 7500 / 500).
2. The smoke-run `epoch 1/1 ...` line + `DONE` line from §2, per backbone
   for the §2 benchmark (which backbone won, and by how much per language).
3. Every per-epoch line from §3 (2k / 4k / 7.5k) + the `DONE` lines +
   actual wall time + the learning-curve decision (per the §3 rule).
4. The full §4 output (both JSON blocks + the `section-exact:` line).
5. The §5 calibration output + the thresholds.json OOF numbers.
6. Which exit bars in §4 passed/failed, and whether early stopping fired
   (which epoch it stopped at).
7. Any OOM/fallback used (§7) and its outcome — including whether
   micro-batch 8 fit (the TARGET claim is unverified until this run).

## 9. What NOT to do

- Do not train or evaluate on the coordinator VM (no torch/GPU — it exits 2).
- Do not score anything under `test-bank/sealed/` with these commands. The
  harness refuses sealed paths; the sealed re-run is a separate coordinator
  step after §4 passes.
- Do not present the validation-split exact rate as the sealed Fresh-20 /
  Kannada-8 number. It is a paraphrase-template proxy; the user target is
  measured on sealed sets only.
- Do not change `--class-weights` off, the backbone, or the loss weights
  without recording the change — the §6 reasons are the tuned defaults and
  any deviation needs its own before/after numbers.
- Do not tune thresholds on Val-500 or include Val-500 records in OOF
  calibration — `scripts/calibrate_thresholds.py` refuses it (exit 2).
- Do not run a Colab-vs-RTX/Kaggle speed comparison — Colab is the
  compute choice, RTX is the equivalent local path, not a comparison.
