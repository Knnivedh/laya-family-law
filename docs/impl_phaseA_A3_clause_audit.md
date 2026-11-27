# Phase A gate A3 — Clause-supervision audit

- **Lane:** A (implementation swarm)
- **Date:** 2026-11-27
- **Checker:** `scripts/check_clause_supervision.py` (pure python, no torch)
- **Verdict: FAIL** — 1 site assigns question-level labels to all
  clauses. Exit code 1.
  (Re-run: `python3 scripts/check_clause_supervision.py` — exit 1.)

## Every clause-loss site (audited files: `src/laya_v7_classifier.py`,
## `scripts/train_v71_classifier.py`)

| # | Site | Loss / supervision source | Verdict |
|---|---|---|---|
| 1 | `classifier.py::encode_labels`, lines ~678–680 | Question-level enum `modality_time` broadcast to every clause | **FLAG — C1 COPY** (see below) |
| 2 | `classifier.py::encode_labels`, gate `denied` column | Span-derived: a span naming a fact/issue the corpus marks `denied` marks its clause | Legitimate clause-local supervision |
| 3 | `classifier.py::encode_labels`, gate `third_party` column | No source — corpus schema has no third-party span label; 0 positive rows in all 8,000 records | **C2 VACUOUS** (see below) |
| 4 | `classifier.py::encode_labels`, `span_mask` | Span-derived: 1 iff a corpus span falls in the clause | Legitimate clause-local supervision |
| 5 | `train.py:752`, `loss_gate` | BCE on `clause_gate_logits` vs `gate` — over ALL `[B, max_c, 3]` slots including padding | **C3 UNMASKED-PAD** (see below) |
| 6 | `train.py:757–760`, `loss_span` | BCE on `clause_span_logits` vs `span_mask`, masked by `span_valid` to real clauses | Legitimate (masked) |
| 7 | `train.py:745–747`, `loss_issue` / `loss_fact` (via `head_loss`, weighted CE / focal CE) | CE on the FULL-question logits only | Legitimate as question-level loss; NOT clause supervision |
| 8 | `classifier.py` forward, lines ~994–1014; `train.py:694–695` (eval), `classifier.py::predict_text` ~1114–1116 (inference) | `clause_issue_logits` / `clause_fact_logits` computed but never in any loss; consumed only by fusion (`fuse_issue_probs`) | **C4 NO-CLAUSE-LOSS** (see below) |
| 9 | `train.py` `ClauseDataset` / `collate` | Question-level `encode_labels()` output stored once per record; no per-clause label tensors exist | By design (no copy) — but see C4 |

No other clause-loss site exists in either file: `grep` for
`clause_issue_logits` / `clause_fact_logits` finds only the forward
computation (site 8) and the fusion use; `loss_issue` / `loss_fact`
reference only the full logits.

## C1 — the flagged copy (gate FAIL)

`src/laya_v7_classifier.py::encode_labels` (lines ~678–680):

```python
if record["enums"].get("modality_time") in ("hypothetical", "quoted"):
    for row in gate:
        row[1] = 1
```

If the question-level enum is `hypothetical` or `quoted`, EVERY
clause gets `gate[hypothetical] = 1` — including requested clauses in
mixed-modality questions (e.g. "If I file for divorce [hypothetical],
can I still claim my stridhan and child maintenance [requested]?").
The gate then learns "requested clause ⇒ hypothetical" on those
records, which is exactly the GPT-RERUN warning: a hypothetical
clause is not automatically irrelevant, and a question-level modality
must never be stamped onto every clause.

Measured on the 8,000-record corpus (via the checker): **637 train
clause-rows + 28 validation clause-rows** carry `hypothetical=1`, and
**all 637 + 28 come from this broadcast** (139 hypothetical + 114
quoted train records × all their clauses; 2 hypothetical + 11 quoted
validation records). There is no clause-local source for any of them.

## C2 — vacuous third-party supervision

Gate column 2 (`third_party`) has **0 positive rows in train (7,500)
and 0 in validation (500)**. The corpus schema carries no
third-party span label (the `encode_labels` docstring admits this:
"this stays 0 unless Lane 02 adds one"). BCE against all-zero targets
trains the head to always predict ~0, so the third-party veto in
`fuse_issue_probs` can never fire. A never-firing veto must not be
presented as a safety feature.

## C3 — gate loss unmasked over padded slots

`scripts/train_v71_classifier.py:752`:

```python
loss_gate = bce(out["clause_gate_logits"], b_in["gate"])
```

This BCE covers the full `[B, max_c, 3]` tensor. Padded clause slots
have all-zero gate targets and logits computed from pad tokens, and
they contribute loss on every step. The span loss immediately below
(:757–760) IS masked (`span_logits[span_valid]`); the gate loss is
not. Fix: mask the gate BCE by clause counts exactly as the span loss
is masked.

## C4 — clause predictions with zero clause supervision

`clause_issue_logits` / `clause_fact_logits` are computed in
`forward` (classifier.py ~994–1014) and used by fusion — in
`train.py:694–695` (`evaluate`) and in `predict_text` (~1114–1116) —
but no loss term ever references them (site 7's `loss_issue` /
`loss_fact` use only the full-question logits). This is the mirror
image of the C1 error: not question labels copied to clauses, but
clause predictions with no clause supervision at all. Note the 1-pass
nuance (Lane B has landed 1-pass as the default, `pooling="one_pass"`):
clause vectors now come from span-pooling the SAME trained encoding
rather than separate clause encodings, so the encoder itself is
trained — but still no loss is ever computed on the clause logits, so
the fused `requested` score rests on clause predictions with zero
direct clause supervision. The span-pooled heads need a defined
supervision source — spans or MIL — before Run #1.

## C5 — span coverage (informational)

- Train: 3,289 / 7,500 records carry NO spans; validation: 217 / 500.
  The span head trains on the remaining 4,211 / 283 records only
  (5,568 train clause-rows with `span_mask=1`, 383 validation).
- Gate `denied=1` rows (span-derived, legitimate): 257 train, 18
  validation. These are the only clause-local gate positives with a
  real supervision source besides the C1 broadcast.

## Lane B fixes required (file + line)

1. **C1 (blocking):** `src/laya_v7_classifier.py::encode_labels`
   ~678–680 — remove the all-clause broadcast. Hypothetical/quoted
   must come from clause-local evidence (spans, or MIL where spans
   are unavailable); where clause-level labels are unavailable, mask
   that gate loss and rely on question-level supervision. Do not
   replace the broadcast with a per-clause copy of any other
   question-level label.
2. **C2:** `src/laya_v7_classifier.py::encode_labels` gate column 2 —
   either Lane 02 adds third-party span labels to the corpus, or
   drop the column (and the third veto input in `fuse_issue_probs`).
   Do not ship a head trained on all zeros.
3. **C3:** `scripts/train_v71_classifier.py:752` — mask the gate BCE
   to real clause counts (`span_valid`-style mask, as at :757–760).
4. **C4:** decide the clause-supervision source for the adopted
   1-pass architecture before Run #1 (annotated evidence spans or
   MIL, per GPT-RERUN §4) and wire a loss to it; fusion must not
   max-pool over unsupervised clause scores.
5. **C5:** note the 3,289 span-less train records in the training
   report; the span head's effective training set is 4,211 records,
   not 7,500.
