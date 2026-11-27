# Lane 03 — Evidence Anchors (LAYA v7.1 recall swarm)

**Owner:** Lane 03. **File owned:** `src/laya_v7_evidence.py` only.
**Status:** C4 + C5 complete. **Date:** 2026-11-27.
**Baseline (before any change):** 16-Q evidence mode 14/16, esc_bool_strict 16/16, esc_kinds_strict 10/16, rating 7.6.
**Final (after C4 + C5):** 16-Q evidence mode **14/16**, esc_bool_strict **16/16**, esc_kinds_strict **10/16**, rating **7.6** — no regression. Same two pre-existing misses (H6 pwdva-18, H14 hma-13; documented v2-vs-v4 deltas).

## What was measured (EN validation split, `data/synthetic_v7_1/validation.jsonl`)

Corpus kept changing under measurement while Lane 02 regenerated it; final
sha for every number below:
`7640d067c28abf539131dbcc891e4bdffedf62bbef4a7d66c1659bb96d07e58e` (en=235, total 500).
Audit script `/tmp/lane03_audit.py` (+ FP sweep `/tmp/lane03_fp_sweep.py`);
16-Q outputs `/tmp/lane03-after-c4-16q.json`.

| Cluster | C3 audit (same sha) | After C4 (final) |
|---|---|---|
| All 11 issues (birth_certificate, custody, divorce, dv_compensation, joint_property, maintenance, procedure, residence, restitution, stridhan, violence) | divorce 1/18, dv_comp 2/4, maintenance 3/85, procedure 8/8, residence 3/32 | **0 misses on every issue — recall 1.00** |
| child_maintenance_only | 19/20 | **0/20** |
| school_fees_fact | 9/23 | **0/23** |
| child_safety_risk | 4/14 | **0/14** |
| coercive_eviction_or_lockout | 3/13 | **0/13** |
| existing_order_enforcement | 3/7 | **0/7** |
| interim_asked | 1/3 | **0/3** |
| proceeding_pending_hma | 1/9 | **0/9** |
| divorce_asked / dv_injury_comp_asked / stridhan_claim / violence | 2/18, 2/4, 1/20, 2/20 | **0 on all** |
| in_scope | 3/222 | **3/222 (unchanged — see residuals)** |
| False positives (full fact+issue sweep, 235 EN records) | divorce FP 1 | **0 FPs total** |

## Anchors changed/added (C4, in `src/laya_v7_evidence.py`)

**Kaanoon study-sample patterns** (from `docs/kaanoon_phrasing_patterns.md`, study
sample only; eval set `data/kaanoon_eval/heldout.jsonl` never opened — contract R6):
- Stridhan: "will not give the gold (back)", "kept my Stridhan with my parents for safety" (safe-possession), jewelleries/jewelries plurals.
- Custody: "not ready to give me my son", "will not allow me to keep my son with me".
- Residence/eviction: "forced me to leave (the) house", "asked to leave my matrimony house", "not taken back", "right to stay in matrimonial home".
- Divorce/settlement: "agreed to pay 14 lakh final settlement … end the litigations" (also the reverse word order "litigations end"), "She is not agreeing for the divorce", "divorce is not essential".
- Maintenance/school: itemised school costs — "school bus transport, school dress, stationary"; "only paying her school fees excluding …".
- Violence: "habitual drinker", "fractured her hand", "ruptured my eardrum" (fractur\*/ruptur\* stems).
- Joint property: "in joint name". Third-party askers: "asking for (a) friend", "daughter-in-law / son-in-law" (mother-/father-in-law deliberately NOT added — they appear in genuine first-person clauses).
- Procedure closings: "how do I proceed legally", "time limit to appeal", "Can the court jail me", "what is the punishment".

