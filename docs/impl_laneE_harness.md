# Lane E — Integrated Backtest Harness (contract C3)

Owner: Lane E. Files: `tests/integrated_backtest.py` (new),
`docs/impl_laneE_harness.md` (this file). Contract: C3 in
`docs/impl_swarm_state.md`. Runtime contract consumed: C1
(`src/laya_integrated.py`, Lane C).

## Command

```bash
python3 tests/integrated_backtest.py [--mode auto|rule-based|classifier] \
    [--suite all|validation|kaanoon|16q|brutal] [--checkpoint PATH] \
    --json-out <path>
```

Also useful:

```bash
python3 tests/integrated_backtest.py --self-test   # CPU-only harness checks, no scoring
python3 tests/integrated_backtest.py --mode rule-based --suite 16q --json-out /tmp/x.json
```

Exit codes: `0` success; `2` refusal / contract error (sealed request,
frozen-SHA mismatch, classifier mode without a checkpoint, C1 key drift,
first-question runtime failure); `1` unexpected failure / self-test failure.

## Suites

| Suite | Source (read-only) | Method |
|---|---|---|
| `validation` | `data/synthetic_v7_1/validation.jsonl` (frozen 500) | Expected sections derived via Stage 2 from each record's own issues/facts/enums (Lane 07 method). SHA verified before scoring (see below). |
| `kaanoon` | `data/kaanoon_eval/heldout.jsonl` (28) | Same scorer, separate number. CONTRACT R6: evaluation only, never tuned against. |
| `16q` | `ground-truth/ground-truth-v2-hma27-A.json` (K0 + H1–H15) | Frozen 16-Q regression set + frozen gate rating (§2 below). |
| `brutal` | `test-bank/brutal-bank-v1-frozen.json` (230) | `v7_backtest` brutal convention (custody `statutory_primary` + custody-companion projection). No 10-point rating (see below) — judged by the §3.2 bar. |
| `all` | all four, in the order above | — |

**Sealed refusal.** `--suite sealed` (or any value/path containing
`sealed` or `test-bank`) exits 2 with a message explaining sealed sets
run only on Colab/RTX. No sealed file is ever loaded. There is no
`--suite sealed` and no sealed path argument.

**Frozen validation SHA.** Before any scoring the harness verifies
sha256 of `data/synthetic_v7_1/validation.jsonl` AND the manifest's
`frozen_validation_sha256` both equal
`7640d067c28abf539131dbcc891e4bdffedf62bbef4a7d66c1659bb96d07e58e`.
A mismatch aborts (exit 2). The Brutal bank SHA is recorded in the JSON
and warned on if it differs from
`934a2b22…` (it matched at verification); it does not abort, because the
task requires the abort only for the validation split.

## Outputs

Stdout per suite: exact `n/N` + %, Wilson 95% CI, micro-P / micro-R /
micro-F1, TP/FP/FN, silent count, plus (16-Q) the gate rating with its
arithmetic, and (Brutal) the §3.2 bar verdict. Every run prints the
HONEST CLAIM RULE in its header:

> **No claim of >=70% until a real sealed re-run measures it.**

The `--json-out` file records: the exact command (`sys.argv`), git HEAD
+ dirty flag, mode/suite/checkpoint, runtime source + note, the SHA
verification results, the per-set results (including per-row detail),
and the mode-qualified baseline table used for the printed deltas.

## How the gate rating is computed (16-Q only)

Identical to `tests/v7_backtest.py::score_dataset` with
`legacy_16q_compat=True` (same `_pr` convention, same H12 special case,
same strict-vs-legacy esc_bool reporting):

```
E  = exact / 16
Rm = mean recall, Pm = mean precision (H12 empty/empty = 1.0/1.0)
C  = court correct / 16, S = esc_bool (legacy compat) / 16
raw = 10 * (0.60*E + 0.15*Rm + 0.10*Pm + 0.075*C + 0.075*S)
      - 0.5*Fb - 1.0*Fp            (clamped [0,10], 1 decimal)
rating = apply_gate_caps(raw, ...)   # frozen caps, defaults = honest
                                     # unverified state (G12 unverified,
                                     # sealed not passed, no confirmation)
```

