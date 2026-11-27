# Brutal bank — third-reader adjudication

**Adjudicator:** third reader, independent of both raters and of all tuning work.
**Date:** 2026-11-27. **Work:** offline only.
**Scope honoured:** I read ONLY `brutal-bank-second-rater-report.md` (§5.1, §6 D4),
the draft bank entries named below (`brutal-bank-v1-draft.json`, question text +
draft GT + gt_notes only), and `brutal-test-200-plan.md` §2. I did NOT read any
v6-deep-dive, v6-lane, v5, notebook, live-result, or sealed-set file.
**Authority:** plan §2.2 step 3 — where the two raters disagree on a **legal** point,
a third qualified reader settles it and the reasoning is logged in one line per
adjudicated question. Each verdict below was reached independently from the
question text and the governing rule; the second rater's recommendations were
checked, not rubber-stamped.

---

## Part 1 — D1–D4 (second rater recommended DRAFT WINS on all four)

| Item | Verdict | GT after adjudication |
|---|---|---|
| D1 — B-030 (C1) | **DRAFT STANDS** | Unchanged: [bnss-144, pwdva-20, pwdva-17, pwdva-19, pwdva-18], Magistrate, true, [quantum, residence, safety] |
| D2 — B-123 (C6) | **DRAFT STANDS** | Unchanged: [hma-13, hma-27, hma-26], Family Court, true, [custody, fact] |
| D3 — B-007 (C1) | **DRAFT STANDS** | Unchanged: [bns-316, bnss-144, pwdva-20, hma-24], Family Court, true, [recovery, quantum] |
| D4 — B-213 (C13) | **DRAFT STANDS** | Unchanged: [pwdva-17, pwdva-19, pwdva-18], Magistrate, true, [residence, safety] |

**D1 — B-030: DRAFT STANDS.** Reasoning: a communicated demand that the wife vacate
the shared household is a threatened restriction of access to it, i.e. economic abuse
under PWDVA s.3 Expl. I(iv)(c), which a s.18 protection order is the remedy to restrain
— thinnest of the four calls, but the draft is right; dropping pwdva-18 would also drop
the safety kind.

**D2 — B-123: DRAFT STANDS.** Reasoning: "I will be filing for divorce next week" is a
definite statement of filing, so custody inside that proceeding falls under HMA 26 —
the same pending/being-filed trigger the bank uses for HMA 27; the second rater's GWA
default was the error here, not the draft.

**D3 — B-007: DRAFT STANDS.** Reasoning: money for two children "while the case
continues" in a pending divorce is maintenance pendente lite under HMA 24, and the
Family Court hearing the divorce is the lead forum — the second rater's
BNSS 144/PWDVA 20-only GT misses the interim-in-pending-proceeding dimension and gets
the forum wrong.

**D4 — B-213: DRAFT STANDS.** Reasoning: actual expulsion from the shared household is
itself an act of domestic violence (economic abuse, PWDVA s.3), so a s.18 protection
order accompanies the pwdva-17/19 residence orders — stronger than D1's mere threat,
and consistent with the plan's own BX-15 convention (thrown-out → pwdva-17/18/19).

**Part 1 outcome: I agree with the second rater on all four. No disagreement with the
second rater's recommendations in Part 1.** No GT changes arise from D1–D4.

---

## Part 2 — "Being filed" grey area: B-012, B-022, B-026 (C1), B-120 (C6)

**Governing rule (D1-A, settlement spec):** "being filed" = the user states they are
filing / will file an HMA petition; wanting divorce ≠ being filed; a conditional
"if I file" is hypothetical, not a statement of filing. HMA 27 is available only "in
any proceeding under this Act" (HMA s.27), so it fires only where a proceeding is
pending or being filed **and** there is jointly-owned property.

| Item | Verdict | Replacement GT (exact — apply as written) |
|---|---|---|
| B-012 | **GT CORRECTED** | sections [hma-13]; court Family Court; escalates true; kinds [fact, procedure] |
| B-022 | **GT CORRECTED** | sections [hma-13, hma-25]; court Family Court; escalates true; kinds [quantum, fact] |
| B-026 | **GT CORRECTED** | sections [hma-13b, gwa-1890]; court Family Court; escalates true; kinds [custody, fact] |
| B-120 | **GT CORRECTED** | sections [hma-13]; court Family Court; escalates true; kinds [fact] |

**B-012: GT CORRECTED (remove hma-27).** Reasoning: "I want a divorce" plus "I have
never filed anything" is a wish, not a filing — no proceeding exists for HMA 27; the
draft note's claim "Divorce being filed" is false on the question's own words.

**B-022: GT CORRECTED (remove hma-27; keep hma-25).** Reasoning: wanting a divorce is
not filing one, so no proceeding exists for HMA 27; the one-time-settlement ask stays
labelled hma-25 (see note on the hma-25 convention below).

**B-026: GT CORRECTED (remove hma-27).** Reasoning: "we both want" a mutual divorce is
a shared wish, not a filing — no proceeding for HMA 27; custody stays GWA 1890 under
the bank's own contemplated-divorce rule (cf. B-116), and hma-13b stands as the divorce
route they want.

**B-120: GT CORRECTED (remove hma-27).** Reasoning: "If I file for divorce" is expressly
conditional and hypothetical, not a statement of filing — the draft note's convention
"Conditional filing = being filed" directly contradicts the D1-A rule.

