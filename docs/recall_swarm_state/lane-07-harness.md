# Lane 07 — Evaluation Harness (recall swarm)

Owner: Lane 07. File owned: `tests/recall_eval.py` (+ this status file).
Working copy: `~/workspace/laya-v71-work`.

## What changed

- NEW `tests/recall_eval.py` — the ONLY number lanes may use to claim
  progress on the synthetic split. Scores the pipeline on
  `data/synthetic_v7_1/validation.jsonl` ONLY (split size read from
  `data/synthetic_v7_1/manifest.json`: `n_validation`, never hardcoded).
- Method: `assess_v7_batch(..., mode="evidence", device="cpu")` — zero-model
  regex evidence path, CPU-only, no torch, no model weights — plus Stage 2
  graph rules (`evaluate_stage2_v7`, `custody_vocab="v3_bundled"`) applied
  identically to derive expected sections from each record's
  issues/facts/enums and to route the pipeline's own prediction.
- Reports: exact-match rate (predicted == expected section set), micro
  P/R/F1, per-issue (requested) exact, per-language (en/kn/kn_roman) exact,
  per-cluster exact, silent count, Wilson 95% CI, top missing/extra
  sections, and a per-cause failure tag (coarse built-in tagger;
  `--tagger module:function` hook + `--failures-out` JSONL for Lane 01's
  taxonomy). Reuses `wilson_ci` from `tests/v7_backtest.py` (import, not a
  copy) and `load_corpus_jsonl` from Lane 04's `src/laya_v7_classifier.py`.
- Sealed guard: any input path containing `sealed` or `test-bank`
  (case-insensitive) exits with an error before any data is read. Verified
  in `--self-test` (3 refusal cases).
- `--self-test` is CPU-only, no data files, no torch; 12 checks PASS
  (21 after the Kaanoon extension below).
- File header is a README: how to run, how to interpret the number, and
  the warning that validation-split exact is a PROXY, not the sealed
  Fresh-20 number.
- 2026-11-27 ~19:24 IST — added `--suite kaanoon` (CONTRACT R6, see below).

## Commands run (exact output lines)

```
$ python3 tests/recall_eval.py --self-test
SELF-TEST: PASS (0 failures)

$ python3 tests/recall_eval.py --misses 5 \
    --failures-out results/recall_eval_failures_baseline.jsonl \
    --json-out results/recall_eval_summary_baseline.json
exact:        173/500 (34.6%)  Wilson 95% CI [0.3056, 0.3887]
micro P/R/F1: 0.8498 / 0.3389 / 0.4846  (TP/FP/FN [345, 61, 673])
silent:       263 (expected non-empty, predicted empty)

$ python3 tests/test_graph_v4.py
GRAPH V4 + FROZEN SHA TEST PASS: 34 sections / 66 nodes / 99 edges, 0 dangling edges, 7/7 frozen hashes intact.

$ python3 tests/test_prose_renderer_v2.py
PROSE VALIDATION PASS: 246 cases, Fp=0, quality_flags=0, 15/15 adversarial mutants caught, mean=0.0265ms, max=0.181ms
```

## Baseline number (synthetic validation split, BEFORE Lane 03's anchor changes)

- **Exact: 173/500 = 34.6%** (Wilson 95% CI [0.3056, 0.3887])
- Split: `data/synthetic_v7_1/validation.jsonl`, n_scored=500,
  manifest n_validation=500, seed 7102
- Method: mode=evidence, CPU-only, no torch; custody_vocab=v3_bundled;
  extractor_modes={'evidence': 500}; wall 0.61s, mean 0.0012s/Q
- Commit measured at: `2633a58a01746e1141426431c40850c12663378f`
  (HEAD had moved past the swarm-start 1cb0bff — Lane 10 commits landed;
  the baseline is recorded at the commit actually measured)
- Micro P/R/F1: 0.8498 / 0.3389 / 0.4846 (TP/FP/FN 345/61/673)
- Silent: 263 (expected non-empty, predicted empty) — the dominant failure
  mode, not wrong sections
- Per-language: en 129/228 (0.566); kn 23/153 (0.150); kn_roman 21/119 (0.176)
- Per-issue exact (requested): procedure 9/13 (0.692); joint_property 10/21
  (0.476); divorce 18/42 (0.429); custody 34/80 (0.425);
  birth_certificate 6/15 (0.400); maintenance 56/243 (0.230);
  violence 7/31 (0.226); stridhan 5/31 (0.161); residence 10/86 (0.116);
  dv_compensation 0/12 (0.000); restitution 0/12 (0.000)
- Per-cluster: hn_f 52/76 (0.684); hn_e 18/42 (0.429); core 45/121 (0.372);
  neg 6/16 (0.375); hn_d 8/28 (0.286); hn_a 5/19 (0.263); combo 29/121
  (0.240); hn_c 8/36 (0.222); hn_b 2/34 (0.059); conflict 0/7 (0.000)
- Failure tags: silent 263; exact 173; missing_only 27; extra_only 20;
  missing_and_extra 12; empty_expected_nonempty_pred 5