The capped rating can therefore never exceed 9.0 from this harness.
**Brutal gets no 10-point rating:** the formula is a 16-question
instrument and its `-0.5 × Fb` term is not calibrated for a
230-question gating-probe set — the frozen scorer itself rates the
current-code evidence-mode Brutal run 0.0 (Fb=58 → −29). Brutal is
judged by the §3.2 bar instead: exact ≥ 200/230, micro-F1 ≥ 0.95,
court ≥ 200, esc_bool ≥ 200, silent 0, per-cat ≥ 0.75, errors 0,
Fp 0 — reported per row, pass/fail.

## Reuse map (no duplicated scorers)

- Reused by import: `tests/recall_eval.py` — `load_split`,
  `load_kaanoon_split`, `score_predictions` (the shared pure scorer),
  `guard_path`; `tests/v7_backtest.py` — `_load_16q`, `_load_brutal`,
  `wilson_ci`, `_pr`, `apply_gate_caps`, `compute_fb`,
  `SCORING_KINDS_V7`, `CUSTODY_COMPANIONS`.
- Mirrored (not reused): `score_dataset` — it calls `assess_v7_batch`
  directly and would bypass the integrated runtime, so
  `_score_typed_suite` re-implements its row logic over C1 outputs and
  was verified aggregate-identical against it (see Verification).
- New: runtime loading + C1 validation, the stand-in adapter, the
  Fb/Fp row logic, suite runners, printing, JSON report, self-test.

## Runtime status: Lane C landed mid-task

