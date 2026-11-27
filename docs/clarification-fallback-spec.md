# Clarification-Fallback Spec — LAYA v7.1 (V71-P1-5, plan §1.2 + §2.3 V71-P2-4)

Date: 2026-11-27 · Lane 04 · Status: **spec, reconciled with Lane 05's implementation**

## 0. What this spec is

When the pipeline is *uncertain* about a high-impact fact or issue it must
**ask a structured clarifying question instead of silently predicting `[]`**
(or silently guessing a section). This spec defines:

1. the trigger (when to ask instead of predict),
2. the `ClarificationPrompt` schema (one shape for the maintenance runtime
   and the unified v7 runtime),
3. the ranking (max 2 questions/turn, remedy-flip information gain),
4. the six required question types (plan §2.3 V71-P2-4),
5. the exact interface `src/laya_clarifier.py` (Lane 05) must implement,
6. the maintenance-side wiring (what Lane 04 changed in
   `src/laya_family_evidence.py`, and what the runtime must do with prompts).

## 1. Reconciliation note — Lane 05 already built the module

`src/laya_clarifier.py` (Lane 05, committed before this spec existed)
already implements plan §2.3 directly. **This spec adopts Lane 05's public
entry points as normative** and records the deltas below, so no rework is
needed — the coordinator reconciles only the listed deltas:

| Item | Lane 05 as built | This spec (normative) |
|---|---|---|
| Entry points | `rank_clarifications(state, facts, issues, *, max_questions=2, kept_ids=None)` and alias `clarifying_questions_for_turn(...)` | **Adopted as-is.** Both names are required; `clarifying_questions_for_turn` is the seam name other lanes call. |
| Max questions/turn | `MAX_QUESTIONS_PER_TURN = 2` | **Adopted.** Hard cap, never exceeded, even when >2 facts are uncertain. |
| Gray band | `TAU_LOW = 0.30`, `TAU_HIGH = 0.70` | **Adopted as defaults.** Final calibrated values are Lane 10's job (V71-P7-3); this spec does not re-decide them. See §2 for the reconciliation with the maintenance runtime's `0.70 / 0.20` thresholds. |
| Target record | `ClarificationTarget` dataclass (`fact_key`, `question`, `base_priority`, `flips_if_yes`, `flips_if_no`, `reason`; `information_gain() = base_priority + flip_count`) | **Adopted as-is.** |
| Prompt dict shape | `{fact_key, question, reason, information_gain (string, 1 decimal), flips_if_yes, flips_if_no}` (comma-joined strings) | **Adopted as-is** — this is the `ClarificationPrompt` schema (§3). One shape for both runtimes. |
| Conflict bonus | `+5.0` gain for `conflicting` status | **Adopted.** Conflicts outrank gray-band items at the same base priority. |
| `disambiguation_prompt(fact_key, prior_status, new_status)` | returns `information_gain: "conflict"` (non-numeric sentinel) | **Accepted, documented:** `information_gain` is a string; the literal value `"conflict"` is the only permitted non-numeric value and means "ask before any ranked prompt". |
| Never-ask rule | user-confirmed facts (provenance rank 1) and verified spans (ranks 2–3) are never re-asked; settled facts are never re-asked | **Adopted.** See §4. |
| Missing-fact rule | a fact with no evidence object at all is askable only for `violence`, `urgent_safety_risk`, `in_scope` ("not_raised" otherwise) | **Adopted.** A missing fact means "not raised", not "uncertain" — except the two plan-mandated gates (safety, scope). |
| Already-pending rule | facts already in `state.pending_clarifications` are not repeated | **Adopted.** A question is asked once per session until answered or superseded. |

**Delta D-1 (naming):** plan §2.3 calls the trigger fact
`proceeding_pending_hma`; Lane 05's table uses that key. The maintenance
runtime's equivalent keys are `hma_pending` / `hma_decree` /
`bnss_order` (`src/laya_family.py: QUESTIONS`). The unified runtime
(Lane 05, `laya_runtime.py`) MUST map `hma_pending -> proceeding_pending_hma`
and `hma_decree -> decree` when forwarding maintenance facts to the
clarifier; the clarifier itself only ever sees the canonical keys in §5.

**Delta D-2 (scope trigger):** Lane 05 asks `in_scope` only when
`kept_ids == []` **and** scope is not proved true. This spec additionally
requires the trigger in §2 rule T-2: the scope question also fires when
`kept_ids == []` and `in_scope` is `unknown`/`conflicting`/gray-band even
if a low-confidence model score exists — "not proved true" and "uncertain"
are the same gate for this purpose.

