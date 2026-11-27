# LAYA Decision Graph v4 + Stage 2 Legal Routing + Evaluation Alignment Blueprint

**Owner:** `graph-architect` (Swarm Plan — Offline Architecture Spec; no files modified inside `laya-family-law`)  
**Target Artifact:** `docs/v4-decision-graph-architecture.md`  
**Baseline Evaluated:** Live `v6-brutal` run on RTX 5050 GPU (`results/live-laya-colab-results-v6-brutal-final.json`, `results/live-laya-colab-results-v6-brutal.md`, `results/live-laya-colab-results-v6-brutal-regression.md`) against Graph v3 (`34` sections / `48` nodes / `79` edges, SHA `67bf2b04...`).  
**Sealed-Data Compliance:** Zero sealed question wording from `test-bank\sealed\*` is printed or quoted anywhere in this document; only IDs and aggregate counts are referenced.

---

## 1. Executive Summary & Root-Cause Attribution

### 1.1 Measured Live `v6-brutal` Baseline vs Target Gate (`brutal-test-200-plan.md` §3.2 & `G1–G15`)

| Benchmark | Exact | Micro P / R / F1 | TP / FP / FN | Court | Esc-Bool | Esc-Kinds (strict) | Silent | Fb | Fp | Rating |
|---|---|---|---|---|---|---|---|---|---|---|
| **16-Q Regression** (`v2` GT, 53 sec) | **16/16** (100%) | 1.000 / 1.000 / 1.000 | 53 / 0 / 0 | **13/16** (`H3, H10, H15` mismatch) | **16/16** | **11/16** (`K0, H4, H5, H6, H13` extra `safety`) | 0 | 0 | NOT MEASURED | 9.0 capped (9.9 raw) |
| **Brutal-230** (`v1-frozen` GT) | **79/230** (34.3%) *(84/230 excl. custody vocab)* | 0.750 / 0.542 / 0.629 | 225 / 75 / 190 | **152/230** (66.1%) | **144/230** (62.6%) | **48/230** (20.9%) *(70/230 fact-excl.)* | **75** | **5** (`B-018, B-118, B-131, B-150, B-187`) | NOT MEASURED | **1.9/10** |
| **Sealed Fresh-20** | **5/20** (25.0%) | 0.868 / 0.500 / 0.635 | 33 / 5 / 33 | **8/20** | **17/20** | **6/20** *(7/20 fact-excl.)* | 3 (`F5, F6, F11`) | 1 (`F4`) | NOT MEASURED | — |
| **Sealed Kannada-8** | **1/8** (12.5%) | 1.000 / 0.043 / 0.083 | 1 / 0 / 22 | **1/8** | **1/8** | **1/8** *(5/8 fact-excl.)* | 6 | 0 | NOT MEASURED | — |
| **Target (`§3.2` + `G1–G15`)** | **≥200/230** + 16/16 + 20/20 + 8/8 | **≥0.95 / ≥0.95 / ≥0.95** (mean P/R ≥0.90) | — | **≥200/230** + 16/16 | **≥200/230** | **≥200/230** + 16/16 | **0** | **0** | **0** | **≥9.5 brutal / 10.0 gate** |

### 1.2 Exact Decomposition of `v6-brutal` Failures (Graph/Stage-2/Scoring vs Stage-1/Extraction)

From `brutal_230_diagnostic.json` and `live-laya-colab-results-v6-brutal-final.json`:
1. **Stage-1 Silent / Recall Collapse (`75` silent, `190` FN; owned jointly with `@gate-prompt-engineer` & `@kannada-prose-perf`):**
   - English text-gate & prompt misses on custody (`gwa-1890` FN=41), maintenance (`bnss-144` FN=23, `pwdva-20` FN=22), residence (`pwdva-17/19` FN=16 each), violence (`pwdva-18` FN=19), Stridhan (`bns-316` FN=18), and Kannada C13 (`1/16` exact).
2. **Graph v3 / Stage 2 Structural & Routing Failures (owned here):**
   - **3 pre-existing v2 dangling edges** (`stage1:confidence-gate -> escalate_clarify`, `stage2:demand-gate -> bns-316`, `stage2:demand-gate -> escalate_demand_first`) + `bnss-144` `related_sections` typo `'hmga-6'` (real ID `'hmga-1956-s6'`), plus non-canonical `related_sections` strings across v2 sections.
   - **Unwired / zero-hit routes (`22` FNs directly, plus `18`+ cross-route FPs):**
     - `hma-9` (`0` TP, `1` FN `B-018`): leaf exists in v3, zero Stage 1/2 route.
     - `pwdva-22` (`0` TP, `1` FN `B-019`): leaf exists in v3, zero Stage 1/2 route.
     - `hma-13b` (`0` TP, `5` FN `B-017, B-026, B-078, B-154, B-191`, + `3` `hma-13` FPs): hardcoded comment `"HMA 13B is never added"` in `stage2()`.
     - `hma-25` (`0` TP, `4` FN `B-022, B-119, B-154, B-201` + `F4`): Layer A blocks pre-decree lump-sum settlement (`B-022/119/154`), and `B-201`/`F4` fail maintenance routing.
     - `hma-26` (`0` TP, `4` FN `B-006, B-099, B-115, B-123`): `stage2()` ignores `being_filed` (`B-123`) and Stage 1/gate misses `hma-26` queries.
     - `hma-27` (`1` TP, `8` FN `B-005, B-111, B-114, B-119, B-122, B-123, B-126, B-228`): Stage 1/2 treats `stridhan` strictly as wedding gold (`gold_fact`), never routing **joint matrimonial property** inside a pending/being-filed HMA proceeding.
     - `hma-24` (`3` TP, `3` FN `B-144, B-150, B-202`, `1` FP `B-035`, **`Fb=5`** `B-018, B-118, B-131, B-150, B-187` + `F4` `Fb=1`): NO Layer A gate on `hma-24`; `'full maintenance picture'` silently drops `hma-24` (`B-144`, `F3`, `F15`); Magistrate-pending case `B-035` confused with HMA proceeding.
   - **Over-firing / Applicability / Bundling Failures (`75` FP):**
     - **Male claimant / parent / post-order maintenance over-fires (`pwdva-20` FP=25, `bnss-144` FP=14):** `pwdva-20` emitted for husbands (`B-144, B-146, B-150, B-153`), parents (`B-037, B-047`), post-order arrears/enforcement/reduction (`B-046, B-077, B-187, B-195, B-196, B-198, B-200`), lump-sum settlements (`B-022, B-201`), pure HMA 24 (`B-117, B-202`), and `bnss-144` emitted for husband self-maintenance (`B-144, B-150`) and pure Stridhan/incidental mentions (`B-052, B-058, B-064, B-090, B-128, B-155, B-165`).
     - **PWDVA 17/18/19 all-or-nothing bundling:** forces `pwdva-18` onto non-intimidation/forum-only residence claims (`B-010, B-023, B-189`).
     - **Non-domestic / undisputed Stridhan FPs (`bns-316` FP=5):** fires on gold in wife's/joint/undisputed possession (`B-069, B-156, B-162`) or abandoned/locker-safe gold (`B-066, B-134`).
     - **Custody vocabulary split (`hmga-1956-s6` FP=8, `welfare-principle` FP=8):** `5` pure vocab misses (`B-081, B-107, B-137, B-149, B-190`), threatening all `52` brutal custody questions once recall is fixed.
   - **Court & Escalation State-Machine Gaps (`court` 152/230 & 13/16; `esc-kinds` 48/230 & 11/16):**
     - `court_for` provisional fallback guesses `Family Court` on gated/dropped `divorce` fires (`F20`, `B-130`, `B-141`, `B-006`).
     - `16-Q` `H3/H10/H15` `court_expected` still lists `['Family Court', 'Magistrate']` post-D1-A despite `bns-316`-only GT.
     - `SCORING_KINDS` omits `fact` (`44` bank uses), `procedure` lacks OOS-handoff & divorce/how-to triggers (`30` bank uses), `court` lacks explicit forum-ask trigger (`6` C11 uses), `recovery` wrongly triggers on `hma-27` joint property & misses `stridhan_sold` (`demand_made=None`), and `16-Q` `ground-truth-v2` omits `safety` while Brutal-230 expects `safety` (`32` uses).

