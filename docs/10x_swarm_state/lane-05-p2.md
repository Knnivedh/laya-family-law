# Lane 05 — P2 unified runtime + Graph v4.1 + multi-turn provenance — STATUS

- Lane: 05 (V71-P2-1..V71-P2-4)
- Date: 2026-11-27
- Working copy: `~/workspace/laya-v71-work` (baseline bc7f40f + plan docs)
- Status: **DONE (code + local verification, evidence mode, CPU VM)** — neural-mode
  verification and the MT1–MT4 12/12 suite still need the RTX 5050 run (see §7).

## 1. Files built / changed (only my files — contract C4 honoured)

| File | Change |
|---|---|
| `src/laya_schema_v71.py` | NEW. `ProvenanceSource` 6-level literal, `PROVENANCE_PRECEDENCE`, `TurnRecord`, `SessionState` exactly per plan §2.2, `FactEvidence`/`IssueEvidence` re-exported from `laya_v7_schema` (one shared type identity, no parallel copy). Also `KNOWN_FACT_KEYS`, `FACT_KEY_TO_ISSUE`, `provenance_rank`, `canonical_provenance`, `new_session`. |
| `src/laya_graph_engine.py` | NEW. Declarative Graph v4.1 interpreter: `load_graph_v41`, `audit_reachability_single_root` (single root — stricter than `laya_v7_graph.audit_graph_reachability`, which seeds 4 entries), `validate_graph_v41`, `traverse_with_layer_a` (runs real `layer_a_filter_options` per choice node), `execute` (Layer A + Stage 2, genuine `candidates_before_gate` = all disposition keys, `gated_out_layer_a` + `gated_out_stage2` + union `gated_out`), `apply_vocab_profile` (3 profiles, legacy fold bnss-144-3/146 → bnss-144). |
| `src/laya_runtime.py` | NEW. `assess_turn(state, question, *, confirmations, vocab_profile="v4_legacy_18", ...)` → `(result, new_state)`; `assess_turns` (shared-state dialogue); `resolve_turn_state` (replaces `apply_confirmations_v7`, generic bi-directional override for every fact key); `stage2_facts` (Stage 2 facts-dict builder); `SUPERSEDING_TRANSITIONS` (MT1–MT3); guarded delegation to `extract_v7` / `evaluate_stage2_v7` / `render_prose` / `laya_family.assess` (all degrade, never crash, on a torch-less VM). |
| `src/laya_clarifier.py` | NEW. Targeted clarifying-question engine per **plan §2.3 V71-P2-4** (see §6 — Lane 04's spec did not exist). `rank_clarifications` / `clarifying_questions_for_turn`, max 2/turn, ranked by remedy-flip information gain (base priority + sections flipped; safety first; conflicting +5). `TAU_LOW=0.30`, `TAU_HIGH=0.70` gray band (calibration is Lane 10's job). |
| `src/build_graph_v4.py` | EXTENDED ONLY. Added `build_v41_graph()` + `--v41` / `--v41-only` flags. Default behaviour unchanged (plain run still builds v4 only). `build_v4_graph()` untouched. |
| `graph/laya-crpc-bns-section-decision-tree-v4.1.json` | NEW. Built by `python3 src/build_graph_v4.py --v41-only`. 36 sections / 68 nodes / 104 edges. LF SHA-256 `27b03d4ce1ebbf74b70c8a7c998bb66709070fd09a2cef197244620468f98958`. Frozen v2/v3 and graph v4.json untouched (v4 still 34/66/99; see guardrail results). |

## 2. Graph v4.1 — actually measured here

- Single-root BFS from `root:issue-classification`: **68/68 reachable, 0 unreachable**
  (v4 measured the same way: 61/66 — the 5 unreachable were `stage1:confidence-gate`,
  `stage1:conversation-context`, `stage1:kannada-mapping`, `stage1:escalate-clarify`,
  `stage2:no-dispute-empty`). Fix: 3 new root edges (to kannada-mapping,
  confidence-gate, conversation-context); the other two hang off confidence-gate.
- `validate_graph_v41`: **valid, 0 problems** — 0 dangling edges, 0 empty choice
  nodes, all `section_set` ids resolve, welfare-principle scoring metadata present,
  bnss-144-3 + bnss-146 sections and `stage2:bnss-144-3-leaf` /
  `stage2:bnss-146-leaf` nodes present under `maintenance:post-order-enforcement`
  (section_set now `[bnss-144, hma-24, hma-25, bnss-144-3, bnss-146]`).
