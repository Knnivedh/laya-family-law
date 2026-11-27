# Brutal v6 build — merged report (FULL end-to-end backtest)

**Status: BUILT AND VALIDATED. Ready for the live Colab run.**
**Date:** 2026-11-27. **Work:** offline only — no live run, no Colab, no browser.
**Coordinator:** merged from Lane A (labels + graph v3) and Lane B (v6 notebook build), validated independently by the coordinator.
**Scope cut applied 10:51 IST (user: run NOW, do not wait):** prose renderer NOT built — Fp is NOT MEASURED in this round, recorded honestly, never faked. Kannada native-speaker confirmation, typed escalations (D5/D9), and all other open items were NOT waited on.

## 1. Deliverables (paths + SHA-256, all verified by the coordinator)

| File | SHA-256 | Notes |
|---|---|---|
| `live-laya-colab-test-v6-brutal.ipynb` (v6 notebook, 24 cells, 184 KB) | `d6ee579534b5f2ac0b836f834954afe73fd5480d0da7a7a9fc5bec6e2461ff98` | Builder re-run byte-identical (coordinator re-ran it, exit 0, same SHA) |
| `build_laya_v6_brutal.py` (builder) | `184657d96facf697f2aaee7db8cdff8e3dcb2c4b889a2295e7fddcc3c7e2cc7b` | Deterministic; two consecutive runs identical |
| `v6-laneB-build-note.md` | `d28b14cb1a281b1488076e25f7c76033cab419d181f4dd9cc54a3df3f3e4a0d7` | Per-cell changes, kind table, G2 text, gaps |
| `../laya-crpc-bns-section-decision-tree-v3.json` (graph v3) | `67bf2b04ca946f7c7fa3062068e01ce051fbce8f4d740c281afe6fff841c34a5` | 34 sections / 48 nodes / 79 edges |
| `graph-v3-change-log.md` | — | D2 patch + two new sections, counts, recovery-text location |
| `brutal-bank-v1-frozen.json` (frozen bank, 230 q) | `934a2b2265ac137c96939e1fbeca3682a037010e42f972bfd459c2fcac4ec717` | UNCHANGED — verified after build |
| `sealed/sealed-fresh-20.json` | `1d8b5dc376e711c3ac6ead4424bb2d8ce52b07552b9a533ad86e0616dbcf8837` | UNCHANGED |
| `sealed/sealed-kannada-8.json` | `2f652af1123a22441cc4158ddf480ef0981aa923858bbcb9dc3622f5e5c25853` | UNCHANGED |
| `ground-truth-v2-hma27-A.json` (v2 GT, 53 sections) | `87818b1b659583bf06a25280a6b53dabedf65f29cab99058f02b8ed31c9ac97e` | UNCHANGED |
| `../laya-crpc-bns-section-decision-tree-v2.json` (graph v2) | `c7e095ad185242e9360d8b9f180fefff894f5677b52d188174413a32a2704255` | UNCHANGED |
| `hma27-D2-gate.patch` | `6349c922944275d26bdc38f6c725daee12ddcd25f86f39ae1485f104e507fc04` | Applied into graph v3 |

All paths under `workspace/goals/english-family-law-chatbot-retest/files/` (`laya-graph/` unless marked `../` = `files/`).

## 2. What was built

**Lane A — graph v3 (labels).** D2 patch applied to a copy of v2 (verified: R-HMA27-04 `if_fail` now `"drop"`, 0 occurrences of "alternatively", all 17 G-edits present, intermediate counts still 32/46/77, intermediate SHA identical to the D2 validation log). Two new sections added in the existing schema, each with all 14 fields and a choice-type `laya_question`, grounded on the bank question + statute text verified against India Code sources: `hma-9` (HMA s.9 restitution of conjugal rights, for B-018) and `pwdva-22` (PWDVA s.22 compensation orders, for B-019; entry distinguishes s.22 compensation from s.20/BNSS-144 monthly support and notes the s.2(a) woman-only limit). +2 nodes (`stage2:hma-9-leaf`, `stage2:pwdva-22-leaf`) and +2 edges. Counts 32→34 sections, 46→48 nodes, 77→79 edges; version 3.0, date 2026-11-27.

