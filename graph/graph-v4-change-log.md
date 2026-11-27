# Decision Graph v4 Change Log (`v3 -> v4`)

- **Date:** 2026-11-27
- **Generator:** [`src/build_graph_v4.py`](../src/build_graph_v4.py) (verified against untouched frozen `v3` LF SHA-256 `67bf2b04ca946f7c7fa3062068e01ce051fbce8f4d740c281afe6fff841c34a5`)
- **Output:** [`graph/laya-crpc-bns-section-decision-tree-v4.json`](laya-crpc-bns-section-decision-tree-v4.json)
- **Counts:** **`34` sections / `66` nodes / `99` edges** (`+0` sections, `+18` nodes, `+20` net edges vs `v3`'s `34/48/79`)
- **Validator:** [`tests/test_graph_v4.py`](../tests/test_graph_v4.py) (passes with `0` dangling edges, `0` unresolved `related_sections`, and all `7/7` frozen files untouched)

## 1. Structural & Schema Defects Fixed from v2/v3 (`DEF-1..DEF-8`)

1. **`DEF-1` (Edge `[67]`):** Added `stage1:escalate-clarify` (`leaf`, `section_set: []`) and repointed `stage1:confidence-gate -> stage1:escalate-clarify` (replacing non-existent `escalate_clarify`).
2. **`DEF-2` (Edge `[74]`):** Repointed `stage2:demand-gate -> stridhan:bns-316-leaf` (replacing raw section ID `bns-316`).
3. **`DEF-3` (Edge `[75]`):** Added `stage2:escalate-demand-first` (`leaf`, `section_set: ["bns-316"]`) and repointed `stage2:demand-gate -> stage2:escalate-demand-first` (replacing non-existent `escalate_demand_first`).
4. **`DEF-4` (`bnss-144` typo):** Fixed `related_sections[4]` `'hmga-6'` → `'hmga-1956-s6'`.
5. **`DEF-5` & `DEF-6` (`related_sections` canonicalization):** Normalized all string, `UPPER_SNAKE`, `section` display-label, and multi-section entries (including `hma-26`, `gwa-1890`, `hmga-1956-s6`, `welfare-principle`, `hma-27`, `bns-316`, `pwdva-17/18/19`, `hma-13/13b`, `proc-*`, `doc-*`) into `{"section_id": "<canonical-id>", "relationship": "..."}` where **100%** resolve in `SECTION_IDS`.
6. **`DEF-7` (`laya_question` schema):** Upgraded bare string `laya_question` fields on `hma-13`, `hma-13b`, and `births-deaths-act-1969` into structured `{"type": "choice", "question": ..., "options": [...]}` objects matching the rest of the graph.
7. **`DEF-8` (Domain applicability metadata):** Updated `bnss-144` exclusions (male spouse self-maintenance excluded; father child-only permitted), `pwdva-17/18/19/20/22` exclusions (`s.2(a)` woman-only domestic relationship), `hma-27` (`when_used` covering joint matrimonial property under pending/being-filed HMA), and `hma-25` (`decree` / lump-sum settlement).

## 2. New Routing Nodes (`+18`) & Edges (`+20` net)

- **Restitution & DV Compensation (`+2` nodes, `+2` net edges):** Replaced direct root-to-leaf shortcuts `[77]`/`[78]` with interactive choice nodes `matrimonial:hma-9-choice` (`B-018`) and `violence:pwdva-22-choice` (`B-019`).
- **Divorce Exclusive `13` vs `13B` Fork (`+2` nodes, `+2` edges):** Expanded `procedure:divorce-gate` to 4 options and added `stage2:hma-13-leaf` + `stage2:hma-13b-leaf`.
- **Joint Matrimonial Property `HMA 27` (`+3` nodes, `+3` edges):** Added `stridhan:joint-property-check` -> `stage2:hma-27-leaf` | `stage2:not-joint-property-leaf` gated on `proceeding_pending_hma | being_filed`.
- **Claimant Applicability & Post-Order Enforcement (`+4` nodes, `+8` net edges):** Interposed `maintenance:claimant-applicability-gate` on edge `[57]` and added `maintenance:post-order-enforcement`, `stage2:hma-24-only-leaf`, and `stage2:hma-25-settlement-leaf`.
- **PWDVA Per-Section Independence & Male DV Handoff (`+3` nodes, `+3` edges):** Added `stage2:pwdva-17-19-residence-leaf`, `stage2:pwdva-18-protection-leaf`, and `stage2:male-claimant-dv-handoff` under `stage2:pwdva-per-section-gate`.
- **Empty-GT Clarification (`+2` nodes, `+2` edges):** Added `stage2:out-of-scope-handoff` (civil/landlord/employer escalation) and `stage2:no-dispute-empty` (undisputed no-court leaf) under `stage1:confidence-gate`.
