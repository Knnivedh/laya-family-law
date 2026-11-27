# v6 Lane 3 — Open legal decisions (HMA 27, H7 escalate, frozen calls, H5 sub-choice)

**Lane:** 3 (open legal decisions), v6 deep-dive. **Work mode:** offline only — no browser,
no Colab. **No ground truth was changed. No notebook was touched. No graph JSON was edited.**
This file is legal analysis and recommendations only.

**Status of the two v4 decisions:** the v4 legal-decisions memo
(`legal-decisions-v4.md`, 2026-11-26, research only) already resolved Q1 (HMA 27) and Q2 (H7)
with primary-source research. This lane re-derived both verdicts independently from the
graph's own rules and the v4r live facts, and **concurs with v4 on both headline verdicts**
— but with three material refinements v4 missed or left loose (see §1.3, §1.4, §2.3):
(1) K0 is a fourth HMA 27 GT error, not just H3/H10/H15; (2) the graph's HMA 27 prereq
carries an overbroad "alternatively…" limb that is itself legally wrong and must be deleted,
not kept; (3) the v5 report's rating formula differs from the gate's frozen formula, which
changes every rating number quoted since v4r (see §5.4).

**Sources read (only):**
- `laya-10-10-gate-definition.md` §4.1 (frozen judgement calls), §5 (forbidden list),
  §6 rule 1 (GT disputes → independent rater; GT change invalidates all prior runs), §2 (rating formula)
- `v5-precision-report.md` §6–§7 (escalates 12/16 prediction; open items incl. H5 sub-choice)
- `laya-10-10-exact-plan.md` §3.2 (HMA 27 "do NOT gate — unresolved contradiction"),
  §3.4 (H7 ambiguity), line 78 (sub-choices had no observable effect)
- v2 graph JSON (`colab_bundle/laya-crpc-bns-section-decision-tree-v2.json`): `hma-27`
  prerequisites/related/escalate_rule, `hma-24`, `hma-25`, `hma-26`, `hma-13`, `hma-13b`,
  `pwdva-20`, `pwdva-17/18/19`, `bns-316`, `gwa-1890`, Stage 2 pipeline, co-fire rules,
  `v2_new_rules`
- `v2-lanes/lane3-stage2-recheck.json`: R-HMA27-01…09, R-HMA24-01, R-HMA26-02, R-HMA13-01,
  R-PWDVA20-01…09, R-BNS316-01…09, R-BIRTH-01…05
- v4r live JSON (`~/workspace/browser_downloads/sess-2184034649/…-v4r-residence-only.json`):
  per-question facts, GT, predictions, sub-choices, escalations_typed
- `backtest-laya-vs-llama8b.md` §3 (GT table + the two documented judgement calls)
- `legal-decisions-v4.md` (v4 research: statute text and case law for Q1–Q3, reused here;
  **not re-verified by fresh browser research in this offline lane** — see §6)

**Method note on Q1:** the verdict below rests on (a) the text of HMA s.27 itself
("In any proceeding under this Act, the court may make such provisions in the decree…"),
(b) the authorities as recorded in v4 (SC *Balkrishna Ramchandra Kadam v. Sangeeta
Balkrishna Kadam* (1997) 7 SCC 500; Chhattisgarh HC Full Bench *Babulal Yadav v. Sonu
Yadav* (2023 SCC OnLine Chh 2815); *Babita v. Modprasad* (2017); Allahabad HC
*Krishna Kumar Gupta v. Priti Gupta* (2025)), and (c) internal consistency of the graph's
own rules for the parallel ancillary sections HMA 24/25/26. No new case law was searched.
The one contrary authority v4 flagged — HP HC *Astha Thakur v. Dhananjay Kanwar* (reported
31 Dec 2025), read only as a LiveLaw summary — is still unread in full; it does not change
the verdict (single High Court, does not bind outside HP, conflicts with *Babulal* and
*Krishna Kumar Gupta*), but the rater should read the full judgment before freezing a GT
change (see D1).

---

## 1. Q1 — HMA s.27: does it require a proceeding to be PENDING?

### 1.1 Verdict (one line)

**The graph's prerequisite is CORRECT in substance and the GT is WRONG: HMA s.27 is
ancillary — it can only be pressed inside a matrimonial proceeding under the HMA that is
pending or being filed together with the claim, never as a freestanding application with
no HMA proceeding — so HMA 27 should not be in the GT for H3, H10, H15, *and K0* as those
questions are worded (no proceeding pending or being filed in any of the four).**

### 1.2 Evidence from the graph's own rules (internal consistency)

The graph already treats every other ancillary HMA section this way, and HMA 27 is the
odd one out only in its *enforcement*, not its *statement*:

| Section | Prereq as written in the graph | Lane-3 recheck on "no proceeding" | Notebook Stage 2 behaviour (v4r) |
|---|---|---|---|
| HMA 24 (interim maintenance) | "A proceeding under the HMA is pending (or being instituted)" | R-HMA24-01: **drop** | Dropped on K0/H1/H5/H6/H8/H9/H10/H11/H13; kept only on H14 (pending). Correct. |
| HMA 26 (custody) | "A matrimonial proceeding under the HMA is pending, or is being filed" | R-HMA26-02: **drop** | Dropped (GWA route) on K0/H2/H5; kept only on H14. Correct outcome (see §4.1 for the audit-trail defect). |
| HMA 25 (permanent alimony) | "An HMA decree is being passed or has already been passed" | drop (decree=false) | Gated out on K0/H1/H3/H5/H6/H8/H9/H10/H11/H13/H14. Correct. |
| **HMA 27 (Stridhan)** | "A matrimonial proceeding under the HMA is pending or being filed …; alternatively the claim is pressed as part of the family-court case for maintenance/custody/residence" | R-HMA27-04: **escalate only** (drop_reason: null) | **Never gated in v4r** — no `hma-27` entry appears in any question's `gated_out`; `stage2()` adds it unconditionally on stridhan firing (plan §3.2). |

Three internal contradictions follow:

1. **R-HMA27-04 violates the Stage 2 pipeline's own drop rule.** The pipeline (§2 of
   lane3 recheck file) says: "A section failing ANY prerequisite or exclusion check is
   DROPPED, not kept." R-HMA27-04 is a prerequisite check whose `if_fail` is `escalate`
   with no drop reason — so a failed proceeding prereq can never drop the section. Its
   siblings R-HMA24-01 and R-HMA26-02 are both `if_fail: drop`. There is no principled
   reason for s.27 to be the exception; the "escalate" was presumably chosen because the
   GT contradiction was known and unresolved (plan §3.2: "Do NOT gate — unresolved
   contradiction"), i.e. the recheck was bent to fit the GT rather than the law.
2. **The "alternatively…" limb in the section node is legally wrong as written.**
   The node prerequisite (graph JSON line 5919) reads in full: *"A matrimonial proceeding
   under the HMA is pending or being filed (s.27 operates within / in connection with such
   proceedings); alternatively the claim is pressed as part of the family-court case for
   maintenance/custody/residence."* A Family Court case for maintenance (BNSS s.144 /
   PWDVA s.20), custody (GWA 1890) or residence (PWDVA ss.17–19) is **not** a proceeding
   under the HMA. s.27's own words are "in any proceeding **under this Act**" and "in the
   decree". Pressing a Stridhan claim "as part of" a BNSS/PWDVA/GWA case does not make it
   a s.27 claim; it makes it a claim in that other proceeding, where the correct label is
   the Family Courts Act s.7(1) Explanation (c) route (see §1.5). This limb is the only
   reading under which the current GT could be right — and it is the limb that must go.
   (v4's recommended rewording kept the "pending or being filed" limb but did not
   expressly delete this alternative limb; the corrected wording in §1.4 does.)
3. **The "being filed" limb cannot save H3/H10/H15/K0 even on a loose reading.**
   None of the four questions states any intention to file a matrimonial petition, or
   asks about filing one:
   - K0: "how do I get my gold back, and which court do I go to?" — asks the route; no
     petition mentioned. Facts: `proceeding_pending: false`, `demand_made: true`.
   - H3: "My mother gave me gold at my wedding and my in-laws kept it. I have never
     asked them to return it." — no proceeding, no filing intention. Facts:
     `proceeding_pending: false`, `demand_made: false`.
   - H10: "My husband has my gold and I have not asked for it back yet, and he gives no
     money…" — no proceeding, no filing intention. Facts: `proceeding_pending: false`,
     `demand_made: false`.
   - H15: "He sold my gold without asking me." — no proceeding, no filing intention.
     Facts: `proceeding_pending: false`, `demand_made: true` (see §4.4 on that annotation).
   "Being filed" must mean the user states they are filing / will file / have instructed
   filing of an HMA petition — not merely that they want relief. (Consistency check: the
   system already reads it this way for HMA 24 — H5 "I want a divorce" does **not** count
   as a pending/being-filed proceeding for HMA 24, which the backtest walk correctly
   drops on H5; and H11 "I have not filed any case yet" correctly withholds HMA 24. The
   same reading must apply to HMA 27 and HMA 26 — see §4.1.)

### 1.3 Refinement 1 — K0 is a fourth affected question (v4 and the plan both say three)

v4's recommendation (§Q1) and the exact plan (§3.2) both say "H3/H10/H15" / "3 exact
matches". That count is wrong. K0's GT also contains HMA 27
(`{BNSS 144, PWDVA 20, GWA 1890, HMGA s.6, WELFARE, HMA 27, BNS 316, PWDVA 17, PWDVA 18,
PWDVA 19}`) with facts `proceeding_pending: false`. K0 is the *known* case, so the error
was presumably inherited from the original retest GT rather than the held-out set — but
it is the same error, and any GT correction that omits K0 leaves a known-wrong label in
the set and a live HMA 27 fire (v4r K0 pred includes HMA 27) scored as correct.

**Corrected count: 4 questions carry HMA 27 in GT with no proceeding — K0, H3, H10, H15.
GT total would fall 57 → 53 if HMA 27 is removed from all four without replacement**
(§1.5, option C, preserves the count with a replacement label).

Score consequence, stated plainly: under the corrected GT, the v4r exact count falls
before any system change is applied — K0 (exact in v4r) and H10 (exact in v4r) both become
non-exact, because the live system still fires HMA 27 on both. That is the correction
working, not a regression — but it means **the GT correction and the HMA 27 Stage-2 gate
must be applied in the same logged change** (one change per gate §4 step 3, applied as a
single combined change with the GT correction recorded alongside it), so that no run is
ever scored with the gate on and the old GT, or vice versa. v4 already recommended this
pairing; this lane repeats it because the K0 omission makes the pairing load-bearing for
two currently-exact questions, not one (H10) as v4 implied.

### 1.4 Corrected rule wording (for the graph node, the lane-3 recheck, and the notebook)

Replace the `hma-27` prerequisite (graph node) with:

> **"HMA 27 fires only when a matrimonial proceeding under the HMA (ss. 9–13/13B) is
> pending, or is being filed together with the property claim, and the s.27 application
> is made before that proceeding is decided. A freestanding s.27 application with no
> HMA proceeding is not maintainable. A Family Court case under another Act (BNSS s.144,
> PWDVA, GWA 1890) is not an HMA proceeding for this purpose. 'Being filed' means the
> user states they are filing, will file, or have instructed the filing of an HMA
> petition; wanting a divorce or wanting the property back, without more, does not count."**

