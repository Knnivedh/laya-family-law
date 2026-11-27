# Brutal bank — second-rater report (blind double-rating, 25% sample)

**Rater:** second rater (independent of the first rater and of all tuning work).
**Date:** 2026-11-27. **Work:** offline only.
**Scope restriction honoured:** I read ONLY `brutal-test-200-plan.md` §2/§2.4 and the draft
bank `brutal-bank-v1-draft.json`. I did NOT read any v6-deep-dive, v6-lane, v5, notebook,
live-result, or sealed-set file.

## 1. Method (blinding)

1. The 230 draft questions were grouped by category; a stratified random sample of 58
   (25%) was drawn proportional to category size with **fixed seed 20261127**
   (Python `random.Random(20261127)`, largest-remainder allocation).
2. I wrote my own GT for each sampled question from the **question text alone** —
   via a questions-only file with all GT fields stripped — and recorded it to disk
   BEFORE opening any draft GT. Only then was the comparison run.
3. All 16 C13 Kannada items were rated the same blind way (the 4 sampled C13 items
   plus the other 12), for fluency and GT correctness.
4. B-148 and the extended label set were reviewed after the blind rating, from the
   draft entries only.

## 2. Sample (seed 20261127, n = 58)

Allocation — C1 8, C2 5, C3 5, C4 5, C5 5, C6 4, C7 4, C8 3, C9 4, C10 3, C11 3,
C12 2, C13 4, C14 3 (sums to 58).

Sampled IDs (draw order): B-140, B-037, B-030, B-193, B-017, B-221, B-219, B-202,
B-180, B-174, B-047, B-132, B-056, B-217, B-125, B-146, B-058, B-011, B-102, B-123,
B-151, B-153, B-215, B-134, B-208, B-090, B-071, B-103, B-156, B-101, B-227, B-117,
B-131, B-107, B-173, B-183, B-072, B-041, B-054, B-067, B-007, B-024, B-014, B-075,
B-069, B-029, B-209, B-083, B-111, B-046, B-157, B-033, B-198, B-192, B-164, B-021,
B-109, B-165.

## 3. Agreement — headline

| Field | Agreement |
|---|---|
| **Full agreement (sections + court + escalates + kinds)** | **45 / 58 (77.6%)** |
| Sections (`gt_sections`, set equality) | 55 / 58 (94.8%) |
| Court (`gt_court`) | 57 / 58 (98.3%) |
| Escalates boolean | 58 / 58 (100%) |
| Escalation kinds (set equality) | 47 / 58 (81.0%) |

Per-category full agreement: C1 5/8, C2 2/5, C3 4/5, C4 4/5, C5 3/5, C6 3/4, C7 4/4,
C8 3/3, C9 4/4, C10 3/3, C11 3/3, C12 1/2, C13 4/4 (sampled), C14 2/3.

**13 disagreements in the sample: 3 section-level, 10 kinds-only.** No disagreement
on the escalates boolean anywhere, and no disagreement on any empty-GT item in the
sample (B-069, B-156 both agreed empty/False; B-173, B-174, B-180 agreed empty/True
with a procedure handoff).

## 4. Per-question agreement table (58)

Agree = full agreement on all four fields. S/C/E/K = sections/court/escalates/kinds.