**Lane B — v6 notebook (24 cells).** Base: v5 notebook (9 cells). Cell 5: upload graph v3, assert **(34, 48, 79)** + SHA `67bf2b04…`. Cell 5b: upload frozen bank, verify SHA `934a2b22…` + 230 questions, read-only. Cell 6: corrected v2 GT (53 sections) with frozen fact `being_filed` (True only on stated / will-file / instructed filing; "I want a divorce" does not count; False ×16 on the regression set). Cell 7: D2 drop-gate for HMA 27 (drop, not escalate, when no proceeding is pending/being filed), all v5 fixes kept (evidence gates, custody gate, single-issue guard, H14 route, v3 thresholds), stale "skeleton — fixes pending" header fixed, recovery text amended to the D1-A wording, per-question pipeline refactored into `run_one_question` (dedent-equivalence verified; no logic/threshold/prompt change). Cell 8: 16-question regression scoring + shared `score_batch` helper. Cells 9–18: batches B1–B9 (25 each: B-001..B-225) + B10 (5: B-226..B-230), each saves + downloads its per-batch JSON immediately and prints batch + cumulative summaries; NO tuning between batches (stated in every batch cell). Cell 19: sealed upload + verify (read-only). Cell 20: fresh-20 run + score. Cell 21: Kannada-8 run + score. Cell 22 (final): cumulative brutal scoring (230) + regression + sealed summaries + pass/fail vs plan §3.2, Wilson interval, brutal rating (capped 9.0, Fp NOT MEASURED), gate-row summary, G14 check print. **Cell 9 prose: SKIPPED entirely per the 10:51 IST scope cut.**

**Escalates — dual scoring.** Every batch, sealed section, and the final cell report BOTH the old boolean escalates score AND the typed-kinds score. Kind derivation from kept sections + facts covers the bank's vocabulary (quantum, court, demand, custody, residence, recovery, procedure, fact, safety); `esc_live` = {quantum, court, demand, custody, residence, recovery, procedure, safety}. Underivable kinds are recorded as known scoring gaps (see §6), never silently mapped to True.

**Sealed sets.** Both SHAs verified against the freeze note before scoring. ID normalisation checked: the pipeline already emits `hmga-1956-s6` / `welfare-principle`, so the mapping is identity; only court names are normalised. F20 scored under the human-lawyer rule (out-of-scope, GT empty, escalates True as a handoff — the F20-specific rule wins). Pre-D1-A HMA 27 in sealed GT (F8/F9/F10/F16, KN3) is scored as frozen with GT-rule notes, not as plain system errors and never edited.

**Latency.** Per-question latency recording kept from v5; G14 check print in Cell 8 and the final cell (mean ≤15 s, max ≤30 s, full 16-run ≤240 s excl. load, load ≤60 s). Expect FAIL on CPU — v5 mean was 61.93 s (max 138.2 s). Nothing tuned to pass it. T4 unverified; no T4 numbers claimed.

## 3. Coordinator validation (independent, run by the coordinator after Lane B)

- Notebook SHA matches Lane B's claim (`d6ee5795…`); builder SHA matches; build-note SHA matches.
- `nbformat.validate`: PASS (24 cells, 23 code). All code cells compile: **zero failures** (IPython `!pip` magic excluded as in v5).
- Builder re-run by the coordinator: exit 0, byte-identical SHA `d6ee5795…`.
- Key strings present: `(34, 48, 79)`, graph SHA, bank SHA, `being_filed`, `score_batch`, sealed filenames, `G14`, `NOT MEASURED`. Old wrong recovery wording ("civil recovery under HMA s.27") ABSENT; FCA s.7(1) wording present.
- Cell inventory matches the build note exactly: 0 markdown; 1–4 unchanged; 5 graph v3; 5b bank; 6 v2 GT; 7 pipeline; 8 regression; 9–18 B1–B10; 19 sealed upload; 20 fresh-20; 21 Kannada-8; 22 final (index 23).
- Frozen files verified unchanged after the build: bank, both sealed sets, graph v2, v2 GT (SHAs in §1).
- Lane B's own verification (recorded in its build note): builder exit 0 twice, byte-identical; Cell 6 exec PASS (16 questions, 53 sections); HMA25 + HMA27 shadow tests PASS; stub-agent D2/kinds test PASS; stub `score_batch` test PASS.