- 4 empty choice nodes populated: `stage1:kannada-mapping`,
  `stage2:demand-gate`, `stage2:pwdva-per-section-gate`,
  `stage1:conversation-context`.
- `welfare-principle.laya_question`: type stays `"score"`; added `scoring_semantics`
  (A/B/C scale, 4 inputs, rule: the score NEVER creates a kept section by itself —
  welfare is a principle recorded in `applied_principles`, not a standalone remedy).
- New sections `bnss-144-3` (arrears recovery, one-year condition per amount due)
  and `bnss-146` (variation on change of circumstances), each with an explicit
  pre-BNSS guard: NEVER silently route on an unverified pre-1 Jul 2024 CrPC s.125
  order (BNSS s.531 savings).

## 3. Guardrail tests (run here, both PASS)

- `python3 tests/test_graph_v4.py` — PASS (34/66/99, 0 dangling, 7/7 frozen SHAs intact).
- `python3 tests/test_prose_renderer_v2.py` — PASS (246 cases, Fp=0, quality_flags=0, 15/15 mutants).
- `python3 -m py_compile` on all 5 touched/created `.py` files — PASS.

## 4. Runtime smoke tests (run here, evidence mode, CPU — all PASS)

Single turn (brutal_primary + v4_legacy_18): kept `bnss-144, pwdva-20, bns-316,
pwdva-17/18/19` on a lockout + maintenance + Stridhan question; `prose_fp_hits=[]`;
Layer A genuinely removed 5 options (e.g. `maintenance:maintenance-root ::
interim maintenance … [no_pending_or_being_filed_hma]`,
`procedure:divorce-gate :: Contested divorce … [divorce_not_asked]`);
`candidates_before_gate` = 6 disposition keys (genuine superset of kept_ids —
the `laya_v7.py:100,168` clone is fixed); `prose_forbidden_check` now receives
the real `gated_out`, never `[]`.

### MT1–MT4 coverage (smoke level, evidence mode — NOT the 12/12 suite)

- **MT4 accretion** — residence-only → +violence → +maintenance: T3 kept
  `[bnss-144, pwdva-20, pwdva-17, pwdva-19, pwdva-18]`; 0 dropped facts.
- **MT2 superseding** — divorce asked → mutual consent: `hma-13` → `hma-13b`,
  transition `MT2-divorce-mutual-consent` logged in `override_log`, `hma-13`
  not carried forward. Then `confirmations={"divorce_asked": False}` removes
  both (bi-directional override works for every fact key via `FACT_KEY_TO_ISSUE`).
- **MT3 superseding** — custody `gwa-1890` → proceeding starts
  (`proceeding_pending_hma=True` confirmation) → `hma-26`, transition
  `MT3-custody-route` logged, `gwa-1890` retired.
- **MT1 demand→recovery** — demand never made → `demand_made=True` confirmation:
  `bns-316` stays, `demand` escalation drops (`[recovery, demand]` → `[recovery]`),
  transition `MT1-demand-to-recovery` logged.
- **Conflicting flagging** — span-vs-span contradiction → status `conflicting` +
  disambiguation prompt enqueued; a span-less model denial does NOT flag and does
  NOT retract a prior verified span.
- **Clarifier** — `rank_clarifications` returns ≤ 2, safety first
  (`violence` gain 102.0 > `urgent_safety_risk` 100.0); already-confirmed /
  verified-span facts are never re-asked.
- **Vocab profiles** — `apply_vocab_profile` folding verified for all 3 profiles;
  unknown profile raises `ValueError`. Maintenance-profile smoke runs through
  the full pipeline (evidence-only shim) without crashing.

## 5. Two real bugs found and fixed during smoke testing

1. **`negated_issues` as FactEvidence → TypeError.** My first version stored the
   negated-issue set as a `FactEvidence` inside `active_facts`; Stage 2's
   `_normalize_legacy_facts` does `set(f["negated_issues"])` and crashed.
   Fix: `active_issues` (intent=`denied`) is the single source of truth;
   `stage2_facts()` re-attaches `negated_issues` / `open_fact_markers` as plain
   sets only in the dict handed to Stage 2.
