# Phase A gate A5 — Grouped validation split audit

- **Lane:** A (implementation swarm)
- **Date:** 2026-11-27
- **Verdict: FAIL as a grouped split — the split is random row-level,
  not grouped.** The limitation is recorded here. **The frozen split
  is NOT rewritten**: `data/synthetic_v7_1/validation.jsonl` sha256
  stays `7640d067c28abf539131dbcc891e4bdffedf62bbef4a7d66c1659bb96d07e58e`
  (recomputed from disk during this audit — matches the manifest).
  All numbers below were computed on this VM from the corpus files.

## What the corpus actually carries

Records have exactly these top-level fields: `id`, `lang`, `text`,
`issues`, `facts`, `enums`, `spans`, `meta`. There is **no
`template_family_id`, no `grammar_rule_id`, no `scenario_family`, no
`template_id`, no `family_id`, no `scenario_id`** field anywhere in
train (7,500) or validation (500). The only grouping signal is
`meta = {cluster, blocks, split}`:

- `cluster`: one of core / combo / hn_a–hn_h / neg / conflict.
- `blocks`: the template-block name(s) that generated the record
  (e.g. `['quoted_maintenance']`, `['multi_ask_maint_stridhan',
  'custody_mother']`).

## How the split was made (code, not assumption)

`scripts/build_synthetic_corpus.py::generate` (lines ~1892–1900):

```python
rng.shuffle(records)
val = records[:N_VAL]
train = records[N_VAL:]
```

A single global random shuffle, then the first 500 records become
validation. No grouping key is consulted at split time. The split is
row-level i.i.d. by construction.

## Measured overlap (train 7,500 vs validation 500)

| Overlap measure | Result |
|---|---|
| Template blocks in validation also present in train | **136 / 136 (100%)** — every validation block appears in train; only 9 blocks are train-only |
| Validation records whose exact `meta.blocks` signature appears in train | **500 / 500 (100%)** |
| Validation records whose requested-issue+fact label combination appears in train | **500 / 500 (100%)** (81 distinct combos in train, 79 in validation) |
| Validation records whose FULL label tuple (issues + facts + enums) appears in train | **500 / 500 (100%)** |
| Validation records with a same-(blocks, full-labels) sibling in train in a DIFFERENT language | **500 / 500 (100%)** — translation siblings cross the split |
| Validation records sharing ≥1 word 8-gram with train | **489 / 500 (97.8%)**; 8,012 shared 8-grams (train has 40,177 distinct 8-grams) |
| Per-cluster block containment | every cluster's validation blocks ⊆ train blocks (core 43, combo 50, hn_f 17, hn_c 15, neg 12, hn_d 10, hn_b 9, hn_e 8, hn_h 6, hn_g 5, conflict 4, hn_a 3) |

Two honesty notes on the proxies: (1) the (blocks, full-labels)
signature space is coarse (only 199 distinct block-signatures in
train), so 500/500 on that proxy partly reflects coarse signatures —
but combined with the shuffle code and the 136/136 block overlap, the
conclusion does not depend on the proxy. (2) The 8-gram overlap is
*expected* for template-generated text (shared template phrasing) and
is not itself leakage of test-bank content — the filed leakage report
already records 0 8-gram overlap vs the sealed/16-Q/brutal banks
(max cosine 0.8269). The problem here is different: **the validation
split measures in-grammar fit, not generalisation to unseen scenario
families**, because the same families generate both sides.

## Consequence

- The frozen-split numbers (261/500 = 52.2% evidence mode) are a
  valid *progress* metric on the frozen file, but they are optimistic
  as a predictor of unseen-human-question accuracy: the model can
  memorise template structure (the same blocks, the same label
  combinations, the same phrasing in another language) and score
  higher on validation than on genuinely new scenarios. This is the
  "Val-500 i.i.d. grammar optimism" failure mode (Gemini Q4.4,
  GPT-RERUN §11): expect a ~12–15 point gap to human text.
- The plan's A5 pass check ("if related scenario families cross the
  split, record the limitation and create an additional genuinely
  group-disjoint development set") is therefore the operative outcome:
  **limitation recorded; a group-disjoint dev set is still to be
  built** (see below). The frozen split itself is untouched.

## What is needed (not done here — needs a coordinator decision)

1. **An additional genuinely group-disjoint development set** built
   from template-block signatures (the only family proxy the corpus
   has): hold out whole `meta.blocks` signatures — and, better, whole
   block *families* (blocks sharing a stem, e.g. all `kn_*` variants
   of one scenario) — from training, and evaluate on them. This set
   must be a NEW file (e.g. `data/synthetic_v7_1/grouped_dev.jsonl`)
   with its own manifest entry; it must NOT replace
   `validation.jsonl` and must NOT be presented as comparable to the
   frozen-split numbers.
2. **Do not use the sealed-bank similarity index repeatedly as a
   training-data optimisation feedback loop** (plan A5). The grouped
   dev set is the feedback mechanism; the sealed sets stay sealed.
3. **Future corpus builds (Lane 02 / Phase C):** emit a real
   `template_family_id` (and `scenario_family` / `scenario_id`)
   per record at generation time, and split by it. The current
   `meta.blocks` is a usable but coarse proxy — it cannot distinguish
   two scenarios built from the same block with different facts.
4. **Threshold/calibration work (Lane B / Lane 10):** OOF calibration
   must use grouped folds (Train-7500 only, never Val-500 — GPT-RERUN
   §6) built on block signatures, not random folds, or the OOF
   thresholds inherit the same optimism.
