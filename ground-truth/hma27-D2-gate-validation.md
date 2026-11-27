# HMA 27 D2 gate — validation log

**Date:** 2026-11-27 (IST). **Lane:** D2 (gate), paired with D1 Option A (user decision
2026-11-27 ~09:46 IST). **Mode:** offline only — no Colab, no live model runs.
**Patch file only:** no live graph or notebook file was modified in place.

- Patch: `hma27-D2-gate.patch` (363 lines, unified diff, paths relative to
  `~/workspace/goals/english-family-law-chatbot-retest/files/`)
- Patch SHA-256: `6349c922944275d26bdc38f6c725daee12ddcd25f86f39ae1485f104e507fc04`
- Patched graph SHA-256: `d8d75663589673e359f8d24da914db42604c5b2dfe48535a55bcaac7a42a6352`
- Patched notebook SHA-256: `842609aedc3e7fe5abfd684ad51ddda11c54cdafc07b1e695f744f3967d943c0`
- Live (unpatched) SHAs, verified unchanged after all work:
  - graph `c7e095ad185242e9360d8b9f180fefff894f5677b52d188174413a32a2704255`
  - notebook `3121f742f24ac59d73924328a7c4ff685261351b65cab1eddf3e01df328979d7`

## 1. Sources

- `v6-deep-dive-report.md` §4 (D2: adopt §1.4 wording, R-HMA27-04 → drop, delete the
  "alternatively…" limb, amend co-fire rule + BNS 316 exclusion, gate in notebook —
  same logged change as D1)
- `v6-lane3-legal-decisions.md` §1.4 (corrected HMA 27 rule wording — quoted exactly
  below in change 2)

## 2. Exact change list

### File 1 — `laya-crpc-bns-section-decision-tree-v2.json` (graph)

