# Lane 01 — Diagnosis: why unseen questions fail (validation-500 evidence-mode run)

- **Lane:** 01 Diagnosis (analysis only)
- **Status:** DONE — analysis only, no code or corpus file edited.
- **Working copy:** `~/workspace/laya-v71-work`, HEAD `1cb0bff`, tree clean at start.
- **What changed:** Nothing in the repo except this file. Scratch scripts live in `/tmp`
  (`/tmp/lane01_diag.py`, `/tmp/lane01_followup.py`, `/tmp/lane01_followup2.py`,
  per-record rows `/tmp/lane01_rows.json`); they are not part of the deliverable.
- **Sealed discipline:** `test-bank/sealed/*.json` was never opened. Sealed numbers below
  come only from the already-logged aggregates in `results/live-laya-v7-results.md`
  and `docs/10x_plane.md` §1.1.

## 0. READ FIRST — the validation split moved under this lane (pin + warning)

All headline numbers below are pinned to **one exact file version**:

```
data/synthetic_v7_1/validation.jsonl  sha256 11ffa32d015bca691aae83692af9fdbfe977e11bbe50df67f64e2c71934019e7
```

Lane 02 was regenerating the corpus concurrently (builder comment: "recall-swarm
expansion (Lane 02, 8,000; thin clusters + hn_g/hn_h)"; manifest `n_total` is now
8000). During this lane's work I observed **three distinct validation versions**:
the swarm-start file, then `95b6b47f…`, then the pinned `11ffa32d…` (hash verified
stable across the diag + follow-up runs behind this report), then a further
version `2bfceb39…` minutes later. I measured all three; the per-version decimals
move (exact 35.8% → 37.0% → 35.8%), so **no lane should quote a validation
number without its sha**. The coordinator must freeze/version the split (contract
R1) before any lane's numbers are comparable. The findings that held across all
three versions — the actual diagnosis — are in §6; the pinned-version numbers are
in §2–§5.

## 0.1 Verdict in one paragraph

On the pinned validation split (500 records) the current evidence-mode pipeline
scores **179/500 exact (35.8%)**, micro-P 0.78 / micro-R 0.38 / micro-F1 0.51,
TP/FP/FN **353/99/567**, and is **silent on 235 of 411 oracle-non-empty records
(57.2%)**. The failure is almost entirely Stage 1 extraction, not Stage 2
routing: predicted kept_ids == Stage 2 over extracted facts on **0/500
mismatches**, so every pred-vs-oracle gap is an extraction gap. The dominant
cause is language, not paraphrase subtlety: the extractor recovers **zero
Kannada facts (0.0 recall on every fact, 0/121 KN records)** and near-zero
Kanglish, because evidence mode has no translation and English regexes cannot
match KN script or romanised Kannada. In English the regexes are strong on
money/custody/child/joint/birth (recall 0.88–1.00) but collapse on decree,
dv-compensation (both 0.00), child-maintenance-only (0.05), demand (0.17) and
restitution (0.20). **70% exact needs the classifier (Lane 04) + KN coverage
(Lane 05) first; anchor widening (Lane 03) alone caps out near ~54% (the
English-only exact rate).**

## 1. Method (every number below comes from these runs)

**Baseline sanity (known-good pattern).** Command:

```
python -m tests.v7_backtest --suite 16q --mode evidence --device cpu --misses 0
```

Exact output (tail): `16-Q` exact `14/16`, `esc_kinds_strict 10/16`,
`esc_bool_strict 16/16`, `fp_prose 0`, `raw_formula_rating 7.6`, `total_wall_s 0.043`.
This reproduces the coordinator-logged 16-Q evidence-mode numbers exactly, so the
pipeline works on this VM. (`python3 -c "import torch"` fails — no torch, no neural
run, as expected.)

**Main run** (`/tmp/lane01_diag.py`, wall 0.533s for 500 records, on the pinned file):

1. Load `data/synthetic_v7_1/validation.jsonl` (500 records: EN 229 / KN 121 /
   kn_roman 150).
2. **Oracle kept_ids:** each record's GT issues/facts (enums mapped F→female,
   M→male, U→unknown; `negated_issues` = issues with intent `denied`) fed into
   `evaluate_stage2_v7(custody_vocab="v3_bundled")` — the same Stage 2 and custody
   vocab as the 16-Q/sealed backtest default. The oracle isolates Stage 2: Stage 2
   is deterministic given facts, so pred-vs-oracle gaps are Stage 1 gaps.
