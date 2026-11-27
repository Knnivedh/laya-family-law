# v5 Lane A — aux-prompt audit (PRECISION round, round 2 of overnight 10/10 run)

- **Scope:** offline analysis only. No Colab run. Starting point v4r live
  (2026-11-27 ~00:19 IST): exact 10/16, micro P/R 0.826/1.000, micro-F1 0.905,
  TP/FP/FN 57/12/0. Recall 1.000, zero FN. All 12 FP are precision-only.
- **Sources:** `live-laya-colab-test-v4r-residence-only.ipynb` Cell 7 (line
  numbers below are Cell 7 source lines) and the v4r results JSON
  (`browser-download-20261126T185447.300061282Z-0-live-laya-colab-results-v4r-residence-only.json`,
  `raw_live_runs` incl. `fired_source`, `aux_scores`, `aux_max`).
- **Firing rule (Cell 7 L461–471, L505–511):** per issue,
  `final = max(clause_max, full_question, aux_max)` (L468–469), issue fires
  iff `final >= THRESHOLDS[issue]` (L510). `fired_source` (L471) records
  which of the three won. `fired_clause` is the argmax clause (L463–466).
  Thresholds L134–144: maintenance 0.10 (L135), stridhan 0.50 (L137).
  Aux prompts L179–192; each becomes
  `Does this question say "<verbatim phrase>" or mean the same thing?`
  (L444), run on the FULL question (L442–455).
