# Stage 1 Routes Audit — LAYA v7.1 Recall Swarm, Lane 08

- Lane: 08 (Stage 1 routes audit)
- Date: 2026-11-27
- Working copy: `~/workspace/laya-v71-work` (HEAD `1cb0bff`, 10x swarm merged)
- Author: Lane 08 agent. Coordinator owns merge/push.
- Scope: every Stage 1 route/emission against the 34-section Graph v4
  (`graph/laya-crpc-bns-section-decision-tree-v4.json`) + 2-section Graph v4.1
  delta (`graph/laya-crpc-bns-section-decision-tree-v4.1.json`) = **36 sections**.
- Method: static read of `src/laya_v7_evidence.py` (anchors — read-only, Lane 03
  owns), `src/laya_v7_extractor.py` (11 noul prompts after this lane, 18 Qwen
  constrained slots), `src/laya_v7_graph.py` (`evaluate_stage2_v7`,
  `layer_a_filter_options`), `src/laya_prose_v2.py` (`KNOWN_SECTIONS`), plus
  grep coverage counts over `tests/test_v7_rules.py`, `tests/test_prose_renderer_v2.py`,
  `tests/test_graph_v4.py`, `tests/test_laya_family.py`, maintenance fixtures,
  and the 16-Q backtest. No sealed file was opened (guardrail R: only aggregates
  already logged in `results/` were used; the Fresh-20/Kannada-8 numbers below
  are the ones in `docs/recall_swarm_state.md`).
- Baseline (before any change, this lane, CPU evidence mode):
  `python3 -m tests.v7_backtest --suite 16q --mode evidence --device cpu` →
  **14/16, rating 7.6**, top FN `pwdva-18: 1` (H6), `hma-13: 1` (H14), 0 FP,
  0 errors. Guardrails before: `tests/test_graph_v4.py` PASS (34/66/99, 7/7
  frozen SHAs), `tests/test_prose_renderer_v2.py` PASS (246 cases, Fp=0),
  `tests/test_v7_rules.py` 10/10, `tests/test_laya_family.py` OK.

## 1. Headline counts

| Count | Value |
|---|---|
| Sections audited | 36 (34 v4 + bnss-144-3, bnss-146 v4.1) |
| Sections with NO route at all before this lane (no Stage 2 disposition in the v7 path) | **2**: `bnss-144-3`, `bnss-146` |
| Sections with no kept-emission route by design (procedure/document nodes, never `kept_ids`) | **16** (all `proc-*` / `doc-*`, §4) |
| Sections with no route after this lane's fixes | **0 statutory** (both sub-routes are now conditional candidates, §3); 16 proc/doc remain by design |
| Routes with no test in the v7 path (no `tests/test_v7_rules.py` case) | **4**: `hma-26`, `births-deaths-act-1969`, `bnss-144-3`, `bnss-146` — of which 2 are covered elsewhere (16-Q + prose) and **2 are truly untested in the v7 path** (`bnss-144-3`, `bnss-146`; only the separate `laya_family` runtime tests them) |
| New routes added by this lane with no committed test yet | **3**: `restit_p` prompt, `dvcomp_p` prompt, post-order split facts (`arrears_recovery_asked` / `maintenance_variation_asked`) — tests are not this lane's owned files, so verification is by ad-hoc probe (§3.3), not a committed test |
| 16-Q before / after | **14/16 → 14/16** (rating 7.6 → 7.6, same H6/H14 misses, 0 new FP) — no regression, by construction (§3.3) |

