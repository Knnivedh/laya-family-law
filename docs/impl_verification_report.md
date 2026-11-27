# Lane F — Independent Verification Report: LAYA v7.1 Implementation Swarm

- **Verifier:** Lane F (independent; no code edited)
- **Date:** 2026-11-27 (evening IST)
- **Working copy:** `~/workspace/laya-v71-work`
- **HEAD verified:** `34e407a` ("R-IMPL: coordinator — correct Lane A verdicts in shared state …; Lane B2 spawned")
- **Method:** every number below comes from a command I ran on this VM (no GPU, no torch). Commands are cited with each result. No sealed text was opened at any point; sealed files were only refused by the harness (exit 2) and named in notebook markdown.

## HEAD-movement note (read first)

HEAD moved twice during this verification: `ce3d021` (at session start, with 3 uncommitted files) → `4573615` (Lane A, corrections to A3/A4/A6 docs + checkers for the landed Lane B state) → `34e407a` (coordinator, corrected shared-state Lane A verdicts + Lane B2 spawned). The only changes across those two commits are **documentation and checker line numbers** — no pipeline, classifier, runtime, harness, or notebook code changed. All verification runs used content identical to current HEAD; the two guardrails were re-run at `34e407a` after the last move. The working tree is clean at report time (`git status` empty).

## Verdict table

