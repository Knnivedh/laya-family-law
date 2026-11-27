# Brutal-test bank v1 — FREEZE NOTE

**Frozen file:** `brutal-bank-v1-frozen.json`
**SHA-256:** `934a2b2265ac137c96939e1fbeca3682a037010e42f972bfd459c2fcac4ec717`
**Frozen:** 2026-11-27 (IST). **Questions:** 230. **Status:** FROZEN.

**Freeze rule (plan §2.2):** GT is frozen before any run. After freeze, no GT edit is
permitted; a GT error found during/after a run is logged as a bank defect and fixed
only by a new bank version (bank v2) with a fresh freeze — never by editing this file.
The draft file (`brutal-bank-v1-draft.json`) is retained as the pre-adjudication record;
it differs from the frozen file by exactly the 5 adjudicated GT corrections listed in §4.

## 1. D1 branch applied: A

HMA s.27 is ancillary — it can only be pressed inside a pending HMA proceeding or one
being filed together with the claim, never freestanding; a BNSS/PWDVA/GWA case is not an
HMA proceeding. **"Being filed" ONLY on a definite filing / will-file / going-to-file
statement.** Wanting, contemplating, mutual wish, and conditional "if I file" are NOT
being filed (adjudicated 2026-11-27 — the first rater's wider convention, including
"conditional 'if I file' = being filed", was rejected). Divorce merely asked about,
contemplated, or undecided is NOT a pending proceeding. Jointly-owned property without
a pending/being-filed HMA proceeding carries NO `hma-27`.

9 questions carry `hma-27` in frozen GT, all verified pending/being-filed:
B-005, B-111, B-114, B-119, B-122, B-123, B-125, B-126, B-228.

## 2. Category counts (total 230)

| Cat | n | Cat | n |
|---|---|---|---|
| C1 multi-issue | 30 | C8 role reversal | 12 |
| C2 maintenance-only | 20 | C9 incidental money/gold | 16 |
| C3 Stridhan vs maintenance | 20 | C10 out-of-scope | 12 |
| C4 residence must-NOT-fire | 20 | C11 court/forum traps | 12 |
| C5 custody vs residence | 20 | C12 quantum disputes | 8 |
| C6 HMA 27/26 prereq | 16 | C13 Kannada script | 16 |
| C7 negation | 16 | C14 adversarial paraphrases | 12 |

Length mix: 47 one-liners, 10 long narratives, majority medium (2–3 sentences).
IDs B-001…B-230 in category order. Lead-forum rule (header, applied uniformly):
any HMA/GWA relief → Family Court; else any PWDVA/BNSS/BNS relief → Magistrate;
birth/death registration → Registrar; no family-law relief → none. A pending HMA
proceeding alone does not make the forum Family Court unless HMA/GWA relief is sought.

## 3. How the bank was built and checked

- **First rater** (independent of tuning): wrote all 230 questions + GT from
  `brutal-test-200-plan.md` §1–§7 + own legal knowledge only; did not read any
  v6/v5 reports, lane files, notebooks, live JSONs, or sealed-set text.
- **Second rater** (independent, blind): stratified random sample of 58 (25%),
  fixed seed 20261127, own GT written from questions-only text before seeing draft
  GT. Full agreement 45/58 (77.6%); sections 55/58 (94.8%), court 57/58 (98.3%),
  escalates boolean 58/58 (100%), kinds 47/58 (81.0%). All 16 C13 items blind-rated
  for fluency + GT. Report: `brutal-bank-second-rater-report.md`.
- **Third reader (adjudication):** settled the 4 legal disagreements (B-030, B-123,
  B-007, B-213) — DRAFT STANDS on all four — and audited all of C6 plus the flagged
  "being filed" items. Report: `brutal-bank-adjudication.md`.
- **8-gram overlap check** (scripted, counts/flags only): vs current-16, sealed
  fresh-20/Kannada-8, 20 plan design examples, v5 lane paraphrase tests, gate lines.
  Run 1: 11 flagged, rewritten. Run 2: 4 flagged, rewritten. Run 3 (final):
  **0 flagged of 230**. Adjudication changed GT + notes only (no question text), so
  the check stands.