The v6 example that motivated this lane (`hma-9` + `pwdva-22` as "leaf nodes
with no route") is **outdated**: both have had a full evidence → Stage 2 route
since the v6 work. What they lacked — and still lacked before this lane — was
any *neural* route: no noul prompt and no Qwen slot, so both were
evidence-anchor-only. This lane fixes that half (§3.1). The true
no-route leaves in v4/v4.1 were `bnss-144-3` / `bnss-146` (§3.2).

## 2. Full audit table (36 sections)

Legend — Route: YES = a question can reach this section as `kept_ids` (or, for
companions, as `kept_ids` under `v3_bundled` / `applied_principles` under
`statutory_primary`); COND = Stage 2 considers it but only as a `conditional`
disposition (never `kept_ids`); DESIGN = never a `kept_id` by design. Prompt =
`LAYA_NOUL_PROMPTS` key in `src/laya_v7_extractor.py` (9 before this lane, 11
after). Slot = Qwen constrained slot in `CONSTRAINED_SLOTS`. Test = grep
evidence in `tests/test_v7_rules.py` (`t7r`), prose tests, 16-Q/Brutal via
`tests/v7_backtest.py`, or the maintenance fixtures / `test_laya_family.py`
(`fam`, separate runtime only).

| # | Section | Route | Evidence anchor (`laya_v7_evidence.py`) | Noul prompt | Qwen slot | Stage 2 (`laya_v7_graph.py`) | Test coverage |
|---|---|---|---|---|---|---|---|
| 1 | `bnss-144` | YES | `money_fact` (`_MAINT_CLAIM_RE`) | `maint_a`, `maint_p` | `mn` | eligible (subsistence / parent / father-child-only / existing-order / post-decree) | t7r ×11, fixtures, prose, 16-Q |
| 2 | `hma-24` | YES | `interim_asked`, `proceeding_pending_hma`, `being_filed` | — (via pending/interim facts) | `ph`, `bf` | eligible (pending-HMA interim) | t7r ×1, fixtures, prose, 16-Q H14 |
| 3 | `hma-25` | YES | `lump_sum_settlement`, `decree` | — (via lump-sum/decree facts) | `ls`, `dc` | eligible (decree / lump-sum settlement) | t7r ×1, fixtures, prose, 16-Q |
| 4 | `pwdva-20` | YES | `money_fact` + female + `domestic_relationship` | `maint_a`, `maint_p` | `mn` | eligible (female, dom. rel., not child-only) | t7r ×3, prose, 16-Q |
| 5 | `hma-26` | YES | `custody_claim` + `proceeding_pending_hma`/`being_filed` | `cust_p` | `cs`, `ph`, `bf` | eligible (custody inside HMA proceeding) | **no t7r case**; 16-Q H14, prose |
| 6 | `gwa-1890` | YES | `custody_claim`, no pending HMA | `cust_p` | `cs` | eligible (standalone guardianship/custody) | t7r ×3, prose, 16-Q |
| 7 | `hmga-1956-s6` | COND | — (companion, no independent trigger) | — | — | companion: appended to `kept_ids` under `v3_bundled`; `applied_principles` only under `statutory_primary` (D-V4-1) | t7r ×1, 16-Q |
| 8 | `welfare-principle` | COND | — (companion, never creates a kept section by itself; v4.1 `scoring_semantics`) | — | — | same as `hmga-1956-s6` | t7r ×2, 16-Q |
| 9 | `hma-27` | YES | `joint_property_claim` (`_JOINT_PROP_RE`) | `jp_p` | `jp` | eligible (D2 gate: HMA proceeding pending/being filed) | t7r ×8, prose, 16-Q |
| 10 | `bns-316` | YES | `stridhan_claim` + `stridhan_held_or_disposed`, female | `strid_p` | `st` | eligible (female, dom. rel., held/disposed); male claimant gated out | t7r ×2, prose, 16-Q H3/H10/H15 |
| 11 | `pwdva-17` | YES | `residence_claim` | `res_a` | `rs` | eligible (female, dom. rel.) | t7r ×2, prose, 16-Q |
| 12 | `pwdva-18` | YES | `violence` / `coercive_eviction_or_lockout`, not `explicit_residence_order_only` | `vio_a` | `vo` | eligible, independent of pwdva-17/19 | t7r ×3, prose, 16-Q — **known FN: H6 (1)** |
| 13 | `pwdva-19` | YES | `residence_claim` | `res_a` | `rs` | eligible (female, dom. rel.) | t7r ×2, prose, 16-Q |
| 14 | `hma-13` | YES | `divorce_asked`, not `judicial_separation_only` | `div_p` | `dv` | eligible (contested) | t7r ×2, prose, 16-Q — **known FN: H14 (1)** |
| 15 | `hma-13b` | YES | `mutual_consent` | — (no dedicated prompt; `div_p` covers divorce generally) | `mc` | eligible (mutual consent, supersedes hma-13) | t7r ×2, prose, 16-Q |
| 16 | `births-deaths-act-1969` | YES | `birth_cert_asked` (`_BIRTH_CERT_RE`) | `bc_p` | `bc` | eligible | **no t7r case**; prose, 16-Q H7 |
| 17 | `hma-9` | YES (evidence-only before this lane; +neural now) | `restitution_asked` (`_RESTITUTION_RE`) + issue `restitution` | **NEW `restit_p`** (§3.1) | — (no slot; 18-slot DFA unchanged) | eligible (not divorce-asked) | t7r ×1 |
| 18 | `pwdva-22` | YES (evidence-only before this lane; +neural now) | `dv_injury_comp_asked` (`_DV_COMP_RE`) + issue `dv_compensation`; requires `violence` | **NEW `dvcomp_p`** (§3.1) | — (no slot) | eligible (female, dom. rel., violence + comp ask) | t7r ×1 |
| 19 | `bnss-144-3` | **NO → COND** (§3.2) | `existing_order_enforcement` only (generic; `_ARREARS_VARY_RE` conflates recovery + variation) | — | `eo` (generic existing-order only) | **no disposition before this lane**; now `conditional` when `arrears_recovery_asked` | **no v7-path test**; `fam` runtime only (fixtures, `test_laya_family.py`, `live_family_smoke.py`) |
| 20 | `bnss-146` | **NO → COND** (§3.2) | as above; additionally `_ENHANCE_COST_RE` actively suppresses `existing_order` on "prices gone up, increase it" asks (Lane 03, §5) | — | `eo` (generic) | **no disposition before this lane**; now `conditional` when `maintenance_variation_asked` | **no v7-path test**; `fam` runtime only |
| 21 | `proc-court-family-court` | DESIGN | — | — | — | never emitted; forum derives from kept sections via `court_for_v7` | none (by design) |
| 22 | `proc-court-magistrate` | DESIGN | — | — | — | as above | none (by design) |
| 23 | `proc-filing-hma` | DESIGN | `procedure_how_to_asked` feeds the `procedure` escalation kind, not a kept id | — | — | never emitted | none (by design) |
| 24 | `proc-filing-magistrate` | DESIGN | as above | — | — | never emitted | none (by design) |
| 25 | `proc-interim-relief` | DESIGN | `interim_asked` feeds hma-24 routing, not a kept id | — | — | never emitted | none (by design) |
| 26 | `proc-evidence` | DESIGN | — | — | — | never emitted | none (by design) |
| 27 | `proc-final-order-enforcement` | DESIGN | `existing_order_enforcement` feeds bnss-144 / 144-3 / 146 routing, not a kept id | — | — | never emitted | none (by design) |
| 28 | `proc-divorce-gate` | DESIGN | `divorce_asked` gates hma-13/13b; Layer A `procedure:divorce-gate` branch exists | — | — | never emitted (choice node only) | Layer A branch exists; no kept-id test (by design) |
| 29 | `doc-marriage-proof` | DESIGN | — | — | — | never emitted | none (by design) |
| 30 | `doc-birth-certificate` | DESIGN | `birth_cert_asked` feeds `births-deaths-act-1969`, not a kept id | `bc_p` | `bc` | never emitted | none (by design) |
| 31 | `doc-income-ask-not-demand` | DESIGN | — | — | — | never emitted | none (by design) |
| 32 | `doc-school-fee-amount` | DESIGN | `school_fees_fact` (fact only) | — | — | never emitted | none (by design) |
| 33 | `doc-husband-whereabouts` | DESIGN | — | — | — | never emitted | none (by design) |
| 34 | `doc-stridhan-list-proof` | DESIGN | `stridhan_claim` feeds bns-316, not a kept id | `strid_p` | `st` | never emitted | none (by design) |
| 35 | `doc-residence-proof` | DESIGN | `residence_claim` feeds pwdva-17/19, not a kept id | `res_a` | `rs` | never emitted | none (by design) |
| 36 | `proc-timeline-staged` | DESIGN | — | — | — | never emitted | none (by design) |

Notes on the table:
- "Route YES" means the section is reachable as `kept_ids` from a real
  question through the v7 path (`extract_v7` → `evaluate_stage2_v7`). It does
  NOT mean recall is good — the 16-Q FNs (H6 pwdva-18, H14 hma-13) and the
  sealed Fresh-20 FNs (hma-27 ×4, pwdva-17/18/19 ×3 each, hma-13 ×2, hma-24
  ×2, gwa-1890 ×2, hmga-1956-s6 ×2 — per `docs/10x_plane.md` §1.1) are cases
  where the route exists but the Stage 1 evidence missed. Those are anchor /
  calibration failures, not missing routes.
- `hma-13b` has no dedicated noul prompt: `div_p` asks about divorce
  generally and `mc` (slot) + the evidence anchor carry mutual consent. A
  `mutual_p` probe is a cheap follow-up, not done here (threshold calibration
  needs RTX ROC data anyway).
- `hmga-1956-s6` / `welfare-principle` are companions by design (D-V4-1):
  they ride with custody under `v3_bundled` and live in `applied_principles`
  under `statutory_primary`. No independent trigger exists or is wanted —
  welfare never creates a kept section by itself.
- `proc-*` / `doc-*` (16 sections): a grep for `proc-` / `doc-` across
  `src/` and `tests/` returns **zero hits outside the graph JSON itself** —
  no code anywhere emits them as `kept_ids`, and no test expects them. That
  is a design decision, recorded in §4, not a fix: they are routing /
  procedure / document metadata, and their content surfaces through
  `court_live`, typed escalation kinds, and prose — not through `kept_ids`.

## 3. Fixes applied (this lane)

All fixes are in this lane's owned files only: `src/laya_v7_extractor.py`,
`src/laya_v7_graph.py`. `src/laya_v7_evidence.py` was **not touched**
(contract R3 — Lane 03 owns it). No other lane's files were touched.

### 3.1 Neural routes for hma-9 and pwdva-22 (extractor)

- `LAYA_NOUL_PROMPTS`: 9 → **11 prompts**. Added:
  - `restit_p`: "Does the speaker want their husband or wife who left home
    to come back and resume living together as husband and wife (not a
    divorce)?"
  - `dvcomp_p`: "Does the speaker ask for compensation, damages, or payment
    of medical or hospital costs for injuries caused by domestic violence?"
- `_merge_laya_and_grounded`: both pooled as `max(full, cmax)` like the other
  probes, then `_boost("restitution_asked", "restitution", restit_p, 0.55)`
  (gated on divorce NOT asked, mirroring the graph gate) and
  `_boost("dv_injury_comp_asked", "dv_compensation", dvcomp_p, 0.45)` (gated
  on proved violence or the `vio_a` probe firing).
- Thresholds are **UNCALIBRATED**: no ROC data exists on this CPU-only VM
  (no torch/GPU, no neural run possible here). RTX re-calibration against the
  validation split is a follow-up; the prompts must not be treated as tuned.
- Structured mode still has no restitution / DV-comp slot: the 18-slot DFA
  (`CONSTRAINED_SLOTS`) is unchanged — adding slots 19/20 changes the
  grammar and is a coordinator decision, not a one-lane fix. In structured
  mode both sections remain evidence-anchor-only. Documented in
  `_apply_structured_slots`.

### 3.2 Post-order sub-routes bnss-144-3 / bnss-146 (extractor + graph)

Root cause (verified by reading the code, not assumed): `evaluate_stage2_v7`
had **zero dispositions** for either section — the graph v4.1 JSON has the
leaf nodes (`stage2:bnss-144-3-leaf`, `stage2:bnss-146-leaf`) and the
`maintenance:post-order-enforcement` choice node, but the executable Stage 2
never consulted them. The only live routes were in the *separate*
`laya_family.py` runtime (`recover` → bnss-144-3, `vary` → bnss-146), which
the v7 path never calls. The v7 evidence layer could not have distinguished
them anyway: it emits one generic `existing_order_enforcement` fact whose
`_ARREARS_VARY_RE` conflates arrears words with vary words.

Fix, in two parts:

(a) **Extractor — post-order split facts** (`_post_order_split_facts`,
    wired into `extract_v7_batch` for all modes, with module regexes
    `_ARREARS_RECOVERY_RE`, `_MAINT_ORDER_PHRASE_RE`,
    `_MAINTENANCE_VARIATION_RE`):
    - `arrears_recovery_asked`: supported when grounded
      `existing_order_enforcement` is proved AND arrears language is present
      ("arrears", "unpaid maintenance/instalments", "has not paid …
      maintenance", "recover the arrears", "execution petition", "warrant …
      recovery", "amounts already due", "overdue"). The "not paying
      maintenance" phrasing is the common real-world form (Kaanoon, §6).
    - `maintenance_variation_asked`: supported when an order phrase AND a
      variation phrase are both present ("court ordered/fixed maintenance" +
      "increase/reduce/vary/revise the maintenance/amount", "change of
      circumstances", "amount be revised", "get it increased"). It is
      deliberately NOT gated on grounded `existing_order`: the evidence
      `_ENHANCE_COST_RE` guard suppresses `existing_order` on exactly the
      "prices gone up, increase it" asks, which would make the fact dead on
      arrival (see §5, Lane 03 item 3). Stem forms (`increas\w*`) are used
      because a trailing `\b` after "increase" can never match "increased" /
      "revised" — the same dead-alternative trap found in `_DV_COMP_RE`
      (§5, Lane 03 item 1).
    - Both facts use `source="extractor"`, confidence 0.8, and are absent
      (not set) when there is no order signal, so downstream `proved_true()`
      defaults to False. Lane 03 may promote/strengthen them into
      `evidence.py` later; they are extractor-side emissions, not evidence
      anchors.

(b) **Graph — conditional dispositions + Layer A + forum**
    (`src/laya_v7_graph.py`):
    - New §1b block in `evaluate_stage2_v7`: when maintenance is requested
      and either split fact fires, adds a `conditional` disposition for
      `bnss-144-3` ("arrears_recovery_asked_post_order") and/or `bnss-146`
      ("maintenance_variation_asked_post_order"), with
      `missing_facts=["existing_order_statute_bnss144"]` and a `gated_out`
      entry explaining the gate.
    - **Why conditional, not eligible — deliberate and blocking:** promoting
      either section to `kept_ids` today would break the live pipeline.
      `src/laya_prose_v2.py:KNOWN_SECTIONS` (18 sections) contains NEITHER
      `bnss-144-3` nor `bnss-146`; `render_prose` returns
      `INVALID_RECORD_HANDOFF` with `status="error"` for any unknown kept
      id. (Kannada prose, `src/laya_prose_kn.py`, DOES cover both — EN prose
      is the gap.) Eligible promotion needs (i) EN prose templates for both
      sections — prose lane's file, not this lane's — and (ii) a statute fact
      proving the order is BNSS s.144, not a pre-1 Jul 2024 CrPC s.125 order
      (BNSS s.531 savings; no such fact exists in v7 evidence — Lane 03 /
      legal registry). Conditional dispositions still put both sections in
      `candidates_before_gate`, so the route is now measurable instead of
      invisible, and `kept_ids` are unchanged (zero 16-Q impact).
    - `MAGISTRATE_SECTIONS` += `bnss-144-3`, `bnss-146`; forum authority
      entries added for both (used once they become eligible).
    - `layer_a_filter_options`: new `maintenance:post-order-enforcement`
      branch — drops the 144(3) option unless existing-order + arrears ask,
      drops the 146 option unless variation ask, drops the generic
      arrears/shortfall option unless existing-order or variation ask.

### 3.3 Verification (all run by this lane, CPU, evidence mode)

Ad-hoc probes (not committed tests — test files are not this lane's):
- Arrears ("court ordered maintenance … has not paid it for six months …
  recover the arrears"): `existing_order_enforcement` supported,
  `arrears_recovery_asked` supported, `maintenance_variation_asked` denied;
  kept `['bnss-144']` unchanged; `candidates_before_gate` now includes
  `bnss-144-3`. ✓
- Variation ×3 ("prices have gone up … get it increased", "earns double …
  amount be revised because circumstances have changed", "lost my job …
  amount be reduced"): `maintenance_variation_asked` supported in all
  three; kept unchanged; `candidates_before_gate` includes `bnss-146`. ✓
  (Note: `existing_order_enforcement` is *denied* on the first two — the
  `_ENHANCE_COST_RE` suppression, §5 item 3 — which is why the variation
  fact is not gated on it.)
- Fresh maintenance / fresh divorce probes: neither split fact fires. ✓
- Layer A (`maintenance:post-order-enforcement` options): arrears question
  keeps 4/5 (drops only the 146 option); variation question keeps 4/5
  (drops only the 144(3) option); fresh-maintenance question keeps 2/5
  (drops all three post-order options). ✓

Full battery, before → after:
| Check | Before | After |
|---|---|---|
| `python3 -m tests.v7_backtest --suite 16q --mode evidence --device cpu` | 14/16, rating 7.6 (misses H6 pwdva-18, H14 hma-13) | **14/16, rating 7.6 (same two misses, 0 FP, 0 errors)** |
| `python3 tests/test_graph_v4.py` | PASS (34/66/99, 7/7 SHAs) | PASS (same) |
| `python3 tests/test_prose_renderer_v2.py` | PASS (246, Fp=0) | PASS (same) |
| `PYTHONPATH=. python3 tests/test_v7_rules.py` | 10/10 OK | 10/10 OK |
| `PYTHONPATH=. python3 tests/test_laya_family.py` | OK | OK |

## 4. Design decisions recorded (not fixes)

1. **`proc-*` / `doc-*` (16 sections) have no kept-emission route, by
   design.** They are procedure/document metadata in the graph JSON; no code
   in `src/` or `tests/` references them as `kept_ids` (verified by grep —
   zero hits outside the graph JSON). Their content surfaces through
   `court_live`, typed escalation kinds (`procedure`, `court`, `fact`,
   `quantum`), and prose — not through `kept_ids`. If any future ground
   truth ever expects a `proc-*` / `doc-*` id inside `kept_ids`, that would
   be a systematic miss on every question; no current GT (16-Q, Brutal-230,
   sealed aggregates) does. Coordinator to confirm this is the intended
   contract — if not, the fix is a Stage 2 / scorer change, not a Stage 1
   route fix.
2. **`hmga-1956-s6` / `welfare-principle` are companions, not independent
   routes** (D-V4-1). No trigger of their own is wanted.
3. **`bnss-144-3` / `bnss-146` stay conditional, not eligible** (§3.2b) until
   EN prose covers them and a BNSS-order statute fact exists. This is a
   deliberate cap, not an oversight.

## 5. Gaps found for other lanes (not fixed here — out of this lane's files)

These were found while auditing and are recorded so the owning lane can act;
none were fixed here because the files belong to other lanes.

1. **Lane 03 — `_DV_COMP_RE` "injur" alternative is dead** (`evidence.py`).
   The pattern requires `\b(?:injur|…)\b` — a word boundary *after* "injur".
   "injury"/"injuries" continue with a word character (`y`/`i`), so the
   alternative can never match a real word. Verified: "Can I get
   compensation for my injuries?" (with proved violence, "broke my arm")
   returns `dv_injury_comp_asked` denied and `pwdva-22` is missed; the probe
   kept only `pwdva-18`. Fix is a one-character-class change in Lane 03's
   file (`injur\w*`). My `dvcomp_p` neural prompt covers the same ask in
   laya mode, but the evidence path — the one the CPU backtest uses — needs
   the anchor fix.
2. **Lane 03 — `_RESTITUTION_RE` misses the common lay phrasing, and the
   custody anchor over-fires on it** (`evidence.py`). Probe: "My wife left
   home six months ago … I want her to come back and live with me." The
   restitution anchor requires "come back *to* live with me" — "come back
   *and* live with me" misses — so `restitution_asked` is denied AND the
   custody anchor (`_CUSTODY_ASK_RE`, "want her … to come back … with me")
   fires instead, keeping `gwa-1890` + companions on a spouse-return
   question. The Kaanoon reference (§6) shows "my wife is not coming back
   to me" / "she left and went to her hometown" is how laypeople actually
   phrase this — the anchor's "come back to" wording is lawyer-shaped, not
   lay-shaped. My `restit_p` prompt covers it in laya mode; the evidence
   anchor needs the "come back and live" / "not coming back" forms, and the
   custody anchor needs a spouse-vs-child guard on return phrasing.
3. **Lane 03 — `_ENHANCE_COST_RE` blocks the bnss-146 route**
   (`evidence.py`). It suppresses `existing_order_enforcement` whenever an
   enhancement ask is detected ("prices have gone up … increase"), so a
   variation question can never carry the fact the 146 route needs. This
   lane worked around it with the extractor-side order phrase (§3.2a), but
   the clean fix is a dedicated statute/enhancement fact in evidence.py.
4. **Lane 01 / coordinator — no pre-BNSS statute fact.** Nothing in v7
   evidence distinguishes a BNSS s.144 order from a pre-1 Jul 2024 CrPC
   s.125 order, so `bnss-144-3` / `bnss-146` (and, equally, the existing
   `existing_order` → `bnss-144` routing) cannot honour the BNSS s.531
   savings guard. `src/laya_legal_registry.py` documents the rule; no Stage
   0/1 fact feeds it.
5. **Prose lane — EN prose has no `bnss-144-3` / `bnss-146` templates**
   (`src/laya_prose_v2.py:KNOWN_SECTIONS`, 18 sections). This is the binding
   blocker on eligible promotion (§3.2b). Kannada prose already covers both.
6. **Coordinator — structured-mode slots cannot split recover vs vary.**
   Slot `eo` is one bit for "enforcing arrears or varying … an existing
   order". Splitting it needs slots 19/20 and a DFA change.
7. **Lane 03 / Lane 01 — 16-Q residual FNs are anchor failures, not route
   gaps.** H6 (pwdva-18) and H14 (hma-13) both have complete routes; the
   evidence missed on those items. No route fix in this lane can close them.

## 6. Kaanoon reference — what it contributed

Per the follow-up task (user, voice call 2026-11-27): `https://www.kaanoon.com/`
("Legal answers online from lawyers — Indian Kaanoon", the Q&A portal the
user mentioned on 2026-11-26 for clarity on the Laya decision graph) was used
as a REFERENCE for how real laypeople phrase family-law questions. Rules
followed: no scraping or copying of Q&A content (licensing/IP); only observed
phrasing patterns, paraphrased here; no Kaanoon answer cited as legal
authority; small sample only — 2 web searches + 1 public page fetch
(`browser.search` / `browser.open` text fetch, no live-browser work).

What was observed (patterns, paraphrased — no quoted Q&A content):
- **Maintenance arrears is phrased as non-payment, not as a section.**
  Laypeople write "court ordered maintenance but he is not paying" / "not
  giving money for monthly expense" / "how do I get the money / execution".
  This is the bnss-144-3 ask, and it is common. It confirmed the 144-3 gap
  as the highest-value real-world route gap: the most ordinary
  post-order question in the wild had no v7 route at all.
- **Variation is phrased as insufficiency + change.** "Amount is not
  enough", "prices have gone up", "he earns double now", "can it be
  increased / revised" — the bnss-146 ask, again without section language.
  It also exposed the `_ENHANCE_COST_RE` suppression (§5 item 3): the
  exact phrasing laypeople use is the phrasing the evidence layer excludes
  from `existing_order`.
- **Restitution is phrased as desertion + return, not as a section.**
  "My wife is not coming back to me", "she left and went to her hometown",
  "I asked her several times to continue the married life", "what should I
  do — RCR or divorce?" The fork itself (save the marriage vs end it) is
  often the question. This exposed the `_RESTITUTION_RE` miss and the
  custody over-fire (§5 item 2).
- **Mutual consent is phrased as agreement.** "We both agree", "she agrees
  to divorce", "both want to end it by mutual consent" — supports the
  existing `mc` slot + anchor; no dedicated noul prompt exists (§2, row 15).

What it changed in this lane: it set the fix priority (post-order split
first, because arrears/variation are everyday lay questions with zero route)
and it supplied the exact lay phrasings the new split-fact regexes and the
two new noul prompts are written against. It changed no code by itself —
every fix above is grounded in the repo's own graph and code, with Kaanoon
as the phrasing check.

Lane 11 note (contracts R6/R7): Lane 11 is building a study sample whose
phrasing patterns go to `docs/kaanoon_phrasing_patterns.md`, plus a separate
fresh held-out eval set at `data/kaanoon_eval/heldout.jsonl`. **As of the
final write of this audit, `docs/kaanoon_phrasing_patterns.md` does not exist
yet** (checked 2026-11-27 ~19:24 IST and again before committing — file
absent; Lane 11 had not landed). This audit therefore uses only the lane's
own small Kaanoon reference read above, not Lane 11's patterns file. If that
file lands, the coordinator can append its deltas; this audit does not claim
them. The held-out eval set was **never opened, read, or used for any fix or
tuning** (R6); only Lane 07 scores it. Study/eval disjointness (R7) is
Lane 11's to guarantee — nothing in this lane touches either sample.

## 7. What is still unverified

- **Neural prompts (`restit_p`, `dvcomp_p`):** uncalibrated thresholds
  (0.55 / 0.45), no ROC data, no neural run possible on this VM (no
  torch/GPU). Needs an RTX run: `extract_laya_probs_batch` on the
  validation split + threshold calibration before the prompts are trusted.
  Evidence-mode numbers are unaffected (prompts only run in `laya` mode).
- **Split facts:** verified only by the six ad-hoc probes in §3.3. No
  committed test covers them (test files are not this lane's). A
  `test_v7_rules.py` case for arrears/variation routing is the obvious
  follow-up for whoever owns tests.
- **Eligible promotion of bnss-144-3 / bnss-146:** blocked on EN prose
  templates + BNSS-order statute fact (§3.2b, §5 items 4–5). Until those
  land, the sections are candidates, not kept ids — an unseen arrears or
  variation question will still score `bnss-144` only on exact match.
- **Sealed sets:** untouched, as required. No claim is made about
  Fresh-20/Kannada-8 movement — the sealed re-run happens only on the RTX
  machine (Lane 07 / coordinator).
- **Lane 11 patterns file:** not yet landed at audit time (§6) — a later
  delta may add phrasings this audit did not see.