| # | Item | Verdict |
|---|---|---|
| 1 | Guardrails: `test_graph_v4.py`, `test_prose_renderer_v2.py`, unittest 66 OK | **VERIFIED** |
| 2 | Frozen SHAs: 7 frozen files byte-identical to `90e20c5` baseline; validation sha256 `7640d067…` | **VERIFIED** (see note on "7 vs 9" below) |
| 3 | Integrated runtime (Lane C): `--self-test`, 16-Q 14/16 (H6/H14), `--mode classifier` no-checkpoint exit 2 | **VERIFIED** |
| 4 | Harness (Lane E): all four suites reproduce; `--suite sealed` exits 2 | **VERIFIED** (with one doc-label finding, F-5) |
| 5 | Lane B classifier: `--check-data-only` 7500/500, py_compile, stable signatures, `weighted_ce` default / `focal_ce` available, OOF Val-500 refusal exit 2 | **VERIFIED** |
| 6a | Lane A A1 graph contract | **VERIFIED AS FAILING** — checker reproduces exit 1, 21 uncovered (task's "expect exit 0" is wrong; see F-1) |
| 6b | Lane A A3 clause supervision | **VERIFIED AS FAILING** — checker reproduces exit 1; both cited violation sites confirmed in committed code (fix sized in §6b) |
| 6c | Lane A A2 oracle | **VERIFIED** — degraded GG 9/16, not the 12/16 in the task/shared state (see F-2); miss list matches the filed doc exactly |
| 6d | Lane A A5 grouped split | **VERIFIED AS FAILING** — 500/500 shared families; but `data/synthetic_v7_1/dev_grouped.jsonl` **does not exist** (task expectation wrong; see F-3) |
| 6e | Lane A A4 tokenizer / A6 VRAM | **VERIFIED AS OPEN** — both scripts exit 2 (no transformers/torch), no numbers, as filed; filed numbers are consistent (there are none to check) |
| 6f | Lane A A7 brief reconciliation | **VERIFIED** — arithmetic checks out from aggregates (see §6f) |
| 7 | Lane D notebook: JSON + nbformat valid, no code cell loads sealed, CPU smoke cells exit 0 | **VERIFIED** |
| 8a | Brutal-230 discrepancy (210 vs 230) | **RECONCILED** — 210/230 independently confirmed; regression claim holds as a measurement, causation unproven (see §8a) |
| 8b | 16-Q rating (9.0 vs 7.6) | **RECONCILED** — honest number is **7.6** (see §8b) |
| 8c | Lane D's two failed execs | **NOT VERIFIABLE from the repo** — no trace in the working copy; nothing in Lane D's deliverables depends on a failed command (see §8c) |
| 9 | Git hygiene | **VERIFIED with findings** — no frozen file touched, no cross-lane file commits except two declared/shared-state touches (see §9) |

---

## 1. Guardrails (re-run)

```bash
python3 tests/test_graph_v4.py
# GRAPH V4 + FROZEN SHA TEST PASS: 34 sections / 66 nodes / 99 edges, 0 dangling edges, 7/7 frozen hashes intact. (exit 0)

python3 tests/test_prose_renderer_v2.py
# PROSE VALIDATION PASS: 246 cases, Fp=0, quality_flags=0, 15/15 adversarial mutants caught, mean=0.0164ms, max=0.133ms (exit 0)

python3 -m unittest discover -s tests -p "test_*.py"
# Ran 66 tests in 0.324s — OK (exit 0)
```

All three match the builders' claims exactly.

## 2. Frozen SHAs

```bash
sha256sum data/synthetic_v7_1/validation.jsonl
# 7640d067c28abf539131dbcc891e4bdffedf62bbef4a7d66c1659bb96d07e58e  (matches the frozen value)

git diff 90e20c5..HEAD -- graph/laya-crpc-bns-section-decision-tree-v2.json \
  graph/laya-crpc-bns-section-decision-tree-v3.json \
  ground-truth/ground-truth-v2-hma27-A.json test-bank/brutal-bank-v1-frozen.json \
  test-bank/sealed/sealed-fresh-20.json test-bank/sealed/sealed-kannada-8.json \
  notebooks/live-laya-colab-test-v6-brutal.ipynb \
  tests/test_graph_v4.py tests/test_prose_renderer_v2.py
# (empty — no diff)
```

Note on counting: the task says "7 frozen files" but lists 9 paths (v2, v3, GT, brutal, 2 sealed, v6 notebook, 2 frozen tests). I diffed **all 9** — all byte-identical to `90e20c5`. The "7/7 frozen hashes" in the graph test is that test's own internal count; it is not a count of the frozen-file list. No frozen file appears in any commit since `90e20c5` (see §9).

## 3. Integrated runtime (Lane C)

```bash
python3 src/laya_integrated.py --self-test        # exit 0
# 3 questions: EN -> sections [bnss-144, pwdva-20], court [Magistrate], escalations [quantum];
# Kannada-script -> sections [], escalations [procedure, court] (known gap, as Lane C filed);
# Kanglish -> [bnss-144, pwdva-20]. Matches Lane C's doc exactly, including latencies of a few ms.

python3 src/laya_integrated.py --mode classifier "test question about maintenance"
# stderr: error: no trained checkpoint found at .../models/v71-classifier/best/model.pt; run the Colab notebook first or use --mode rule-based
# exit 2  ✓

python3 src/laya_integrated.py --mode auto "I need maintenance from my husband" --json
# keys exactly the 12 C1 keys; extractor=rule_based; fallback_reason names the missing default checkpoint path. ✓
```

16-Q via the runtime (expected sections taken from `gt_ids`, the kept-id field — **not** `gt_sections`, which are display names like "BNSS 144" and would false-fail every row):

```bash
python3 - <<EOF  # run_question(text, mode='auto') over _load_16q() rows
# K0 OK, H1 OK, H2 OK, H3 OK, H4 OK, H5 OK, H6 MISS missing=['pwdva-18'],
# H7 OK, H8 OK, H9 OK, H10 OK, H11 OK, H12 OK, H13 OK,
# H14 MISS missing=['hma-13'], H15 OK
# 16Q EXACT: 14 / 16
EOF
```

**14/16 confirmed, misses H6 (missing `pwdva-18`) and H14 (missing `hma-13`) — the same two as the recorded baseline.** All calls `rule_based` with `fallback_reason` set.

## 4. Harness (Lane E)

```bash
python3 tests/integrated_backtest.py --mode rule-based --suite all --json-out /tmp/impl_verify_rulebased.json
# exit 0
```

| Suite | Measured (this run) | Claimed baseline | Match |
|---|---|---|---|
| validation | **261/500 (52.2%)**, micro-P/R/F1 0.8905/0.4623/0.6086, TP/FP/FN 423/52/492, silent 212; EN 209/235, KN 30/153, Kanglish 22/112 | 261/500, same micros/TP/silent | **MATCH +0** |
| kaanoon | **14/28 (50.0%)**, 0.75/0.60/0.6667, 27/9/18, silent 6 | 14/28, same | **MATCH +0** |
| 16-Q | **14/16 (87.5%)**, 1.0/0.9623/0.9808, 51/0/2, court 13/16, esc 16/16, kinds strict 10/16, silent 0, Fp 0, misses H6 + H14; rating raw **9.1 → capped 9.0** | 14/16, same metrics; rating 7.6 | exact MATCH; rating differs — see §8b |
| brutal | **210/230 (91.3%)**, 0.9974/0.9205/0.9574, 382/1/33, court 215/230, esc 213/230, kinds strict 152/230, silent 15, C13 1/16; §3.2 bar FAIL (silent 15, per-cat 0.0625) | recorded 215/230; current-code ref 210/230 | **MATCH to current-code ref**; −5 vs recorded — see §8a |

JSON (`/tmp/impl_verify_rulebased.json`) records `validation_sha256.ok: true`, `brutal_sha256.ok: true` (brutal `934a2b22…`), git HEAD + dirty flag, runtime `src/laya_integrated.py`. The harness scored the **real** Lane C runtime (`run_question` per question), not the stand-in — confirmed by reading `_run_questions` and by the JSON `runtime.source`.

```bash
python3 tests/integrated_backtest.py --suite sealed --json-out /tmp/x.json
# stderr: ERROR: refusing --suite 'sealed': sealed test banks ... are NEVER scored by this harness. ...
# exit 2 ✓ (no sealed file loaded)

python3 tests/integrated_backtest.py --self-test
# SELF-TEST: PASS (0 failures) — incl. sealed-guard, C1 key validation, toy rating math, Fp facts regression (exit 0)

python3 tests/integrated_backtest.py --mode classifier --suite 16q --json-out /tmp/x2.json
# exit 2 (no checkpoint; Lane C FileNotFoundError surfaced) ✓
```

**Finding F-5 (minor, doc-label):** the Brutal suite's JSON `method.custody_vocab` reads `"statutory_primary (stand-in assess call; the real C1 runtime chooses its own vocab — see doc)"`. The brutal run in this verification used the real C1 runtime (per-question `run_question`, which takes no `custody_vocab` argument — the parameter is silently ignored for the real runtime). The parenthetical is stale/misleading: it describes the stand-in path, not the path that ran. The numbers are unaffected (they match the frozen scorer exactly — see §8a), but the label should say the vocab parameter is ignored by the real runtime. One-line fix in `tests/integrated_backtest.py::run_brutal_suite`.

## 5. Lane B (classifier)

```bash
python3 scripts/train_v71_classifier.py --train-file data/synthetic_v7_1/train.jsonl \
    --val-file data/synthetic_v7_1/validation.jsonl --check-data-only
# OK: train=7500 val=500 (torch NOT needed for this mode).
# Loader report: n_ok 7500/500, n_skipped 0/0, no unknown issue/fact/enum keys on either split.
# Train langs EN 3573 / KN 1931 / kn_roman 1996; validation EN 235 / KN 153 / kn_roman 112. Spans 5829 / 401.
# (matches Lane B's doc exactly)

python3 -m py_compile src/laya_v7_classifier.py scripts/train_v71_classifier.py scripts/calibrate_thresholds.py
# (no output = OK)
```

Signatures (verified by AST inspection, no torch import needed — all five C2 functions exist in `src/laya_v7_classifier.py`):

- `predict_text(model, tokenizer, text: str, config: ClassifierConfig | None = None)`
- `load_checkpoint(path: str | Path, *, device: str = "cpu")`
- `save_checkpoint(model, config: ClassifierConfig, path: str | Path)`
- `evaluate_checkpoint(checkpoint_path, val_path, *, device="cpu", limit=None, config=…)`
- `score_label_predictions(gold_records, pred_records)`

Loss/backbone (from `--help` and source):

- `--loss` choices `[weighted_ce, focal_ce]`, `default="weighted_ce"` ✓; `focal_ce` present in both files; no `asymmetric` string in either file (0 occurrences) ✓.
- `BACKBONES = {jhu-clsp/mmBERT-base: MIT, google/muril-base-cased: Apache-2.0, FacebookAI/xlm-roberta-base: MIT}`; `ClassifierConfig.max_seq_len: int = 320`; `pooling="one_pass"` default ✓.
- All notebook-needed flags exist: `--train-subset`, `--pooling`, `--head-lr`, `--bf16`, `--dump-predictions`, `--eval-checkpoint`, `--backbone` (3 choices), `--epochs` (max 4) ✓.

OOF calibration guard (proper test — a dummy OOF file + dummy checkpoint dir containing `model.pt`, so the Val-500 guard itself is what fires):

```bash
python3 scripts/calibrate_thresholds.py --oof-predictions /tmp/dummy_oof.jsonl \
    --train-file data/synthetic_v7_1/validation.jsonl --checkpoint-dir /tmp/dummy_ckpt
# stderr: ERROR: REFUSED — --train-file is the frozen validation split (..., sha256 7640d067c28a...).
#   OOF calibration runs on Train-7500 ONLY; the frozen split must stay untouched by calibration.
# exit 2 ✓
```

(The guard is at `scripts/calibrate_thresholds.py:242–249`, checking both the sha and the filename.)

**Finding: Lane B did not address any A3 item.** `grep` of `docs/impl_laneB_classifier_changes.md` finds no A3 fix; the C1 broadcast, the unmasked gate BCE, the vacuous `third_party` column, and the unsupervised clause logits are all still present in the committed code (verified in §6b). The coordinator has since spawned **Lane B2** for exactly this (shared state, HEAD `34e407a`) — so this is recorded as the open fix, not a surprise.

## 6. Lane A gates (each check script re-run)

### 6a. A1 graph contract — FAIL reproduced (exit 1)

```bash
python3 scripts/check_graph_contract.py   # exit 1
# Distinct graph-consumed fact/enum keys: 59
# Summary: FACT 27 · ENUM 2 · DERIVED 3 · DEFAULTED 2 · LEGACY 3 · ALIAS 1 · UNCOVERED 21
# FAIL: graph input keys without a classifier producer / derivation. A1 gate NOT passed (exit 1).
```

The 21 uncovered keys match the filed doc exactly (incl. `arrears_recovery_asked`, `maintenance_variation_asked`, `interim_only_asked`, the five `*_negated` facts, the 7 still-dead keys, and the escalation flags). Reverse-dead confirmed: `procedure` (issue), `school_fees_fact` (fact), `modality_time` (enum).

**Finding F-1:** my task brief said "expect exit 0" for this script. That is wrong: the gate FAILS by design (exit 1) and Lane A's doc files it as FAIL. The exit-1 is the correct, honest outcome — the 21-key schema gap is an open coordinator decision, not a passing gate. (The coordinator's `34e407a` shared-state correction now records A1 as FAIL.)

