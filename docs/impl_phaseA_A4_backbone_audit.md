# Phase A gate A4 — Backbone swap + tokenizer audit + 3-backbone smoke benchmark

- **Lane:** A (implementation swarm)
- **Date:** 2026-11-27
- **Script:** `scripts/smoke_backbones.py` (part (a) needs transformers,
  part (b) needs torch + GPU)
- **Verdict: OPEN — code ready, run on Colab.** No numbers exist yet.
  Nothing was faked.

## Environment fact (measured on this VM)

```bash
python3 -c "import transformers"   # ModuleNotFoundError
python3 -c "import torch"          # ModuleNotFoundError
python3 scripts/smoke_backbones.py --part a
# CODE READY, RUN ON COLAB ... No numbers are reported from this VM (exit 2).
```

`transformers` is not importable without torch on this VM, so part (a)
could not be attempted here even in tokenizer-only form. The script
exits 2 with the Colab instruction instead of producing numbers.

## The three backbones (no predetermined winner)

| Backbone | Licence (expected) | Role in the benchmark |
|---|---|---|
| `jhu-clsp/mmBERT-base` | MIT | Primary candidate (307M, 1,833 languages) — NOT the presumed winner |
| `google/muril-base-cased` | Apache-2.0 | Serious Kanglish challenger: Indian-language focus, transliteration-aware pretraining (Kannada + transliteration pairs) |
| `FacebookAI/xlm-roberta-base` | MIT | Multilingual baseline |

Licences: Lane B has already verified them from the HF model cards
and recorded them in code (`src/laya_v7_classifier.py:226–235`:
mmBERT MIT, MuRIL Apache-2.0, XLM-R MIT, corroborated by GPT-RERUN
§7). The script re-verifies them at run time via the Hugging Face Hub
API when reachable and marks them UNVERIFIED otherwise — on this VM
`huggingface_hub` is not installed, so all three are UNVERIFIED in
this run. **Do not train on a backbone whose licence was not confirmed
in the Colab run log.** Checkpoint revision must also be recorded at
download time on Colab.

## What the script does

**Part (a) — tokenizer fertility + truncation audit** (transformers
only, CPU-capable on Colab): for each backbone, tokenize the corpus
stratified by language (en / kn / kanglish) and report, per language:
tokens-per-whitespace-word (median, p95), length inflation vs English,
truncation rate at `max_seq_len` 320, and evidence retention (fraction
of annotated spans fully inside the first 320 tokens). No claim about
Kanglish fragmentation is made until these measurements exist —
GPT-RERUN is explicit: do not assume mmBERT fragments Kanglish worse
until tokenization establishes it, and fewer tokens does not
automatically mean better semantics.

**Part (b) — 1-fold smoke-F1 code path** (torch + GPU): builds a
grouped 2,000-example subset (whole template-block signatures held
out — the corpus has no `template_family_id`, see A5), then drives
`scripts/train_v71_classifier.py` once per backbone with identical
exposure, and scores per-language section-exact via the Lane 07
harness (`tests/recall_eval.py`). Pre-flight: the train script must
accept the backbone in its `--backbone` choices; if it does not, that
backbone is reported NOT-RUN with the exact missing change and no
number is faked. Selection rule (GPT-RERUN §7): prefer the model with
the highest **worst-language** exact match among comparable
candidates; if the difference is < ~3pp, repeat with more seeds/data.
The 20-minute benchmark is a compatibility smoke test, not a reliable
winner decision.

## Lane B state at audit time (already landed — this doc was corrected
## for it; the audit itself ran against the post-Lane-B tree)

- The backbone default in `src/laya_v7_classifier.py` is now
  `jhu-clsp/mmBERT-base` (Lane B, `DEFAULT_BACKBONE`, line 238), with
  all three benchmark backbones in `BACKBONES` (lines 233–235) and in
  the train script's `--backbone` choices. The default was swapped
  BEFORE the benchmark names a winner — that ordering is Lane B's /
  the coordinator's call, and it means the smoke benchmark (part b)
  now measures whether the already-chosen default is actually the
  best of the three, rather than choosing from scratch. If MuRIL or
  XLM-R wins the benchmark, the default must be changed to match.
- `max_seq_len` default is now **320** (Lane B,
  `ClassifierConfig.max_seq_len`, line 254) — the adopted FALLBACK-2
  value, superseding the plan's 288 and the old default 192.
- `--loss {weighted_ce,focal_ce}` (default `weighted_ce`) and 1-pass
  span pooling (`pooling="one_pass"`, default) have also landed
  (Lane B). Part (b)'s pre-flight (train script accepts all three
  backbones) therefore passes today; the remaining blocker for part
  (b) is only the GPU run itself.

## What Lane A did NOT do (ownership)

- Lane A does not edit the classifier or the train script. The
  backbone default swap above is Lane B's work, recorded here so the
  benchmark's purpose is stated honestly.
- The GPT-RERUN gate question is RESOLVED and is not re-opened here:
  the relaxed ≥75% overall / ≥70% per-language gate is rejected;
  **80% per language stays** (Wilson: 80/100 → lower bound 71.1%
  vs 70/100 → 60.4%).

## Run on Colab (exact commands)

```bash
# Part (a) — tokenizer audit (needs transformers only):
python3 scripts/smoke_backbones.py --part a \
    --train-file data/synthetic_v7_1/train.jsonl \
    --val-file data/synthetic_v7_1/validation.jsonl \
    --json-out /tmp/smoke_backbones_a.json
# Part (b) — 1-fold smoke-F1 (needs torch + GPU; Lane B must first
# have added the three backbones to the train script's --backbone
# choices):
python3 scripts/smoke_backbones.py --part b --n-train 2000 --epochs 1 \
    --train-file data/synthetic_v7_1/train.jsonl \
    --val-file data/synthetic_v7_1/validation.jsonl \
    --json-out /tmp/smoke_backbones_b.json
```

## Lane B prerequisites for part (b) — DONE, except the GPU run

1. ~~Add the three backbones to the train script / classifier~~ —
   LANDED (Lane B, see above).
2. ~~Land 1-pass span pooling + `--loss`~~ — LANDED (Lane B).
   Part (b) as written drives the train script as-is; the run log
   must still record the pooling mode and loss actually used, so a
   smoke result is traceable to the config that produced it.