**Note on B-022 / hma-25 (flagged, not silently decided):** strictly, HMA s.25 also
presupposes a decree under the Act, so the same "no proceeding" logic could be run
against hma-25. I retain it because the bank labels a lump-sum settlement ask as
hma-25 by the relief sought (second rater §8 verified all four hma-25 uses, including
B-022, as correct), and removing it would leave the settlement ask unlabeled. The
freeze note should record this explicitly: **hma-25 is relief-labelled, while
hma-24 / hma-26 / hma-27 are proceeding-gated** — or the coordinator may prefer to
revisit hma-25 under the strict reading. Either way, it is a convention to be written
down, not left implicit.

---

## Part 3 — C6 audit (B-111–B-126): hma-27 presence/absence vs the rule

Rule applied per item: hma-27 present ⟺ proceeding pending or being filed **and**
jointly-owned property in issue; otherwise absent. (hma-26/hma-24 checked in passing;
no errors found there.)

| ID | Proceeding status + property | hma-27 in draft GT | Verdict |
|---|---|---|---|
| B-111 | Petition running 1 year; joint flat | present | CORRECT |
| B-112 | "I want a divorce"; joint house — wish, not filing | present | **ERROR — GT CORRECTED: sections [hma-13]; court Family Court; escalates true; kinds [fact]** |
| B-113 | Neither filed anything; joint flat | absent (GT []) | CORRECT |
| B-114 | "Going to file next month"; joint plot | present | CORRECT ("going to file" = definite filing statement) |
| B-115 | Pending; custody only, no property | absent | CORRECT (no property issue) |
| B-116 | "Thinking of asking"; custody only | absent | CORRECT |
| B-117 | Pending 1 year; interim money, no property | absent | CORRECT (no property issue) |
| B-118 | No case yet; monthly money | absent | CORRECT |
| B-119 | Pending; joint shop | present | CORRECT |
| B-120 | "If I file"; joint car — hypothetical | present | **ERROR — see Part 2** |
| B-121 | No case; house solely in husband's name | absent (GT []) | CORRECT (no proceeding AND solely owned) |
| B-122 | Pending 1+ year; joint flat sold during proceedings | present | CORRECT |
| B-123 | "Will be filing next week"; joint house | present | CORRECT (see D2 above) |
| B-124 | "Want a divorce"; monthly money, no joint property | absent | CORRECT (no joint property in any event) |
| B-125 | Pending; joint house (+ gold) | present | CORRECT |
| B-126 | Pending; joint flat | present | CORRECT |

**Additional errors found by the audit (beyond the four flagged items): 1 — B-112.**
Its draft note repeats the same false premise ("Divorce being filed") as B-012/B-022/
B-026. Replacement GT: sections [hma-13]; court Family Court; escalates true; kinds
[fact]. Reasoning: "I want a divorce" is a wish, not a filing; no proceeding exists
for HMA 27.

---

## Verdict on the bank's "being filed" convention

**The convention as applied in the draft is WRONG, and I say so plainly.** The draft
notes treat "I want a divorce" (B-012, B-022, B-112), "we both want a mutual divorce"
(B-026), and a conditional "if I file" (B-120) as "being filed" — in B-120 the note
even states "Conditional filing = being filed" as if it were the rule. That is the
opposite of D1-A. The first rater's header adopting conditional "if I file" as being
filed does not survive the test against the rule; a header convention cannot override
the settlement spec.

**The rule that should be written into the freeze note:**

> "Being filed" means only a definite statement that the user is filing, will file,
> or is going to file an HMA petition (with or without a timeframe — e.g. "will be
> filing next week", "going to file next month"). Wanting a divorce, contemplating
> one ("thinking of", "have not decided"), a mutual wish ("we both want"), and a
> conditional ("if I file") are **not** being filed. HMA 27 (and HMA 24 / HMA 26)
> fire only where a proceeding is pending or being filed under that definition.

**Total hma-27 errors from this convention: 5 items** — B-012, B-022, B-026, B-120
(flagged) plus B-112 (found by the C6 audit). All five need the replacement GTs above
applied before freezing, **and their gt_notes corrected too** (each currently asserts
the false "being filed" premise). No other C6 item is affected. The rest of C6 is
clean and internally consistent — notably B-113/B-121 (correctly empty) and B-114/B-123
(correctly treating definite future filing as being filed) show the rater applied the
right rule everywhere except the "want / conditional" cases.

## Summary of all GT changes to apply before freeze

1. B-012 → [hma-13], Family Court, true, [fact, procedure] (+ fix gt_note).
2. B-022 → [hma-13, hma-25], Family Court, true, [quantum, fact] (+ fix gt_note).
3. B-026 → [hma-13b, gwa-1890], Family Court, true, [custody, fact] (+ fix gt_note).
4. B-120 → [hma-13], Family Court, true, [fact] (+ fix gt_note).
5. B-112 → [hma-13], Family Court, true, [fact] (+ fix gt_note).
6. Freeze note: record the "being filed" rule as stated above, and the hma-25
   relief-labelled vs hma-24/26/27 proceeding-gated distinction (or the coordinator's
   decision if hma-25 is revisited).
7. No changes from Part 1 (D1–D4: draft stands on all four).