3. **Predicted kept_ids:** `assess_v7_batch(mode="evidence", device="cpu",
   with_prose=False)` — the current evidence-mode pipeline (English regex anchors
   only; no torch, no NLLB translation, no neural probes).
4. **Cause attribution per FN/FP section-instance** (deterministic rules, in order):
   `scope_flip` → `dead_route` (gate fact in the 8 formerly-dead keys AND emitted
   0× as supported across the run) → `paraphrase_miss` (gate fact missed,
   lang kn/kn_roman) → `anchor_miss` (gate fact missed, lang en, ≥1 token from
   that fact's anchor vocabulary in the text) → `classifier_gap` (gate fact missed,
   lang en, no anchor token in the text) → `false_blocking_fact` → `stage2_rule_gap`.
   FP mirror: extracted-supported gate fact GT does not support → `false_anchor_fire`;
   else `stage2_rule_gap_fp`. Gate sets were read from `evaluate_stage2_v7`.
   The anchor vocabulary per fact is listed in §7 (it is the current regexes'
   surface vocabulary, so the anchor/classifier boundary is vocabulary-relative —
   see the caveat in §5).
5. **Follow-ups** (`/tmp/lane01_followup2.py` on the pinned file) re-ran extraction
   to ground the ambiguous buckets (the 4 `stage2_rule_gap` FNs, the 31
   `stage2_rule_gap_fp` FPs, the zero-recall facts) with fact diffs and example texts.
   (An earlier follow-up script over-prints: it lists ALL FN records, not just
   stage-2 ones — only the v3 follow-up-2 output was used for §4.)

**Oracle limits (read before quoting any number):**

- The synthetic schema has **28 facts; 7 of the 8 formerly-dead keys are not in it**
  (`money_fact_child_or_parallel`, `stay_in_house_under_eviction_pressure`,
  `stridhan_held_by_inlaws_refused`, `stridhan_safe_in_own_possession`,
  `stridhan_abandoned_or_undisputed`, `urgent_safety_risk`,
  `hypothetical_or_joint_prop_fact_only` — only `interim_asked` is). Dead-route
  kept_ids impact is therefore **unmeasurable on this split** except via
  `interim_asked` (§4).
- The schema has **no `interim_only_asked` fact**, but Stage 2 reads it
  (pending-HMA interim-only → hma-24 alone). 2 FNs are an artifact of this (§4),
  not a Stage 2 bug. Sensitivity: exact would be **180/500 (36.0%)** if the
  extractor is right on that 1 record.
- Oracle coverage is thin for two sections: **hma-27 has only 11 oracle
  positives** (23 of 34 joint-property requests lack pending/being-filed, so the
  D2 gate correctly yields no hma-27) and **hma-26 is thin too (9 FN on the
  pinned file; it had 6 oracle positives in the second measured version)**.
  The split barely diagnoses hma-27 — yet hma-27 was the #1 FN section in
  Sealed Fresh-20.
- `procedure` has **no extractor trigger and no section** (21 records request it);
  it cannot affect kept_ids. `demand_made`, `explicit_residence_order_only`,
  `child_safety_risk`, `urgent_safety_risk` affect escalations/safety only, not kept_ids.

## 2. Headline numbers (pinned validation-500, evidence mode, CPU)

| Metric | Value |
|---|---|
| Exact | **179/500 = 35.8%** |
| Micro P / R / F1 | 0.7810 / 0.3837 / 0.5146 |
| TP / FP / FN (section instances) | 353 / 99 / 567 |
| Silent (oracle non-empty, pred empty) | **235 / 411 = 57.2%** |
| Oracle-empty records | 89 (pred also empty on 77 of them) |
| Exact among oracle-nonempty | 102/411 = 24.8% |
| Exact among oracle-empty | 77/89 = 86.5% |
| Scope flips (extracted in_scope denied, GT supported) | 0 |
| `assess` vs Stage-2-over-extracted-facts mismatches | 0/500 |

Exact by language: **EN 123/229 = 53.7%**, **KN 22/121 = 18.2%**,
**kn_roman 34/150 = 22.7%**. (KN/kn_roman exacts are almost all oracle-empty
records where `[]` happens to be right.)

