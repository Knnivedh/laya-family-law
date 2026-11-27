# Lane 08 — Stage 1 Routes Audit — STATUS

- Lane: 08 (Stage 1 routes audit)
- Date: 2026-11-27
- Working copy: `~/workspace/laya-v71-work` (HEAD `1cb0bff` at start)
- Status: **DONE (code + local verification, evidence mode, CPU VM)** — neural
  prompts uncalibrated, sealed re-run still needs RTX (see §5).
- Full audit: `docs/recall_stage1_routes_audit.md`

## 1. Sections with no route

- **Before fixes: 2 statutory sections with no route at all** (no Stage 2
  disposition in the v7 path): `bnss-144-3`, `bnss-146`. The v6 example
  (`hma-9`, `pwdva-22`) turned out to already have full evidence → Stage 2
  routes; what they lacked was any *neural* route.
- **After fixes: 0 statutory sections without a route.** Both sub-routes are
  now `conditional` candidates (see §3).
- **16 proc/doc sections** (`proc-*` / `doc-*`) have no kept-emission route
  **by design** (procedure/document metadata; verified zero references in
  `src/` or `tests/` outside the graph JSON). Recorded as a design decision
  in the audit (§4), not a fix.

## 2. Routes with no test

- **4 sections with no `tests/test_v7_rules.py` case:** `hma-26`,
  `births-deaths-act-1969`, `bnss-144-3`, `bnss-146`.
- Of those, 2 are covered elsewhere (`hma-26` via 16-Q H14 + prose;
  `births-deaths-act-1969` via 16-Q H7 + prose), so **2 are truly untested
  in the v7 path:** `bnss-144-3`, `bnss-146` (only the separate
  `laya_family` runtime tests them).
- **3 new routes added by this lane have no committed test yet:**
  `restit_p` prompt, `dvcomp_p` prompt, post-order split facts — verified by
  ad-hoc probes only (test files are not this lane's owned files).

## 3. Fixes applied

1. **Extractor (`src/laya_v7_extractor.py`) — neural routes for hma-9 /
   pwdva-22:** `LAYA_NOUL_PROMPTS` 9 → 11 (`restit_p`, `dvcomp_p`), wired in
   `_merge_laya_and_grounded` with `_boost` (thresholds 0.55 / 0.45,
   UNCALIBRATED — no ROC data on this VM).
2. **Extractor — post-order split facts:** `_post_order_split_facts()`
   emits `arrears_recovery_asked` / `maintenance_variation_asked`
   (extractor-side, all modes; `source="extractor"`). Phrasings from the
   Kaanoon reference read (§6 of audit): "court ordered maintenance but he
   is not paying" (144-3); "amount is not enough, prices gone up, increase
   it" (146).
3. **Graph (`src/laya_v7_graph.py`) — bnss-144-3 / bnss-146 as conditional
   dispositions** (§1b block), `MAGISTRATE_SECTIONS` + forum authority for
   both, and a `maintenance:post-order-enforcement` branch in
   `layer_a_filter_options`. Deliberately conditional, NOT eligible: EN prose
   (`KNOWN_SECTIONS`) has no template for either section and would return an
   error handoff on them as kept ids; plus no BNSS-order statute fact exists
   yet (pre-1 Jul 2024 CrPC s.125 guard). Both blockers are recorded in the
   audit (§5) for the prose lane / Lane 03.
4. **Not touched:** `src/laya_v7_evidence.py` (R3 — Lane 03 owns it) and all
   other lanes' files. Gaps found in evidence anchors (dead `injur`
   alternative in `_DV_COMP_RE`; `_RESTITUTION_RE` missing "come back and
   live" + custody over-fire; `_ENHANCE_COST_RE` blocking bnss-146) are
   recorded in the audit §5 for Lane 03, with exact mechanisms and probes.

## 4. 16-Q before / after (evidence mode, CPU)

- Before: `python3 -m tests.v7_backtest --suite 16q --mode evidence --device cpu`
  → **14/16, rating 7.6**, misses H6 (pwdva-18), H14 (hma-13), 0 FP.
- After: **14/16, rating 7.6, same two misses, 0 FP, 0 errors.** No regression.
- Guardrails after: `tests/test_graph_v4.py` PASS (34/66/99, 7/7 SHAs);
  `tests/test_prose_renderer_v2.py` PASS (246, Fp=0);
  `tests/test_v7_rules.py` 10/10 OK; `tests/test_laya_family.py` OK.
- Ad-hoc probes (§3.3 of audit): arrears → `bnss-144-3` in candidates,
  kept unchanged; variation ×3 → `bnss-146` in candidates, kept unchanged;
  fresh maintenance/divorce → no false fire; Layer A post-order branch
  drops exactly the non-asked sub-route option in each case.

## 5. What is still unverified

- Neural prompts uncalibrated; needs RTX ROC + validation-split run.
- Split facts verified by ad-hoc probes only; no committed test (follow-up
  for test owners: add `test_v7_rules.py` arrears/variation cases).
- Eligible promotion of bnss-144-3 / bnss-146 blocked on EN prose templates
  + BNSS-order statute fact.
- Sealed Fresh-20 / Kannada-8 untouched; no claim about movement — sealed
  re-run is RTX-only (Lane 07 / coordinator).
- Lane 11's `docs/kaanoon_phrasing_patterns.md` had **not landed** when this
  audit was written (checked twice; file absent). This lane used its own
  small Kaanoon reference read (2 searches + 1 page fetch, patterns only,
  no Q&A content copied, no answers cited as authority). The held-out eval
  set `data/kaanoon_eval/heldout.jsonl` was never opened or used (R6).