## 4. Live-run sheet (for the parent — the live Colab run)

Account: nivedhbhat15@gmail.com (already signed in for the v5 run; if a sign-in step appears, use the saved login — never guess a password). Runtime: CPU (torch 2.14.1+cpu), ~4 hours for the full run at ~60 s/question. Do NOT use T4 — unverified and not approved.

1. Open Google Colab. File > Upload notebook → upload `live-laya-colab-test-v6-brutal.ipynb`. Do NOT create a new notebook or edit its code.
2. Runtime > Run all. Cells 1–4 run first (environment, install, API inspect, model load ~30–40 s).
3. Cell 5 file picker → upload `laya-crpc-bns-section-decision-tree-v3.json`. It must print the (34, 48, 79) assert PASS and SHA `67bf2b04…`. If it does not, STOP and report.
4. Cell 5b file picker → upload `brutal-bank-v1-frozen.json`. It must verify SHA `934a2b22…` and 230 questions. If it does not, STOP and report.
5. Cells 6–8 run the 16-question regression (Cell 8 must print the regression score; expected 16/16 under the re-base — if it is not 16/16, record it and continue; do not edit anything).
6. Batch cells B1–B10 run in order. EACH batch cell saves + downloads its per-batch JSON immediately (`live-laya-colab-results-v6-brutal-B<n>.json`). Download each file as it lands — a crash loses at most one batch. Do NOT tune, edit, or re-run anything between batches.
7. Sealed cells (19–21): the sealed upload picker appears at Cell 19 → upload `sealed-fresh-20.json` and `sealed-kannada-8.json` (verify SHAs against §1). Cells 20–21 run and score them.
8. Final cell (22): cumulative scoring + pass/fail. Download `live-laya-colab-results-v6-brutal-final.json` and the regression JSON (`live-laya-colab-results-v6-brutal-regression.json`).
9. Report every batch as it lands + the final numbers (see §5).

**Expected first checkpoint — Batch 1 (B-001..B-025):** 25 questions, per-batch JSON downloaded, printed batch summary showing exact/25, micro precision/recall/F1, TP/FP/FN, court correct/25, escalates correct/25 (boolean + kinds), forbidden 0, silent 0, model errors 0, per-category exact for the categories present in B1, plus the cumulative summary (same 25). If B1 downloads and prints, the run is alive.

## 5. What the live run delivers (per batch and at the end)

Per batch (B1–B10, each downloaded immediately): exact / batch size, micro precision / recall / F1, TP/FP/FN, court correct, escalates correct (boolean AND typed kinds), per-category exact, forbidden count, silent count, model errors, mean latency for the batch, cumulative totals so far.
At the end (final cell + final JSON): exact /230, micro precision/recall/F1, TP/FP/FN, court correct /230, escalates correct /230 (boolean + kinds), per-category exact for all 14 categories, forbidden / silent / model-error totals, mean + max per-question latency with the G14 verdict, 16-question regression (must be 16/16), sealed fresh-20 score (measured number only until the G2 amendment is signed), sealed Kannada-8 score, prose Fp NOT MEASURED, and the honest overall rating — the accuracy number for integration (brutal rating, capped at 9.0 while Fp is unmeasured; gate-formula rating on the 16 with full arithmetic printed).

**Pass bar (brutal plan §3.2):** ≥200/230 exact, micro-F1 ≥0.95, court and escalates ≥200, zero silent / forbidden / model errors, no category below 75%.

## 6. Honest limitations — read before the run (nothing hidden)