### 6b. A3 clause supervision — FAIL reproduced (exit 1); violation sites confirmed; fix sized

```bash
python3 scripts/check_clause_supervision.py   # exit 1
# FAIL: 1 site(s) assign question-level labels to all clauses. A3 gate NOT passed (exit 1).
# C1 COPY (encode_labels ~678-680) · C3 UNMASKED-PAD (train.py:752) · C4 NO-CLAUSE-LOSS (train.py:745-762)
# C2 VACUOUS third_party: 0 positives in train (7,500) and validation (500)
# Corpus: train 3,289/7,500 records with NO spans; gate hypothetical=1 rows 637 train + 28 val, ALL from the C1 broadcast;
#   gate denied=1 rows 257 train / 18 val (span-derived, legitimate); span_mask=1 rows 5,568 train / 383 val.
```

I inspected both cited sites in the committed code:

- **C1 — `src/laya_v7_classifier.py::encode_labels`, lines 678–680** (exact):
  ```python
  if record["enums"].get("modality_time") in ("hypothetical", "quoted"):
      for row in gate:
          row[1] = 1
  ```
  Present and unmodified by Lane B. The docstring above it (lines ~661–669) even describes the broadcast as intended behaviour ("hypothetical=1 if modality_time is hypothetical/quoted").