Exact by cluster (meanings from `scripts/build_synthetic_corpus.py` `HN_BLOCKS`;
hn_g/hn_h are Lane 02's new recall-swarm clusters): core 55/137 (40.1%), combo
28/106 (26.4%), hn_a custody-vs-residence co-location 3/18 (16.7%), **hn_b
residence-explicit-only / lockout / dv-comp 7/42 (16.7%)**, hn_c divorce
pending/filed/JS/restitution/decree 8/30 (26.7%), hn_d stridhan / joint-property
11/24 (45.8%), hn_e maintenance arrears/vary/elder/male-self/father-child-only
11/30 (36.7%), hn_f hypothetical/third-party/quoted/pre-BNSS 34/49 (69.4%),
**hn_g incidental-mention traps 3/20 (15.0%)**, hn_h modality traps
(hypothetical/quoted/past) 7/13 (53.8%), neg 6/20 (30.0%), conflict 6/11 (54.5%).

## 3. Per-cause breakdown (the deliverable)

### 3.1 FN causes — 567 missed section-instances

| # | Cause | Count | Share of FN |
|---|---|---|---|
| 1 | **Paraphrase miss (kn/kn_roman)** — gate fact GT-supported, extractor silent; evidence mode has no translation and English regexes cannot match KN script or romanised Kannada (only 2 KN hooks exist in `laya_v7_evidence.py`) | **488** | **86.1%** |
| 2 | **Anchor miss (EN)** — gate fact missed although an anchor token is in the text; the regex exists but this paraphrase does not match it | **52** | **9.2%** |
| 3 | **Classifier gap / no-anchor-token (EN)** — gate fact missed and no token from that fact's anchor vocabulary is in the text; nothing for a regex to grip | **15** | **2.6%** |
| 4 | Anchor miss + classifier gap (mixed, multi-fact record) | 8 | 1.4% |
| 5 | Stage 2 rule gap (first-pass label — §4 shows all 4 are extraction artifacts, true Stage 2 FN = 0) | 4 | 0.7% |
| — | Scope flip | 0 | 0% |
| — | Dead route | 0 | 0% (unmeasurable here — §4) |
| — | False blocking fact | 0 | 0% |

**Top 3 causes: paraphrase miss 488, anchor miss 52, classifier gap 15.**

FN by section: bnss-144 110, pwdva-20 61, hmga-1956-s6 53, welfare-principle 53,
pwdva-18 50, gwa-1890 45, pwdva-17 26, pwdva-19 26, pwdva-22 26, bns-316 26,
hma-25 16, hma-13 15, hma-24 11, births-deaths-act-1969 11, hma-9 11, hma-27 10,
hma-26 9, hma-13b 8. FN by section × lang: EN 79, KN 241, kn_roman 247.
The custody triple (gwa+hmga+welfare, 45/53/53) is one underlying miss —
`custody_claim` — counted 3× by the v3_bundled companions.

### 3.2 FP causes — 99 false section-instances

| Cause | Count | Share of FP |
|---|---|---|
| **False anchor fire (EN)** — an extracted-supported gate fact GT does not support | **68** | **68.7%** |
| **Missed blocking/branch fact** — no false gate fact, but a GT-supported fact that would have blocked or re-routed the section was missed (labelled `stage2_rule_gap_fp` by the first script; re-analysis in §4 shows every one traces to extraction) | **31** | **31.3%** |

Sub-breakdown of the 31 (all but 1 are pwdva-20): `child_maintenance_only`
missed → pwdva-20 over-fires on child-only money (4); `decree` missed → fell
through to the plain maintenance branch (8); `existing_order_enforcement`
missed (3); claimant role/sex enum missed alone (15); `proceeding_pending_hma`
missed → gwa-1890 over-fire (1). **True Stage 2-rule FP: 0.** Note the
diagnosis script counts a false gate fact first, so enum misses are undercounted
in the headline split: the re-analysis found a branch/enum fact diff on 72/99
FP instances overall — claimant sex/role extraction is weak (sex is left
"unknown" whenever the text does not say "my husband" / "I am the wife"
explicitly; it usually does not change kept_ids, but it does when GT is male
or the role is child/other/parent).

FP by section: pwdva-20 41, bnss-144 12, gwa-1890 11, hmga-1956-s6 10,
welfare-principle 10, pwdva-18 5, hma-13b 4, births-deaths-act-1969 2,
pwdva-17 1, pwdva-19 1, hma-13 1, bns-316 1.

## 4. What the follow-ups proved (corrections to the first pass)

**a. "Stage 2 rule gap" FN = 0, not 4.** The 4 first-pass `stage2_rule_gap` FNs
are two extraction artifacts: SYN-VA-0062 + SYN-VA-0262 are `mutual_consent`
**false fires** ("My husband will not agree to a mutual divorce. Can I still
get a divorce without his consent?" — `_MUTUAL_CONSENT_RE` matches "mutual
divorce" while `_MUTUAL_NEG_RE` only covers "don't/do not want a mutual
divorce"), which flip hma-13 → hma-13b; SYN-VA-0282 ×2 sections is the
`interim_only_asked` oracle artifact ("While the divorce case is going on, I
need interim maintenance" — extractor sets `interim_only_asked`, the schema has
no such fact, so the oracle emits bnss-144 + pwdva-20 alongside hma-24 and the
extractor correctly emits hma-24 alone per Graph v4). No FN in this run is
attributable to Stage 2 routing given correct facts.

**b. "Stage 2 rule gap" FP = 0, not 31.** Every one of the 31 re-analysed FPs
traces to an extraction miss (§3.2). Stage 2 is not the bottleneck.

**c. The dead-8 keys are wired, not dead — but near-zero-fire.** Plan §1.1
listed 8 keys as "never produced by Stage 0/1". At HEAD `1cb0bff` the 10x Lane 01
already wired all 8 into `extract_grounded_v7`. Extracted-supported counts across
all 500 records (pinned file): `interim_asked` 6,
`money_fact_child_or_parallel` 1, `stay_in_house_under_eviction_pressure` 2,
`stridhan_held_by_inlaws_refused` 2, `stridhan_safe_in_own_possession` 0,
`stridhan_abandoned_or_undisputed` 0, `urgent_safety_risk` 2,
`hypothetical_or_joint_prop_fact_only` 10. "Dead" now means "emitted but almost
never fires", and 7 of the 8 are absent from the synthetic schema, so their
kept_ids impact cannot be measured on this split at all.

**d. Kannada extraction is zero; Kanglish is near-zero.** Per-fact recall by
language: **KN 0.0 on every one of the 28 facts**; kn_roman nonzero only on
money_fact 3/66 (0.05), lump_sum 1/6 (0.17), interim_asked 2/3 (0.67),
custody_claim 1/25 (0.04), child_fact 3/45 (0.07), birth_cert_asked 2/5 (0.40)
— all via English loanwords in the text ("maintenance", "Lump sum",
"Mutual consent divorce", "divorce filing"). KN texts contain 0 English anchor
tokens (measured on the previous version; the pattern is unchanged). `in_scope`
recall 1.00 on KN is a default artifact (no OOS English token → supported by
default), not detection. Silent by language: KN 99, kn_roman 113, EN 23
(of 235 silent).

**e. Concrete EN regex defects (verified on the text, not inferred):**
- `_DECREE_PASSED_RE` misses "The court gave the divorce decree last year"
  (SYN-VA-0030) and "Our divorce is already decided (by the court)"
  (SYN-VA-0055) — needs "decree was passed/granted" or "divorce was granted".
  Decree EN recall **0/9**.
- `_RESTITUTION_RE` misses "I want him to come back home and live with me"
  (SYN-VA-0066) and "I want my husband to return" (SYN-VA-0190) — needs the
  exact phrase "come back to live with me". Restitution EN recall **2/10**.
  The same "live with me" wording makes `_CUSTODY_ASK_RE` fire `custody_claim`
  on childless restitution records (SYN-VA-0066/0358/0417 → 9 FP instances of
  gwa/hmga/welfare).
- `_DEMAND_TRUE_RE` misses "I asked for it back and they refused to give it"
  (SYN-VA-0067/0088) — needs "asked them to return" / "demanded".
  Demand EN recall **2/12**.
- `_DV_COMP_RE` misses both "I want compensation for my injuries"
  (SYN-VA-0072 — the trailing `\b` after `injur` never matches
  "injuries/injury") and "I spent a lot of money on medicines after my husband
  beat me. I want the court to order him to pay for my treatment"
  (SYN-VA-0042 — no "compensation/injury" words at all). DV-comp EN recall
  **0/15**.
- `_CHILD_ONLY_CLAIM_RE` misses "I need money only for the child's school
  fees" (SYN-VA-0070) and a 16-year-old's self-support ask (SYN-VA-0013).
  Child-only EN recall **1/20 (0.05)** — the worst non-zero EN fact — and its
  misses cause 4 pwdva-20 FPs.
- `_CHILD_SAFETY_RISK_RE` misses "My husband beats our daughter too; my
  daughter is not safe at home" (SYN-VA-0182 — needs "beats the child") and
  neglect phrasing "My child is left alone at home… not looked after properly"
  (SYN-VA-0264). Child-safety EN recall **2/7**.
- `_RESIDENCE_ASK_RE` misses "keep living at home with me; this is about
  staying in the house" (SYN-VA-0006/0170/0175/0382 — needs "keep staying in
  **the** house"). Residence EN recall 24/30 = 0.80 on this version (it was
  0.31–0.33 on the two earlier versions — the template mix changed; the
  "this house" / "keep living" gap persists in all three).
- `_MUTUAL_CONSENT_RE` false-fires on "will not agree to a mutual divorce"
  (SYN-VA-0062/0262, §4a). `_JS_ONLY_RE` is defeated by its own negation check
  on the one EN JS record (SYN-VA-0357: "live apart with a court order" — no
  "judicial separation" words at all; needs semantics).
- Conflicting/retracted claims: "I want custody of my child. Actually, no, let
  my husband keep our child" (SYN-VA-0002/0213 — GT `custody_claim=conflicting`,
  extractor takes the first clause → custody FP triple) and procedural custody
  questions ("I want to start a case for my child's custody. Which documents
  will the court ask for first?" SYN-VA-0286 — GT custody unknown, extractor
  fires on "child's custody").
