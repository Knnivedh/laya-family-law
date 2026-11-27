# Phase A gate A6 — VRAM smoke-test script

- **Lane:** A (implementation swarm)
- **Date:** 2026-11-27
- **Script:** `scripts/vram_smoke.py` (torch + transformers; GPU only)
- **Verdict: OPEN — code ready, run on Colab.** It cannot run on this
  VM (no torch), so no numbers exist yet. Nothing was faked.

## Environment fact (measured on this VM)

```bash
python3 scripts/vram_smoke.py --backbone jhu-clsp/mmBERT-base \
    --train-file data/synthetic_v7_1/train.jsonl
# torch is NOT installed on this VM. Do not run here. Run this script
# on Colab (T4 GPU) or the RTX 5050 machine: ...   (exit 2)
```

## Adopted config under test

1-pass span pooling, `max_seq_len` 320, bf16, gradient checkpointing,
dynamic padding — the FALLBACK-2 config as amended by GPT-RERUN §4.
**Micro-batch 8 is a TARGET, not a guarantee:** the fallback's VRAM
claim (9× → 1× sequences, "~6× VRAM drop") was overstated — 8.1×
padded tokens is not a proven VRAM reduction (parameter weights and
optimizer states are not replicated nine times; dynamic padding
changes the actual token ratio). The script therefore SWEEPS
micro-batch 1, 2, 4, 8 and verifies what actually fits.

## What the script does (Colab T4 / RTX 5050)

1. **Micro-batch sweep (1, 2, 4, 8):** forward + backward + optimizer
   step on REAL tokenized corpus batches (dynamic padding to the
   longest sequence in the batch), bf16 autocast, gradient
   checkpointing on. Records peak allocated memory per size (via
   `torch.cuda.max_memory_allocated`), loss, seconds and tokens/s.
   An OOM at any size is recorded as `fits: False` for that size and
   the sweep continues — an OOM at 8 is a GATE FAILURE for the
   target, and the report names the largest fitting size as the
   fallback for Lane B. Nothing is silently shrunk.
2. **Loss-decrease check:** 32 real records, 10 optimizer steps at
   the largest fitting micro-batch, lr 2e-5. Gate: final loss <
   initial loss. A non-decreasing loss means the probe training loop
   is broken, not that the model is bad.
3. **Truncation audit:** tokenizes the training corpus at
   `max_seq_len` 320; counts truncated records and counts ANNOTATED
   SPANS whose tokens fall beyond 320 (annotated labels lost).
   Gate: 0 annotated labels lost. (Question-level issue/fact labels
   cannot be attributed to truncated tokens, so the span-based count
   is the auditable proxy; the truncated-record count is reported
   alongside it.)

The probe is a **standalone encoder + heads** (AutoModel mmBERT-base
+ linear heads sized 11×4 / 28×4 / enums, with span-attention pooling
over the single full-question encoding). It measures the ADOPTED
1-pass architecture — which Lane B has already landed as the default
in `src/laya_v7_classifier.py` (`pooling="one_pass"`, line 264; the
9-pass path remains as a fallback). The script detects and reports
which architecture the repo classifier currently implements, so the
probe and the repo code cannot silently diverge.

## Expected-gate table (all must pass for A6 PASS)

| Gate | Target | Source |
|---|---|---|
| Peak memory at micro-batch 8 | **< 6.5 GB** | Gemini gate; the RTX 5050 has 8 GB — on a 16 GB Colab T4 the same number is the portability target, not the cap |
| Largest fitting micro-batch | **8** (target; else record the fallback) | GPT-RERUN §4 |
| Loss decreases on the 32-example subset | yes (final < initial) | smoke-test validity |
| Truncation events | recorded (count + % of records) | diagnostic |
| Annotated labels lost to truncation | **0** | plan A6 |

Exit codes: 0 = all gates pass; 1 = a gate fails (report names the
failing gate and the fallback micro-batch); 2 = torch/transformers
missing (run on Colab).

## Run on Colab (exact command)

```bash
python3 scripts/vram_smoke.py --backbone jhu-clsp/mmBERT-base \
    --train-file data/synthetic_v7_1/train.jsonl \
    --max-seq-len 320 --json-out /tmp/vram_smoke.json
# For a fast first pass, add --audit-limit 2000 (truncation audit on
# a 2,000-record sample instead of all 7,500).
```

## Notes for Lane B

- If micro-batch 8 OOMs, the training script must **fail loudly on
  OOM and suggest the fallback** (GPT-RERUN §4 / impl_swarm_state
  GPT-RERUN correction 1) — never silently change the batch size.
  The fallback order is 4 → 2 → 1 with grad-accum adjusted to keep
  the effective batch at 16 (8×2, 4×4, 2×8, 1×16).
`max_seq_len` 320 is now the train script's default as well (Lane B,
`ClassifierConfig.max_seq_len`, line 254), not just the probe's. The
truncation audit is the check that 320 loses no annotated labels — if
it does, the answer is overlapping windows / overflow processing,
never silent truncation.
- VRAM numbers from the T4 run do not transfer 1:1 to the RTX 5050
  (different total memory, different allocator behaviour). The
  < 6.5 GB gate is the portability target that makes the same config
  safe on both; record the T4 peak AND, when the RTX run happens,
  the RTX peak.