**Corpus-paraphrase anchors** (from `validation.jsonl` surface texts + audit misses):
- Child-only: `maintenance/money/support only for my <child>`; `only for / asking only for my <child>'s school fees|tuition|food|expenses`; `only want|want only <money> for my <child>`; `only … <money> for … <child>` (exclusivity word required); `pays only my child's school fees`; minor-speaker carve-out ("I am N years old" for N 1–17 asking for support for themself); "nothing / not … for myself" is a child-only signal, not a self-ask.
- Ages: decimal years ("2.5 yrs old"), "N years M months", "N months old", `(?:yrs?|years?)` so "yrs" matches — in `_CHILD_MENTION_RE`, `_MINOR_CHILD_AGE_RE`, `_ADULT_CHILD_AGE_RE`, and the child-only age slot.
- School fees: new `_SCHOOL_FEES_RE` (school fees/tuition, schooling, "for my school", "<child>'s school|schooling|education|tuition|fees|expenses", Kaanoon itemisation, "for my education|studies|schooling"); `school_fees_fact` also fires on maintenance-asked-for-a-minor-child (corpus convention — measured 23/23 supported, 0 denied on the EN split).
- Maintenance: payment-verb targets += `school|schooling|tuition|education|fees|settlement`; support-before-verb branch ("What support can I get now?").
- Pending: "case|petition|matter|proceeding goes on" (both `_PENDING_STATE_RE` and the inline `divorce_case_ongoing`); "until the case ends" counts as pending even with no act named (narrow, corpus convention).
- Interim: "maintenance/support for now / during the case / till|until the final order".
- Existing order: "court|magistrate ordered (my|her|his)? (husband|wife|spouse) to pay"; arrears += "has not paid", "not paid since", "revis(e|ed|ing|ion)"; a revision word now overrides the enhancement exclusion (`_ORDER_REVISE_RE`).
- Child safety: "fear he/she/they will hurt my child", "shouts at our/my child", "leaves (child) alone at home", "does not give the child food", "drinks every day", "habitual drinker".
- Lockout/residence: "locked the door", "would not let me in", "asked (me) to leave (the|my) (house|home|matrimony house)", "(was) not taken back / did not take me back", "keep living in (our|my|the|this) (house|home)" (residence only), "will not leave (it|the house|the home)" (lockout).
- Negations: `_MUTUAL_NEG_RE` += "refuses to agree", "will not agree to (a) mutual", "does not agree", "without (his|her|their) consent"; `_DIVORCE_NEG_RE` += "will not agree to end (the) marriage", "divorce is not possible (now|yet)", "not agreeing for/to (a) (mutual) divorce", "divorce is not essential" (incl. "the" article).
- Divorce ask: "only about (a) divorce"; final-settlement + end-litigations conjunction (both orders).
- Lump sum: "final settlement". DV-comp: "mental harassment|harassment". Violence: bare "violence" (`violen\w*` — was only "violent").
- Stridhan: held += "(won't|will not) (give|return)", "still with (them|him|her|my in-laws|his/her family)"; demand += "will not give / won't give"; an explicit refusal beats a possession statement in the same text (both the claim computation and the `negated_issues` entry).
- DV-comp negation guard: new `_DV_COMP_NEG_RE` — "I am not asking for compensation" must not mint a claim.
- JS: live-apart paraphrase broadened to "living apart … under a court order".
- Negated-lockout mask: now handles the coordinated form "Nobody has hit me or locked me out" (was only the direct form).
- OOS terms: "income tax|tax notice|tax department", "travel abroad for (a) job", "partnership firm|dissolve (a) business|firm|company|partnership", "traffic police|driving licen[cs]e", "store sold me|damaged (phone|product|item)".
- Procedure issue: evidence now emits an 11th issue, `"procedure": forum_asked or proc_asked` (corpus schema has 11 issues; evidence emitted 10). Verified: `graph.py` `_wanted()` never looks up "procedure", so this is output-only/safe. Procedure phrasing += papers/documents, free legal help, cost-to-file, court fees.

**in_scope OOS override** (placed just before the `facts` dict, after issues are computed):
if an OOS-domain term is present AND no family-law claim exists, `in_scope` is
denied. Family-claim set = money_fact, lump_sum, existing_order, custody_claim,
residence_claim, stridhan_claim, divorce_asked, restitution_asked,
joint_property_claim, birth_cert, dv_injury_comp — **excluding bare violence**
(workplace harassment by a manager must not rescue scope). Measured: the
manager/landlord OOS FPs from the C3 audit are gone (FP sweep 0); verified zero
validation records have an OOS term AND a requested family issue, so the
override is safe on measured data.

## Two regressions caught and fixed during verification (both in the record)

1. **H13 16-Q regression (14/16 → 13/16, rating 7.6 → 7.2).** Cause: my first
   child-only branch `(money|maintenance|support) for … my <child>` had NO
   exclusivity requirement, so H13 ("…gives no money for my son's school fees")
   flipped `child_maintenance_only` to supported — and the graph gates out
   pwdva-20 whenever `child_only` is true. Fix: every child-only money branch
   now requires an exclusivity signal ("only", "pays only …"); H13 is
   `child_maintenance_only` = denied again, 16-Q back to 14/16. Pinned by a
   regression test (`test_h13_no_exclusivity_no_child_only` +
   `test_end_to_end_h13_keeps_pwdva20`).