- **C3 — `scripts/train_v71_classifier.py:752`**: `loss_gate = bce(out["clause_gate_logits"], b_in["gate"])` — full `[B, max_c, 3]` tensor, unmasked. The span loss directly below (:757–760) IS masked via `span_valid` (`span_logits[span_valid]`), so the fix pattern already exists in the same function.
- **C2 — `third_party`**: only set at `classifier.py:693–694` when a span carries `label == "third_party"`; the corpus schema has no such label, so the column is all-zero in all 8,000 records (checker-measured). The gate head `clause_gate_head = nn.Linear(hidden, 3)` (line 887) and the veto in `fuse_issue_probs` (lines 1021–1056: a clause is vetoed iff ANY of its three gate sigmoids ≥ `tau_neg` 0.5) mean a never-firing third column is dead weight in a live veto path.
- **C4 — clause logits**: `clause_issue_logits` / `clause_fact_logits` are built in `forward` (~994–1014) and consumed only by fusion (`train.py:694–695` evaluate, `classifier.py::predict_text` ~1114–1116). `loss_issue` / `loss_fact` (:745–747) use only the full-question logits. No loss term references the clause logits anywhere (confirmed by the checker and by inspection).

**Fix sizing (for Lane B2 — what exactly must change):**

1. **C1 (blocking, ~5 lines):** delete the broadcast at `classifier.py:678–680`. Do not replace it with any other question-level copy. Hypothetical/quoted gate supervision must come from clause-local evidence only; where no clause-local label exists, mask that gate column's loss for those clauses (or drop the hypothetical column's supervision until spans carry it). After the fix, `check_clause_supervision.py` must report 0 hypothetical rows sourced from broadcast (re-run the checker; the 637+28 rows must disappear unless a legitimate span source replaces them).
2. **C3 (~3 lines):** mask the gate BCE exactly like the span loss — index `clause_gate_logits` and `gate` by the same `span_valid`-style mask derived from `b_in["counts"]` before the BCE at `train.py:752`. One-line-class change; no new tensors needed.
3. **C2 (coordinator decision, then ~10 lines):** either Lane 02 adds third-party span labels to the corpus (schema change + regeneration), or drop gate column 2: shrink `clause_gate_head` to 2 outputs, remove the third veto input in `fuse_issue_probs`, and update `encode_labels` + the checker. Do not ship a head trained on all zeros. (Lane B2's brief already scopes this.)
4. **C4 (design decision before Run #1, the largest item):** pick ONE clause-supervision source for the 1-pass architecture and wire a loss to `clause_issue_logits`/`clause_fact_logits` — either (a) span-derived clause labels (spans already carry key/kind/offsets; 4,211/7,500 train records have spans, so coverage is partial by construction), or (b) multiple-instance learning from the question-level label. Until one is wired, `fuse_issue_probs` max-pools over clause scores the heads were never trained to produce; the conservative interim option is to disable clause fusion (use full-question probs only) and record the fused score as unvalidated. This is a design decision, not a line edit — it needs the coordinator, and it gates Train Run #1.
5. **C5 (reporting only):** the training report must state the span head's effective training set is 4,211 records (not 7,500).

### 6c. A2 oracle — 9/16 degraded, NOT 12/16

```bash
python3 scripts/run_graph_oracle.py --legacy-16q --gold ground-truth/ground-truth-v2-hma27-A.json --gold-provenance independent
# DEGRADED MODE: legacy 16-Q GT carries NO gold issues and NO gold enums — only 8 legacy fact keys.
# GG gold/gold: 9/16 exact (56.2%)   (exit 1, as designed)
#   miss K0: missing=[gwa-1890, hmga-1956-s6, pwdva-18, welfare-principle]
#   miss H2: missing=[gwa-1890, hmga-1956-s6, welfare-principle]
#   miss H4: missing=[pwdva-18]
#   miss H5: missing=[gwa-1890, hmga-1956-s6, welfare-principle]
#   miss H6: missing=[pwdva-18]
#   miss H7: missing=[births-deaths-act-1969]
#   miss H14: missing=[hma-26, hmga-1956-s6, welfare-principle]
# ORACLE CEILING MEASURED: gold-input exact is 9/16, not 100%. ... In DEGRADED mode this gap is expected.
```

**Finding F-2:** my task brief said "confirm the 12/16 gold-input smoke result and the H3/H10/H15 + H9 misses". That is wrong on both counts: the filed A2 doc says **9/16**, and my independent re-run gives **9/16** with misses K0/H2/H4/H5/H6/H7/H14 — no H3/H10/H15/H9 misses at all (those four are exact under gold inputs). The shared state's earlier "12/16" line was the source of the error; the coordinator's `34e407a` correction now records 9/16. The 9/16 is a **missing-input artifact** (no `custody_claim`, no `birth_cert_asked`, no violence/coercive fact in the legacy 8-key annotation), not a measured graph ceiling — the doc says so explicitly and the miss list supports it (every miss is a section whose trigger the legacy file cannot express). Full GG/GP/PG/PP remains blocked on human-annotated gold issues + 28 facts + enums.

### 6d. A5 grouped split — FAIL reproduced; grouped dev file does NOT exist

```bash
# Independent recomputation from data/synthetic_v7_1/{train,validation}.jsonl:
# val records whose meta.blocks signature appears in train: 500 / 500
# val records whose full label tuple (issues+facts+enums) appears in train: 500 / 500
# val records whose (issues+facts) label combo appears in train: 500 / 500
# train block signatures: 199; val block signatures: 183 (all ⊆ train)
# any template_family_id in train: False; record fields: enums, facts, id, issues, lang, meta, spans, text
```

The split is a random row-level shuffle by construction (`scripts/build_synthetic_corpus.py::generate` ~1892–1900, `rng.shuffle` then first 500 → validation — as filed). The frozen split is untouched (sha still `7640d067…`).

**Finding F-3:** my task brief said "confirm … that `data/synthetic_v7_1/dev_grouped.jsonl` exists with 0 shared families vs train". **The file does not exist** — `ls` fails, `find . -name "*grouped*"` returns nothing, and no commit since `90e20c5` creates it. The A5 doc is explicit that the group-disjoint dev set is "still to be built (coordinator)". Nothing can be confirmed about a file that was never created; building it is an open coordinator decision, and it must be a NEW file that does not replace `validation.jsonl`.

### 6e. A4 tokenizer / A6 VRAM — OPEN, exit 2, no numbers (as filed)

```bash
python3 -c "import transformers"   # ModuleNotFoundError
python3 -c "import torch"          # ModuleNotFoundError
python3 scripts/smoke_backbones.py --part a    # exit 2
# ... huggingface_hub not installed — UNVERIFIED in this run (all three backbones)
# CODE READY, RUN ON COLAB: part (a) needs transformers, part (b) needs torch + GPU. No numbers are reported from this VM (exit 2).
python3 scripts/vram_smoke.py --backbone jhu-clsp/mmBERT-base --train-file data/synthetic_v7_1/train.jsonl   # exit 2
# torch is NOT installed on this VM. Do not run here. Run this script on Colab (T4 GPU) or the RTX 5050 machine: ...
```

Both scripts behave exactly as their docs state: code-ready, refuse cleanly, produce no numbers here. The A4 doc's claim set is consistent with its own method (no fertility/truncation numbers exist anywhere on this VM, so there is nothing to cross-check — the numbers must come from Colab). **Correction to the record:** the shared state's earlier line "A4 MuRIL wins KN/Kanglish fertility" was false — no backbone has won anything yet; MuRIL is only the challenger. The coordinator's `34e407a` correction now records A4 as OPEN with no winner. One consequence to carry forward: the mmBERT default was swapped in **before** the benchmark names a winner (Lane B's call, recorded in the A4 doc) — if MuRIL or XLM-R wins part (b), the default must change to match.

### 6f. A7 brief reconciliation — arithmetic VERIFIED from aggregates

Spot-checked from the cited aggregate sources only (no sealed text opened):

- `results/live-laya-v7-results.md:23`: Sealed Fresh-20 **7/20**, TP/FP/FN **38/5/28** ✓. Internal consistency: 38+28=66 GT sections, 38/66=0.5758 (reported micro-recall) ✓; 38/43=0.8837 (reported micro-precision) ✓.
- `docs/v6-lane5-validation.md`: freeze-note composition maintenance 4, custody 3, Stridhan 3, residence 2, violence 2, divorce 2, **birth cert 2**, OOS 2 (= 20) ✓; "dropping F17/F18 (birth cert)" corroborates F17/F18 as the birth-cert pair ✓. Category breakdown (5/18) + birth cert 2/2 = 7/20 ✓ — discrepancy 1 reconciled as filed.
- FN list sums to 27 vs headline 28 — discrepancy 2 stays OPEN as filed (one FN unitemised, section unknown; must be carried as "27 itemised + 1 unitemised", never silently changed to 27).
- Kannada-8: headline 4/8 with the same composition logic (remaining four must be 4/4 exact) — consistent with the filed reasoning; FN list sums correctly (7=7), so no FN gap there.

## 7. Lane D notebook

```bash
python3 -m json.tool notebooks/laya_v71_train_backtest.ipynb > /dev/null   # OK
python3 -c "import nbformat; nb=nbformat.read(...); nbformat.validate(nb)"
# NBFORMAT_VALIDATE_OK, cells: 21 (9 markdown, 12 code — as filed)
```

Sealed check: `grep` finds 8 "sealed" mentions, all in **markdown** cells (cell 19, the Phase E "no sealed re-run cell, deliberately" note, which names the two sealed files only to say they are never loaded). **No code cell mentions `sealed`, `fresh-20`, or `kannada-8`** — verified per-cell (21 cells enumerated; `sealed_mention=True` only on markdown cell 19). No code cell loads a sealed file. ✓

CPU smoke cells (tagged `cpu_smoke`: cells 1, 2, 6, 7, 11) extracted verbatim and run as a plain script:

```bash
python3 /tmp/nb_smoke.py   # exit 0
# REPO_ROOT: /home/hatch/workspace/laya-v71-work
# HEAD: 4573615303fdb464fb7a8ce820bd44f4b65e0ec0   (HEAD at extraction time; report HEAD is 34e407a — doc-only delta, see header note)
# train=7500 val=500
# OK: frozen validation split matches the frozen sha256.
# --self-test exit 0; 16-Q spot check: 5/5 exact (K0, H1–H4)
# OK: train=7500 val=500 (torch NOT needed for this mode).
```

Exit 0 confirmed. GPU cells (4, 5, 9, 12, 13, 14, 16, 18, 20) never executed here — correct, they need a T4. Cells 9/16/18 print a loud SKIP if the file they call is absent from the checkout; all other GPU cells are gated on `CPU_SMOKE_TEST = False`. One dependency note (already filed by Lane D §4, still true at push time): the notebook clones `main` from GitHub, so the push must land before the Colab run — the notebook prints the HEAD it runs from so a stale checkout is visible.

## 8. Discrepancy reconciliations

### 8a. Brutal-230: 210/230 (C1 harness) vs 230/230 (v7 live run)

**The 210/230 number is independently confirmed** — through a second, different code path:

```bash
PYTHONPATH=. python3 tests/v7_backtest.py --suite brutal --mode evidence --device cpu
# exact: 210/230, TP/FP/FN [382, 1, 33], court 215/230, esc_bool 213/230,
# kinds_strict 152/230, silent 15, fb_count 58, rating 0.0
# Misses (first 10 of 20): B-024, B-027, B-075, B-086, B-127 (English) + B-203–B-217 (C13 Kannada, all silent)
```

The frozen scorer's aggregates are **identical** to the harness's on every field except Fb (58 vs 0-unmeasured — the C1 gap, see §8b) and the rating (0.0 vs none — the harness correctly refuses to rate Brutal). The miss IDs match exactly.

**What the 230/230 actually was:** `results/live-laya-v7-results.md:45–46` records Brutal-230 twice — `evidence` (CPU) **215/230** (214/214 EN, C13=1/16) and `laya` (CUDA, neural) **230/230** (incl. C13=16/16). The 230/230 was **never an evidence-mode number**; it is the neural `laya` mode on CUDA. The task spec's "must stay 230/230" compared a rule-based measurement against a neural-mode number — a category error, now corrected in the shared state and the notebook (gate: do not regress below 210/230, 230/230 as aspiration).

**Does the regression claim hold?** As a measurement, yes: evidence mode went **215/230 → 210/230** (−5 exact), with esc_bool 230→213 (−17) and kinds strict 184→152 (−32). The 5 new misses are all English: B-024, B-027, B-075, B-086, B-127 (top FNs pwdva-20 ×10, bnss-144 ×6, gwa-1890 ×5, bns-316 ×4; the single FP is hma-9 on B-075). The 15 C13 Kannada silents are unchanged (1/16 both before and after — the known no-translation gap). **Causation is NOT established:** Lane E's suspects (Lane 03 anchor hardening, Lane 08 route fixes) are plausible — they are the only pipeline changes since the v7 verification runs — but no bisect was run by any lane, and I ran none either (it is out of this verification's scope and would need checkouts of intermediate recall-swarm commits). What would confirm causation: `git bisect` (or manual bisection) of evidence-mode Brutal over the recall-swarm commits, scoring B-024/B-027/B-075/B-086/B-127 at each step; or reverting Lane 03's anchor changes and Lane 08's route changes independently and re-scoring. Until then, "regression, cause unknown (Lane 03/08 suspected)" is the honest statement. The §3.2 bar verdict is unchanged in shape (it already failed on silent 15 + C13 before the regression).