## 2. Trigger — when to ask instead of predict

Let `P(f)` be the calibrated head probability for fact/issue `f`, with gray
band `[tau_low, tau_high) = [0.30, 0.70)` by default (Lane 10 calibrates).

- **T-1 (gray band):** any high-impact fact/issue with
  `tau_low <= P(f) < tau_high` is **not** decided by the model. The runtime
  MUST emit a `ClarificationPrompt` for the highest-gain such fact(s)
  instead of using the model's guess as evidence. (In the maintenance
  evidence layer this is structural: `supervised_signals_to_evidence()`
  in `src/laya_family_evidence.py` drops every signal below `tau_high`
  outright — it never becomes evidence, so the clarifier is the only
  consumer of that uncertainty. A dropped signal must never be re-read as
  a "no".)
- **T-2 (scope):** when `kept_ids == []` **and** `in_scope` is uncertain
  (`unknown`, `conflicting`, or gray-band), emit the scope question (§5,
  type 2) instead of returning a silent `[]`. A kept section already
  proves scope, so the scope question never fires when `kept_ids != []`.
- **T-3 (conflict):** when two assertions in one turn — or an unconfirmed
  model guess vs a prior verified span — conflict on one fact, set that
  fact's status to `"conflicting"` and emit its disambiguation prompt
  (`disambiguation_prompt()`) before any ranked prompt. A conflict is
  never resolved by silently picking a side.
- **T-4 (silent-drop ban):** an in-scope query MUST NOT end with
  `kept_ids == []`, no routes, and no prompt. If nothing is kept and no
  fact qualifies under T-1–T-3, the runtime MUST ask the scope question
  (T-2) — this is what eliminates the 2 silent misses in Sealed Fresh-20.
  The only silent `[]` allowed is a *confirmed* out-of-scope answer
  (user-confirmed `in_scope == False`, or a verified span proving it).

**Threshold reconciliation (maintenance runtime):**
`src/laya_family.py: _interpret` today maps numeric model scores with
`>= 0.70 -> "yes"` and `<= 0.20 -> "no"`, and procedural facts
(`hma_pending`, `hma_decree`, `bnss_order`) accept *only* evidence or user
confirmation — never a model score. The clarifier gray band `[0.30, 0.70)`
is therefore **not** the same interval as `_interpret`'s `[0.20, 0.70)`
unknown band: a maintenance score in `[0.20, 0.30)` is "unknown" to
`_interpret` but *below* the clarifier's gray band, so it produces no
prompt on its own — it is covered by T-4 (ask scope) or by the
maintenance runtime's own `QUESTIONS` flow. Lane 10's calibration
(V71-P7-3) owns unifying these into one calibrated pair; until then both
defaults stand and neither may be silently changed by a lane.

## 3. Prompt schema — `ClarificationPrompt`

One dict per question, returned as a list of at most 2, highest gain first.
This is exactly the dict `rank_clarifications()` returns today:

```python
{
    "fact_key": str,            # canonical fact key, e.g. "bnss_order"
    "question": str,            # plain-language question, no legalese,
                                # no statute numbers the user must decode,
                                # never a court-choice question (Fp #5)
    "reason": str,              # "<plan reason> (<why: unknown|conflicting|gray_band|not_extracted>)"
    "information_gain": str,    # "12.0" (1 decimal) or the literal "conflict" (see §1)
    "flips_if_yes": str,        # comma-joined section ids whose disposition
                                # flips if the user answers yes, "" if none
    "flips_if_no": str,         # same for a no answer; "all" means every
                                # kept section is retired (scope-no only)
}
```

Rules on the schema:

- `question` MUST be answerable yes/no (or with a single short fact such as
  a date). It MUST NOT contain a forbidden prose item (no invented rupee
  amounts, no "pay slip" / tenancy language, no precedent strings).
- `flips_if_yes` / `flips_if_no` name **section ids** (`bnss-144-3`,
  `hma-24`, …), never free text. They are the audit trail for the ranking:
  a prompt that flips nothing must have `base_priority` high enough to
  justify itself (safety/scope only).
- The list is **ranked, highest gain first, max 2**. The runtime asks them
  in list order and MUST NOT ask a third question in the same turn — the
  remaining facts wait for the next turn (multi-turn accretion, V71-P2-3).

## 4. Ranking — remedy-flip information gain

