# Phase A gate A1 — Dead fact keys + graph contract

- **Lane:** A (implementation swarm)
- **Date:** 2026-11-27
- **Script:** `scripts/check_graph_contract.py` (pure python, no torch)
- **Verdict: FAIL** — 21 of 59 graph-consumed keys have no classifier
  producer, no derivation, and no meaningful default. Exit code 1.
  (Re-run: `python3 scripts/check_graph_contract.py` — exit 1.)

## What was checked

Every key `src/laya_v7_graph.py` reads — via `proved_true` /
`fact_value` / `is_denied` (on `facts` or the normaliser alias `f`),
`_as_str`, `.get`, `[...]` and `"x" in facts` — was extracted from the
source (59 distinct keys) and classified against the classifier's vocab
(`src/laya_v7_classifier.py`: 11 issues, 28 facts, 3 enum heads) plus
deterministic derivations in `_normalize_legacy_facts` and in the
Stage 1 → Stage 2 bridge (`tests/recall_eval.py::predict_sections_from_stage1`,
lines ~236–238, which builds `negated_issues` / `denied_issues` from
denied issue intents).

## The 10x-swarm "8 dead keys" claim — verified, and it does NOT hold for the classifier path

The 10x swarm (Lane 01 diagnosis §4c) reported the 8 formerly-dead keys
as "wired, not dead". That is TRUE for the **evidence/extractor path**
only: all 8 are emitted by `src/laya_v7_evidence.py:931–938`
(`extract_grounded_v7`), with near-zero fire counts on the frozen split
(`interim_asked` 6, `money_fact_child_or_parallel` 1,
`stay_in_house_under_eviction_pressure` 2,
`stridhan_held_by_inlaws_refused` 2, `stridhan_safe_in_own_possession` 0,
`stridhan_abandoned_or_undisputed` 0, `urgent_safety_risk` 2,
`hypothetical_or_joint_prop_fact_only` 10 — Lane 01, pinned file).

For the **classifier path** — the Stage 1 that is supposed to REPLACE
the extractor — 7 of the 8 are still dead: only `interim_asked` is in
the classifier's 28 FACTS. The other 7 never appear in any classifier
output, and the graph reads `False`/absent for them on every question:

| Dead-8 key | Classifier FACT? | Evidence path? | Graph effect in classifier path |
|---|---|---|---|
| `interim_asked` | YES | yes | covered |
| `money_fact_child_or_parallel` | NO | yes | `pending_hma and not money_fact_child_or_parallel` always takes the non-parallel branch |
| `stay_in_house_under_eviction_pressure` | NO | yes | protection trigger relies on `violence` / `coercive_eviction_or_lockout` only |
| `stridhan_held_by_inlaws_refused` | NO | yes | recovery escalation needs `demand_made` / sold instead |
| `stridhan_safe_in_own_possession` | NO | yes | `stridhan_held_or_disposed` derivation always takes the "held" branch when `stridhan_claim` is true |
| `stridhan_abandoned_or_undisputed` | NO | yes | same derivation, same default |
| `urgent_safety_risk` | NO | yes | safety escalation falls back to `violence` only |
| `hypothetical_or_joint_prop_fact_only` | NO | yes | procedure escalation never fires on this condition |

## Coverage table (59 keys)

Counts: FACT 27 · ENUM 2 · DERIVED 3 · DEFAULTED 2 · LEGACY 3 · ALIAS 1 ·
UNCOVERED 21.

