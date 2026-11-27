# Phase A gate A7 — Brief inconsistency reconciliation (Fresh-20)

- **Lane:** A (implementation swarm)
- **Date:** 2026-11-27
- **Verdict: RECONCILED (category gap) + ONE OPEN REPORTING ERROR (FN gap).**
- **Method:** aggregates only — `results/live-laya-v7-results.md` §1,
  `docs/recall_status.md` §11, `docs/recall_consultation_brief.md`
  §2, `docs/10x_plane.md` line 30, `docs/v6-lane5-validation.md`
  §§2.1–2.2 (freeze-note composition). **Sealed text was never opened.**
  No sealed file was read, listed, hashed, or touched for this gate.

## The two discrepancies (as flagged by both ChatGPT consultations)

1. **Category breakdown covers 18 questions / 5 exact, not 20 / 7.**
2. **Itemised FNs sum to 27, not the reported 28.**

## Discrepancy 1 — RESOLVED: the two unaccounted questions are the birth-certificate pair, both exact

Headline aggregates (all three sources agree):

| Source | Exact | TP / FP / FN | Silent |
|---|---|---|---|
| `results/live-laya-v7-results.md` §1 (v7 live run, Run 1 = Run 2) | **7/20** | 38 / 5 / 28 | 2 |
| `docs/recall_consultation_brief.md` §2 | 7/20 (35%) | 38 / 5 / 28 | 2 |
| `docs/recall_status.md` §11 | 7/20 | 38 / 5 / 28 | — |

Internal consistency of the headline: TP + FN = 66 GT sections;
38/66 = 0.5758 = the reported micro-recall; TP + FP = 43 predicted;
38/43 = 0.8837 = the reported micro-precision. The headline is
self-consistent — the breakdown is the odd one out.

Category breakdown (identical in the brief §2 and `docs/10x_plane.md`
line 30):

| Category | Exact |
|---|---|
| divorce | 0/2 |
| residence | 0/2 |
| stridhan | 0/3 |
| custody | 1/3 |
| violence | 1/2 |
| maintenance | 2/4 |
| out-of-scope | 1/2 |
| **Total** | **5/18** |

The freeze-note composition of the sealed 20
(`docs/v6-lane5-validation.md` §2.1, verified from the freeze note's
own metadata — not from sealed text):

> maintenance 4, custody 3, Stridhan 3, residence 2, violence 2,
> divorce 2, **birth cert 2**, OOS 2 (= 20)

The breakdown's seven categories reproduce seven of these eight
composition categories with **exactly matching counts** (maintenance 4,
custody 3, stridhan 3, residence 2, violence 2, divorce 2, OOS 2).
The sole absent category is **birth cert, 2 questions**. Corroboration
from the same validation doc (§2.2): "dropping F17/F18 (birth cert)"
— the two birth-certificate questions are F17/F18.

Arithmetic (categories partition the 20 questions by primary category;
the composition table sums exactly to 20, so each question is counted
once):

- Questions: 18 listed + 2 birth-cert = 20 ✓
- Exact: 5 listed + x birth-cert = 7 headline ⇒ **x = 2**

**Reconciled category table (Fresh-20):** divorce 0/2, residence 0/2,
stridhan 0/3, custody 1/3, violence 1/2, maintenance 2/4,
out-of-scope 1/2, **birth cert 2/2** — total **7/20** ✓.

Status of this finding: an inference from logged aggregates, not a
reading of sealed text. It is the only arithmetic-consistent
completion — the alternative (wrong denominators in the breakdown)
would require the breakdown to disagree with the independently
recorded freeze-note composition, which it does not on any of the
seven categories it lists. The "two unaccounted exact questions" are
therefore explained, not merely flagged.

### Parallel check — Kannada-8 resolves the same way

Kannada-8 composition (`v6-lane5-validation.md` line 41, from the
freeze note): KN1 maintenance, KN2 custody, KN3 Stridhan, KN4
residence, KN5 divorce-asked multi-issue, KN6 divorce-not-asked,
KN7 birth certificate, KN8 out-of-scope. Breakdown (brief §2,
10x_plane line 31): divorce 0/2 (KN5, KN6), residence 0/1 (KN4),
stridhan 0/1 (KN3) — 4 questions, 0 exact. Headline 4/8 ⇒ the
remaining four (KN1 maintenance, KN2 custody, KN7 birth cert, KN8
OOS) must be **4/4 exact**. Same method, same conclusion shape. The
Kannada-8 FN list sums correctly (2+1+1+1+1+1 = 7 = headline 7), so
Kannada-8 has no FN discrepancy — only the category-coverage gap,
now resolved.

## Discrepancy 2 — OPEN REPORTING ERROR: one FN is missing from the itemised list

Itemised Fresh-20 FNs (identical in all sources):

hma-27 4; welfare-principle 3; pwdva-17 3; pwdva-18 3; pwdva-19 3;
hma-13 2; hma-24 2; gwa-1890 2; hmga-1956-s6 2; hma-25 1; bns-316 1;
hma-26 1 — **sum = 27**, headline = **28**.

The FP list is consistent (pwdva-20 2, hma-13 2, bnss-144 1 = 5 =
headline FP 5), and the headline FN = 28 is consistent with
micro-recall (38/66). So the headline is right and the itemised list
is short by exactly **one FN whose section is unknown from the
aggregates**. It cannot be identified without per-question data, and
per-question data lives in the sealed file, which this gate does not
open. Candidates cannot be ranked honestly from aggregates: any of
the 12 listed sections (or an unlisted 13th) could carry the extra
instance.

**Flagged as a reporting error in the brief/plan lineage** (the list
was copied from the 10x plan into the consultation brief, and both
ChatGPT consultations caught the same shortfall). The next evaluation
report must either (a) re-derive the FN-by-section list from the
sealed run logs that are already filed (`results/live-laya-v7-run1.log`
/ `run2.log` — aggregates only, no sealed text) and correct the
list, or (b) carry the list as "27 itemised + 1 unitemised" until a
sealed re-run regenerates it. Do not silently change 28 → 27 (that
would break micro-recall) and do not invent a 28th entry.

Methodological note: the category table counts *questions* by primary
category; the FN list counts *section instances* (a multi-issue
question contributes several FNs). The two cannot be summed against
each other directly — that is why discrepancy 1 (a question-count
gap) is resolvable from the composition table while discrepancy 2
(a section-instance gap) is not resolvable from aggregates at all.

## Bottom line for the next evaluation report

- Use **7/20, TP/FP/FN 38/5/28** as the Fresh-20 headline (unchanged).
- Use the reconciled category table **including birth cert 2/2**.
- Carry the FN list as **27 itemised + 1 unitemised (section unknown)**.
- Kannada-8: **4/8**, categories divorce 0/2, residence 0/1, stridhan
  0/1, maintenance / custody / birth cert / OOS 4/4 combined
  (per-question split across those four is not in the aggregates).