2. **dv_compensation FP (2 records).** Cause: bare "violence" now matching made
   `violence` true on "I am not asking for compensation. I only want the
   violence at home to stop." and `_DV_COMP_RE` matched compensation+violence
   across the negated sentence. Fix: `_DV_COMP_NEG_RE` guard. FP sweep back to 0.

## C5 — unit tests (`tests/test_v7_rules.py`, class `V7EvidenceAnchorTests`)

17 tests: lockout/residence, DV-comp + negation, explicit-residence order,
Stridhan held/safe/refusal, restitution-vs-custody, decree, child-only
(decimal age, minor speaker, "nothing for myself", self-ask negative),
judicial-separation paraphrase, nobody-negation masks, mutual/divorce soft
negations, OOS override + rescue, procedure issue, H13 guard, school
fees/pending/existing-order/interim, joint-name/final-settlement/Kaanoon
custody, and 2 end-to-end `assess_v7` checks. Full suite: **66 tests, OK**
(was 49). Graph test PASS (34 sections / 66 nodes / 99 edges, 7/7 frozen
hashes intact). Prose test PASS (246 cases, 0 Fp, 15/15 adversarial mutants).

## Deliberately NOT added (observed, rejected with reason)

- "displayed/shown at the wedding" as a Stridhan held signal (provenance, not possession).
- "leaves India without any information" as restitution (disappearance alone).
- Owner-side eviction "let her out of this floor".
- Mother-in-law / father-in-law in `_THIRD_PARTY_ACTOR_RE` (genuine first-person clauses).
- `other_live` change for `hypothetical_or_joint_prop_fact_only` (no measured benefit, graph-behavior risk).

## Residuals / still unverified

- **in_scope 3/222** (recall 0.99): third-party relayed speech — "A woman at my
  workplace said, 'My husband stopped paying me anything.'" The OOS term
  ("workplace") sits inside the clause the third-party filter drops, so
  `has_oos` (computed on active text) is false and the override cannot fire.
  Fixing needs clause-level OOS tracking — a bigger change to shared clause
  logic; left for a follow-up lane, not chased here.
- **Landlord-evictor probe (invented, not a corpus record):** "My husband's
  landlord is threatening to evict us." still yields `in_scope` supported —
  the bare `evict` branch in `_RESIDENCE_ASK_RE` fires residence (landlord as
  evictor). The actual corpus landlord records (SYN-VA-0325, SYN-VA-0381) do
  not contain "evict"/"threaten" and are handled correctly. A landlord-actor
  guard on the eviction branches is a known follow-up, not measured on the
  corpus.
- **Mixed genuine-DV-plus-OOS limitation of the in_scope override:** a question
  with real DV and an OOS term but no other family claim is wrongly denied
  (bare violence does not rescue scope by design). No such record exists in
  the current validation split.
- **Workplace-violence scoping:** "My wife's manager harasses her" is correctly
  out of scope, but a genuine "my husband beats me at work" shape has no
  special handling; for Lane 08 / follow-up.
- **Corpus label noise flagged earlier (SYN-VA-0276, SYN-VA-0497):** resolved by
  corpus regeneration in the current split — 0276 is now Kannada text,
  0497's text does mention "my child", and the audit shows 0 misses on
  `money_fact` / `child_fact`. No anchor chasing was needed.
- **Not run here (needs the RTX 5050 machine / other lanes):** Brutal-230,
  Sealed Fresh-20, Kannada-8, `mode="laya"` re-runs. No GPU/torch on this VM.
  No scores were faked; every number above is a measured run on this VM.
- The `school_fees_fact` money+minor rule and the "until the case ends"
  pending rule follow the synthetic corpus's own labeling conventions
  (measured 23/23 and the single audit miss respectively); they should be
  re-checked against Lane 07's held-out Kaanoon eval, not assumed to
  generalise to real phrasing.

## Kaanoon contribution log

Study sample only (`docs/kaanoon_phrasing_patterns.md`, IDs KAN-S01–S16;
question text only, lawyers' answers not used). Patterns that changed anchors
are listed in "Anchors changed/added" above (Stridhan, custody, residence,
divorce/settlement, school itemisation, violence, joint property, third-party
askers, procedure closings). The held-out eval set was never opened (R6) and
study/eval samples are disjoint (R7). No Kaanoon content was scraped or copied.