Consequential edits that must travel with it (same change):
- **R-HMA27-04** (lane3 recheck): change `if_fail` from `escalate` to **`drop`**, with
  drop_reason: *"No HMA proceeding pending or being filed — HMA s.27 cannot be invoked
  standalone; route Stridhan return to the Family Court under Family Courts Act s.7(1)
  Expl. (c) / CPC s.151, and keep BNS s.316 as the criminal route."* Keep the
  `fact_needed` ("whether a matrimonial proceeding is already pending or must be freshly
  filed") as the ask that precedes the drop decision — i.e. ask once, then drop if the
  answer is no (the pipeline's step-8 escalate-then-re-run pattern), not drop silently.
- **Delete the "alternatively…" limb** from the `hma-27` node prerequisite (see §1.2.2).
- **Amend the Stridhan co-fire rule** ("HMA 27 + BNS 316 must be cited TOGETHER, never one
  without the other"): after the correction BNS 316 routinely stands **without** HMA 27
  (with the FCA s.7(1) Expl. (c) civil route instead). New wording: *"BNS 316 (criminal)
  and the civil return route must be cited together — HMA 27 where an HMA proceeding is
  pending/being filed, otherwise the Family Court property suit under Family Courts Act
  s.7(1) Expl. (c) / CPC s.151; never cite BNS 316 as the civil recovery route by itself,
  and never cite HMA 27 without a proceeding."* The BNS 316 node exclusion ("NOT a civil
  recovery remedy by itself — the civil/family-court return route is HMA s.27") needs the
  same amendment, or it will contradict the corrected GT on every Stridhan question.
- **Notebook Stage 2** (Cell 7): apply the gate — HMA 27 is dropped when
  `proceeding_pending` is false and no being-filed fact is present — in the same logged
  change as the GT correction (§1.3). Until then the plan §3.2 "do NOT gate" hold stays
  in force; this lane's verdict is the settlement that lifts it.

### 1.5 What replaces HMA 27 in those GT sets (recommendation, for the independent rater)

The standalone route exists — it is just not s.27 (v4, following *Babulal* paras 25–29):
an independent suit/application in the Family Court under **Family Courts Act 1984,
s.7(1) Explanation (c)** ("a suit or proceeding between the parties to a marriage with
respect to the property of the parties or of either of them"), procedurally as a
**CPC s.151** application. **BNS s.316 stays in GT for all four questions** (criminal
breach of trust — *Pratibha Rani v. Suraj Kumar* (1985) 2 SCC 370; wife absolute owner,
husband/family mere trustees/custodians).

Options for the rater (see decision D1):
- **(C, recommended if the label set can gain a label):** replace `HMA 27` with a new
  label, e.g. `FCA 7(1) Expl. (c) / CPC 151 — Family Court property suit (Stridhan
  return)`, on K0/H3/H10/H15. GT total stays 57; the system then needs a Stage-1/Stage-2
  path that can produce that label, which is new work, not a relabel.
- **(A, honest fallback if it cannot):** drop HMA 27 from those four GT sets without
  replacement and record the missing-label gap in the gate file. GT total becomes 53.
  Do **not** keep a known-wrong label to preserve the exact-match count.
- **(B, rejected):** keep GT and weaken the prereq to "s.27 fires whenever Stridhan is
  withheld". This would require deleting the proceeding requirement from HMA 24/26 as
  well for consistency, and it contradicts the statute text and *Balkrishna*/*Babulal*/
  *Krishna Kumar Gupta*. Rejected on the law.

### 1.6 Second-order scope point (not relied on for the verdict, but material)

Even *with* a pending proceeding, s.27 on its text covers only property *"which may
belong jointly to both the husband and the wife"*. *Babulal* (paras 20–21) holds exclusive
Stridhan — e.g. gold given by the wife's own parents at her wedding, as in H3, H10, H15
(and the gold/cash in K0) — outside s.27. *Balkrishna* took a broader view (the wife's
jewellery given by her father was held within s.27). This is a genuine tension between a
Supreme Court authority and a High Court Full Bench; it is **not** relied on for the
verdict above (the proceeding point alone decides it), but it is a further reason to
prefer the FCA s.7(1) Expl. (c) label for exclusive-Stridhan claims rather than
stretching s.27 — and a reason the rater should not "fix" the GT by merely adding a
pending-proceeding fact to these questions.

### 1.7 What remains uncertain (Q1)

- HP HC *Astha Thakur* (see headnote): single-HC contrary authority, full judgment
  unread. Read it before freezing the GT change; if it is followed, it would at most
  support a *Family Court jurisdiction* reading, not a freestanding-s.27 label.
- No Supreme Court decision directly decides the freestanding-s.27 question; the chain
  is SC *Balkrishna* (ancillary, in-the-decree) + HC Full Bench / Division Bench
  authority. Strong, not SC-direct — say so in the rater's record.

---

## 2. Q2 — H7 escalate: is there any genuine reason this question needs escalation?

Question: *"How do I get my daughter's birth certificate? The hospital did not give us
one."* GT: `{Births and Deaths Act 1969}` only. Court expected: Registrar.
Cell 6: `escalate_expected: true`.

### 2.1 Verdict (one line)

**Escalate_expected = True is CORRECT — but only on a named fact-ask reason, and it is
NOT a quantum/income escalation. The question is fully answerable at the general-procedure
level and NOT fully answerable at the concrete-next-step level: the route (and, in the
>1-year case, the forum) turns entirely on facts the question does not give — the child's
date of birth / age, place of birth, and whether the birth was ever registered.**

This concurs with v4's verdict and disagrees with the exact plan §3.4 framing ("the
question is fully answerable … with no missing fact") only in the sense that §3.4
conflates the two levels. The plan's own alternative branch — "the escalation reason must
be named" — is the correct branch.

### 2.2 Reasoning

1. **The general procedure is answerable.** Registration of Births and Deaths Act 1969
   (not HMA — gate §5 prose item 6): the hospital reports the birth (s.8(1)(b) — medical
   officer in charge gives the information to the Registrar); the Registrar registers and
   issues the certificate (s.12 — free of charge, within seven days of registration); if
   already registered, obtain by search/application (s.17). The hospital was never the
   issuer — that correction, the Act, the authority (Registrar of the area of birth, s.7),
   and the s.8/s.12 mechanism can all be stated without any further fact. No lawyer
   referral is needed for this level.
2. **The concrete route turns entirely on delay, which the question does not state.**
   S.13 (delayed registration, as amended 2023, in force 1 Oct 2023):

   | Delay | Route |
   |---|---|
   | ≤ 30 days | Registrar, late fee — s.13(1) |
   | 30 days – 1 year | District Registrar's written permission + self-attested document — s.13(2) |
   | > 1 year | Order of District Magistrate / SDM / authorised Executive Magistrate — s.13(3) |

   If the daughter is over one year old and unregistered, the operative authority is a
   Magistrate's order, not the Registrar alone — a material difference the system cannot
   know without asking. The question gives no DOB, no age, no place, and does not say
   whether the birth was registered at all. That is a genuine escalation reason, not a
   scoring technicality.
3. **The graph's own recheck agrees.** R-BIRTH-01 (prerequisite, `if_fail: escalate`):
   "A birth certificate … exists, OR hospital/school records are available" — neither is
   established on these facts. R-BIRTH-05 (court, `if_fail: escalate`) likewise leaves the
   forum open. The system design already treats H7 as escalate-on-missing-fact; only the
   *typed* escalation kinds in Cell 8 (quantum / court / demand) fail to express it.
4. **What the v4r numbers actually show — and the v5 misreading to avoid.** In v4r, H7
   reads `escalates_live: true, escalates_correct: true` — but that True came from the
   **quantum boilerplate** ("husband's income / school fees unknown"), which is
   content-wrong on a birth-certificate question (plan §3.4, line 201: "boolean correct,
   content wrong"). The v5 report §6 then says fixing H7's sections "removes their only
   escalation reason under current Cell 8 typed scoring" and predicts H7 escalates False
   in v5. Both readings are artefacts of the *scoring mechanism*, not of the question:
   the boolean was right for the wrong reason in v4r, and would be wrong for the wrong
   reason in v5. The question itself has a named, genuine fact-ask reason throughout.
   **Do NOT "fix" H7 by re-attaching the quantum boilerplate, and do NOT "fix" it by
   flipping the expectation to False** (False would assert the system can give the complete
   concrete next step, which it cannot without the DOB).

### 2.3 Recommendation (no GT change needed)

1. **Keep `escalate_expected: true` for H7.** This resolves the plan §3.4 ambiguity in
   favour of the "True on a named reason" branch — the branch under which escalates can
   reach 16/16 without any GT change (see D3).
2. **Name the reason as a typed escalation, `kind: fact` (not `quantum` / `court` /
   `demand`):** *"Ask: daughter's date of birth / age, place of birth, and whether the
   birth was ever registered; then apply the s.13 tier — if over one year and unregistered,
   a Magistrate's order under s.13(3) is needed."* Cell 8 should score H7's escalation
   from this fact flag; the quantum flag must be False for H7.
3. **Court stays Registrar** for the classification (the Registrar is the issuing authority
   in every tier, including as recipient of a Magistrate's order under s.13(3)); do not
   change `court_expected` to Magistrate on these facts. (Note: v4r H7 court was wrong
   only because the maintenance FP added Magistrate; once v5 gates remove the maintenance
   FP, court reads Registrar only — the court fix and the escalate fix are independent.)
4. **Prose rule (for the prose gate, §5):** H7 prose must give the tiered s.13 procedure
   (all three windows) plus the ask, and must state the hospital reports under s.8 while
   the Registrar issues under s.12. It must never carry the "husband's income / school
   fees unknown" boilerplate. State Rules vary (forms, fees, local office, CRS portal) —
   prose must flag "as per your State Rules" rather than invent a form or fee.
5. **Conditionality to record:** the True verdict is conditional on the fact being missing
   *in the question as asked*. If a follow-up answer gives the DOB (e.g. newborn within
   21/30 days), the escalation collapses to a routine Registrar application. The
   escalation is a **fact-ask to the user, then re-run**, not a lawyer referral.

---

## 3. Audit of the other frozen judgement calls

### 3.1 H14 includes HMA 13 — DEFENSIBLE, but the thinnest frozen call; rater to confirm

- Facts: *"My divorce case is already going on in the Family Court. I want my son to
  stay with me and money for his school fees while the case goes on."*
  `divorce_asked: true, proceeding_pending: true`. GT:
  `{HMA 13, HMA 26, HMGA s.6, WELFARE, HMA 24, BNSS 144, PWDVA 20}`.
- Backtest §3 rationale: "the divorce case is already pending, so the pending petition is
  under HMA 13; the reliefs sought are custody + interim maintenance, but citing the
  governing section of the pending case is not an error. HMA 13B is excluded (no mutual
  consent stated)."
- **For keeping it:** a pending divorce petition in the Family Court under the HMA is, on
  the ordinary reading, a contested petition under s.13 (13B requires mutual consent,
  which is not stated; ss.9/10 are restitution/judicial separation, not "divorce case").
  R-HMA13-01's gate ("user has EXPRESSLY asked for divorce") is satisfied in substance
  by having filed for divorce. HMA 24 and HMA 26 in the same GT set are both justified
  *by* the pending proceeding, so naming its governing section is coherent.
- **Against it (the weakness):** HMA 13 is not a relief sought in *this* question — the
  user asks for custody and interim money, not for a divorce. Every other section in
  every other GT set names a relief sought or a route to one; HMA 13 on H14 names the
  *governing section of an already-pending case*. That conflates two different things a
  GT set can contain. On a strict "relief-sought-only" reading, H14's GT would be the
  other six sections. The backtest rationale does not address this distinction, and no
  ground under s.13 is stated in the question.
- **Verdict: keep, but only as a rater-confirmed judgement call (D6), not as settled law.**
  It is defensible, not proven. If the rater adopts the relief-sought-only reading and
  drops HMA 13, the system change must travel with it: the notebook currently fires the
  divorce issue on H14 (pending → `divorce_signal: pending`) and keeps HMA 13, so dropping
  it from GT without gating that fire would make H14 non-exact by FP — the gate and the GT
  change must be paired, exactly as for HMA 27 (§1.3).

### 3.2 H4 excludes PWDVA 20 — DEFENSIBLE; keep

- Facts: *"They changed the lock and I cannot enter my house. The house is in my
  husband's name."* GT: `{PWDVA 17, PWDVA 18, PWDVA 19}`. No money or rent is claimed;
  no expenses are stated.
- **For the exclusion:** PWDVA s.20 is monetary relief (graph node: prereq — "Expenses or
  losses actually incurred or reasonably anticipated"; R-PWDVA20-03 escalates on expenses;
  `v2_new_rules`: "PWDVA 20 needs money actually asked for (violence alone is a protection
  claim, not a monetary claim)"). H4 asks for entry/stay, not money. The residence set
  already covers the stay (s.17 right, s.18 protection, s.19 enforceable order). This is
  consistent across the set: H5 (beats me, no residence/money-for-stay claim) has no
  ss.17/19; H6 keeps s.20 because money *is* asked; H13 keeps s.20 because school fees
  *are* asked.
- **Counter-argument considered and rejected:** lock-out creates a need for alternative
  accommodation, whose rent s.20 can cover (graph related-sections for s.17/s.19 say so).
  But the user has not asked for rent or alternative accommodation, and on a "reliefs
  available in the abstract" reading every residence question would also carry s.20,
  which would collapse the H4/H6 distinction the set is designed to test. The exclusion
  follows the set's own rule (s.20 fires iff money/rent is claimed), so it is consistent,
  not ad hoc.
- **Related check — H4 *does* include PWDVA 18:** changing the lock / denying entry is
  dispossession backed by threat; s.18 (protection order) is the forward-looking
  protection against it. Defensible. No change recommended; rater to confirm as-is (D7).
  No GT invalidation arises from a confirm-as-is.

---

## 4. Audit of the H5 sub-choice issue and every other GT-vs-rule contradiction in the 16

### 4.1 H5 custody sub-choice A ("HMA s.26") with no proceeding pending — sub-choice WRONG, GT RIGHT, Stage 2 silently correct

- Facts: *"I want a divorce from my husband. He beats me, I need money every month and I
  want my daughter to stay with me."* `divorce_asked: true, proceeding_pending: false`.
  GT custody route: `{GWA 1890, HMGA s.6, WELFARE}`. v4r sub-choice:
  `custody:custody_sub_issue_choice = "A: Custody inside a matrimonial proceeding (HMA s.26)"`.
  v4r kept set correctly contains GWA, not HMA 26 — so Stage 2 produced the right outcome
  while the sub-choice said the opposite, and **no `gated_out` entry records the HMA 26
  drop** (H5's `gated_out` lists only residence-gate and hma-25). The outcome is right;
  the audit trail is missing.
- **Why A is wrong:** HMA 26's prereq (graph node; R-HMA26-02, `if_fail: drop`) requires a
  proceeding "pending, or being filed". "I want a divorce" is a wish/intention, not a
  filing — the same point as §1.2.3: the system already reads it this way for HMA 24 on
  H5 (correctly dropped). A sub-choice that reads divorce-asked as proceeding-pending for
  custody but not for maintenance is internally inconsistent. The correct sub-choice on
  these facts is B ("Standalone custody/guardianship, no HMA proceeding (GWA 1890)"),
  as on K0/H2.
- **Fix (system change, not GT — D8):** derive the custody sub-choice from the
  `proceeding_pending` / being-filed fact, not from the divorce-asked signal; and record
  the HMA 26 drop in `gated_out` with reason whenever sub-choice A is proposed but the
  proceeding prereq fails. No score impact is expected (the kept set is already right);
  the value is auditability and the generalisation to fresh questions, where a silent
  correct outcome cannot be distinguished from a lucky one. This is one logged change
  under gate §4 step 3; it does not invalidate prior runs (GT unchanged).

### 4.2 Other GT-vs-rule / rule-vs-rule contradictions found (full-16 sweep)

| # | Where | Contradiction | Verdict |
|---|---|---|---|
| C1 | K0 GT vs HMA 27 prereq | K0 carries HMA 27 with `proceeding_pending: false` — same error as H3/H10/H15, missed by v4 and the plan's "3 exact matches" count (§1.3). | GT wrong; include K0 in D1. |
| C2 | H3 sub-choice vs GT | `stridhan:civil-vs-criminal = "civil_only_s27"` yet GT keeps **BNS 316** as well. The sub-choice and the GT cannot both be right; the co-fire rule (cite together) sides with GT. | Sub-choice wrong / no observable effect (plan line 78: the three Stridhan sub-choices "had no observable effect on output"). Record; do not change GT on this alone. |
| C3 | H15 sub-choice vs GT | `stridhan:civil-vs-criminal = "criminal_only_s316"` and `stridhan-subissue = "stridhan_no_proof"` yet GT keeps **HMA 27**. The sub-choice already says criminal-only — it agrees with the §1 verdict, not with GT. | Supports D1 (GT wrong on H15). Sub-choice should be audited, not treated as evidence for GT. |
| C4 | H3/H10 BNS 316 with `demand_made: false` | BNS 316's prereq includes "demand for return was made (or refusal is evident from conduct)". No demand has been made on H3/H10, yet GT keeps BNS 316. | **Defensible, not a contradiction** — the graph's own demand-first fallback (R-BNS316-03, `if_fail: escalate`, not drop; backtest §3) keeps BNS 316 as provisional/escalated ("make a written demand first, then re-evaluate"). Note the asymmetry is principled: BNS 316's prereq is demand-*or*-refusal-evident, while HMA 27's prereq is a proceeding — the two sections correctly receive different treatment. |
| C5 | Divorce-gate sub-choice body on K0/H4/H10/H12 | Raw v4r `sub_choices["procedure:divorce-gate"] = "Divorce expressly asked -> open gate, Family Court under HMA s.13/s.13B"` on questions where `divorce_asked: false` (K0, H4, H10, H12). Stage 2 correctly drops HMA 13 on all four, so no score impact — but the sub-choice text asserts a false fact. | Notebook/graph logging defect, not a GT error. Fix with D8's family (derive the gate text from the `divorce_asked` fact). Flag for the notebook lane; do not let a future lane cite these sub-choice strings as evidence that divorce was asked. |
| C6 | H15 `demand_made: true` annotation | Question ("He sold my gold without asking me") states no demand. The True value is an *inference* (sale = refusal evident from conduct, per R-BNS316-02/03). | Annotation inference, not GT error. Rater to confirm (D11): if the rater sets it False/None, BNS 316 stays via the demand-first fallback and the escalation kind changes from demand to fact — no GT change, no invalidation. |
| C7 | H2/H4 `escalate_expected: true` vs typed kinds | H2 (custody-only) and H4 (residence-only) are escalate-True in v4r and escalate-False live (no quantum/court/demand reason fires), exactly the H7/H15 shape (v5 §6). Genuine reasons exist: H2 — welfare facts missing (where the 6yo lives now, day-to-day caregiver, any existing order; father is natural guardian above five under HMGA s.6, so the mother's claim rests on welfare facts not yet stated); H4 — immediate facts missing (where she is now, whether she needs an urgent residence/protection order vs alternative accommodation). | **GT expectations defensible; typed-escalation design is the gap** (same family as H7/H15 — see D5). Do not flip the expectations; add a `fact` kind with named asks. |
| C8 | H15 escalate (v5 §6 framing) | v5 §6 says H15 "kept = stridhan only, demand_made=True → no demand escalation → False vs expected True", implying no genuine reason. In fact genuine fact/proof reasons exist: proof of Stridhan (no list/receipts stated), sale details and value (gold sold — in-specie return impossible, value recovery is the question), and the criminal-route facts. | **Escalate True defensible on fact/proof grounds, not demand grounds** (D4). The v5 framing is too narrow — it equates "escalation" with the three existing typed kinds. |
| C9 | H14 HMA 24 / HMA 26 vs H5 | H14 keeps HMA 24 + HMA 26 (proceeding pending); H5 drops both (divorce asked, no proceeding). | **Consistent, correct.** This pair is the control that proves the system already applies the pending/being-filed distinction correctly for HMA 24/26 — HMA 27 is the only ancillary section not held to it. Strengthens §1. |
| C10 | H11 vs HMA 27 | H11 ("I have not filed any case yet") correctly withholds HMA 24; no Stridhan is in play so HMA 27 is untested there — but the *principle* (explicit no-case statement → no ancillary HMA section) is stated in the question text. | Consistent with §1; no action. |
| C11 | H1 "no case filed anywhere" | Explicit no-proceeding statement; GT correctly contains no HMA 24/25/26. | Consistent with §1; the only HMA section H1's facts could wrongly attract is HMA 27 via the Stridhan FP — which v5 Fix 1 (gold_fact) blocks. No action. |
| C12 | H6 / H13 / K0 divorce gate | H6 explicitly does NOT want a divorce → no HMA 13 (correct); H13 no divorce asked → no HMA 13 (correct); K0 no divorce asked → HMA 13 dropped (correct). | Consistent; no action. |
| C13 | Rating formula (§5.4) | The v5 report's "frozen formula" (0.4·exact + 0.3·micro-F1 + 0.15·court + 0.15·escalates) is **not** the gate §2 formula (10×[0.60·E + 0.15·Rm + 0.10·Pm + 0.075·C + 0.075·S] − 0.5·Fb − 1.0·Fp). Every rating since v4r is quoted under the v5 formula. | Coordinator decision required (D10); restate v4r/v5 ratings under the gate formula. No GT impact. |

No other GT-vs-rule contradiction was found in the 16. In particular: H5's PWDVA 18
without ss.17/19 (violence, no residence claim) is consistent; H13's five-section set
(no custody, no divorce) is consistent; H12 empty GT is consistent (out-of-scope, and
the divorce-issue fire on H12 is correctly dropped by Stage 2); H8/H9 maintenance-only
sets are consistent.

---

## 5. Decision table — everything that needs the USER or an independent rater

Per gate §6 rule 1: **any GT change invalidates all prior runs on that set — they must
be re-run and re-filed.** That consequence is stated explicitly for every option below
that changes GT (D1, D6, and the flip-True-to-False branches of D3/D4/D5). A
confirm-as-is, a graph/notebook-only change, or a typed-escalation-kind addition that
leaves `escalate_expected` untouched does **not** invalidate prior runs (it is a system
change, logged as one change per gate §4 step 3, and the next run is scored under the
existing GT).

| # | Decision (who settles it) | Options | Lane 3 recommendation | Consequence if decided each way (rating / gate) |
|---|---|---|---|---|
| D1 | **HMA 27 GT correction** (independent rater, NOT the tuning lane) | **A.** Remove HMA 27 from K0/H3/H10/H15 GT, no replacement (GT 57→53). **B.** Keep GT, weaken prereq (reject — §1.2). **C.** Replace HMA 27 with new label `FCA 7(1) Expl. (c) / CPC 151` on the four questions (GT stays 57). | **C if the label set can gain a label; otherwise A.** B rejected on the law. Rater to read HP *Astha Thakur* full judgment before freezing. | **A or C both INVALIDATE all prior runs on the current 16** (gate §6.1): v3/v4r/v5 numbers must be re-run and re-filed under the corrected GT; the v5 "predicted 16/16" (computed under the old GT) falls away. Under A, v4r exact would re-score 8/16 before the gate is applied (K0, H10 lose exact), then recover when the §1.4 gate is applied in the same change. Under C, the system additionally needs a path that can produce the new label — new work, and the fresh-20 GT must use the same label. Keeping B preserves the count but keeps a known-wrong label and contradicts the statute — not recommended at any rating. |
| D2 | **HMA 27 corrected rule + gate** (coordinator + notebook lane; lifts plan §3.2 hold) | **A.** Adopt §1.4 wording, R-HMA27-04 → drop, delete "alternatively…" limb, amend co-fire rule + BNS 316 exclusion, gate in notebook — in the same logged change as D1. **B.** Adopt wording but leave R-HMA27-04 as escalate. **C.** Leave ungated. | **A.** | A: HMA 27 stops firing on no-proceeding questions; with D1, exact can reach 16/16 on sections. B: the gate never drops the section — the contradiction persists in a new form. C: the plan §3.2 hold continues and 10/10 stays blocked on sections. No GT invalidation from D2 alone (system change); paired with D1 it shares D1's invalidation. |
| D3 | **H7 escalate expectation** (independent rater confirms; coordinator implements typed kind) | **A.** Keep `escalate_expected: true`, add `kind: fact` with the §2.3 named ask. **B.** Flip to False (question "fully answerable"). | **A.** | A: **no GT change, no invalidation**; with the fact kind implemented, H7 escalates correctly and the v5 12/16 → 13/16 on this row alone. B: **GT change → invalidates all prior runs**; and it asserts the system can give the complete concrete next step without the DOB, which §2.2 shows is false — if the rater nevertheless chooses B, the s.13-tier prose requirement (§2.3.4) should still be kept as a prose rule. |
| D4 | **H15 escalate expectation** (rater confirms) | **A.** Keep True, re-ground on fact/proof kind (proof, sale details/value, criminal-route facts) — demand kind no longer the reason. **B.** Flip to False (demand already made, so "nothing to escalate"). | **A.** | A: no GT change, no invalidation; H15 escalates correctly once the fact kind exists. B: GT change → invalidates all prior runs; and it would assert a sold-gold Stridhan claim with no proof or value stated needs no follow-up, which §4.2 C8 shows is false. |
| D5 | **H2/H4 escalate expectations + typed kinds** (coordinator; rater confirms expectations as-is) | **A.** Keep both True; add `kind: fact` with named asks (H2 welfare facts; H4 immediate-residence facts — §4.2 C7). **B.** Flip either/both to False. **C.** Keep True but leave typed kinds as-is (quantum/court/demand only). | **A.** | A: no GT change, no invalidation; H2+H4 escalates become scorable-correct. **A + D3 + D4 together move v5 predicted escalates 12/16 → 16/16** (the four wrong rows are exactly H2/H4/H7/H15), which under the gate formula (§5.4) moves the v5 predicted rating 9.8 → 10.0 *formula* — still capped at 9.0 until fresh/Kannada/prose/confirmation pass (gate §2 caps). B: GT change → invalidates all prior runs, and asserts custody-only and residence-only questions need no follow-up. C: expectations stay True but unscorable — escalates stays 12/16 and 10/10 stays blocked on G9. |
| D6 | **H14 HMA 13 — keep or drop** (independent rater) | **A.** Keep (governing-section reading, §3.1). **B.** Drop (relief-sought-only reading). | **A (keep), as a rater-confirmed judgement call** — but this is the weakest call in the set and the rater may reasonably choose B. | A: no change, no invalidation. B: **GT change → invalidates all prior runs**; GT 57→56 (53→52 if combined with D1-A); and the notebook's pending-divorce fire of HMA 13 must be gated in the same change, or H14 becomes non-exact by FP. |
| D7 | **H4 PWDVA 20 exclusion — confirm as-is** (independent rater) | **A.** Confirm exclusion (s.20 needs money claimed). **B.** Add PWDVA 20 (lock-out ⇒ alternative-accommodation rent). | **A.** | A: no change, no invalidation. B: GT change → invalidates all prior runs; would also force re-examination of every residence question's s.20 treatment (H5/H6/H13 consistency, §3.2). |
| D8 | **H5 sub-choice fix + audit trail** (notebook lane; coordinator logs the change) | **A.** Derive custody sub-choice from `proceeding_pending`/being-filed fact; record HMA 26 drop in `gated_out`. Fix the divorce-gate sub-choice text (C5) the same way. **B.** Leave as-is (correct outcome, silent). | **A.** | A: no GT change, no invalidation; no score change expected (kept set already right); auditability + fresh-set generalisation improve. B: no cost now, but the next fresh question with a wrong sub-choice and a wrong kept set will be undebuggable. |
| D9 | **Typed-escalation design** (coordinator — the mechanism behind D3/D4/D5) | **A.** Add `kind: fact` (named ask per question) alongside quantum/court/demand; score escalates from the applicable kind, never from the quantum boilerplate. **B.** Keep three kinds only. | **A.** | A: the four fact-ask questions become scorable-correct without any GT change. B: escalates caps at 12/16 on this set regardless of section accuracy, and G9 (16/16) can never pass. Prose rule travels with A: no quantum boilerplate on non-maintenance questions (gate §5 item 7 — a section dropped for the stated facts must not reappear in prose; the quantum text is its equivalent for escalations). |
| D10 | **Rating formula discrepancy** (coordinator — see §5.4) | **A.** Gate §2 formula governs (it is the frozen one); restate v4r as 7.3/10 and v5-predicted as 9.8/10 under it. **B.** Adopt the v5 formula (0.4/0.3/0.15/0.15) by amending the gate doc. | **A** — the gate doc states its formula is frozen and §6.9 forbids changing metric definitions mid-tuning without the coordinator and re-passing the gate. | A: all ratings since v4r are restated down/up as in §5.4; no GT impact; the 10/10 claim still requires G2/G3/G12/G15, so the formula choice does not change what is claimable today (cap 9.0 either way). B: requires a gate amendment, which per §6.9 invalidates the "10/10" label until the full gate is re-passed under the amended version. |
| D11 | **H15 `demand_made: true` annotation** (rater) | **A.** Confirm (sale = refusal evident from conduct). **B.** Set False/None (no demand stated). | **A**, with the inference recorded in the annotation. | Either way: **no GT change, no invalidation** — BNS 316 stays via the demand-first fallback (C4) and only the escalation kind changes (demand → fact). |

### 5.1 What the user (Nivedh) himself must decide vs what the rater decides

- **Rater decisions (not Nivedh, not the tuning lane):** D1, D3 (confirm), D4 (confirm),
  D6, D7, D11 — anything that changes or confirms GT. Per gate §6 rule 1 the rater must
  be independent of the tuning lane.
- **Coordinator decisions:** D2, D8, D9, D10 — system/graph/notebook changes and the
  formula question. D10 in particular is a gate-document question, not a legal one.
- **Nivedh decisions:** none of the above strictly requires him, except (i) whether to
  authorise the new FCA label (D1-C) as a label the system should be able to produce —
  that is a product-scope choice; and (ii) whether to accept that the HMA 27 correction
  invalidates the v4r/v5 runs and requires re-running them (it does, as a matter of the
  gate rules, not preference — but he should be told plainly, because the headline
  "10/16 → predicted 16/16" story is re-based by it).

---

## 5.2 Consequences for the rating, stated with the arithmetic (not live results)

All numbers below are arithmetic from already-measured metrics, not new runs.

### 5.3 v5 predicted escalates, resolved

v5 predicts (offline, from v4r numbers) sections 16/16, court 16/16, escalates **12/16**
(wrong: H2, H4, H7, H15). D3+D4+D5 option A together resolve all four on fact grounds
with no GT change → escalates **16/16**. D3 alone → 13/16. D3+D4 → 14/16.

### 5.4 Rating-formula discrepancy (D10) — the numbers

Gate §2 formula: `10 × [0.60·E + 0.15·Rm + 0.10·Pm + 0.075·C + 0.075·S] − 0.5·Fb − 1.0·Fp`.
v5-report formula: `0.4·exact + 0.3·micro-F1 + 0.15·court + 0.15·escalates` (×10).

| Run | Gate §2 formula | v5-report formula |
|---|---|---|
| v4r live (E 10/16, Rm 1.000, Pm 0.833, C 13/16, S 14/16, Fb 0) | 10×[0.375+0.15+0.0833+0.0609+0.0656] = **7.3/10** | **7.7/10** (as reported) |
| v5 predicted (E 16/16, Rm 1.000, Pm 1.000, C 16/16, S 12/16) | 10×[0.6+0.15+0.10+0.075+0.05625] = **9.8/10** | **9.6/10** (as reported) |
| v5 predicted + D3/D4/D5-A (S 16/16) | **10.0** formula | **10.0** formula |

In every case the **caps** still apply (gate §2): prose not measured → ≤ 9.0; fresh set
not run/passed → ≤ 9.0; Kannada not run/passed → ≤ 9.0; no confirmation re-run → ≤ 9.0.
So even a 10.0 formula score is a **9.0** until G2/G3/G12/G15 pass. The formula choice
changes no claimable rating today; it must still be settled (D10) before any rating is
quoted, because 7.7 vs 7.3 for the same live run is exactly the kind of drift the frozen
formula exists to prevent.

### 5.5 HMA 27 correction vs the v5 prediction

The v5 "predicted 16/16" was computed under the **old** GT (HMA 27 in K0/H3/H10/H15).
Under the corrected GT (D1-A, 53 sections) the v5 fixes still remove the same FPs, but
the prediction must be recomputed: the system must *also* stop firing HMA 27 on those
four questions (D2-A, same change) for the prediction to hold. If D1 is adopted without
D2, the corrected-GT exact count would be 14/16 (K0, H10 non-exact by HMA 27 FP); if D2
is adopted without D1, the old-GT exact count would be 14/16 (K0, H10 non-exact by HMA 27
FN). Neither half-measure is scorable as progress. This is why §1.3 insists on pairing.

---

## 6. Limits of this lane

- **Offline only:** no browser, no Colab, no new case-law search. The Q1 authorities are
  as recorded in v4 (with its URLs and pin cites); their accuracy was checked against the
  graph's own text and internal consistency, not re-verified against the judgments.
  The HP *Astha Thakur* full judgment remains unread (v4's caveat stands).
- **Not legal advice** for any real person; this is test-system design (which label the
  classifier should emit for stylised test facts).
- **No GT, graph, or notebook file was modified.** All changes above are recommendations
  for the rater / coordinator / notebook lane, in the order the gate requires: rater
  settles D1/D6 (and confirms D3/D4/D7/D11) → coordinator logs one combined change
  (D1 + D2, plus D8/D9 as separate single changes per gate §4 step 3) → live Colab re-run
  and re-filing under the corrected GT.
- **Sukhdev Singh v. Sukhbir Kaur (2025) verification** (v4 Q3) was not re-opened: it does
  not bear on HMA 27, H7, or any decision in this lane, and v4 verified it (2025 INSC 197;
  s.25 "any decree" includes a s.11 nullity decree; grant discretionary). It remains
  usable only for the void-marriage → s.25/s.24 question, never for Stridhan/custody/
  residence, and it gives no support to "HMA 25 with no decree" fires.

## 7. One-paragraph summary for the coordinator

HMA 27: prereq right, GT wrong — on **four** questions (K0, H3, H10, H15), with the
graph's "alternatively… family-court case" limb itself legally wrong and to be deleted,
R-HMA27-04 to be changed from escalate to drop, and the GT correction paired with the
gate in a single logged change (a GT change invalidates all prior runs on the set).
H7: escalate True is correct on a named s.13 fact-ask (DOB/age, place, registration
status), never on quantum — no GT change needed, but Cell 8 needs a `fact` escalation
kind, as do H2/H4/H15, whose expectations are likewise defensible and likewise
unscorable under the current three kinds; fixing the kinds moves v5 predicted escalates
12/16 → 16/16 with no GT change. H14/HMA 13 is defensible but thin (rater to confirm);
H4/no-PWDVA 20 is defensible (confirm as-is). H5's custody sub-choice A is wrong on the
facts (divorce-asked ≠ proceeding pending) with the right outcome reached silently —
fix the derivation and the audit trail, not the GT. Finally, the v5 report's rating
formula is not the gate's frozen formula (v4r is 7.3, not 7.7, under the gate formula) —
settle that before quoting any rating.