1. **B-018 (`hma-9`) and B-019 (`pwdva-22`) are guaranteed misses.** Graph v3 adds only stage-2 leaf nodes; no Stage 1 issue maps to them and `stage2()` has no route emitting them. Emitting them needs a new issue prompt + stage2 route — a pipeline change beyond this round's no-logic-change constraint. The brutal run's ceiling is therefore 228/230 on sections, not 230/230.
2. **Underivable escalation kinds (known scoring gaps):** `fact` — 44 uses in the bank; 7 fact-only questions (B-111, B-112, B-114, B-120, B-122, B-126, B-228 — all hma-27 C6 questions) are guaranteed boolean + kinds misses. `procedure` non-birth branches — 30 uses. `court` forum-ask — 6. `demand` — B-010/B-135. Safety — B-108. These are recorded, not silently mapped to True.
3. **Prose NOT MEASURED.** Cell 9 renderer skipped per the 10:51 IST scope cut. Fp is NOT MEASURED; brutal rating is capped at 9.0. Design exists (v6-deep-dive-report.md §5, prose-renderer-design.md, v6-lane4-prose-latency.md §2 corrected templates, §4: 4 bugs + 1 gap) but was not buildable cleanly in this round: Lane 4's fixes need new Cell 6 facts, the stridhan-sold wording needs legal sign-off, user-facing escalation lines for the four new kinds + safety are undefined, and B1 facts for prose would need the same text derivation.
4. **G14 latency: expect FAIL on CPU** (v5 mean 61.93 s vs ≤15 s budget). T4 is unverified — no T4 numbers claimed.
5. **Sealed maintenance-only court scores will show systematic misses** — sealed GT expects Family Court; the pipeline follows the 16-set Magistrate convention. Recorded, not "fixed".
6. **Kannada C13 native-speaker confirmation still open** — second rater verified at working-reading level only. Recorded, not blocking (per the scope cut).
7. **Sequential (not stratified) batches** — flagged as a deviation from the plan's batching note.
8. **Pre-existing graph defects (v2, untouched):** 3 edges pointing at non-nodes (`escalate_clarify`, `bns-316`, `escalate_demand_first`) and a wrong id (`hmga-6` in bnss-144's related_sections; real id `hmga-1956-s6`). Cell 5 asserts counts only, so they cannot block the run. Coordinator decision: left unfixed, recorded here.
9. **`run_one_question` refactor is untested live** — equivalence verified only by the builder's dedent check + stub-agent tests. The live run is the first real test; the B1 checkpoint is the early warning.
10. **Residence split-GT structural gap** (from the build note) and **Kannada fact-derivation limitation** (facts for Kannada questions are derived from English-language patterns) are recorded in the build note.
11. **Confirmation re-run: PLANNED, not run** — second independent live Colab run, zero code changes, frozen hashes. It happens only after this full brutal run completes.

## 7. Gate coverage table — every row in gate §1 (G1–G16)

Evidence files are under `files/laya-graph/` unless stated. "Not run" means this backtest run will produce it (brutal) or it is a later step (confirmation).

| # | Gate row | Target | This backtest: status + evidence |
|---|---|---|---|
| G1 | Exact, current 16 (v2 GT, 53 sections) | 16/16 | SCORED in-run — Cell 8 regression; re-base predicts 16/16 with D2 (offline estimate, NOT a live result) |
| G2 | Exact, fresh held-out set (§4) | 16/16 per gate; **20/20 after amendment** | SCORED in-run as measured number only — Cell 20 fresh-20. Gate pass needs the G2 amendment signed first (see §8). Until signed: NOT A GATE PASS |
| G3 | Exact, Kannada 8 | 8/8 | SCORED in-run — Cell 21 Kannada-8 |
| G4 | Mean precision, current 16 | ≥0.95 | SCORED in-run — Cell 8 regression |
| G5 | Mean recall, current 16 | ≥0.95 | SCORED in-run — Cell 8 regression |
| G6 | Micro P/R, current 16 | ≥0.95 / ≥0.95 | SCORED in-run — Cell 8 regression |
| G7 | TP/FP/FN, current 16 (53 GT sections) | 53/0/0 | SCORED in-run — Cell 8 regression |
| G8 | Court correct, current 16 | 16/16 | SCORED in-run — Cell 8 regression |
| G9 | Escalates correctly, current 16 | 16/16 | SCORED in-run, BOTH boolean + typed kinds — Cell 8. Known: v5 live was 12/16; typed kinds (D5/D9) are a follow-up build, so 16/16 is NOT expected in this run |
| G10 | Silent questions (non-empty GT, empty prediction) | 0 | SCORED in-run — all sets (brutal batches, regression, sealed) |
| G11 | Forbidden before Stage-2 recheck (all sets) | 0 | SCORED in-run — all sets; HMA-27 forbidden rule added in Cell 8 (D2-consequent) |
| G12 | Prose forbidden mappings (§5) | 0 | NOT MEASURED — renderer does not exist; Cell 9 skipped per 10:51 IST scope cut. Caps the rating at 9.0 |
| G13 | Model errors (all sets) | 0 | SCORED in-run — all sets |
| G14 | Latency: mean ≤15 s, max ≤30 s, 16-run ≤240 s excl. load, load ≤60 s | within budget | SCORED in-run — per-question latency recorded, G14 check printed in Cell 8 + final cell. EXPECTED FAIL on CPU (v5 mean 61.93 s) |
| G15 | Confirmation re-run: full gate passed a second time, zero code changes | passed twice | PLANNED, NOT RUN — separate step after this brutal run |
| G16 | Run log complete: every run numbered, dated, code version recorded, results JSON+MD filed | complete | PARTIAL — this report + build note + hashes file the build; the live run's logs are produced by the notebook cells (per-batch + final JSONs) and must be filed after the run |

**Brutal-230 rows (plan §3.2, beyond the gate):** exact ≥200/230, micro-F1 ≥0.95, court + escalates ≥200, zero silent/forbidden/model errors, no category <75% — all SCORED in-run, batches B1–B10 + final cell.

## 8. G2 amendment text (PREPARED, NOT applied — needs parent sign-off)

Gate file NOT rewritten. For the parent to sign:

> Amendment 2026-11-27 — G2 fresh held-out set amended 16 → 20 questions. The fresh-20 sealed set (`sealed-fresh-20.json`, frozen 2026-11-27) replaces the 16-question composition in gate §4. Until this amendment is signed, the fresh-20 score is a measured number only, NOT a gate pass.

Composition table (verbatim from `sealed/sealed-sets-freeze-note.md`): Total 20; Maintenance (F1–F4) 4; Custody (F5–F7) 3; Stridhan (F8–F10) 3; Residence (F11–F12) 2; Violence/protection (F13–F14) 2; Divorce (F15–F16) 2; Birth certificate (F17–F18) 2; Out-of-scope/escalate (F19–F20) 2; Single-issue ≥8 → 13 tagged; Multi-issue (≥3 issues) ≥5 → 5 (F10, F14, F15, F16, F18), of which five-issue 1 (F15); Missing facts ≥5 → 5; No case filed anywhere 5; Case pending 2; Decree already passed (HMA 25 keep-branch) 1 (F4); Divorce NOT asked ≥3 incl. 1 confused/undecided → 4; Negation ≥2 → 3; Judicial separation vs divorce 1 (F18). Two gate elements are NOT verifiably present in the 20 (salary-slips-missing, no-proceeding interim money) — recorded as accepted composition deviations (v6 §7.2). Never trim 20→16.

## 9. Files inventory (this round)

- `live-laya-colab-test-v6-brutal.ipynb` + `build_laya_v6_brutal.py` + `v6-laneB-build-note.md` (Lane B)
- `laya-crpc-bns-section-decision-tree-v3.json` + `graph-v3-change-log.md` (Lane A; graph file lives in `files/`)
- This report: `brutal-v6-build-report.md`
- Inputs untouched: frozen bank, both sealed sets, graph v2, v2 GT, D2 patch (SHAs in §1)
