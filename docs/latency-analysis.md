# Latency analysis — v3 Cell 7 (Laya family-law system)

**Status:** ANALYSIS ONLY. No notebook, builder, graph, or results file was
modified. All counts below were derived by reading v3 Cell 7 code and by
running its own deterministic `split_clauses()` on the 16 Cell 6 questions —
no live run, no model call, no results-JSON scoring was needed.

**Headline numbers (measured live, v3 run 2026-11-26):** Cell 7 took **897.6 s**
for 16 questions — **mean 56.1 s/question, range 35–123 s/question**
(model load excluded). The gate row G14 (`laya-10-10-gate-definition.md` §1)
requires mean ≤ 15 s, max ≤ 30 s, full run ≤ 240 s excl. load. **v3 fails all
three parts of G14.** v1 passed it (mean 11.77 s, max 24.17 s, run 188 s).
The empty-5 recall fix cost ~4.8× latency and broke the latency gate. Any v8
plan that keeps v3's call pattern cannot pass G14 — see §5.

## 1. What a `noul` call is, and how the count was done

Cell 7 drives the model through `agent.predict({'body': ...}, payload)`,
where `payload` is a dict of keys, each key one scored prompt. A key of type
`'noul'` is one yes/no probability judgement — one model inference. A key of
type `'choice'` (sub-choices) is also one model inference, but it is **not**
a `noul` call; it is counted separately in §2.4.

Counting rule used here: **one `noul` call = one `'noul'` key submitted in a
payload.** This assumes the backend executes each key as its own inference
(sequential on CPU). That assumption is consistent with the measured time —
897.6 s / 682 noul keys ≈ 1.32 s/key (§3) — but Cell 7 records only
per-question wall time, not per-call time, so per-key parallelism inside one
`predict` call cannot be ruled out from the notebook alone. The v8 build
should log per-`predict`-call wall time to confirm (§5.4).

Recomputation pattern (the structural fact behind the count): the full
question is scored with 10 prompts; then **every clause is re-scored with the
same 10 prompts**; then the full question is scored a **third** time with 12
aux prompts. Nothing is shared or cached between the three passes.

## 2. Exact count — `noul` calls per question (v3 Cell 7)

### 2.1 The three `noul` groups

| Group | Keys per invocation | Invocations per question | `noul` keys |
|---|---|---|---|
| Full-question pass | 10 | 1 | **10** |
| Clause-split passes | 10 per clause | C (clause count) | **10 × C** |
| Aux prompts | 12 | 1 | **12** |
| **Total per question** | — | — | **22 + 10C** |

Full-pass keys (10): the 7 `ISSUES` prompts (maintenance, custody, stridhan,
**residence R0**, violence, divorce, birth_certificate) + `issue_residence_r1`
(R1) + `issue_divorce_pending` + `issue_in_scope`. Note the residence issue is
scored **twice** in every pass (R0 and R1); R0 never fires — it is recorded
for the R0/R1 comparison only.

Clause-pass keys (10 per clause): the identical 10 keys, with `body` = the
clause instead of the full question.

Aux keys (12): one per `AUX_PROMPTS` entry, all on the full question —
maintenance 6, residence 3, custody 2, divorce_pending 1.

### 2.2 Clause counts per question (deterministic — run from Cell 7's own splitter)

| ID | Clauses (C) | `noul` = 22 + 10C | Clause texts (abridged) |
|---|---|---|---|
| K0 | 5 | **72** | 5 clauses; longest question |
| H1 | 3 | **52** | 3 clauses |
| H2 | 2 | **42** | 2 clauses |
| H3 | 2 | **42** | 2 clauses |
| H4 | 2 | **42** | 2 clauses |
| H5 | 3 | **52** | 3 clauses |
| H6 | 2 | **42** | 2 clauses |
| H7 | 2 | **42** | 2 clauses |
| H8 | 1 | **32** | single clause = full question |
| H9 | 1 | **32** | single clause = full question |
| H10 | 2 | **42** | 2 clauses |
| H11 | 1 | **32** | single clause = full question |
| H12 | 2 | **42** | 2 clauses (clause 1 mangled — see §4.5) |
| H13 | 1 | **32** | single clause = full question |
| H14 | 2 | **42** | 2 clauses |
| H15 | 2 | **42** | 2 clauses |
| **Total** | **33** | **682** | mean C = 2.06 clauses/question |

### 2.3 Run totals