| # | Location | Old | New |
|---|---|---|---|
| G1 | stage2 rechecks, `R-HMA27-04` (was line 4227) | `if_fail: "escalate"`, `drop_reason: null`, condition "A matrimonial proceeding under the HMA is pending or being filed (s.27 operates within / in connection with such proceedings)." | `if_fail: "drop"`; `drop_reason: "No HMA proceeding pending or being filed — HMA s.27 cannot be invoked standalone; route Stridhan return to the Family Court under Family Courts Act s.7(1) Expl. (c) / CPC s.151, and keep BNS s.316 as the criminal route."` (verbatim lane 3 §1.4); condition replaced with the §1.4 operative wording incl. the "being filed" definition. `fact_needed` unchanged ("whether a matrimonial proceeding is already pending or must be freshly filed") — the ask that precedes the drop decision. |
| G2 | `sections[id=hma-27].prerequisites[3]` (was line 5919) | "A matrimonial proceeding under the HMA is pending or being filed (s.27 operates within / in connection with such proceedings); alternatively the claim is pressed as part of the family-court case for maintenance/custody/residence" | Corrected §1.4 wording, quoted exactly: "HMA 27 fires only when a matrimonial proceeding under the HMA (ss. 9–13/13B) is pending, or is being filed together with the property claim, and the s.27 application is made before that proceeding is decided. A freestanding s.27 application with no HMA proceeding is not maintainable. A Family Court case under another Act (BNSS s.144, PWDVA, GWA 1890) is not an HMA proceeding for this purpose. 'Being filed' means the user states they are filing, will file, or have instructed the filing of an HMA petition; wanting a divorce or wanting the property back, without more, does not count." The "alternatively…" limb is deleted, not kept. |
| G3 | stage2 `set_co_fire_rules`, `stridhan-set` rule (was line 3805) | "Stridhan rechecks HMA 27 + BNS 316 TOGETHER: civil/family-court return (HMA 27) and criminal breach of trust (BNS 316) must be cited together for the same facts, never one without the other and never replaced by Rajnesh v. Neha. …" | "Stridhan rechecks the civil return route + BNS 316 TOGETHER: BNS 316 (criminal) and the civil return route must be cited together — HMA 27 where an HMA proceeding is pending/being filed, otherwise the Family Court property suit under Family Courts Act s.7(1) Expl. (c) / CPC s.151; never cite BNS 316 as the civil recovery route by itself, and never cite HMA 27 without a proceeding. …" (demand-first fallback sentence unchanged). |
| G4 | `R-HMA27-06` condition | "Co-fire BNS 316: the criminal route for the same withheld Stridhan must be cited TOGETHER with HMA 27, never one without the other." | "Co-fire BNS 316: the criminal route for the same withheld Stridhan must be cited TOGETHER with the civil return route — HMA 27 where an HMA proceeding is pending/being filed, otherwise the Family Court property suit under Family Courts Act s.7(1) Expl. (c) / CPC s.151; never cite BNS 316 as the civil recovery route by itself, and never cite HMA 27 without a proceeding." |
| G5 | hma-27 recheck `co_fire_rules[0]` | "stridhan-set: HMA 27 (civil return) + BNS 316 (criminal) cited together; …" | "stridhan-set: the civil return route (HMA 27 where an HMA proceeding is pending/being filed, otherwise the Family Court property suit under Family Courts Act s.7(1) Expl. (c) / CPC s.151) + BNS 316 (criminal) cited together; …" |
| G6 | hma-27 `related_sections` → BNS s.316 | "… s.27 (civil/family-court return) and s.316 (criminal complaint/FIR) must be cited TOGETHER, never one without the other, and never replaced by Rajnesh v. Neha" | "… the civil return route (HMA 27 where an HMA proceeding is pending/being filed, otherwise the Family Court property suit under Family Courts Act s.7(1) Expl. (c) / CPC s.151) and s.316 (criminal complaint/FIR) must be cited TOGETHER, never one without the other, and never replaced by Rajnesh v. Neha" |
| G7 | hma-27 `exclusions` | "NOT a standalone criminal remedy — the criminal route for withheld Stridhan is BNS s.316, cited alongside s.27, not instead of it" | "… cited alongside the civil return route (HMA 27 where an HMA proceeding is pending/being filed, otherwise the Family Court property suit under Family Courts Act s.7(1) Expl. (c) / CPC s.151), not instead of it" |
| G8 | `R-BNS316-05` condition | "… NOT civil recovery by itself (that is HMA 27), NOT maintenance, custody or residence." | "… NOT civil recovery by itself (that is the civil return route — HMA 27 where an HMA proceeding is pending/being filed, otherwise the Family Court property suit under Family Courts Act s.7(1) Expl. (c) / CPC s.151), NOT maintenance, custody or residence." |
| G9 | `R-BNS316-06` condition + `fact_needed` | "Co-fire HMA 27: the civil/family-court return claim must be cited TOGETHER with BNS 316 for the same facts, never one without the other. A criminal conviction does not by itself order return — the s.27 claim does. …"; `fact_needed: "HMA 27 recheck outcome"` | "Co-fire the civil return route: the civil/family-court return claim must be cited TOGETHER with BNS 316 for the same facts, never one without the other — HMA 27 where an HMA proceeding is pending/being filed, otherwise the Family Court property suit under Family Courts Act s.7(1) Expl. (c) / CPC s.151. A criminal conviction does not by itself order return — the civil return claim does. …"; `fact_needed: "civil return route recheck outcome (HMA 27 / FCA s.7(1) Expl. (c))"` |
| G10 | `R-BNS316-08` condition | "… The civil return claim runs in parallel in the Family Court under HMA 27. …" | "… under the civil return route (HMA 27 where an HMA proceeding is pending/being filed, otherwise the Family Court property suit under Family Courts Act s.7(1) Expl. (c) / CPC s.151). …" |
| G11 | bns-316 recheck `co_fire_rules[0]` | "stridhan-set: BNS 316 (criminal) + HMA 27 (civil) cited together; … while the complaint and s.27 claim are pending." | "stridhan-set: BNS 316 (criminal) + the civil return route (HMA 27 where an HMA proceeding is pending/being filed, otherwise the Family Court property suit under Family Courts Act s.7(1) Expl. (c) / CPC s.151) cited together; … while the complaint and the civil return claim are pending." |
| G12 | bns-316 `exclusions[0]` — the BNS 316 exclusion named in §1.4 | "NOT a civil recovery remedy by itself — the civil/family-court return route is HMA s.27; s.316 is the criminal route and the two must be cited TOGETHER" | "NOT a civil recovery remedy by itself — the civil/family-court return route is HMA 27 where an HMA proceeding is pending/being filed, otherwise the Family Court property suit under Family Courts Act s.7(1) Expl. (c) / CPC s.151; s.316 is the criminal route and the two must be cited TOGETHER" |
| G13 | bns-316 `exclusions` ("NOT a substitute…") | "NOT a substitute for the s.27 return order — a criminal conviction does not by itself order return; the family-court s.27 claim does" | "NOT a substitute for the civil return order — a criminal conviction does not by itself order return; the family-court civil return claim does" |
| G14 | bns-316 `not_for[0]` | "civil return of property (that is HMA s.27)" | "civil return of property (that is the civil return route — HMA 27 where an HMA proceeding is pending/being filed, otherwise the Family Court property suit under Family Courts Act s.7(1) Expl. (c) / CPC s.151)" |
| G15 | bns-316 `related_sections` → HMA s.27, and → PWDVA s.18 | "… s.316 (criminal) and s.27 (civil) must be cited TOGETHER for the same facts. …"; "… while the criminal complaint and s.27 claim are pending" | "… s.316 (criminal) and the civil return route (HMA 27 where an HMA proceeding is pending/being filed, otherwise the Family Court property suit under Family Courts Act s.7(1) Expl. (c) / CPC s.151) must be cited TOGETHER for the same facts. …"; "… while the criminal complaint and the civil return claim are pending" |
| G16 | bns-316 `court` | "… The civil return claim runs in parallel in the Family Court under HMA s.27. …" | "… under the civil return route (HMA 27 where an HMA proceeding is pending/being filed, otherwise the Family Court property suit under Family Courts Act s.7(1) Expl. (c) / CPC s.151). …" |
| G17 | bns-316 `relief` | "… the actual return order comes from the parallel HMA s.27 family-court claim. …" | "… the actual return order comes from the parallel civil return claim in the Family Court (HMA 27 where an HMA proceeding is pending/being filed, otherwise the Family Court property suit under Family Courts Act s.7(1) Expl. (c) / CPC s.151). …" |