| ID | Cat | Agree | S | C | E | K |
|---|---|---|---|---|---|---|
| B-140 | C7 | yes | ✓ | ✓ | ✓ | ✓ |
| B-037 | C2 | yes | ✓ | ✓ | ✓ | ✓ |
| B-030 | C1 | **no** | ✗ | ✓ | ✓ | ✗ |
| B-193 | C11 | yes | ✓ | ✓ | ✓ | ✓ |
| B-017 | C1 | yes | ✓ | ✓ | ✓ | ✓ |
| B-221 | C14 | yes | ✓ | ✓ | ✓ | ✓ |
| B-219 | C14 | yes | ✓ | ✓ | ✓ | ✓ |
| B-202 | C12 | **no** | ✓ | ✓ | ✓ | ✗ |
| B-180 | C10 | yes | ✓ | ✓ | ✓ | ✓ |
| B-174 | C10 | yes | ✓ | ✓ | ✓ | ✓ |
| B-047 | C2 | yes | ✓ | ✓ | ✓ | ✓ |
| B-132 | C7 | yes | ✓ | ✓ | ✓ | ✓ |
| B-056 | C3 | **no** | ✓ | ✓ | ✓ | ✗ |
| B-217 | C13 | yes | ✓ | ✓ | ✓ | ✓ |
| B-125 | C6 | yes | ✓ | ✓ | ✓ | ✓ |
| B-146 | C8 | yes | ✓ | ✓ | ✓ | ✓ |
| B-058 | C3 | yes | ✓ | ✓ | ✓ | ✓ |
| B-011 | C1 | **no** | ✓ | ✓ | ✓ | ✗ |
| B-102 | C5 | yes | ✓ | ✓ | ✓ | ✓ |
| B-123 | C6 | **no** | ✗ | ✓ | ✓ | ✓ |
| B-151 | C8 | yes | ✓ | ✓ | ✓ | ✓ |
| B-153 | C8 | yes | ✓ | ✓ | ✓ | ✓ |
| B-215 | C13 | yes | ✓ | ✓ | ✓ | ✓ |
| B-134 | C7 | yes | ✓ | ✓ | ✓ | ✓ |
| B-208 | C13 | yes | ✓ | ✓ | ✓ | ✓ |
| B-090 | C4 | **no** | ✓ | ✓ | ✓ | ✗ |
| B-071 | C4 | yes | ✓ | ✓ | ✓ | ✓ |
| B-103 | C5 | **no** | ✓ | ✓ | ✓ | ✗ |
| B-156 | C9 | yes | ✓ | ✓ | ✓ | ✓ |
| B-101 | C5 | yes | ✓ | ✓ | ✓ | ✓ |
| B-227 | C14 | **no** | ✓ | ✓ | ✓ | ✗ |
| B-117 | C6 | yes | ✓ | ✓ | ✓ | ✓ |
| B-131 | C7 | yes | ✓ | ✓ | ✓ | ✓ |
| B-107 | C5 | **no** | ✓ | ✓ | ✓ | ✗ |
| B-173 | C10 | yes | ✓ | ✓ | ✓ | ✓ |
| B-183 | C11 | yes | ✓ | ✓ | ✓ | ✓ |
| B-072 | C4 | yes | ✓ | ✓ | ✓ | ✓ |
| B-041 | C2 | **no** | ✓ | ✓ | ✓ | ✗ |
| B-054 | C3 | yes | ✓ | ✓ | ✓ | ✓ |
| B-067 | C3 | yes | ✓ | ✓ | ✓ | ✓ |
| B-007 | C1 | **no** | ✗ | ✗ | ✓ | ✓ |
| B-024 | C1 | yes | ✓ | ✓ | ✓ | ✓ |
| B-014 | C1 | yes | ✓ | ✓ | ✓ | ✓ |
| B-075 | C4 | yes | ✓ | ✓ | ✓ | ✓ |
| B-069 | C3 | yes | ✓ | ✓ | ✓ | ✓ |
| B-029 | C1 | yes | ✓ | ✓ | ✓ | ✓ |
| B-209 | C13 | yes | ✓ | ✓ | ✓ | ✓ |
| B-083 | C4 | yes | ✓ | ✓ | ✓ | ✓ |
| B-111 | C6 | yes | ✓ | ✓ | ✓ | ✓ |
| B-046 | C2 | **no** | ✓ | ✓ | ✓ | ✗ |
| B-157 | C9 | yes | ✓ | ✓ | ✓ | ✓ |
| B-033 | C2 | **no** | ✓ | ✓ | ✓ | ✗ |
| B-198 | C12 | yes | ✓ | ✓ | ✓ | ✓ |
| B-192 | C11 | yes | ✓ | ✓ | ✓ | ✓ |
| B-164 | C9 | yes | ✓ | ✓ | ✓ | ✓ |
| B-021 | C1 | yes | ✓ | ✓ | ✓ | ✓ |
| B-109 | C5 | yes | ✓ | ✓ | ✓ | ✓ |
| B-165 | C9 | yes | ✓ | ✓ | ✓ | ✓ |