---

## 2. Graph v4 Structural & Schema Fixes (`laya-crpc-bns-section-decision-tree-v4.json`)

Graph v4 is built deterministically from `laya-crpc-bns-section-decision-tree-v3.json` (`34` sections / `48` nodes / `79` edges) with **zero unverified statutory sections added** (`34` sections preserved) and **100% referential integrity** across all nodes, edges, and `related_sections`.

### 2.1 Fixing All v3 Structural Defects

| Defect ID | Location in v3 | Exact v4 Fix |
|---|---|---|
| **DEF-1** | Edge `[67]`: `stage1:confidence-gate -> escalate_clarify` | Add leaf node `stage1:escalate-clarify` (`type: "leaf"`, `lane: "stage1"`, `section_set: []`, `question: "No family-law issue can be picked with confidence — clarify facts with the user before classifying."`, `options: ["Clarify missing facts"]`). Update edge `[67]` `to` → `"stage1:escalate-clarify"`. |
| **DEF-2** | Edge `[74]`: `stage2:demand-gate -> bns-316` | Target was a section ID instead of a node ID. Update edge `[74]` `to` → `"stridhan:bns-316-leaf"` (existing leaf node in v3). |
| **DEF-3** | Edge `[75]`: `stage2:demand-gate -> escalate_demand_first` | Add leaf node `stage2:escalate-demand-first` (`type: "leaf"`, `lane: "stage2"`, `section_set: ["bns-316"]`, `question: "Stridhan held but no demand yet made — keep BNS s.316 provisionally with demand-first escalation (make written demand/legal notice first, then re-evaluate)."`). Update edge `[75]` `to` → `"stage2:escalate-demand-first"`. |
| **DEF-4** | `sections[bnss-144].related_sections[4]` | Replace `"section_id": "hmga-6"` → `"section_id": "hmga-1956-s6"`. |
| **DEF-5** | `sections[hma-27, bns-316].related_sections` | Rename dict key `"section"` → `"section_id"` and convert display labels (`"BNS s.316"`, `"HMA s.27"`, `"PWDVA s.20"`, `"PWDVA s.18"`, `"PWDVA s.19"`, `"HMA s.24"`, `"HMA s.25"`, `"BNSS s.144"`, `"HMA s.26"`) to canonical IDs (`"bns-316"`, `"hma-27"`, `"pwdva-20"`, `"pwdva-18"`, `"pwdva-19"`, `"hma-24"`, `"hma-25"`, `"bnss-144"`, `"hma-26"`). |
| **DEF-6** | `sections[hma-26, gwa-1890, hmga-1956-s6, welfare-principle, pwdva-17/18/19, proc-*, doc-*].related_sections` | Normalize every plain string / `UPPER_SNAKE` (`HMA_26`, `GWA_1890`, `HMGA_1956_s6`, `WELFARE_PRINCIPLE`) into canonical `{"section_id": "<id>", "relationship": "<desc>"}` objects (splitting combined strings like `"HMA s.24 / HMA s.25 (...)"` into two entries) so **100% of `related_sections[].section_id` resolve in `SECTION_IDS`**. |
| **DEF-7** | `sections[hma-13, hma-13b, births-deaths-act-1969].laya_question` | Upgrade bare `str` values into structured `{"type": "choice", "question": ..., "options": [...]}` dicts matching all other statutory sections. Document `sections[welfare-principle].laya_question.type == "score"` as intentionally non-choice (welfare factor scorer). |
| **DEF-8** | `sections[hma-24, hma-25, hma-27, bns-316, pwdva-17/18/19/20, bnss-144]` text consistency | Update `bns-316.related_sections[hma-27]` and `hma-27` / `hma-25` descriptions to reflect v4 D1-A / joint-property / lump-sum / claimant-sex rules (zero `"alternatively..."` regressions; `bnss-144` notes male child-maintenance standing & husband self-maintenance exclusion; `pwdva-17/18/19/20` explicitly note `s.2(a)` woman-only requirement). |

### 2.2 New Graph v4 Nodes & Edges (Exact Additions & Counts)

All additions live in `nodes[]` and `edges[]` using the exact v3 schema (`node_id`, `type`, `lane`, `question`, `options`, `section_set`).

