# v5 Lane D build note — PRECISION skeleton (Phase 1)

**Status:** skeleton built and validated 2026-11-27 ~05:00 IST. No live Colab run.
Awaiting the merged Lane A+B+C fix spec for Phase 2.

## Files
- Skeleton notebook: `live-laya-colab-test-v5-precision.ipynb`
- Builder (deterministic, re-runnable): `build_laya_v5_precision.py`
- Base: `live-laya-colab-test-v4r-residence-only.ipynb` (untouched)

## sha256
- v5 skeleton: `a5fb02e70b00d3b8e9dbbd3119c3aec3aeac4885c02add715fb72e5ec9797a22`
- Builder re-run to a second path (`/tmp/v5-rerun.ipynb`) is byte-identical
  (same sha256, `cmp` clean). Rebuild with:
  `python3 build_laya_v5_precision.py`

## What Phase 1 changed (only this)
Version strings / output filenames, v4r → v5. Nothing else. Verified by an
independent cell-by-cell diff against the v4r base:
- Cells 0–6: IDENTICAL (Cell 6 diff is empty — GT, facts, court_expected,
  escalate_expected untouched).
- Cell 7: 1 line changed — the header line only.
- Cell 8: 10 lines changed — header, `notebook_version` string, results
  banner, `live-laya-colab-results-v5-precision.json/.md` filenames (open /
  print / download), markdown title, final download print.
- No `v4r-residence-only` / `v4r residence-only` string remains in Cells 7–8.
  (Historical `v4`/`v3`/`v1` references in comments are intentionally kept —
  they document earlier versions, not this one.)

## Validation (all PASS, enforced by the builder)
- nbformat.validate PASS.
- Cells 7–8 compile PASS.
- TEST_SET ids K0+H1–H15 unchanged; GT ids unchanged (re-extracted from
  Cell 6 source and compared to v4r).
- Carried-over invariants spot-checked present: HMA 25 gate shadow-test
  asserts + PASS print (Cell 7), graph assert `(32, 46, 77)` (Cell 5),
  `esc_live = bool(kinds & {'quantum', 'court', 'demand'})` (Cell 8),
  hard rule "NO fallback to keyword" (Cell 7 header).

## v4r baseline this skeleton inherits (live, measured 2026-11-27 ~00:19 IST)
Exact 10/16, mean P/R 0.833/1.000, micro P/R 0.826/1.000, TP/FP/FN 57/12/0,
court 13/16, escalates 14/16. Exact: K0, H2, H4, H5, H8, H9, H10, H11,
H12, H13. Remaining non-exact (precision-only, recall 1.000 everywhere):
H1, H3, H6, H7, H14, H15 — 12 FPs to remove. Source:
`workspace/browser_downloads/sess-2184034649/browser-download-20261126T185447.300061282Z-0-live-laya-colab-results-v4r-residence-only.json`.

## Insertion points for the merged Lane A+B+C fixes (v5 Cell 7, 585 lines)
Line numbers are identical to v4r (Phase 1 changed no line counts).

| Fix area (per v5-planning-note.md) | Location |
|---|---|
| 4-option financial-claim choice (§1, Gemini) — replaces the independent maintenance / Stridhan `noul` prompts | `ISSUES` list, lines 156–164 (maintenance prompt line 157, Stridhan prompt line 159); new choice classifier + cutoff goes in the live loop: full-question pass lines 397–413, clause pass lines 415–439, or as a new block before the final-score pool at line 456 |
| Choice cutoff / firing for maintenance & Stridhan | Final-score max pool + `TRACK`, lines 456–471; firing loop, lines 503–513 (`score, thr = final[name], THRESHOLDS[name]`) |
| Thresholds (only if the merged spec names new values — no global move) | `THRESHOLDS` dict, lines 134–144 |
| AUX_PROMPTS list (add/remove/replace aux phrases, e.g. residence verbatim "stay in the house") | Lines 179–192 (list body 180–191); aux scoring loop lines 441–455 |
| H14 proceeding-aware custody routing (§3) — drop standalone GWA 1890 when `proceeding_pending` is True | `stage2()`, custody block lines 262–267 (`if 'custody' in fired:` … `kept_pre |= {'gwa-1890', ...}`); do NOT touch the no-proceeding route (H2 keeps GWA 1890 + HMGA s.6 + WELFARE) |
| H6 clause-split fix (§4) — v6, NOT v5 unless the merged spec says so | `split_clauses()`, lines 195–223 (`_SPLIT_RE` at lines 206–209) |
| Residence 2-option choice gate (§5) — v5/v6, only if the merged spec includes it | Residence fact gate block, lines 486–502; `RESIDENCE_R0/R1` + `RESIDENCE_PROMPT`, lines 150–152 |
| Guard block (any new fact gate) | Next to the residence gate, lines 486–502; `gated_out_a` is initialised at line 396 and appended to `rec['gated_out']` at line ~562 |
| Stage 2 custody routing (general) | `stage2()`, lines 246–321 |
| Sub-choice loop (if a new choice node is added to the graph) | Lines 518–556; node lookup via `ISSUE_NODE` / `ISSUE_EXTRA_NODE`, lines 165–176 |
| New metric (e.g. FP-by-issue) — Cell 8 only | After the `rows` loop ends (~line 111), before the empty-5 slice at line 119; add to `agg` dict (lines 161–196) and to the markdown output if the spec wants it printed |