### 8b. 16-Q rating: harness 9.0 vs frozen scorer 7.6 — the honest number is 7.6

Independent frozen-scorer re-run:

```bash
PYTHONPATH=. python3 tests/v7_backtest.py --suite 16q --mode evidence --device cpu
# exact: 14/16, TP/FP/FN [51, 0, 2], court 13/16, esc_bool 16/16, kinds_strict 10/16,
# fb_count: 3, fb_by_mapping: {statutory_prerequisite_gate: 3},
# raw_formula_rating: 7.6, rating: 7.6 (capped)
```

Arithmetic check (frozen formula, same components both scorers agree on): E=0.875, Rm=0.9786, Pm=1.0, C=0.8125, S=1.0 → 10×(0.60×0.875 + 0.15×0.9786 + 0.10×1.0 + 0.075×0.8125 + 0.075×1.0) = 10×0.9077 ≈ **9.1** raw. The frozen scorer then subtracts 0.5×Fb = 0.5×3 = 1.5 → **7.6**. The harness computes the same 9.1 but with Fb=0 because **Fb is unmeasurable through the C1 output** — `run_question` returns no pre-gate candidates, no `dispositions`, no `gated_out`, so the harness reports `fb_measured: false` and the rating as a provisional upper bound (its own print and JSON say so explicitly).