No list lengths changed anywhere in the graph. BNS 316 is untouched as a route
(still a section, still co-fired, still kept by the notebook gate — see N3).

### File 2 — `laya-graph/live-laya-colab-test-v5-precision.ipynb` (notebook)

| # | Location | Old | New |
|---|---|---|---|
| N1 | Cell 6 header comment | Ends "# Ground truth is otherwise byte-identical to v3." | Adds a v6 D2 note documenting the new `being_filed` fact (definition, "I want a divorce" ≠ being filed, values False for all 16). |
| N2 | Cell 6, all 16 `facts` dicts (K0, H1–H15) | No `being_filed` key | `"being_filed": False` added after each `"proceeding_pending"` line (16 insertions, asserted in the builder). H14 (proceeding pending) also gets `being_filed: False` — it states a case "already going on", not a fresh filing. |
| N3 | Cell 7 header | Notes 1–8 only | Adds note 9 documenting the D2 HMA 27 gate (definition, HMA 25 Layer B shape, `gated_out` with distinct reason, BNS 316 stays). |
| N4 | Cell 7 `stage2()`, after the HMA 25 Layer B block, before the "old … recheck block is DELETED" comment | No HMA 27 gate — `hma-27` added unconditionally with `bns-316` when stridhan fires | D2 gate: if `'hma-27' in kept` and neither `facts.get('proceeding_pending')` nor `facts.get('being_filed', False)`, remove `hma-27` from `kept` and append to `gated_out`: `"hma-27: gated (D2) — no HMA proceeding pending or being filed; HMA s.27 cannot be invoked standalone; civil return route is the Family Court property suit under FCA s.7(1) Expl. (c) / CPC s.151; BNS s.316 kept as the criminal route"`. Never added to `dropped[]` (gated-before-generation, like HMA 25 Layer B). `hma-27` stays in `candidates_before_gate` (computed before this block). BNS 316 is NOT gated. |
| N5 | Cell 7, after the HMA 25 shadow test | One shadow test (HMA 25) | Adds an offline HMA 27 shadow test (no model calls): no-proceeding → `hma-27` gated out, `bns-316` kept, `hma-27` gated_out entry present, `hma-27` in `candidates_before_gate`; `proceeding_pending=True` → kept; `being_filed=True` → kept. |