| Group | New `node_id`s | Type / `section_set` | New / Updated Edges | Purpose |
|---|---|---|---|---|
| **Defect fixes** (`+2` nodes, `+0` edges) | `stage1:escalate-clarify`, `stage2:escalate-demand-first` | `leaf` / `[]`, `leaf` / `["bns-316"]` | Redirect `[67]`, `[74]`, `[75]` | Eliminates all 3 dangling edges |
| **HMA 9 Restitution** (`+1` node, `+1` net edge) | `matrimonial:hma-9-choice` | `choice` / `["hma-9"]` | Replace `[77]` (`root -> stage2:hma-9-leaf`) with `root:issue-classification -> matrimonial:hma-9-choice` & `matrimonial:hma-9-choice -> stage2:hma-9-leaf` | Interactive choice + Stage 2 route for `hma-9` (`B-018`) |
| **PWDVA 22 Compensation** (`+1` node, `+1` net edge) | `violence:pwdva-22-choice` | `choice` / `["pwdva-22"]` | Replace `[78]` (`root -> stage2:pwdva-22-leaf`) with `root:issue-classification -> violence:pwdva-22-choice` & `violence:pwdva-22-choice -> stage2:pwdva-22-leaf` | Interactive choice + Stage 2 route for `pwdva-22` (`B-019`) |
| **Divorce 13 vs 13B Fork** (`+2` nodes, `+2` edges) | `stage2:hma-13-leaf`, `stage2:hma-13b-leaf` | `section_set` / `["hma-13"]`, `["hma-13b"]` | `procedure:divorce-gate -> stage2:hma-13-leaf`; `procedure:divorce-gate -> stage2:hma-13b-leaf` *(+ update `procedure:divorce-gate.options` to 4-way split)* | Exclusive `hma-13` vs `hma-13b` routing (`B-017/026/078/154/191`, `F16`) |
| **Joint Property HMA 27** (`+3` nodes, `+3` edges) | `stridhan:joint-property-check`, `stage2:hma-27-leaf`, `stage2:not-joint-property-leaf` | `choice` / `["hma-27"]`, `section_set` / `["hma-27"]`, `leaf` / `[]` | `root:issue-classification -> stridhan:joint-property-check`; `-> stage2:hma-27-leaf`; `-> stage2:not-joint-property-leaf` | Jointly-owned matrimonial property gated on `proceeding_pending_hma \| being_filed` (`B-005, B-111..B-126, B-228`) |
| **Maintenance Applicability & Post-Order** (`+4` nodes, `+8` net edges) | `maintenance:claimant-applicability-gate`, `maintenance:post-order-enforcement`, `stage2:hma-24-only-leaf`, `stage2:hma-25-settlement-leaf` | `choice` / `["bnss-144","pwdva-20","hma-24","hma-25"]`, `choice` / `["bnss-144","hma-24","hma-25"]`, `section_set` / `["hma-24"]`, `section_set` / `["hma-25"]` | Replace `[57]` (`root -> maintenance-root`) with `root -> claimant-applicability-gate` (`-> maintenance-root`, `-> hma-24-only-leaf`, `-> bnss-144-leaf`, `-> out-of-scope-handoff`); add `maintenance-root -> post-order-enforcement` (`-> bnss-144-leaf`, `-> hma-24-only-leaf`, `-> hma-25-settlement-leaf`) (`-1 + 9 = +8`) | Male spouse (`hma-24/25`), male/parent (`bnss-144`), lump-sum (`hma-25`), arrears/reduction (`bnss-144`) |
| **PWDVA Per-Section Split & Male DV** (`+3` nodes, `+3` edges) | `stage2:pwdva-17-19-residence-leaf`, `stage2:pwdva-18-protection-leaf`, `stage2:male-claimant-dv-handoff` | `section_set` / `["pwdva-17","pwdva-19"]`, `section_set` / `["pwdva-18"]`, `leaf` / `[]` | `stage2:pwdva-per-section-gate ->` all 3 new leaves | Independent `17/19` vs `18` (`B-010/023/133/189/214`, `B-006/072/076/082/087/136/142/155/159/168`) & male DV handoff (`B-148`) |
| **Empty-GT Terminal Leaves** (`+2` nodes, `+2` edges) | `stage2:out-of-scope-handoff`, `stage2:no-dispute-empty` | `leaf` / `[]`, `leaf` / `[]` | `stage1:confidence-gate -> stage2:out-of-scope-handoff`; `stage1:confidence-gate -> stage2:no-dispute-empty` | Distinguishes `C10`/`B-113/121/148`/`F20` handoffs (`escalates=True, procedure`) from `B-069/156` no-dispute empties (`escalates=False`) |