## 4. Adjudication log (changes vs draft — the ONLY differences between draft and frozen)

| ID | Change | Reason (one line) |
|---|---|---|
| B-012 | GT [hma-13, hma-27] → [hma-13] | "I want a divorce" + "never filed anything" is a wish, not a filing. |
| B-022 | GT [hma-13, hma-25, hma-27] → [hma-13, hma-25] | Wanting a divorce is not being filed; hma-25 kept (flagged, see §6). |
| B-026 | GT [hma-13b, hma-27, gwa-1890] → [hma-13b, gwa-1890] | "We both want" is a shared wish, not a filing; custody stays GWA. |
| B-112 | GT [hma-13, hma-27] → [hma-13] | "I want a divorce" is a wish, not a filing (found by the C6 audit). |
| B-120 | GT [hma-13, hma-27] → [hma-13] | "If I file" is hypothetical, not a filing. |

Courts, escalates booleans, and kinds are unchanged on all five. D1–D4 (B-030
pwdva-18 + safety; B-123 hma-26; B-007 hma-24 + Family Court; B-213 pwdva-18 +
safety): draft stands.

## 5. Kind conventions (write-down, per second rater — binding for scoring)

- `fact`: added wherever an open or disputed fact exists (44 uses). Boundary (tight):
  an open fact that changes the remedy or forum — not a catch-all for any uncertainty.
- `demand`: added where Stridhan recovery is sought but no demand has yet been made.
- `procedure`: added where a procedural relief is sought. Boundary vs `court` kind:
  forum choice = `court`; process = `procedure`.
- `hma-26` / `gwa-1890` rule: custody inside a pending or being-filed HMA proceeding
  → `hma-26`; custody with divorce merely asked/contemplated → `gwa-1890`. Same
  pending/being-filed trigger as HMA 27.
- Out-of-scope convention: empty-GT items carry `gt_escalates=true` with kind
  `["procedure"]` as a handoff (BX-13 design example); the two C9 no-dispute empties
  carry `gt_escalates=false`.
- B-148 verdict (confirmed): empty GT is CORRECT — PWDVA s.2(a) "aggrieved person"
  is a woman, so no PWDVA order is available to a male claimant; procedure handoff.

## 6. Open items / pre-run requirements (recorded, not hidden)

1. **Label coverage gap — MUST be fixed before the brutal run:** `hma-9` (B-018) and
   `pwdva-22` (B-019) are NOT in the graph's 32-section label set (verified by the
   coordinator against `laya-crpc-bns-section-decision-tree-v2.json`). Both are
   legitimate labels (second rater verified the uses), but the system physically
   cannot produce them — both questions are guaranteed misses until the labels are
   added to the system (graph + notebook) as a separate logged system change, after
   which the brutal run happens. The other four extended labels (hma-24, hma-25,
   hma-26, hma-13b) ARE in the label set.
2. **Kannada C13 — native confirmation still open:** second rater verified all 16
   C13 items at working-reading level (fluent, natural Kannada; GT 12/16 full
   agreement, 15/16 sections) but is not a native Kannada speaker. Native-speaker
   confirmation is still recommended and should be recorded before the bank is used
   for a scored run.
3. **B-022 / hma-25 flag:** s.25 strictly presupposes a decree; B-022's lump-sum
   ask with no proceeding yet is the thinnest hma-25 use. Both raters and the
   adjudicator kept it; recorded here, not silently decided.
4. **Recovery text (system, not bank):** the Lane 2 `recovery` escalation text
   naming "civil recovery under HMA s.27" must be amended before any v6 run is
   scored — wrong on K0/H15 under D1-A.
5. **Rater identity:** rater lanes were agent lanes, not named humans; no rater
   name/ID or legal-qualification record exists for this bank (contrast with the
   sealed sets, which have the same gap — v6 §7.1). Recorded as a known gap.