2. **Closed-world extractor vs MT4 accretion (design finding, not a typo).**
   Verified: `extract_v7` (evidence mode) emits a COMPLETE per-turn assignment —
   every fact gets supported/denied, source `user_text`, confidence 1.0,
   `span=None` on every denial. A "denied" therefore means "not mentioned in
   THIS turn's text", not "explicitly denied". A naive provenance merge let
   turn 2 erase turn 1's residence claim. Fix in `resolve_turn_state`: supported
   facts are STICKY against later-turn absence-denials; a later supported fact
   overwrites a prior denied one (that IS accretion); `unknown` never overwrites;
   explicit retraction is only via `user_confirmation` (rank 1). Conflict is
   flagged only for span-vs-span contradictions. **Known limitation recorded:**
   until Stage 0/1 emits an explicit "explicitly-denied-in-text" signal
   (Lane 01 / P1-3), a prose retraction ("Actually I don't want a divorce")
   cannot retract without a confirmation. `kept_ids` are recomputed fresh from
   merged facts every turn — prior kept_ids are never unioned forward.

## 6. Notes / deviations

- **Lane 04 spec missing:** `docs/clarification-fallback-spec.md` did not exist
  when this lane ran, so `laya_clarifier.py` implements plan §2.3 V71-P2-4
  directly. Coordinator to reconcile if Lane 04's spec lands with a different
  interface; the seam functions are `rank_clarifications` /
  `clarifying_questions_for_turn`.
- **Honesty note (graph engine):** edge `condition` strings in the JSON are
  English prose, not executable predicates, so `execute` does NOT claim fully
  declarative legal execution — it traverses structurally, runs Layer A for
  real, and delegates disposition computation to `evaluate_stage2_v7`. What it
  guarantees is: the graph file is actually loaded/traversed, Layer A removals
  are recorded, and `candidates_before_gate` / `gated_out` are genuine (Fb
  measurable — Lane 10 contract C1).
- **Version-label collision:** `docs/v4-1-change-log.md` already uses "v4.1" for
  an evidence-first *notebook* variant. This graph file is a different artefact
  with the same label. Recorded in `build_v41_graph()` docstring and the graph's
  `graph_v41_note` field. A rename is a coordinator decision.
- **Concurrent lanes:** while working, sibling lanes' files appeared
  (`docs/10x_swarm_state/lane-07-p4.md`, `lane-08-p5.md`, `legal/`,
  `scripts/distill_student.py`, etc.) and `src/laya_family_evidence.py` /
  `tests/v7_backtest.py` show modifications — those are NOT mine; I touched
  only the files in §1.

## 7. What needs RTX / human (not verifiable on this VM)

- **MT1–MT4 12/12 turns + 4/4 final-turn suite** (plan §2.4) in neural mode
  (`mode="laya"` / `"auto"`, CUDA) on the RTX 5050 — the smoke tests above are
  evidence-mode only and do NOT count toward 12/12. Suggested run on the RTX
  machine (same assertions as §4, with `mode="laya", device="cuda"`):
  `python3 -c "import sys; sys.path.insert(0,'.'); from src.laya_runtime import assess_turns; ..."` —
  dialogue scripts are the four MT dialogues in §4 (MT4 lockout→violence→
  maintenance; MT2 divorce→mutual consent; MT3 custody→proceeding→decree;
  MT1 demand never made→made+refused).
- **16-Q / Brutal-230 parity through `assess_turn`** vs `assess_v7`
  (Lane 10 scorer reads `candidates_before_gate`; Fb should now be measurable
  and 0 on those sets — needs the RTX run to confirm, not assumed here).
- **Human:** the C4 wrapper refactor (§8) needs Lane 01 to apply; the
  `maintenance_sub_routes` field mapping for `recover`/`vary`/`new_support`
  needs a legal sanity check (see §8); the prose-retraction limitation in §5
  needs a Stage 0/1 explicit-denial signal decision.

## 8. C4 patch spec — refactor `laya_v7.py` / `laya_family.py` into thin wrappers (Lane 01 applies; NOT done here)

### 8.1 `src/laya_v7.py`