When Lane E started, `src/laya_integrated.py` did not exist; the harness
was built against contract C1 with a documented stand-in adapter (frozen
`assess_v7_batch`, mode="evidence", CPU, shaped into the exact C1 dict,
labelled `runtime.source == "stand-in"`). Lane C landed while Lane E
was working (commit `792c75f`, "R-IMPL: Lane C — integrated runtime (C1)
+ lane doc"). **The verification run below therefore scored the REAL
Lane C runtime, not the stand-in** — the harness imported it with no
change. The stand-in remains as a dormant fallback if the file is ever
absent; it cannot do classifier mode (exit 2, Colab/RTX only).

### Interface drift / gaps found against C1 (report, not silent workarounds)

1. **No drift on the C1 keys.** `run_question` returns exactly the
   contracted keys; the harness's strict first-result validation passed.
   Lane C's rule-based path is `extract_v7(mode="evidence")` →
   `evaluate_stage2_v7` → `render_prose` — no new extraction behaviour.
2. **No `custody_vocab` parameter on C1.** Lane C always routes with the
   default (`v3_bundled`); the frozen scorer's Brutal path uses
   `statutory_primary`. The harness applies the custody-companion
   projection at scoring time for Brutal. Measured effect this run:
   none — every Brutal aggregate matches the `statutory_primary`
   reference exactly (see Verification).
3. **Fb is UNMEASURABLE through the C1 output.** No pre-gate
   candidates, no `dispositions`, no `gated_out`. The harness reports
   `fb_count` as a lower bound (0 here) with `fb_measured: false`, and
   the 16-Q rating is computed with the Fb term omitted — a provisional
   UPPER BOUND, flagged in print and JSON. Recommendation for the
   coordinator: ask Lane C to expose `candidates_before_gate` /
   `gated_out` (even as optional extra keys) so Fb becomes measurable.
   The harness already picks up `_assess_record` when present; the same
   hook can take real C1 pre-gate keys with no other change.
4. **Fp item 7's dropped half is unmeasurable** (needs `gated_out`);
   the real-runtime Fp is a lower bound. Items 1–6, 8, 9 and item 7's
   cited-not-kept half ARE checkable from prose + kept sections + the
   C1 `facts` dict. **Harness bug found and fixed during verification:**
   the first version passed empty facts `{}`, which false-fires Fp
   item 3 on any HMA 13/13B prose mention (H5 hit; 28 spurious Brutal
   hits). Passing the C1 facts fixes it (verified: H5 authoritative
   check `[]`, Lane C prose byte-identical to `assess_v7` prose). A
   regression check is in `--self-test`
   (`fp_c1_facts_no_false_hit`, `fp_empty_facts_false_fires_item3`).
5. **Classifier failure mode.** Lane C's API raises `FileNotFoundError`
   (no checkpoint) / `RuntimeError` (checkpoint unloadable, e.g. no
   torch); the harness converts a first-question failure into exit 2
   instead of scoring a suite of error rows. Verified: `--mode
   classifier` with no checkpoint exits 2 with Lane C's message.

## Verification (this VM, CPU, rule-based — the only mode that runs here)

Command: `python3 tests/integrated_backtest.py --mode rule-based
--suite all --json-out /tmp/impl_laneE_rulebased.json`
(recorded at git HEAD `792c75f`, dirty — other lanes' in-progress files
present; my files untracked at the time).

| Suite | Measured | Baseline (mode-qualified) | Delta |
|---|---|---|---|
| validation | **261/500 = 52.2%**, Wilson [0.4782, 0.5654], micro-P 0.8905 / R 0.4623 / F1 0.6086, TP/FP/FN 423/52/492, silent 212; per-lang EN 209/235, KN 30/153, Kanglish 22/112 | 261/500, same micros/TP/silent (`docs/recall_status.md` §3) | **MATCH, +0** |
| kaanoon | **14/28 = 50.0%**, Wilson [0.3263, 0.6737], 0.7500 / 0.6000 / 0.6667, 27/9/18, silent 6 | 14/28, same (`docs/recall_status.md` §3) | **MATCH, +0** |
| 16-Q | **14/16 = 87.5%**, Wilson [0.6398, 0.9650], 1.0000 / 0.9623 / 0.9808, 51/0/2, court 13/16, esc 16/16, kinds strict 10/16, silent 0, Fp 0, misses H6 (pwdva-18) + H14 (hma-13) — same two as the baseline; **rating raw 9.1 → capped 9.0** | 14/16, same metrics, **rating 7.6** (Fb 3, Fp 0) | exact **MATCH**; rating **+1.4, explained**: Fb is unmeasured via C1 (0 instead of 3 → +1.5 in the raw formula), so 9.0 is a **provisional upper bound, not a measured 9.0**. The frozen scorer's measured rating is 7.6. Do not quote 9.0 without the qualifier. |
| brutal | **210/230 = 91.3%**, Wilson [0.8695, 0.9430], 0.9974 / 0.9205 / 0.9574, TP/FP/FN 382/1/33, court 215/230, esc 213/230, kinds strict 152/230 (FE 170/230), silent 15, per-cat_min 0.0625 (C13 1/16); §3.2 bar FAIL (silent 15, per-cat 0.0625) | Recorded evidence baseline 215/230, 1.0 / 0.9325 / 0.9651, 387/0/28, court 215/230, esc 230/230, kinds 184/230, silent 15 (`results/live-laya-v7-results.md` §2, pre-recall-swarm code) | **−5 exact, −17 esc_bool, −32 kinds strict — a real finding, see below.** Current-code frozen-scorer reference is **210/230 with identical aggregates** (see Verification note). The headline "Brutal 230/230" is the NEURAL `laya`/CUDA number, never a rule-based expectation. |

### Verification notes

- **Scorer-mirror check.** The harness's 16-Q and Brutal aggregates were
  diffed against fresh `tests/v7_backtest.py --suite {16q,brutal} --mode
  evidence --device cpu` runs: identical on every field except
  `fb_count` (3→0 on 16-Q, 58→0 on Brutal — the C1 gap above) and
  `latency_mean_s` (0.002→0.001 s, timing noise from per-question
  `run_question` calls vs the batched assess). Per-category tables
  identical, including Brutal C13 1/16.
- **Brutal −5 (215 → 210) is a recall-swarm regression on evidence mode,
  not a harness artifact.** The 20 misses are the same 15 C13 Kannada
  items (B-203–B-217, all silent — the known Kannada gap: evidence mode
  has no NLLB translation) PLUS 5 English misses that the recorded
  baseline did not have: B-024, B-027, B-075, B-086, B-127 (top FNs
  pwdva-20 ×10, bnss-144 ×6, gwa-1890 ×5, bns-316 ×4; the single FP is
  hma-9 on B-075). Escalations regressed further than exact: esc_bool
  230→213, kinds strict 184→152. The only pipeline changes since the
  v7 verification runs are Lane 03's anchor hardening (evidence.py,
  5 rounds) and Lane 08's route fixes (extractor/graph) — the likely
  suspects, but causation is NOT established here; no bisect was run
  (out of Lane E scope). Flagged for the coordinator / Lane F.
  The §3.2 bar verdict is unchanged in shape vs the recorded baseline
  (it already failed on silent 15 + C13 then).