- Top missing sections: bnss-144 (149), pwdva-20 (95), pwdva-17 (73),
  pwdva-19 (73), pwdva-18 (44), gwa-1890 / hmga-1956-s6 /
  welfare-principle (39 each), bns-316 (24), hma-25 (18), hma-13 (18),
  hma-24 (15)
- Top extra sections: pwdva-20 (25), welfare-principle / gwa-1890 /
  hmga-1956-s6 (8 each), bnss-144 (6)
- Artifacts: `results/recall_eval_summary_baseline.json`,
  `results/recall_eval_failures_baseline.jsonl` (327 non-exact rows)

Reading: high precision (0.85) with low recall (0.34) — the evidence path
rarely predicts a wrong section but misses most of them, and it is silent
on 263/500. Kannada/Kanglish (0.15–0.18) is far behind English (0.57).
This is a proxy number: it measures synthetic-paraphrase recall, NOT the
sealed Fresh-20 (7/20) / Kannada-8 (4/8) numbers. Do not present it as a
sealed result.

## Cross-lane contract proposed for Lane 04 (to confirm in shared state)

Lane 04 owns the model-side scoring function for the trained classifier.
Agreed shared signature (implemented in `tests/recall_eval.py`, Lane 04 to
confirm — I do not edit Lane 04's files):

```python
predict_sections_from_stage1(issues, facts, enums, *, custody_vocab="v3_bundled") -> set[str]
# issues/facts/enums are predict_text() outputs ({issue: {"intent": ...}},
# {fact: {"state": ...}}, {head: {"value": ...}}); plain intent/state/value
# strings are accepted too. Runs Stage 2 and returns predicted sections.

score_predictions(records, predicted_sections, *, failure_tagger=None) -> dict
# Pure scorer both paths share. records = load_corpus_jsonl() records;
# predicted_sections = list of section sets aligned with records.
```

## Kaanoon real-phrasing eval — CONTRACT R6 (2026-11-27 ~19:24 IST)

- Lane 11 is building a FRESH HELD-OUT eval set from real Kaanoon
  family-law questions at `data/kaanoon_eval/heldout.jsonl` (target ~25–35
  items, source URL per item, annotated issues/facts + expected sections).
- R6: it is EVALUATION ONLY. This lane is the ONLY lane that scores it,
  read-only measurement, and no lane (including Lane 07) may tune anything
  against it.
- Harness support: `python3 tests/recall_eval.py --suite kaanoon`
  (option `--kaanoon-path`, default `data/kaanoon_eval/heldout.jsonl`).
  Same evidence-mode pipeline, same Stage 2 rules; reports exact /
  micro-P/R/F1 / per-category / silent as a SEPARATE number, labelled
  "Kaanoon real-phrasing eval (n=..., never tuned against)" — never merged
  with the synthetic validation number. Loader is schema-tolerant
  (accepts `text` or `question`; expected sections from an explicit
  `expected_sections` / `gt_sections` / `gt_ids` / `expected` field when
  present, else derived via Stage 2 from issues/facts; category from
  `category` / `primary_issue` / `meta.cluster`; source URL kept per row
  for audit). Same sealed/test-bank guard applies to the Kaanoon path.
- **Kaanoon baseline: PENDING Lane 11** — `data/kaanoon_eval/` does not
  exist yet in this working copy (checked 2026-11-27 ~19:24 IST).
  `--suite kaanoon` currently exits with a loud "pending" message
  (exit 3), not a number. Run it once the file lands and record the
  baseline here. Verified 2026-11-27 ~19:35 IST:

```
$ python3 tests/recall_eval.py --suite kaanoon
KAANOON BASELINE PENDING — Kaanoon held-out set not found: .../data/kaanoon_eval/heldout.jsonl
  (Lane 11 has not landed data/kaanoon_eval/heldout.jsonl yet)
exit=3
```

  Kaanoon self-test coverage (temp-file loader checks, explicit-expected
  override, guard on the Kaanoon path): all PASS — `--self-test` now
  21 checks, 0 failures. Synthetic re-run after the extension reproduces
  the baseline exactly (173/500, 34.6%; micro 0.8498/0.3389/0.4846;
  silent 263), and `test_graph_v4.py` + `test_prose_renderer_v2.py`
  still PASS.

## What is still unverified

- The baseline above is the pre-Lane-03-anchor-change number; re-run after
  Lane 03 lands and record the delta (same command, same commit note).
- Lane 04 has not yet confirmed the `predict_sections_from_stage1` /
  `score_predictions` shared signature (proposed here; needs coordinator
  merge into shared state).
- Lane 01 has not yet plugged its failure taxonomy into the `--tagger`
  hook; the built-in tags are coarse.
- Validation-split exact is a proxy: the >=70% user target is measured on
  Sealed Fresh-20 / Kannada-8, which only the RTX machine may re-run.
  No validation number may be quoted as a sealed number.
- Kaanoon baseline pending Lane 11's `data/kaanoon_eval/heldout.jsonl`.
- `results/` baseline artifacts are run outputs, not frozen files; if the
  corpus changes (Lane 02), re-run the harness and the leakage gate and
  record a new baseline rather than editing these files in place.