1. **`apply_confirmations_v7` (L33–49) → delegate.** Keep the signature
   `(extracted, confirmations) -> extracted`. New body: build a one-turn
   `SessionState` from `extracted["facts"]` / `extracted["issues"]`
   (`TurnRecord(turn_id=1, raw_text="", lang=..., script=...)`), call
   `laya_runtime.resolve_turn_state(state, turn, confirmations)`, and return
   the extracted dict rebuilt from `state.active_facts` / `state.active_issues`
   (plus `negated_issues` as a plain set derived from denied intents). Effect:
   the divorce-only special case becomes the generic bi-directional override
   for every fact key; no other behaviour change.
2. **`assess_v7` → delegate to `assess_turn`.** Replace the
   extract → confirm → `evaluate_stage2_v7` → prose body with:
   `result, _ = assess_turn(None, question, confirmations=confirmations,
   vocab_profile={"v3_bundled": "v4_legacy_18", "statutory_primary":
   "brutal_primary"}[custody_vocab], locale=locale, mode=mode, device=device,
   kannada_strategy=kannada_strategy, with_prose=with_prose)`.
   Then map back to the EXISTING return shape key-for-key:
   `candidates_before_stage2` ← `result["candidates_before_gate"]` (genuine set,
   fixes L100/L168 clone); `gated_out` ← `result["gated_out"]`; prose fields
   (`prose`, `prose_fp_hits`, `prose_quality_flags`, `prose_render_ms`) come
   from the runtime — **do NOT re-run `prose_forbidden_check` with `[]`** (the
   L105/L173 bug). Keep `latency_s` semantics. Keep the CLI `main()` unchanged.
3. **`assess_v7_batch` → delegate per question.** One fresh single-turn
   `SessionState` per question (preserves strict per-question isolation),
   same loop shape and return `(records, total_wall_s)`; per-record keys as
   in (2), plus existing `model_slots` / `translated_text` passthrough from
   the runtime result if present.
4. **Must still pass unchanged:** `tests/test_v7_rules.py` (10/10),
   `tests/test_graph_v4.py`, `tests/test_prose_renderer_v2.py`,
   `tests/v7_backtest.py` (Lane 10 — note the scorer now gets genuine
   `candidates_before_gate`; expect Fb to become measurable, value 0 on
   16-Q/Brutal-230, to be confirmed on RTX).

### 8.2 `src/laya_family.py`

1. **`assess(question, extract, confirmed)` → delegate, keeping the `extract`
   seam.** Keep signature `(question, extract, confirmed) -> dict` (tests pass
   an `extract` callable). New body: translate `confirmed` maintenance fields
   to v7.1 fact keys (proposed mapping — **needs legal sanity check**):
   `hma_pending` → `proceeding_pending_hma`, `hma_decree` → `decree`,
   `bnss_order` → `bnss_order`, `interim` → `interim_asked`,
   `permanent` → `lump_sum_settlement` (only when a decree/settle is meant —
   flag: this is lossy), `recover` → intent `bnss-144-3` (no 1:1 fact key;
   pass as `existing_order_enforcement=True` + a `recover=True` marker fact),
   `vary` → intent `bnss-146` (same treatment), `new_support` / `wife` /
   `minor_child` / `parent` / `husband` → beneficiary facts
   (`claimant_role`, `minor_child`, `money_fact`) — these have no 1:1 v7.1
   keys either, so the wrapper needs a small adapter, not a rename. Then
   `result, _ = assess_turn(None, question, confirmations=mapped,
   vocab_profile="maintenance_sub_routes", ...)` and translate the runtime
   result back to the EXISTING maintenance shape (`status` / `routes` /
   `questions` / `notes` / `facts`). `extract`, when given, stays the Stage 0
   source for the maintenance profile (pass-through); when `None`, runtime
   extraction is used. **Preserve in the wrapper (do not drop):** the
   non-Latin-script guard (L129–132, `unsupported_language`) and the 3000-char
   guard — the runtime has neither.
2. **`guided_assessment` → shared state.** Keep signature
   `(question, extract, confirmed, prompt, tell)`. New body: one
   `SessionState` for the whole dialogue; each loop iteration calls
   `assess_turn(state, question, confirmations=answers, ...)` and reads
   `result["pending_clarifications"]` / `maintenance_questions` for the next
   prompt instead of re-running `assess()` from scratch (today it has no
   memory between answers — this is what gives it true multi-turn state).
3. **`parse_confirmations`, `QUESTIONS`, `REASONS`, CLI `main()`:** unchanged.
4. **Must still pass unchanged:** `tests/test_laya_family.py` (32/32),
   `tests/laya_maintenance_backtest.py`.