- Threat-to-child misread as DV: "My husband has threatened to hide our
  daughter from me. I am afraid he will take my daughter away" (SYN-VA-0391 —
  GT violence unknown, extractor fires `violence` on "threatened" → pwdva-18 FP
  while custody/child-safety are missed).

## 5. Per-fact recall (GT-supported → extracted-supported; pinned file)

Overall recall is dragged down by KN/Kanglish; EN recall is the informative column.

| Fact | GT-sup (n) | Recall all | Recall EN | Recall KN | Recall kn_roman |
|---|---|---|---|---|---|
| money_fact | 210 | 0.433 | **0.96** | 0.0 | 0.05 |
| custody_claim | 85 | 0.376 | **0.94** | 0.0 | 0.04 |
| child_fact / minor_child | 173 / 173 | 0.43 / 0.42 | 0.97 / 0.99 | 0.0 | 0.07 / 0.0 |
| joint_property_claim | 35 | 0.543 | **1.00** | 0.0 | 0.0 |
| birth_cert_asked | 21 | 0.476 | **1.00** | 0.0 | 0.40 |
| lump_sum_settlement | 10 | 0.40 | 1.00 | 0.0 | 0.17 |
| mutual_consent | 10 | 0.20 | 1.00 | 0.0 | 0.0 |
| being_filed | 12 | 0.333 | 1.00 | 0.0 | 0.0 |
| divorce_asked | 32 | 0.344 | 0.92 | 0.0 | 0.0 |
| violence | 61 | 0.344 | 0.88 | 0.0 | 0.0 |
| residence_claim | 50 | 0.48 | 0.80 | 0.0 | 0.0 |
| stridhan_claim | 45 | 0.422 | 0.76 | 0.0 | 0.0 |
| coercive_eviction_or_lockout | 24 | 0.417 | 0.71 | 0.0 | 0.0 |
| interim_asked | 10 | 0.60 | 1.00 | 0.0 | 0.67 |
| proceeding_pending_hma | 24 | 0.208 | 0.56 | 0.0 | 0.0 |
| existing_order_enforcement | 25 | 0.16 | 0.57 | 0.0 | 0.0 |
| school_fees_fact | 47 | 0.213 | 0.50 | 0.0 | 0.0 |
| child_safety_risk | 15 | 0.133 | 0.29 | 0.0 | 0.0 |
| restitution_asked | 13 | 0.154 | 0.20 | 0.0 | 0.0 |
| demand_made | 22 | 0.091 | 0.17 | 0.0 | 0.0 |
| child_maintenance_only | 44 | 0.023 | **0.05** | 0.0 | 0.0 |
| decree | 14 | 0.0 | **0/9** | 0.0 | 0.0 |
| dv_injury_comp_asked | 26 | 0.0 | **0/15** | 0.0 | 0.0 |
| judicial_separation_only | 4 | 0.0 | 0/1 | 0.0 | 0.0 |
| stridhan_sold_or_mortgaged | 3 | 0.333 | 1.00 | 0.0 | 0.0 |
| explicit_residence_order_only | 8 | 0.50 | 1.00 | 0.0 | 0.0 |
| in_scope | 478 | 1.00 | 1.00 | 1.00 | 1.00 (default, not detection) |

