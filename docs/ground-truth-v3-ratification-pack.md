# Ground-Truth v3 Ratification Pack — PREPARED, PENDING independent-rater ratification

**Status: PREPARED — PENDING independent-rater ratification (human step).**
**This pack does NOT create or freeze ground-truth-v3.**
**It does NOT modify `ground-truth/ground-truth-v2-hma27-A.json` (frozen, SHA-256
`87818b1b659583bf06a25280a6b53dabedf65f29cab99058f02b8ed31c9ac97e`).**

- Prepared by: Lane 07 (V71-P4-4 prep), 2026-11-27, working copy `~/workspace/laya-v71-work`.
- Plan ref: `docs/10x_plane.md` §4.4 (V71-P4-4), §8.1 Phase 0.
- Base: ground-truth v2 (D1-A, 53 sections across 16 questions: K0, H1–H15).
  All per-question deltas below were derived from the v2 file's `gt_ids`,
  `gt_court` and `gt_escalation_kinds` fields as read by Lane 07. No sealed
  test-bank file was opened for this pack; sealed deltas in §5 are recorded
  from the plan / architecture doc / freeze note as cited, not from sealed text.
- What happens next (not in this pack): the independent rater decides every
  item marked **RATER DECIDES**, signs the adjudication record in §7, and
  only then does the coordinator create `ground-truth-v3` as a NEW file.
  Per gate §6.1, creating v3 invalidates all prior 16-Q runs — they must be
  re-run and re-filed under v3 (same rule as the D1-A erratum,
  `ground-truth/ground-truth-v2-erratum.md` §4).

## 0. Pre-ratification blocker checklist (must clear before the rater signs)

- [ ] **Recovery-text fix (erratum §6).** The Lane 2 `recovery` escalation
      text still says civil recovery is "under HMA s.27". Under D1-A that is
      wrong on K0 and H15. Amend it (civil recovery in the Family Court,
      without naming s.27) before any run scores those kinds — otherwise the
      removed label re-enters through prose. Same for the BNS 316 node
      exclusion text naming HMA s.27 as the civil return route.