**Quote 7.6, never 9.0 unqualified.** The harness's 9.0 is an upper bound that assumes zero false-before-gate; the measured Fb is 3. The fix (for Lane C, post-B2): expose pre-gate data (`candidates_before_gate` / `gated_out`, even as optional extra keys) so Fb becomes measurable through C1; the harness already picks up `_assess_record` when present. Until then, every harness 16-Q rating must carry the "Fb unmeasured — upper bound" qualifier, and the frozen scorer stays the rating authority. (Same gap makes the harness's Brutal Fb 0 vs the frozen scorer's 58 — the harness correctly refuses to rate Brutal at all, so no number is misquoted there.)

### 8c. Lane D's two failed execs (exit 1, exit 2)

**Not verifiable from the working copy.** I searched `docs/impl_laneD_notebook.md`, `docs/impl_swarm_state.md`, and the notebook itself for any record of failed execs: there is none. No file in Lane D's deliverables references a failed command, and nothing in them depends on one:

- The only locally-runnable path (CPU smoke cells) exits 0 — verified independently in §7.
- The GPU cells cannot run here by design (no torch/GPU); cells 9/16/18 SKIP loudly if their target file is absent, and the rest are gated on `CPU_SMOKE_TEST = False`.
- The exit-1/exit-2 events visible anywhere in this swarm are the **designed** gate outcomes: A1/A3 checkers exit 1 (genuine FAILs), A4/A6 scripts exit 2 without torch/transformers. The coordinator's shared state (`34e407a`) attributes "two failed execs" to **Lane A** ("Lane A's two failed execs are the A1/A3 checkers exiting 1 as designed").