- **16-Q rating.** The harness prints 9.0, but the honest measured
  rating under the frozen scorer is 7.6. The +1.4 is entirely the
  missing −0.5×3 Fb term. Treat the harness's 16-Q rating as an upper
  bound until Lane C exposes pre-gate data.
- **Guardrails (all run after the harness landed):**
  `tests/test_graph_v4.py` PASS (34 sections / 66 nodes / 99 edges,
  0 dangling, 7/7 frozen hashes intact);
  `tests/test_prose_renderer_v2.py` PASS (246 cases, Fp=0,
  quality_flags=0, 15/15 mutants);
  `python3 -m unittest discover -s tests -p "test_*.py"` → **Ran 66
  tests — OK** (the harness file is `integrated_backtest.py`, not
  `test_*.py`, so it is not collected; the suite count is unchanged).
- **Other checks:** `--self-test` PASS (14 checks, incl. sealed-guard,
  suite-sealed refusal, SHA verification, C1 key validation, toy
  16-Q rating math, Fp facts regression);
  `--suite sealed` exits 2 with the sealed message;
  `--mode classifier` with no checkpoint exits 2 (Lane C's
  FileNotFoundError surfaced);
  `--mode auto --suite 16q` reproduces 14/16 (falls back to
  rule-based with `fallback_reason` set).
- **What the JSON contains.** `/tmp/impl_laneE_rulebased.json`:
  per-set results with full rows, exact command, git HEAD `792c75f`,
  runtime `src/laya_integrated.py`, SHA verifications (validation OK,
  brutal OK).

## What still needs the Colab GPU run (not runnable here)

- **Classifier-mode backtest** (`--mode classifier` / `--mode auto`
  with a real checkpoint): no checkpoint exists yet
  (`models/v71-classifier/best/model.pt` absent) and this VM has no
  torch. Needs Lane D's notebook (contract C4): Train Run #1 on Colab
  T4, then this same harness command with `--mode classifier` (or
  `auto`) on the same four suites. The harness already handles the
  classifier path (per-question `run_question`, first-failure abort,
  per-question error rows after that).
- **Sealed re-run** (Fresh-20 / Kannada-8): Colab/RTX only, by design.
  Nothing in this harness touches sealed files.
- **16-Q rating to a measured number**: needs the Fb gap closed (Lane C
  pre-gate exposure, §drift-3) or a frozen-scorer cross-check alongside
  the harness run.

## Files

- `tests/integrated_backtest.py` — the harness (new).
- `docs/impl_laneE_harness.md` — this file (new).
- No frozen file touched; no other file edited. Lane C's
  `src/laya_integrated.py` was read, never modified.
