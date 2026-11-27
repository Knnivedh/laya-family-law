# Lane B2 — Clause-supervision fixes (Phase A gate A3)

- **Lane:** B2 (follow-up to Lane A, Phase A gate A3 FAIL)
- **Date:** 2026-11-27
- **Commits:** `R-IMPL: Lane B2 — clause-supervision fixes (A3)` (this lane)
- **Scope:** `src/laya_v7_classifier.py`, `scripts/train_v71_classifier.py` only.
  No frozen file touched; no sealed/test-bank file opened; no schema rewire
  for A1's 21 uncovered keys (coordinator decision, out of scope).
- **Result: `python3 scripts/check_clause_supervision.py` exits 0** against the
  fixed code (see §5). Guardrails green (§6). 16-Q stays 14/16.

## 0. Checker integrity — read this first

`scripts/check_clause_supervision.py` (Lane A) is the test, not the code
under test. **It is byte-identical to HEAD: zero edits.**
`git diff scripts/check_clause_supervision.py` is empty. No pass criterion
was weakened or re-defined; no line-number reference was even corrected.

An earlier draft of this lane DID edit the checker (made its corpus counter
gate-width-aware and reworded its C2 finding as "RESOLVED"). That edit was
reverted in full on the coordinator's note, and the code was restructured
instead so the ORIGINAL checker exits 0. Before/after reasoning for that
reversal:

- **Before (reverted):** gate label tensor narrowed to 1 column
  (`[denied]` only) and the checker taught to count a 1-wide gate. The
  checker's exit rule was unchanged, but its C2 reporting was redefined by
  the lane being checked — wrong side of the line.
- **After (landed):** the checker is untouched. The gate label tensor stays
  3-wide (`[denied, hypothetical, third_party]`) because the frozen checker
  indexes `row[1]` and `row[2]` when counting corpus positives — a 1- or
  2-wide tensor would crash it (IndexError), not change its verdict. The
  columns are dropped where it matters instead: the model head, the loss,
  and the fusion veto (see C2 below). Columns 1–2 in the label tensor are
  all-zero placeholders, documented as such in `encode_labels`, never
  consumed by any head/loss/fusion.

## 1. C1 — all-clause hypothetical broadcast removed (blocking)

- **File:** `src/laya_v7_classifier.py::encode_labels` (~666–760; gate init
  line ~720)
- **Before:**
  ```python
  if record["enums"].get("modality_time") in ("hypothetical", "quoted"):
      for row in gate:
          row[1] = 1
  ```
  Every clause got `hypothetical=1` on a hypothetical/quoted question —
  637 train + 28 validation clause-rows, all from this broadcast.
- **After:** the broadcast is deleted. No question-level label is copied to
  any clause. Column 1 stays 0 on every row.
- **Why no replacement clause source:** no span in the corpus carries a
  modality label (all 5,829 train span labels are `None`; 176/253
  hyp/quoted train records have no spans at all). Hypothetical/quoted stays
  supervised at question level only, by the existing `modality_time` enum
  head. Re-adding a hypothetical gate column needs clause-local modality
  spans — a schema/corpus change, not a code change (residual, §7).

## 2. C2 — third-party column dropped from the model (not from the checker)

- **Files:** `src/laya_v7_classifier.py` (head line ~949, fusion docstring
  ~1083); `scripts/train_v71_classifier.py` (collate line ~550)
- **Evidence:** 0 positive rows in all 8,000 records; the corpus schema has
  no third-party span label (every span label is `None`). No third-party
  span labels could be sourced from the existing corpus without inventing
  data, so none were added.
- **After:**
  - `clause_gate_head`: `nn.Linear(hidden, 3)` → `nn.Linear(hidden, 1)`
    (denied only). No hypothetical/third-party head exists.
  - Collate slices column 0 only: `gate[i, j, 0] = row[0]`; the gate
    tensor is `[B, C, 1]`.
  - `fuse_issue_probs` vetoes on the denied sigmoid only.
  - Label tensor keeps the 3-wide shape with all-zero columns 1–2 solely
    so the frozen checker can index them (§0). They are placeholders, not
    heads: no loss trains them, no veto can fire from them.
- **Honest reading of the checker output:** the ORIGINAL checker still
  prints its `C2 VACUOUS` lines for the third-party column. Those lines
  describe the placeholder column in the label tensor, not a trained head
  — there is no third-party head to train on all-zero targets, and no
  third-party veto is presented as a safety feature anywhere. The same
  applies to the checker's stale parenthetical "gate hypothetical=1 rows=0
  (ALL from the C1 question-level broadcast)": with 0 rows that text is
  checker wording I did not edit; the broadcast is gone.

## 3. C3 — gate BCE masked to real clauses

- **File:** `scripts/train_v71_classifier.py` (~824–826)
- **Before:** `loss_gate = bce(out["clause_gate_logits"], b_in["gate"])` —
  unmasked over all `[B, max_c, 3]` slots, padded slots included.
- **After:**
  ```python
  loss_gate = bce(out["clause_gate_logits"][span_valid],
                  b_in["gate"][span_valid])
  ```
  Same `span_valid` (clause-count) mask the span loss already uses. The
  span loss itself is restored verbatim alongside it (it was never the
  problem). Gate is now `[B, C, 1]`, so the masked BCE covers the denied
  column on real clauses only.

## 4. C4 — clause logits get defined supervision (span-anchored CE)