Most likely explanation: the "Lane D failed execs" in my task brief is a misattribution of the Lane A checker exits (or of Lane D's own expected GPU-path failures while probing the notebook locally, which leave no trace in the repo). Either way: **no Lane D deliverable depends on a failed command, and no rework is needed on that account.** If the coordinator's session log shows specific Lane D execs, those should be named — I cannot reconstruct them from the working copy.

## 9. Git hygiene

```bash
git log --oneline 90e20c5..HEAD   # 10 commits (at report HEAD 34e407a)
# 34e407a coordinator — correct Lane A verdicts in shared state (A1 FAIL…, A2 9/16…, B2 spawned)
# 4573615 Lane A — correct A3/A4/A6 docs + checkers to landed Lane B state
# ce3d021 coordinator — shared state (Lane A done, Lane F verification running)
# 43a0b4d Lane E — integrated backtest harness (C3) + lane doc
# b28453c coordinator — shared state (Lane A committed fa9703b)
# 7795ffb coordinator — shared state (Lane B done 7527258)
# fa9703b Lane A — Phase A gates A1–A7 (5 scripts + 7 gate docs + Lane B handoff note)
# 06483d8 coordinator — shared state (Lane C done, Lane D done, Lane B committed, Brutal-230 discrepancy recorded)
# 7527258 Lane B — FALLBACK-2 classifier amendments
# 3216272 Lane D — Colab train+backtest notebook (C4) + lane doc
# 792c75f Lane C — integrated runtime (C1) + lane doc
```

Files per commit (from `git show --name-only`):

- Lane C `792c75f`: `src/laya_integrated.py`, `docs/impl_laneC_runtime.md` — own files only ✓
- Lane D `3216272`: `notebooks/laya_v71_train_backtest.ipynb`, `docs/impl_laneD_notebook.md` — own files only ✓
- Lane B `7527258`: `src/laya_v7_classifier.py`, `scripts/train_v71_classifier.py`, `scripts/calibrate_thresholds.py` (new), `docs/impl_laneB_classifier_changes.md`, `docs/rtx-recall-training-commands.md` — own files, **plus** an amendment note at the top of `docs/recall_swarm_state/lane-04-classifier.md` (Lane 04's file; declared in Lane B's doc as a top-note only, Lane 04's record untouched below it — minor, declared, not a behaviour change)
- Lane A `fa9703b`: 5 scripts + 7 gate docs (own files) **plus** `docs/impl_swarm_state.md` (coordinator-owned shared state — Lane A wrote its own findings into it; the coordinator has since corrected that section in `34e407a`)
- Lane A `4573615`: A3/A4/A6 docs + 2 checkers **plus** `docs/impl_swarm_state.md` again (same shared-state touch)
- Lane E `43a0b4d`: `tests/integrated_backtest.py`, `docs/impl_laneE_harness.md` — own files only ✓
- Coordinator commits (`06483d8`, `7795ffb`, `b28453c`, `ce3d021`, `34e407a`): `docs/impl_swarm_state.md` only ✓

**No lane committed another lane's code; no frozen file was touched by any commit** (verified: no frozen path in any commit's file list, and `git diff 90e20c5..HEAD` over all 9 frozen paths is empty). `git status` is clean at report time. Nothing was pushed by me (no push performed; per task).

## 10. Prioritised fix list

### Must fix before the push (blocking)

1. **A3 clause supervision (Lane B2 — already spawned, in flight).** Remove the C1 broadcast (`classifier.py:678–680`); mask the gate BCE (`train.py:752`); resolve the vacuous `third_party` column (drop it or get Lane 02 span labels); decide the clause-supervision source for 1-pass fusion (spans or MIL) before Train Run #1 — or disable clause fusion meanwhile. Gate: `scripts/check_clause_supervision.py` exits 0. **Do not start Train Run #1 until C1 + C4 are decided** — otherwise the run trains a gate head on broadcast labels and fuses over unsupervised clause scores.
2. **Harness 16-Q rating qualifier (Lane E, 5 minutes).** The harness already labels its rating an upper bound in print/JSON; make the printed `gate rating:` line itself carry "(Fb unmeasured — upper bound; measured rating 7.6)" so a copied line cannot be misquoted. Alternatively/additionally, have the harness print the frozen scorer's 7.6 alongside as the measured reference.
3. **Correct the Brutal gate in every place that still says 230/230** (coordinator — mostly done: shared state + notebook now say "do not regress below 210/230"). Grep the push manifest / plan for any remaining "Brutal must stay 230/230" and replace with the 210/230 C1 baseline + 230/230 aspiration. Do not report any classifier Brutal number against 230/230 as if it were the C1 baseline.

### Must fix before the Colab GPU run (not blocking the push)

4. **Fb measurability (Lane C, small).** Expose `candidates_before_gate` / `gated_out` (optional extra keys) from `run_question` so the harness can measure Fb/Fp item 7's dropped half through C1. Until then the harness rating stays an upper bound.
5. **Harness Brutal method label (Lane E, one line).** Fix the stale "stand-in assess call" parenthetical in `run_brutal_suite` (see F-5).
6. **Build the grouped dev set (coordinator decision).** `data/synthetic_v7_1/dev_grouped.jsonl` does not exist; build it from whole `meta.blocks` signatures (better: block families) held out of training, as a NEW file with its own manifest entry. It must not replace `validation.jsonl` and must not be presented as comparable to frozen-split numbers. OOF calibration must then use grouped folds on Train-7500.
7. **A1 schema decision (coordinator/parent — human decision).** 28 → 36 facts (or the deterministic-derivation subset: `interim_only_asked`, `money_fact_child_or_parallel` in the Stage 1→2 adapter, not the frozen graph). Until decided, the classifier path reads `False` on all 21 keys on every question — record it as a known limitation in the training report.
8. **A2 oracle human gate.** Independent annotation of gold issues + 28 facts + enums (16-Q re-annotation, or first slice of the Phase D 300-item holdout) before GG/GP/PG/PP can run. Never derive gold from Graph v4.

### Needs a human (not agent work)

9. **Brutal regression causation.** Bisect evidence-mode Brutal over the recall-swarm commits (or independently revert Lane 03 anchors / Lane 08 routes and re-score B-024/B-027/B-075/B-086/B-127). A human/coordinator decision on whether to chase the −5 before or after Train Run #1.
10. **Phase D/E human gates.** 300-item independent holdout (≥80% per language) and the sealed re-run (Fresh-20/Kannada-8) — Colab/RTX only, after Phase B/C gates pass. No ≥70% claim until the sealed re-run measures it.

### Can wait (documented, not blocking)

11. **A4/A6 Colab runs.** 3-backbone smoke benchmark (part a tokenizer fertility + part b 1-fold smoke-F1) and the VRAM sweep (micro-batch 1/2/4/8, <6.5 GB at 8). If MuRIL/XLM-R wins, change the mmBERT default. If micro-batch 8 OOMs, the training script already fails loudly with the fallback — verify the actual behaviour on the T4.
12. **Lane B's open items (already filed):** full fact binding needs a Lane 02 schema change (`spans[].subject` + `spans[].event_id`); per-floor Pareto re-optimisation; 5-fold grouped OOF generation; LoRA/`--merge-lora` unverified without torch/peft; γ/β/w₀/cap grids untuned.

## Task-brief corrections (for the coordinator's record)

The brief I was given contained three wrong expectations, all now corrected in the repo by `34e407a` / `4573615` (verified independently here):

- **F-1:** A1 "expect exit 0" → actual exit 1 (FAIL, 21 uncovered). Correct.
- **F-2:** A2 "12/16 … H3/H10/H15 + H9 misses" → actual 9/16, misses K0/H2/H4/H5/H6/H7/H14. Correct.
- **F-3:** A5 "`dev_grouped.jsonl` exists with 0 shared families" → the file does not exist. Correct (still to build).
- The shared state's earlier one-line Lane A summary ("A1 PASS 0 dead keys; A2 12/16; A3 2 violations; A4 MuRIL wins") was wrong on all four points; `34e407a` replaced it with the corrected verdicts, which match the filed gate docs and my re-runs.

## Bottom line

**The builders' code is verified where it can run on this VM, and the failures are honest ones, not hidden ones.** Guardrails pass (66 tests OK), frozen files are untouched, the runtime reproduces 14/16, the harness reproduces all four suites, Lane B's classifier amendments are present with stable signatures and the Val-500 calibration guard working. The open defects are exactly the ones the lanes already filed: **A1 (21 uncovered keys — schema decision), A3 (clause supervision — Lane B2 in flight, blocks Train Run #1), A5 (no grouped dev set — file never built), A2/A4/A6 (human/GPU gates)**. The two numbers that could have been misquoted are now pinned: **Brutal evidence-mode baseline is 210/230, not 230/230** (230/230 was neural `laya`/CUDA), and **the honest 16-Q rating is 7.6, not 9.0** (the harness's 9.0 omits the measured Fb=3). Nothing in this report required opening sealed text, and no score was faked: every number traces to a command above.