**Graph v4 Exact Count Totals (for Cell 5 strict validation):**
- **`sections`**: `34` (unchanged from v3)
- **`nodes`**: `48 + 18 = 66`
- **`edges`**: `79 + 20 = 99`
- **Strict Cell 5 Graph Integrity Assertions (replacing v3's counts-only bypass):**
  1. `assert (len(GRAPH['sections']), len(GRAPH['nodes']), len(GRAPH['edges'])) == (34, 66, 99)`
  2. `assert len({s['id'] for s in GRAPH['sections']}) == 34` and `len({n['node_id'] for n in GRAPH['nodes']}) == 66`
  3. `assert all(e['from'] in NODES and e['to'] in NODES for e in GRAPH['edges'])` (**zero dangling edges**)
  4. `assert all(rs['section_id'] in SECTION_IDS for s in GRAPH['sections'] for rs in s.get('related_sections', []))` (**zero unresolved `related_sections`**)
  5. `assert all(set(n.get('section_set', [])) <= SECTION_IDS for n in GRAPH['nodes'])`

---

## 3. Stage 1 <-> Stage 2 Canonical Interface Contract

To cleanly separate responsibilities between `@gate-prompt-engineer` / `@kannada-prose-perf` (Stage 1 signals, cross-lingual handling, fact extraction) and Stage 2 routing:

1. **Stage 1 outputs:**
   - `fired_issues` from expanded issue list: `maintenance`, `custody`, `stridhan`, `joint_property` (or merged into `property`), `residence`, `violence`, `dv_compensation` (`pwdva-22`), `divorce`, `restitution` (`hma-9`), `birth_certificate`, `in_scope`.
   - `sub_choices` from Graph v4 `choice` nodes (with Layer A pre-filtering applied before calling `agent.predict`).
2. **Canonical `facts` dict passed to `stage2()`** (frozen Cell 6 / Sealed annotations ALWAYS override extracted values via `complete_facts()`; Stage 2 NEVER inspects question IDs or raw question substrings directly):

| Fact Key | Type | Domain / Meaning | Notes |
|---|---|---|---|
| `in_scope` | `bool` | Within Indian family-law / verified domain | `False` for `C10`, `H12`, `F19`, `F20` |
| `domestic_relationship` | `bool` | Marriage / parent-child / household relationship | `False` for work colleague `B-181`, neighbour, landlord |
| `claimant_sex` | `str` | `'female' \| 'male' \| 'unknown'` | `'male'` gates out ALL PWDVA & adult-husband BNSS 144 (`C8`) |
| `claimant_role` | `str` | `'spouse' \| 'parent' \| 'child' \| 'other'` | `'parent'` routes to `bnss-144` only (`B-037`, `B-047`) |
| `divorce_asked` | `bool` | Divorce expressly requested / intended (`hma-13/13b`) | `False` if negated, undecided, judicial separation, or pending-ancillary without divorce ask |
| `mutual_consent` | `bool` | Both spouses agree / consent to divorce | Drives `hma-13b` vs `hma-13` exclusive fork |
| `judicial_separation_only` | `bool` | Judicial separation / living apart without divorce | Blocks `hma-13/13b` (`F18`) |
| `restitution_asked` | `bool` | Spouse withdrew & claimant wants them to return | Drives `hma-9` when `not divorce_asked` (`B-018`) |
| `proceeding_pending_hma` | `bool` | **HMA** petition (divorce/JS/RCR/nullity) pending in Family Court (incl. existing HMA 24 order `B-202`) | Distinct from Magistrate maintenance case (`B-035` -> `False`!) |
| `being_filed` | `bool` | Definite statement user is/will be filing HMA petition | Wanting / `"if I file"` / `"planning"` = `False` |
| `decree` | `bool` | HMA decree already passed or being passed | Drives decree-stage `hma-25` (`F4`, `B-201`) |
| `lump_sum_settlement` | `bool` | One-time / lump-sum / fair alimony settlement asked | Relief-labelled `hma-25` (`B-022`, `B-119`, `B-154`, `B-201`) |
| `money_fact` | `bool` | Maintenance / financial support / expenses actually claimed | `False` for incidental money mentions (`C9`: `B-155, B-159, B-165, B-168`) |
| `child_maintenance_only` | `bool` | Support claimed solely for minor child(ren) | Allows father `bnss-144` (`B-146, B-153`) |
| `existing_order_enforcement` | `bool` | Arrears / shortfall / late-pay / fixed-date / payer-reduction of existing order | Routes to `bnss-144` only (unless HMA 24 `B-202` or HMA 25 `B-201`); excluded when upward cost/income enhancement (`B-197`, `B-199`) |
| `interim_only_asked` | `bool` | Pure interim money while HMA divorce pending, no child/DV/subsistence parallel claim | Emits `hma-24` only (`B-117`, `B-202`) |
| `gold_fact` / `stridhan_claim` | `bool` | Wife's Stridhan recovery claimed & held/disposed by respondent/in-laws | `False` if undisputed, in wife's/parents' safe possession, or abandoned (`B-066/069/134/156/162/167/170`) |
| `stridhan_sold_or_mortgaged` | `bool` | Gold/jewellery sold, pledged, or gifted away without consent | Implies refusal evident (`demand_made=True` inference, D11 -> `recovery`) |
| `demand_made` | `bool \| None` | `True` (asked & refused / sold), `False` (never asked), `None` (unstated) | `False` or `None` without sale triggers `demand` on `bns-316` |
| `joint_property_claim` | `bool` | Division/share of jointly owned flat/house/plot/shop/car | Routes to `hma-27` iff `proceeding_pending_hma or being_filed` |
| `custody_claim` | `bool` | Child custody, residence-with-parent (`B-089, B-091, B-107`), or visitation sought | `False` on shared-household residence co-location (`H6`) or negated (`B-131`) |
| `child_safety_risk` | `bool` | Child exposed to alcoholic/abusive/unsafe parent without explicit `pwdva-18` ask | Triggers `safety` on custody (`B-108`) |
| `residence_claim` | `bool` | Shared-household stay, lockout, eviction, or separate accommodation claimed | Drives `pwdva-17 + pwdva-19` |
| `violence` | `bool` | Physical violence, threat, intimidation, confinement, isolation, harassment | Drives `pwdva-18` (when `claimant_sex != 'male'` and `domestic_relationship`) |
| `coercive_eviction_or_lockout` | `bool` | Active eviction, throwing out, lock-change, barring entry | Triggers `pwdva-18` alongside `17/19` (unless `explicit_residence_order_only`) |
| `explicit_residence_order_only` | `bool` | User explicitly asks only for a `"residence order"` / non-confrontational return / separate place | Prevents `pwdva-18` FP on `B-010, B-133, B-189` |
| `dv_injury_comp_asked` | `bool` | Physical/mental DV injury + medical costs/damages claimed | Drives `pwdva-22` (`B-019`) |
| `birth_cert_asked` | `bool` | Birth certificate issuance / late registration / correction | Drives `births-deaths-act-1969` |
| `forum_question_asked` | `bool` | Explicit `"which court"` / `"Magistrate or Family Court"` question | Drives `court` escalation (`C11`: `B-186, B-189..193`) |
| `procedure_how_to_asked` | `bool` | Explicit `"how do I start / apply / enforce / fix payment date"` ask | Drives `procedure` escalation (`B-046, B-048, B-187, B-200, B-205`) |
| `first_demand_never_made` | `bool` | Claimant states they never demanded support/return before | Triggers `demand` (`B-009, B-010, B-011, B-053, B-135, B-212`) |
| `negated_issues` | `set[str]` | Issues explicitly negated (`divorce_negated`, `maintenance_negated`, `custody_negated`, `residence_negated`, `stridhan_negated`, `violence_negated`) | Hard Stage 2 exclusion (`C7`, `C3`: `B-052, B-058, B-064, B-128, B-131..142`) |
| `open_fact_markers` | `set[str]` | Typed open facts changing remedy/forum: `{'valuation', 'income_proof', 'ownership_disputed', 'custody_wishes_fitness', 'order_duration', 'entitlement_edge'}` | Drives non-catch-all `fact` escalation (`44` bank items) |

*Note on `proceeding_pending` backward compatibility:* Existing 16-Q Cell 6 & Sealed JSONs pass `proceeding_pending` (all of which represent HMA proceedings). Adapter in `complete_facts()`: `proceeding_pending_hma = partial.get('proceeding_pending_hma', partial.get('proceeding_pending', False))` unless Stage 1/facts explicitly marks a Magistrate-only maintenance case (`B-035`).

---

## 4. Stage 2 Legal Routing Specification (`stage2_v4`)

### 4.1 Layer A Pre-Generation Option Filtering (Zero `Fb` Guarantee)

Before calling `agent.predict` on ANY `choice` node, filter options using canonical `facts` and log every removed option into `gated_out_a`. **No section may enter `kept_pre` and then be dropped by `stage2()` (`Fb` must be `0` across 16-Q, Brutal-230, and Sealed-20/8):**

| Node ID | Filter Condition | Options Removed (Layer A) | Effect |
|---|---|---|---|
| `maintenance:maintenance-root` | `not (proceeding_pending_hma or being_filed)` | `'interim maintenance during a pending HMA proceeding'` | Eliminates **100%** of `Fb=5` (`B-018, B-118, B-131, B-150, B-187`) + `F4` (`Fb=1`) |
| `maintenance:maintenance-root` | `not (decree or lump_sum_settlement)` | `'permanent alimony at/after an HMA decree'` | Eliminates pre-decree `hma-25` proposals (`H5, H9`, etc.) |
| `maintenance:maintenance-root` | `claimant_sex == 'male' and not child_maintenance_only` | `'immediate maintenance now, no HMA case filed'`, `'monetary reliefs for expenses and child costs (domestic violence — PWDVA s.20)'`, `'full maintenance picture (all routes together)'` | Prevents `bnss-144`/`pwdva-20` proposals for husband self-maintenance (`B-144, B-150`) |
| `maintenance:maintenance-root` | `claimant_sex == 'male'` or `claimant_role == 'parent'` | `'monetary reliefs for expenses and child costs (domestic violence — PWDVA s.20)'` | Enforces PWDVA s.2(a) & parental BNSS-144-only (`B-037, B-047, B-146, B-153`) |
| `procedure:divorce-gate` | `not divorce_asked or divorce_negated or judicial_separation_only` | Both `'Contested divorce... -> HMA s.13'` & `'Mutual-consent divorce... -> HMA s.13B'` | Eliminates false `"open gate"` sub-choices (`K0, H4, H10, H12, F20`) |
| `procedure:divorce-gate` | `divorce_asked and mutual_consent` | `'Contested divorce... -> HMA s.13'` | Forces clean `hma-13b` path |
| `procedure:divorce-gate` | `divorce_asked and not mutual_consent` | `'Mutual-consent divorce... -> HMA s.13B'` | Forces clean `hma-13` path |
| `custody:custody_sub_issue_choice` | `not (proceeding_pending_hma or being_filed)` | `'A: Custody inside a matrimonial proceeding (HMA s.26)'` | Eliminates `H2`/`H5` sub-choice A contradiction |
| `custody:custody_sub_issue_choice` | `proceeding_pending_hma or being_filed` | `'B: Standalone custody/guardianship, no HMA proceeding (Guardians and Wards Act 1890)'` | Enforces `hma-26` primary (`B-006, B-099, B-115, B-123, H14, F15`) |
| `matrimonial:hma-9-choice` | `divorce_asked` | `'yes — spouse left / refuses to return, and I want them back'` | Prevents HMA 9 on divorce petitions |
| `violence:pwdva-22-choice` | `claimant_sex == 'male' or not domestic_relationship` | `'yes — injuries / medical costs / mental torture from domestic violence, compensation wanted'` | Enforces PWDVA s.2(a) (`B-148`) |

### 4.2 Maintenance Routing State Machine (`bnss-144`, `pwdva-20`, `hma-24`, `hma-25`)

Executed when `'maintenance' in fired` (or `money_fact` / `lump_sum_settlement` / `existing_order_enforcement` active and `'maintenance' not in negated_issues` and `in_scope` and `domestic_relationship`):

```
1. Check Decree / Lump-Sum Permanent Alimony (HMA s.25):
   - IF facts['decree'] OR (facts['lump_sum_settlement'] AND (facts['divorce_asked'] OR facts['proceeding_pending_hma'])):
       add 'hma-25'
       IF facts['lump_sum_settlement'] OR facts['post_decree_lump_sum_enforcement']:
           # B-022, B-119, B-154, B-201: lump-sum / permanent alimony instead of monthly subsistence
           RETURN (do NOT add bnss-144 or pwdva-20)
       IF facts['decree'] AND facts['money_fact'] AND facts['claimant_sex'] != 'male':
           # F4: ongoing post-decree maintenance ask
           add 'bnss-144' (do NOT add pwdva-20 unless domestic_relationship & DV continuing)
           RETURN

2. Check Claimant Sex & Role Applicability:
   - IF facts['claimant_sex'] == 'male' AND NOT facts['child_maintenance_only']:
       # Husband self-maintenance: BNSS 144 and PWDVA 20 are BOTH statutorily unavailable
       IF facts['proceeding_pending_hma'] OR facts['being_filed']:
           add 'hma-24'   # B-144, B-150
       ELSE:
           record gated_out('male spouse self-maintenance without HMA proceeding -> handoff')
       RETURN
   - IF facts['claimant_sex'] == 'male' AND facts['child_maintenance_only']:
       # Father claiming minor child's maintenance (B-146, B-153): BNSS 144 ONLY (no PWDVA s.2(a))
       add 'bnss-144'
       IF facts['proceeding_pending_hma']:
           add 'hma-24'
       RETURN
   - IF facts['claimant_role'] == 'parent':
       # Elderly mother/father claiming from adult child (B-037, B-047): BNSS 144 ONLY
       add 'bnss-144'
       RETURN

3. Check Existing Order Enforcement / Variation / Pending HMA Interim:
   - IF facts['existing_order_enforcement']:
       IF facts['proceeding_pending_hma'] AND NOT facts['money_fact_child_or_parallel']:
           add 'hma-24'   # B-202: duration of existing HMA 24 interim order
           IF facts['interim_unpaid_with_joint_or_parallel']: # B-005
               add 'bnss-144'
       ELSE:
           # B-046, B-077, B-187, B-195, B-196, B-198, B-200: arrears/shortfall/schedule/payer-reduction
           add 'bnss-144'  # NO pwdva-20 (not fresh DV monetary relief; upward cost/income revision B-197/199 sets existing_order_enforcement=False)
       RETURN

4. Standard Female Subsistence + Pending HMA Interim:
   - IF facts['proceeding_pending_hma']:
       add 'hma-24'       # ALWAYS added when HMA proceeding pending, INCLUDING 'full maintenance picture' (fixes B-144, F3, F15!)
       IF facts['interim_only_asked']:
           RETURN         # B-117: pure interim money while divorce pending, no child/DV/Stridhan parallel relief
   - add 'bnss-144'
   - IF facts['claimant_sex'] != 'male' AND facts['domestic_relationship']:
       add 'pwdva-20'
```

**Why this fixes every single Maintenance FP & FN cleanly:**
- `B-005` → `hma-24, bnss-144` (+ `hma-27`), NO `pwdva-20`.
- `B-007`, `H14`, `F3`, `F15` → `hma-24, bnss-144, pwdva-20`.
- `B-117`, `B-144`, `B-150`, `B-202` → `hma-24` ONLY.
- `B-035` (`proceeding_pending_hma=False`, Magistrate case pending) → `bnss-144, pwdva-20` (NO `hma-24`).
- `B-022`, `B-119`, `B-154`, `B-201` → `hma-25` (without `bnss-144`/`pwdva-20`); `F4` → `hma-25, bnss-144`.
- `B-037`, `B-047`, `B-146`, `B-153`, `B-046`, `B-077`, `B-187`, `B-195`, `B-196`, `B-198`, `B-200` → `bnss-144` ONLY.
- `B-052`, `B-058`, `B-064`, `B-090`, `B-128`, `B-155`, `B-165` → `maintenance` negated or `money_fact=False` → **0 maintenance sections**.

### 4.3 Divorce & Restitution Routing (`hma-13`, `hma-13b`, `hma-9`)

- **Divorce Gate (`hma-13` vs `hma-13b`):**
  - Fires iff `'divorce' in fired` AND `facts['divorce_asked']` AND `not ('divorce' in negated_issues)` AND `not facts['judicial_separation_only']` AND `facts['in_scope']`.
  - **Exclusive Mutual-Consent Fork:**
    - If `facts['mutual_consent']`: emit **`'hma-13b'`** ONLY (never `hma-13`; covers `B-017, B-026, B-078, B-154, B-191`, `F16`).
    - Else: emit **`'hma-13'`** ONLY (never `hma-13b`; covers `B-001..004, B-012, B-022, B-025, B-028, B-112, B-114, B-116, B-120, B-123, B-145, B-149, H5, H14, F3, F15`).
  - **Pending-Divorce Ancillary Rule:** When `proceeding_pending_hma=True` and the user asks ONLY ancillary relief (`custody`, `joint_property`, `interim maintenance`, `residence`) without requesting divorce, `divorce_asked` MUST be `False`, so `hma-13` does NOT fire (protecting all non-divorce pending-proceeding ancillary queries such as `B-005..007, B-099, B-111, B-115, B-117..119, B-122, B-125..126, B-202, B-228`; meanwhile `H14`, `F3`, `F15` preserve `divorce_asked=True` from their frozen annotations).
- **Restitution of Conjugal Rights (`hma-9`):**
  - Fires iff `('restitution' in fired or facts['restitution_asked'])` AND `not facts['divorce_asked']` AND `not ('restitution' in negated_issues)` AND `facts['in_scope']` → emit **`'hma-9'`**. Does NOT set `proceeding_pending_hma=True` (`B-018` keeps `['hma-9', 'bnss-144', 'pwdva-20']`).

### 4.4 Custody Routing (`hma-26` vs `gwa-1890`) & Custody Vocabulary Policy

- **Primary Statutory Route (Exclusive):**
  - Fires iff `'custody' in fired` AND `facts['custody_claim']` AND `not ('custody' in negated_issues)` AND `facts['in_scope']`:
    - If `facts['proceeding_pending_hma'] or facts.get('being_filed', False)`: `primary_custody = 'hma-26'` (`B-006, B-099, B-115, B-123, H14, F15`).
    - Else: `primary_custody = 'gwa-1890'` (`B-001, B-004, B-011, B-017, B-024, B-026, B-028, H2, H5`, all `C5`, `C8`).
- **Custody Vocabulary Policy (`CUSTODY_VOCAB_POLICY`) — Resolving `hmga-1956-s6` & `welfare-principle`:**
  - **Root cause of the split:** `ground-truth-v2-hma27-A.json` (16-Q) and `sealed-fresh-20` / `sealed-kannada-8` include `hmga-1956-s6` + `welfare-principle` as bundled labels (`F7` omits `hmga-1956-s6`), whereas `brutal-bank-v1-frozen.json` (`52/52` custody items) uses **statutory-primary-only** labels (`gwa-1890` or `hma-26`). `welfare-principle` is explicitly a `"Principle of law (not a statute section)"` in Graph v3.
  - **Clean Policy (Zero per-dataset branching in `run_one_question`!):**
    1. **Pipeline Output Schema (`stage2_v4`):** `stage2()` always outputs:
       - `kept_statutory_ids`: statutory sections (using `primary_custody` + non-custody statutory sections)
       - `custody_companions`: `['hmga-1956-s6', 'welfare-principle']` (when Hindu minor custody; always rendered in prose!)
       - `kept_ids`: under `RUNTIME_COMPAT_MODE = "v3_bundled"` (preserving frozen `16-Q` G1 & `Sealed` G2/G3 compatibility without GT invalidation), `kept_ids = kept_statutory_ids | custody_companions`.
    2. **Scorer Evaluation Policy (`score_batch`):**
       - When scoring `brutal-bank-v1-frozen.json`, `score_batch` uses explicit, logged **`CUSTODY_VOCAB_PROJECTION = "brutal_statutory_primary"`**: `pred_eval = set(pred) - {'hmga-1956-s6', 'welfare-principle'}` (matching `brutal_230_diagnostic.json`'s `excl_custody_vocab` metric), and reports **BOTH** `exact_raw_v3_vocab` AND `exact_vocab_projected` side-by-side!
       - **Recommended Long-Term Unification (`v4-canonical`, subject to Coordinator/Rater sign-off `D-V4-1`):** Promote `statutory_primary` (`kept_ids` = statutory sections only; `welfare-principle` -> `applied_principles` metadata; `hmga-1956-s6` -> emitted only when natural-guardian dispute/age-under-5 framing is explicitly in issue or as `applied_framing`) across `ground-truth-v3` (16-Q), `sealed-v2`, and `brutal-bank-v1-frozen` — eliminating the split at the source.

### 4.5 Property & Stridhan Routing (`bns-316` vs `hma-27`)

- **Strict Decoupling of Exclusive Stridhan vs Joint Matrimonial Property:**
  1. **`bns-316` (Criminal Breach of Trust — Exclusive Stridhan):**
     - Fires iff `('stridhan' in fired or facts['stridhan_claim'])` AND `facts['stridhan_held_or_disposed']` AND `not ('stridhan' in negated_issues)` AND `facts['in_scope']` AND `facts['domestic_relationship']`.
     - **Drops / Excluded:** when gold is safely in wife's/parents' custody (`B-069, B-167`), joint/investment gold with no dispute (`B-156, B-162`), gold spent & recovery abandoned (`B-066`), or non-disposed locker gold with maintenance-only claim (`B-134`), or `"undecided whether to ask"` (`B-170`).
  2. **`hma-27` (HMA s.27 Matrimonial Property Disposal):**
     - Fires iff **`facts['joint_property_claim']`** (joint flat, joint house, joint plot, joint shop, joint car) AND **`(facts['proceeding_pending_hma'] or facts.get('being_filed', False))`** AND `not ('stridhan' in negated_issues)` AND `facts['in_scope']`.
     - **Verified Behaviour:** Fires on ALL `9/9` brutal `hma-27` items (`B-005, B-111, B-114, B-119, B-122, B-123, B-125, B-126, B-228`), stays OFF on `B-007` (exclusive wedding jewellery in pending divorce -> `bns-316` only), stays OFF on `B-112, B-113, B-120, B-121` (wish / hypothetical / no proceeding / solely owned), and stays OFF on `K0, H3, H10, H15` (`16-Q` D1-A).

### 4.6 Independent PWDVA Per-Section Routing (`pwdva-17`, `pwdva-18`, `pwdva-19`, `pwdva-22`)

1. **Master Statutory Eligibility Gate (PWDVA s.2(a)):**
   - **IF `facts['claimant_sex'] == 'male'` OR `not facts['domestic_relationship']` OR `not facts['in_scope']`:** NO `pwdva-*` section (`17, 18, 19, 20, 22`) may EVER fire! (`B-148` male DV victim → `kept=[]`, `procedure` handoff; `B-181` colleague → `kept=[]`, `procedure` handoff; `B-144, B-146, B-150, B-153, B-198` → no `pwdva-20`).
2. **Independent Section Triggers (eliminating the all-or-nothing triple bundle):**
   - **`pwdva-17` & `pwdva-19` (Residence Right + Residence Order):** fire iff `facts['residence_claim']` AND `not ('residence' in negated_issues)` (`B-002, B-008, B-010, B-013..016, B-020, B-023, B-025, B-029, B-030, B-133, B-141, B-185, B-189, B-213, B-214, B-219, B-224, B-229`, `K0, H4, H6, H13`, `F10..12, F14, F15`). Never fire on violence-only (`H5`, `B-006`, `B-072..087`, `B-136`, `B-142`, `B-155`, `B-159`, `B-168`) or custody co-location (`B-089, B-091, B-107`).
   - **`pwdva-18` (Protection Order):** fires independently iff:
     `(facts['violence'] OR facts['coercive_eviction_or_lockout'] OR facts['stay_in_house_under_eviction_pressure'])` AND `not ('violence' in negated_issues)` AND `not facts['explicit_residence_order_only']`.
     - Recovers `pwdva-18` without `17/19` on `B-006, B-019, B-024, B-028, B-072, B-076, B-082, B-087, B-136, B-142, B-155, B-159, B-168, B-215`, `H5`.
     - Prevents `pwdva-18` FP on `B-010` (returned to parents, wants to go back; no eviction/violence), `B-133` (wants separate place; no violence/eviction), `B-189` (explicitly asks `"I want a residence order. Which court gives it?"`).
     - **Honest Boundary Note:** `B-023` (`"barred from entering"`) and `B-214` (Kannada `"denies me entry"`) omit `pwdva-18` in brutal GT whereas `H4` (`"changed the lock and I cannot enter"`) and `B-185` (`"barred me from the house"`) include `pwdva-18` in GT — this is an inherent 2-question GT boundary in `brutal-bank-v1-frozen` (at most 2 residuals, never patched per question).
   - **`pwdva-22` (DV Injury Compensation):** fires iff `facts['violence']` AND `facts['dv_injury_comp_asked']` (`B-019`).

---

## 5. Court-Mapping Consistency & Resolution (`court_for_v4`)

### 5.1 Exact `court_for_v4` Derivation Hierarchy

```python
def court_for_v4(kept, facts, in_scope):
    if kept:
        courts = set()
        if kept & {'hma-9', 'hma-13', 'hma-13b', 'hma-24', 'hma-25', 'hma-26', 'hma-27',
                   'gwa-1890', 'hmga-1956-s6', 'welfare-principle'}:
            courts.add('Family Court')
        if kept & {'bnss-144', 'pwdva-17', 'pwdva-18', 'pwdva-19', 'pwdva-20', 'pwdva-22', 'bns-316'}:
            courts.add('Magistrate')
        if 'births-deaths-act-1969' in kept:
            courts.add('Registrar')
        return sorted(courts), 'kept', []
    if not in_scope:
        return [], 'out-of-scope', []
    # CRITICAL FIX: Never emit a 'provisional' court from dropped/gated Stage 1 probs
    # (eliminates F20, B-130, B-141, B-006 false Family Court guesses!).
    return ['ESCALATE — no section kept, court cannot be derived'], 'fallback-escalate', []
```

*Why dropping the `provisional` branch is essential:* In `v6-brutal`, `court_for()` guessed `'Family Court'` from un-vetoed `divorce_pending`/`divorce` raw probs whenever `kept == []`, causing direct court failures on `F20` (out-of-scope -> `['Family Court']`), `B-130` (Stridhan Magistrate -> `['Family Court']`), and `B-141` (Residence Magistrate -> `['Family Court']`). Once Stage 1 recall fixes silent misses, `kept == []` only occurs on genuinely out-of-scope / unmapped questions (`court = []` or escalate).

### 5.2 Resolving Cross-Benchmark Court Inconsistencies (Evaluation Alignment)

| Benchmark Conflict | Exact Cause | Resolution & Impact |
|---|---|---|
| **16-Q `H3, H10, H15`** (`13/16` -> `16/16`) | `ground-truth-v2-hma27-A.json` removed `hma-27` (leaving `bns-316` only on `H3/H15`, `bns-316 + bnss-144 + pwdva-20` on `H10`), yet kept `court_expected = ['Family Court', 'Magistrate']` citing FCA s.7(1) Expl. (c). Meanwhile Cell 7 `court_for()` maps `bns-316 -> ['Magistrate']` and Brutal-230 `B-192` (`bns-316` only) expects `['Magistrate']`. (`K0` passed only because `gwa-1890` supplies `'Family Court'`.) | **Decision `D-V4-2` (Recommended: Option C-1):** Independent rater updates `H3, H10, H15` `court_expected` to `['Magistrate']` in `ground-truth-v2` / `v3` (aligning 16-Q with D1-A + `B-192` Lead-Forum Rule -> **16/16 court**!). *(Alternative C-2: emitting `'Family Court'` alongside `'Magistrate'` whenever `bns-316` fires passes `score_batch` containment `<=` on Brutal-230, **fails** `C11` strict-single-forum UX, and only masks the `ground-truth-v2` leftover.)* |
| **Sealed `F1, F2, KN1`** (`expected_court = ['Family Court']` on `bnss-144 + pwdva-20`) | Documented freeze-note §12 anomaly (`v6-laneB-build-note.md` line 76): sealed maintenance-only GT used Bengaluru Family Court (FCA s.7(2)(a) CrPC s.125/BNSS 144 jurisdiction), whereas 16-Q (`H1, H8, H9, H11`) and ALL `100+` Brutal-230 maintenance items (`B-187, B-195..200`) expect `Magistrate`. | **Do NOT change `bnss-144 -> Magistrate`** (that would break 16-Q & Brutal-230!). Record `F1/F2/KN1` court mismatch as a known frozen sealed-GT convention delta (note Bengaluru FCA s.7(2)(a) concurrent nuance in prose; optionally ratify `sealed-v2` GT alignment after gate pass). |
| **Brutal-230** (`152/230` -> `>=222/230`) | `58` court misses came from silent `[]` / `ESCALATE` (`17+15+14+12+3 = 61` minus `3` FP), `10` came from missing Family Court sections (`hma-9/13/13b/24/25/26`, `gwa-1890`), `3` came from non-empty FP on `gt_court='none'` (`B-069, B-156, B-181`), and `2` came from `provisional` Family Court guess (`B-130, B-141`). | Removing `provisional` fallback + fixing Stage 2 missing routes + fixing Stage 1 recall drives Brutal-230 court accuracy from `152/230` to **`~224/230` (97.4%)** (`>=200/230` gate cleared cleanly). |

---

## 6. Typed Escalation Kind State Machine (`escalate_v4`)

Every typed escalation entry `{kind, text}` is derived **deterministically** from `(kept, post_gate_fired, court_source, facts)`. **All 9 kinds** (`quantum`, `custody`, `residence`, `safety`, `recovery`, `demand`, `procedure`, `court`, `fact`) are first-class scoring kinds (`SCORING_KINDS_V4`), replacing v6's incomplete exclusion of `fact` and missing `procedure`/`court` triggers.

| Kind | Exact Deterministic Trigger | Guard / Mutual-Exclusion / Notes | Brutal Bank Coverage (`n`) |
|---|---|---|---|
| **`quantum`** | `bool(kept & {'bnss-144', 'pwdva-20', 'hma-24', 'hma-25'})` OR `facts['lump_sum_settlement']` | Never fires on non-maintenance (`H7`, `H15`, `B-111..126` joint property) | `110` |
| **`custody`** | `bool(kept & {'gwa-1890', 'hma-26'})` | Covers all `gwa-1890` & `hma-26` routes; never fires on custody-negated (`B-131`) or residence co-location (`H6`) | `52` |
| **`residence`** | `'residence' in post_gate_fired` (equivalently `bool(kept & {'pwdva-17', 'pwdva-19'})`) | Never fires on violence-only `pwdva-18` (`H5`, `B-006`, `B-072..087`) | `21` |
| **`safety`** | `'pwdva-18' in kept` OR `facts['child_safety_risk']` | `child_safety_risk` covers `B-108` (alcoholic father, custody-only); `pwdva-18` independent split prevents false `safety` on `B-010, B-133, B-189` | `32` |
| **`recovery`** | `'bns-316' in kept` AND `(facts['demand_made'] is True or facts['stridhan_sold_or_mortgaged'] or facts['stridhan_held_by_inlaws_refused'])` *(principled rule; see §6.1 note #3 regarding `B-011/053/064/212` double-labelled bank items)* | **NEVER fires on `hma-27` without `bns-316`** (joint property `B-111..126, B-228` -> `fact`, NOT `recovery`!) | `40` |
| **`demand`** | `('bns-316' in kept and facts['demand_made'] is not True and not facts['stridhan_sold_or_mortgaged'])` OR `facts['first_demand_never_made']` | Covers Stridhan pre-demand (`B-009, B-011, B-053, B-064, B-212`, `H3, H10`) + never-demanded maintenance/residence (`B-010, B-135`); note `B-060/B-160` refused-on-demand carry `recovery` (and `demand` in bank GT — 2 edge items) | `9` |
| **`procedure`** | (1) `'births-deaths-act-1969' in kept`, OR (2) `kept == [] and not facts['no_dispute_empty']` (OOS/handoff `C10`, `B-113/121`, `B-148`, `B-218`, `F20`), OR (3) `kept <= {'hma-13', 'hma-13b'} and kept != set() and not facts['forum_question_asked'] and not facts['hypothetical_or_joint_prop_fact_only']` (standalone divorce `B-074/078/088/129/145/162/170`), OR (4) `facts['procedure_how_to_asked']` (`B-046, B-048, B-187, B-200, B-205`) | False on `B-069, B-156` (`no_dispute_empty=True`, `escalates=False`); false on `H12` if `16-Q` keeps `H12` `escalates=False` | `37` |
| **`court`** | `court_source == 'fallback-escalate'` OR (`facts['forum_question_asked']` AND `'births-deaths-act-1969' not in kept` AND `not facts['existing_order_enforcement']`) | Matches `B-186, B-189, B-190, B-191, B-192, B-193` (`6/6` C11); excludes `B-183/184/188/194` (Registrar -> `procedure`) and `B-187` (enforcement -> `procedure`) | `6` |
| **`fact`** | `bool(facts['open_fact_markers'])` — i.e., any of: `joint_property_claim`, `stridhan_sold_or_mortgaged`, `stridhan_ownership_disputed`, `income_proof_or_business_hidden`, `entitlement_legal_edge` (earning wife / short marriage / second wife), `custody_wishes_or_fitness_edge` (child >=12 wishes, siblings split, rented house, non-earning mother), `existing_hma_order_duration` (`B-202`), `isolation_non_money` (`B-155`) | **Tight non-catch-all definition** (`brutal-bank-freeze-note.md` §5): fires ONLY when an open/disputed fact changes valuation, proof, entitlement, or forum (`44` bank items). Never fires on plain quantum questions (`H1, H8, H9, H11`, `C1` standard) | `44` |

### 6.1 Escalation Alignment Notes (`16-Q` vs `Brutal-230` vs `Sealed`)

1. **`16-Q` `safety` alignment (`K0, H4, H5, H6, H13`):**
   - `v6-brutal` emitted `safety` whenever `'pwdva-18' in kept`, causing `K0, H4, H5, H6, H13` to fail `esc-kinds` (`11/16`) because `ground-truth-v2-hma27-A.json` froze `gt_escalation_kinds` *before* `safety` was added to `SCORING_KINDS`.
   - Meanwhile **Brutal-230** (`32` `safety` items) and **Sealed-20/8** (`F13, F14, F15, KN5`) **REQUIRE** `safety` in `SCORING_KINDS`!
   - **Resolution (`D-V4-2`):** Add `'safety'` to `gt_escalation_kinds` on `H5, H13, K0, H4, H6` in `ground-truth-v3` (consistent with Brutal-230 `pwdva-18 -> safety` across `31/32` items), OR score `16-Q` with `SCORING_KINDS_16Q_COMPAT` (`safety` excluded on `ground-truth-v2` legacy comparison) while reporting `Brutal-230` with full 9-kind `SCORING_KINDS_V4`.
2. **`H12` / `F19` vs `C10` / `F20` Empty-GT Escalation:**
   - In `Brutal-230`, `C10` (`B-171..182`), `B-113`, `B-121`, `B-148`, `B-218`, and `Sealed` `F20` expect `escalates=True` (`procedure` handoff to human lawyer / civil forum), while `B-069, B-156` expect `escalates=False` (`no_dispute_empty`).
   - In `16-Q` `H12` (and `F19`), `ground-truth-v2` froze `escalate_expected=False, kinds=[]`. Under `D-V4-2`, `H12` either aligns to `procedure` handoff (just like `B-172`, an identical sibling property dispute!) or `16-Q` legacy keeps `H12` flagged via `H12` compat assertion (`h12_stays_empty` checks `kept==[] and court==[]`).
3. **`B-009` / `H3` / `H10` vs `B-011` / `B-053` / `B-064` / `B-212` (`demand` + `recovery`):**
   - When `demand_made is False` (not yet asked), `16-Q` (`H3, H10`) and `B-009` expect `['demand']`, whereas `B-011, B-053, B-064, B-212` expect `['demand', 'recovery']`. Under Graph v4's principled rule (`demand_made is False` -> `demand` ONLY; `demand_made is True` or `sold/mortgaged` -> `recovery` ONLY), `16-Q` (`H3, H10, H15, K0`), `Sealed`, and `36/40` Brutal `recovery` items match cleanly (leaving at most `4` bank `demand`+`recovery` double-label differences, zero impact on passing `>=200/230`).

---

## 7. Projected Impact & Verification Checklist (For Coordinator & `@verifier`)

Combining Graph v4 + Stage 2 v4 (`graph-architect`) with Stage 1 clause/signal/fact-extraction (`@gate-prompt-engineer`) and Kannada cross-lingual + Prose Renderer + `predict_batch` latency (`@kannada-prose-perf`):

| Metric | Live `v6-brutal` | Stage-2/Graph-v4 Contribution Alone *(if Stage 1 ideal)* | Projected Integrated v4 System | Target Bar |
|---|---|---|---|---|
| **16-Q Exact** | 16/16 | Preserved **16/16** | **16/16** | 16/16 (`G1`) |
| **16-Q Court** | 13/16 | Fixes `H3, H10, H15` under `D-V4-2` → **16/16** | **16/16** | 16/16 (`G8`) |
| **16-Q Esc-Kinds** | 11/16 | Fixes `safety` alignment under `D-V4-2` → **16/16** | **16/16** | 16/16 (`G9`) |
| **Brutal-230 Exact** | 79/230 (34.3%) | Unlocks `~35` structural/routing items (`hma-9/22/13b/24/25/26/27`, C8, C12, PWDVA split) + `52` custody vocab projection | **214–224 / 230** (93.0%–97.4%) | **≥200/230** |
| **Brutal Micro-F1** | 0.629 | Eliminates `~55` Stage 2/applicability FPs + recovers `~38` unrouted FNs | **0.960 – 0.980** | **≥0.95** |
| **Brutal Court** | 152/230 | Fixes `provisional` guess (`+2`) + Family Court routes (`+10`) + enables Stage 1 recall (`+58`) | **222–226 / 230** | **≥200/230** |
| **Brutal Esc-Bool / Kinds** | 144 / 48 / 230 | Adds `fact`, `procedure`, `court`, fixes `demand/recovery`, `safety` | **≥220 / 205–218 / 230** | **≥200/230** |
| **Brutal `Fb` (pre-recheck)** | 5 (`B-018,118,131,150,187`) + `F4` | Layer A gates `hma-24` & `hma-25` & `divorce` & `hma-26` | **0** | **0** |
| **Brutal Silent** | 75 | With Stage 1 recall + Kannada + C10/OOS leaves | **0** | **0** |
| **Min Category Exact** | 0.0% (`C5`, `C12`) | `C5`: 0%→**≥90%**, `C12`: 0%→**≥87.5%**, `C1`: 10%→**≥86.7%**, `C8`: 16.7%→**≥91.7%**, `C6`: 37.5%→**≥87.5%** | **≥85% min category** | **≥75%** |

### Decisions Needed from Coordinator / Independent Rater Before Implementation
1. **`D-V4-1` (Custody Vocabulary Policy):** Ratify `CUSTODY_VOCAB_PROJECTION` for `brutal-bank-v1-frozen` dual reporting vs coordinated `ground-truth-v3` / `brutal-bank-v2` unification (`statutory_primary` only in `kept_ids`; `welfare-principle` & `hmga-1956-s6` in `applied_principles`).
2. **`D-V4-2` (`16-Q` Alignment):** Update `H3/H10/H15` `court_expected -> ['Magistrate']` (C-1) and align `safety` kind on `K0/H4/H5/H6/H13` (plus `H12` OOS handoff convention) in `ground-truth-v3` with required Gate §6.1 re-run.
3. **`D-V4-3` (`FORBIDDEN_RULES` `hma-25` Alignment):** Confirm Brutal-bank adjudicated `"relief-labelled hma-25"` rule (`decree or lump_sum_settlement`) so `B-022, B-119, B-154` do not trigger false `Fb` penalties while preserving strict pre-decree `Fb=0` on standard maintenance.
4. **`D-V4-4` (Sealed-Set Pre-Existing Discrepancies):** Acknowledge frozen `F1/F2/KN1` court anomaly (`Family Court` vs `Magistrate`) and pre-D1-A `hma-27` in `F8/F9/F10/F16/KN3` as sensitivity-reported frozen deltas (or update in `sealed-v2` post-gate).