```
information_gain(target) = base_priority(target) + |flips_if_yes ∪ flips_if_no|
conflicting status:      + 5.0
```

Base priorities (plan §2.3 order; Lane 05's table, adopted):

| Priority | Fact key(s) | Why this high |
|---|---|---|
| 100 | `violence` | safety first, always |
| 99 | `urgent_safety_risk` | safety first, always |
| 90 | `in_scope` | scope gate — decides whether anything applies at all |
| 80 / 79 | `proceeding_pending_hma` / `being_filed` | gates `hma-24`, `hma-26`, `hma-27` |
| 70 | `bnss_order` | gates `bnss-144-3`, `bnss-146`; includes the pre-BNSS 1 Jul 2024 date question (CrPC s.125 vs BNSS s.144) |
| 60 | `demand_made` | gates `bns-316` |
| 50 | `minor_child` | gates `bnss-144`, `gwa-1890`, `hma-26` (age under 18) |
| 45 / 40 / 35 / 30 | `mutual_consent`, `decree`, `domestic_relationship`, `custody_claim` | permitted extensions (Lane 05); same formula |

Ties break by `fact_key` alphabetically (deterministic; Lane 05 sorts by
`(-gain, fact_key)`).

**Safety decoupling (non-negotiable, plan §4.3 V71-P4-3):** a safety
question (`violence` / `urgent_safety_risk`) fires **before and
independently** of `kept_ids`, `claimant_sex`, `domestic_relationship`,
`proceeding_pending_hma`, `demand_made`, or any clarification hold. It is
never gated behind a procedural question ("first clarify if an HMA case is
pending"). Non-violent residence-only requests
(`explicit_residence_order_only == True`) MUST NOT trigger a safety prompt.

**Never ask:** a fact the user already confirmed (provenance rank 1), a
fact grounded in a verified user/translated span (ranks 2–3), a fact
already settled high-confidence, or a fact already pending in
`state.pending_clarifications`.

## 5. The six required question types (plan §2.3 V71-P2-4)

These six MUST exist in `CLARIFICATION_TARGETS`. Lane 05's table already
contains all six (plus the four extensions in §4). Canonical wording is
Lane 05's `question` strings; the runtime MUST NOT reword them without a
human-legal review, because the wording is the user-facing contract.

1. **Safety check** — `violence` (base 100) and `urgent_safety_risk`
   (base 99). "Are you, or a child in the house, facing threats, hitting,
   or any immediate physical danger right now?" / urgent-risk variant.
   Flips: `pwdva-18`, `safety`.
2. **Scope disambiguation** — `in_scope` (base 90). Fires only under T-2
   (`kept_ids == []` and scope uncertain). "Is your question about Indian
   family law — marriage, divorce, maintenance, custody, residence, or
   Stridhan — or is it about a different matter such as rent, employment,
   or a loan?" Flips-if-no: `all`.
3. **Proceeding gates** — `proceeding_pending_hma` (80) /
   `being_filed` (79). "Is a case about your marriage under the Hindu
   Marriage Act currently pending in court?" / being-filed variant. Flips:
   `hma-24`, `hma-26`, `hma-27`. Maintenance mapping: `hma_pending`.
4. **Order statute / date** — `bnss_order` (70). "Does the existing
   maintenance order cite section 144 of the BNSS, 2023, or does it cite
   the older section 125 of the CrPC?" Flips: `bnss-144-3`, `bnss-146`.
   This is the prompt final_check rows 022–024's `must_ask` already
   require in the maintenance runtime (`QUESTIONS["bnss_order"]`).
   Maintenance mapping: `bnss_order`.
5. **Demand** — `demand_made` (60). "Have you made a written demand for
   the return of your Stridhan (gold/jewellery), and was it refused?"
   Flips: `bns-316`.
6. **Minor-child age** — `minor_child` (50). "Is the child under 18 years
   of age?" Flips: `bnss-144`, `gwa-1890`, `hma-26`. Maintenance mapping:
   `minor_child` (same key; `QUESTIONS["minor_child"]` is the maintenance
   wording — the unified runtime uses the §5 wording above).

## 6. Exact interface `src/laya_clarifier.py` must implement

(Lane 05 owns the file; this is the contract the coordinator holds it to.
Signatures below are Lane 05's as built, adopted as normative.)

```python
MAX_QUESTIONS_PER_TURN: int = 2
TAU_LOW: float = 0.30
TAU_HIGH: float = 0.70

@dataclass(frozen=True)
class ClarificationTarget:
    fact_key: str
    question: str
    base_priority: float
    flips_if_yes: tuple[str, ...] = ()
    flips_if_no: tuple[str, ...] = ()
    reason: str = ""
    @property
    def flip_count(self) -> int: ...
    def information_gain(self) -> float: ...   # base_priority + flip_count

CLARIFICATION_TARGETS: tuple[ClarificationTarget, ...]
# Must contain at least the six §5 types, in §4 priority order.

def rank_clarifications(
    state: SessionState | None,
    facts: dict[str, Any],
    issues: dict[str, Any] | None = None,
    *,
    max_questions: int = MAX_QUESTIONS_PER_TURN,
    kept_ids: list[str] | None = None,
) -> list[dict[str, str]]: ...
# Returns ClarificationPrompt dicts (§3), highest gain first, len <= max_questions.

def clarifying_questions_for_turn(
    state: SessionState | None,
    facts: dict[str, Any],
    issues: dict[str, Any] | None = None,
    *,
    max_questions: int = MAX_QUESTIONS_PER_TURN,
    kept_ids: list[str] | None = None,
) -> list[dict[str, str]]: ...
# Alias for rank_clarifications — the seam name other lanes call.

def disambiguation_prompt(
    fact_key: str, prior_status: str, new_status: str,
) -> dict[str, str]: ...
# Targeted prompt for a conflicting fact (T-3); information_gain == "conflict".
```

Contract rules for the implementation:

- **No model calls.** The clarifier reads `FactEvidence` / `IssueEvidence`
  dicts and `SessionState` only; it never calls a model and imports nothing
  from the runtime (no import cycle).
- **Deterministic.** Same `(facts, issues, kept_ids, pending)` → same list,
  same order. No randomness, no wall-clock dependence.
- **Provenance-aware.** `_needs_clarification()` MUST consult provenance
  rank (`laya_schema_v71.provenance_rank`): ranks 1–3 are never askable.
  A `FactEvidence` with `status == "conflicting"` is askable regardless
  of its confidence; a `model_uncertain` / `model_suggestion` fact is
  askable only inside `[TAU_LOW, TAU_HIGH)`.
- **Facts are dicts of `FactEvidence`.** Callers MUST pass the evidence
  objects, not bare strings — a bare string carries no provenance, and
  the clarifier cannot tell a verified span from a guess without it.
  (`_fact_evidence()` returns `None` for non-`FactEvidence` values, and
  `None` means "not raised" except for the safety/scope gates.)
- **Maintenance mapping (Delta D-1)** is the *caller's* job
  (`laya_runtime.py`): `hma_pending -> proceeding_pending_hma`,
  `hma_decree -> decree`. The clarifier never sees maintenance-local keys.

## 7. Maintenance-side wiring (Lane 04 — what changed, what must happen)

**Changed in this lane** (`src/laya_family_evidence.py`, V71-P1-4):

- `SupervisedSignal` dataclass + `verify_supervised_span()` +
  `supervised_signals_to_evidence()` — the placeholder interface through
  which Lane 03's classifier heads will plug in (see §8). Until Lane 03
  ships, all calls pass `supervised=None` and behaviour is unchanged.
- `requested_procedural_actions(question, *, supervised=None)`,
  `direct_support_evidence(question, *, supervised=None)`,
  `grounded_beneficiaries(question, *, supervised=None)` — verified
  high-confidence supervised "yes" signals (score `>= 0.70`, span verified
  verbatim) merge in via `setdefault`: they fill a purpose/beneficiary the
  regex missed but never overwrite a regex "no" (declined clause) or an
  existing regex "yes". Signals below `0.70`, `"no"`/`"unknown"` signals,
  unknown fields, and unverified spans are dropped — they are clarifier
  input (T-1), never evidence.
- Regex-gap fixes that remove the two final_check FNs at the evidence
  layer (so the clarifier is not needed to rescue them): see
  `docs/10x_swarm_state/lane-04-p1-4-p1-5.md`.

**What the runtime must do (Lane 05 unified runtime; NOT this lane's
files — `src/laya_family.py` is out of scope for Lane 04):**

1. After `assess()` / `assess_v7()` computes `facts` and `kept_ids`, if
   `kept_ids == []` and the result would otherwise be a silent
   `needs_clarification` / `review_needed` with no routes, call
   `clarifying_questions_for_turn(state, facts, issues, kept_ids=[])` and
   attach the returned prompts to the result (max 2) instead of returning
   bare. The maintenance runtime's existing `QUESTIONS` dict already holds
   the maintenance wordings for `hma_pending`, `hma_decree`, `bnss_order`,
   `minor_child`, `new_support`, `wife`, `parent`, `interim`,
   `permanent`, `recover`, `vary` — the unified runtime MUST prefer the
   §5 canonical wording for the six shared types and keep the maintenance
   wordings only for maintenance-only keys (`new_support`, `wife`,
   `parent`, `interim`, `permanent`, `recover`, `vary`).
2. Map maintenance keys to canonical keys before calling the clarifier
   (Delta D-1) and map the answers back: a yes/no answer to a prompt for
   `proceeding_pending_hma` sets `hma_pending` in the maintenance facts
   (user_confirmation provenance, rank 1).
3. Never feed a clarifier answer back into the model as a training signal
   in the same turn; answers are `user_confirmation` facts, not model
   scores.

## 8. Supervised-head interface (for Lane 03 — summary; code is normative)

Lane 03's classifier MUST return, per question, a mapping
`field -> SupervisedSignal` for fields in
`{"new_support", "interim", "permanent", "recover", "vary", "wife",
"minor_child", "parent"}`. `SupervisedSignal` fields: `field`, `value`
(`"yes" | "no" | "unknown"`), `score` in `[0, 1]`, `span`
`{"start", "end", "text"}` (verbatim question span), `head`
(e.g. `"purpose_head"`, `"beneficiary_head"`), `model`. Admission rule
(code in `src/laya_family_evidence.py: supervised_signals_to_evidence`):
admit only `value == "yes"`, `score >= 0.70`, span verifies exactly
(`question[start:end] == text`, in bounds, non-empty, contains a letter).
Everything else is dropped here and routed to the clarifier under T-1.
No score, span, or label in the evidence module is a classifier output —
the module invents none.

## 9. Worked examples

- **final_check 018 (vary, was an FN):** "What is the process to have the
  amount changed after my long illness?" — after Lane 04's regex fix the
  evidence layer now fires `vary=yes` + `bnss_order=yes` directly, so no
  prompt is needed. *Before* the fix this is exactly a T-1 case: a vary
  score in the gray band with `bnss_order` unknown would have emitted the
  `bnss_order` prompt (type 4) instead of a silent miss.
- **final_check 022–024 (`must_ask` rows):** `hma_pending` / `hma_decree` /
  `bnss_order` unknown with a purpose already yes → the runtime asks the
  type-3 / type-4 prompt. These already work in the maintenance runtime
  (`QUESTIONS`); the spec keeps their wording and adds the §3 audit
  fields (`flips_if_yes/no`, `information_gain`).
- **Sealed Fresh-20 silent pattern:** a question whose facts all land
  below `tau_high` and keeps nothing → T-4: ask the scope question
  (type 2) rather than returning `[]` with no prompt.

## 10. Verification (RTX 5050 — cannot run on this VM)

```bash
# Maintenance backtest with the real model (confirms 34/34 incl. the 2 FNs):
python3 -m tests.laya_maintenance_backtest --split final_check --device cuda
python3 -m tests.laya_maintenance_backtest --split final_check --device cuda --extractor structured
# Row-level detail is available on development / challenge only:
python3 -m tests.laya_maintenance_backtest --split development --device cuda --detail
python3 -m tests.laya_maintenance_backtest --split challenge --device cuda --detail
# Guardrails (CPU, run on this VM — both pass):
python3 tests/test_graph_v4.py
python3 tests/test_prose_renderer_v2.py
python3 -m unittest discover -s tests -p "test_*.py"
```

## 11. Open items

- **O-1 (Lane 10):** calibrate `TAU_LOW` / `TAU_HIGH` per head
  (V71-P7-3) and unify with `_interpret`'s `0.70 / 0.20` — until then the
  §2 defaults stand.
- **O-2 (Lane 05):** apply §7 runtime wiring in `laya_runtime.py`
  (attach prompts when `kept_ids == []`) and the Delta D-1 key mapping.
  The maintenance `QUESTIONS` wordings for the six shared types are
  superseded by §5 wording once the unified runtime lands.
- **O-3 (Lane 03):** ship `src/laya_v7_classifier.py` returning
  `SupervisedSignal` mappings per §8; until then `supervised=None`
  everywhere and the regex evidence layer carries recall.
- **O-4 (human):** the six §5 wordings are adopted from Lane 05's table
  without a human legal read; G12 rater should confirm the plain-language
  questions do not misstate any section's test.