## 5. Disagreement log — sample (13)

Per the plan, **the first rater wins on disagreement**; my view is logged, not imposed.
Kinds-only disagreements are convention differences, not legal errors — see §5.2.
Legal disagreements (4 in total, counting C13 B-213 in §6) carry a recommended
adjudication with one line of reasoning each.

### 5.1 Legal disagreements (3 in sample)

**D1 — B-030 (C1).** Q: husband stopped talking, gives no money; brother-in-law says
she must vacate the house; divorce contemplated but not decided.
- Mine: [bnss-144, pwdva-20, pwdva-17, pwdva-19], Magistrate, [quantum, residence].
- Draft: adds **pwdva-18** and kind **safety** ("Maintenance + residence + intimidation").
- My reasoning: no act of violence is described, only a brother-in-law's instruction
  to vacate; a protection order felt unwarranted.
- **Recommended adjudication: draft wins.** A communicated threat to dispossess the
  wife from the shared household is intimidation/economic abuse within the domestic
  relationship, and a protection order is the remedy that restrains it. (Thinnest of
  the four legal calls; an adjudicator could reasonably drop pwdva-18 — if dropped,
  the safety kind goes with it.)

**D2 — B-123 (C6).** Q: "I will be filing for divorce next week. We have a jointly
owned house and a 9-year-old son. I want the house divided and my son to stay with me."
- Mine: [hma-27, hma-13, gwa-1890], Family Court, [custody, fact].
- Draft: [hma-13, hma-27, **hma-26**], Family Court, [custody, fact].
- My reasoning: I defaulted custody to GWA 1890, the bank's usual custody label.
- **Recommended adjudication: draft wins.** "Will be filing next week" = proceeding
  being filed, so custody inside it falls under HMA 26 — the same pending/being-filed
  trigger the bank uses for HMA 27. (My error, not a draft error.)

