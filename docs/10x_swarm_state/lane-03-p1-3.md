# Lane 03 — V71-P1-3 Supervised Multi-Head Stage 0/1 Classifier — STATUS

- Lane: 03 (P1-3, code only, no training)
- Files owned (only these touched): `src/laya_v7_classifier.py` (new),
  `scripts/train_v71_classifier.py` (new)
- Status: DONE (code complete, verified torch-free paths only — see below)
- No other lane's files edited; no frozen files touched; no git commands run.

## What was built

### `src/laya_v7_classifier.py`
Unified multi-head teacher over a config-chosen encoder backbone:
- `ClassifierConfig` — backbone, max_seq_len (192), max_clauses (8), dropout,
  freeze/LoRA flags, `tau_neg` (0.5), per-head temperatures, loss weights.
- `build_model(config)` — one shared encoder + `issue_head` [11,4],
  `fact_head` [28,4], `enum_heads` (claimant_sex [F,M,U], claimant_role
  [spouse,parent,child,other], modality_time [present,past,future,hypothetical,quoted]),
  `clause_gate_head` (per-clause [denied, hypothetical, third_party] logits),
  `span_attn` (token-level attention weights = evidence-span mass) and a
  per-clause `span_head` (span-presence logit, BCE-trained).
- Inputs: `[CLS] full_question [SEP]` + batched `[CLS] clause_i [SEP]`.
  No regex anchor vetoes anywhere in the model path (plan §1.2).
- `fuse_issue_probs(...)` — calibrated `max(full_p, cmax_p)` for the
  `requested` intent only; a clause is excluded from the clause max-pool iff
  any of its three gate sigmoids >= `tau_neg`. The veto applies to that clause
  alone — sibling clauses are unaffected. Other intents use the full encoding;
  the row is renormalised.
- `split_clauses(text)` — pure-python sentence/clause splitter with char
  offsets; handles `. ! ?`, `;`, Kannada danda (।/॥), newlines; overflow
  clauses merge into the last slot so no text is lost.
- `load_corpus_jsonl(path)` / `encode_labels(record)` — contract C2 loader
  (pure python, no torch): missing issues -> `uncertain`, missing facts ->
  `unknown`, missing enums -> `U`/`other`/`present`; unknown keys counted in
  the report and ignored (strict mode available). `modality_time="general"`
  (laya_v7_schema spelling) maps to `present`.
- `predict_text(model, tokenizer, text)` — one-question inference returning
  plain-JSON `{issues, facts, enums, spans, clauses}`; top-3 attention-mass
  spans mapped back to char offsets via the tokenizer offset mapping.
- `save_checkpoint` / `load_checkpoint` (state_dict + config JSON).
- Torch/transformers are imported lazily and guarded: importing the module,
  splitting clauses, loading a corpus and label encoding all work with NO
  torch installed; `build_model`/`predict_text`/training raise a clear
  `RuntimeError` pointing at the RTX 5050 run command instead of faking a run.

### `scripts/train_v71_classifier.py`
- Full argparse (`--data` + `--val-frac` split, or `--train-file`/`--val-file`;
  `--backbone`, `--epochs`, `--batch-size`, `--grad-accum`, `--lr`,
  `--max-seq-len`, `--max-clauses`, `--loss-weights`, `--class-weights`,
  `--freeze-backbone`, `--lora`, `--grad-checkpoint`, `--tau-neg`, `--seed`,
  `--device`, `--fp16`, `--output-dir`, `--smoke`, `--check-data-only`).
- Multi-head weighted CE loss (issue/fact/enum/gate/span BCE), optional
  inverse-frequency class weights (clipped [0.25, 4.0]), AdamW + linear
  warmup + cosine decay, fp16 autocast + GradScaler, grad accumulation.
- Eval: hand-computed macro/micro-F1 per head (no sklearn dependency) +
  pooled `requested`-class recall (the recall-critical number: a missed
  `requested` is a silent section drop downstream). Per-epoch JSONL log.
- Checkpointing: `best/` (best mean val macro-F1 over issue+fact heads:
  `model.pt` + `config.json` + `label_maps.json`) and `last/`; data report
  saved to `data_report.json`.
- `--check-data-only` works with no torch (verified on this VM).
- `--lora` is genuinely wired via peft (`LoraConfig` r=8; ModernBERT target
  `Wqkv`, DeBERTa-v3 target `query_proj/key_proj/value_proj`; heads kept
  trainable via `modules_to_save`). Needs `peft` installed on the GPU box.

## Exact RTX 5050 training command

From the repo root, after Lane 02 produces the corpus:

```bash
python scripts/train_v71_classifier.py \
    --data data/synthetic_v7_1/corpus.jsonl \
    --val-frac 0.10 --backbone answerdotai/ModernBERT-large \
    --epochs 5 --batch-size 4 --grad-accum 2 --lr 2e-5 \
    --max-seq-len 192 --max-clauses 8 \
    --output-dir models/v71-classifier --device cuda --fp16 \
    --grad-checkpoint --seed 42
```

If Lane 02 emits separate files, replace `--data ... --val-frac 0.10` with
`--train-file data/synthetic_v7_1/train.jsonl --val-file data/synthetic_v7_1/val.jsonl`.
Memory note: RTX 5050 has 8 GB VRAM; batch 4 + grad-accum 2 + grad-checkpoint
is the safe default. If OOM persists: `--batch-size 2 --grad-accum 4`, or
`--freeze-backbone`, or `--lora`.