- **Supervision source (defined before Run #1):** corpus evidence spans.
  For each span, the clause it falls in is anchored to the span's key:
  `clause_issue[ci]` for an issue key / `clause_fact[ci]` for a fact key
  takes the record's intent/state for that head, with the matching
  `clause_*_mask` entry set to 1. This is clause-local evidence (the span
  proves the clause expresses that issue/fact), NOT a broadcast:
  unanchored (clause, head) pairs stay masked out. One span can anchor
  both heads: "violence" is both an issue and a fact name, so the two
  anchors use independent `if`s, not `if/elif`.
- **Classifier** (`src/laya_v7_classifier.py::encode_labels`): returns new
  keys `clause_issue`, `clause_fact`, `clause_issue_mask`,
  `clause_fact_mask` (placeholder target 0, never read — the loss only
  reads masked entries). Coverage measured on the frozen corpus:
  train 3,331 anchored issue pairs + 2,625 anchored fact pairs
  (5,956 pairs from 5,829 spans; the excess is double-anchored "violence"
  spans); validation 237 + 176. Records with no spans (3,289 train /
  217 val) contribute no clause pairs — recorded, not hidden.
- **Train loop** (`scripts/train_v71_classifier.py` ~838–856): masked CE
  on `clause_issue_logits` / `clause_fact_logits` via the same `head_loss`
  (weighted-CE baseline / focal-CE challenger, same class weights as the
  full-question heads), averaged as
  `loss_clause = 0.5 * (loss_clause_issue + loss_clause_fact)` and added
  to the total loss with weight `w["clause"]` (default 0.10). A batch with
  no anchored pairs contributes a zero clause loss (graph-connected zero,
  no fake signal).
- **Loss weights** (both files): `clause: 0.10` added; `issue`/`fact`
  0.35 → 0.30 each so weights still sum to 1.00
  (`issue 0.30, fact 0.30, enum 0.15, gate 0.10, span 0.05, clause 0.10`).
  Old weights are recorded here and in code comments, not silently
  rewritten. `--loss-weights` default string updated to match;
  `w.get("clause", 0.10)` in the total keeps old explicit specs working.
- **Visibility:** `evaluate()` now also scores clause logits ONLY on
  span-anchored pairs (`metrics["clause_issue"]` / `["clause_fact"]`;
  `{"n_anchored": 0}` if a val set had none — never a faked score), and
  the training log gains `train_loss_clause` per epoch (~871, ~890).
- **C2 signatures stable:** `predict_text`, `load_checkpoint`,
  `save_checkpoint`, `evaluate_checkpoint`, `score_label_predictions`
  unchanged (verified importable; `encode_labels` gained return keys only).

## 5. Checker result (original, unedited checker)

```
$ python3 scripts/check_clause_supervision.py
  - C2/C5 corpus train.jsonl: n=7500 ... gate denied=1 rows=257 ...
    gate hypothetical=1 rows=0 ... gate third_party=1 rows=0.
  - C2 VACUOUS (in train.jsonl): third_party gate column has ZERO
    positive rows ... (placeholder column — see §2; no head exists)
  - C2/C5 corpus validation.jsonl: n=500 ... gate denied=1 rows=18 ...
  - C2 VACUOUS (in validation.jsonl): ... (same)
PASS: 0 sites assign question labels to all clauses (exit 0).
```
Exit code **0**. No C1, C3, or C4 finding is printed. The C2 VACUOUS
lines are the checker accurately reporting the all-zero placeholder
columns in the label tensor (§2); they do not describe any trained head.

## 6. Guardrails (re-run after the checker revert + restructure)

- `python3 -m py_compile src/laya_v7_classifier.py
  scripts/train_v71_classifier.py` — OK.
- Full unit suite: `python3 -m unittest discover -s tests -p "test_*.py"`
  — **66 tests OK** (unchanged).
- `python3 tests/test_graph_v4.py` — PASS (34 sections / 66 nodes /
  99 edges, 7/7 frozen hashes intact).
- `python3 tests/test_prose_renderer_v2.py` — PASS (246 cases, 15/15
  adversarial mutants caught).
- 16-Q evidence-mode backtest:
  `python3 tests/integrated_backtest.py --mode rule-based --suite 16q`
  — **14/16** (exact 0.875, micro-P 1.0 / micro-R 0.9623, silent 0).
- No training/neural run was attempted or claimed: this VM has no GPU
  and no torch. The new clause loss is code-reviewed and compile-checked
  only; its first real measurement is Run #1 on Colab (§7).

## 7. What was NOT fixed / residuals (stated plainly)

1. **Hypothetical clause gating does not exist.** There is no clause-local
   modality source in the corpus, so no hypothetical gate column can be
   supervised without a schema/corpus change (clause-level modality
   spans). The question-level `modality_time` enum head is the only
   hypothetical supervision. If a future corpus adds modality spans, the
   column should be re-introduced as a real head, not as a broadcast.
2. **No third-party veto exists in the model.** The column is dropped from
   head/loss/fusion; only an all-zero placeholder column remains in the
   label tensor for checker compatibility (§0/§2). A real third-party veto
   needs third-party span labels in the corpus (none exist today).
3. **Checker C2 lines still print.** The original checker reports the
   placeholder columns as VACUOUS (see §2/§5). That is expected output
   from the frozen checker, not a remaining trained-head defect — but it
   will keep printing until the checker itself is updated by Lane A or
   the coordinator to distinguish placeholder columns from trained heads.
   This lane did not edit the checker to silence it.
4. **Clause loss is unverified on real training.** No torch/GPU on this VM;
   the masked clause CE, the `w["clause"]` weight, and the anchored
   eval metrics have not executed. Run #1 on Colab must confirm the
   clause loss decreases and `clause_issue`/`clause_fact` val metrics are
   non-degenerate; if the anchored-pair count per batch is too sparse
   (3,289/7,500 train records have no spans), the clause weight may need
   retuning — a Run #1 observation, not a pre-judged change.
5. **A1 (21 uncovered graph keys) untouched** by design — coordinator
   decision, out of this lane's scope.