Per-issue requested recall: maintenance 0.443, residence 0.48, custody 0.376,
divorce 0.344, stridhan 0.45, joint_property 0.529, violence 0.362,
dv_compensation 0.0, restitution 0.154, birth_certificate 0.476, procedure 0.0
(no trigger exists).

**Caveat on the anchor/classifier split:** `classifier_gap` means "no token from
that fact's anchor vocabulary in the text", where the vocabulary is the current
regexes' surface vocabulary (§7). Some of the 15 are new-pattern-fixable, not
semantically hard — e.g. "Our divorce was decided by the court" (decided ≠
decree/granted/dissolved in my vocabulary, but "divorce was decided" is
regex-matchable). The robust claim is the combined one: **67 EN FNs need
either wider regexes (52 anchor + some of the 15) or a semantic classifier
(the rest of the 15)**. The 488/52/15 split itself is exact per the stated rule;
the interpretation boundary is fuzzy at the edges.

## 6. What held across all three corpus versions (the stable diagnosis)

I measured three validation versions (swarm-start, `95b6b47f…`, pinned
`11ffa32d…`). The decimals move; these do not:

| Finding | v1 (swarm-start) | v2 (`95b6b47f…`) | v3 pinned (`11ffa32d…`) |
|---|---|---|---|
| Exact | 179/500 (35.8%) | 185/500 (37.0%) | 179/500 (35.8%) |
| Micro-R | 0.346 | 0.403 | 0.384 |
| Silent / oracle-nonempty | 257/417 (61.6%) | 238/407 (58.5%) | 235/411 (57.2%) |
| Paraphrase share of FN | 529/653 (81.0%) | 472/574 (82.2%) | 488/567 (86.1%) |
| Anchor-miss share of FN | 94/653 (14.4%) | 77/574 (13.4%) | 52/567 (9.2%) |
| Classifier-gap share of FN | 19/653 (2.9%) | 18/574 (3.1%) | 15/567 (2.6%) |
| KN fact recall | 0.0 all facts | 0.0 all facts | 0.0 all facts |
| EN strong facts (money/custody/child/joint/birth) | 0.88–1.00 | 0.95–1.00 | 0.88–1.00 |
| EN weak facts (decree / dv-comp / child-only / demand / restitution) | 0.0 / 0.0 / 0.21 / 0.0 / 0.0 | 0.0 / 0.0 / 0.04 / 0.25 / 0.22 | 0.0 / 0.0 / 0.05 / 0.17 / 0.20 |
| True Stage 2 FN/FP after re-analysis | 0 / 0 | 0 / 0 | 0 / 0 |
| FP split (false anchor fire / missed blocking fact) | 40 / 21 | 76 / 24 | 68 / 31 |