| Key | Class | Impact |
|---|---|---|
| `being_filed`, `birth_cert_asked`, `child_fact`, `child_maintenance_only`, `child_safety_risk`, `coercive_eviction_or_lockout`, `custody_claim`, `decree`, `demand_made`, `divorce_asked`, `dv_injury_comp_asked`, `existing_order_enforcement`, `explicit_residence_order_only`, `in_scope`, `interim_asked`, `joint_property_claim`, `judicial_separation_only`, `lump_sum_settlement`, `minor_child`, `money_fact`, `mutual_consent`, `proceeding_pending_hma`, `residence_claim`, `restitution_asked`, `stridhan_claim`, `stridhan_sold_or_mortgaged`, `violence` | FACT (27) | kept_ids / escalations |
| `claimant_sex`, `claimant_role` | ENUM (2) | kept_ids (sex/role gating; bridge maps M/F/U → male/female/unknown) |
| `negated_issues`, `denied_issues` | DERIVED — bridge (from denied intents) | kept_ids |
| `stridhan_held_or_disposed` | DERIVED — graph normaliser (from `stridhan_claim` + safe/abandoned flags) | kept_ids |
| `domestic_relationship` | DEFAULTED — normaliser sets `True` when absent | kept_ids (PWDVA eligibility defaults to true) |
| `open_fact_markers` | DEFAULTED — normaliser sets empty set (graph itself adds `joint_property_claim` / `stridhan_sold_or_mortgaged` markers) | escalations |
| `gold_fact`, `magistrate_case_only`, `proceeding_pending` | LEGACY — normaliser inputs only; feed derivations whose targets are FACTS | normaliser / filter fallback |
| `stridhan_sold` | ALIAS of `stridhan_sold_or_mortgaged` | escalations |
| `arrears_recovery_asked` | UNCOVERED | kept_ids (conditional-only bnss-144-3 disposition; never eligible today) |
| `maintenance_variation_asked` | UNCOVERED | kept_ids (conditional-only bnss-146 disposition; never eligible today) |
| `interim_only_asked` | UNCOVERED | kept_ids — KNOWN artifact: pending-HMA interim-only should emit hma-24 alone; in the classifier path it always also emits bnss-144 + pwdva-20 (Lane 01 §4a: 2 FNs on the frozen split) |
| `interim_unpaid_with_joint_or_parallel` | UNCOVERED | kept_ids (parallel bnss-144 never fires) |
| `post_decree_lump_sum_enforcement` | UNCOVERED | kept_ids (`handled_maint` flag; lump-sum path still works via `lump_sum_settlement`) |
| `money_fact_child_or_parallel` | UNCOVERED | kept_ids (existing-order branch always non-parallel) |
| `stay_in_house_under_eviction_pressure` | UNCOVERED | kept_ids (protection trigger narrows to violence / lockout) |
| `custody_negated`, `maintenance_negated`, `residence_negated`, `stridhan_negated`, `violence_negated` | UNCOVERED (5) | kept_ids — always False; negation currently flows only via the `negated_issues` set, so these are redundant *unless* a fact-level negation without an issue-level denial is needed |
| `urgent_safety_risk` | UNCOVERED | kept_ids + safety escalation (falls back to `violence`) |
| `stridhan_held_by_inlaws_refused` | UNCOVERED | escalations (recovery needs demand/sold) |
| `stridhan_safe_in_own_possession`, `stridhan_abandoned_or_undisputed` | UNCOVERED (2) | normaliser (feed the `stridhan_held_or_disposed` derivation; always False ⇒ held defaults True) + civil-handoff check |
| `first_demand_never_made`, `forum_question_asked`, `procedure_how_to_asked`, `no_dispute_empty`, `hypothetical_or_joint_prop_fact_only` | UNCOVERED (5) | escalations only (demand / court / procedure kinds never fire on these conditions) |

## Reverse-dead outputs (produced, never read by the graph)

- `school_fees_fact` — a classifier fact head (in all 8,000 corpus
  records) that no graph branch reads. It trains, it is never consumed.
- `procedure` — a classifier issue head the graph never reads via
  `_wanted()` (10 of 11 issues are read; Lane 01 already noted
  procedure has no extractor trigger and no section).
- `modality_time` — a classifier enum head the graph never reads
  (it feeds the clause gate in training, so it is not fully dead —
  but as a graph input it is unused).

## What "covered" does NOT mean

`DEFAULTED` keys are not producers: `domestic_relationship=True` is a
silent assumption (every claimant is treated as in a domestic
relationship unless the legacy input says otherwise), and
`open_fact_markers=set()` means the fact-kind escalation fires only on
the two markers the graph adds itself. `LEGACY` keys are inputs the
classifier never emits; they are harmless only while their derivation
targets (`proceeding_pending_hma`, `stridhan_claim`) are present as
FACTS. None of these may be cited as "the classifier supplies this key".

## Lane B fixes required (do NOT edit the graph — it stays frozen)

1. **Schema decision (coordinator):** the uncovered set is 21 keys.
   The recall-swarm tracker already records the open schema-bump
   decision (28 → 36 facts) as a parent/coordinator decision. A1's
   evidence: 7 of the 8 dead keys + the post-order split facts +
   the `*_negated` facts + the escalation flags are the candidates.
   Until the schema grows, these keys read `False` on every
   classifier-path question — record that as a known limitation, do
   not silently treat absence as evidence.
2. **Deterministic derivations first (no schema change needed):**
   `stridhan_held_or_disposed` is already derived in the graph; the
   same pattern can cover `interim_only_asked` ← `interim_asked` +
   pending-HMA context, and `money_fact_child_or_parallel` ←
   `money_fact` + `child_maintenance_only` + parallel-proceeding
   context — but the derivation must live in the Stage 1 → Stage 2
   adapter (Lane C's runtime / the bridge), NOT in the frozen graph.
3. **`school_fees_fact`, `procedure`, `modality_time`:** decide
   whether they stay as auxiliary-only heads (documented as such) or
   gain a graph consumer. `school_fees_fact` in particular is a
   trained head whose signal is currently discarded.
4. **Negation:** the five `*_negated` facts duplicate the
   `negated_issues` set mechanism. Pick one source of truth for
   fact-level negation and remove or wire the other; do not leave
   both half-alive.
