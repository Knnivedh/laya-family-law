# LAYA v7.1 / 10x — Live Execution Status Tracker

Owner: Lane 11 (docs/repo). Coordinator owns the merge/push; this file is the live tracker only.
Baseline: `bc7f40f` + plan `f4cfd6f` + swarm state `167af57`. Working copy: `~/workspace/laya-v71-work`.
Last updated: 2026-11-27 ~18:19 IST (coordinator, Lane 01 merge — commits `c9da5f1` + `28f5424`; ALL 11 LANES MERGED).
Rule: every status line cites its source lane file or a command Lane 11 ran. Nothing here is invented.

## How to read this file

- `pending` = no lane status file has landed yet for that task (directory `docs/10x_swarm_state/` was empty at last check).
- `done / blocked / needs-RTX / needs-human` are only used when a lane file or a run states them.
- Test pass lines are recorded ONLY for suites Lane 11 actually ran on this VM (see §2).

## 1. Phase 0 tasks

| Task | Lane | Owner files | Status | Source |
|---|---|---|---|---|
| V71-P1-1 — Section A code/rule bugs (laya_v7.py, laya_v7_graph.py, laya_v7_evidence.py, laya_v7_extractor.py, laya_prose_v2.py) | 01 | `src/laya_v7*.py`, `src/laya_prose_v2.py` | **done** — merged commit `c9da5f1` (235 insertions / 38 deletions); C1 genuine `candidates_before_gate`; 16-Q evidence-mode re-run by coordinator: exact 14/16, esc_bool_strict 16/16, esc_kinds_strict 10/16, fp_prose 0 | `docs/10x_swarm_state/lane-01-p1-1.md`; coordinator re-run `python -m tests.v7_backtest --suite 16q --mode evidence --device cpu` |
| V71-P7-1 — Scorer honesty (Fb, §2 caps, H12, esc_kinds >= 200/230 flag) | 10 | `tests/v7_backtest.py` | **done** — merged commit `77d9bac`; self-tests 18/18 PASS; open follow-up: `compute_fb` H12 empty-candidates fix (see swarm state) | `docs/10x_swarm_state/lane-10-p7.md` |
| V71-P6-1 partial — prose `status="ok"` + `proceeding_pending_hma` fix | 01 | `src/laya_prose_v2.py` | **done** — merged commit `c9da5f1`; coordinator also applied the EN item-8 fix as `28f5424` (bare-comma false fire) | `docs/10x_swarm_state/lane-01-p1-1.md` |
| V71-P4-4 — D-V4-1..4 + ground-truth-v3 ratification | 07 | `docs/ground-truth-v3-ratification-pack.md` (prep) | **done (prep only)** — merged commit `4cc53ba`; needs-human (independent rater ratifies GT-v3; see §4) | `docs/10x_swarm_state/lane-07-p4.md`; plan §4.4 |

Phase 0 exit gate (plan §8.1 / `docs/10x_swarm_state.md`): Brutal-230 esc_kinds_strict >= 225/230
(NEEDS RTX 5050 confirmation run — cannot verify on this VM), Fb genuinely measured = 0,
42/42 + expanded unit tests pass, 16-Q reconciled cleanly under ground-truth-v3 (ratification pending human rater).

## 2. Test results actually run on this VM (Lane 11, 2026-11-27 ~18:10 IST)

These are BASELINE runs on the clean tree (HEAD `167af57`, no lane code landed yet). They are
not Phase 0 verification — they prove the baseline was intact before lanes started.

| Suite | Command | Result (exact pass line) |
|---|---|---|
| Graph v4 + frozen SHA | `python3 tests/test_graph_v4.py` | PASS: `GRAPH V4 + FROZEN SHA TEST PASS: 34 sections / 66 nodes / 99 edges, 0 dangling edges, 7/7 frozen hashes intact.` (exit 0) |
| Prose renderer v2 | `python3 tests/test_prose_renderer_v2.py` | PASS: `PROSE VALIDATION PASS: 246 cases, Fp=0, quality_flags=0, 15/15 adversarial mutants caught, mean=0.0163ms, max=0.132ms` (exit 0) |
| Full unit suite | `python3 -m unittest discover -s tests -p "test_*.py"` | `Ran 42 tests in 0.122s — OK` (exit 0) |

Notes:
- No torch on this VM (`python3 -c "import torch"` fails) — no neural run, training, distillation,
  or T4 run is possible here. Any RTX/T4 numbers must come from the user's RTX 5050 machine or Colab.
- Prose latency vs plan §0: plan records mean 0.0351ms / max 0.12ms; this run measured
  mean 0.0163ms / max 0.132ms. Counts identical (246/246, 15/15, Fp=0). Timing-only variance, not a gap.

## 3. Plan-vs-code mismatches (from Lane 01's status file)