The single most version-sensitive number is residence EN recall (0.33 → 0.31 →
0.80) — the template mix changed, not the regexes. Do not quote residence recall
without a corpus sha.

## 7. Comparison with the logged sealed aggregates (does the split proxy the real gap?)

Sealed Fresh-20 (logged): 7/20 exact, TP/FP/FN 38/5/28, micro-R 0.5758, 2 silent.
Top FN sections: hma-27 4, welfare-principle 3, pwdva-17 3, pwdva-18 3, pwdva-19 3,
hma-13 2, hma-24 2, gwa-1890 2, hmga-1956-s6 2, hma-25 1, bns-316 1, hma-26 1.
Sealed Kannada-8 (logged): 4/8 exact, 16/0/7, micro-R 0.6957, 0 silent. Top FN:
pwdva-18 2, hma-27 1, bnss-144 1, pwdva-20 1, pwdva-19 1, pwdva-17 1.

- Validation exact 35.8% ≈ Fresh-20 35% — same order of magnitude, but validation
  micro-R (0.384) is well below sealed (0.576 / 0.696): the synthetic split is
  **harder** than the sealed sets, mostly because 54% of it is KN/Kanglish (vs
  8/28 sealed) and its templates are deliberately paraphrased away from the
  Brutal-tuned regexes.
- The FN section pattern overlaps where it matters: pwdva-17/18/19, welfare,
  gwa/hmga, hma-13, hma-24, bns-316, hma-25 all appear in both top lists.
- Divergences: validation is dominated by bnss-144 (110) + pwdva-20 (61) because
  maintenance is 210/500 of the split; hma-27 is the sealed #1 FN but only 10/567
  here (thin oracle coverage, §1); hma-26 has 9 FN here vs 1 in sealed. The split
  is a usable proxy for the residence/custody/stridhan failure pattern, not for
  hma-27/hma-26.

## 8. Reproduction appendix (so Lane 09 can re-derive every count)