- **Headline finding:** the task brief's premise is half wrong. Of the
  8 financial FPs, only **4 are aux-driven (H3, H15 maintenance)**. The
  other 4 are **clause-max-driven (H1 stridhan, H7 maintenance)** — no aux
  prompt is involved at all. Any fix that only touches aux prompts can
  remove at most 4 FPs. The common root cause is the **max-pool itself**:
  the full-question scores on H3/H7/H15 are 0.0001 / 0.0 / 0.0001 — the
  main prompts separate perfectly. The clause/aux max-pool is what
  manufactures the fires (the v3 plan already recorded this separability
  for full-question scores; v4r's max-pool destroyed it).

## 0. Verified re-score (offline, from the v4r JSON — not a projection)

The simulation below was validated by reproducing the v4r baseline
exactly (10/16, TP/FP/FN 57/12/0, F1 0.905, court 13/16, escalates 14/16,
rating 7.7/10 by the frozen formula
0.4·exact + 0.3·micro-F1 + 0.15·court + 0.15·escalates). Variants change
only which issues fire, then re-derive kept sections (Stage 2 mapping),
courts and escalates (quantum iff maintenance fired/kept; demand iff
stridhan fired and `demand_made` is False — Cell 7 stage2 + Cell 8
patched escalates rule incl. demand).

| Variant | Exact | TP/FP/FN | micro-F1 | Court | Escalates | Rating |
|---|---|---|---|---|---|---|
| v4r baseline | 10/16 | 57/12/0 | 0.905 | 13/16 | 14/16 | 7.7 |
| (a) maintenance bar 0.30 (§4) | 13/16 | 57/6/0 | 0.950 | 14/16 | 12/16 | 8.5 |
| (a3) (a) + stridhan clause bar 0.77 — REJECTED, knife-edge (§4) | 14/16 | 57/4/0 | 0.966 | 15/16 | 12/16 | 8.9 |
| (c) evidence gates (§6) | 14/16 | 57/4/0 | 0.966 | 15/16 | 12/16 | 8.9 |
| (b) 4-option choice (§5), IF the choice is perfect | 14/16 | 57/4/0 | 0.966 | 15/16 | 12/16 | 8.9 |

Escalates falls 14→12 in every fixing variant (H7 + H15, §7) — a
scoring side-effect, not a section regression. Remaining FP after any
of (a)/(b)/(c): H6 custody ×3 + H14 GWA ×1 (other lanes).

## 1. Per-FP diagnosis

### H1 — Stridhan FP (BNS 316 + HMA 27). Mechanism: CLAUSE-MAX, not aux.

- Question: "My husband has not given me any money for three months.
  I earn fifteen thousand a month and I have two small children and no
  case filed anywhere." No gold / gift / cash-held mention anywhere.
- v4r JSON: stridhan full 0.4948 (just under the 0.50 threshold),
  **clause_max 0.7545**, final 0.7545, `fired_source: "clause"`.
  Stridhan has **no aux prompts at all** (`aux_scores` has no stridhan
  key; `aux_max` stridhan is None) — no aux mechanism exists to blame.
- Argmax clause (`fired_clause.stridhan`): **"My husband has not
  given me any money for three months."** — the money-only sentence,
  a standalone clause from `split_clauses` (Cell 7 L195–222; it is one
  sentence, so no split artefact). That clause alone scores 0.7545 on
  the stridhan prompt (L159: "gold, cash or gifts given to the wife at
  marriage that are held by the husband or his family").
- Mechanism: the model reads "has not given me any money" as "cash
  held / withheld" — "not given money" matches the prompt's "cash …
  held" loosely enough to score 0.75. The full question (0.4948) is
  correctly just under threshold; the clause-max lifts a single
  money-only clause over it. Court wrong as a consequence: HMA 27 adds
  Family Court (live [Family Court, Magistrate], GT [Magistrate]).
- Maintenance in H1 is a TRUE positive (final 0.8020, aux-driven,
  §3) — do not touch it.

### H3 — Maintenance FP (BNSS 144 + PWDVA 20). Mechanism: AUX-MAX.

- Question: "My mother gave me gold at my wedding and my in-laws kept
  it. I have never asked them to return it." No money asked.
- v4r JSON: maintenance full 0.0001, **clause_max 0.0433**,
  **aux_max 0.1218**, final 0.1218, `fired_source: "aux"`. Threshold
  0.10. Clause alone (0.0433) would NOT fire; aux alone fires it.
- Guilty prompt: **"he gives no money for me and my child"**
  (Cell 7 L185) scores **0.1218** on this gold-only question.
  But it is NOT the only guilty prompt — three of the six maintenance
  aux prompts independently clear 0.10 on H3 (see §2). The max is the
  L185 prompt; the mechanism is the whole aux pool sitting at a
  ~0.08–0.13 background level on non-money questions.
- Stridhan in H3 is a TRUE positive (full 0.9332) — do not touch it.

### H7 — Maintenance FP (BNSS 144 + PWDVA 20). Mechanism: CLAUSE-MAX, not aux.

- Question: "How do I get my daughter's birth certificate? The
  hospital did not give us one." No money mention.
- v4r JSON: maintenance full 0.0, **clause_max 0.1971**,
  **aux_max 0.0335**, final 0.1971, `fired_source: "clause"`.
  Aux (max 0.0335) would NOT fire at any threshold ≥0.10. This FP is
  entirely clause-max.
- Argmax clause (`fired_clause.maintenance`): **"The hospital did not
  give us one."** — scores 0.1971 on the maintenance prompt (L157:
  "ask for monthly money or maintenance for the wife or a child").
  Mechanism: the 2-word overlap "did not give" bleeds into "gives no
  money". A short clause with a negation + "give" is enough to clear
  the 0.10 threshold. Court wrong as a consequence: Magistrate added
  (live [Magistrate, Registrar], GT [Registrar]).
- Birth certificate in H7 is a TRUE positive (final 0.6887, clause) —
  do not touch it.

### H15 — Maintenance FP (BNSS 144 + PWDVA 20). Mechanism: AUX-MAX.

- Question: "He sold my gold without asking me. The gold was given to
  me by my parents at my wedding." No money mention.
- v4r JSON: maintenance full 0.0001, **clause_max 0.0298**,
  **aux_max 0.1269**, final 0.1269, `fired_source: "aux"`. Clause
  alone (0.0298) would NOT fire; aux alone fires it.
- Guilty prompt: **"he gives no money for me and my child"**
  (Cell 7 L185) scores **0.1269** — the same prompt as H3, the same
  margin over threshold (~0.02–0.03). Again not the only guilty prompt
  (three prompts independently clear 0.10 on H15, §2).
- Stridhan in H15 is a TRUE positive (full 0.9032) — do not touch it.

### Summary table (all values from v4r `raw_live_runs`)

| Q | FP issue | Full | Clause-max | Aux-max | Final | Fired source | Guilty mechanism |
|---|---|---|---|---|---|---|---|
| H1 | stridhan | 0.4948 | **0.7545** | — (no stridhan aux) | 0.7545 | clause | Clause "My husband has not given me any money for three months." on the stridhan prompt |
| H3 | maintenance | 0.0001 | 0.0433 | **0.1218** | 0.1218 | aux | Aux L185 "he gives no money for me and my child" (0.1218); +2 more prompts ≥0.10 (§2) |
| H7 | maintenance | 0.0 | **0.1971** | 0.0335 | 0.1971 | clause | Clause "The hospital did not give us one." on the maintenance prompt |
| H15 | maintenance | 0.0001 | 0.0298 | **0.1269** | 0.1269 | aux | Aux L185 "he gives no money for me and my child" (0.1269); +2 more prompts ≥0.10 (§2) |

## 2. Why deleting / narrowing ONE aux prompt cannot fix H3 or H15

The L185 prompt ("he gives no money for me and my child") is the
max on both H3 and H15, but the aux pool has a background floor, not
a single bad prompt. Maintenance aux scores on the two questions:

| Aux prompt (Cell 7 line) | H3 | H15 | ≥0.10? |
|---|---|---|---|
| L181 "I need money while my case is going on, but I have not filed any case yet" | 0.0968 | **0.1007** | H15 only |
| L182 "I need maintenance but I do not have my husband's salary slips…" | 0.0428 | 0.0825 | — |
| L183 "gives no money for my son's school fees" | **0.1114** | 0.0826 | H3 only |
| L184 "money for his school fees while the case goes on" | 0.0263 | 0.0520 | — |
| L185 "he gives no money for me and my child" | **0.1218** | **0.1269** | both |
| L186 "My husband has not given me any money for three months" | **0.1205** | **0.1108** | both |

- H3: THREE prompts independently clear 0.10 (L183, L185, L186).
  Deleting L185 leaves L186 at 0.1205 → still fires.
- H15: THREE prompts independently clear 0.10 (L181, L185, L186).
  Deleting L185 leaves L186 at 0.1108 → still fires.
- Deleting all three/four would gut the pool: L183 is the WINNING aux
  on H13 (0.8809, a true positive) and L181 is the winning aux on H10
  (0.6772) and H11 (0.9018) — both true positives. Deletion is
  rejected: it does not fix the FPs without surgery on true-positive
  prompts, and it leaves the clause-max FPs (H1, H7) untouched anyway.
- Note the same L185 prompt is genuinely useful elsewhere: it is the
  winning aux on K0 (0.8888) and H1 (0.8020), both true maintenance.
  Deleting it would not break K0/H1 (K0 falls back to L186 0.2956,
  still ≥0.10; H1 falls back to clause 0.7208), but it would not fix
  H3/H15 either. The prompt is not "guilty" in isolation — the
  threshold 0.10 is below the pool's background level on non-money
  questions. The fix must be a bar the background cannot clear, or a
  mechanism that does not use bare aux scores at all (§4–§6).

## 3. Guardrail check — the 10 exact questions

Exact set: K0, H2, H4, H5, H8, H9, H10, H11, H12, H13. What each fix
risks, and why it does not break them (all values v4r `raw_live_runs`):

- **K0 — MUST stay `both` (maintenance + stridhan).** Maintenance
  fires via aux L185 0.8888 (full 0.0773, clause 0.2400 — aux is the
  ONLY source above 0.10 except clause 0.24). Stridhan fires via full
  0.9064. Any fix must keep an aux path that clears its bar on K0:
  aux bar 0.30 keeps it (0.8888); evidence gate keeps it (money fact
  True — "gives no money", "not enough"; gold fact True — "gold …
  will not return it"); 4-option choice must return `both` (risk §5).
- **H10 — MUST stay `both`.** Maintenance fires via aux L181 0.6772
  (full 0.1467, clause 0.3252). Stridhan fires via clause 0.8984 /
  full 0.8929. Aux bar 0.30 keeps it (0.6772); evidence gate keeps it
  (money fact True — "gives no money for me and my child"; gold fact
  True — "has my gold"); 4-option choice must return `both` (risk §5).
- **H8 / H9 / H11 maintenance must still fire.** H8: aux L182 0.8495
  (full/clause 0.1746 — aux is essential). H9: full/clause 0.7931
  (aux irrelevant). H11: aux L181 0.9018 (full/clause 0.1432 — aux is
  essential). Aux bar 0.30 keeps all three (0.8495 / 0.7931 /
  0.9018). Evidence gate keeps all three (H8 money fact True via the
  explicit ask "I need maintenance" — the gate rule MUST count an
  explicit maintenance ask as grounding, §6; H9 "how much money …
  every month"; H11 "I need money while my case is going on").
- **H3 / H15 stridhan must still fire.** H3: full 0.9332, clause
  0.7868. H15: full 0.9032, clause 0.8446. Neither depends on aux
  (stridhan has none). Evidence gate keeps both (gold fact True).
  A stridhan clause bar would need to sit above H1's 0.7545 but below
  H3's 0.7868 — a 0.032 gap — see §4, rejected as overfit.
- **H2, H4, H5, H12, H13.** No maintenance/stridhan aux or clause
  change touches them except: H5 maintenance fires via clause 0.7467
  (aux 0.2861 — irrelevant); H13 maintenance fires via aux L183
  0.8809 (full/clause 0.1031 — aux essential, kept by bar 0.30 and by
  the evidence gate); H5 custody fires via aux 0.2189 — see the
  global-bar warning below. H2/H4/H12 have no maintenance/stridhan
  fire to preserve (aux_max 0.0820 / 0.0844 / 0.0824 — all below 0.10
  already, and below any 0.30 bar).
- **⚠️ Global-bar warning (critical): any aux/clause bar must be
  MAINTENANCE-SPECIFIC, never global.** H5 custody (true positive:
  GWA 1890 / HMGA s.6 / WELFARE) fires via custody aux 0.2189
  ("I want my daughter to stay with me", full 0.1098, clause 0.0957,
  threshold 0.20). A global aux bar of 0.30 would kill H5 custody →
  3 new FN, recall 1.000 → 0.947, exact 10/16 → worse. Same for a
  global clause bar at 0.77: it would kill H7 birth_certificate
  (true positive, clause 0.6887). Bars are per-issue only.

## 4. Mechanism (a) — minimal fix: per-source bars (maintenance only)

**Design.** Keep THRESHOLDS['maintenance'] = 0.10 for the
FULL-question score only. A clause-max or aux-max contribution counts
toward firing only if it clears its own bar of **0.30**. Equivalently
(verified identical on this set): raise the maintenance threshold to
0.30 for the pooled final. The 0.30 value sits in a wide empty band,
not on a knife edge: FP maintenance finals are 0.1218 / 0.1269 /
0.1971 (max 0.1971); true maintenance finals are 0.6772–0.9018 (min
H10 0.6772). True aux maxima that must survive: min 0.6772 (H10);
true clause maxima that must survive: min 0.7017 (H14). Implementation
is a ~5-line change in the final-score block (Cell 7 L461–471):
compute `clause_ok = best_cprob >= 0.30`, `aux_ok = aux_m >= 0.30`
for maintenance only, and exclude barred sources from `cands`.

**Verified effect (offline re-score, §0):** H3, H7, H15 become exact.
13/16, TP/FP/FN 57/6/0, micro-F1 0.950, court 14/16 (H7 fixed),
escalates 12/16 (§7), rating 8.5/10. Zero recall risk on this set.

**What it does NOT fix:** H1 stridhan (2 FP). H1's stridhan clause
0.7545 is above every true maintenance value and above H7's true
birth-certificate clause (0.6887), so no shared bar separates it.
A stridhan-only clause bar at 0.77 would fix H1 (0.7545 < 0.77) while
keeping all true stridhan clause wins (min H3 0.7868) — verified
14/16, F1 0.966 — but the margin is **0.016 below H1 and 0.017 above
H3**, i.e. pure threshold-fitting on 16 questions. **Rejected:**
do not ship the 0.77 bar. H1 is therefore **OPEN under mechanism
(a)** — see §8.

**Token-guard variant of (a) (recorded, not recommended as primary):**
maintenance aux/clause fires only if the question contains a
money token (money/month/monthly/support/salary/fees/earn/income/
maintenance); stridhan fires only if it contains gold/cash/gift.
On this set it fixes all 8 FPs (H3/H7/H15 have no money token; H1
has no gold/cash/gift token). Rejected as primary because it is a
keyword rule: it violates the Cell 7 hard rule (L123–127, "NO
fallback to keyword / phrase / rule matching" for issue picks), it
fails silently on paraphrase ("my ornaments", "he keeps my
jewellery", "what I am owed each month"), and it cannot run on the
sealed fresh-20 without the same paraphrase risk. It is a
deterministic patch, not a mechanism.

## 5. Mechanism (b) — Gemini's 4-option financial-claim choice

**⚠️ Wording verification (required by the brief):** the four labels
are as Gemini gave them, but **no option definitions were transmitted**.
`gemini-v4-consultation.md` §5 contains only the labels
(`maintenance_only` / `stridhan_only` / `both` / `neither`) and the
projection (14/16, F1 0.966). The definitions in `v5-planning-note.md`
§1 are draft reconstructions from ground truth, explicitly flagged
there as NOT a verbatim quote. There is no verbatim Gemini wording to
quote. The wordings below are therefore **Lane A drafts, derived from
the ground-truth separation on the 16, to be validated live — not
Gemini quotes.**

**Draft option wordings (one Laya `choice` node, replacing the
independent maintenance + stridhan `noul` prompts):**

- `maintenance_only` — "The question asks for periodic money or
  maintenance for the wife or a child, and does NOT ask for return of
  gold, cash or gifts given at marriage."
- `stridhan_only` — "The question asks for return of gold, cash or
  gifts given to the wife at marriage that are held by the husband or
  his family, and does NOT ask for periodic money or maintenance."
- `both` — "The question asks for BOTH: periodic money or maintenance
  AND return of gold, cash or gifts given at marriage."
- `neither` — "The question asks for NEITHER periodic money/maintenance
  NOR return of gold, cash or gifts given at marriage."

**Mapping to fired issues:** `maintenance_only` → fire maintenance
only; `stridhan_only` → fire stridhan only; `both` → fire both;
`neither` → fire neither. Other issues keep existing prompts. The
choice replaces the 0.10 (maintenance) and 0.50 (stridhan) cutoffs for
these two issues. **Cutoff:** unknown from Gemini; per Gemini §6,
choice prompts move signal into a separable 0.35–0.85 range, so the
winning-option cutoff must be set from a live dry run (start 0.35,
the bottom of that range — do not assert a number as known). If no
option clears the cutoff, fire neither (abstain) rather than falling
back to the old noul scores, or the old FPs return through the back
door.

**What happens to K0/H10 `both`:** this is the mechanism's central
risk. Both questions carry two strong simultaneous signals (K0:
stridhan full 0.9064 + maintenance aux 0.8888; H10: stridhan full
0.8929 + maintenance aux 0.6772). A 4-way choice must output `both`
on exactly these two questions and a single label on the other
fourteen. If the choice collapses to the stronger single label
(e.g. `stridhan_only` on H10 because the gold signal is stronger),
that is a NEW FN — recall 1.000 breaks, the one thing v5 must not
do. `both` behaviour is **untested**; the v5 live run must report the
choice distribution on all 16, and K0/H10 `both` is a go/no-go check
before any other result is trusted.

**Projected effect IF the choice is perfect:** H1 → `maintenance_only`
(stridhan FP gone), H3/H15 → `stridhan_only` (maintenance FP gone),
H7 → `neither` (maintenance FP gone). 14/16, 57/4/0, F1 0.966,
court 15/16, escalates 12/16 (§7), rating 8.9/10 — the same numbers
as (c), but contingent on untested choice behaviour. Build cost is
the highest of the three (new choice node, new firing logic, Stage 2
mapping change, cutoff to fit live).

## 6. Mechanism (c) — ChatGPT's per-issue evidence gates

**Design (ChatGPT §5, as recorded in `chatgpt-v4-consultation.md`
§5 and `v5-planning-note.md` §2):** an issue fires only on a stated
grounding fact, not on a bare prompt score. Same evidence-first
principle as v4.1's residence rule (ChatGPT Option D, already built
as `live-laya-colab-test-v4-1-evidence-first.ipynb`), extended to
money. Concretely for v5, two Cell 6 fact fields in the same frozen-
annotation style as `residence_claim` (Cell 7 header note 8):

- `money_fact` (bool) — True iff the question states money not given
  / asks for periodic money / states a need for money for self or
  child / asks how much money per month / **explicitly asks for
  "maintenance" by name**. Gate: maintenance fires only if
  `money_fact` is True (score threshold 0.10 still applies on top —
  gate as veto, Gemini's shape, not as the firing signal itself).
- `gold_fact` (bool) — True iff the question states gold / cash /
  gifts given at marriage held by the husband's side, or sold /
  not returned. Gate: stridhan fires only if `gold_fact` is True.

**Verified separation on the 16 (checked question by question):**
`money_fact` True exactly on {K0, H1, H5, H6, H8, H9, H10, H11, H13,
H14} — exactly the GT-maintenance set. `gold_fact` True exactly on
{K0, H3, H10, H15} — exactly the GT-stridhan set. No true positive
is gated out; all four FP questions are gated out (H1 gold False;
H3/H7/H15 money False). **Verified effect (offline re-score, §0):**
14/16, TP/FP/FN 57/4/0, micro-F1 0.966, court 15/16 (H1 fixed),
escalates 12/16 (§7), rating 8.9/10. No knife-edge anywhere: the
gates are boolean, not threshold-fitted.

**Guardrail notes.** (i) H8 is the most gate-sensitive true
positive: its money fact rests on the explicit word "maintenance"
("I need maintenance but I do not have my husband's salary slips…")
— the rule above counts an explicit ask by name as grounding; a
narrower rule ("money-not-given only") would wrongly gate H8 out.
(ii) H10's gold fact holds although demand has not yet been made
("I have not asked for it back yet") — holding, not demanding, is
the grounding fact; `demand_made` (already a Cell 6 fact) stays
separate. (iii) H13's money fact is "gives no money for my son's
school fees" — school fees count as money. (iv) The H1 money fact
is True ("not given me any money for three months") — the gate
blocks H1's *stridhan*, not its (true) maintenance.

**Honest limitation (same as `residence_claim`):** on the 16, the
facts are hand annotations, so the gate restates ground truth — it
proves the mechanism on this set but nothing about unseen questions.
For the sealed fresh-20 the facts must be model-extracted (a Laya
choice prompt per fact, as `v5-planning-note.md` §5 already schedules
for residence) or the gate cannot run there. That extraction step is
unbuilt and its error rate unmeasured. This limitation is shared by
the residence gate already shipped in v4r — it is the round's
established methodology, not a new deviation — but it must be stated,
not hidden.

## 7. Side-effect present in EVERY fixing variant: escalates 14→12/16

Fixing H7 and H15's sections removes their only escalation reason,
and the escalate expectation (True on both) is unchanged (ground
truth is not to be changed):

- **H7:** currently escalates True only via the maintenance quantum
  escalation. After the fix, kept = {births-deaths-act-1969} only,
  no quantum / demand / court escalation → escalates False vs
  expected True. This is the already-OPEN H7 escalate ambiguity
  (Cell 8 header; v4r aggregate note): a fully answerable
  birth-certificate question with escalate_expected=True and no
  named reason. The section fix makes the ambiguity visible; it
  does not create it.
- **H15:** currently escalates True via maintenance quantum. After
  the fix, kept = stridhan only and `demand_made` is True (Cell 6),
  so no demand escalation fires either → escalates False vs expected
  True. Same shape as H7: a fully answerable stridhan-only question
  with escalate_expected=True and no remaining escalation reason.
- **H3 keeps escalates True:** after the fix, kept = stridhan only
  but `demand_made` is False, so the demand escalation fires
  (Cell 8 patched rule counts demand) → escalates True, still correct.
- **H1 keeps escalates True** under (b)/(c) (maintenance still fires
  → quantum). Under (a) H1 is unchanged, so also True.
- Net: every variant that fixes H7+H15 drops escalates to 12/16
  (H2 and H4 were already wrong in v4r). The rating still rises
  (8.5–8.9 vs 7.7) because exact + F1 + court gain more than
  escalates loses. The H7/H15 escalate expectations are a question
  for the merger/parent — whether a fully-answered single-issue
  question should expect escalation — not something this lane changes.

## 8. Recommendation

**Recommend (c) ChatGPT's per-issue evidence gates for v5.
Fallback for v6: (b) Gemini's 4-option choice. Safety-net / diagnostic:
(a) maintenance per-source bar 0.30.**

Reasons for (c) as v5 primary:

1. **It is the only mechanism that fixes all 8 FPs with no
   knife-edge and no recall risk on the 16.** Verified 14/16,
   F1 0.966, court 15/16, rating 8.9/10 by offline re-score —
   identical section numbers to (b)'s best case, but deterministic
   rather than contingent on untested model behaviour.
2. **It has a built precedent in this codebase.** v4.1 implements
   exactly this pattern for residence (ChatGPT Option D); v5 extends
   the same shape to two more issues, with Cell 6 facts in the same
   frozen-annotation style as `residence_claim`. Lowest build risk
   of the three structural options.
3. **It fixes H1 structurally.** H1's stridhan FP (clause 0.7545 on a
   money-only clause) cannot be fixed by any score bar without
   overfitting (0.032 gap, §4) and cannot be fixed by any aux change
   (stridhan has no aux prompts). Only a grounding requirement — "no
   gold-held fact, no stridhan" — separates it. (b) also fixes H1,
   but only if the choice behaves (§5 risk).
4. **Its weakness is shared, stated, and scheduled.** Hand-annotated
   facts do not generalise — but neither does the residence gate
   already in v4r, and the model-extracted replacement is already
   planned (`v5-planning-note.md` §5). The v5 run on the 16 measures
   the mechanism; the sealed set measures the extraction.

Reasons (b) is the fallback, not the primary, despite being the
planning note's designated v5 mechanism:

1. **Its option definitions were never transmitted verbatim.**
   The build would start from Lane A drafts (§5), not from Gemini's
   words — the "verify wording against the consultation file" step
   the plan requires cannot be satisfied, because the file contains
   only the four labels.
2. **`both` on K0/H10 is an untested recall risk.** A single-label
   collapse creates the first FN of the run (recall < 1.000). (c)
   has no equivalent failure mode on the 16.
3. **Its cutoff is unknown** (must be fitted live in the 0.35–0.85
   range) — the same overfit class as (a)'s bars, with a bigger build.

Reasons (a) is the safety-net, not the primary: it is the cheapest
fix (one threshold/bar change, no new machinery) and it is verified
to 13/16 with zero recall risk — ship it as the v5 diagnostic
re-score, and as the fallback if the (c) build slips. But it leaves
H1 OPEN (2 FP, court still wrong on H1) and its 0.30 bar is fitted
to this set's gap, so it is a patch, not the boundary fix.

**OPEN item — H1 under (a) only:** if v5 ships (a) instead of (c),
H1 stridhan stays fired (clause 0.7545 ≥ 0.50) with BNS 316 + HMA 27
as FPs and the wrong court. Trade-off: accept 13/16, or take the
0.77 stridhan clause bar (verified 14/16) knowing the margin is
0.016/0.017 and it will very likely not survive the sealed set.
Do not silently accept a recall loss anywhere: no variant above
loses recall on the 16 (FN stays 0 in all re-scores).

**Build checklist for v5 (for the merger):** (1) add `money_fact` /
`gold_fact` to Cell 6 with the rules in §6, values per the verified
sets; (2) gate maintenance/stridhan firing on the facts (veto shape,
score threshold still applies); (3) run the (a) bar re-score offline
first as a cross-check (expect 13/16); (4) live run must report the
full per-issue firing table; (5) do NOT bundle the H6 custody or H14
GWA fixes into v5 — one mechanism per run, per the plan.

## 9. Predicted FP reduction (v5, mechanism (c))

- Financial FPs removed: **8 of 8** (H1 ×2, H3 ×2, H7 ×2, H15 ×2).
- Remaining FP: **4 of 12** — H6 custody ×3 + H14 GWA ×1 (other lanes).
- Predicted v5: **exact 14/16, TP/FP/FN 57/4/0, micro-F1 0.966,
  court 15/16, escalates 12/16, rating ≈ 8.9/10** (offline re-score;
  live run decides). If (a) ships instead: 13/16, 57/6/0, F1 0.950,
  court 14/16, escalates 12/16, rating ≈ 8.5/10, H1 OPEN.