Expected outputs: per-epoch train loss (total + per head) and val
macro/micro-F1 per head + `requested` recall printed to stdout;
`models/v71-classifier/best/{model.pt,config.json,label_maps.json}`,
`models/v71-classifier/last/{model.pt,config.json}`,
`models/v71-classifier/train_log.jsonl`, `models/v71-classifier/data_report.json`.
Exit bar (plan §1.3): synthetic held-out macro/micro-F1 >= 0.95 per head;
`requested` recall >= 0.98 before any sealed evaluation. For the 5-fold CV
claim, repeat with Lane 02's fold files via `--train-file`/`--val-file`
(this script runs one split per invocation).

## Architecture decisions (deviations / choices made, all documented in code)
1. Backbone default `answerdotai/ModernBERT-large` (Apache-2.0); DeBERTa-v3-large
   (MIT) accepted; `PIXMELT/laya` accepted as a config choice but the code
   REFUSES to train on it until its license is verified (raises ValueError).
2. 11th issue is `procedure` (forum/how-to questions) — the plan says 11 issues
   but never enumerates them; the evidence module's 10 triggers + `procedure`
   is the natural set (see Assumptions).
3. 28 facts exclude enum-valued keys (`claimant_sex`/`claimant_role` — separate
   enum heads), the scope meta-fact (`in_scope`), and derived/meta keys
   (`no_dispute_empty`, `first_demand_never_made`, `forum_question_asked`,
   `procedure_how_to_asked`, `interim_only_asked`,
   `interim_unpaid_with_joint_or_parallel`). Canonical interim name is
   `interim_asked` (the graph's dead key, L453/L468); loader aliases
   `interim_only_asked` -> `interim_asked`.
4. Gate weak labels: `hypothetical` is set on ALL clauses when modality is
   hypothetical/quoted, `third_party`/`denied` only from explicitly labelled
   spans. Without span attribution the gate learns from clause text. This is
   a weak-label approximation — Lane 02 can strengthen it by emitting
   per-clause gate labels if its schema supports them.
5. Fusion applies only to the `requested` class (plan wording); other intents
   come from the full encoding. Temperatures default to 1.0 (neutral);
   Lane 10 fits them on held-out dev.
6. F1 is hand-computed (no sklearn) so the training box needs only
   torch + transformers (+ peft for `--lora`).

## Assumptions about Lane 02's schema (contract C2)
- C2 as written in `docs/10x_swarm_state.md`: `{id, lang, text, issues, facts,
  enums, spans}`. Coded against exactly that.
- Assumed `issues`/`facts` are `{name: label-string}` maps; `enums` is
  `{claimant_sex, claimant_role, modality_time}` of plain strings; `spans`
  are `{start, end, text}` dicts with optional `clause_idx` and `label`.
- Assumed the corpus covers all 11 issues / 28 facts with the names in
  `ISSUES`/`FACTS` in `src/laya_v7_classifier.py`. If Lane 02's actual names
  differ (e.g. no `procedure` issue, different fact set, or span shape),
  the loader logs every unknown key in its report and defaults the rest —
  training will still run, but the coordinator must reconcile the vocab
  (ideally by editing the `ISSUES`/`FACTS` constants + aliases in the
  classifier module) before the GPU run, or the model will train on
  `uncertain`/`unknown` defaults for the mismatched labels.
- Assumed corpus path `data/synthetic_v7_1/corpus.jsonl` (or
  `train.jsonl`/`val.jsonl`); the script accepts either layout.

## Verification done on this VM (no torch / no GPU)
- `python3 -m py_compile src/laya_v7_classifier.py scripts/train_v71_classifier.py` — OK.
- `--check-corpus` and `--check-data-only` on a 5-record sample corpus in
  `/tmp` (EN + KN, third-party + hypothetical + unknown-key cases): 5/5 loaded,
  unknown keys (`telecom`, `rent_dispute`, enum `X`, modality `general`)
  correctly reported, not fatal; clause split, label encoding and gate weak
  labels inspected and correct (S-003 third-party gate [0,0,1] on clause 0;
  S-004 hypothetical gate on both clauses).
- `build_model()` without torch raises the intended `RuntimeError`;
  training mode without torch exits 2 with the RTX-5050 instruction.
- Guardrails: `python3 tests/test_graph_v4.py` PASS (34 sections / 66 nodes /
  99 edges, 7/7 frozen hashes intact); `python3 tests/test_prose_renderer_v2.py`
  PASS (246 cases, Fp=0, 15/15 mutants).
- NO training run attempted or faked; no neural execution of any kind.

## Blockers / what needs GPU or humans
- BLOCKED on Lane 02: no corpus exists yet (`data/` does not exist in the
  working copy). Training cannot start until `data/synthetic_v7_1/*.jsonl`
  lands; the exact command above assumes that path.
- NEEDS GPU (RTX 5050): the training run itself, plus verification that the
  model loads, a `--smoke` pass, and the F1 >= 0.95 / requested-recall >= 0.98
  exit check. Nothing about model quality is known yet — no scores exist.
- NEEDS HUMAN/COORDINATOR: (a) reconcile the 11-issue / 28-fact vocab with
  Lane 02's actual corpus at merge; (b) Lane 06 license audit before any run
  on `PIXMELT/laya` (code already blocks it); (c) temperature calibration
  (`tau_neg`, per-head temperatures) is Lane 10's job on held-out dev.
- OPEN (mine, for follow-up): the corpus `spans` schema is the least certain
  part of C2 — if Lane 02's spans carry no `clause_idx`/`label`, the gate and
  span heads train on weaker labels; the code tolerates that but the
  coordinator should confirm the span shape.