- Commands: §1. Scripts: `/tmp/lane01_diag.py` (main run + attribution),
  `/tmp/lane01_followup2.py` (corrected stage-2/FP re-analysis, zero-recall
  examples, silent/oracle-empty breakdowns). Per-record oracle/pred rows for the
  pinned file: `/tmp/lane01_rows.json` (overwritten by the last diag run — re-run
  `/tmp/lane01_diag.py` against the pinned sha to regenerate).
- **Pin check before trusting any number here:** `sha256sum
  data/synthetic_v7_1/validation.jsonl` must print
  `11ffa32d015bca691aae83692af9fdbfe977e11bbe50df67f64e2c71934019e7`. If it does
  not, the corpus has moved again and §2–§5 do not apply to the current file —
  §6 (cross-version findings) still does.
- Gate sets (from `evaluate_stage2_v7`): bnss-144 {money_fact,
  existing_order_enforcement, decree, lump_sum_settlement, child_maintenance_only,
  proceeding_pending_hma, being_filed, interim_asked, claimant_sex, claimant_role,
  minor_child}; hma-24 {proceeding_pending_hma, being_filed, interim_asked,
  money_fact, existing_order_enforcement, claimant_sex, child_maintenance_only};
  hma-25 {decree, lump_sum_settlement, divorce_asked, proceeding_pending_hma,
  being_filed}; hma-13 {divorce_asked, mutual_consent, judicial_separation_only};
  hma-13b {divorce_asked, mutual_consent}; hma-9 {restitution_asked,
  divorce_asked}; gwa-1890/hma-26 {custody_claim, proceeding_pending_hma,
  being_filed}; hmga/welfare {custody_claim}; pwdva-17/19 {residence_claim,
  claimant_sex}; pwdva-18 {violence, coercive_eviction_or_lockout,
  explicit_residence_order_only, claimant_sex}; pwdva-20 {money_fact,
  claimant_sex, child_maintenance_only}; pwdva-22 {dv_injury_comp_asked,
  violence, claimant_sex}; bns-316 {stridhan_claim, claimant_sex}; hma-27
  {joint_property_claim, proceeding_pending_hma, being_filed};
  births-deaths-act-1969 {birth_cert_asked}. Sex is treated directionally: only
  GT-female→extracted-male counts as an FN-relevant sex miss. (Known attribution
  gap, found in v3: a GT-denied fact that the extractor falsely supports — e.g.
  `mutual_consent` on SYN-VA-0062/0262 — is not counted as a "missed gate fact"
  by the FN rules, so such FNs land in `stage2_rule_gap` on the first pass.
  §3.1 lists 4 `stage2_rule_gap` FNs as first-pass labels; §4a reclassifies
  all 4 (2 mutual-consent false-fire + 2 interim_only artifact), so true
  Stage 2 FN = 0.)
- Anchor vocabulary per fact (substring match, lowercased text): money_fact
  {maintenance, alimony, money, support, school fee, fees, expense, allowance,
  interim, lump}; existing_order {order, arrear, enforce, vary, reduce, unpaid,
  maintenance order}; decree {decree, granted, dissolved}; lump_sum {lump,
  one-time, one time, settlement}; proceeding_pending_hma {pending, case, hma,
  court, filed}; being_filed {filing, file, will file, going to file,
  instructed}; divorce_asked {divorce, end marriage, separate, dissolve};
  mutual_consent {mutual, consent, both agree, amicab}; judicial_separation_only
  {judicial separation}; restitution_asked {restitution, come back, return,
  conjugal}; custody_claim {custody, guardianship, child, son, daughter,
  live with, visitation, keep}; child_fact {child, son, daughter, baby, kid};
  minor_child {year-old, minor, school, baby, toddler}; child_maintenance_only
  {only for, child, school fee}; school_fees_fact {school, fee, tuition};
  child_safety_risk {alcoholic, drunk, abduct, unsafe, violent}; residence_claim
  {house, home, residence, stay, evict, lock, entry, thrown out};
  coercive_eviction_or_lockout {throw, threw, kicked, lock, evict, leave, vacate,
  entry}; explicit_residence_order_only {residence order, separate place,
  accommodation}; violence {beat, hit, slap, threat, harass, abuse, violence,
  assault, cruelty}; dv_injury_comp_asked {compensation, damages, medical,
  hospital, injur}; stridhan_claim {stridhan, gold, jewellery, jewelry, ornament,
  bangle, mangalsutra}; stridhan_sold_or_mortgaged {sold, pawned, mortgaged,
  melted}; demand_made {demand, asked, return, refused}; joint_property_claim
  {joint, jointly, both names, together, divide, share}; birth_cert_asked {birth
  certificate, birth, registrar, registered}; in_scope {husband, wife, marriage,
  divorce, maintenance, child}; interim_asked {interim}; claimant_sex/role
  {husband, wife, mother, father, i am / parent}.

