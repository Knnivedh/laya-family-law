# v6 Lane 2 — Escalates redesign (custody / residence / H7 / H15)

**Status: DESIGN ONLY. Offline. No browser, no Colab. No ground truth changed.
No notebook touched.** This lane designs the typed-escalation fix; the parent /
independent rater decides the two open expectations (H7, H15). Nothing in this
file changes Cell 6.

**Starting point — v4r LIVE (2026-11-27 ~00:19 IST):** exact 10/16, micro-F1
0.905, court 13/16, escalates **14/16** (wrong: H2, H4). **v5 (built, NOT live
measured)** predicts exact 16/16, court 16/16, escalates **12/16** — H2/H4
still wrong, and H7/H15 newly wrong because fixing their false maintenance
sections removes their only escalation reason under current typed scoring
(quantum / court / demand).

**Sources read:** `v5-precision-report.md` §6–§7; v4r live JSON
(`browser-download-20261126T185447…-v4r-residence-only.json`, `raw_live_runs`
+ `per_question`); v5 notebook `live-laya-colab-test-v5-precision.ipynb`
Cell 6 (all 16 `escalate_expected` values) and Cell 8 (scoring line) and
Cell 7 `stage2()` (escalation generation); `laya-10-10-gate-definition.md`
§1 G9, §5.

**Headline finding — the v4r H7/H15 "True" was an artefact.** In v4r, H7 and
H15 read `escalates_live=True` only because the quantum boilerplate attached
to a *false* maintenance fire (H7 maintenance full 0.0, clause-max 0.1971;
H15 maintenance full 0.0001, aux 0.1269). Cell 7 `stage2()` appends quantum
whenever `'maintenance' in fired or maint_kept`. Once v5 gates that false
fire out, the quantum — and with it the only reason — disappears. The v5
report §6 is right: do NOT re-attach the quantum boilerplate. The question
is whether a *genuine, content-correct* reason exists for each of H7/H15,
and what kinds cover H2/H4. Answer: yes, for all four — §1 and §2.

**Predicted outcome under this design: escalates 16/16** (per-question table
§4.4), which with v5's predicted 16/16 sections and 16/16 courts gives
10.0 by either rating formula on the current 16 — **capped at 9.0** until
G2 (fresh), G3 (Kannada), G12 (prose) and G15 (confirmation re-run) pass.
G9 alone does not make 10/10. See §4.5.

---

## 0. What "escalates" means — the definition this design adopts

The flag needs a stated meaning before kinds can be judged. This design
adopts:

> **escalates = True iff the correct answer names at least one concrete
> thing the bot cannot decide or complete itself, which must go to a human
> (lawyer / court / authority), and the system names that thing.**

Under this definition the *kinds* are the content; the boolean is just
"≥ 1 kind present". Two consequences, stated honestly:

1. **The expectation column as annotated is near-constant** — 15 True / 1
   False (only H12, out of scope, is False). Every in-scope question with a
   non-empty kept set expects True. That means the boolean barely
   discriminates: any design that fires on every non-empty kept set passes.
   The real test is therefore in the *kinds* — each must name a genuine,
   question-grounded gap, not a boilerplate. A kind that could attach to
   anything (e.g. a catch-all "needs human review") would make the metric
   vacuous, so no such kind is proposed (§1, rule 4).
2. **The alternative definition is also coherent:** "escalates only when the
   bot cannot decide an amount, a court, or a first demand" (i.e. only
   quantum / court / demand count). Under *that* definition H7 and H15
   should be False. The choice between definitions is the parent /
   independent rater's, not this lane's — §2 argues both sides and
   recommends, and §2.3 shows the 16/16 holds under either decision *provided
   the kinds and the expectations are decided consistently together*.
   The failure mode to avoid is deciding them inconsistently (keeping
   `True` with no kind, or shipping a kind against a flipped expectation).

## 1. Design — typed escalations for custody-only (H2) and residence-only (H4)

### 1.1 Design rules (all new kinds must satisfy all five)

1. **Trigger on kept sections and/or frozen Cell 6 facts only — never on
   raw scores, never on pre-gate fired state, never on a question ID.**
   (Gate rule 4: no per-question special cases. A trigger written as a
   section id is an issue rule, not a question rule — same shape as the
   existing `demand` kind and the residence/money/custody gates.)
2. **Each kind names one concrete thing the bot cannot do**, and the text
   says what happens instead (who it goes to, what must not be stated).
   No boilerplate: a kind whose text is true of every question is rejected.