**D3 — B-007 (C1).** Q: divorce pending; mother-in-law holds wedding jewellery; needs
money for two children while the case continues.
- Mine: [bns-316, bnss-144, pwdva-20], Magistrate, [quantum, recovery].
- Draft: adds **hma-24**, court **Family Court** ("Pending HMA proceeding: Stridhan
  recovery + maintenance, incl. HMA 24 interim; Family Court leads").
- My reasoning: I treated the money as ordinary BNSS 144/PWDVA 20 maintenance.
- **Recommended adjudication: draft wins.** Money "for my two children while the case
  continues" in a pending divorce is maintenance pendente lite under HMA 24, and the
  Family Court hearing the divorce is the lead forum — consistent with B-117, where I
  independently reached hma-24/Family Court and agreed with the draft.

### 5.2 Kinds-only disagreements (10 in sample) — draft stands, convention to be written down

The draft applies three escalation-kind conventions systematically; my blind rating
under-applied all three. These are **not** legal disagreements. First rater wins;
the freeze note should state each rule explicitly so it is not mistaken for rater whim.

**(a) The `fact` kind — 8 items.** The draft adds `fact` wherever an open or disputed
fact exists. Mine omitted it in all 8.

| ID | Open fact the draft marks |
|---|---|
| B-202 (C12) | Duration of interim maintenance disputed ("only till the divorce ends") |
| B-056 (C3) | Ownership of the bangles disputed ("family property, not mine") |
| B-090 (C4) | Gold sold; value/money owed is the open fact |
| B-103 (C5) | 16-year-old's wishes are the open fact |
| B-227 (C14) | Hidden cash income; proof of income is the open fact |
| B-107 (C5) | Rented-house living situation is the open fact |
| B-041 (C2) | Earning wife vs higher-earning husband; entitlement is the open fact |
| B-033 (C2) | No pay slips; proof of (non-)earnings is the open fact |

Verdict: the convention is coherent and applied consistently (the draft uses `fact`
44 times across the bank). **Draft stands.** Warning: if `fact` means "any open fact",
it is close to a catch-all — the freeze note should define its boundary tightly, or
kind-level scoring will punish any system that does not guess it on every
fact-sensitive question.

**(b) The `demand` kind — 1 item (B-011).** Draft adds `demand` where Stridhan recovery
is sought but no demand has yet been made ("I have not asked … for anything since I
left"). Coherent; **draft stands**. Same convention appears in C13 B-212 (see §6).

**(c) The `procedure` kind — 1 item (B-046).** Draft adds `procedure` where a procedural
relief is sought (a fixed monthly payment date for irregular maintenance). Coherent;
**draft stands**. Note a thin boundary: B-193 ("Which court do I go to?" — protection
order) carries the `court` kind, while B-205 (C13, "where do I apply for maintenance?")
carries `procedure` — both are "where do I apply" questions. The freeze note should
define the court-kind vs procedure-kind boundary; the distinction as applied is
defensible (forum choice vs process) but fine.

## 6. C13 Kannada check — all 16 items

**Kannada verdict: VERIFIED at working-reading level — with one open caveat (see below).**

I read Kannada script and understood all 16 questions (translations below are mine,
from the script). All 16 are fluent, natural Kannada: correct legal vocabulary
(ಜೀವನಾಂಶ maintenance, ವಿಚ್ಛೇದನ divorce, ಚಿನ್ನ gold, ಜನ್ಮ ಪ್ರಮಾಣಪತ್ರ birth certificate,
ಅತ್ತೆ mother-in-law), natural word order and case/gender agreement, no transliteration,
no visible machine-translation errors, no English leakage. The draft's own notes on
B-205/B-211/B-212/B-213 say "needs Kannada-fluent rater check before freeze" — this
section is that check, at the level stated in the caveat.

**Caveat, stated plainly:** I am not a native Kannada speaker. I read Kannada at a
working level — good enough to translate every item and rate its GT (15/16 section
agreement) — but I cannot claim native-level fluency verification. A native-speaker
confirmation before freeze is still recommended, and the Kannada check should be
recorded as verified-to-working-level, not native-verified.

C13 blind GT vs draft — **12/16 full agreement**; sections 15/16, court 16/16,
escalates 16/16, kinds 13/16.

| ID | My reading (translation) | My GT | Draft GT | Verdict |
|---|---|---|---|---|
| B-203 | Months passed, husband gave no money; help needed for son's education costs; which path? | bnss-144, pwdva-20; Magistrate; [quantum] | same | agree |
| B-204 | Husband earns ₹80,000/month, gives nothing; how much maintenance? | bnss-144, pwdva-20; Magistrate; [quantum] | same | agree |
| B-205 | Husband gave no money for 6 months; I don't work; where do I apply for maintenance? | bnss-144, pwdva-20; Magistrate; [quantum, **court**] | [quantum, **procedure**] | kinds-only; draft stands (§5.2c) |
| B-206 | Daughter's books and other study expenses; father gives nothing | bnss-144, pwdva-20; Magistrate; [quantum] | same | agree |
| B-207 | Daughter should stay with me; father wants to keep her at his house | gwa-1890; Family Court; [custody] | same | agree |
| B-208 | After divorce, with whom will my son stay? I want him with me | gwa-1890; Family Court; [custody] | same | agree |
| B-209 | Husband took my son to his native place; I want the child back with me | gwa-1890; Family Court; [custody] | same | agree |
| B-210 | Gold bangles from parents at marriage are with mother-in-law; she refuses to return | bns-316; Magistrate; [recovery] | same | agree |
| B-211 | Husband sold my gold chain and spent the money; I want the money back | bns-316; Magistrate; [recovery] | [recovery, **fact**] | kinds-only; draft stands (§5.2a) |
| B-212 | My gold is at mother-in-law's house; I have not asked for it; how do I get it back? | bns-316; Magistrate; [recovery] | [recovery, **demand**] | kinds-only; draft stands (§5.2b) |
| B-213 | Husband threw me out of the house; I want to stay in the same house | pwdva-17, pwdva-19; Magistrate; [residence] | adds **pwdva-18**; [residence, **safety**] | **legal disagreement — see D4** |
| B-214 | House I lived in is registered in husband's name; he now denies me entry; what is the remedy? | pwdva-17, pwdva-19; Magistrate; [residence] | same | agree |
| B-215 | Husband assaults me, gives no household money; daughter must stay with me; what action? | pwdva-18, bnss-144, pwdva-20, gwa-1890; Family Court; [safety, quantum, custody] | same | agree |
| B-216 | I want a divorce; husband won't return my gold or give me money | hma-13, bns-316, bnss-144, pwdva-20; Family Court; [quantum, recovery] | same | agree |
| B-217 | Child's birth certificate not received; how to get it? | births-deaths-act-1969; Registrar; [procedure] | same | agree |
| B-218 | Landlord locked my shop saying rent wasn't paid; what do I do? | []; none; True; [procedure] (handoff) | same | agree |

**D4 — B-213 (C13), the 4th legal disagreement.** Q: thrown out of the house, wants to
stay in the same house. Mine: pwdva-17 + pwdva-19 only. Draft: adds pwdva-18 + safety.
- **Recommended adjudication: draft wins.** Being thrown out of the shared household
  is itself an act of domestic violence, so a protection order accompanies the residence
  orders — and it follows the plan's own BX-15 convention (thrown-out → pwdva-17/18/19).
  My blind GT missed pwdva-18 here, as I did in the parallel case B-030 (D1).

## 7. Flagged item review — B-148 (C8)

Q: "I am a husband and my wife hits me when she drinks. I want protection from her."
Draft GT: `[]`, court `none`, escalates True, kinds `['procedure']`. Note: "Husband as
violence victim: no PWDVA order is available to a male claimant; handoff to criminal
complaint/lawyer, nothing in the label set fires."

**Verdict: empty GT is CORRECT. Draft stands.**

Reasoning: the Protection of Women from Domestic Violence Act 2005 defines the
"aggrieved person" as a woman (s.2(a)). A husband cannot obtain a PWDVA protection,
residence, monetary or compensation order, so no PWDVA label can fire — and no other
label in the bank's set covers a male victim's protection remedy (the only BNS label
in the set is bns-316, criminal breach of trust for Stridhan). The correct treatment
is exactly what the draft does: empty sections, no forum, escalates True with a
procedure handoff to a criminal complaint / human lawyer. This is also consistent
with the bank's own handling of male claimants elsewhere: B-146 and B-153 (husband
claiming child maintenance from the wife) correctly use bnss-144 only — BNSS 144 is
gender-neutral for children/parents, PWDVA is not. The role-reversal category (C8)
is doing its job here: a system that assumes the claimant is always the wife would
wrongly fire pwdva-18 for B-148.

## 8. Flagged item review — extended label set

Labels reviewed: hma-24, hma-25, hma-26, hma-9, hma-13b, pwdva-22. Usage in the draft
bank (230 questions): hma-24 ×6 (B-005, B-007, B-117, B-144, B-150, B-202),
hma-25 ×4 (B-022, B-119, B-154, B-201), hma-26 ×4 (B-006, B-099, B-115, B-123),
hma-13b ×5 (B-017, B-026, B-078, B-154, B-191), hma-9 ×1 (B-018), pwdva-22 ×1 (B-019).

**Verdict: ALL SIX are legitimate labels for the system to produce. None should be
replaced.** Each is a real provision, correctly applied in every use I spot-checked:

| Label | Provision | Use is correct because… |
|---|---|---|
| hma-24 | Maintenance pendente lite (HMA s.24) | All 6 uses are money "while the divorce case is pending" (B-117, B-202, B-007); the right provision, not BNSS 144. |
| hma-25 | Permanent alimony (HMA s.25) | All 4 uses are one-time/lump-sum settlement or an unpaid lump-sum alimony order (B-022, B-119, B-201); B-154 correctly notes HMA 25 is open to either spouse. |
| hma-26 | Custody of children in HMA proceedings (HMA s.26) | All 4 uses are custody sought while a divorce proceeding is pending or being filed (B-006, B-099, B-115, B-123). |
| hma-13b | Divorce by mutual consent (HMA s.13B) | All 5 uses are couples who both want the divorce (B-017, B-026, B-154). |
| hma-9 | Restitution of conjugal rights (HMA s.9) | Single use B-018: husband left home, wife wants him back + interim money — the textbook RCR fact pattern. |
| pwdva-22 | Compensation order (PWDVA s.22) | Single use B-019: broken arm, ₹60,000 hospital costs, medical costs claimed — textbook compensation fact pattern. |

Two qualifications:

1. **The hma-26 / gwa-1890 fork needs its rule written down.** The draft applies it
   consistently once the rule is inferred — custody inside a *pending or being-filed*
   HMA proceeding → hma-26; custody with divorce merely asked (B-028) or merely
   contemplated (B-017, B-026) → gwa-1890 — and that rule is the same pending/being-filed
   trigger the bank uses for HMA 27. But the rule is only inferable from individual
   gt_notes; it is not stated as a rule anywhere in the material I was allowed to read.
   Write it into the freeze note, or a future rater (or the system) will re-derive it
   differently. This fork is also the single hardest distinction in the bank for the
   system: it must detect proceeding status before it can choose the custody label.
2. **Label-set coverage is NOT verified by me.** I was forbidden from reading the
   graph/notebook/v5/v6 files, so I could not check whether the system can actually
   produce these six labels. They are legally legitimate, but if any is missing from
   the system's label set, every question using it is a guaranteed miss — the same
   warning the plan (§2.3) gives for a D1-C label. The freeze note / coordinator must
   confirm coverage before the run. (Thin-coverage note: hma-9 and pwdva-22 have one
   use each — that is a bank-design observation, not a defect.)

## 9. Summary for the freeze note

- **Agreement rate: 45/58 (77.6%) full agreement.** Sections 55/58, court 57/58,
  escalates 58/58, kinds 47/58.
- **Legal disagreements needing adjudication: 4** (B-030, B-123, B-007 in the sample;
  B-213 in C13). Recommended adjudication in all four: **draft wins** — my blind GT
  was the weaker one in each case (D1 is the thinnest; see §5.1).
- **Kinds-only disagreements: 13** (10 sample + 3 C13). All resolve to three draft
  conventions (`fact` for open/disputed facts, `demand` for Stridhan with no demand
  yet made, `procedure` for procedural relief). Draft stands; the freeze note must
  state all three rules, plus the court-kind vs procedure-kind boundary and the
  hma-26/gwa-1890 rule.
- **Kannada: verified at working-reading level** (16/16 fluent, no defects found;
  GT 12/16 full agreement, 15/16 sections). Native-speaker confirmation still
  recommended before freeze — I am not a native Kannada speaker.
- **B-148: empty GT CORRECT** — no PWDVA order is available to a male claimant
  (PWDVA s.2(a) "aggrieved person" is a woman); empty sections + procedure handoff
  is the right treatment.
- **Extended label set: all six legitimate, none to be replaced** — with the
  hma-26/gwa-1890 rule to be written down and system label-set coverage still to be
  confirmed by the coordinator (not verifiable from within my allowed scope).

## 10. Things I could not verify (blunt list)

- Whether the system (graph + notebook) can produce hma-24, hma-25, hma-26, hma-9,
  hma-13b, pwdva-22 — outside my allowed reading scope; must be confirmed before freeze.
- Native-level Kannada fluency — I read at working level, not as a native speaker.
- The exact intended definition of the `fact` escalation kind — I inferred it from
  44 uses in the draft; the v6 typed-kind design was outside my allowed reading scope.
- Whether the first rater's lead-forum rule for multi-issue questions matches mine in
  the unsampled 172 questions — in the sample we agreed on court 57/58 (the one miss,
  B-007, was my hma-24 miss, not a forum-rule dispute).