## 9. Which lanes this points at

- **Lane 05 (Kannada/Kanglish) — biggest lever, first.** 488/567 FNs (86.1%) and
  212/235 silent records are KN/kn_roman, where evidence mode extracts ~nothing.
  No anchor work can fix this; it needs KN/Kanglish templates or the classifier
  on KN text. Note the few kn_roman loanword hits ("maintenance", "Lump sum")
  prove English tokens alone do not help — syntax and morphology are missing.
- **Lane 04 (classifier training) — required for 70%.** Even with perfect EN
  anchors, exact caps near the EN-only rate (53.7%); KN needs a semantic model,
  and 15 EN FNs have no anchor token at all. The classifier is the only route
  past ~54%.
- **Lane 03 (evidence anchors) — highest-value regex fixes, in order:**
  child-maintenance-only ("money only for the child's school fees") — 19 EN
  misses, 4 pwdva-20 FPs; dv-comp (`injur\b` bug + "pay for my treatment"
  pattern) — 15 EN misses on pwdva-22; decree ("divorce was decided", "gave the
  divorce decree") — 9 EN misses on hma-25/bnss-144; demand ("asked for it
  back") — 10 EN misses; restitution ("come back home and live with me",
  "want my husband to return") — 8 EN misses on hma-9; residence ("keep living
  at home", "this house") — 6 EN misses; child-safety ("beats our daughter",
  neglect phrasing) — 5 EN misses.
- **Lane 08 (Stage 1 routes audit) — over-fire fixes:** `_CUSTODY_ASK_RE`
  "live with me" firing on childless restitution records (9 FP instances);
  conflicting/retracted custody claims (GT `conflicting` → extractor takes the
  first clause; 6 FP instances); procedural custody questions ("Which documents
  will the court ask for first?" → custody FP); `_MUTUAL_CONSENT_RE` false
  fire on "will not agree to a mutual divorce" (2 records, flips hma-13 →
  hma-13b); threat-to-child read as DV violence (SYN-VA-0391); the
  `interim_only_asked` vs `interim_asked` split (two facts, two regexes).
  Also: `procedure` has no extractor trigger at all (Lane 08 owns extractor
  routes) — no kept_ids impact, but it is a coverage hole.
- **Lane 02 (corpus) — freeze the split first, then schema gaps:** add
  `interim_only_asked` (else the artifact recurs on every run); add the 7
  missing dead-8 facts to the schema (else dead-route impact stays unmeasurable);
  add more hma-27 positives (only 11 oracle positives — the sealed #1 FN
  section) and keep hma-26 positives (6 oracle positives in the second measured
  version); record a sha with every corpus regeneration so lanes stop measuring
  different files.
- **Lane 07 (evaluation harness) — report both numbers + the pin:** exact
  179/500 overall AND exact-among-oracle-nonempty 102/411, plus the corpus sha
  on every run. The headline 35.8% flatters the pipeline on the 89 oracle-empty
  records (77/89 exact by predicting `[]`).
- **Lane 06 (consultation brief):** the brief should carry the §4e defect list
  verbatim — these are concrete regex failures the models can propose patterns
  for — and the KN-zero finding (evidence mode extracts nothing on 121/121 KN
  records) as the headline.

## 10. Still unverified / open

- Whether the extractor is *right* on the interim_only artifact record
  (SYN-VA-0282): needs a schema fact + human/GT call, not more analysis. Exact
  is 179/500 measured, up to 180/500 on that call.
- Whether the validation split's KN/Kanglish templates fairly represent real
  Kannada questions (no P2.1 native-speaker audit of the corpus exists yet).
- Neural-mode numbers: nothing here measures `mode="laya"` (no torch/GPU on
  this VM). The 9 zero-shot prompts may already recover some EN/KN misses on
  RTX — the RTX re-run, not this diagnosis, settles that.
- Sealed re-run stays RTX-only, per guardrails; no 70% claim is made here.
- **Corpus stability is the open process risk:** three validation versions in
  ~15 minutes, manifest now 8000. Until Lane 02 freezes a version (or the
  coordinator pins a sha per lane), every lane's validation number is
  stale on arrival.