| Group | `noul` calls / 16-question run | Share |
|---|---|---|
| Full-question pass | 10 × 16 = **160** | 23.5% |
| Clause-split passes | 10 × 33 = **330** | **48.4%** |
| Aux prompts | 12 × 16 = **192** | 28.2% |
| **Total `noul`** | **682** | 100% |

### 2.4 Sub-choice (`choice`, not `noul`) calls — counted separately

One `agent.predict` call per **fired** issue, each carrying 1–2 `choice` keys
(the issue's graph node, plus the extra node for stridhan/residence).
Per question: `2 + C + F` predict calls total, where F = number of fired
issues (F is recorded per question in the filed v3 JSON,
`RESULTS[].fired_issues`; it was not re-derived here). Run total predict
calls = 65 + ΣF. The `choice` keys are real model inferences too, so the
true inference count per run is 682 + (choice keys). With typical F of 1–3
and 1–2 keys per fired issue, that is roughly a further 20–50 inferences per
run (~3–7% on top of the 682). They are a small share of cost — but §4.6
shows two of them are pure waste.

### 2.5 What is recomputed per clause (the waste, stated precisely)

Each clause pass re-scores **all 10 prompts**, including three that have
nothing to do with clause-level rescue:

- **Residence R0** — scored on the full question and on every clause, but
  never used for firing (R1 is the firing prompt). Pure comparison data.
- **`in_scope`** — scored per clause, although its final value is
  `max(clause_max, full)` and it is a whole-question property.
- **`divorce_pending`** — scored per clause, although its final value is
  `max(clause_max, full, aux_max)`.

In addition, for the four single-clause questions (H8, H9, H11, H13) the
single clause **is** the full question (modulo a trailing full stop), so the
clause pass is a 100% duplicate of the full pass: 10 `noul` keys that can
only return the same scores.

## 3. Where the 897.6 s goes

- 897.6 s / 682 noul keys ≈ **1.32 s per `noul` key** on Colab CPU
  (this folds the sub-choice `choice` inferences in as well, so the true
  per-key figure is marginally lower — ≈1.25–1.30 s if ~25 choice keys are
  included).
- Mean 56.1 s/question ÷ 1.32 s/key ≈ 42 keys — exactly the typical
  per-question count (C = 2 → 42). The arithmetic closes: latency is
  dominated by the sheer number of sequential CPU inferences, not by any
  single slow call.
- Implied per-group wall time: clause passes ≈ 330 × 1.32 ≈ **436 s**
  (~49% of the run), aux ≈ 192 × 1.32 ≈ **253 s**, full pass ≈ 160 × 1.32
  ≈ **211 s**. (Estimates — per-group timing was not logged; see §5.4.)

**Biggest cost: the clause-split passes — 330 of 682 `noul` calls (48.4%),
≈ 436 s of the 897.6 s run.** No other single group is close. But see the
caveat in §5.1: clause-split is also the mechanism that fixed the empty-5
recall failure, so it cannot simply be deleted.

## 4. Reduction proposals (semantics-preserving first)

Savings are estimated at 1.32 s/key. "Risk to scores" means risk to
`fired_issues` / `kept_ids` / court / escalates — not to diagnostics. All
proposals that change a recorded diagnostic field are flagged as such.

### 4.1 Skip the clause pass when C == 1 — saves 10 keys/question

- **Applies to:** H8, H9, H11, H13 (4 questions) → **40 keys/run (~53 s)**.
- **Why it is safe:** with one clause, the clause *is* the full question, so
  `clause_max` == full-question score for every key; the final score is
  `max(clause, full, aux)` and the full value is already in the pool.
  `fired_clause` becomes `(full question)` for every issue, which is already
  the recorded fallback. **Zero risk to firing, kept, court, or escalates.**
  Only `stage1_clause_max` loses a redundant copy of the full-pass values.
- **Do first.** It is a three-line guard (`if len(clauses) == 1: skip`), and
  it is the only proposal with literally no downside.

### 4.2 Drop residence R0 from all scoring passes — saves 49 keys/run

- **Applies to:** 1 key in the full pass + 1 key per clause, every question
  → (16 + 33) = **49 keys/run (~65 s)**.
- **Why it is safe:** R0 is recorded for the R0/R1 comparison only and never
  fires (`RESIDENCE_PROMPT = 'R1'`). Removing it changes no firing decision,
  no kept section, no court, no escalation. **Zero risk to scores.**
- **Cost:** the R0/R1 comparison diagnostic disappears. Keep R0 behind a
  flag (`SCORE_R0 = False` default) so a comparison run can re-enable it;
  default runs drop it. The v3 R0/R1 comparison is already published, so the
  diagnostic has served its purpose.

### 4.3 Skip an issue's aux prompts once that issue already fires — saves ~50–90 keys/run (estimate)

- **Applies to:** aux prompts are per-issue (maintenance 6, residence 3,
  custody 2, divorce_pending 1). After the full + clause passes, if issue X
  already fires from `max(full, clause_max)`, X's aux prompts cannot change
  anything: the final score is a max-pool, and aux can only raise X's score
  further — X already fires, and aux for X feeds no other issue.
- **Estimated saving:** 4–6 keys/question on average → **~64–96 keys/run
  (~85–127 s)**. The estimate assumes ~2 issues already fire pre-aux on a
  typical question; it must be verified offline (below) before the v8 build
  locks it in.
- **Risk to scores: none for firing/kept/court/escalates**, for the max-pool
  reason above. Cost: `aux_max` / `aux_scores` become partial (only
  non-fired issues have aux values), and `fired_source` can no longer read
  `'aux'` for an already-fired issue. Both are diagnostics.
- **Offline verification (no live run needed):** the filed v3 JSON contains
  `stage1_raw`, `stage1_clause_max`, and `aux_max` per question. Recompute
  firing with aux restricted to issues not firing from `max(raw,
  clause_max)` and confirm `fired_issues` is unchanged on all 16. If it
  changes on any question, the proposal is wrong and must not ship.

### 4.4 Restrict `in_scope` and `divorce_pending` to the full question (+ aux for pending) — saves 66 keys/run, VERIFY FIRST

- **Applies to:** 2 keys per clause × 33 clauses = **66 keys/run (~87 s)**.
- **Why it is tempting:** both are whole-question properties, not
  clause-local ones; a divorce-pending statement ("My divorce case is already
  going on") is visible in the full question.
- **Risk to scores: LOW BUT NON-ZERO.** The final values are max-pools
  (`in_scope_final = max(clause_max, full)`,
  `pending_final = max(clause_max, full, aux_max)`), so dropping the clause
  term can lower the score — and `divorce_pending`'s threshold is very low
  (0.12), so a clause-only lift could matter. This is exactly the kind of
  change that must **not** be adopted on reasoning alone.
- **Offline verification (no live run needed):** the filed v3 JSON contains
  `stage1_clause_max` for both keys per question. Check whether
  `clause_max > raw` for either key on any of the 16, and whether dropping
  the clause term changes `in_scope` or the divorce signal on any question.
  Adopt only if the answer is "no change on all 16"; otherwise keep clause
  scoring for these two keys.

### 4.5 Cache identical (body, prompt) pairs within a run — saves ~0–10 keys/run on this set

- **Applies to:** exact duplicate (body text, prompt key) pairs. On the
  current 16 there are almost none beyond §4.1's duplicates — but one real
  defect surfaced while counting: H12's clause splitter mangles "My brother
  and I are fighting…" into the ungrammatical clause "I are fighting over our
  father's ancestral house." ("My brother" is dropped as < 3 words.) That
  clause is scored 10 times and its scores are meaningless.
- **Saving:** negligible on this set; the value is insurance on the fresh and
  Kannada sets, where repeated phrasing across questions is likelier.
  **Zero risk** (identical input → identical output; a dict cache keyed on
  `(body, prompt_key)`).
- **Note for the clause-split lane (not this lane's to fix):** the H12
  mangling is a splitter bug worth a fix of its own — " and I" should not
  split when "I" is the subject of the *same* clause's verb. Flagged here
  because it wastes 10 calls on a broken clause.

### 4.6 Drop dead sub-choice calls (custody, stridhan) — saves ~10–25 `choice` inferences/run

- **Finding from reading `stage2()`:** the sub-choice answers for **custody**
  and **stridhan** are never read. Custody keeps a fixed set
  (`gwa-1890`, `hmga-1956-s6`, `welfare-principle`, plus `hma-26` if a
  proceeding is pending — a fact, not a choice). Stridhan keeps a fixed set
  (`hma-27`, `bns-316`). Only maintenance (`maintenance-root`), residence
  (both nodes), and divorce (`divorce-gate`) sub-choices are consumed.
- **Saving:** 1 predict call per fired custody/stridhan issue (1–2 `choice`
  keys each). Exact count needs ΣF from the filed JSON; roughly **10–25
  inferences/run (~13–33 s)**. Small, but it is a genuine dead-code finding,
  not a tuning trade-off.
- **Risk to scores: none** for kept/court/escalates. Cost: `sub_choices`
  loses the custody/stridhan entries (diagnostic only). Flag to the
  coordinator: either delete these two calls in v8, or — if the graph lane
  intends the custody/stridhan choices to matter — fix `stage2()` to read
  them. One of the two must happen; shipping calls whose answers are ignored
  is the worst of both worlds.

### 4.7 Combined effect of the zero-risk proposals (§4.1 + §4.2 + §4.3 + §4.6)

- Keys saved: ~40 + 49 + ~70 + ~15 ≈ **~175 model inferences/run (~25%)**.
- Run time: ~897.6 s → **~665 s**; mean ~56 s → **~42 s/question**.
- With §4.4 verified and adopted: a further −66 keys → **~575 s**,
  **~36 s/question**.
- **That is still a G14 failure** (needs ≤ 240 s / ≤ 15 s mean). See §5.

## 5. Latency target for v8 — and the honest verdict

### 5.1 The structural problem

The zero-risk trims in §4 recover ~25–35%. G14 needs a **73%** cut
(897.6 s → ≤ 240 s). No combination of semantics-preserving trims closes
that gap, because the cost driver is the *number of inferences*, and every
inference costs ~1.3 s on Colab CPU. At that unit cost, a 15 s/question
budget buys **~11 inferences**. The v3 full pass alone is 10 `noul` keys —
before any clause, aux, or sub-choice call. In other words: **G14 is
unreachable on Colab CPU with this per-prompt architecture, by trimming
alone.** The v8 plan must pick one of three honest options:

1. **Move to a GPU Colab runtime (recommended).** A T4 GPU typically cuts
   per-inference cost for a 421M model by ~3–10×. At ~0.2–0.4 s/key, the
   *untrimmed* v3 pattern would run at ~10–20 s/question, and with the §4
   trims at ~7–14 s/question — inside G14 with margin. This is the only
   option that keeps the recall mechanism (clause-split + aux) intact.
   It changes the run environment, not the classification semantics — but
   the gate's "live Colab run" wording and the v1 CPU baseline must be
   re-read by the coordinator: a GPU run is still a live Colab run, and the
   per-question figures must be reported with the runtime (GPU type)
   recorded, or CPU/GPU numbers will be silently incomparable.
2. **Restructure scoring to ~10–12 inferences/question on CPU.**
   Full pass only (10 keys) + sub-choices only for maintenance / residence /
   divorce, with clause-split and aux replaced by a *targeted* rescue: run
   clause/aux scoring only for issues that are near-threshold on the full
   pass and only on the clauses that could plausibly lift them. This is a
   **semantics-changing** redesign that needs its own offline simulation
   (from the filed v3 JSON) and a live A/B against v3 exact/F1 before it
   can be trusted — it is, in effect, re-deriving the empty-5 fix under a
   latency budget. It might reach ~15 s/question on CPU, but only by
   risking the recall the empty-5 fix bought.
3. **Amend G14.** The gate document is frozen; amending it requires the
   coordinator and invalidates the "10/10" label until the full gate is
   re-passed under the amended version. If the user values recall over the
   15 s budget, this is a legitimate decision — but it must be an explicit
   decision, not a silent drift. Note v3 already fails G14, so the v3 run
   cannot be presented as gate-passing on any reading.

### 5.2 Realistic v8 target

| Scenario | Mean / question | Max / question | Full 16 run | G14? |
|---|---|---|---|---|
| v3 as-is (CPU) | 56.1 s | 123 s | 897.6 s | Fail |
| v8, §4 trims only (CPU) | ~36–42 s | ~90 s | ~575–665 s | Fail |
| v8, §4 trims + T4 GPU (~0.3 s/key) | **~8–12 s** | **~20 s** | **~130–190 s** | **Pass** |
| v8, §5.1 option 2 restructure (CPU) | ~15 s (hoped) | ~25 s (hoped) | ~240 s (hoped) | Borderline, unproven |

**Recommended v8 target: mean ≤ 12 s/question, max ≤ 25 s, full run ≤ 200 s
excl. load, on a recorded GPU runtime, with the §4 trims applied.** That
passes G14 with margin and keeps classification semantics intact. The
CPU-only fallback target is mean ≤ 40 s/question — which must be reported as
a **G14 failure**, not rounded into a pass.

### 5.3 The "fraction of a second" aspiration — not achievable with this architecture

The user's original aspiration (classification in a fraction of a second) is
recorded in the gate document as a **separate stretch goal, not part of the
gate** — and for good reason. The arithmetic:

- One `noul` inference costs ~1.3 s on Colab CPU. A single question needs at
  minimum one inference. Even a *single* inference per question is ~1.3 s on
  CPU — already not a fraction of a second.
- The v3 pattern needs 32–72 inferences per question. Sub-second per
  question would need ~0.01–0.03 s per inference at that count, or a
  completely different architecture: a **single forward pass with a
  multi-label classification head** (one inference per question, all issues
  scored at once), running on GPU or ONNX-quantised on CPU. That is a model
  change, not a notebook optimisation — it means fine-tuning or distilling
  Laya into a multi-label classifier, validating it against the same 16 +
  fresh + Kannada sets, and re-proving the gate. Honest estimate for that
  architecture: ~0.2–0.5 s/question on GPU, ~1–2 s/question on CPU — the
  "fraction of a second" is achievable only on GPU, and only after a model
  rebuild that is out of scope for the v8 notebook.
- What **is** achievable in v8: ~8–12 s/question on GPU with the current
  architecture + §4 trims (§5.2). That is ~5× faster than v3 and inside the
  gate. It is not a fraction of a second, and it should not be presented as
  one.

### 5.4 What must be true to hit the v8 target

1. **Runtime:** Colab GPU (T4 or better), recorded in the run log alongside
   the per-question figures. CPU numbers and GPU numbers must never be
   compared as if they were the same thing.
2. **Trims applied:** §4.1 and §4.2 unconditionally; §4.3 and §4.4 only after
   their offline verifications pass on the filed v3 JSON; §4.6 after the
   coordinator decides delete-vs-use for the dead sub-choice calls.
3. **Instrumentation (no semantic change):** Cell 7 logs wall time per
   `agent.predict` call (not just per question), so the v8 run can report
   per-key cost by group (full / clause / aux / sub-choice) instead of the
   inferred ~1.32 s/key used here. Without this, the next latency analysis
   will be guessing again.
4. **No silent scope change:** the trims must be the *only* Cell 7 changes in
   the v8 run that claims the latency improvement (gate §4 step 3: one change
   per cycle — the latency trims are one change class, but they must not be
   bundled with a threshold or prompt change in the same run, or the score
   change cannot be attributed).
5. **Prose rendering adds nothing:** the Cell 9 prose renderer (see
   `prose-renderer-design.md`) is pure string templating — zero model calls,
   milliseconds per question. Latency work and prose work do not interact.

## 6. Summary for the coordinator

- **Count:** 682 `noul` calls per 16-question run — full pass 160 (23.5%),
  clause passes 330 (48.4%), aux 192 (28.2%). Per question: 22 + 10C, with
  C = 1–5 (K0 highest at 72, H8/H9/H11/H13 lowest at 32). Plus ~20–50
  `choice` inferences for sub-choices.
- **Biggest cost: the clause-split passes (330 calls, ~436 s).** They are
  also the recall mechanism, so the lever is conditional/trimmed clause
  scoring (§4.1, §4.4), not deletion.
- **Biggest *free* lever:** dropping the never-firing residence R0 prompt
  (§4.2, −49 keys) plus skipping the clause pass on single-clause questions
  (§4.1, −40 keys) — 89 keys/run, ~117 s, zero risk to any score.
- **G14 verdict:** v3 fails G14 (56.1 s mean / 123 s max / 897.6 s run vs
  15 / 30 / 240 s). Trims alone cannot restore it on CPU. The realistic v8
  path is §4 trims + a recorded GPU runtime (target ~8–12 s/question);
  the "fraction of a second" aspiration needs a single-forward-pass model
  rebuild and is out of scope for v8.
- **Side findings for other lanes:** (a) custody/stridhan sub-choice answers
  are never read by `stage2()` (§4.6); (b) H12's first clause is mangled by
  the splitter (§4.5); (c) Cell 8 does not compute the §2 rating — the Cell 9
  prose design closes that gap.