3. **Each kind must be falsifiable on this set**: there must be questions
   where it does not fire. (Checked per kind below.)
4. **No catch-all kind.** In particular there is NO generic `review` kind
   ("fully answerable but no named reason"). H7/H15 are handled by two
   specific kinds (§2), not by a generic one — a generic kind would pass
   the 16 and teach nothing, and would fire on any future question.
5. **A gated-out issue must never escalate.** H6's custody is gated out
   in v5 and H2's residence was gated out in v4r; neither may produce a
   custody/residence escalation. This forces the trigger choice in §1.3.

### 1.2 The four new kinds

| Kind | Trigger (kept / facts) | Exact text (what the system says) | What it does instead of a bare True/False |
|---|---|---|---|
| `custody` | `kept ∩ {gwa-1890, hma-26} ≠ ∅` | "Custody: who the child stays with is a welfare decision for the Family Court — the bot names the route ({route}) but does not say who gets the child. Escalate for interim custody and the welfare assessment. If either parent has said they will take the child away, that needs urgent human help." ({route} = "HMA s.26 (proceeding pending)" if `hma-26` in kept else "GWA 1890".) | Hands the who-gets-the-child question to a lawyer / Family Court filing. The bot must never state an outcome ("you will get the child"). |
| `residence` | `'residence' in fired` (post-gate fired issues — see §1.3) | "Residence: the bot names PWDVA 17–19 but cannot restore entry to the house — a Magistrate's residence order is needed (the house being in the husband's name does not remove the right). Escalate for filing the residence application and for immediate help re-entering." | Hands filing/enforcement to a lawyer / Magistrate. Must never advise forcing entry, and must never call residence "tenancy rights" (gate §5 prose-forbidden #4). |
| `recovery` | `kept ∩ {hma-27, bns-316} ≠ ∅` AND `facts['demand_made'] is True` | "Stridhan recovery: sold or withheld gold cannot be recovered or valued by the bot — escalate to a lawyer for valuation, a police complaint under BNS s.316 and civil recovery under HMA s.27." | Hands valuation + complaint + recovery to a lawyer. The bot must never value the gold or say it will be returned. |
| `procedure` | `'births-deaths-act-1969' in kept` | "Birth certificate: the exact procedure depends on facts not stated (date of birth, any delay, whether the hospital will issue) and requires applying in person to the Registrar. Escalate for human follow-up with the hospital / Registrar if issuance is refused or delayed." | Hands the application / hospital follow-up to a human. The text asserts no unstated fact (no delay is claimed to exist) and never places the certificate under HMA (gate §5 prose-forbidden #6). |

### 1.3 Why the triggers are written this way — the H5 / PWDVA 18 case

The residence trigger is deliberately **`'residence' in fired` (post-gate)**,
not `kept ∩ {pwdva-17, pwdva-18, pwdva-19}`. The two differ on exactly one
question, and the difference decides correctness:

- **H5** keeps PWDVA 18 via the *violence-only* branch in `stage2()` (`if
  'violence' in fired and 'residence' not in fired: kept_pre.add('pwdva-18')`)
  — a protection order, not a residence order. H5 has no eviction, no
  lockout, no "stay in the house" claim (`residence_claim=False`). A
  kept-set trigger would attach the re-entry text to H5, where it is
  content-wrong. The fired trigger does not fire on H5 (residence never
  fired there), which is correct — H5 already escalates via quantum +
  custody.
- Conversely the fired trigger is safe against gated-out issues (rule 5):
  the residence/custody gates in Cell 7 force `final = 0.0` *before* the
  firing loop, so a gated-out issue is never in `fired`. H2's residence
  (R0 full 0.8247 in v4r, gated by `residence_claim=False`) therefore
  cannot produce a residence escalation, and H6's gated-out custody cannot
  produce a custody escalation.

General rule for all kinds: **triggers use post-gate `fired` and/or `kept`,
whichever the kind's meaning requires; never raw scores or pre-gate state.**
For custody, `kept ∩ {gwa-1890, hma-26}` and post-gate `custody in fired`
are equivalent on the 16 (custody fired ⟹ its primary is kept; no drop
rule removes GWA/HMA 26) — the kept form is used because the kind is about
the kept answer. For residence the fired form is required, per H5 above.
For consistency the spec also moves `quantum` to kept-only
(`maint_kept`, i.e. `kept ∩ {bnss-144, pwdva-20, hma-24, hma-25}`) and
`demand` to `('stridhan' in fired)` — both behaviour-preserving on the 16
(maintenance/stridhan fired ⟺ their sections kept; no drop rule removes
them), stated here so the trigger rule is uniform. See §4.1.

### 1.4 H2 and H4 under this design

- **H2** — "Who will get my six year old son? My husband says as the father
  he will take him away from me." v5 kept: {GWA 1890, HMGA s.6, WELFARE}.
  `custody` fires (GWA 1890 kept). **Expected value: True.** The bot's
  answer names the Act and the court but cannot answer the question as
  asked — *who gets the child* is a welfare decision only a court can
  make, and the father's stated intention to take the child makes human
  review urgent, not optional. The static text carries that urgency as a
  conditional clause ("If either parent has said they will take the child
  away…"), so no new fact field is needed. (Optional enrichment, not
  load-bearing: a frozen Cell 6 fact `removal_threat` — True iff the
  question states a parent threatens to take the child away; True only on
  H2 in this set — would let the text assert the urgency unconditionally
  for H2. Not required for 16/16; do not add it unless the parent wants
  the urgency machine-readable.)
- **H4** — "They changed the lock and I cannot enter my house. The house is
  in my husband's name." v5 kept: {PWDVA 17, PWDVA 18, PWDVA 19}.
  `residence` fires (residence fired, post-gate). **Expected value: True.**
  The bot names the sections but cannot restore entry: only a Magistrate's
  residence order does that, and the ownership point (husband's name) is
  exactly the legal distinction a human must handle — the right to reside
  does not depend on ownership. A bare True/False here would hide that the
  next step is a filing, not information.

### 1.5 Existing kinds — restated, unchanged in meaning

| Kind | Trigger (current Cell 7) | Fires on (v5) | Note |
|---|---|---|---|
| `quantum` | maintenance fired OR maintenance kept → **v6: kept-only** (§1.3) | K0, H1, H5, H6, H8, H9, H10, H11, H13, H14 | Genuine everywhere it fires: the husband's income / the amount is unstated in all ten. Minor content defect (not score-affecting): the text also says "school fees unknown" on questions with no school fees (H1, H8, H9, H11). Recommend trimming the static text to income-only and mentioning school fees only via the `fact` text — see §5. |
| `court` | `court_source == 'fallback-escalate'` (kept empty + in scope) | none on the 16 | Dormant on this set, correctly: no in-scope question has empty kept. Keep — it is the kind that covers a silent in-scope question on the fresh set. |
| `demand` | stridhan fired AND `demand_made is False` → **v6: `demand_made is not True`** (§4.1, zero effect on the 16) | H3, H10 | Genuine: the first step is a written demand before BNS 316 is re-evaluated. Mutually exclusive with `recovery` by construction. |
| `fact` | accompanies quantum (ask income / school-fee amount / whereabouts) | same ten as quantum | Informational only — **never in the scoring set**. It is a follow-up question list, not an escalation reason. Keep it out of `esc_live`. |

### 1.6 Falsifiability check (rule 3)

Each new kind does not fire somewhere it must not: `custody` does not fire
on H1/H3/H4/H6/H7/H8/H9/H10/H11/H12/H13/H15 (no custody kept);
`residence` does not fire on H5 (violence-only PWDVA 18, §1.3) nor on any
non-residence question; `recovery` does not fire on H3/H10 (demand not yet
made — `demand` fires instead); `procedure` fires only on H7. H12 (kept
empty) fires no kind at all — the guard that must hold on every run (§4.3).

### 1.7 Optional, NOT load-bearing: a `safety` kind

Trigger `facts['violence'] is True`; text: "Safety: violence is stated —
escalate urgently for immediate safety help and a protection order under
PWDVA s.18; do not treat this as information-only." Fires on H5, H13 only
in this set, both already True via quantum, so it changes no score. It is
recommended (violence questions genuinely need urgent human help, and the
fresh set contains a violence + residence + school-fees question) but it is
**not required for 16/16** and is not in the §4 spec's required set. If the
parent accepts it, add `'safety'` to the Cell 8 set in the same edit;
if not, nothing else changes.

## 2. H7 and H15 — both sides, then recommendations

### 2.1 H7 — birth certificate. Kept (v5): {Births and Deaths Act 1969} only. Expected: True (OPEN since v3).

Question: "How do I get my daughter's birth certificate? The hospital did not
give us one."

**Case for True (keep):**
- The bot can name the Act and the authority (Registrar) but cannot obtain
  the certificate: the user must apply in person with documents, and the
  procedure branches on facts not stated — the child's date of birth, how
  long ago the birth was (delayed registration has a different procedure),
  and whether the hospital will issue at all. A hospital that "did not
  give us one" is a non-cooperative institution; follow-up with the
  hospital / Registrar may need a human.
- The `procedure` kind (§1.2) captures exactly this, without inventing a
  delay or any other unstated fact — its text says the procedure *depends
  on* facts not stated.
- The fresh set contains a birth-certificate question (gate §4): under
  keep-True, that question is expected to escalate the same way, which is
  consistent with treating birth-certificate answers as procedure-plus-
  human-follow-up rather than pure information.

**Case for False (change expectation):**
- On its face this is the most fully answerable question in the set: one
  section, one authority, no amount to decide, no opposing party, no
  court discretion, no missing document the bot must ask for. If
  "escalates" means "the bot cannot decide something material", there is
  nothing material undecided here.
- The original True looks like the default annotation (15/16 True) rather
  than a per-question judgement, and its v4r live True was an artefact of
  the false maintenance fire (§0). Keeping True by inventing a
  "procedure depends on unstated facts" reason risks being boilerplate in
  disguise: *every* answer's next step depends on some unstated fact.
- The honest counter to the "delayed registration" point: nothing in the
  question states a delay. If the child is a newborn, the procedure is
  trivial (hospital issues / apply within 21 days) and no human is needed.

**Recommendation — H7: KEEP `escalate_expected=True`, with the new
`procedure` kind.** The keep is defensible and the weaker of the two keeps
in this report: it rests on the hospital's non-issuance plus genuinely
branching procedure, and the `procedure` text is careful not to assert
unstated facts. But it is borderline, and the False case is legitimate.
**This is the one expectation where a rater could reasonably go the other
way.** If the parent / independent rater flips H7 to False, drop the
`procedure` kind (H7 then reads False) — escalates is still 16/16 (§2.3).
Do NOT keep True and ship no kind, and do NOT ship the kind against a
flipped expectation.

### 2.2 H15 — stridhan sold. Kept (v5): {BNS 316, HMA 27}. Expected: True.

Question: "He sold my gold without asking me. The gold was given to me by my
parents at my wedding." Facts: `demand_made=True`.

**Case for True (keep):**
- The gold was *sold* — this is not a "ask for it back" case (that is H3,
  covered by `demand`). Recovery of sold property needs valuation (what
  was it worth when sold?), a police complaint under BNS 316, and civil
  recovery under HMA 27. The bot cannot value sold gold, cannot file a
  complaint, and cannot say the gold or its value will be recovered.
  A criminal provision (BNS 316) is inherently a human/lawyer step.
- The `recovery` kind (§1.2) captures exactly this, and it is mutually
  exclusive with `demand` (demand not made → `demand`; demand made →
  `recovery`), so the two stridhan branches are cleanly separated.
- Unlike H7, the reason here is stated in the question itself ("sold"),
  not in unstated facts. The escalation is grounded in the question text.

**Case for False (change expectation):**
- The sections are fully determined (BNS 316 + HMA 27), both courts are
  named (Family Court + Magistrate), and the demand step is already done
  (`demand_made=True`), so under the narrow quantum/court/demand
  definition there is nothing left undecided — the classification task is
  complete.
- The v4r live True was, like H7's, an artefact of the false maintenance
  fire (§0), so the True has never yet been earned by a genuine reason.

**Recommendation — H15: KEEP `escalate_expected=True`, with the new
`recovery` kind. This keep is strong** — materially stronger than H7's.
The False case is coherent only under the narrow definition (§0), and
adopting that definition would also force re-examining H2/H4 (which
everyone agrees are True). If the rater nevertheless flips H15 to False,
drop the `recovery` kind for the `demand_made=True` branch only (K0 stays
True via quantum/custody/residence) — escalates is still 16/16 (§2.3).

### 2.3 What follows from each rater decision (all paths reach 16/16)

| Rater decision | Kinds shipped | H7 live / exp | H15 live / exp | Escalates |
|---|---|---|---|---|
| Keep both True (recommended) | custody, residence, recovery, procedure | True / True | True / True | **16/16** |
| Flip H7 → False only | custody, residence, recovery (no procedure) | False / False | True / True | **16/16** |
| Flip H15 → False only | custody, residence, procedure (no recovery) | True / True | False / False | **16/16** |
| Flip both → False | custody, residence only | False / False | False / False | **16/16** |

The 16/16 does not depend on the rater agreeing with this lane; it depends
on kinds and expectations being decided **consistently together**. Note the
v5 report §6 arithmetic ("flip H7/H15 to False → 14/16") assumed no H2/H4
fix; with the §1 kinds, flipping them costs nothing.

**Neither expectation is changed in this file and neither may be changed by
the tuning lane** (gate §6 rule 1; v5 report §6). The decisions above are
RECOMMENDATIONS for the parent / independent rater.

## 3. Audit — the whole `escalate_expected` column (all 16)

Kept sets are the **v5 predicted** kept sets (v4r kept minus the vetoed FPs;
v5 report §5). "Current kinds" = kinds under v5 with the *current* Cell 8
scoring set {quantum, court, demand}. "Well-defined?" judges the
*expectation*, not the system: is True/False plainly the right value for
this question?

| Q | Question (short) | v5 kept | Current kinds (v5, old scoring) | Live | Exp. | Well-defined? |
|---|---|---|---|---|---|---|
| K0 | Multi-issue: no money, gold held, thrown out, who gets daughter | BNSS 144, PWDVA 20, GWA 1890, HMGA s.6, WELFARE, HMA 27, BNS 316, PWDVA 17/18/19 | quantum, fact | True | True | **Yes.** Amount unknown (husband's income, school fees) — quantum is a genuine, named reason. (v6 also: custody, residence, recovery.) |
| H1 | No money 3 months; earns ₹15k; two small children; no case | BNSS 144, PWDVA 20 | quantum, fact | True | True | **Yes.** Amount unknown — husband's income unstated. (Her ₹15k is stated; quantum concerns his contribution / the amount.) |
| H2 | Who will get my 6-yr-old son? Father says he will take him away | GWA 1890, HMGA s.6, WELFARE | — (none) | False | True | **Expectation yes, scoring no.** True is plainly right (who gets the child needs a court); no kind covers custody-only. Fixed by `custody` (§1.4). |
| H3 | Gold kept by in-laws; never asked for return | HMA 27, BNS 316 | demand | True | True | **Yes.** Demand not made — genuine, named reason; the `demand` kind exists precisely for this. |
| H4 | Lock changed, cannot enter house; house in husband's name | PWDVA 17, PWDVA 18, PWDVA 19 | — (none) | False | True | **Expectation yes, scoring no.** True is plainly right (only a Magistrate's order restores entry); no kind covers residence-only. Fixed by `residence` (§1.4). |
| H5 | Wants divorce; beaten; needs monthly money; daughter to stay with her | HMA 13, BNSS 144, PWDVA 20, PWDVA 18, GWA 1890, HMGA s.6, WELFARE | quantum, fact | True | True | **Yes.** Amount unknown (quantum). (v6 also: custody. Residence kind correctly does NOT fire — PWDVA 18 here is violence-only, §1.3.) |
| H6 | Does NOT want divorce; monthly money; stay in house with daughter | BNSS 144, PWDVA 20, PWDVA 17/18/19 | quantum, fact | True | True | **Yes.** Amount unknown (quantum). (v6 also: residence. Custody kind correctly does NOT fire — custody gated out in v5.) |
| H7 | How to get daughter's birth certificate? Hospital did not give one | Births and Deaths Act 1969 | — (none) | False | True | **NO — genuinely ambiguous.** Fully answerable on its face; no named reason. See §2.1. |
| H8 | Needs maintenance; no salary slips; husband's income unknown | BNSS 144, PWDVA 20 | quantum, fact | True | True | **Yes — the clearest quantum case.** Income unknown is the question's point. |
| H9 | How much money can I get every month? | BNSS 144, PWDVA 20 | quantum, fact | True | True | **Yes.** Quantum explicitly asked; amount must not be invented. |
| H10 | Gold held, not yet asked back; gives no money for her + child | HMA 27, BNS 316, BNSS 144, PWDVA 20 | demand, quantum, fact | True | True | **Yes — two independent reasons.** Demand not made + amount unknown. |
| H11 | Needs money while case going on; no case filed yet | BNSS 144, PWDVA 20 | quantum, fact | True | True | **Yes.** Amount unknown (quantum). The no-proceeding subtlety (HMA 24 unavailable) is a section matter, not an escalation matter. |
| H12 | Brother/sister fight over father's ancestral house; who owns it? | (none) | — (none) | False | False | **Yes — the only well-defined False.** Out of scope, nothing kept, nothing to escalate to. Guard: no kind may ever fire on empty kept (§4.3). |
| H13 | Beats her, throws her out, no money for son's school fees | PWDVA 17/18/19, PWDVA 20, BNSS 144 | quantum, fact | True | True | **Yes.** School-fee amount + husband's income unknown — quantum text actually fits here. (v6 also: residence.) |
| H14 | Divorce case pending in Family Court; son to stay with her; school-fee money | HMA 13, HMA 26, HMGA s.6, WELFARE, HMA 24, BNSS 144, PWDVA 20 | quantum, fact | True | True | **Yes.** Interim amount / school-fee amount unknown (quantum). (v6 also: custody via HMA 26.) |
| H15 | He sold my gold without asking me; parents gave it at wedding | BNS 316, HMA 27 | — (none; demand_made=True so no `demand`) | False | True | **NO — genuinely ambiguous, but the True case is strong.** Sold property needs recovery/valuation/complaint. See §2.2. |

**Other ambiguous expectations: none.** Apart from H7 and H15, every
expectation is well-defined and correct as annotated. The H2/H4 misses are
a *scoring* gap (missing kinds), not an expectation problem — do not "fix"
them by editing expectations. The near-constant column (15 True / 1 False)
is itself a finding (§0.1): for the fresh-20 freeze, each question's
escalate expectation should be annotated with a **named reason** (which
kind), not just True/False, so kinds can be checked against reasons rather
than booleans (§5).

## 4. Cell 8 spec for v6 (exact change)

Two sites change. **Cell 8 alone cannot fix this**: Cell 8 only scores the
kinds present in `escalations_typed`; the new kinds must first be generated
in Cell 7 `stage2()`. Both edits below are required, and both are small.

### 4.1 Cell 7 `stage2()` — generate the new kinds

Location: in `stage2()`, immediately after the existing quantum block and
before `return kept, dropped, esc_typed, gated_out, candidates_before_gate`.
(Existing block, for anchor: `maint_kept = bool(kept & {'bnss-144',
'pwdva-20', 'hma-24', 'hma-25'})` followed by the quantum + fact appends.)

```python
    # --- v6 typed escalations: custody / residence / recovery / procedure ---
    # Triggers are kept sections and/or frozen Cell 6 facts ONLY — never raw
    # scores, never pre-gate fired state, never a question id. Each kind names
    # one concrete thing the bot cannot decide or complete itself.
    # Residence uses post-gate 'residence' in fired (NOT kept PWDVA 17/18/19):
    # H5 keeps PWDVA 18 via the violence-only branch and its residence text
    # would be content-wrong there. Custody uses kept (fired <=> kept here).
    if kept & {'gwa-1890', 'hma-26'}:
        _route = 'HMA s.26 (proceeding pending)' if 'hma-26' in kept else 'GWA 1890'
        esc_typed.append({'kind': 'custody', 'text': (
            f"Custody: who the child stays with is a welfare decision for the Family Court "
            f"-- the bot names the route ({_route}) but does not say who gets the child. "
            f"Escalate for interim custody and the welfare assessment. "
            f"If either parent has said they will take the child away, that needs urgent human help.")})
    if 'residence' in fired:
        esc_typed.append({'kind': 'residence', 'text': (
            "Residence: the bot names PWDVA 17-19 but cannot restore entry to the house "
            "-- a Magistrate's residence order is needed (the house being in the husband's name "
            "does not remove the right). Escalate for filing the residence application "
            "and for immediate help re-entering.")})
    if kept & {'hma-27', 'bns-316'} and facts['demand_made'] is True:
        # demand_made False is covered by the 'demand' kind above; this is the
        # sold / already-demanded branch: recovery, not a first demand.
        esc_typed.append({'kind': 'recovery', 'text': (
            "Stridhan recovery: sold or withheld gold cannot be recovered or valued by the bot "
            "-- escalate to a lawyer for valuation, a police complaint under BNS s.316 "
            "and civil recovery under HMA s.27.")})
    if 'births-deaths-act-1969' in kept:
        esc_typed.append({'kind': 'procedure', 'text': (
            "Birth certificate: the exact procedure depends on facts not stated (date of birth, "
            "any delay, whether the hospital will issue) and requires applying in person to the "
            "Registrar. Escalate for human follow-up with the hospital / Registrar "
            "if issuance is refused or delayed.")})
```

Two accompanying Cell 7 cleanups (behaviour-preserving on the 16;
recommended, separable — either may be deferred without affecting 16/16):

```python
    # (a) quantum trigger: kept-only, for uniformity with the new kinds.
    #     Old:  if 'maintenance' in fired or maint_kept:
    #     New:  if maint_kept:
    #     No-op on the 16: maintenance fired <=> its sections kept (no drop rule removes them).
    # (b) demand trigger: 'demand_made is False' -> 'demand_made is not True'.
    #     No-op on the 16 (stridhan questions there are True/False only). Generalisation fix:
    #     if demand status is unstated (None), the safe first step is still a written demand,
    #     and BNS 316 must not sit in the answer with no demand advice attached.
    #     'demand' and 'recovery' stay mutually exclusive by construction.
```

If the parent accepts the optional `safety` kind (§1.7), append in the same
block: `if facts['violence'] is True: esc_typed.append({'kind': 'safety',
'text': "Safety: violence is stated -- escalate urgently for immediate
safety help and a protection order under PWDVA s.18; do not treat this as
information-only."})` and add `'safety'` to the Cell 8 set.

### 4.2 Cell 8 — scoring change (the exact line)

Current line (Cell 8, per-question loop):

```python
    esc_live = bool(kinds & {'quantum', 'court', 'demand'})  # PATCHED 2026-11-26: include demand so H3 demand-only reads escalates=True
```

New line:

```python
    esc_live = bool(kinds & {'quantum', 'court', 'demand', 'custody', 'residence', 'recovery', 'procedure'})  # v6: custody/residence/recovery/procedure kinds (Lane 2); 'fact' deliberately excluded (follow-up questions, not an escalation reason)
```

Keep unchanged: `esc_live_any = bool(kinds)` (diagnostic, any typed kind
incl. `fact`) and `esc_live_bool = bool(r.get('escalations'))` (diagnostic,
v1 rule). `escalates_correct` stays `esc_live == t['escalate_expected']`.
No change to `escalate_expected` in Cell 6.

Cell 8 header comment must be updated (it currently says H2/H3/H7/H15 read
False under the primary rule and H7 is OPEN): replace with a note recording
the v6 kinds, the rater's H7/H15 decisions, and that `fact` is excluded.
Likewise the aggregate string `'h7_escalate_ambiguity'` (currently "OPEN …
Resolve the expectation before re-scoring") must be replaced by a resolution
note, e.g. `'h7_h15_escalate_resolution': 'H7/H15 expectations kept True by
rater decision <date>; procedure/recovery kinds added (Lane 2).'` — or the
flipped variant if the rater decides otherwise. The MD footer line "H7
escalate ambiguity is OPEN" must be updated the same way, and the print line
"esc = escalates correctly (typed quantum/court flag)" becomes "(typed
escalation kinds)".

### 4.3 Cell 8 — new diagnostics / guards (add to the aggregate + rows)

- Per-question row: add `'escalation_kinds': sorted(kinds)` so the audit
  table (§3) is reproducible from the run JSON without re-reading Cell 7.
- Aggregate: add `'escalates_on_empty_kept': <count of questions with no
  kept sections but ≥1 escalation kind>` — **must be 0** (H12 guard; a
  kind firing on empty kept is a design bug, not a score quirk).
- Aggregate: add `'escalation_kinds_by_question': {id: sorted(kinds)}` (or
  rely on the per-question rows) so the v6 run file shows which kind
  carried each True.
- Keep the H12 check (`h12_stays_empty` requires `escalates_live is False`)
  as-is; it now also covers the new kinds.

### 4.4 Predicted per-question escalates under this design (target 16/16)

Kinds are those generated by §4.1 on the v5 predicted kept sets. `fact`
is listed for completeness but is NOT scored.

| Q | v5 kept (summary) | Kinds firing (v6) | Live | Exp. | Correct |
|---|---|---|---|---|---|
| K0 | 10 sections | quantum, fact, custody, residence, recovery | True | True | ✓ |
| H1 | BNSS 144, PWDVA 20 | quantum, fact | True | True | ✓ |
| H2 | GWA 1890, HMGA s.6, WELFARE | **custody** | True | True | ✓ |
| H3 | HMA 27, BNS 316 | demand | True | True | ✓ |
| H4 | PWDVA 17/18/19 | **residence** | True | True | ✓ |
| H5 | HMA 13, BNSS 144, PWDVA 20, PWDVA 18, GWA, HMGA s.6, WELFARE | quantum, fact, custody (residence correctly absent, §1.3) | True | True | ✓ |
| H6 | BNSS 144, PWDVA 20, PWDVA 17/18/19 | quantum, fact, residence (custody correctly absent — gated out) | True | True | ✓ |
| H7 | Births and Deaths Act 1969 | **procedure** | True | True | ✓ |
| H8 | BNSS 144, PWDVA 20 | quantum, fact | True | True | ✓ |
| H9 | BNSS 144, PWDVA 20 | quantum, fact | True | True | ✓ |
| H10 | HMA 27, BNS 316, BNSS 144, PWDVA 20 | demand, quantum, fact | True | True | ✓ |
| H11 | BNSS 144, PWDVA 20 | quantum, fact | True | True | ✓ |
| H12 | (none) | — (none) | False | False | ✓ |
| H13 | PWDVA 17/18/19/20, BNSS 144 | quantum, fact, residence | True | True | ✓ |
| H14 | HMA 13, HMA 26, HMGA s.6, WELFARE, HMA 24, BNSS 144, PWDVA 20 | quantum, fact, custody | True | True | ✓ |
| H15 | BNS 316, HMA 27 | **recovery** | True | True | ✓ |

**Escalates 16/16.** Changes vs v5's predicted 12/16: H2 (+custody),
H4 (+residence), H7 (+procedure), H15 (+recovery). No other question's
value changes; no question flips from correct to wrong. The four new kinds
are the entire delta — each fires on exactly the question(s) it was
designed for, plus already-correct questions where it is redundant (K0,
H5, H6, H13, H14).

### 4.5 Rating implication (do not over-claim)

With v5's predicted 16/16 exact, 1.000 micro-F1, 16/16 court and this
design's 16/16 escalates: **10.0 by the v5-report formula
(0.4·exact + 0.3·micro-F1 + 0.15·court + 0.15·escalates) and 10.0 by the
gate §2 formula** on the current 16. But the gate caps apply: prose not
measured (≤ 9.0), fresh set not run (≤ 9.0), Kannada not run (≤ 9.0), no
confirmation re-run (≤ 9.0). So the honest statement after a passing v6
live run is **"G9 passes; current-16 rating 10.0 by formula, capped at
9.0"** — not "10/10". G9 passing is necessary, not sufficient.

## 5. Risks, limits, and open items for the parent

1. **H7/H15 decisions needed before the v6 run** (parent / independent
   rater, §2.3). The notebook must not be built with both the kinds and
   the old expectations left inconsistent. Recommended: keep both True.
2. **Fresh-set annotation.** When the fresh 16 are frozen, annotate each
   question's escalate expectation with a **named reason (kind)**, not just
   True/False — otherwise the kinds cannot be checked against reasons.
   The fresh set contains a birth-certificate question and a custody
   question; under this design both are expected True via `procedure` /
   `custody` respectively. If the fresh rater instead expects False for
   either, that is a definitional dispute to resolve at freeze time, not
   after the run.
3. **Single-occurrence kinds.** `procedure` is exercised once on the 16
   (H7) and `recovery` twice (K0, H15). Their generalisation rests on the
   fresh set, not on this set. `custody` (4 questions) and `residence`
   (4 questions) are better exercised.
4. **Quantum text over-claim** (§1.5): "school fees unknown" appears on
   questions with no school fees. Content defect only (kind still fires
   correctly); recommend trimming the static text to income-only.
5. **Demand `None` edge** (§4.1b): a future stridhan question with
   `demand_made=None` gets `demand` under the proposed `is not True`
   trigger. That is a deliberate generalisation choice, zero effect on
   the 16; the parent may defer it, in which case such a question gets
   neither `demand` nor `recovery` and would need a rater decision.
6. **Same hand-annotation caveat as all v5 gates:** the new kinds trigger
   on kept sections (model output) plus the frozen `demand_made` fact —
   the only hand-annotated input is `demand_made`, which already exists.
   No new fact field is required by the primary spec (the optional
   `removal_threat` in §1.4 is enrichment only). The kinds themselves are
   general rules, not per-question branches, so they comply with gate
   rule 4 — but like every v5 mechanism they are validated on n=16 until
   the fresh set runs.
7. **What this lane did NOT do:** no notebook edits, no GT changes, no
   live run, no browser work. The v6 live run must still confirm the v5
   predicted kept sets reproduce (especially H5 custody aux 0.2189,
   margin 0.0189 — v5 report §7.6); if a kept set differs, the kinds
   table in §4.4 must be re-derived from the actual kept sets before the
   escalates score is quoted.

---

*Lane 2 (escalates redesign), v6 deep-dive. Offline only. Files read:
`v5-precision-report.md`, v4r live JSON
(`browser-download-20261126T185447.300061282Z-0-live-laya-colab-results-v4r-residence-only.json`),
v5 notebook Cells 6/7/8 (`live-laya-colab-test-v5-precision.ipynb`),
`laya-10-10-gate-definition.md`. No ground truth changed; no notebook
edited.*