- [ ] **D5 / D7 / D11 carried, not decided here.** D5 (H2/H4 escalate
      expectations + custody/residence kinds), D7 (H4 excludes PWDVA 20 —
      confirm-as-is recommended by v6 Lane 3 §3.2), D11 (H15
      `demand_made: true` as the inference "sale = refusal evident from
      conduct") are still outstanding at v2 freeze time (erratum §6). The
      rater may settle them in the same sitting, but this pack does not
      pre-decide them.
- [ ] **Sealed-set HMA 27 question (erratum §4).** The sealed fresh-20 and
      Kannada-8 sets also contain HMA 27 in their GT. No sealed run may be
      scored until the same D1 question is decided for them (see §5).

## 1. D-V4-1 — Custody vocabulary unification (statutory_primary)

**Draft change.** One canonical schema in ground-truth-v3 (and brutal-bank-v2):
`kept_ids` = statutory sections only. For custody, `kept_ids` is `["gwa-1890"]`
or `["hma-26"]`; `"hmga-1956-s6"` and `"welfare-principle"` move to
`applied_principles` and are always rendered in prose. This eliminates the
16-Q/Sealed vs Brutal-230 split (plan §4.4; `docs/v4-decision-graph-architecture.md`
§5.1, `v4-canonical`).

**Exact per-question effect on v2 `gt_ids` (rater to confirm each row):**

| Q | v2 `gt_ids` (count) | v3 `kept_ids` (count) | v3 `applied_principles` |
|---|---|---|---|
| K0 | bnss-144, pwdva-20, gwa-1890, hmga-1956-s6, welfare-principle, bns-316, pwdva-17, pwdva-18, pwdva-19 (9) | bnss-144, pwdva-20, gwa-1890, bns-316, pwdva-17, pwdva-18, pwdva-19 (7) | hmga-1956-s6, welfare-principle |
| H2 | gwa-1890, hmga-1956-s6, welfare-principle (3) | gwa-1890 (1) | hmga-1956-s6, welfare-principle |
| H5 | hma-13, bnss-144, pwdva-20, pwdva-18, gwa-1890, hmga-1956-s6, welfare-principle (7) | hma-13, bnss-144, pwdva-20, pwdva-18, gwa-1890 (5) | hmga-1956-s6, welfare-principle |
| H14 | hma-13, hma-26, hmga-1956-s6, welfare-principle, hma-24, bnss-144, pwdva-20 (7) | hma-13, hma-26, hma-24, bnss-144, pwdva-20 (5) | hmga-1956-s6, welfare-principle |
| All other 12 questions | — | unchanged | — |

**Totals.** v2 has 53 sections in `gt_ids`. Under D-V4-1 alone, v3 `kept_ids`
total = **45** (8 moved to `applied_principles`: 2 each on K0/H2/H5/H14).
Courts are unaffected: K0 stays `['Family Court', 'Magistrate']`
(gwa-1890 supplies Family Court), H2 stays `['Family Court']`, H5/H14 stay
`['Family Court', 'Magistrate']`. Escalation kinds are unaffected by D-V4-1
alone (`custody` kind still fires on gwa-1890/hma-26 in kept).

**RATER DECIDES:** confirm the four rows above (including that
`applied_principles` are scored as present-but-not-kept, never as missing
sections, and that prose always renders them).

## 2. D-V4-2 — 16-Q alignment: separating conflated items

Five sub-items. (a)–(c) are drafted as changes; (d)–(e) are drafted as
explicit either/or decisions because the plan and the v6 record pull in
opposite directions.

### (a) H3 / H10 / H15 court fix — `['Family Court', 'Magistrate']` → `['Magistrate']`

**Draft change (Option C-1, v4-arch §5.2).** v2 kept the dual court on the
grounds that the civil Stridhan recovery route is still a Family Court route
under FCA s.7(1) Expl. (c). But after D1-A the only kept section on H3/H15
is `bns-316`, and on H10 the kept set is `bns-316 + bnss-144 + pwdva-20` —
and `court_for()` maps `bns-316 -> ['Magistrate']`, as does Brutal-230 B-192
(`bns-316` only → `['Magistrate']`). Align 16-Q with D1-A + B-192 (Lead-Forum
Rule): H3, H10, H15 `gt_court` become `['Magistrate']`.

- Rejected alternative (C-2): emitting `'Family Court'` alongside `'Magistrate'`
  whenever `bns-316` fires passes the Brutal-230 containment check but fails
  the C11 strict-single-forum UX rule and only masks the v2 leftover.
- K0 is NOT in this fix: its court stays `['Family Court', 'Magistrate']`
  because `gwa-1890` (custody) supplies Family Court.

**RATER DECIDES:** confirm C-1 for H3/H10/H15 (or record a reasoned C-2).

### (b) Safety escalation kind on K0 / H4 / H5 / H6 / H13

**Draft change.** Add `'safety'` to `gt_escalation_kinds` on all five.
Current v2 kinds and the draft result:

| Q | v2 kinds | v3 kinds (draft) | Ground |
|---|---|---|---|
| K0 | quantum, custody, residence, recovery | + safety | pwdva-18 in GT |
| H4 | residence | residence, safety | pwdva-18 in GT |
| H5 | quantum, custody | quantum, custody, safety | pwdva-18 in GT |
| H6 | quantum, residence | quantum, residence, safety | pwdva-18 in GT (see (d) — if (d) drops pwdva-18, H6 safety falls away with it) |
| H13 | quantum, residence | quantum, residence, safety | pwdva-18 in GT |

Consistent with Brutal-230, where `pwdva-18 -> safety` holds across 31/32
items, and with Sealed F13/F14/F15/KN5 which require `safety` in the scoring
kinds (v4-arch §6.1 note 1). The alternative — scoring 16-Q with a legacy
compat kind set that excludes `safety` while Brutal-230 uses the full 9-kind
set — is recorded here only as the fallback if the rater rejects the change.

**RATER DECIDES:** confirm the five additions (or the compat-fallback).

### (c) H12 procedure OOS handoff convention

**Draft position — open, two options.** v2 froze H12 as empty GT, empty court,
`escalates=False`, kinds `[]`, with the note "no kind may ever fire on empty
kept". Brutal-230 C10 items (B-171..182), B-113/B-121/B-148/B-218 and Sealed
F20 expect `escalates=True` with kind `procedure` (handoff to a human lawyer /
civil forum) on the same shape of question; B-069/B-156 expect
`escalates=False` (`no_dispute_empty`). H12 is an identical sibling-property
dispute to B-172.

- **Option 1 — align:** H12 becomes `escalates=True`, kinds `['procedure']`
  (OOS handoff), `kept_ids`/`court` stay empty. Aligns 16-Q with C10/F20.
- **Option 2 — keep legacy, flagged:** H12 stays empty/False, and the
  `h12_stays_empty` compat assertion (`kept==[] and court==[]`) is kept in
  the scorer so the legacy convention is visible, not silent.

**RATER DECIDES:** Option 1 or 2, with reasons. Either way the choice must be
recorded in the v3 header so a later reader knows it was deliberate.

### (d) H6 pwdva-18 delta — legacy triple bundle vs decoupled graph

**The conflict, stated plainly.** v2 GT for H6 is the legacy triple bundle
`bnss-144, pwdva-20, pwdva-17, pwdva-18, pwdva-19` (5 sections), with v2
facts `violence: False, residence_claim: True, money_fact: True`. The v7
Graph v4 decoupled pwdva-17/19 from pwdva-18: pwdva-18 now needs violence,
coercive eviction/lockout, or eviction pressure — and H6 states a co-living
wish with no violence and no lockout, so v7 does not fire pwdva-18 on H6.

- **Option A — keep pwdva-18 in H6 GT (legacy bundle stands).** Then the
  graph's decoupling is the error to fix for H6-shaped facts, and the system
  scores a pwdva-18 false negative on H6 until Stage 2 changes. v3 H6 stays
  5 sections; (b) safety on H6 stands.
- **Option B — drop pwdva-18 from H6 GT.** v3 H6 becomes 4 sections
  (`bnss-144, pwdva-20, pwdva-17, pwdva-19`); the decoupling is vindicated;
  the (b) safety kind on H6 falls away with pwdva-18 (H6 kinds become
  `['quantum', 'residence']` as in v2). Contrast control: H4 KEEPS pwdva-18
  (lock changed / entry denied = dispossession backed by threat — v6 Lane 3
  §3.2), so dropping H6's pwdva-18 does not touch H4.

**RATER DECIDES:** A or B, with reasons. This is a GT change either way only
under B; under A it is a system-change requirement, to be logged as such.

### (e) H14 hma-13 delta — governing-section vs relief-sought-only (D6)

**The conflict, stated plainly.** v2 GT for H14 keeps `hma-13` (7 sections:
`hma-13, hma-26, hmga-1956-s6, welfare-principle, hma-24, bnss-144, pwdva-20`;
H14 is the ONLY question with `proceeding_pending: true`). v6 Lane 3 §3.1
calls this the thinnest frozen call: on a strict relief-sought-only reading,
H14's GT would name only reliefs/routes, and hma-13 names the governing
section of the pending proceeding, not a relief sought. On the
governing-section reading it stays.

- **Option A — keep (recommended by v6 Lane 3, as a rater-confirmed judgement
  call, not settled law).** No GT change; no invalidation arises from D6.
- **Option B — drop.** v3 total falls by 1 on this item alone (53 → 52
  before D-V4-1's 8 moves; 45 → 44 after D-V4-1). GT change → invalidates all
  prior runs; AND the notebook's pending-divorce fire of hma-13 must be gated
  in the same change, or H14 becomes non-exact by false positive.

**RATER DECIDES:** A or B, with reasons. The rater may reasonably choose B;
the pack does not pre-decide it.

## 3. D-V4-3 — hma-25 lump_sum_settlement confirmation

**Draft confirmation (rater to sign, not a new rule).** The adjudicated
"relief-labelled hma-25" rule: `hma-25` is eligible iff `decree` OR
(`lump_sum_settlement` AND (`divorce_asked` OR `proceeding_pending_hma`)).
Authority: `docs/v4-decision-graph-architecture.md` §7 / D-V4-3; the graph
already implements it (`src/laya_v7_graph.py:426-427` eligible,
`:435-437` conditional + `gated_out` otherwise).

- **Items it covers:** B-022, B-119, B-154 (and B-201 per v4-arch §7) —
  lump-sum / permanent-alimony-instead-of-monthly-subsistence cases. These
  must NOT trigger false `Fb` (forbidden-proposed-before-gate) penalties.
- **What it does not change:** strict pre-decree `Fb = 0` on standard
  maintenance (no `lump_sum_settlement`, no decree) is preserved; the
  forbidden "HMA 25 with no decree" fires (H5/H9 in the retest) remain
  forbidden, and Sukhdev Singh gives them no support (its holding widens
  *which* decrees count, it does not remove the decree requirement —
  see `legal/verified_authorities.json`, sukhdev entry, limits).
- **RATER DECIDES:** confirm the rule as adjudicated (or amend it, stating
  the amended rule verbatim). If confirmed, the scorer's `Fb` accounting for
  B-022/B-119/B-154 is ratified as-is.

## 4. D-V4-4 — Sealed sensitivity documentation (frozen deltas, not changes)

**Draft documentation for the v3 header / sensitivity annex.** These are
FROZEN discrepancies in the sealed sets, recorded so no sealed run is ever
scored as if they did not exist. Lane 07 opened no sealed file for this pack;
the deltas below are taken from the plan (§4.4), the architecture doc (§5.2)
and the brutal-bank freeze note (§12) as cited.

1. **Pre-D1-A hma-27 in sealed GT — F8, F9, F10, F16, KN3.** The sealed
   fresh-20 / Kannada-8 ground truths still carry the known-wrong HMA 27
   label (same D1-A error corrected in 16-Q v2). A sealed run scored under
   that GT inherits the error. **Action:** decide the sealed D1 question
   before any sealed run is scored; document the affected items as a frozen
   sensitivity report (post-D1-A vs pre-D1-A scoring), and commission a
   sealed-v2 post-gate if the rater aligns the sealed GT.
2. **Bengaluru FCA s.7(2)(a) Family Court deltas — F1, F2, KN1.** Sealed
   maintenance-only GT expects `['Family Court']` on `bnss-144 + pwdva-20`
   (Bengaluru Family Court jurisdiction under FCA s.7(2)(a)), whereas 16-Q
   (H1/H8/H9/H11) and all 100+ Brutal-230 maintenance items expect
   `['Magistrate']`. **Action:** do NOT change `bnss-144 -> Magistrate`
   (that would break 16-Q and Brutal-230). Record F1/F2/KN1 as a known frozen
   sealed-GT convention delta, with the Bengaluru FCA s.7(2)(a) concurrent-
   jurisdiction nuance noted in prose (plan §6.2, V71-P6-2); optionally
   ratify the alignment in sealed-v2 after the gate passes.

**RATER DECIDES:** confirm both deltas are documented as frozen sensitivity
reports (not silently corrected), and state whether sealed-v2 commissioning is
approved in principle.

## 5. Projected v3 totals (for the rater to verify after deciding)

| Scenario | v3 `kept_ids` total | Change vs v2 (53) |
|---|---|---|
| D-V4-1 only | 45 | −8 (moved to `applied_principles`, not deleted) |
| D-V4-1 + (d) Option B (drop H6 pwdva-18) | 44 | −9 |
| D-V4-1 + (e) Option B (drop H14 hma-13) | 44 | −9 |
| D-V4-1 + (d) B + (e) B | 43 | −10 |
| (a) court fix, (b) safety kinds, (c) either option | no count change | kinds/court only |

(H12 Option 1 changes kinds, not sections. D-V4-3 changes no GT content.
D-V4-4 changes no GT content — it documents sealed deltas.)

## 6. Gate §6.1 consequence (read before signing)

Creating ground-truth-v3 invalidates **all prior 16-Q runs** on the current
set — they must be re-run and re-filed under v3. No rating quoted from a
v2-scored run survives the change. The D2 gate (HMA 27 Stage 2 drop) already
shipped paired with v2; any further gate change implied by a decision above
(particularly (d) Option B or (e) Option B) must ship **in the same logged
change** as v3, so no run is ever scored with the gate on and the old GT, or
vice versa.

## 7. Adjudication record — template (rater to complete and sign)

> **Ground-truth-v3 adjudication record**
>
> - Rater name / role: ______________________ (independent of the tuning lanes)
> - Date / time (IST): ______________________
> - Base file reviewed: `ground-truth/ground-truth-v2-hma27-A.json`
>   (SHA-256 `87818b1b659583bf06a25280a6b53dabedf65f29cab99058f02b8ed31c9ac97e`)
> - This pack reviewed: `docs/ground-truth-v3-ratification-pack.md`
>   (Lane 07 prep, 2026-11-27)
> - Erratum reviewed: `ground-truth/ground-truth-v2-erratum.md` (D1-A, D3, D4)
> - Legal background reviewed: `docs/legal-decisions-v4.md` (Q1–Q3);
>   citation registry: `legal/verified_authorities.json`
>   (status at prep time: 1 verified_primary — Sukhdev Singh; 8 unverified)
>
> | Item | Decision | Reasoning (one line minimum) | GT effect |
> |---|---|---|---|
> | D-V4-1 custody unification (§1) | Confirm / Amend: ___ | | kept total → ___ |
> | D-V4-2(a) H3/H10/H15 court → Magistrate | Confirm C-1 / C-2 / Reject: ___ | | court only |
> | D-V4-2(b) safety kind K0/H4/H5/H6/H13 | Confirm / Amend: ___ | | kinds only |
> | D-V4-2(c) H12 convention | Option 1 (align) / Option 2 (legacy flagged): ___ | | kinds only |
> | D-V4-2(d) H6 pwdva-18 | Option A (keep) / Option B (drop): ___ | | −1 if B |
> | D-V4-2(e) H14 hma-13 (D6) | Option A (keep) / Option B (drop): ___ | | −1 if B |
> | D-V4-3 lump_sum_settlement rule | Confirm / Amend (state rule): ___ | | none |
> | D-V4-4 sealed sensitivity (F8/F9/F10/F16/KN3; F1/F2/KN1) | Document as frozen / Amend: ___ | | none (sealed-v2: Y/N) |
> | D5 / D7 / D11 (carried items, §0) | Settled here / Still open: ___ | | record |
> | Recovery-text fix (§0 blocker) | Verified done / Still open: ___ | | prose only |
> | **Final v3 kept_ids total** | **___ sections** | | |
>
> - Signature: ______________________
> - Note to coordinator: on signature, create `ground-truth-v3` as a NEW file
>   (never edit v2), copy this signed record into its header, trigger the
>   Gate §6.1 baseline re-run, and file the re-run results as new files only.
>
> _Template only — no signature exists yet. An unsigned pack authorises nothing._

## 8. Sources used for this pack (Lane 07 read only)

- `docs/10x_plane.md` §4.4, §8.1 (D-V4-1..4, Phase 0 gate).
- `ground-truth/ground-truth-v2-hma27-A.json` — `gt_ids` / `gt_court` /
  `gt_escalation_kinds` per question (aggregate fields only; question text
  not reproduced here).
- `ground-truth/ground-truth-v2-erratum.md` §§1–7 (D1-A diff, Astha Thakur
  verification scope, D3/D4 confirmations, outstanding D2/D5/D6/D7/D11, §6.1).
- `docs/legal-decisions-v4.md` Q1–Q3 (HMA 27 ancillary rule; H7 procedure
  escalation; Sukhdev Singh verification).
- `docs/v4-decision-graph-architecture.md` §§5.1–5.2, 6.1, 7 (D-V4-1..4
  drafting, C-1/C-2, safety alignment, lump-sum rule).
- `docs/v6-lane3-legal-decisions.md` §3.1 (H14/D6), §3.2 (H4/D7).
- `legal/verified_authorities.json` (Lane 07, this swarm) for the citation
  status carried into §7.