## Known defects found in the v4r base while scaffolding — NOT fixed
(Phase 1 changes version strings only. Fix only if the merged spec says so.)
1. **Cell 7 header, lines 7–8, stale thresholds:** "(a) v3 thresholds KEPT
   (M 0.10, C 0.20, R 0.15, divorce-asked 0.40 / divorce-pending 0.13)"
   contradicts the code — `THRESHOLDS` (lines 141–142) is actually
   divorce_asked 0.45 / divorce_pending 0.12. Comment is wrong; code is right.
2. **Cell 8 header, lines 3–6, stale baseline:** "Original metrics are kept
   verbatim so v4 compares directly with the v3 live baseline (exact 5/16,
   …)". In v5 the live baseline is v4r (exact 10/16, micro-F1 0.905). The
   `agg` dict has `v1_baseline_reference` and `v3_baseline_reference` but no
   `v4r_baseline_reference` — add one in Phase 2 if the spec wants the
   comparison updated (suggested value: "v4r live: exact 10/16, mean P/R
   0.833/1.000, micro P/R 0.826/1.000, TP/FP/FN 57/12/0, court 13/16,
   escalates 14/16, residence fired 4/16, gated 12/16.").
3. **Cell 8 H12 check — checked, NOT a defect in this base:** the task brief
   mentioned a hardcoded-literal H12 check known from v3. In the v4r base it
   is measured, not hardcoded: `h12_empty` (Cell 8, lines ~126–129) reads
   live `h12_rec.get('kept_ids') == []`, `court_live == []`, and
   `escalates_live is False` from `rec_by_id` / `rows_by_id`. No fix needed;
   if v3 had the literal, v4 already repaired it.

## Phase 2 instructions (for when the merged spec arrives)
- Fill in `apply_merged_fixes(nb)` in `build_laya_v5_precision.py` from the
  spec only; do not invent fixes.
- Each fix must assert its anchor string / line number before editing; on
  any mismatch the builder must fail loudly — flag back to the coordinator
  instead of improvising.
- Re-run the builder, re-validate (builder enforces: Cells 0–6 identical,
  GT unchanged, nbformat.validate, Cells 7–8 compile), record the new
  sha256 here, and append the final change log below.

## Phase 2 change log
**Applied 2026-11-27 ~05:35 IST from the merged spec
(`v5-precision-report.md`). Builder updated in place
(`build_laya_v5_precision.py` — skeleton renames + `apply_fix1_cell6` +
`apply_merged_fixes`, every edit assert-before-edit). New sha256:
`3121f742f24ac59d73924328a7c4ff685261351b65cab1eddf3e01df328979d7`
(builder re-run byte-identical, `cmp` clean). v4r base untouched
(sha256 still `7d67bd53…82f5`).**

- **Fix 1 — evidence gates.** Cell 6: `money_fact`/`gold_fact` added to all
  16 facts dicts per the spec table (money True on K0, H1, H5, H6, H8, H9,
  H10, H11, H13, H14; gold True on K0, H3, H10, H15 only). Cell 7: veto
  after the residence gate, before firing — missing fact forces the final
  to 0.0 with a distinct `gated_out_a` reason per veto
  (`evidence gate: maintenance gated, money_fact=false` /
  `evidence gate: stridhan gated, gold_fact=false`). Threshold still
  applies on top.
- **Fix 2 — custody gate.** Patterns + `_has_custody_claim` inserted
  verbatim just before the residence-gate block; application immediately
  after the residence gate. Records `custody_claim`, `custody_gated`, and
  pre-gate final `custody_final_pre_gate`. THRESHOLDS['custody'] (0.20),
  AUX_PROMPTS custody entries, main custody prompt, `split_clauses`
  untouched.
- **Fix 3 — single-issue guard.** `GUARD_LIFT_BAR = 0.80`,
  `GUARD_FULL_CEILING = 0.01`, same insertion zone, after Fix 2.
  Dominance from raw full scores (`raw`), divorce on asked only (>= 0.45),
  residence on R0 full; lift = max(`clause_max`, `rec['aux_max']`), divorce
  lift also includes pending clause/full/aux. Records
  `rec['single_issue_guard']` {armed, dominant, dominant_full, blocked}
  and one distinct `gated_out_a` entry per blocked issue. No in_scope
  firing gate, no global aux/clause bar.
- **Fix 4 — H14 exclusive primary route.** `stage2()` custody block
  replaced with the exclusive branch (pending → HMA 26 + HMGA s.6 +
  WELFARE; else → GWA 1890 + HMGA s.6 + WELFARE). Recheck lines kept as
  Layer-B defence-in-depth; no symmetric remove-GWA recheck added.
- **Doc-only fixes (from the Phase 1 known-defects list):** Cell 7 header
  divorce thresholds 0.40/0.13 → 0.45/0.12; Cell 8 header baseline v3 →
  v4r and `v4r_baseline_reference` added to the agg dict.
- **Cell 8 FP-by-issue metric:** `SECTION_ISSUE` map + `fp_by_section` /
  `fp_by_issue` computed after the rows loop (before the empty-5 slice),
  added to `agg` (`fp_total`, `fp_by_section`, `fp_by_issue`), printed in
  the markdown output (section after the Empty-5 table). PWDVA 18 is
  counted as `residence-or-violence` (shared section).
- **Recording:** `rec` init gains `money_fact`, `gold_fact`,
  `custody_claim`, `custody_gated`, `custody_final_pre_gate`,
  `single_issue_guard`. `fired_clause`/`fired_source` untouched by all
  vetoes (still record what WOULD have fired).
- **NOT shipped, per spec:** maintenance bar 0.30, Gemini 4-option choice,
  keyword token guards, H6 split-trigger extension, residence 2-option
  choice gate. No threshold changes (THRESHOLDS asserted unchanged).
  `escalate_expected` untouched — the predicted H7/H15 escalate dip stands
  as an OPEN expectation decision.

### Adaptations / observations (no anchor mismatches — zero)
- **No anchor or line-number mismatches.** All spec anchors matched on
  first attempt (Cell 7 residence gate 486–502, firing loop 503–513,
  stage2 custody 262–265, recheck 298–300, header lines 7–8; Cell 8 rows
  loop ends ~111, empty-5 ~119, agg 161–196).
- **Variable-name mapping (Fix 3):** Lane C pseudocode `raw` /
  `clause_max` / `rec['aux_max']` are the actual Cell 7 names — no
  renaming was needed. Full scores are the `raw` dict (R0 residence =
  `raw['residence']`); divorce asked full = `raw['divorce']`, pending =
  `raw['divorce_pending']`.
- **Guard message format:** the spec's f-string would crash if lift is
  None (no clause/aux evidence at all); the builder formats None as
  0.0000 in the message while recording None in the `blocked` tuple.
  Cannot occur on the 16 (every issue has a clause-max); defence only.
- **Guard × divorce firing (latent interaction, NOT fixed — spec does not
  authorise it):** divorce firing reads `asked_fires`/`pending_fires`,
  computed before the guard, so a guard veto on divorce zeroes the
  recorded final only and cannot change the firing decision. On the 16
  this is inert (H7/H15 divorce asked/pending are both False, and the
  veto is recorded but changes nothing). On the sealed set a
  blocked-divorce `gated_out` entry would not by itself stop a divorce
  fire if asked/pending fired — flagged for v6.
- **Fix 2 definition placement:** patterns + helper sit just before the
  residence-gate block inside the live loop, exactly where the spec put
  them (re-compiled per question; negligible cost on 16 questions).
- **Fix order in the insertion zone:** Fix 1 → Fix 2 → Fix 3, per the
  merged report §2 ("in this order"). The task message's "immediately
  after the residence gate" for Fix 2 is satisfied in the sense that all
  three vetoes sit between the residence gate and the firing loop, and
  the vetoes are independent (each reads scores/clauses/facts, not
  another veto's output) except the guard's dominance, which uses raw
  full scores as required.

### Validation (Phase 2, all PASS)
- Builder-enforced: Cells 0–5 identical to v4r; Cell 6 diff is EXACTLY
  the two added fact fields (independent diff: 16 hunks, each one
  `residence_claim` line → itself + `money_fact` + `gold_fact`, nothing
  else); TEST_SET ids K0+H1–H15; GT ids unchanged; THRESHOLDS unchanged;
  nbformat.validate PASS; Cells 7–8 compile PASS; HMA 25 shadow test /
  graph 32/46/77 / esc_live incl. 'demand' / no-keyword-fallback all
  present; builder re-run byte-identical.
- **Offline replay harness (new file
  `offline_replay_harness_v5.py`):** executes the ACTUAL built Cell 6 +
  Cell 7 + Cell 8 code with a fake `agent` replaying the recorded v4r
  live scores (clause calls replay the recorded clause-max; sub-choice
  calls replay the recorded option via opt-index, with the HMA-25
  Layer-A filter applied). Result: **exact 16/16, TP/FP/FN 57/0/0,
  micro-F1 1.000, court 16/16, escalates 12/16, 0 model errors,
  `fp_by_issue`/`fp_by_section` empty** — exactly the §5 prediction.
  Escalates wrong: H2, H4 (pre-existing, untouched) + H7, H15 (the
  predicted dip). Guard arming/blocking matches the logic sim question
  by question (arms on H1, H3, H7, H8, H9, H11, H14, H15; blocks
  maintenance on H3/H7/H15 with lifts 0.1218/0.1971/0.1269).
  `custody_claim` True exactly on K0/H2/H5/H14 (the GT-custody set);
  pre-gate finals match v4r (H5 0.2189, H6 0.3669, H14 0.7895).
  **Caveat:** the harness replays v4r scores, so it validates the
  notebook code paths, not the live model — the live Colab run must
  still confirm the scores reproduce, especially H5 custody aux 0.2189
  (margin 0.0189 over threshold).