`stage2()`'s return shape is unchanged (`kept, dropped, esc_typed, gated_out,
candidates_before_gate`); the main loop already merges `gated_out_b` into
`rec['gated_out']`, so the D2 drop is recorded per question with its own distinct
reason, different from the HMA 25 Layer B reason (verified in §3).

## 3. Validation commands + results

All validation ran on copies in `/tmp/d2val` (and `/tmp/d2val2` for the
colab_bundle copy). The live files were never written; their SHAs above match the
pre-work values.

1. **Patch build** — `python3 /tmp/d2work/build_patch_inputs.py`
   (JSON edits with per-edit assertions: every old string found exactly once, 16
   `being_filed` insertions, no `alternatively` left, counts 32/46/77).
   Result: `graph written` / `notebook written`. The builder's own `json.dumps(…,
   indent=1, ensure_ascii=False)` round-trips both originals byte-identically, so
   the diff contains only the intended lines (graph diff 160 lines, notebook diff
   203 lines).
2. **Patch creation** — `diff -u --label a/… --label b/…` for both files into
   `hma27-D2-gate.patch`. Result: 363 lines, two file headers.
3. **Patch applies cleanly** — fresh copies in `/tmp/d2val`, `patch -p1 --dry-run`
   then `patch -p1`. Result: both files patched with no rejects/fuzz reported;
   patched copies byte-identical (`cmp`) to the builder output.
4. **Graph JSON parses; counts unchanged** — `json.load` on the patched graph.
   Result: sections/nodes/edges = 32/46/77 (same as Cell 5's assert and the
   `counts` object); `stage2.total_checks` still 121; `R-HMA27-04 if_fail: drop`
   with the §1.4 `drop_reason`; `hma-27` prerequisites still 4 items;
   `'alternatively'` occurrences: 0; BNS 316 still a section.
5. **colab_bundle copy** — the identical graph copy at
   `laya-graph/colab_bundle/laya-crpc-bns-section-decision-tree-v2.json` (SHA
   matches the canonical file) also accepts the patch (`patch -p1 --dry-run` OK).
   The patch must be applied to that copy too when the notebook is next bundled,
   or the bundle will carry the old graph.
6. **Notebook nbformat validation** — `nbformat.read` + `nbformat.validate`.
   Result: PASS, nbformat 4, 9 cells.
7. **Every cell compiles** — `compile()` on each code cell's source (Cell 2's one
   `!pip install …` line stripped for the syntax check only — it is valid Colab
   IPython syntax, not Python). Result: cells 1–8 all compile OK (Cell 7: 743
   lines, Cell 6: 548 lines, Cell 8: 312 lines).
8. **Cell 6 executes** — `exec` of the patched Cell 6 source. Result: TEST_SET =
   16 questions; `being_filed` present on all 16, all `False`; `proceeding_pending`
   True only on H14.
9. **Cell 7 pre-loop executes; both shadow tests PASS** — `exec` of Cell 7 up to
   `RESULTS = []` with a stub `agent` (the live loop needs the model, so it was
   not executed — offline lane). Result: `HMA25 gate shadow test: PASS` and
   `HMA27 gate shadow test: PASS` printed; no assertion raised.
10. **D2 gate behaviour on the real 16 facts** — `stage2({'stridhan'}, {}, facts)`
    per question. Result:
    - K0, H3, H10, H15 (pending=False, being_filed=False): `hma-27` NOT kept,
      `bns-316` kept, `hma-27` gated_out entry present, `hma-27` in
      `candidates_before_gate`.
    - H14 (pending=True): `hma-27` kept, `bns-316` kept, no gated_out entry.
    - `hma-27` gated_out reason differs from the `hma-25` Layer B reason
      (distinct reason per veto — verified by direct comparison).

## 4. Deviations from the lane-3 spec / task brief (blunt)

1. **The graph path in the task does not exist.** The brief named
   `files/laya-graph/laya-crpc-bns-section-decision-tree-v2.json`; that file is
   not there. The canonical graph is `files/laya-crpc-bns-section-decision-tree-v2.json`
   (SHA `c7e095ad…`), with a byte-identical copy in `laya-graph/colab_bundle/`.
   The patch is written with paths relative to `files/` so it applies to the
   canonical file, and it was verified to dry-run-apply to the colab_bundle copy
   as well. The notebook path in the brief was correct.
2. **No "being-filed" fact existed in Cell 6.** The brief said the gate should be
   "wired to the proceeding_pending / being-filed facts already in Cell 6" — only
   `proceeding_pending` was there. I added `being_filed` as a new frozen
   annotation (N2, all False — no question states filing/will file; H5 "I want a
   divorce" does not count, per lane 3 §1.2.3). The gate reads it via
   `facts.get('being_filed', False)` so pre-existing fact dicts without the key
   (e.g. the HMA 25 shadow-test facts) do not raise `KeyError`.
3. **"Ask once, then drop" (lane 3 §1.4) is only half-implementable in the notebook.**
   The notebook has no interactive ask; the fact is a frozen Cell 6 annotation, so
   the gate drops on the annotated fact and records the drop in `gated_out` with
   the §1.4 drop_reason text (which names the FCA route). The ask itself is
   preserved as R-HMA27-04's unchanged `fact_needed` in the graph. A live
   ask-then-drop flow would be new work, not part of D2.
4. **Co-fire amendment applied everywhere the rule is stated, not just the two
   sentences §1.4 names.** G3–G17 cover every sentence that asserts HMA 27 is
   *the* civil route unconditionally (stridhan-set rule, both co-fire checks, both
   `co_fire_rules` lists, both `related_sections`, hma-27 exclusions, BNS 316
   exclusion/not_for/court/relief, R-BNS316-05/08). Leaving any of them would
   leave a sentence contradicting the corrected GT. Shorthand cross-references
   "Stridhan is HMA s.27 / BNS s.316" in other sections' exclusions (HMA 25,
   PWDVA 20, etc.) were intentionally left untouched — they are labels, not the
   co-fire rule.
5. **GT is NOT changed by this patch.** Cell 6 `gt_ids` still contain `hma-27` on
   K0/H3/H10/H15 — D1 is the independent rater's change. Consequence, stated
   plainly: applying D2 alone under the old GT makes those four questions
   non-exact by HMA 27 false-negative until D1 lands (lane 3 §1.3/§5.5). This
   patch must be applied in the same logged change as D1, never alone.
6. **Not changed (out of scope, flagged for the coordinator):** the graph's
   `open_questions_from_lanes` still lists "HMA s.27 needs a proceeding" as
   unconfirmed; Cell 7's `court_for` still adds Family Court when `hma-27` is in
   `kept` (correct after the gate, since `hma-27` is only kept when a proceeding
   exists — no change needed).

## 5. Notes / loose ends

- The patch file's SHA-256 is recorded in the header (§1); verify the patch by
  that hash and by re-running `patch -p1 --dry-run` on fresh copies.
- Builder script kept at `/tmp/d2work/build_patch_inputs.py` (ephemeral; regenerate
  from this log if the patch ever needs rebuilding — the change list in §2 is the
  authoritative record).
- No live run was performed and none is claimed: the gate's effect on the live
  16/16 prediction can only be measured by the next Colab run under the corrected
  GT (D1 + D2 together).