Lane 01 has filed `docs/10x_swarm_state/lane-01-p1-1.md`. Confirmed mismatches:
1. Graph joint-property condition is at **L512, not L511** (the plan's "off-by-one" note is itself off by one). Fixed at L512.
2. `stay_in_house_under_eviction_pressure` is read at **L364, not L530** as the plan cites.
3. Confirmed EXACT (no mismatch): L430 (divorced wife + adult child → bnss-144), L506 (bns-316 sex check), L417 (extractor residence block removed), L558/L625 prose lines (P6-1 partial).

Earlier plan corrections PC-1 (mmBERT license MIT, not Apache-2.0), PC-2 (vocab reconciliation — sharpened at Lane 02 merge), PC-3 (Parity Guard thresholds are Lane 08's implementation choice), PC-4 (ci_gate `--strict` mismatch — RESOLVED), PC-5 (v4.1 label collision — open decision) live in `docs/10x_swarm_state.md`.

## 4. What Phases 1–4 need before they can start

| Need | Phases | Source |
|---|---|---|
| GPU — user's RTX 5050 (or Colab T4) for all neural runs: teacher training, distillation, ONNX parity, Brutal-230 esc_kinds >= 225/230 confirmation, G14-T4 parity (0 flips) | 0 (confirm), 1, 3 | plan §5, §8.1; swarm state guardrails ("This VM has NO GPU and NO torch") |
| Human — independent legally trained rater to ratify D-V4-1..4 / ground-truth-v3 (never editing frozen GT-v2, SHA 87818b1b…) | 0 (P4-4 gate), 4 (brutal-bank-v2 authorship + 25% second rater + adjudication) | plan §4.4, §7.2 |
| Human — G12 blind legal rater (2 raters, 25% double-rating) + P2.1 native Kannada speaker/legal reviewer | 4 (P6-3); lifts the <= 9.0 prose cap | plan §6.2–6.3 |
| Human — P2.4/P2.5 primary-judgment verification (Balkrishna, Babulal, Krishna Kumar Gupta, Pratibha Rani, Satish Chander Ahuja, Rajnesh metadata, Astha Thakur paras 3–13, 15–17, 19) | 2 (P4-2) | plan §4.2 |
| Decision — LICENSE choice: Lane 06 drafts Apache-2.0, flagged as pending owner confirmation (contract C5) | 2 (P3-1) | swarm state contract C5 |
| Decision — Phase 0 gate outcome: whether esc_kinds_strict >= 225/230 is met on RTX before Phase 1 proceeds | 0 → 1 | plan §8.1 |
| Code dependency — Lane 02 corpus schema (contract C2) before Lane 03 classifier code can be validated against it; Lane 01 `candidates_before_gate` (contract C1) still to land — Lane 10 is DONE and measures Fb meanwhile via the dispositions fallback, source recorded per run | 1 (P1-2→P1-3), 0 (P1-1→P7-1, fallback in place) | swarm state contracts C1, C2; lane-10-p7.md. UPDATE 2026-11-27 ~18:18 IST: C2 now VERIFIED end-to-end — Lane 03's loader reads Lane 02's corpus 4500/4500 OK (only unknown key `in_scope`); remaining item is the one-key vocab pin (PC-2), not the schema itself. |

## 5. Lane status board (from `docs/10x_swarm_state/lane-*.md` files)

Updated by coordinator 2026-11-27 ~18:15 IST (Lane 03 merge). Source: `docs/10x_swarm_state.md` status board.

| Lane | Task | Status |
|---|---|---|
| 01 | V71-P1-1 + P6-1 partial (Section A bugs) | **DONE** — merged commit `c9da5f1` (235 insertions / 38 deletions, 5 files); C1 genuine `candidates_before_gate`, P6-1 partial done; 16-Q evidence-mode re-run by coordinator: exact 14/16, esc_bool_strict 16/16, esc_kinds_strict 10/16, fp_prose 0; mismatches L512-not-L511 + stay_in_house-L364-not-L530; queued specs from Lanes 05/07/06 NOT applied — see open follow-ups; coordinator applied EN item-8 fix separately as `28f5424` |
| 02 | V71-P1-2 synthetic corpus + leakage gate | **DONE** — merged commit `c718f36` (builder + gate + 5,000-record corpus, train sha256 8777bddd…); leakage re-run by coordinator: 0 8-grams, max cosine 0.8182, exit 0; rebuild verified byte-identical; C2 verified end-to-end (Lane 03 loader 4500/4500 OK); sealed check QUEUED (trusted command recorded, not run); PC-4 resolved (`--strict` added, ci_gate now 4/1/1); KN templates have had no P2.1 audit; vocab reconciliation sharpened — see PC-2 |
| 03 | V71-P1-3 multi-head classifier (code only) | **DONE** — merged commit `7d34f05` (`src/laya_v7_classifier.py` 699 lines, `scripts/train_v71_classifier.py` 584 lines); code only, no training run; blocked on Lane 02 corpus; vocab assumption (11 issues / 28 facts) needs coordinator reconciliation before GPU run — see PC-2 |
| 07 | V71-P4 legal registry + citations + safety | **DONE** — merged commit `4cc53ba` (registry JSON 9 authorities / 1 verified_primary; crosswalk module, CPU self-test 31/31 PASS; GT-v3 ratification pack PREP ONLY, v3 NOT created); safety decoupling as patch SPEC queued for Lane 01; 8 authorities need human primary-judgment verification |
| 08 | V71-P5 distillation + ONNX + T4 notebook | **DONE** — merged commit `6149de9` (distill + student + ONNX export + Colab builder + 9-cell notebook, nbformat.validate PASS); scripts/design only, no GPU run; blocked on Lane 02 corpus, Lane 03 teacher, Lane 06 licence; Parity Guard thresholds need coordinator confirm — see PC-3; vocab reconciliation open — see PC-2 |
| 04 | V71-P1-4/P1-5 maintenance + clarification | **DONE** — merged commit `90dc517` (evidence fixes +281/−21; clarification-fallback-spec.md); evidence-only stub harness lane-reported 162 rows, 0 mismatches / 0 FP after fix (35 before); real 34/34 proof needs RTX CUDA run; spec adopts Lane 05's clarifier entry points as normative (deltas D-1/D-2) — Lane 04/05 reconciliation closed |
| 05 | V71-P2 unified runtime + Graph v4.1 + multi-turn | **DONE** — merged commit `17fff27` (schema + graph engine + runtime + clarifier + v4.1 JSON 36/68/104, SHA-256 27b03d4c…; build_v4_graph() output verified identical to disk v4); v4.1 validate True, 0 problems, reachability 68/68 from single root; C4 wrapper-refactor patch spec queued for Lane 01; v4.1 label collision — see PC-5 |
| 09 | V71-P6 Kannada prose + audit packets | **DONE** — merged commit `e69433a` (KN prose 20/20 sections, 9/9 kinds, all DRAFT pending P2.1 native-speaker sign-off; 25 KN mutants, 7/7 OK; blind audit packet exporter); full unit suite now 49 tests OK; patch spec queued for Lane 01 (incl. EN item-8 amount-pattern fix) |
| 10 | V71-P7 scorer + calibration + CI | **DONE** — merged commit `77d9bac` (honest Fb via `compute_fb`, raw + capped ratings, H12 unmasked, blind sealed diagnostics, `--strict`; calibration module; CI workflow + ci_gate); self-tests 18/18 + calibration PASS; ci_gate at merge: 3 pass / 2 fail (license NLLB default — expected; leakage `--strict` mismatch — see PC-4) / 1 blocked (latency-determinism, no ONNX artifact) |
| 06 | V71-P3 multilingual + licensing | **DONE** — merged commit `01b686b`; LICENSE Apache-2.0 draft pending owner confirmation |
| 11 | Docs tracker + push manifest | **DONE** — merged commit `50a2855`; tracker updates now fall to the coordinator |
| 01 | Phase 0 lane (P1-1 + P6-1 partial) | **DONE** — see row above. **No lanes running. All 11 lanes merged.** Open follow-ups (not lane work): Lane 07 safety patch spec, Lane 05 wrapper-refactor spec, Lane 06 NLLB retirement, Lane 10 compute_fb H12 fix, PC-2 Lane 08 vocab re-alignment, PC-5 v4.1 rename decision — see `docs/10x_swarm_state.md`.

Note: the §4 dependency row "Lane 02 corpus schema (C2) before Lane 03 classifier code can be validated against it" still stands — Lane 03's code is written against the C2 contract from plan §1.2 and must be reconciled with Lane 02's actual schema/corpus at merge.

## 6. Plan-document verification (Lane 11, 2026-11-27)

Spot-check of `docs/10x_plane.md` (commit `f4cfd6f`) — see `docs/10x_swarm_state/lane-11-docs.md` for detail.
Result: COMPLETE on all three spot-checks.
- §0 baseline table: 7/7 rows present (Brutal-230, 16-Q, Sealed Fresh-20, Sealed Kannada-8,
  Brutal-230 CPU, Codex Maintenance 4-split, Offline Verification Suite).
- §8.1 phased roadmap: 5/5 phases present (Phase 0–4), all four Phase 0 tasks named in the Phase 0 row.
- §8.3 scorecard: 9/9 rows present (Fresh-20, Kannada-8, Brutal scale/CI, Maintenance, Multi-Turn,
  Fb/Fp, Latency, License, Calibration).
- Cross-references checked exist: `docs/brutal-test-200-plan.md`, `results/live-laya-v7-results.md`,
  `graph/laya-crpc-bns-section-decision-tree-v4.json`, `tests/v7_backtest.py` — all present.
- Caveat: the user's pasted plan text was NOT supplied to Lane 11, so this is a structural /
  internal-consistency check, not a line-by-line diff against the paste. One timing-only variance
  noted in §2 (prose mean/max ms); no content gap found.
