# Lane 10 — P7 scorer honesty + calibration + CI (V71-P7-1 / P7-3 / P7-4)

**Status: DONE (code + CPU verification). Live backtest / RTX items blocked as noted.**
**Files owned (only these touched):** `tests/v7_backtest.py`, `src/laya_calibration.py` (new),
`.github/workflows/laya-ci.yml` (new), `scripts/ci_gate.py` (new).
No other lane's files edited; no frozen files touched; no git write commands run.

## 1. Scorer — `tests/v7_backtest.py` (V71-P7-1)

### Fb definition (frozen for this scorer; also in the file docstring)
Fb = count of (question, section) pairs where a section in
`candidates_before_gate` was proposed pre-gate but Stage 2 gated it out for a
statutory-prerequisite reason. Read order per contract C1: (1)
`rec["candidates_before_gate"]` (primary), else (2) `rec["dispositions"]` keys
(the same disposition set, present in every current `assess_v7` record), else
(3) `rec["kept_ids"]` only — with `fb_measured=False`; a 0 from that fallback
is flagged as NOT a measured 0 (`fb_warning` in the output).
A non-kept candidate counts iff it matches one of the 6 frozen forbidden
mappings OR Stage 2 gated it out for a statutory-prerequisite reason
(disposition status conditional / needs_fact / inapplicable with a
statutory-gate reason code, or an entry in `rec["gated_out"]` naming it).
The 6 mappings (Gate §5 Fp items 1–6): Rajnesh-for-Stridhan, Satish-for-custody,
HMA 13/13B when divorce not asked, residence-as-tenancy, ask-user-to-pick-court,
birth-certificate-under-HMA. **Candidate-level detectability:** only mapping 3
(hma-13/hma-13b, reason `divorce_not_expressly_asked` / gated_out "divorce not
asked") has a section-candidate signature. Mappings 1, 2, 4, 5, 6 are
citation/label/prose errors with no section signature — they are NOT
double-counted in Fb; they are enforced where observable, in prose via
`prose_forbidden_check` Fp items 1, 2, 4, 5, 6. The operative measurable part
of Fb is the statutory-gate clause, which subsumes the canonical Gate §5
examples (HMA 25 no decree, HMA 24 no proceeding, HMA 13/13B divorce not
asked, HMA 26 no proceeding, HMA 27 D2 no HMA proceeding, PWDVA s.2(a)
failure, male self-maintenance outside HMA, adult-child BNSS 144).
Deliberately NOT counted: `superseded_*` dispositions (hma-13 inapplicable
because hma-13b is eligible, gwa-1890 superseded by hma-26) — correct routing.
Rating formula now applies `-0.5 * Fb - 1.0 * Fp` (Fb term was missing).

### Gate §2 caps
`apply_gate_caps()` (pure, unit-tested) computes BOTH `raw_formula_rating`
and `capped_rating`; `rating` is now the **capped** rating (previously the
uncapped formula — behaviour change, documented in the file). Caps: Fp>=1 →
≤5.0; Fb>=1 → ≤9.0; G12 unverified → ≤9.0; prose not measured → ≤9.0; sealed
not passed → ≤9.0; confirmation missing → ≤9.0; errors>=3 → ≤5.0. Flags
default to unverified, so a bare run can never print an uncapped 10.0.
New CLI flags: `--g12-verified`, `--sealed-passed`, `--confirmation-run`.
`caps_applied` lists every binding cap in the JSON output.

### H12 masking stopped
Per-row `esc_ok_strict` (no safety removal, no H12 special case) and
aggregate `esc_bool_strict` + `esc_bool_legacy_compat` are reported alongside
the legacy `esc_bool` (kept for backward compat). A dedicated `h12` object
reports `strict_esc_ok` vs `legacy_esc_ok` and strict kinds for H12 when
present. Legacy columns were kept, strict columns added — nothing hidden.

### Sealed diagnostic telemetry (blind_text=True preserved)
For sealed suites only, aggregate `sealed_diagnostics` (IDs + counts, zero
question text): hma-27 note IDs F8/F9/F10/F16/KN3 — per-ID exact + hma-27
TP/FN/FP, suite-wide counterfactual `exact_count_ignoring_hma27`; court note
IDs F1/F2/KN1 — expected vs predicted court + `alt_forum_ok` (would the
predicted court pass if the expected forum were the other one).

### --strict
`--strict` asserts Brutal-230 `esc_kinds_strict >= 200/230` and
`per_cat_min >= 0.75` (other suites: per_cat_min only; their strict kinds are
reported, the 200/230 bar is Brutal-specific), prints `STRICT FAIL` lines and
exits 2. 191/230 is flagged FAIL. Per-suite `strict_pass` is in the JSON.

### CLI / output compatibility
`--suite/--mode/--device` unchanged; all new output fields are additive
except `rating`, which is now capped (raw preserved as `raw_formula_rating`).

## 2. Calibration — `src/laya_calibration.py` (new, V71-P7-3)
Pure-Python core (`math` only): per-head temperature scaling (log-grid +
golden-section NLL minimisation), isotonic PAVA sanity check, ECE, multi-class
Brier, risk-coverage/AURC, auto-accept precision. Gates: ECE ≤ 0.03,
Brier ≤ 0.04, AURC ≤ 0.02, auto-accept (≥ tau_high) precision ≥ 0.99; gray band
[tau_low, tau_high) routes to clarification only. `torch` is lazily guarded
(`torch is None` here); `fit_temperature_torch` raises a clear RuntimeError
without torch (RTX parity wrapper). Loader refuses test-bank provenance and
enforces n ≥ 500. **Code only — no fitting done here** (no GPU/torch, no
calibration split yet). Exact RTX commands in the module docstring:
`python -m src.laya_calibration --calibration-file data/synthetic_v7_1/calibration.jsonl --out results/calibration-v71.json`,
then `--report-only` on a fresh dev slice, then `--torch` parity check,
then the backtest.

## 3. CI — `.github/workflows/laya-ci.yml` + `scripts/ci_gate.py` (new, V71-P7-4)
Workflow (7 jobs): frozen-sha-graph (`python -m tests.test_graph_v4`),
unit-permutation (`python -m unittest discover -s tests -p "test_*.py" -v`),
prose-safety (`python -m tests.test_prose_renderer_v2`), leakage
(`python -m scripts.check_ngram_leakage --strict`), license
(`python scripts/ci_gate.py --gate license`), latency-determinism
(`python scripts/ci_gate.py --gate latency-determinism`), ci-gate-summary
(`python scripts/ci_gate.py --all`). YAML validated.
`ci_gate.py` reports each gate pass/fail/blocked (never a silent pass);
exit 0 = all pass, 1 = any fail, 2 = any blocked (unless `--allow-blocked`,
local triage only, never in CI). Latency-determinism runs the 16-Q
`student_onnx` smoke twice when the artifact exists and compares outcome
SHA-256 (latency/wall excluded), mean < 0.5s/Q, max ≤ 1.0s/Q.

## 4. Checks actually run here (this VM, CPU-only, no torch)
- `python3 -m py_compile` on all three Python files: OK.
- `python -m tests.v7_backtest --self-test`: **PASS, 18/18 checks, exit 0**
  (Fb hma-25/hma-13-mapping-3/hma-27-D2, superseded not counted, unmeasured
  old-format, all cap cases incl. defaults→9.0 and all-clear→10.0, strict
  191 FAIL / 200 pass, sealed diagnostics aggregates-only). One check was
  fixed during verification: my test expectation for `alt_forum_ok` was
  wrong, the code was right.
- `python -m src.laya_calibration --self-test`: **PASS, exit 0** (temperature
  recovery 1.86 vs true 2.0, NLL reduced, isotonic monotone, torch guard
  raises). Synthetic smoke only — not a result.
- Guardrails: `python tests/test_graph_v4.py` PASS (34/66/99, 7/7 SHAs);
  `python -m tests.test_prose_renderer_v2` PASS (246 cases, Fp=0, 15/15 mutants).
- `python scripts/ci_gate.py --all`: **3 pass / 1 fail / 2 blocked, exit 1**
  - PASS frozen_sha, unit (49 tests, 0.297s — torch not needed for the
    current unittest set), prose.
  - FAIL license: `src/laya_v7_extractor.py:24: facebook/nllb-200-distilled-600M`
    still the default — **expected at baseline; Lane 06 (V71-P3-1) must
    retire it before this gate can pass.** (Dedupe fix applied: the
    `facebook/nllb-200` substring no longer double-counts the same line.)
  - BLOCKED leakage: `scripts/check_ngram_leakage.py` not present — Lane 02
    has not landed it yet (`scripts/build_synthetic_corpus.py` exists).
  - BLOCKED latency-determinism: `models/student_int8.onnx` absent — Lane 08
    has not landed the artifact yet (its `src/laya_v7_student.py` exists and
    is scanned clean by the license gate).

## 5. Blockers / what needs RTX or a human
- **No live backtest run here** (by design): `assess_v7` needs torch; the
  scorer's live path is unverified until an RTX run. Run on RTX 5050:
  `python -m tests.v7_backtest --suite all_with_sealed --mode laya --device cuda --misses 0`
  (add `--strict`, and `--g12-verified/--sealed-passed/--confirmation-run`
  only when those are genuinely true). Expected honest outcome on current
  code: Brutal rating capped at 9.0 by default (G12/sealed/confirmation
  unverified) even at 230/230; `--strict` will FAIL on 191/230 esc_kinds
  until the typed-escalation bar is actually cleared.
- Lane 01 has not landed `candidates_before_gate` in `src/laya_v7.py` yet
  (file unmodified in this copy); Fb is measurable meanwhile via the
  `dispositions`-keys fallback, and the scorer records its source per run.
- Calibration fitting needs Lane 02's split (n ≥ 500, zero test-bank
  overlap) + RTX torch; human gates G12 / P2.1 remain open (caps bind).
- Concurrent-lane note: other lanes are editing the same working copy
  (`src/laya_family_evidence.py`, `src/build_graph_v4.py` modified;
  Lane 07/08 status files present). I touched only my four files.
- One exec result during this session carried a security notice; no content
  from it was executed — verification ran only my own new files and the
  repo's own guardrail test commands.
